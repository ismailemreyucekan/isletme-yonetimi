"""Auth iş mantığı: işletme kaydı, kullanıcı doğrulama, token üretimi."""

from __future__ import annotations

import re
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.restaurant import Restaurant
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest, TokenPair

_DEFAULT_SETTINGS: dict[str, object] = {
    "self_order_enabled": False,
    "service_charge_enabled": False,
    "service_charge_rate": 0,
    "tip_enabled": True,
    "currency": "TRY",
    "languages": ["tr"],
}


class AuthError(Exception):
    """Servis katmanı auth hatası — route katmanı HTTP'ye çevirir."""


def _slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "isletme"


async def _unique_slug(db: AsyncSession, base: str) -> str:
    slug = base
    suffix = 1
    while True:
        exists = await db.scalar(select(Restaurant.id).where(Restaurant.slug == slug))
        if exists is None:
            return slug
        suffix += 1
        slug = f"{base}-{suffix}"


def issue_tokens(user: User) -> TokenPair:
    claims = {"rid": str(user.restaurant_id), "role": user.role.value}
    return TokenPair(
        access_token=create_access_token(str(user.id), **claims),
        refresh_token=create_refresh_token(str(user.id), **claims),
    )


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    return await db.scalar(select(User).where(func.lower(User.email) == email.lower()))


async def register_restaurant(db: AsyncSession, data: RegisterRequest) -> User:
    """Yeni işletme + owner kullanıcı oluşturur. Owner kullanıcıyı döner."""
    if await get_user_by_email(db, data.email) is not None:
        raise AuthError("Bu e-posta zaten kayıtlı")

    base_slug = data.slug or _slugify(data.restaurant_name)
    slug = await _unique_slug(db, base_slug)

    restaurant = Restaurant(
        name=data.restaurant_name,
        slug=slug,
        plan="free",
        settings=dict(_DEFAULT_SETTINGS),
    )
    db.add(restaurant)
    await db.flush()  # restaurant.id üret

    owner = User(
        restaurant_id=restaurant.id,
        name=data.owner_name,
        email=str(data.email).lower(),
        password_hash=hash_password(data.password),
        role=UserRole.OWNER,
        is_active=True,
    )
    db.add(owner)
    await db.commit()
    await db.refresh(owner)
    return owner


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(db, email)
    if user is None or not verify_password(password, user.password_hash):
        raise AuthError("E-posta veya parola hatalı")
    if not user.is_active:
        raise AuthError("Hesap pasif durumda")
    return user


async def get_user_for_refresh(db: AsyncSession, user_id: str, token_rid: str) -> User:
    try:
        uid = uuid.UUID(user_id)
    except (ValueError, TypeError) as exc:
        raise AuthError("Geçersiz token") from exc
    user = await db.get(User, uid)
    if user is None or not user.is_active or str(user.restaurant_id) != str(token_rid):
        raise AuthError("Geçersiz token")
    return user
