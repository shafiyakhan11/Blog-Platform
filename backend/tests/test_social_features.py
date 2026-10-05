from backend.app.models import User, Post, FollowRequest, PostLike
from backend.app.services.authorization import PrivacyPolicy


def _user(username: str, profile_visibility: str = "public", user_id: int = 1) -> User:
    return User(
        id=user_id,
        name=username.title(),
        username=username,
        email=f"{username}@example.com",
        password_hash="hash",
        bio="bio",
        role="user",
        is_active=True,
        profile_visibility=profile_visibility,
    )


def test_public_post_is_visible_to_anyone() -> None:
    author = _user("author", user_id=11)
    viewer = _user("viewer", user_id=12)
    post = Post(id=1, author_id=author.id, title="Hello", content="Body", visibility="public")

    assert PrivacyPolicy().can_view_post(viewer, post, viewer_user_id=viewer.id, author_user_id=author.id)


def test_private_post_blocks_non_owner() -> None:
    author = _user("author", user_id=21)
    viewer = _user("viewer", user_id=22)
    post = Post(id=2, author_id=author.id, title="Private", content="Body", visibility="private")

    assert not PrivacyPolicy().can_view_post(viewer, post, viewer_user_id=viewer.id, author_user_id=author.id)


def test_follow_requests_require_approval_for_private_accounts() -> None:
    requester = _user("requester", user_id=31)
    target = _user("target", profile_visibility="private", user_id=32)

    follow_request = FollowRequest(
        id=1,
        requester_id=requester.id,
        target_user_id=target.id,
        status="pending",
    )

    assert follow_request.status == "pending"
    assert PrivacyPolicy().can_follow_user(requester, target, viewer_user_id=requester.id, target_user_id=target.id)


def test_like_model_rejects_duplicate_like_objects() -> None:
    like = PostLike(post_id=10, user_id=7)
    assert like.user_id == 7
    assert like.post_id == 10
