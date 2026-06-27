"""Menü kategori ve ürün şemaları."""

from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# --- MenuCategory ---

class MenuCategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    sort_order: int = 0
    is_active: bool = True


class MenuCategoryCreate(MenuCategoryBase):
    pass


class MenuCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    sort_order: int | None = None
    is_active: bool | None = None


class MenuCategoryOut(MenuCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    restaurant_id: uuid.UUID


# --- MenuItem ---

class MenuItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    price: Decimal = Field(gt=0, decimal_places=2)
    image_url: str | None = None
    is_available: bool = True
    sort_order: int = 0


class MenuItemCreate(MenuItemBase):
    category_id: uuid.UUID


class MenuItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    image_url: str | None = None
    is_available: bool | None = None
    sort_order: int | None = None
    category_id: uuid.UUID | None = None


class MenuItemOut(MenuItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    restaurant_id: uuid.UUID
    category_id: uuid.UUID
