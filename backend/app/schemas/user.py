"""User şemaları."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr


class UserCreate(UserBase):
    """Mevcut bir işletmeye personel ekleme (owner/manager tarafından)."""

    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.WAITER


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    restaurant_id: uuid.UUID
    role: UserRole
    is_active: bool
    created_at: datetime
