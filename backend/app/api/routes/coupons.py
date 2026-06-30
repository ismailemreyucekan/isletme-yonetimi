"""Kupon uçları: listele, oluştur, sil (yönetici)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import (
    DbSession,
    require_feature,
    require_manager,
    require_staff,
)
from app.core.features import Feature
from app.models.restaurant import Restaurant
from app.models.user import User
from app.schemas.coupon import CouponCreate, CouponOut
from app.services import coupon_service
from app.services.coupon_service import CouponError

router = APIRouter(prefix="/coupons", tags=["coupons"])

RequireStaff = Annotated[User, Depends(require_staff)]
RequireManager = Annotated[User, Depends(require_manager)]
RequireCoupons = Annotated[Restaurant, Depends(require_feature(Feature.COUPONS))]


@router.get("", response_model=list[CouponOut])
async def list_coupons(
    db: DbSession, restaurant: RequireCoupons, _: RequireStaff
) -> list[CouponOut]:
    coupons = await coupon_service.list_coupons(db, restaurant.id)
    return [CouponOut.model_validate(c) for c in coupons]


@router.post("", response_model=CouponOut, status_code=status.HTTP_201_CREATED)
async def create_coupon(
    data: CouponCreate, db: DbSession, restaurant: RequireCoupons, _: RequireManager
) -> CouponOut:
    try:
        coupon = await coupon_service.create_coupon(
            db, restaurant.id, data.code, data.mode, data.value, data.is_active
        )
    except CouponError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return CouponOut.model_validate(coupon)


@router.delete("/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_coupon(
    coupon_id: uuid.UUID,
    db: DbSession,
    restaurant: RequireCoupons,
    _: RequireManager,
) -> None:
    try:
        await coupon_service.delete_coupon(db, restaurant.id, coupon_id)
    except CouponError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
