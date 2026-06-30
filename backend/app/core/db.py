"""Async SQLAlchemy engine & session yönetimi."""

from collections.abc import AsyncGenerator
from urllib.parse import urlsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def _connect_args(url: str) -> dict:
    """Uzak Postgres (Neon/Supabase vb.) SSL ister; yerel/Docker DB istemez."""
    host = (urlsplit(url).hostname or "").lower()
    is_local = host in ("localhost", "127.0.0.1", "db", "")
    return {} if is_local else {"ssl": True}


engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
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
