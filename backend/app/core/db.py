"""Async SQLAlchemy engine & session yönetimi."""

from collections.abc import AsyncGenerator
from urllib.parse import urlsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def _connect_args(url: str) -> dict:
    """Uzak Postgres (Neon/Supabase vb.) SSL ister; yerel/Docker DB istemez."""
    host = (urlsplit(url).hostname or "").lower()
    is_local = host in ("localhost", "127.0.0.1", "db", "")
    if is_local:
        return {}
    # Uzak DB (Neon) — SSL şart. Neon'un pooler'ı (PgBouncer, transaction mode)
    # hazır sorgu (prepared statement) önbelleğini desteklemez; asyncpg'de bunu
    # kapatmazsak "prepared statement" hataları / bağlantı sorunları çıkar.
    return {"ssl": True, "statement_cache_size": 0}


engine = create_async_engine(
    settings.database_url,
    # SQL echo kapalı: uzak DB'de (Neon) her sorguyu log'a basmak gereksiz yük
    # ve gürültü yaratıyordu. (Önceden echo=settings.debug idi.)
    echo=False,
    pool_pre_ping=True,
    future=True,
    connect_args=_connect_args(settings.database_url),
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — istek başına bir DB oturumu sağlar."""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
