"""Sipariş (Order) ve sipariş satırı (OrderItem) modelleri."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.modifier import OrderItemModifier
    from app.models.payment import Payment
    from app.models.table import Table


class OrderStatus(enum.StrEnum):
    OPEN = "open"
    PAID = "paid"
    CLOSED = "closed"


class OrderSource(enum.StrEnum):
    DINE_IN = "dine_in"
    TAKEAWAY = "takeaway"
    QR_SELF_ORDER = "qr_self_order"


class PaidStatus(enum.StrEnum):
    UNPAID = "unpaid"
    LOCKED = "locked"
    PAID = "paid"


class KitchenStatus(enum.StrEnum):
    NEW = "new"
    PREPARING = "preparing"
    READY = "ready"
    SERVED = "served"


class Order(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "orders"

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    table_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("tables.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source: Mapped[OrderSource] = mapped_column(
        Enum(OrderSource, native_enum=False), default=OrderSource.DINE_IN, nullable=False
    )
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False), default=OrderStatus.OPEN, nullable=False, index=True
    )

    # Para alanları (bkz. PLAN §5, §6.2)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    discount_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    # Servis ücreti/kuver: oran sipariş açılışında ayarlardan snapshot'lanır,
    # tutar ara toplam üzerinden her hesaplamada yeniden bulunur (bkz. PLAN §6.2).
    service_charge_rate: Mapped[float] = mapped_column(
        Numeric(5, 2), default=0, server_default="0", nullable=False
    )
    service_charge_amount: Mapped[float] = mapped_column(
        Numeric(10, 2), default=0, server_default="0", nullable=False
    )
    total: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    paid_total: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    table: Mapped[Table | None] = relationship(back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    payments: Mapped[list[Payment]] = relationship(cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Order {self.id} {self.status}>"


class OrderItem(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "order_items"

    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    menu_item_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("menu_items.id", ondelete="SET NULL"), nullable=True
    )
    # Snapshot: menü sonradan değişse de geçmiş hesap bozulmaz (bkz. PLAN §5)
    name_snapshot: Mapped[str] = mapped_column(String(150), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    line_total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    paid_status: Mapped[PaidStatus] = mapped_column(
        Enum(PaidStatus, native_enum=False), default=PaidStatus.UNPAID, nullable=False
    )
    kitchen_status: Mapped[KitchenStatus] = mapped_column(
        Enum(KitchenStatus, native_enum=False),
        default=KitchenStatus.NEW,
        nullable=False,
        index=True,
    )

    order: Mapped[Order] = relationship(back_populates="items")
    modifiers: Mapped[list[OrderItemModifier]] = relationship(
        back_populates="order_item", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<OrderItem {self.name_snapshot!r} x{self.quantity}>"
