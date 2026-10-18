from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DraftFlow"
    environment: str = "development"
    database_url: str # "******localhost:5432/blog_portal"
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    google_client_id: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    frontend_url: str | None = None
    cors_origins: str = "http://localhost:5173,http://localhost:3000,https://draftflow.netlify.app/"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allow_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_production_configuration(self) -> Settings:
        if self.environment.lower() in {"production", "prod"}:
            if len(self.jwt_secret_key) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters in production")
            if not self.database_url.startswith(("postgresql://", "postgresql+psycopg://")):
                raise ValueError("DATABASE_URL must use PostgreSQL in production")
            if not self.database_url or "localhost" in self.database_url or "127.0.0.1" in self.database_url:
                raise ValueError("DATABASE_URL must point to a non-local database in production")
            if not self.allow_origins or "*" in self.allow_origins:
                raise ValueError("CORS_ORIGINS must contain explicit production origins")
            if any(
                urlparse(origin).scheme != "https"
                or not urlparse(origin).netloc
                or urlparse(origin).path
                or urlparse(origin).hostname in {"localhost", "127.0.0.1"}
                for origin in self.allow_origins
            ):
                raise ValueError("CORS_ORIGINS must contain only HTTPS production origins")
            if not self.smtp_host or not self.smtp_from_email or not self.frontend_url:
                raise ValueError("SMTP_HOST, SMTP_FROM_EMAIL, and FRONTEND_URL are required in production")
            frontend = urlparse(self.frontend_url)
            if frontend.scheme != "https" or not frontend.netloc or frontend.path:
                raise ValueError("FRONTEND_URL must be an HTTPS origin in production")
            if self.frontend_url.rstrip("/") not in self.allow_origins:
                raise ValueError("FRONTEND_URL must also be listed in CORS_ORIGINS")
            if bool(self.smtp_username) != bool(self.smtp_password):
                raise ValueError("SMTP_USERNAME and SMTP_PASSWORD must be set together")
        return self


settings = Settings()
