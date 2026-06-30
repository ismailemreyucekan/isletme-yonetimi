"""Garson çağrısı (WaiterCall) — müşterinin QR ekranından personeli masaya çağırması.

Kalıcı kaydedilir; böylece o an ekrana bakan kimse olmasa bile çağrı kaybolmaz,
personel paneline düşer. Anlık bildirim ayrıca realtime hub üzerinden yayınlanır.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.table import Table


class WaiterCallStatus(enum.StrEnum):
    PENDING = "pending"
    RESOLVED = "resolved"


class WaiterCall(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "waiter_calls"

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    table_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tables.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[WaiterCallStatus] = mapped_column(
        Enum(WaiterCallStatus, native_enum=False),
        default=WaiterCallStatus.PENDING,
        nullable=False,
        index=True,
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    table: Mapped[Table] = relationship()

    def __repr__(self) -> str:  # pragma: no cover
        return f"<WaiterCall {self.table_id} {self.status}>"
