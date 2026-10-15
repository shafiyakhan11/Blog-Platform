from __future__ import annotations

import json
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.core.config import settings


def test_migration_preserves_legacy_posts_and_comments(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "legacy.sqlite"
    database_url = f"sqlite:///{database_path.as_posix()}"
    legacy_engine = create_engine(database_url)
    with legacy_engine.begin() as connection:
        connection.execute(
            text("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    username VARCHAR(150) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    bio TEXT,
                    followers INTEGER NOT NULL DEFAULT 0,
                    following INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        connection.execute(
            text("""
                CREATE TABLE posts (
                    id VARCHAR(100) PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    excerpt TEXT,
                    content TEXT NOT NULL,
                    author VARCHAR(255) NOT NULL,
                    author_handle VARCHAR(255) NOT NULL,
                    avatar VARCHAR(255) NOT NULL,
                    tags JSON NOT NULL,
                    published_date TEXT NOT NULL,
                    read_time INTEGER NOT NULL DEFAULT 1,
                    likes INTEGER NOT NULL DEFAULT 0,
                    views INTEGER NOT NULL DEFAULT 0,
                    shares INTEGER NOT NULL DEFAULT 0,
                    trending_score INTEGER NOT NULL DEFAULT 0,
                    is_bookmarked BOOLEAN NOT NULL DEFAULT 0,
                    is_followed BOOLEAN NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        connection.execute(
            text("""
                CREATE TABLE comments (
                    id VARCHAR(100) PRIMARY KEY,
                    post_id VARCHAR(100) NOT NULL,
                    parent_id VARCHAR(100),
                    author VARCHAR(255) NOT NULL,
                    avatar VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    likes INTEGER NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
        )
        connection.execute(
            text("""
                INSERT INTO users (id, name, username, email, password_hash)
                VALUES (7, 'Legacy Author', 'legacy-author', 'legacy@example.com', 'hash')
            """)
        )
        connection.execute(
            text("""
                INSERT INTO posts (
                    id, title, excerpt, content, author, author_handle, avatar, tags,
                    published_date, read_time
                ) VALUES (
                    'legacy-post-01', 'Saved post', 'Saved excerpt', 'Saved content',
                    'Legacy Author', '@legacy-author', 'LA', :tags, 'June 1, 2026', 3
                )
            """),
            {"tags": json.dumps(["legacy"])},
        )
        connection.execute(
            text("""
                INSERT INTO comments (id, post_id, author, avatar, content)
                VALUES ('legacy-comment-01', 'legacy-post-01', 'Legacy Reader', 'LR', 'Saved comment')
            """)
        )
    legacy_engine.dispose()

    monkeypatch.setattr(settings, "database_url", database_url)
    backend_dir = Path(__file__).resolve().parents[1]
    config_path = backend_dir / "alembic.ini"
    config = Config(str(config_path))
    config.set_main_option("script_location", str(backend_dir / "alembic"))
    command.upgrade(config, "head")

    migrated_engine = create_engine(database_url)
    with migrated_engine.connect() as connection:
        post = connection.execute(
            text("SELECT id, title, content, author, author_id, status, visibility FROM posts")
        ).mappings().one()
        comment = connection.execute(
            text("SELECT id, post_id, content, parent_id, user_id FROM comments")
        ).mappings().one()
        assert post["id"] == "legacy-post-01"
        assert post["content"] == "Saved content"
        assert post["author"] == "Legacy Author"
        assert post["author_id"] is None
        assert post["status"] == "published"
        assert post["visibility"] == "public"
        assert comment["id"] == "legacy-comment-01"
        assert comment["content"] == "Saved comment"
        assert comment["parent_id"] is None
        assert comment["user_id"] is None
        assert connection.execute(text("SELECT id FROM users")).scalar_one() == 7
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "20261001_legacy_schema_compat"

    columns = {column["name"] for column in inspect(migrated_engine).get_columns("users")}
    assert {"role", "is_active", "profile_visibility", "updated_at"} <= columns
    migrated_engine.dispose()


def test_migration_creates_complete_schema_for_a_fresh_database(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "fresh.sqlite"
    database_url = f"sqlite:///{database_path.as_posix()}"
    monkeypatch.setattr(settings, "database_url", database_url)
    backend_dir = Path(__file__).resolve().parents[1]
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("script_location", str(backend_dir / "alembic"))

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    inspector = inspect(engine)
    assert {"users", "posts", "comments", "follows", "user_post_likes", "post_bookmarks", "password_reset_tokens"} <= set(inspector.get_table_names())
    user_columns = {column["name"] for column in inspector.get_columns("users")}
    assert {"role", "is_active", "is_verified", "profile_visibility", "updated_at"} <= user_columns
    with engine.begin() as connection:
        user_id = connection.execute(
            text("""
                INSERT INTO users (name, username, email, password_hash)
                VALUES ('Fresh User', 'fresh-user', 'fresh@example.com', 'hash')
                RETURNING id
            """)
        ).scalar_one()
    assert user_id == 1
    engine.dispose()
