from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(autoflush=False, bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    existing_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(settings, "jwt_secret_key", "test-secret-that-is-long-enough-for-hmac")
    yield TestClient(app)
    app.dependency_overrides.clear()
    app.dependency_overrides.update(existing_overrides)
    engine.dispose()


def _create_user(client: TestClient, *, name: str, email: str) -> tuple[int, str]:
    response = client.post(
        "/api/auth",
        json={"mode": "signup", "name": name, "email": email, "password": "safe-password-123"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    return body["user"]["id"], body["access_token"]


def test_publish_read_interact_and_persist(client: TestClient) -> None:
    _, author_token = _create_user(client, name="Post Author", email="author@example.com")
    _, reader_token = _create_user(client, name="Post Reader", email="reader@example.com")
    author_headers = {"Authorization": f"Bearer {author_token}"}
    reader_headers = {"Authorization": f"Bearer {reader_token}"}

    created = client.post(
        "/api/v1/posts",
        headers=author_headers,
        json={
            "id": "migration-safe-post-01",
            "title": "A persisted post",
            "excerpt": "A short summary",
            "content": "This post must survive a read from the feed.",
            "tags": ["testing"],
            "publishedDate": "June 1, 2026",
            "readTime": 2,
        },
    )
    assert created.status_code == 200, created.text
    assert created.json()["data"]["id"] == "migration-safe-post-01"

    feed = client.get("/api/posts", headers=reader_headers)
    assert feed.status_code == 200, feed.text
    post = next(item for item in feed.json() if item["id"] == "migration-safe-post-01")
    assert post["author"] == "Post Author"
    assert post["content"] == "This post must survive a read from the feed."

    like = client.post("/api/v1/posts/migration-safe-post-01/like", headers=reader_headers)
    assert like.status_code == 200, like.text
    bookmark = client.post("/api/v1/posts/migration-safe-post-01/bookmark", headers=reader_headers)
    assert bookmark.status_code == 200, bookmark.text
    follow = client.post("/api/v1/posts/migration-safe-post-01/follow", headers=reader_headers)
    assert follow.status_code == 200, follow.text
    share = client.post("/api/v1/posts/migration-safe-post-01/share", headers=reader_headers)
    assert share.status_code == 200, share.text

    comment = client.post(
        "/api/v1/posts/migration-safe-post-01/comments",
        headers=reader_headers,
        json={"content": "A saved comment", "parentId": None},
    )
    assert comment.status_code == 200, comment.text
    comment_id = comment.json()["data"]["id"]
    comment_like = client.post(f"/api/v1/comments/{comment_id}/like", headers=author_headers)
    assert comment_like.status_code == 200, comment_like.text
    assert comment_like.json()["data"]["liked"] is True
    comment_unlike = client.post(f"/api/v1/comments/{comment_id}/like", headers=author_headers)
    assert comment_unlike.status_code == 200, comment_unlike.text
    assert comment_unlike.json()["data"]["liked"] is False
    comment_relike = client.post(f"/api/v1/comments/{comment_id}/like", headers=author_headers)
    assert comment_relike.status_code == 200, comment_relike.text
    assert comment_relike.json()["data"]["liked"] is True

    refreshed_feed = client.get("/api/posts", headers=reader_headers)
    saved_post = next(item for item in refreshed_feed.json() if item["id"] == "migration-safe-post-01")
    assert saved_post["likes"] == 1
    assert saved_post["is_liked"] is True
    assert saved_post["is_bookmarked"] is True
    assert saved_post["is_followed"] is True
    assert saved_post["shares"] == 1
    assert saved_post["comments"][0]["content"] == "A saved comment"
    assert saved_post["comments"][0]["likes"] == 1
    assert saved_post["comments"][0]["author"] == "Post Reader"
    assert saved_post["comments"][0]["is_liked"] is False
    author_feed = client.get("/api/posts", headers=author_headers)
    author_post = next(item for item in author_feed.json() if item["id"] == "migration-safe-post-01")
    assert author_post["comments"][0]["is_liked"] is True


def test_comment_cannot_be_attached_to_another_posts_thread(client: TestClient) -> None:
    _, author_token = _create_user(client, name="Thread Author", email="thread-author@example.com")
    _, reader_token = _create_user(client, name="Thread Reader", email="thread-reader@example.com")
    headers = {"Authorization": f"Bearer {author_token}"}
    post_ids = ("thread-post-one", "thread-post-two")
    for post_id in post_ids:
        response = client.post(
            "/api/v1/posts",
            headers=headers,
            json={"id": post_id, "title": post_id, "content": "Content"},
        )
        assert response.status_code == 200, response.text

    comment = client.post(
        f"/api/v1/posts/{post_ids[0]}/comments",
        headers={"Authorization": f"Bearer {reader_token}"},
        json={"content": "First thread"},
    )
    assert comment.status_code == 200, comment.text

    cross_post_reply = client.post(
        f"/api/v1/posts/{post_ids[1]}/comments",
        headers={"Authorization": f"Bearer {reader_token}"},
        json={"content": "Wrong thread", "parentId": comment.json()["data"]["id"]},
    )
    assert cross_post_reply.status_code == 404


def test_password_reset_is_single_use_and_updates_credentials(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _create_user(client, name="Reset Author", email="reset@example.com")
    monkeypatch.setattr(settings, "smtp_host", "smtp.test")
    monkeypatch.setattr(settings, "smtp_from_email", "no-reply@example.com")
    monkeypatch.setattr(settings, "frontend_url", "https://draftflow.test")
    sent: dict[str, str] = {}

    def capture_email(recipient: str, token: str) -> None:
        sent["recipient"] = recipient
        sent["token"] = token

    monkeypatch.setattr("app.main.send_password_reset_email", capture_email)
    requested = client.post("/api/auth/password/forgot", json={"email": "reset@example.com"})
    assert requested.status_code == 200, requested.text
    assert "token" not in requested.text.lower()
    assert sent["recipient"] == "reset@example.com"

    reset = client.post(
        "/api/auth/password/reset",
        json={"token": sent["token"], "password": "new-safe-password-123"},
    )
    assert reset.status_code == 200, reset.text
    assert client.post(
        "/api/auth/password/reset",
        json={"token": sent["token"], "password": "another-safe-password-123"},
    ).status_code == 400

    login = client.post(
        "/api/auth",
        json={"mode": "login", "email": "reset@example.com", "password": "new-safe-password-123"},
    )
    assert login.status_code == 200, login.text
