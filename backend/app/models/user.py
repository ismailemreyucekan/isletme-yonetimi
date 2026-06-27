"""User = personel (owner / manager / cashier / waiter)."""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant


class UserRole(enum.StrEnum):
    OWNER = "owner"
    MANAGER = "manager"
    CASHIER = "cashier"
    WAITER = "waiter"


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    restaurant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("restaurants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # E-posta MVP'de global benzersiz (bir e-posta = bir hesap).
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", values_callable=lambda e: [m.value for m in e]),
        default=UserRole.WAITER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    restaurant: Mapped[Restaurant] = relationship(back_populates="users")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email!r} ({self.role.value})>"
