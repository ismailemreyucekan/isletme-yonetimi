"""KDS uçları: mutfak fişleri (REST) + canlı güncellemeler (WebSocket)."""

from __future__ import annotations

import uuid
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from app.api.deps import (
    DbSession,
    require_feature,
    require_staff,
)
from app.core.db import get_db
from app.core.features import Feature
from app.core.security import decode_token
from app.models.restaurant import Restaurant
from app.models.user import User
from app.realtime import hub
from app.schemas.kds import KdsItem, KdsTicket, SetKitchenStatusRequest
from app.services import kds_service
from app.services.kds_service import KdsError

router = APIRouter(prefix="/kds", tags=["kds"])

RequireStaff = Annotated[User, Depends(require_staff)]
RequireKds = Annotated[Restaurant, Depends(require_feature(Feature.KDS))]


@router.get("/tickets", response_model=list[KdsTicket])
async def list_tickets(
    db: DbSession, restaurant: RequireKds, _: RequireStaff
) -> list[KdsTicket]:
    orders = await kds_service.list_tickets(db, restaurant.id)
    tickets: list[KdsTicket] = []
    for o in orders:
        # Sadece mutfakta aktif kalemleri göster.
        items = [
            KdsItem.model_validate(i)
            for i in o.items
            if i.kitchen_status in kds_service.ACTIVE_KITCHEN
        ]
        tickets.append(
            KdsTicket(
                order_id=o.id,
                table_name=o.table.name if o.table else None,
                source=o.source.value if hasattr(o.source, "value") else str(o.source),
                opened_at=o.opened_at,
                items=items,
            )
        )
    return tickets


@router.patch("/items/{item_id}", response_model=KdsItem)
async def set_item_status(
    item_id: uuid.UUID,
    data: SetKitchenStatusRequest,
    db: DbSession,
    restaurant: RequireKds,
    _: RequireStaff,
) -> KdsItem:
    try:
        item = await kds_service.set_item_status(
            db, restaurant.id, item_id, data.kitchen_status
        )
    except KdsError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return KdsItem.model_validate(item)


@router.websocket("/ws")
async def kds_ws(websocket: WebSocket, token: str, topic: str = "kds") -> None:
    """Canlı mutfak/kasa kanalı. Auth: ?token=<access_token>&topic=kds|pos."""
    # WebSocket'te Authorization header güvenilmez; token query param ile gelir.
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if payload.get("type") != "access":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    rid = payload.get("rid")
    if not rid:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if topic not in ("kds", "pos"):
        topic = "kds"

    # Kullanıcı gerçekten bu kiracıya ait mi? (kısa doğrulama)
    async for db in get_db():
        user = await db.get(User, uuid.UUID(payload["sub"]))
        if user is None or not user.is_active or str(user.restaurant_id) != str(rid):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        break

    channel = hub.channel(str(rid), topic)
    await hub.connect(channel, websocket)
    try:
        while True:
            # İstemciden mesaj beklemiyoruz; bağlantıyı canlı tutmak için dinle.
            await websocket.receive_text()
    except WebSocketDisconnect:
        await hub.disconnect(channel, websocket)
    except Exception:
        await hub.disconnect(channel, websocket)
