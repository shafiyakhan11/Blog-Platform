from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password as hash_secure_password
from app.core.security import verify_password as verify_secure_password

from .api.routes.admin import router as admin_router
from .api.routes.auth import router as auth_router
from .config import APP_NAME, JWT_SECRET
from .database import a_engine, get_db
from .models import Comment, CommentLike, Follow, FollowRequest, Post, PostLike, User, UserBlock
from .services.authorization import PrivacyPolicy

app = FastAPI(title=APP_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(admin_router)


class AuthRequest(BaseModel):
    mode: Literal["login", "signup"]
    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = None


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(raw: str, password_hash: str) -> bool:
    return hash_password(raw) == password_hash


def encode_jwt(user_id: int) -> str:
    payload = json.dumps({"sub": user_id, "exp": (datetime.now(timezone.utc) + timedelta(days=7)).timestamp()}, separators=(",", ":")).encode()
    sig = hmac.new(JWT_SECRET.encode(), payload, hashlib.sha256).digest()
    return f"{payload.hex()}.{sig.hex()}"


def decode_jwt(token: str) -> dict[str, Any]:
    try:
        payload_hex, sig_hex = token.split(".", 1)
    except ValueError as exc:  # pragma: no cover
        raise HTTPException(status_code=401, detail="Invalid token") from exc
    expected = hmac.new(JWT_SECRET.encode(), bytes.fromhex(payload_hex), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig_hex):
        raise HTTPException(status_code=401, detail="Invalid token")
    payload = json.loads(bytes.fromhex(payload_hex))
    exp = float(payload.get("exp", 0))
    if exp < datetime.now(timezone.utc).timestamp():
        raise HTTPException(status_code=401, detail="Token expired")
    return payload


async def get_auth_user(
    db: Session = Depends(get_db),
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.split(" ", 1)[1]
    payload = decode_jwt(token)
    user = db.get(User, payload.get("sub"))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


async def get_optional_user(
    db: Session = Depends(get_db),
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> User | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        return await get_auth_user(db=db, authorization=authorization)
    except HTTPException:
        return None


@app.on_event("startup")
def startup() -> None:
    with a_engine.connect() as connection:
        connection.execute(text("SELECT 1"))


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth")
def authenticate(payload: AuthRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    email_value = str(payload.email).strip().lower()
    user_columns = {column["name"] for column in inspect(db.get_bind()).get_columns("users")}
    selected_columns = ["id", "name", "username", "email", "password_hash"]
    selected_columns.extend(column for column in ("bio", "followers", "following") if column in user_columns)
    user = db.execute(
        text(f"SELECT {', '.join(selected_columns)} FROM users WHERE LOWER(email) = :email"),
        {"email": email_value},
    ).mappings().one_or_none()

    if payload.mode == "login":
        if user is None:
            raise HTTPException(status_code=401, detail="Email or password is incorrect. Check both and try again.")

        stored_hash = str(user["password_hash"])
        is_legacy_hash = len(stored_hash) == 64 and all(character in "0123456789abcdefABCDEF" for character in stored_hash)
        password_matches = (
            hmac.compare_digest(hash_password(payload.password), stored_hash)
            if is_legacy_hash
            else verify_secure_password(payload.password, stored_hash)
        )
        if not password_matches:
            raise HTTPException(status_code=401, detail="Email or password is incorrect. Check both and try again.")

        if is_legacy_hash:
            db.execute(
                text("UPDATE users SET password_hash = :password_hash WHERE id = :user_id"),
                {"password_hash": hash_secure_password(payload.password), "user_id": user["id"]},
            )
            db.commit()
    else:
        if user is not None:
            raise HTTPException(status_code=409, detail="An account with this email already exists. Please sign in.")
        name = (payload.name or "").strip()
        if not name:
            raise HTTPException(status_code=422, detail="Name is required to create an account")

        username_base = re.sub(r"[^a-z0-9_]", "", email_value.split("@", 1)[0])[:32] or "writer"
        username = f"{username_base}_{secrets.token_hex(4)}"
        insert_values = {
            "name": name,
            "username": username,
            "email": email_value,
            "password_hash": hash_secure_password(payload.password),
            "bio": "",
            "followers": 0,
            "following": 0,
            "role": "user",
            "is_active": True,
            "is_verified": False,
            "profile_visibility": "public",
        }
        insert_values = {key: value for key, value in insert_values.items() if key in user_columns}
        columns = ", ".join(insert_values)
        values = ", ".join(f":{column}" for column in insert_values)
        user_id = db.execute(
            text(f"INSERT INTO users ({columns}) VALUES ({values}) RETURNING id"),
            insert_values,
        ).scalar_one()
        db.commit()
        user = {
            "id": user_id,
            "name": name,
            "username": username,
            "email": email_value,
            "bio": "",
            "followers": 0,
            "following": 0,
        }

    return {
        "access_token": encode_jwt(int(user["id"])),
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "username": user["username"],
            "email": user["email"],
            "bio": user.get("bio") or "",
            "followers": user.get("followers") or 0,
            "following": user.get("following") or 0,
        },
    }


@app.get("/api/profile")
def get_profile(db: Session = Depends(get_db), current_user: User = Depends(get_auth_user)) -> dict[str, Any]:
    return {
        "id": current_user.id,
        "name": current_user.name,
        "username": current_user.username,
        "email": current_user.email,
        "bio": current_user.bio,
        "followers": db.execute(select(func.count()).select_from(Follow).where(Follow.following_id == current_user.id)).scalar_one() or 0,
        "following": db.execute(select(func.count()).select_from(Follow).where(Follow.follower_id == current_user.id)).scalar_one() or 0,
        "profile_visibility": current_user.profile_visibility,
    }


@app.put("/api/profile")
def update_profile(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        token_payload = decode_jwt(authorization.split(" ", 1)[1])
        user_id = int(token_payload["sub"])
    except (HTTPException, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    user_columns = {column["name"] for column in inspect(db.get_bind()).get_columns("users")}
    if db.execute(text("SELECT id FROM users WHERE id = :user_id"), {"user_id": user_id}).scalar_one_or_none() is None:
        raise HTTPException(status_code=401, detail="User not found")

    updates = {}
    for field in ("name", "username", "email", "bio", "profile_visibility"):
        if field not in payload or field not in user_columns:
            continue
        value = str(payload[field])
        if field in {"name", "username", "email", "profile_visibility"}:
            value = value.strip()
        if field == "username":
            value = value.removeprefix("@")
        elif field == "email":
            value = value.lower()
        updates[field] = value

    if not updates:
        raise HTTPException(status_code=400, detail="No supported profile fields were provided")

    assignments = ", ".join(f"{field} = :{field}" for field in updates)
    try:
        db.execute(
            text(f"UPDATE users SET {assignments} WHERE id = :user_id"),
            {**updates, "user_id": user_id},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username or email is already in use") from exc

    profile_columns = ["id", "name", "username", "email"]
    profile_columns.extend(field for field in ("bio", "followers", "following") if field in user_columns)
    current_user = db.execute(
        text(f"SELECT {', '.join(profile_columns)} FROM users WHERE id = :user_id"),
        {"user_id": user_id},
    ).mappings().one()
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "username": current_user["username"],
        "email": current_user["email"],
        "bio": current_user.get("bio") or "",
        "followers": current_user.get("followers") or 0,
        "following": current_user.get("following") or 0,
    }


@app.get("/api/v1/users/{username}")
def get_user_profile(username: str, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_user)) -> dict[str, Any]:
    user = db.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    policy = PrivacyPolicy()
    viewer_id = current_user.id if current_user else None
    is_owner = current_user is not None and current_user.id == user.id
    if not is_owner and user.profile_visibility == "private":
        if current_user is None or not policy.can_follow_user(current_user, user, viewer_user_id=viewer_id, target_user_id=user.id):
            raise HTTPException(status_code=403, detail="This profile is private")
    followers_count = db.execute(select(func.count()).select_from(Follow).where(Follow.following_id == user.id)).scalar_one() or 0
    following_count = db.execute(select(func.count()).select_from(Follow).where(Follow.follower_id == user.id)).scalar_one() or 0
    is_following = False
    is_followed_by = False
    if current_user is not None:
        is_following = db.execute(select(Follow.id).where(Follow.follower_id == current_user.id, Follow.following_id == user.id)).scalar_one() is not None
        is_followed_by = db.execute(select(Follow.id).where(Follow.follower_id == user.id, Follow.following_id == current_user.id)).scalar_one() is not None
    return {
        "id": user.id,
        "username": user.username,
        "name": user.name,
        "bio": user.bio,
        "followers_count": followers_count,
        "following_count": following_count,
        "is_following": is_following,
        "is_followed_by": is_followed_by,
        "profile_visibility": user.profile_visibility,
    }


@app.post("/api/v1/users/{user_id}/follow")
def follow_user(user_id: int, current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db.execute(select(UserBlock.id).where(UserBlock.blocker_id == current_user.id, UserBlock.blocked_id == user_id)).scalar_one_or_none() is not None:
        raise HTTPException(status_code=403, detail="Blocked users cannot follow each other")
    if target.profile_visibility == "private":
        existing = db.execute(select(FollowRequest.id).where(FollowRequest.requester_id == current_user.id, FollowRequest.target_user_id == user_id)).scalar_one_or_none()
        if existing is None:
            db.add(FollowRequest(requester_id=current_user.id, target_user_id=user_id, status="pending"))
            db.commit()
            return {"success": True, "data": {"following": False, "status": "pending"}}
    existing = db.execute(select(Follow.id).where(Follow.follower_id == current_user.id, Follow.following_id == user_id)).scalar_one_or_none()
    if existing is not None:
        return {"success": True, "data": {"following": True}}
    follow = Follow(follower_id=current_user.id, following_id=user_id)
    db.add(follow)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"success": True, "data": {"following": True}}
    return {"success": True, "data": {"following": True}}


@app.delete("/api/v1/users/{user_id}/follow")
def unfollow_user(user_id: int, current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    existing = db.execute(select(Follow.id).where(Follow.follower_id == current_user.id, Follow.following_id == user_id)).scalar_one_or_none()
    if existing is not None:
        db.delete(db.get(Follow, existing))
        db.commit()
    return {"success": True, "data": {"following": False}}


@app.get("/api/v1/users/{user_id}/followers")
def list_followers(user_id: int, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_user), page: int = 1, limit: int = 20) -> dict[str, Any]:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    policy = PrivacyPolicy()
    if current_user is None or current_user.id != user_id:
        if not policy.can_view_profile(current_user, target, viewer_user_id=getattr(current_user, "id", None), owner_id=user_id):
            raise HTTPException(status_code=403, detail="Cannot view followers list")
    rows = db.execute(
        select(User.id, User.username, User.name)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.following_id == user_id)
        .order_by(Follow.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    total = db.execute(select(func.count()).select_from(Follow).where(Follow.following_id == user_id)).scalar_one() or 0
    return {"success": True, "data": {"items": [{"id": r.id, "username": r.username, "name": r.name} for r in rows], "page": page, "limit": limit, "total": total}}


@app.get("/api/v1/users/{user_id}/following")
def list_following(user_id: int, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_user), page: int = 1, limit: int = 20) -> dict[str, Any]:
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    policy = PrivacyPolicy()
    if current_user is None or current_user.id != user_id:
        if not policy.can_view_profile(current_user, target, viewer_user_id=getattr(current_user, "id", None), owner_id=user_id):
            raise HTTPException(status_code=403, detail="Cannot view following list")
    rows = db.execute(
        select(User.id, User.username, User.name)
        .join(Follow, Follow.following_id == User.id)
        .where(Follow.follower_id == user_id)
        .order_by(Follow.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()
    total = db.execute(select(func.count()).select_from(Follow).where(Follow.follower_id == user_id)).scalar_one() or 0
    return {"success": True, "data": {"items": [{"id": r.id, "username": r.username, "name": r.name} for r in rows], "page": page, "limit": limit, "total": total}}


@app.post("/api/v1/users/{user_id}/follow-request")
def request_follow(user_id: int, current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself")
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db.execute(select(UserBlock.id).where(UserBlock.blocker_id == current_user.id, UserBlock.blocked_id == user_id)).scalar_one_or_none() is not None:
        raise HTTPException(status_code=403, detail="You are blocked from interacting with this user")
    existing = db.execute(select(FollowRequest.id).where(FollowRequest.requester_id == current_user.id, FollowRequest.target_user_id == user_id)).scalar_one_or_none()
    if existing is not None:
        return {"success": True, "data": {"status": "pending"}}
    request = FollowRequest(requester_id=current_user.id, target_user_id=user_id, status="pending")
    db.add(request)
    db.commit()
    return {"success": True, "data": {"status": "pending"}}


@app.post("/api/v1/follow-requests/{request_id}/accept")
def accept_follow_request(request_id: int, current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    request = db.get(FollowRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Follow request not found")
    if request.target_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the target user can accept a request")
    request.status = "accepted"
    if db.execute(select(Follow.id).where(Follow.follower_id == request.requester_id, Follow.following_id == request.target_user_id)).scalar_one_or_none() is None:
        db.add(Follow(follower_id=request.requester_id, following_id=request.target_user_id))
    db.commit()
    return {"success": True, "data": {"status": "accepted"}}


@app.post("/api/v1/follow-requests/{request_id}/reject")
def reject_follow_request(request_id: int, current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    request = db.get(FollowRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Follow request not found")
    if request.target_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the target user can reject a request")
    request.status = "rejected"
    db.commit()
    return {"success": True, "data": {"status": "rejected"}}


@app.delete("/api/v1/follow-requests/{request_id}")
def delete_follow_request(request_id: int, current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    request = db.get(FollowRequest, request_id)
    if request is None:
        raise HTTPException(status_code=404, detail="Follow request not found")
    if request.requester_id != current_user.id and request.target_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to cancel this request")
    db.delete(request)
    db.commit()
    return {"success": True, "data": {"deleted": True}}


@app.post("/api/v1/users/{user_id}/block")
def block_user(user_id: int, current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot block yourself")
    if db.get(User, user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    existing = db.execute(select(UserBlock.id).where(UserBlock.blocker_id == current_user.id, UserBlock.blocked_id == user_id)).scalar_one_or_none()
    if existing is None:
        db.add(UserBlock(blocker_id=current_user.id, blocked_id=user_id))
        db.commit()
    return {"success": True, "data": {"blocked": True}}


@app.delete("/api/v1/users/{user_id}/block")
def unblock_user(user_id: int, current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    record = db.execute(select(UserBlock).where(UserBlock.blocker_id == current_user.id, UserBlock.blocked_id == user_id)).scalar_one_or_none()
    if record is not None:
        db.delete(record)
        db.commit()
    return {"success": True, "data": {"blocked": False}}


@app.get("/api/v1/feed")
def feed(db: Session = Depends(get_db), current_user: User = Depends(get_auth_user), page: int = 1, limit: int = 20) -> dict[str, Any]:
    followed_ids = [row[0] for row in db.execute(select(Follow.following_id).where(Follow.follower_id == current_user.id)).all()]
    blocked_ids = [row[0] for row in db.execute(select(UserBlock.blocked_id).where(UserBlock.blocker_id == current_user.id)).all()]
    if not followed_ids:
        followed_ids = [current_user.id]
    else:
        followed_ids.append(current_user.id)
    query = select(Post).where(Post.deleted_at.is_(None), Post.author_id.in_(followed_ids), Post.visibility.in_(["public", "followers"]))
    if blocked_ids:
        query = query.where(~Post.author_id.in_(blocked_ids))
    query = query.order_by(Post.created_at.desc()).offset((page - 1) * limit).limit(limit)
    rows = db.execute(query).scalars().all()
    items = []
    for post in rows:
        if post.author_id == current_user.id or post.visibility == "public" or post.author_id in followed_ids:
            items.append({
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "visibility": post.visibility,
                "author_id": post.author_id,
                "like_count": db.execute(select(func.count()).select_from(PostLike).where(PostLike.post_id == post.id)).scalar_one() or 0,
                "liked_by_current_user": db.execute(select(PostLike.id).where(PostLike.post_id == post.id, PostLike.user_id == current_user.id)).scalar_one() is not None,
            })
    return {"success": True, "data": {"items": items, "page": page, "limit": limit}}


@app.get("/api/v1/posts")
def list_posts(db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_user), limit: int = Query(default=20, ge=1, le=100), cursor: int | None = None) -> dict[str, Any]:
    query = select(Post).where(Post.deleted_at.is_(None), Post.status == "published")
    if cursor is not None:
        query = query.where(Post.id < cursor)
    query = query.order_by(Post.id.desc()).limit(limit)
    rows = db.execute(query).scalars().all()
    items = []
    for post in rows:
        if PrivacyPolicy().can_view_post(current_user, post, viewer_user_id=getattr(current_user, "id", None), author_user_id=post.author_id):
            items.append({
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "visibility": post.visibility,
                "author_id": post.author_id,
                "like_count": db.execute(select(func.count()).select_from(PostLike).where(PostLike.post_id == post.id)).scalar_one() or 0,
                "liked_by_current_user": current_user is not None and db.execute(select(PostLike.id).where(PostLike.post_id == post.id, PostLike.user_id == current_user.id)).scalar_one() is not None,
            })
    next_cursor = rows[-1].id if rows else None
    return {"success": True, "data": {"items": items, "limit": limit, "next_cursor": next_cursor}}


@app.get("/api/posts")
def legacy_posts(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    posts = db.execute(text("""
        SELECT id, title, excerpt, content, author, author_handle, avatar, tags,
               published_date, read_time, likes, views, shares, trending_score,
               is_bookmarked, is_followed
        FROM posts
        ORDER BY created_at DESC
        LIMIT 100
    """)).mappings().all()
    return [
        {
            "id": str(post["id"]),
            "title": post["title"],
            "excerpt": post["excerpt"] or post["content"][:160],
            "content": post["content"],
            "author": post["author"],
            "author_handle": post["author_handle"],
            "avatar": post["avatar"],
            "tags": post["tags"] or [],
            "published_date": post["published_date"] or "",
            "read_time": post["read_time"] or 1,
            "likes": post["likes"] or 0,
            "views": post["views"] or 0,
            "comments": [],
            "shares": post["shares"] or 0,
            "trending_score": post["trending_score"] or 0,
            "is_liked": False,
            "is_bookmarked": post["is_bookmarked"] or False,
            "is_followed": post["is_followed"] or False,
        }
        for post in posts
    ]


@app.post("/api/v1/posts")
def create_post(payload: dict[str, Any], current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    title = str(payload.get("title") or "Untitled").strip()
    content = str(payload.get("content") or "")
    excerpt = payload.get("excerpt") or content[:160]
    visibility = str(payload.get("visibility") or "public")
    if visibility not in {"public", "followers", "private"}:
        raise HTTPException(status_code=400, detail="Invalid visibility")
    post = Post(
        author_id=current_user.id,
        title=title,
        slug=title.lower().replace(" ", "-")[:60],
        content=content,
        excerpt=str(excerpt),
        status=str(payload.get("status") or "published"),
        visibility=visibility,
        published_at=datetime.now(timezone.utc),
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return {"success": True, "data": {"id": post.id, "title": post.title, "visibility": post.visibility}}


@app.get("/api/v1/posts/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_user)) -> dict[str, Any]:
    post = db.get(Post, post_id)
    if post is None or post.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Post not found")
    if not PrivacyPolicy().can_view_post(current_user, post, viewer_user_id=getattr(current_user, "id", None), author_user_id=post.author_id):
        raise HTTPException(status_code=403, detail="You do not have permission to view this post")
    like_count = db.execute(select(func.count()).select_from(PostLike).where(PostLike.post_id == post.id)).scalar_one() or 0
    liked_by_current_user = current_user is not None and db.execute(select(PostLike.id).where(PostLike.post_id == post.id, PostLike.user_id == current_user.id)).scalar_one() is not None
    return {"success": True, "data": {"id": post.id, "title": post.title, "content": post.content, "visibility": post.visibility, "author_id": post.author_id, "like_count": like_count, "liked_by_current_user": liked_by_current_user}}


@app.put("/api/v1/posts/{post_id}")
def update_post(post_id: int, payload: dict[str, Any], current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to edit this post")
    post.title = str(payload.get("title") or post.title)
    post.content = str(payload.get("content") or post.content)
    if "visibility" in payload:
        value = str(payload["visibility"]).lower()
        if value in {"public", "followers", "private"}:
            post.visibility = value
    db.commit()
    return {"success": True, "data": {"id": post.id, "title": post.title, "visibility": post.visibility}}


@app.delete("/api/v1/posts/{post_id}")
def delete_post(post_id: int, current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed to delete this post")
    post.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True, "data": {"deleted": True}}


@app.post("/api/v1/posts/{post_id}/like")
def like_post(post_id: int, current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    post = db.get(Post, post_id)
    if post is None or post.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Post not found")
    if not PrivacyPolicy().can_view_post(current_user, post, viewer_user_id=current_user.id, author_user_id=post.author_id):
        raise HTTPException(status_code=403, detail="You cannot like this content")
    existing = db.execute(select(PostLike.id).where(PostLike.post_id == post_id, PostLike.user_id == current_user.id)).scalar_one_or_none()
    if existing is None:
        db.add(PostLike(post_id=post_id, user_id=current_user.id))
        db.commit()
    return {"success": True, "data": {"liked": True}} 


@app.delete("/api/v1/posts/{post_id}/like")
def unlike_post(post_id: int, current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    existing = db.execute(select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == current_user.id)).scalar_one_or_none()
    if existing is not None:
        db.delete(existing)
        db.commit()
    return {"success": True, "data": {"liked": False}}


@app.get("/api/v1/posts/{post_id}/likes")
def get_post_likes(post_id: int, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_user)) -> dict[str, Any]:
    post = db.get(Post, post_id)
    if post is None or post.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Post not found")
    if current_user is None or not PrivacyPolicy().can_view_post(current_user, post, viewer_user_id=current_user.id, author_user_id=post.author_id):
        raise HTTPException(status_code=403, detail="You cannot view likes for this post")
    like_count = db.execute(select(func.count()).select_from(PostLike).where(PostLike.post_id == post_id)).scalar_one() or 0
    liked_by_current_user = current_user is not None and db.execute(select(PostLike.id).where(PostLike.post_id == post_id, PostLike.user_id == current_user.id)).scalar_one() is not None
    return {"id": post.id, "title": post.title, "like_count": like_count, "liked_by_current_user": liked_by_current_user}


@app.post("/api/v1/posts/{post_id}/comments")
def create_comment(post_id: int, payload: dict[str, Any], current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if not PrivacyPolicy().can_view_post(current_user, post, viewer_user_id=current_user.id, author_user_id=post.author_id):
        raise HTTPException(status_code=403, detail="You cannot comment on this post")
    content = str(payload.get("content") or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Comment content cannot be empty")
    comment = Comment(post_id=post_id, user_id=current_user.id, parent_comment_id=payload.get("parent_comment_id"), content=content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {"success": True, "data": {"id": comment.id, "content": comment.content}}


@app.get("/api/v1/posts/{post_id}/comments")
def get_post_comments(post_id: int, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_user)) -> dict[str, Any]:
    post = db.get(Post, post_id)
    if post is None or post.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Post not found")
    if current_user is None or not PrivacyPolicy().can_view_post(current_user, post, viewer_user_id=current_user.id, author_user_id=post.author_id):
        raise HTTPException(status_code=403, detail="You cannot view comments for this post")
    comments = db.execute(select(Comment).where(Comment.post_id == post_id, Comment.parent_comment_id.is_(None)).order_by(Comment.created_at.asc())).scalars().all()
    return {"success": True, "data": {"items": [{"id": c.id, "content": c.content, "user_id": c.user_id, "like_count": db.execute(select(func.count()).select_from(CommentLike).where(CommentLike.comment_id == c.id)).scalar_one() or 0} for c in comments]}}


@app.post("/api/v1/comments/{comment_id}/replies")
def create_reply(comment_id: int, payload: dict[str, Any], current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    parent = db.get(Comment, comment_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    post = db.get(Post, parent.post_id)
    if post is None or not PrivacyPolicy().can_view_post(current_user, post, viewer_user_id=current_user.id, author_user_id=post.author_id):
        raise HTTPException(status_code=403, detail="You cannot reply to this comment")
    content = str(payload.get("content") or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Reply content cannot be empty")
    reply = Comment(post_id=post.id, user_id=current_user.id, parent_comment_id=comment_id, content=content)
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return {"success": True, "data": {"id": reply.id, "content": reply.content}}


@app.get("/api/v1/comments/{comment_id}/replies")
def get_replies(comment_id: int, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_user)) -> dict[str, Any]:
    parent = db.get(Comment, comment_id)
    if parent is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    post = db.get(Post, parent.post_id)
    if current_user is None or post is None or not PrivacyPolicy().can_view_post(current_user, post, viewer_user_id=current_user.id, author_user_id=post.author_id):
        raise HTTPException(status_code=403, detail="You cannot view replies for this comment")
    replies = db.execute(select(Comment).where(Comment.parent_comment_id == comment_id).order_by(Comment.created_at.asc())).scalars().all()
    return {"success": True, "data": {"items": [{"id": c.id, "content": c.content, "user_id": c.user_id} for c in replies]}}


@app.put("/api/v1/comments/{comment_id}")
def update_comment(comment_id: int, payload: dict[str, Any], current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You cannot edit this comment")
    content = str(payload.get("content") or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Comment content cannot be empty")
    comment.content = content
    db.commit()
    return {"success": True, "data": {"id": comment.id, "content": comment.content}}


@app.delete("/api/v1/comments/{comment_id}")
def delete_comment(comment_id: int, current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="You cannot delete this comment")
    db.delete(comment)
    db.commit()
    return {"success": True, "data": {"deleted": True}}


@app.post("/api/v1/comments/{comment_id}/like")
def like_comment(comment_id: int, current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    post = db.get(Post, comment.post_id)
    if post is None or not PrivacyPolicy().can_view_post(current_user, post, viewer_user_id=current_user.id, author_user_id=post.author_id):
        raise HTTPException(status_code=403, detail="You cannot like this comment")
    if db.execute(select(CommentLike.id).where(CommentLike.comment_id == comment_id, CommentLike.user_id == current_user.id)).scalar_one_or_none() is None:
        db.add(CommentLike(comment_id=comment_id, user_id=current_user.id))
        db.commit()
    return {"success": True, "data": {"liked": True}}


@app.delete("/api/v1/comments/{comment_id}/like")
def unlike_comment(comment_id: int, current_user: User = Depends(get_auth_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    existing = db.execute(select(CommentLike).where(CommentLike.comment_id == comment_id, CommentLike.user_id == current_user.id)).scalar_one_or_none()
    if existing is not None:
        db.delete(existing)
        db.commit()
    return {"success": True, "data": {"liked": False}}


@app.get("/api/v1/comments/{comment_id}/likes")
def get_comment_likes(comment_id: int, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_user)) -> dict[str, Any]:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    post = db.get(Post, comment.post_id)
    if post is None or current_user is None or not PrivacyPolicy().can_view_post(current_user, post, viewer_user_id=current_user.id, author_user_id=post.author_id):
        raise HTTPException(status_code=403, detail="You cannot view likes for this comment")
    like_count = db.execute(select(func.count()).select_from(CommentLike).where(CommentLike.comment_id == comment_id)).scalar_one() or 0
    liked_by_current_user = db.execute(select(CommentLike.id).where(CommentLike.comment_id == comment_id, CommentLike.user_id == current_user.id)).scalar_one() is not None
    return {"id": comment.id, "content": comment.content, "like_count": like_count, "liked_by_current_user": liked_by_current_user}


@app.get("/api/v1/users/{user_id}/followers")
def get_followers_v1(user_id: int, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_user)) -> dict[str, Any]:
    return list_followers(user_id, db=db, current_user=current_user)


@app.get("/api/v1/users/{user_id}/following")
def get_following_v1(user_id: int, db: Session = Depends(get_db), current_user: User | None = Depends(get_optional_user)) -> dict[str, Any]:
    return list_following(user_id, db=db, current_user=current_user)
