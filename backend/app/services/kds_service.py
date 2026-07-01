"""KDS iş mantığı: mutfak fişleri, durum ilerletme, gerçek zamanlı yayın."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import KitchenStatus, Order, OrderItem, OrderStatus
from app.realtime import hub

# Mutfakta görünmesi gereken durumlar (servis edilmiş/iptal hariç).
ACTIVE_KITCHEN = (KitchenStatus.NEW, KitchenStatus.PREPARING, KitchenStatus.READY)


class KdsError(Exception):
    pass


async def list_tickets(db: AsyncSession, restaurant_id: uuid.UUID) -> list[Order]:
    """Mutfakta aktif kalemi olan açık siparişleri döner (eskiden yeniye)."""
    result = await db.execute(
        select(Order)
        .where(
            Order.restaurant_id == restaurant_id,
            Order.status == OrderStatus.OPEN,
        )
        .options(selectinload(Order.items), selectinload(Order.table))
        .order_by(Order.opened_at.asc())
    )
    orders = list(result.scalars().all())
    # Sadece mutfakta bekleyen kalemi olanlar.
    return [
        o
        for o in orders
        if any(i.kitchen_status in ACTIVE_KITCHEN for i in o.items)
    ]


async def set_item_status(
    db: AsyncSession,
    restaurant_id: uuid.UUID,
    item_id: uuid.UUID,
    new_status: str,
) -> OrderItem:
    try:
        status = KitchenStatus(new_status)
    except ValueError as exc:
        raise KdsError("Geçersiz mutfak durumu") from exc

    result = await db.execute(
        select(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .where(OrderItem.id == item_id, Order.restaurant_id == restaurant_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise KdsError("Kalem bulunamadı")

    item.kitchen_status = status
    await db.commit()
    # db.refresh() gereksiz: expire_on_commit=False olduğundan alanlar zaten
    # bellekte; uzak DB'ye (Neon) fazladan bir gidiş-dönüş yapmıyoruz.

    await publish_kitchen_event(
        restaurant_id,
        {
            "type": "item.status.changed",
            "order_id": str(item.order_id),
            "item_id": str(item.id),
            "kitchen_status": status.value,
        },
    )
    return item


async def publish_kitchen_event(restaurant_id: uuid.UUID, event: dict) -> None:
    """Mutfak (kds) ve kasa (pos) kanallarına olay yayınlar."""
    rid = str(restaurant_id)
    await hub.publish(hub.channel(rid, "kds"), event)
    await hub.publish(hub.channel(rid, "pos"), event)
