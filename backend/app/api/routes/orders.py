"""Sipariş uçları: açma, ürün ekleme/çıkarma, ödeme, hesap kapatma."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentRestaurant, DbSession, require_staff
from app.models.user import User
from app.schemas.coupon import ApplyCouponRequest
from app.schemas.dashboard import DashboardSummary
from app.schemas.order import (
    AddItemRequest,
    CloseOrderRequest,
    OpenOrderRequest,
    OrderOut,
    PayItemsRequest,
    SetDiscountRequest,
    SetServiceChargeRequest,
    SplitPayRequest,
    UpdateItemRequest,
)
from app.services import coupon_service, order_service
from app.services.order_service import OrderError

router = APIRouter(prefix="/orders", tags=["orders"])

RequireStaff = Annotated[User, Depends(require_staff)]


def _bad(exc: OrderError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# NOT: "/summary" rotası "/{order_id}"den ÖNCE tanımlanmalı; aksi halde "summary"
# bir order_id (UUID) sanılıp 422 döner.
@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireStaff,
) -> DashboardSummary:
    """İşletme ana sayfası özeti: masa doluluğu, aktif siparişler, bugünkü ciro."""
    data = await order_service.dashboard_summary(db, restaurant.id)
    return DashboardSummary.model_validate(data)


@router.post("/open", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def open_order(
    data: OpenOrderRequest,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireStaff,
) -> OrderOut:
    try:
        order = await order_service.open_order(db, restaurant.id, data.table_id, data.source)
    except OrderError as exc:
        raise _bad(exc) from exc
    return OrderOut.model_validate(order)


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: uuid.UUID,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireStaff,
) -> OrderOut:
    try:
        order = await order_service.get_order(db, restaurant.id, order_id)
    except OrderError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return OrderOut.model_validate(order)


@router.post("/{order_id}/items", response_model=OrderOut)
async def add_item(
    order_id: uuid.UUID,
    data: AddItemRequest,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireStaff,
) -> OrderOut:
    try:
        order = await order_service.get_order(db, restaurant.id, order_id)
        order = await order_service.add_item(
            db, order, data.menu_item_id, data.quantity, data.note, data.modifier_ids
        )
    except OrderError as exc:
        raise _bad(exc) from exc
    return OrderOut.model_validate(order)


@router.patch("/{order_id}/items/{item_id}", response_model=OrderOut)
async def update_item(
    order_id: uuid.UUID,
    item_id: uuid.UUID,
    data: UpdateItemRequest,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireStaff,
) -> OrderOut:
    try:
        order = await order_service.get_order(db, restaurant.id, order_id)
        order = await order_service.update_item_quantity(db, order, item_id, data.quantity)
    except OrderError as exc:
        raise _bad(exc) from exc
    return OrderOut.model_validate(order)


@router.delete("/{order_id}/items/{item_id}", response_model=OrderOut)
async def remove_item(
    order_id: uuid.UUID,
    item_id: uuid.UUID,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireStaff,
) -> OrderOut:
    try:
        order = await order_service.get_order(db, restaurant.id, order_id)
        order = await order_service.remove_item(db, order, item_id)
    except OrderError as exc:
        raise _bad(exc) from exc
    return OrderOut.model_validate(order)


@router.post("/{order_id}/discount", response_model=OrderOut)
async def set_discount(
    order_id: uuid.UUID,
    data: SetDiscountRequest,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireStaff,
) -> OrderOut:
    try:
        order = await order_service.get_order(db, restaurant.id, order_id)
        order = await order_service.set_discount(db, order, data.mode, data.value)
    except OrderError as exc:
        raise _bad(exc) from exc
    return OrderOut.model_validate(order)


@router.post("/{order_id}/apply-coupon", response_model=OrderOut)
async def apply_coupon(
    order_id: uuid.UUID,
    data: ApplyCouponRequest,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireStaff,
) -> OrderOut:
    try:
        order = await order_service.get_order(db, restaurant.id, order_id)
        coupon = await coupon_service.get_coupon_by_code(db, restaurant.id, data.code)
        if coupon is None or not coupon.is_active:
            raise OrderError("Kupon bulunamadı veya pasif")
        order = await order_service.set_discount(db, order, coupon.mode.value, coupon.value)
    except OrderError as exc:
        raise _bad(exc) from exc
    return OrderOut.model_validate(order)


@router.post("/{order_id}/service-charge", response_model=OrderOut)
async def set_service_charge(
    order_id: uuid.UUID,
    data: SetServiceChargeRequest,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireStaff,
) -> OrderOut:
    try:
        order = await order_service.get_order(db, restaurant.id, order_id)
        order = await order_service.set_service_charge(db, order, data.rate)
    except OrderError as exc:
        raise _bad(exc) from exc
    return OrderOut.model_validate(order)


@router.post("/{order_id}/pay", response_model=OrderOut)
async def pay_full(
    order_id: uuid.UUID,
    data: CloseOrderRequest,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireStaff,
) -> OrderOut:
    try:
        order = await order_service.get_order(db, restaurant.id, order_id)
        order = await order_service.pay_full(db, order, data.method, data.tip_amount)
    except OrderError as exc:
        raise _bad(exc) from exc
    return OrderOut.model_validate(order)


@router.post("/{order_id}/pay-items", response_model=OrderOut)
async def pay_items(
    order_id: uuid.UUID,
    data: PayItemsRequest,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireStaff,
) -> OrderOut:
    try:
        order = await order_service.get_order(db, restaurant.id, order_id)
        order = await order_service.pay_items(
            db, order, data.item_ids, data.method, data.tip_amount
        )
    except OrderError as exc:
        raise _bad(exc) from exc
    return OrderOut.model_validate(order)


@router.post("/{order_id}/pay-split", response_model=OrderOut)
async def pay_split(
    order_id: uuid.UUID,
    data: SplitPayRequest,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireStaff,
) -> OrderOut:
    try:
        order = await order_service.get_order(db, restaurant.id, order_id)
        order = await order_service.pay_split(
            db, order, data.parts, data.method, data.tip_amount
        )
    except OrderError as exc:
        raise _bad(exc) from exc
    return OrderOut.model_validate(order)
