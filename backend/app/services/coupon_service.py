"""Kupon iş mantığı: CRUD + koda göre arama."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coupon import Coupon, CouponMode


class CouponError(Exception):
    """Kupon işlemlerinde iş kuralı hatası."""


async def list_coupons(db: AsyncSession, restaurant_id: uuid.UUID) -> list[Coupon]:
    result = await db.execute(
        select(Coupon)
        .where(Coupon.restaurant_id == restaurant_id)
        .order_by(Coupon.created_at.desc())
    )
    return list(result.scalars())


async def get_coupon_by_code(
    db: AsyncSession, restaurant_id: uuid.UUID, code: str
) -> Coupon | None:
    result = await db.execute(
        select(Coupon).where(
            Coupon.restaurant_id == restaurant_id,
            func.lower(Coupon.code) == code.strip().lower(),
        )
    )
    return result.scalar_one_or_none()


async def create_coupon(
    db: AsyncSession,
    restaurant_id: uuid.UUID,
    code: str,
    mode: str,
    value: Decimal | float | int,
    is_active: bool = True,
) -> Coupon:
    if await get_coupon_by_code(db, restaurant_id, code) is not None:
        raise CouponError("Bu kupon kodu zaten var")

    coupon = Coupon(
        restaurant_id=restaurant_id,
        code=code.strip(),
        mode=CouponMode(mode),
        value=Decimal(str(value)),
        is_active=is_active,
    )
    db.add(coupon)
    await db.commit()
    await db.refresh(coupon)
    return coupon


async def delete_coupon(
    db: AsyncSession, restaurant_id: uuid.UUID, coupon_id: uuid.UUID
) -> None:
    coupon = await db.get(Coupon, coupon_id)
    if coupon is None or coupon.restaurant_id != restaurant_id:
        raise CouponError("Kupon bulunamadı")
    await db.delete(coupon)
    await db.commit()
