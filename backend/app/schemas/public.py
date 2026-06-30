"""Müşteri (anonim) tarafı şemaları."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.menu import MenuCategoryOut, MenuItemOut
from app.schemas.order import OrderOut


class PublicRestaurant(BaseModel):
    name: str
    slug: str
    currency: str = "TRY"


class PublicTableView(BaseModel):
    """QR ile açılan müşteri görünümü: işletme + masa + aktif hesap."""

    restaurant: PublicRestaurant
    table_name: str
    order: OrderOut | None = None


class PublicMenuView(BaseModel):
    restaurant: PublicRestaurant
    categories: list[MenuCategoryOut]
    items: list[MenuItemOut]


class PublicTableListItem(BaseModel):
    name: str
    qr_token: str
    status: str  # "empty" | "occupied"


class PublicTableList(BaseModel):
    restaurant: PublicRestaurant
    tables: list[PublicTableListItem]


class PublicPayItemsRequest(BaseModel):
    item_ids: list[str]


class PublicSplitRequest(BaseModel):
    parts: int


class PublicOrderLine(BaseModel):
    menu_item_id: str
    quantity: int = 1
    modifier_ids: list[str] = []


class PublicOrderRequest(BaseModel):
    items: list[PublicOrderLine]
