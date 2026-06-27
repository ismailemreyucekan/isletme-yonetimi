"""Restaurant = kiracı (tenant) / hesap."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.menu import MenuCategory
    from app.models.table import Table
    from app.models.user import User

# PostgreSQL'de JSONB, diğer (test/sqlite) ortamlarda generic JSON kullan.
JSONType = JSON().with_variant(JSONB(), "postgresql")


class Restaurant(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "restaurants"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(40), default="free", nullable=False)

    # İşletme ayarları & özellik bayrakları (bkz. PLAN §6.3)
    settings: Mapped[dict[str, Any]] = mapped_column(
        JSONType, default=dict, nullable=False
    )

    users: Mapped[list[User]] = relationship(
        back_populates="restaurant", cascade="all, delete-orphan"
    )
    menu_categories: Mapped[list[MenuCategory]] = relationship(
        back_populates="restaurant", cascade="all, delete-orphan"
    )
    tables: Mapped[list[Table]] = relationship(
        back_populates="restaurant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Restaurant {self.slug!r}>"
