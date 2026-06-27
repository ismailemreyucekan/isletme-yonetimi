"""KDS (mutfak ekranı) şemaları."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class KdsItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name_snapshot: str
    quantity: int
    note: str | None
    kitchen_status: str


class KdsTicket(BaseModel):
    """Bir masanın mutfağa düşen sipariş fişi."""

    order_id: uuid.UUID
    table_name: str | None
    source: str
    opened_at: datetime
    items: list[KdsItem]


class SetKitchenStatusRequest(BaseModel):
    kitchen_status: str  # new | preparing | ready | served
