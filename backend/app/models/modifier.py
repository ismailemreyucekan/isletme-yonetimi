"""Ürün opsiyonları (modifiers) modelleri — bkz. PLAN §6.1.

ModifierGroup ("Boy", "Süt tipi") ─< Modifier ("Büyük +15₺").
Bir grup çoka-çok ile birden çok ürüne bağlanır (MenuItemModifierGroup).
Sipariş anında seçilenler OrderItemModifier olarak ad+fiyatla donar (snapshot).
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Uuid,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.order import OrderItem


class SelectionType(enum.StrEnum):
    SINGLE = "single"  # radio — biri seçilir
    MULTIPLE = "multiple"  # checkbox — birden çok


class ModifierGroup(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "modifier_groups"

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    selection_type: Mapped[SelectionType] = mapped_column(
        SAEnum(SelectionType, native_enum=False),
        default=SelectionType.SINGLE,
        nullable=False,
    )
    min_select: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_select: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    modifiers: Mapped[list[Modifier]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="Modifier.sort_order",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ModifierGroup {self.name!r}>"


class Modifier(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "modifiers"

    modifier_group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("modifier_groups.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    price_delta: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    group: Mapped[ModifierGroup] = relationship(back_populates="modifiers")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Modifier {self.name!r} +{self.price_delta}>"


class MenuItemModifierGroup(Base):
    """Ürün ↔ opsiyon grubu (çoka-çok). Bir grup birçok üründe kullanılır."""

    __tablename__ = "menu_item_modifier_groups"

    menu_item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("menu_items.id", ondelete="CASCADE"), primary_key=True
    )
    modifier_group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("modifier_groups.id", ondelete="CASCADE"), primary_key=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class OrderItemModifier(UUIDMixin, TimestampMixin, Base):
    """Sipariş satırında seçilen opsiyonun snapshot'ı (ad + fiyat donar)."""

    __tablename__ = "order_item_modifiers"

    order_item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("order_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    modifier_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("modifiers.id", ondelete="SET NULL"), nullable=True
    )
    name_snapshot: Mapped[str] = mapped_column(String(80), nullable=False)
    price_delta_snapshot: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    order_item: Mapped[OrderItem] = relationship(back_populates="modifiers")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<OrderItemModifier {self.name_snapshot!r}>"
