"""Platform admin paneli şemaları."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime


class AdminTokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AdminAuthResponse(AdminTokenPair):
    admin: AdminOut


class AdminRefreshRequest(BaseModel):
    refresh_token: str


class AdminRestaurantOut(BaseModel):
    """Admin panelinde işletme satırı — sahibi ve çözülmüş özelliklerle birlikte."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    plan: str
    settings: dict[str, Any] = Field(default_factory=dict)
    features: dict[str, bool] = Field(default_factory=dict)
    user_count: int = 0
    owner_email: str | None = None
    created_at: datetime


class FeatureCatalogItem(BaseModel):
    key: str
    label: str
    description: str


class FeatureUpdateRequest(BaseModel):
    """Tek bir işletmenin özellik override'larını günceller.

    Yalnızca gönderilen anahtarlar değişir; `null` verilen anahtar override'dan
    kaldırılır (plan/varsayılana döner).
    """

    features: dict[str, bool | None]


class PlanUpdateRequest(BaseModel):
    plan: str
