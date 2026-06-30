"""Platform admin iş mantığı: kimlik doğrulama, token üretimi, işletme yönetimi.

Admin token'ları personel (User) token'larından `scope="platform"` claim'i ile
ayrılır; böylece bir admin token'ı yanlışlıkla tenant uçlarında kabul edilmez.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.features import Feature
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.models.platform_admin import PlatformAdmin
from app.models.restaurant import Restaurant
from app.models.user import User, UserRole
from app.schemas.admin import AdminTokenPair

ADMIN_SCOPE = "platform"

# Geçerli özellik anahtarları — admin override'larında doğrulama için.
VALID_FEATURE_KEYS = {f.value for f in Feature}


class AdminError(Exception):
    """Admin servis katmanı hatası — route katmanı HTTP'ye çevirir."""


def issue_admin_tokens(admin: PlatformAdmin) -> AdminTokenPair:
    claims = {"scope": ADMIN_SCOPE}
    return AdminTokenPair(
        access_token=create_access_token(str(admin.id), **claims),
        refresh_token=create_refresh_token(str(admin.id), **claims),
    )


async def get_admin_by_email(db: AsyncSession, email: str) -> PlatformAdmin | None:
    return await db.scalar(
        select(PlatformAdmin).where(func.lower(PlatformAdmin.email) == email.lower())
    )


async def authenticate_admin(
    db: AsyncSession, email: str, password: str
) -> PlatformAdmin:
    admin = await get_admin_by_email(db, email)
    if admin is None or not verify_password(password, admin.password_hash):
        raise AdminError("E-posta veya parola hatalı")
    if not admin.is_active:
        raise AdminError("Hesap pasif durumda")
    return admin


async def get_admin_for_refresh(db: AsyncSession, admin_id: str) -> PlatformAdmin:
    try:
        aid = uuid.UUID(admin_id)
    except (ValueError, TypeError) as exc:
        raise AdminError("Geçersiz token") from exc
    admin = await db.get(PlatformAdmin, aid)
    if admin is None or not admin.is_active:
        raise AdminError("Geçersiz token")
    return admin


async def list_restaurants(db: AsyncSession) -> list[dict]:
    """Tüm işletmeleri kullanıcı sayısı ve owner e-postasıyla birlikte döner."""
    restaurants = (
        await db.scalars(select(Restaurant).order_by(Restaurant.created_at.desc()))
    ).all()

    rows: list[dict] = []
    for r in restaurants:
        user_count = await db.scalar(
            select(func.count(User.id)).where(User.restaurant_id == r.id)
        )
        owner_email = await db.scalar(
            select(User.email)
            .where(User.restaurant_id == r.id, User.role == UserRole.OWNER)
            .order_by(User.created_at)
            .limit(1)
        )
        rows.append(
            {
                "id": r.id,
                "name": r.name,
                "slug": r.slug,
                "plan": r.plan,
                "settings": r.settings or {},
                "features": r.features,
                "user_count": user_count or 0,
                "owner_email": owner_email,
                "created_at": r.created_at,
            }
        )
    return rows


async def get_restaurant(db: AsyncSession, restaurant_id: uuid.UUID) -> Restaurant:
    restaurant = await db.get(Restaurant, restaurant_id)
    if restaurant is None:
        raise AdminError("İşletme bulunamadı")
    return restaurant


async def update_features(
    db: AsyncSession,
    restaurant: Restaurant,
    changes: dict[str, bool | None],
) -> Restaurant:
    """İşletmenin özellik override'larını günceller.

    `True/False` override ekler/değiştirir; `None` override'ı kaldırır (özellik
    plan/varsayılana döner).
    """
    invalid = set(changes) - VALID_FEATURE_KEYS
    if invalid:
        raise AdminError(f"Geçersiz özellik anahtarı: {', '.join(sorted(invalid))}")

    # JSON alanı mutasyonunu SQLAlchemy'nin algılaması için yeni dict ata.
    settings = dict(restaurant.settings or {})
    overrides = dict(settings.get("features", {}))

    for key, value in changes.items():
        if value is None:
            overrides.pop(key, None)
        else:
            overrides[key] = bool(value)

    settings["features"] = overrides
    restaurant.settings = settings

    await db.commit()
    await db.refresh(restaurant)
    return restaurant


async def update_plan(
    db: AsyncSession, restaurant: Restaurant, plan: str
) -> Restaurant:
    restaurant.plan = plan
    await db.commit()
    await db.refresh(restaurant)
    return restaurant
