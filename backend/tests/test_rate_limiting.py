from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


def test_default_rate_limit_returns_429_after_limit() -> None:
    client = TestClient(app, client=(f"rate-limit-test-{uuid4()}", 54321))

    responses = [client.get("/api/health") for _ in range(6)]

    assert all(response.status_code == 200 for response in responses[:5])
    assert responses[5].status_code == 429


def test_authentication_rate_limit_returns_429_after_limit() -> None:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(autoflush=False, bind=engine)

    def override_get_db():
        with testing_session() as db:
            yield db

    existing_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app, client=(f"auth-rate-limit-test-{uuid4()}", 54321)) as client:
            responses = [
                client.post(
                    "/api/v1/auth/login",
                    json={"username": "missing-user", "password": "wrong-password"},
                )
                for _ in range(6)
            ]
        assert all(response.status_code == 401 for response in responses[:5])
        assert responses[5].status_code == 429
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(existing_overrides)
        engine.dispose()
