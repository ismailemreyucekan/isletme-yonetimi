"""Kupon (Coupon) modeli — işletme bazlı indirim kodu (bkz. PLAN §6.3, Faz 2)."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, ForeignKey, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class CouponMode(enum.StrEnum):
    PERCENT = "percent"
    AMOUNT = "amount"


class Coupon(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "coupons"
    __table_args__ = (UniqueConstraint("restaurant_id", "code", name="uq_coupon_code"),)

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    mode: Mapped[CouponMode] = mapped_column(
        SAEnum(CouponMode, native_enum=False), nullable=False
    )
    value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Coupon {self.code!r} {self.mode}={self.value}>"
