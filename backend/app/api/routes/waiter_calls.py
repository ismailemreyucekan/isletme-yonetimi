"""Personel uçları: bekleyen garson çağrılarını listele ve kapat."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentRestaurant, DbSession, require_staff
from app.models.user import User
from app.schemas.waiter import WaiterCallOut
from app.services import waiter_service
from app.services.waiter_service import WaiterCallError

router = APIRouter(prefix="/waiter-calls", tags=["waiter-calls"])

RequireStaff = Annotated[User, Depends(require_staff)]


def _to_out(call) -> WaiterCallOut:
    return WaiterCallOut(
        id=call.id,
        table_id=call.table_id,
        table_name=call.table.name if call.table else None,
        status=call.status.value if hasattr(call.status, "value") else str(call.status),
        note=call.note,
        created_at=call.created_at,
        resolved_at=call.resolved_at,
    )


@router.get("", response_model=list[WaiterCallOut])
async def list_pending(
    db: DbSession, restaurant: CurrentRestaurant, _: RequireStaff
) -> list[WaiterCallOut]:
    calls = await waiter_service.list_pending(db, restaurant.id)
    return [_to_out(c) for c in calls]


@router.post("/{call_id}/resolve", response_model=WaiterCallOut)
async def resolve_call(
    call_id: uuid.UUID,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireStaff,
) -> WaiterCallOut:
    try:
        call = await waiter_service.resolve(db, restaurant.id, call_id)
    except WaiterCallError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    # resolve sonrası table ilişkisi yüklü olmayabilir; çıktı için tekrar yükle.
    return _to_out(call)
