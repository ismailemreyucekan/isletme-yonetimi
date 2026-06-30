"""Tüm route modüllerini tek bir API router altında toplar."""

from fastapi import APIRouter

from app.api.routes import (
    admin,
    auth,
    coupons,
    kds,
    menu,
    modifiers,
    orders,
    public,
    tables,
    uploads,
    waiter_calls,
)

api_router = APIRouter()
api_router.include_router(admin.router)
api_router.include_router(auth.router)
api_router.include_router(menu.router)
api_router.include_router(tables.router)
api_router.include_router(orders.router)
api_router.include_router(modifiers.router)
api_router.include_router(coupons.router)
api_router.include_router(uploads.router)
api_router.include_router(public.router)
api_router.include_router(kds.router)
api_router.include_router(waiter_calls.router)
