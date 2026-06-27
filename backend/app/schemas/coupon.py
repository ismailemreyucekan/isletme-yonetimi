"""Kupon şemaları."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CouponCreate(BaseModel):
    code: str = Field(min_length=1, max_length=40)
    mode: Literal["percent", "amount"]
    value: Decimal = Field(ge=0)
    is_active: bool = True


class CouponOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    restaurant_id: uuid.UUID
    code: str
    mode: str
    value: Decimal
    is_active: bool
    created_at: datetime


class ApplyCouponRequest(BaseModel):
    code: str = Field(min_length=1, max_length=40)
