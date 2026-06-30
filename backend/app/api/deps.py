"""Ortak FastAPI dependency'leri: auth + tenant (kiracı) çözümleme + rol kontrolü.

Kiracı izolasyonunun kalbi burası: her kimliği doğrulanan istekte aktif
`Restaurant` JWT'deki `rid` claim'inden çözülür ve kullanıcının gerçekten o
kiracıya ait olduğu doğrulanır (bkz. PLAN §4, §10).
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Coroutine
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.features import Feature, is_enabled
from app.core.security import decode_token
from app.models.platform_admin import PlatformAdmin
from app.models.restaurant import Restaurant
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer(auto_error=True)

DbSession = Annotated[AsyncSession, Depends(get_db)]

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Geçersiz veya süresi dolmuş kimlik bilgisi",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except jwt.PyJWTError as exc:
        raise _CREDENTIALS_EXC from exc

    if payload.get("type") != "access":
        raise _CREDENTIALS_EXC

    subject = payload.get("sub")
    if not subject:
        raise _CREDENTIALS_EXC
    try:
        user_id = uuid.UUID(subject)
    except (ValueError, TypeError) as exc:
        raise _CREDENTIALS_EXC from exc

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXC

    # Token'daki kiracı ile kullanıcının kiracısı tutarlı olmalı.
    token_rid = payload.get("rid")
    if token_rid is None or str(user.restaurant_id) != str(token_rid):
        raise _CREDENTIALS_EXC

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_restaurant(db: DbSession, user: CurrentUser) -> Restaurant:
    """Aktif kiracıyı döner. Tüm tenant-scoped sorgular bunun id'siyle filtrelenir."""
    restaurant = await db.get(Restaurant, user.restaurant_id)
    if restaurant is None:
        raise _CREDENTIALS_EXC
    return restaurant


CurrentRestaurant = Annotated[Restaurant, Depends(get_current_restaurant)]


def require_roles(
    *roles: UserRole,
) -> Callable[[User], Coroutine[Any, Any, User]]:
    """Belirli rollere sahip kullanıcıları zorunlu kılan dependency üretir."""
    allowed = set(roles)

    async def _checker(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için yetkiniz yok",
            )
        return user

    return _checker


# Kullanışlı kısayollar
require_owner = require_roles(UserRole.OWNER)
require_manager = require_roles(UserRole.OWNER, UserRole.MANAGER)
require_staff = require_roles(
    UserRole.OWNER, UserRole.MANAGER, UserRole.CASHIER, UserRole.WAITER
)


def require_feature(
    feature: Feature,
) -> Callable[[Restaurant], Coroutine[Any, Any, Restaurant]]:
    """Tenant uçlarında bir opsiyonel modülün açık olmasını zorunlu kılar.

    Kapalıysa 403 döner; çağıran kullanıcı zaten o işletmenin personelidir, bu
    yüzden özelliğin varlığını gizlemeye gerek yok (bkz. public uçlarda 404).
    """

    async def _check(restaurant: CurrentRestaurant) -> Restaurant:
        if not is_enabled(restaurant, feature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu özellik işletmeniz için kapalı",
            )
        return restaurant

    return _check


# ── Platform admin (SaaS yöneticisi) ─────────────────────────────────────────

_ADMIN_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Geçersiz veya süresi dolmuş yönetici kimliği",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_admin(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> PlatformAdmin:
    """Aktif platform yöneticisini token'dan çözer.

    Token `scope="platform"` claim'i taşımalıdır; personel token'ları kabul
    edilmez (bkz. admin_service.ADMIN_SCOPE).
    """
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except jwt.PyJWTError as exc:
        raise _ADMIN_CREDENTIALS_EXC from exc

    if payload.get("type") != "access" or payload.get("scope") != "platform":
        raise _ADMIN_CREDENTIALS_EXC

    subject = payload.get("sub")
    if not subject:
        raise _ADMIN_CREDENTIALS_EXC
    try:
        admin_id = uuid.UUID(subject)
    except (ValueError, TypeError) as exc:
        raise _ADMIN_CREDENTIALS_EXC from exc

    admin = await db.get(PlatformAdmin, admin_id)
    if admin is None or not admin.is_active:
        raise _ADMIN_CREDENTIALS_EXC

    return admin


CurrentAdmin = Annotated[PlatformAdmin, Depends(get_current_admin)]
