"""Masa şemaları."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class TableBase(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    sort_order: int = 0


class TableCreate(TableBase):
    pass


class TableUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    sort_order: int | None = None


class TableOut(TableBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    restaurant_id: uuid.UUID
    qr_token: str


class TableWithStatus(TableOut):
    """Masa + aktif sipariş özeti (masa planı için)."""

    status: str  # "empty" | "occupied"
    active_order_id: uuid.UUID | None = None
    active_total: float = 0
    active_paid_total: float = 0
