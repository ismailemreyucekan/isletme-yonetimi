"""Ürün opsiyonu (modifier) şemaları."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ModifierBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    price_delta: Decimal = Field(default=0)
    is_available: bool = True
    sort_order: int = 0


class ModifierCreate(ModifierBase):
    pass


class ModifierUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    price_delta: Decimal | None = None
    is_available: bool | None = None
    sort_order: int | None = None


class ModifierOut(ModifierBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    modifier_group_id: uuid.UUID


class ModifierGroupBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    selection_type: Literal["single", "multiple"] = "single"
    min_select: int = Field(default=0, ge=0)
    max_select: int = Field(default=1, ge=1)
    is_required: bool = False
    sort_order: int = 0
    is_active: bool = True


class ModifierGroupCreate(ModifierGroupBase):
    modifiers: list[ModifierCreate] = Field(default_factory=list)


class ModifierGroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    selection_type: Literal["single", "multiple"] | None = None
    min_select: int | None = Field(default=None, ge=0)
    max_select: int | None = Field(default=None, ge=1)
    is_required: bool | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class ModifierGroupOut(ModifierGroupBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    restaurant_id: uuid.UUID
    modifiers: list[ModifierOut] = Field(default_factory=list)


class AssignGroupsRequest(BaseModel):
    """Bir ürüne bağlı opsiyon gruplarının tam listesi (replace)."""

    group_ids: list[uuid.UUID]
