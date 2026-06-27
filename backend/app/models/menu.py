"""Menü modelleri: MenuCategory ve MenuItem."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.modifier import ModifierGroup
    from app.models.restaurant import Restaurant


class MenuCategory(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "menu_categories"

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    restaurant: Mapped[Restaurant] = relationship(back_populates="menu_categories")
    items: Mapped[list[MenuItem]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MenuCategory {self.name!r}>"


class MenuItem(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "menu_items"

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("menu_categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    category: Mapped[MenuCategory] = relationship(back_populates="items")
    # Okuma amaçlı (atama servis katmanında MenuItemModifierGroup satırlarıyla yönetilir).
    modifier_groups: Mapped[list[ModifierGroup]] = relationship(
        secondary="menu_item_modifier_groups",
        order_by="ModifierGroup.sort_order",
        viewonly=True,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MenuItem {self.name!r}>"
