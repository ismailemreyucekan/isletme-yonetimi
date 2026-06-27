"""Restaurant şemaları."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RestaurantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    plan: str
    settings: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
