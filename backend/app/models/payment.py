"""Ödeme kaydı (Payment) modeli."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class PaymentMethod(enum.StrEnum):
    CASH = "cash"
    CARD = "card"
    ONLINE = "online"


class PaymentStatus(enum.StrEnum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class SplitType(enum.StrEnum):
    FULL = "full"
    ITEMS = "items"
    EQUAL = "equal"


class Payment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "payments"

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    tip_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, native_enum=False), nullable=False
    )
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False), default=PaymentStatus.SUCCESS, nullable=False
    )
    split_type: Mapped[SplitType] = mapped_column(
        Enum(SplitType, native_enum=False), default=SplitType.FULL, nullable=False
    )
    provider_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Payment {self.amount} {self.method}>"
