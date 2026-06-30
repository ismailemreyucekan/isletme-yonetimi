"""İlk platform yöneticisini (PlatformAdmin) oluşturan/güncelleyen CLI.

Kullanım (backend dizininde, venv aktifken):

    python -m app.scripts.create_admin --email admin@kasa.app --name "Yönetici"

Parola argüman olarak verilebilir (--password) ya da istenirse ortamdan
ADMIN_PASSWORD okunur; ikisi de yoksa güvenli şekilde sorulur.

E-posta zaten varsa parolası güncellenir (yeniden çalıştırmak güvenlidir).
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import os

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models.platform_admin import PlatformAdmin
from app.services.admin_service import get_admin_by_email


async def _run(email: str, name: str, password: str) -> None:
    async with SessionLocal() as db:
        existing = await get_admin_by_email(db, email)
        if existing is not None:
            existing.name = name
            existing.password_hash = hash_password(password)
            existing.is_active = True
            await db.commit()
            print(f"✓ Mevcut yönetici güncellendi: {email}")
            return

        admin = PlatformAdmin(
            name=name,
            email=email.lower(),
            password_hash=hash_password(password),
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print(f"✓ Yönetici oluşturuldu: {email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Platform yöneticisi oluştur")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="Platform Yöneticisi")
    parser.add_argument("--password", default=None)
    args = parser.parse_args()

    password = args.password or os.getenv("ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Parola: ")
    if len(password) < 8:
        parser.error("Parola en az 8 karakter olmalı")

    asyncio.run(_run(args.email, args.name, password))


if __name__ == "__main__":
    main()
