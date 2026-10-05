import os
from pathlib import Path

db_path = Path("test_auth.db")
if db_path.exists():
    db_path.unlink()
os.environ["DATABASE_URL"] = "sqlite:///./test_auth.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

engine = create_engine("sqlite:///./test_auth.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_register_login_refresh_and_me():
    payload = {
        "name": "Jane Doe",
        "username": "janedoe",
        "email": "jane@example.com",
        "password": "securepass1",
    }

    register = client.post("/api/v1/auth/register", json=payload)
    assert register.status_code == 201, register.text
    tokens = register.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200, me.text
    assert me.json()["email"] == payload["email"]

    login = client.post(
        "/api/v1/auth/login",
        json={"username": payload["username"], "password": payload["password"]},
    )
    assert login.status_code == 200, login.text

    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refreshed.status_code == 200, refreshed.text
    refreshed_tokens = refreshed.json()
    assert refreshed_tokens["refresh_token"]

    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refreshed_tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {refreshed_tokens['access_token']}"},
    )
    assert logout.status_code == 200, logout.text


def test_invalid_login_fails():
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "doesnotexist", "password": "wrongpass"},
    )
    assert response.status_code == 401


def test_legacy_auth_requires_existing_user_and_eight_character_password():
    missing_user = client.post(
        "/api/auth",
        json={"mode": "login", "email": "missing@example.com", "password": "longpass8"},
    )
    assert missing_user.status_code == 401
    assert "check both" in missing_user.json()["detail"].lower()

    short_password = client.post(
        "/api/auth",
        json={"mode": "login", "email": "missing@example.com", "password": "short"},
    )
    assert short_password.status_code == 422


def test_legacy_auth_registers_and_verifies_database_credentials():
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN followers INTEGER NOT NULL DEFAULT 0"))
        connection.execute(text("ALTER TABLE users ADD COLUMN following INTEGER NOT NULL DEFAULT 0"))

    payload = {
        "mode": "signup",
        "name": "Test Author",
        "email": "legacy-auth@example.com",
        "password": "longpass8",
    }
    registered = client.post("/api/auth", json=payload)
    assert registered.status_code == 200, registered.text
    assert registered.json()["user"]["email"] == payload["email"]
    assert registered.json()["user"]["bio"] == ""

    with engine.begin() as connection:
        connection.execute(
            text("UPDATE users SET bio = :bio, followers = 37, following = 12 WHERE email = :email"),
            {"bio": "A database-backed bio", "email": payload["email"]},
        )

    wrong_password = client.post(
        "/api/auth",
        json={"mode": "login", "email": payload["email"], "password": "wrongpass8"},
    )
    assert wrong_password.status_code == 401

    login = client.post(
        "/api/auth",
        json={"mode": "login", "email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200, login.text
    assert login.json()["access_token"]
    assert login.json()["user"]["bio"] == "A database-backed bio"
    assert login.json()["user"]["followers"] == 37
    assert login.json()["user"]["following"] == 12


def test_profile_save_updates_existing_user_bio():
    payload = {
        "mode": "signup",
        "name": "Profile Author",
        "email": "profile-save@example.com",
        "password": "longpass8",
    }
    registered = client.post("/api/auth", json=payload)
    assert registered.status_code == 200, registered.text

    saved = client.put(
        "/api/profile",
        json={"bio": "Updated bio from profile editor"},
        headers={"Authorization": f"Bearer {registered.json()['access_token']}"},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["bio"] == "Updated bio from profile editor"

    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT id, bio FROM users WHERE email = :email"),
            {"email": payload["email"]},
        ).mappings().all()
    assert len(rows) == 1
    assert rows[0]["bio"] == "Updated bio from profile editor"
