"""İşletme ana sayfası (dashboard) özet şemaları."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class ActiveOrderSummary(BaseModel):
    order_id: uuid.UUID
    table_id: uuid.UUID | None = None
    table_name: str | None = None
    source: str
    total: float = 0
    paid_total: float = 0
    remaining: float = 0
    opened_at: datetime


class DashboardSummary(BaseModel):
    total_tables: int = 0
    occupied_tables: int = 0
    empty_tables: int = 0
    active_orders: int = 0

    # Açık (henüz kapanmamış) hesapların toplamları
    open_total: float = 0
    open_paid: float = 0
    open_remaining: float = 0

    # Bugünün tahsilatı (başarılı ödemeler)
    today_revenue: float = 0
    today_tips: float = 0
    today_payments: int = 0

    active_order_list: list[ActiveOrderSummary] = []
