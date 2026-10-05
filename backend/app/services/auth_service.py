from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, verify_password, hash_password
from app.models import RefreshToken, User
from app.repositories.user_repository import UserRepository
from app.schemas import LoginRequest, RegisterRequest, TokenPair


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def register(self, payload: RegisterRequest) -> TokenPair:
        if self.users.get_by_email(payload.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")
        if self.users.get_by_username(payload.username):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is already taken")

        user = User(
            name=payload.name.strip(),
            username=payload.username.strip(),
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            role="user",
            is_active=True,
            is_verified=False,
        )
        self.users.create(user)

        access_token = create_access_token(str(user.id), user.role)
        refresh_token = create_refresh_token(str(user.id), user.role)
        self._store_refresh_token(user.id, refresh_token)
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def login(self, payload: LoginRequest) -> TokenPair:
        user = self.users.get_by_email_or_username(payload.username)
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is disabled")

        access_token = create_access_token(str(user.id), user.role)
        refresh_token = create_refresh_token(str(user.id), user.role)
        self._store_refresh_token(user.id, refresh_token)
        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def refresh(self, refresh_token: str) -> TokenPair:
        token = self._validate_refresh_token(refresh_token)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user = self.users.get_by_id(token.user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

        access_token = create_access_token(str(user.id), user.role)
        new_refresh_token = create_refresh_token(str(user.id), user.role)
        token.revoked_at = datetime.now(timezone.utc)
        self.db.add(token)
        self._store_refresh_token(user.id, new_refresh_token)
        self.db.commit()
        return TokenPair(access_token=access_token, refresh_token=new_refresh_token)

    def logout(self, user_id: int, refresh_token: Optional[str] = None) -> None:
        if not refresh_token:
            self.db.query(RefreshToken).filter(RefreshToken.user_id == user_id).update({"revoked_at": datetime.now(timezone.utc)})
            self.db.commit()
            return

        token_hash = self._hash_token(refresh_token)
        db_token = self.db.query(RefreshToken).filter(RefreshToken.user_id == user_id, RefreshToken.token_hash == token_hash).first()
        if db_token:
            db_token.revoked_at = datetime.now(timezone.utc)
            self.db.commit()

    def get_current_user(self, user_id: int) -> User:
        user = self.users.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user

    def _store_refresh_token(self, user_id: int, raw_token: str) -> RefreshToken:
        token_hash = self._hash_token(raw_token)
        record = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def _validate_refresh_token(self, raw_token: str) -> Optional[RefreshToken]:
        token_hash = self._hash_token(raw_token)
        return (
            self.db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash, RefreshToken.revoked_at.is_(None))
            .first()
        )

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
