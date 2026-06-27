"""FastAPI uygulama giriş noktası."""

from __future__ import annotations

import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.router import api_router
from app.core.config import settings

API_PREFIX = "/api/v1"

# Yüklenen görsellerin saklandığı dizin (bkz. routes/uploads.py).
UPLOAD_DIR = pathlib.Path("/app/uploads")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Gerçek zamanlı hub (WebSocket + Redis pub/sub) başlat/kapat (bkz. PLAN §7).
    from app.realtime import hub

    await hub.start()
    try:
        yield
    finally:
        await hub.stop()


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{settings.app_name} API",
        version="0.1.0",
        description="Restoran/Kafe Kasa & QR Ödeme Sistemi — multi-tenant API",
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=API_PREFIX)

    # Yüklenen görselleri /api/v1/media altında servis et (frontend /api proxy'si halleder).
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    app.mount(
        f"{API_PREFIX}/media",
        StaticFiles(directory=str(UPLOAD_DIR)),
        name="media",
    )

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "environment": settings.environment,
            "version": __version__,
        }

    return app


app = create_app()
