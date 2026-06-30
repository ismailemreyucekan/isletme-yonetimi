"""Platform admin uçları — SaaS yöneticisi için işletme & özellik yönetimi.

Bu uçlar yalnızca platform yöneticisi token'ı (scope=platform) ile erişilir;
personel/owner token'ları kabul edilmez (bkz. deps.get_current_admin).
"""

from __future__ import annotations

import uuid

import jwt
from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentAdmin, DbSession
from app.core.features import Feature
from app.core.security import decode_token
from app.schemas.admin import (
    AdminAuthResponse,
    AdminLoginRequest,
    AdminOut,
    AdminRefreshRequest,
    AdminRestaurantOut,
    AdminTokenPair,
    FeatureCatalogItem,
    FeatureUpdateRequest,
    PlanUpdateRequest,
)
from app.services import admin_service
from app.services.admin_service import AdminError

router = APIRouter(prefix="/admin", tags=["admin"])

# Özellik kataloğu — frontend'in etiket/açıklama göstermesi için.
_FEATURE_CATALOG: list[FeatureCatalogItem] = [
    FeatureCatalogItem(
        key=Feature.QR_MENU.value,
        label="QR Menü",
        description="Müşterilerin QR ile menüyü görüp masadan sipariş vermesi.",
    ),
    FeatureCatalogItem(
        key=Feature.ONLINE_PAYMENT.value,
        label="Online Ödeme",
        description="Müşterinin QR üzerinden hesabı online ödemesi (tüm / ürün / böl).",
    ),
    FeatureCatalogItem(
        key=Feature.KDS.value,
        label="Mutfak Ekranı (KDS)",
        description="Siparişlerin mutfak ekranında canlı görüntülenmesi.",
    ),
    FeatureCatalogItem(
        key=Feature.COUPONS.value,
        label="Kupon / İndirim",
        description="Kupon kodu ve indirim uygulama modülü.",
    ),
]


@router.post("/login", response_model=AdminAuthResponse)
async def admin_login(data: AdminLoginRequest, db: DbSession) -> AdminAuthResponse:
    try:
        admin = await admin_service.authenticate_admin(db, data.email, data.password)
    except AdminError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    tokens = admin_service.issue_admin_tokens(admin)
    return AdminAuthResponse(**tokens.model_dump(), admin=AdminOut.model_validate(admin))


@router.post("/refresh", response_model=AdminTokenPair)
async def admin_refresh(data: AdminRefreshRequest, db: DbSession) -> AdminTokenPair:
    try:
        payload = decode_token(data.refresh_token)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz token"
        ) from exc

    if payload.get("type") != "refresh" or payload.get("scope") != "platform":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz token türü"
        )

    try:
        admin = await admin_service.get_admin_for_refresh(db, payload.get("sub", ""))
    except AdminError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    return admin_service.issue_admin_tokens(admin)


@router.get("/me", response_model=AdminOut)
async def admin_me(admin: CurrentAdmin) -> AdminOut:
    return AdminOut.model_validate(admin)


@router.get("/features", response_model=list[FeatureCatalogItem])
async def feature_catalog(_: CurrentAdmin) -> list[FeatureCatalogItem]:
    """Yönetilebilir opsiyonel özelliklerin kataloğu."""
    return _FEATURE_CATALOG


@router.get("/restaurants", response_model=list[AdminRestaurantOut])
async def list_restaurants(
    _: CurrentAdmin, db: DbSession
) -> list[AdminRestaurantOut]:
    rows = await admin_service.list_restaurants(db)
    return [AdminRestaurantOut.model_validate(r) for r in rows]


async def _get_or_404(db: DbSession, restaurant_id: uuid.UUID):
    try:
        return await admin_service.get_restaurant(db, restaurant_id)
    except AdminError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/restaurants/{restaurant_id}/features", response_model=AdminRestaurantOut)
async def update_features(
    restaurant_id: uuid.UUID,
    data: FeatureUpdateRequest,
    _: CurrentAdmin,
    db: DbSession,
) -> AdminRestaurantOut:
    restaurant = await _get_or_404(db, restaurant_id)
    try:
        restaurant = await admin_service.update_features(db, restaurant, data.features)
    except AdminError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return _to_admin_row(restaurant)


@router.patch("/restaurants/{restaurant_id}/plan", response_model=AdminRestaurantOut)
async def update_plan(
    restaurant_id: uuid.UUID,
    data: PlanUpdateRequest,
    _: CurrentAdmin,
    db: DbSession,
) -> AdminRestaurantOut:
    restaurant = await _get_or_404(db, restaurant_id)
    restaurant = await admin_service.update_plan(db, restaurant, data.plan)
    return _to_admin_row(restaurant)


def _to_admin_row(restaurant) -> AdminRestaurantOut:
    """Tekil güncelleme yanıtı — liste uçundaki ek alanlar (user_count vb.) burada
    gereksiz; sıfır/None ile döneriz, frontend listeyi yeniden çeker."""
    return AdminRestaurantOut(
        id=restaurant.id,
        name=restaurant.name,
        slug=restaurant.slug,
        plan=restaurant.plan,
        settings=restaurant.settings or {},
        features=restaurant.features,
        user_count=0,
        owner_email=None,
        created_at=restaurant.created_at,
    )
