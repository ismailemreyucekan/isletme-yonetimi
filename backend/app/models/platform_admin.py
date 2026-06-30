"""PlatformAdmin = platform (SaaS sağlayıcı) yöneticisi.

Bir işletmeye (Restaurant) bağlı DEĞİLDİR. Tüm kiracıları görüp ayarlarını ve
özellik bayraklarını yönetebilen, ayrı bir kimlik/giriş akışı olan üst düzey
hesaptır. Personel (User) ile karıştırılmamalıdır.
"""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class PlatformAdmin(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "platform_admins"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<PlatformAdmin {self.email!r}>"
