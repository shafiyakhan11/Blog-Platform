from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DraftFlow"
    environment: str = "development"
    database_url: str = "postgresql://postgres:98989898@localhost:5432/blog_portal"
    jwt_secret_key: str = "8dbc02a04f075ef24b3956f33df9285f31ef1c680ac612bdba39dda06c03498d"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    google_client_id: str = "725546861080-vk2fg53a890kcbk7jvsuqpj19ttsoqlo.apps.googleusercontent.com"
    google_client_secret: str = "YOUR_GOOGLE_CLIENT_SECRET"
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    allow_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
