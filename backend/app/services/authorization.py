from __future__ import annotations

from dataclasses import dataclass

from app.models import Post, User


@dataclass
class PrivacyPolicy:
    def can_view_post(
        self,
        viewer: User | None,
        post: Post,
        *,
        viewer_user_id: int | None = None,
        author_user_id: int | None = None,
        approved_follower: bool = False,
    ) -> bool:
        if post.deleted_at is not None:
            return False
        viewer_id = viewer_user_id if viewer_user_id is not None else getattr(viewer, "id", None)
        author_id = author_user_id if author_user_id is not None else getattr(post, "author_id", None)
        if viewer is not None and getattr(viewer, "role", "user") == "admin":
            return True
        if viewer_id is not None and viewer_id == author_id:
            return True
        if post.visibility == "public":
            return True
        if post.visibility == "followers":
            return bool(approved_follower)
        if post.visibility == "private":
            return False
        return False

    def can_follow_user(
        self,
        requester: User | None,
        target_user: User,
        *,
        viewer_user_id: int | None = None,
        target_user_id: int | None = None,
    ) -> bool:
        requester_id = getattr(requester, "id", None) if requester is not None else viewer_user_id
        target_id = target_user_id if target_user_id is not None else getattr(target_user, "id", None)
        if requester_id is None or target_id is None:
            return False
        if requester_id == target_id:
            return False
        if target_user.profile_visibility == "private":
            return True
        return True

    def can_view_profile(
        self,
        viewer: User | None,
        profile_owner: User,
        *,
        viewer_user_id: int | None = None,
        owner_id: int | None = None,
        approved_follower: bool = False,
    ) -> bool:
        viewer_id = viewer_user_id if viewer_user_id is not None else getattr(viewer, "id", None)
        owner = owner_id if owner_id is not None else getattr(profile_owner, "id", None)
        if viewer_id is not None and viewer_id == owner:
            return True
        if viewer is not None and getattr(viewer, "role", "user") == "admin":
            return True
        if profile_owner.profile_visibility == "public":
            return True
        if profile_owner.profile_visibility == "private":
            return bool(approved_follower)
        return False

    def can_view_followers(self, viewer: User | None, profile_owner: User, *, viewer_user_id: int | None = None, owner_id: int | None = None, approved_follower: bool = False) -> bool:
        return self.can_view_profile(viewer, profile_owner, viewer_user_id=viewer_user_id, owner_id=owner_id, approved_follower=approved_follower)

    def can_view_following(self, viewer: User | None, profile_owner: User, *, viewer_user_id: int | None = None, owner_id: int | None = None, approved_follower: bool = False) -> bool:
        return self.can_view_profile(viewer, profile_owner, viewer_user_id=viewer_user_id, owner_id=owner_id, approved_follower=approved_follower)

    def is_blocked(self, blocker_id: int | None, blocked_id: int | None) -> bool:
        return blocker_id is not None and blocked_id is not None and blocker_id == blocked_id

    def can_edit_post(self, user: User | None, post: Post | None) -> bool:
        if user is None or post is None:
            return False
        return user.id == post.author_id or getattr(user, "role", "user") == "admin"

    def can_delete_post(self, user: User | None, post: Post | None) -> bool:
        return self.can_edit_post(user, post)


def can_view_post(*args, **kwargs) -> bool:
    return PrivacyPolicy().can_view_post(*args, **kwargs)
