"""Auth ile ilgili istek/yanıt şemaları."""

from __future__ import annotations

import re

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import UserOut

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class RegisterRequest(BaseModel):
    """Yeni işletme kaydı: Restaurant + owner User birlikte oluşturulur."""

    restaurant_name: str = Field(min_length=2, max_length=120)
    slug: str | None = Field(default=None, max_length=80)
    owner_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("slug")
    @classmethod
    def _validate_slug(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().lower()
        if not _SLUG_RE.match(v):
            raise ValueError("slug yalnızca küçük harf, rakam ve tire içerebilir")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(TokenPair):
    """Kayıt/giriş sonrası: tokenlar + kullanıcı bilgisi."""

    user: UserOut
