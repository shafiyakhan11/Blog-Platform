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
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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
    monkeypatch.setattr(settings, "google_client_id", "test-google-client-id")
    yield TestClient(app)
    app.dependency_overrides.clear()
    app.dependency_overrides.update(existing_overrides)
    engine.dispose()


def test_google_auth_creates_and_reuses_user(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    claims = {
        "email": "google-user@example.com",
        "email_verified": True,
        "name": "Google User",
    }

    def verify_google_credential(_credential: str, _client_id: str) -> dict[str, object]:
        return claims

    monkeypatch.setattr("app.main.verify_google_credential", verify_google_credential)

    first_response = client.post("/api/auth/google", json={"credential": "valid-google-credential"})
    assert first_response.status_code == 200, first_response.text
    first_result = first_response.json()
    assert first_result["user"]["email"] == claims["email"]
    assert first_result["user"]["name"] == claims["name"]
    assert first_result["access_token"]

    second_response = client.post("/api/auth/google", json={"credential": "valid-google-credential"})
    assert second_response.status_code == 200, second_response.text
    assert second_response.json()["user"]["id"] == first_result["user"]["id"]


def test_google_auth_rejects_unverified_email(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    claims = {"email": "unverified@example.com", "email_verified": False}

    def verify_google_credential(_credential: str, _client_id: str) -> dict[str, object]:
        return claims

    monkeypatch.setattr("app.main.verify_google_credential", verify_google_credential)

    response = client.post("/api/auth/google", json={"credential": "google-credential"})

    assert response.status_code == 401
    assert "verified email" in response.json()["detail"]


def test_google_auth_requires_client_configuration(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "google_client_id", None)

    response = client.post("/api/auth/google", json={"credential": "google-credential"})

    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]
