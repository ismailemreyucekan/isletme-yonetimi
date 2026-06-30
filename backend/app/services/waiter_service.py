"""Garson çağrısı iş mantığı: çağrı oluşturma (debounce), listeleme, kapatma.

Çağrı oluşturulunca hem DB'ye yazılır hem de realtime hub üzerinden personel
kanallarına (pos + kds) anlık bildirim yayınlanır (bkz. PLAN §7).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.table import Table
from app.models.waiter_call import WaiterCall, WaiterCallStatus

# Aynı masadan kısa sürede tekrar basılırsa yeni kayıt açma (spam önleme).
_DEBOUNCE_SECONDS = 60


class WaiterCallError(Exception):
    """Garson çağrısı iş kuralı hatası."""


async def _publish(call: WaiterCall, table_name: str | None) -> None:
    from app.realtime import hub

    rid = str(call.restaurant_id)
    event = {
        "type": "waiter.called",
        "call_id": str(call.id),
        "table_id": str(call.table_id),
        "table_name": table_name,
    }
    await hub.publish(hub.channel(rid, "pos"), event)
    await hub.publish(hub.channel(rid, "kds"), event)


async def call_waiter(
    db: AsyncSession,
    restaurant_id: uuid.UUID,
    table_id: uuid.UUID,
    note: str | None = None,
) -> WaiterCall:
    """Masa için bir garson çağrısı oluşturur.

    Son `_DEBOUNCE_SECONDS` içinde aynı masada bekleyen çağrı varsa yeni kayıt
    açmaz, mevcut çağrıyı döner (çift basışta tek çağrı).
    """
    since = datetime.now(UTC) - timedelta(seconds=_DEBOUNCE_SECONDS)
    existing = await db.scalar(
        select(WaiterCall).where(
            WaiterCall.restaurant_id == restaurant_id,
            WaiterCall.table_id == table_id,
            WaiterCall.status == WaiterCallStatus.PENDING,
            WaiterCall.created_at >= since,
        )
    )
    if existing is not None:
        return existing

    call = WaiterCall(
        restaurant_id=restaurant_id,
        table_id=table_id,
        status=WaiterCallStatus.PENDING,
        note=note,
    )
    db.add(call)
    await db.commit()
    await db.refresh(call)

    table = await db.get(Table, table_id)
    await _publish(call, table.name if table else None)
    return call


async def list_pending(db: AsyncSession, restaurant_id: uuid.UUID) -> list[WaiterCall]:
    result = await db.execute(
        select(WaiterCall)
        .where(
            WaiterCall.restaurant_id == restaurant_id,
            WaiterCall.status == WaiterCallStatus.PENDING,
        )
        .options(selectinload(WaiterCall.table))
        .order_by(WaiterCall.created_at)
    )
    return list(result.scalars().all())


async def resolve(
    db: AsyncSession, restaurant_id: uuid.UUID, call_id: uuid.UUID
) -> WaiterCall:
    # table ilişkisini baştan yükle: çıktı table_name'i async lazy-load patlatmasın.
    call = await db.scalar(
        select(WaiterCall)
        .where(WaiterCall.id == call_id)
        .options(selectinload(WaiterCall.table))
    )
    if call is None or call.restaurant_id != restaurant_id:
        raise WaiterCallError("Çağrı bulunamadı")
    if call.status != WaiterCallStatus.RESOLVED:
        call.status = WaiterCallStatus.RESOLVED
        call.resolved_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(call, ["status", "resolved_at"])
    return call
