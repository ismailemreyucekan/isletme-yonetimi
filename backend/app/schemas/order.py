"""Sipariş şemaları."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OrderItemModifierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name_snapshot: str
    price_delta_snapshot: Decimal


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    menu_item_id: uuid.UUID | None
    name_snapshot: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal
    note: str | None
    paid_status: str
    modifiers: list[OrderItemModifierOut] = Field(default_factory=list)


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    restaurant_id: uuid.UUID
    table_id: uuid.UUID | None
    source: str
    status: str
    subtotal: Decimal
    discount_amount: Decimal
    service_charge_rate: Decimal
    service_charge_amount: Decimal
    total: Decimal
    paid_total: Decimal
    opened_at: datetime
    closed_at: datetime | None
    items: list[OrderItemOut] = []


class OpenOrderRequest(BaseModel):
    table_id: uuid.UUID | None = None
    source: str = "dine_in"


class AddItemRequest(BaseModel):
    menu_item_id: uuid.UUID
    quantity: int = Field(default=1, ge=1)
    note: str | None = None
    modifier_ids: list[uuid.UUID] = Field(default_factory=list)


class UpdateItemRequest(BaseModel):
    quantity: int = Field(ge=1)


class CloseOrderRequest(BaseModel):
    # Nakit/kart ile manuel kapatma; tutar verilmezse kalan tamamı kapanır.
    method: str = "cash"
    tip_amount: Decimal = Field(default=0, ge=0)


class PayItemsRequest(BaseModel):
    """Belirli satırları öde (kendi yediğini öde)."""

    item_ids: list[uuid.UUID]
    method: str = "cash"
    tip_amount: Decimal = Field(default=0, ge=0)


class SplitPayRequest(BaseModel):
    """Hesabı kişi sayısına böl, bir payı öde."""

    parts: int = Field(ge=2, description="Toplam kişi sayısı")
    method: str = "cash"
    tip_amount: Decimal = Field(default=0, ge=0)


class SetDiscountRequest(BaseModel):
    """Hesaba indirim uygula. mode=percent → value yüzde, mode=amount → value ₺.

    value=0 indirimi kaldırır.
    """

    mode: Literal["percent", "amount"]
    value: Decimal = Field(ge=0)


class SetServiceChargeRequest(BaseModel):
    """Hesaba servis ücreti oranı (%) uygula. rate=0 servis ücretini kaldırır."""

    rate: Decimal = Field(ge=0, le=100)
