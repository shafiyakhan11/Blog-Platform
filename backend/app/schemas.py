from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    username: str = Field(..., min_length=3, max_length=40)
    email: EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Username is required")
        if not cleaned.replace("_", "").isalnum():
            raise ValueError("Username may only contain letters, numbers, and underscores")
        return cleaned


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    username: str
    email: str
    role: str
    is_active: bool
    is_verified: bool


class UserCreate(BaseModel):
    name: str
    username: str
    email: str
    password: str
    bio: str = ""


class UserLogin(BaseModel):
    email: str
    password: str


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    name: str
    bio: str | None = None
    profile_visibility: str = "public"
    followers_count: int = 0
    following_count: int = 0
    post_count: int = 0
    is_following: bool = False
    is_followed_by: bool = False


class PostCreate(BaseModel):
    title: str
    content: str
    excerpt: str | None = None
    status: str = "published"
    visibility: str = "public"


class PostUpdate(PostCreate):
    pass


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


class SuccessResponse(BaseModel):
    success: bool = True
    data: dict[str, Any]
