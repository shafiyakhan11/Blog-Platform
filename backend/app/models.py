from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

USER_ID_TYPE = BigInteger().with_variant(Integer, "sqlite")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(USER_ID_TYPE, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    bio: Mapped[str] = mapped_column(Text, default="", nullable=False)
    role: Mapped[str] = mapped_column(String(32), default="user", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    profile_visibility: Mapped[str] = mapped_column(String(20), default="public", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    posts: Mapped[list["Post"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    follows_made: Mapped[list["Follow"]] = relationship(foreign_keys="Follow.follower_id", back_populates="follower")
    follows_received: Mapped[list["Follow"]] = relationship(foreign_keys="Follow.following_id", back_populates="following")
    blocked_by: Mapped[list["UserBlock"]] = relationship(foreign_keys="UserBlock.blocked_id", back_populates="blocked_user")
    blockers: Mapped[list["UserBlock"]] = relationship(foreign_keys="UserBlock.blocker_id", back_populates="blocker")
    sent_follow_requests: Mapped[list["FollowRequest"]] = relationship(foreign_keys="FollowRequest.requester_id", back_populates="requester")
    received_follow_requests: Mapped[list["FollowRequest"]] = relationship(foreign_keys="FollowRequest.target_user_id", back_populates="target_user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(USER_ID_TYPE, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(USER_ID_TYPE, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Follow(Base):
    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "following_id", name="uq_follows_pair"),
        CheckConstraint("follower_id <> following_id", name="ck_follows_not_self"),
        Index("ix_follows_follower_id", "follower_id"),
        Index("ix_follows_following_id", "following_id"),
    )

    id: Mapped[int] = mapped_column(USER_ID_TYPE, primary_key=True, index=True)
    follower_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    following_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    follower: Mapped[User] = relationship(foreign_keys=[follower_id], back_populates="follows_made")
    following: Mapped[User] = relationship(foreign_keys=[following_id], back_populates="follows_received")


class FollowRequest(Base):
    __tablename__ = "follow_requests"
    __table_args__ = (
        UniqueConstraint("requester_id", "target_user_id", name="uq_follow_request_pair"),
        CheckConstraint("requester_id <> target_user_id", name="ck_follow_request_not_self"),
    )

    id: Mapped[int] = mapped_column(USER_ID_TYPE, primary_key=True, index=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    requester: Mapped[User] = relationship(foreign_keys=[requester_id], back_populates="sent_follow_requests")
    target_user: Mapped[User] = relationship(foreign_keys=[target_user_id], back_populates="received_follow_requests")


class Post(Base):
    __tablename__ = "posts"
    __table_args__ = (
        Index("ix_posts_visibility", "visibility"),
        Index("ix_posts_status", "status"),
        Index("ix_posts_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_name: Mapped[str] = mapped_column("author", String(255), nullable=False, default="DraftFlow")
    author_handle: Mapped[str] = mapped_column(String(255), nullable=False, default="@draftflow")
    avatar: Mapped[str] = mapped_column(String(255), nullable=False, default="DF")
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    published_date: Mapped[str] = mapped_column(Text, nullable=False, default="")
    read_time: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    likes_count: Mapped[int] = mapped_column("likes", Integer, nullable=False, default=0)
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    shares: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trending_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_followed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(20), default="published", nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), default="public", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    author: Mapped[User | None] = relationship(back_populates="posts")
    likes: Mapped[list["PostLike"]] = relationship(back_populates="post", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship(back_populates="post", cascade="all, delete-orphan")


class PostLike(Base):
    __tablename__ = "user_post_likes"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_post_like_pair"),
        Index("ix_user_post_likes_post_id", "post_id"),
        Index("ix_user_post_likes_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(USER_ID_TYPE, primary_key=True, index=True)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    post: Mapped[Post] = relationship(back_populates="likes")


class PostBookmark(Base):
    __tablename__ = "post_bookmarks"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_post_bookmark_pair"),
        Index("ix_post_bookmarks_post_id", "post_id"),
        Index("ix_post_bookmarks_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(USER_ID_TYPE, primary_key=True, index=True)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Comment(Base):
    __tablename__ = "comments"
    __table_args__ = (
        Index("ix_comments_post_id", "post_id"),
        Index("ix_comments_parent_comment_id", "parent_id"),
        Index("ix_comments_user_id", "user_id"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    post_id: Mapped[str] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    parent_comment_id: Mapped[str | None] = mapped_column("parent_id", ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    author: Mapped[str] = mapped_column(String(255), nullable=False, default="DraftFlow")
    avatar: Mapped[str] = mapped_column(String(255), nullable=False, default="DF")
    likes_count: Mapped[int] = mapped_column("likes", Integer, nullable=False, default=0)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    post: Mapped[Post] = relationship(back_populates="comments")
    likes: Mapped[list["CommentLike"]] = relationship(back_populates="comment", cascade="all, delete-orphan")


class CommentLike(Base):
    __tablename__ = "comment_likes"
    __table_args__ = (
        UniqueConstraint("comment_id", "user_id", name="uq_comment_like_pair"),
        Index("ix_comment_likes_comment_id", "comment_id"),
        Index("ix_comment_likes_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(USER_ID_TYPE, primary_key=True, index=True)
    comment_id: Mapped[str] = mapped_column(ForeignKey("comments.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    comment: Mapped[Comment] = relationship(back_populates="likes")


class UserBlock(Base):
    __tablename__ = "user_blocks"
    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_user_block_pair"),
        CheckConstraint("blocker_id <> blocked_id", name="ck_block_not_self"),
        Index("ix_user_blocks_blocker_id", "blocker_id"),
        Index("ix_user_blocks_blocked_id", "blocked_id"),
    )

    id: Mapped[int] = mapped_column(USER_ID_TYPE, primary_key=True, index=True)
    blocker_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    blocked_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    blocker: Mapped[User] = relationship(foreign_keys=[blocker_id], back_populates="blockers")
    blocked_user: Mapped[User] = relationship(foreign_keys=[blocked_id], back_populates="blocked_by")
