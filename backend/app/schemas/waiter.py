"""Garson çağrısı şemaları."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CallWaiterRequest(BaseModel):
    note: str | None = Field(default=None, max_length=255)


class WaiterCallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    table_id: uuid.UUID
    table_name: str | None = None
    status: str
    note: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None


class CallWaiterResponse(BaseModel):
    status: str = "ok"
    message: str = "Garson çağrıldı"
