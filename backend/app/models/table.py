"""Masa (Table) modeli."""

from __future__ import annotations

import secrets
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.restaurant import Restaurant


def generate_qr_token() -> str:
    """Tahmin edilemez masa QR token'ı (bkz. PLAN §10)."""
    return secrets.token_urlsafe(24)


class Table(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "tables"

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    qr_token: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False, default=generate_qr_token
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    restaurant: Mapped[Restaurant] = relationship(back_populates="tables")
    orders: Mapped[list[Order]] = relationship(
        back_populates="table", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Table {self.name!r}>"
