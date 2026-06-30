"""Sipariş iş mantığı: toplam hesaplama, ödeme, hesap bölme.

Tüm para hesapları Decimal ile yapılır. Tutar tutarlılığı (subtotal, total,
paid_total) her değişiklikte yeniden hesaplanır (bkz. PLAN §6).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.menu import MenuItem
from app.models.order import Order, OrderItem, OrderStatus, PaidStatus
from app.models.payment import Payment, PaymentMethod, SplitType
from app.models.restaurant import Restaurant
from app.models.table import Table
from app.services import modifier_service

CENT = Decimal("0.01")


class OrderError(Exception):
    """Sipariş işlemlerinde iş kuralı hatası."""


def _money(value: Decimal | float | int) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def recompute_totals(order: Order) -> None:
    """Tutarları satırlardan ve ödemelerden yeniden hesaplar.

    total = ara toplam − indirim + servis ücreti.
    paid_total = tahsil edilen ödemelerin toplamı (gerçek para; bkz. PLAN §6.2).
    Not: order.payments yüklenmiş olmalı (get_order selectinload eder).
    """
    subtotal = sum((Decimal(str(i.line_total)) for i in order.items), Decimal("0"))
    # İndirim ara toplamı aşamaz (ürün silinince total negatife düşmesin).
    discount = min(Decimal(str(order.discount_amount)), subtotal)
    rate = Decimal(str(order.service_charge_rate or 0))
    service_charge = subtotal * rate / Decimal("100")
    collected = sum((Decimal(str(p.amount)) for p in order.payments), Decimal("0"))

    order.subtotal = _money(subtotal)
    order.service_charge_amount = _money(service_charge)
    order.total = _money(subtotal - discount + service_charge)
    order.paid_total = _money(collected)


async def get_order(db: AsyncSession, restaurant_id: uuid.UUID, order_id: uuid.UUID) -> Order:
    result = await db.execute(
        select(Order)
        .where(Order.id == order_id, Order.restaurant_id == restaurant_id)
        .options(
            selectinload(Order.items).selectinload(OrderItem.modifiers),
            selectinload(Order.payments),
        )
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise OrderError("Sipariş bulunamadı")
    return order


async def get_active_order_for_table(
    db: AsyncSession, restaurant_id: uuid.UUID, table_id: uuid.UUID
) -> Order | None:
    result = await db.execute(
        select(Order)
        .where(
            Order.restaurant_id == restaurant_id,
            Order.table_id == table_id,
            Order.status == OrderStatus.OPEN,
        )
        .options(
            selectinload(Order.items).selectinload(OrderItem.modifiers),
            selectinload(Order.payments),
        )
    )
    return result.scalar_one_or_none()


async def dashboard_summary(db: AsyncSession, restaurant_id: uuid.UUID) -> dict:
    """İşletme ana sayfası özeti: masa doluluğu, aktif siparişler, bugünkü ciro.

    Açık hesaplar (status=OPEN) tek sorguda çekilip toplanır; bugünün tahsilatı
    Payment kayıtlarından (UTC gün başından itibaren) toplanır.
    """
    total_tables = (
        await db.scalar(
            select(func.count(Table.id)).where(Table.restaurant_id == restaurant_id)
        )
    ) or 0

    open_orders = (
        await db.execute(
            select(Order)
            .where(
                Order.restaurant_id == restaurant_id,
                Order.status == OrderStatus.OPEN,
            )
            .options(selectinload(Order.table))
            .order_by(Order.opened_at)
        )
    ).scalars().all()

    occupied_tables = len({o.table_id for o in open_orders if o.table_id is not None})
    open_total = sum((Decimal(str(o.total)) for o in open_orders), Decimal("0"))
    open_paid = sum((Decimal(str(o.paid_total)) for o in open_orders), Decimal("0"))

    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    revenue, tips, payment_count = (
        await db.execute(
            select(
                func.coalesce(func.sum(Payment.amount), 0),
                func.coalesce(func.sum(Payment.tip_amount), 0),
                func.count(Payment.id),
            ).where(
                Payment.restaurant_id == restaurant_id,
                Payment.created_at >= today_start,
            )
        )
    ).one()

    active_order_list = [
        {
            "order_id": o.id,
            "table_id": o.table_id,
            "table_name": o.table.name if o.table else None,
            "source": o.source.value if hasattr(o.source, "value") else str(o.source),
            "total": float(o.total),
            "paid_total": float(o.paid_total),
            "remaining": float(_money(Decimal(str(o.total)) - Decimal(str(o.paid_total)))),
            "opened_at": o.opened_at,
        }
        for o in open_orders
    ]

    return {
        "total_tables": total_tables,
        "occupied_tables": occupied_tables,
        "empty_tables": max(total_tables - occupied_tables, 0),
        "active_orders": len(open_orders),
        "open_total": float(_money(open_total)),
        "open_paid": float(_money(open_paid)),
        "open_remaining": float(_money(open_total - open_paid)),
        "today_revenue": float(_money(Decimal(str(revenue)))),
        "today_tips": float(_money(Decimal(str(tips)))),
        "today_payments": int(payment_count),
        "active_order_list": active_order_list,
    }


async def get_recent_paid_order_for_table(
    db: AsyncSession,
    restaurant_id: uuid.UUID,
    table_id: uuid.UUID,
    within_minutes: int = 30,
) -> Order | None:
    """Son `within_minutes` içinde ödenip kapanmış hesabı döner.

    Müşteri tüm hesabı ödeyince sipariş kapanır; bu yüzden "açık hesap" kalmaz.
    Ödeme sonrası kısa süre boyunca müşteriye "ödendi" bilgisini gösterebilmek
    için yakın zamanda kapanan hesabı getiriyoruz.
    """
    cutoff = datetime.now(UTC) - timedelta(minutes=within_minutes)
    result = await db.execute(
        select(Order)
        .where(
            Order.restaurant_id == restaurant_id,
            Order.table_id == table_id,
            Order.status.in_([OrderStatus.PAID, OrderStatus.CLOSED]),
            Order.closed_at >= cutoff,
        )
        .order_by(Order.closed_at.desc())
        .options(
            selectinload(Order.items).selectinload(OrderItem.modifiers),
            selectinload(Order.payments),
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def open_order(
    db: AsyncSession,
    restaurant_id: uuid.UUID,
    table_id: uuid.UUID | None,
    source: str = "dine_in",
) -> Order:
    """Masa için açık sipariş yoksa oluşturur, varsa onu döner."""
    if table_id is not None:
        table = await db.get(Table, table_id)
        if table is None or table.restaurant_id != restaurant_id:
            raise OrderError("Masa bulunamadı")

        existing = await get_active_order_for_table(db, restaurant_id, table_id)
        if existing is not None:
            return existing

    # Servis ücreti oranını işletme ayarlarından snapshot'la (bkz. PLAN §6.2).
    rate = Decimal("0")
    restaurant = await db.get(Restaurant, restaurant_id)
    if restaurant is not None:
        rsettings = restaurant.settings or {}
        if rsettings.get("service_charge_enabled"):
            rate = Decimal(str(rsettings.get("service_charge_rate", 0) or 0))

    order = Order(
        restaurant_id=restaurant_id,
        table_id=table_id,
        source=source,
        service_charge_rate=_money(rate),
    )
    db.add(order)
    await db.commit()
    return await get_order(db, restaurant_id, order.id)


async def add_item(
    db: AsyncSession,
    order: Order,
    menu_item_id: uuid.UUID,
    quantity: int,
    note: str | None = None,
    modifier_ids: list[uuid.UUID] | None = None,
) -> Order:
    if order.status != OrderStatus.OPEN:
        raise OrderError("Kapalı siparişe ürün eklenemez")

    item = await db.get(MenuItem, menu_item_id)
    if item is None or item.restaurant_id != order.restaurant_id:
        raise OrderError("Ürün bulunamadı")

    modifier_ids = list(modifier_ids or [])
    try:
        snapshots, delta = await modifier_service.prepare_modifiers(
            db, order.restaurant_id, menu_item_id, modifier_ids
        )
    except modifier_service.ModifierError as exc:
        raise OrderError(str(exc)) from exc

    # Birim fiyat = ürün fiyatı + seçili opsiyonların fiyat farkları (bkz. PLAN §6.1).
    effective_unit = Decimal(str(item.price)) + delta

    # Opsiyonsuz aynı ürünleri birleştir; opsiyonlu olanlar ayrı satır.
    existing = None
    if not modifier_ids:
        existing = next(
            (
                oi
                for oi in order.items
                if oi.menu_item_id == menu_item_id
                and oi.paid_status == PaidStatus.UNPAID
                and (oi.note or None) == (note or None)
                and not oi.modifiers
            ),
            None,
        )

    if existing is not None:
        existing.quantity += quantity
        existing.line_total = _money(Decimal(str(existing.unit_price)) * existing.quantity)
    else:
        line = OrderItem(
            order_id=order.id,
            menu_item_id=menu_item_id,
            name_snapshot=item.name,
            unit_price=_money(effective_unit),
            quantity=quantity,
            line_total=_money(effective_unit * quantity),
            note=note,
        )
        line.modifiers = snapshots
        order.items.append(line)

    recompute_totals(order)
    await db.commit()

    # Mutfak ekranı (KDS) ve kasa (POS) canlı güncellensin (bkz. PLAN §7).
    await _publish_order_event(order.restaurant_id, order.id, "order.item.added")

    return await get_order(db, order.restaurant_id, order.id)


async def _publish_order_event(
    restaurant_id: uuid.UUID, order_id: uuid.UUID, event_type: str
) -> None:
    from app.realtime import hub

    rid = str(restaurant_id)
    event = {"type": event_type, "order_id": str(order_id)}
    await hub.publish(hub.channel(rid, "kds"), event)
    await hub.publish(hub.channel(rid, "pos"), event)


async def update_item_quantity(
    db: AsyncSession, order: Order, item_id: uuid.UUID, quantity: int
) -> Order:
    if order.status != OrderStatus.OPEN:
        raise OrderError("Kapalı sipariş düzenlenemez")

    line = next((oi for oi in order.items if oi.id == item_id), None)
    if line is None:
        raise OrderError("Satır bulunamadı")
    if line.paid_status == PaidStatus.PAID:
        raise OrderError("Ödenmiş satır değiştirilemez")

    line.quantity = quantity
    line.line_total = _money(Decimal(str(line.unit_price)) * quantity)
    recompute_totals(order)
    await db.commit()
    return await get_order(db, order.restaurant_id, order.id)


async def remove_item(db: AsyncSession, order: Order, item_id: uuid.UUID) -> Order:
    if order.status != OrderStatus.OPEN:
        raise OrderError("Kapalı sipariş düzenlenemez")

    line = next((oi for oi in order.items if oi.id == item_id), None)
    if line is None:
        raise OrderError("Satır bulunamadı")
    if line.paid_status == PaidStatus.PAID:
        raise OrderError("Ödenmiş satır silinemez")

    order.items.remove(line)
    await db.delete(line)
    recompute_totals(order)
    await db.commit()
    return await get_order(db, order.restaurant_id, order.id)


async def set_discount(
    db: AsyncSession, order: Order, mode: str, value: Decimal | float | int
) -> Order:
    """Hesaba indirim uygular (yüzde veya sabit tutar). value=0 indirimi kaldırır.

    İndirim hesap (order) bazlıdır; ara toplamı aşamaz. Toplam yeniden hesaplanır.
    """
    if order.status != OrderStatus.OPEN:
        raise OrderError("Kapalı hesaba indirim uygulanamaz")

    value = Decimal(str(value))
    if value < 0:
        raise OrderError("İndirim negatif olamaz")

    subtotal = sum((Decimal(str(i.line_total)) for i in order.items), Decimal("0"))

    if mode == "percent":
        if value > 100:
            raise OrderError("Yüzde indirim 100'den büyük olamaz")
        discount = subtotal * value / Decimal("100")
    elif mode == "amount":
        discount = value
    else:
        raise OrderError("Geçersiz indirim türü (percent | amount)")

    order.discount_amount = _money(min(discount, subtotal))
    recompute_totals(order)
    await db.commit()
    return await get_order(db, order.restaurant_id, order.id)


async def set_service_charge(
    db: AsyncSession, order: Order, rate: Decimal | float | int
) -> Order:
    """Hesaba servis ücreti oranı (%) uygular. rate=0 servis ücretini kaldırır."""
    if order.status != OrderStatus.OPEN:
        raise OrderError("Kapalı hesaba servis ücreti uygulanamaz")

    rate = Decimal(str(rate))
    if rate < 0 or rate > 100:
        raise OrderError("Servis ücreti oranı 0–100 arasında olmalı")

    order.service_charge_rate = _money(rate)
    recompute_totals(order)
    await db.commit()
    return await get_order(db, order.restaurant_id, order.id)


def _maybe_close(order: Order) -> None:
    """Tüm tutar ödendiyse siparişi kapatır."""
    if Decimal(str(order.paid_total)) >= Decimal(str(order.total)) and order.items:
        order.status = OrderStatus.PAID
        from datetime import datetime

        order.closed_at = datetime.now(UTC)


async def pay_full(
    db: AsyncSession, order: Order, method: str, tip_amount: Decimal | float | int = 0
) -> Order:
    """Kalan tüm tutarı tek seferde öder, hesabı kapatır. Bahşiş opsiyonel."""
    if order.status != OrderStatus.OPEN:
        raise OrderError("Sipariş zaten kapalı")

    remaining = Decimal(str(order.total)) - Decimal(str(order.paid_total))
    if remaining <= 0:
        raise OrderError("Ödenecek tutar yok")

    for line in order.items:
        if line.paid_status != PaidStatus.PAID:
            line.paid_status = PaidStatus.PAID

    order.payments.append(
        Payment(
            restaurant_id=order.restaurant_id,
            amount=_money(remaining),
            tip_amount=_money(tip_amount),
            method=PaymentMethod(method),
            split_type=SplitType.FULL,
        )
    )
    recompute_totals(order)
    _maybe_close(order)
    await db.commit()
    return await get_order(db, order.restaurant_id, order.id)


async def pay_items(
    db: AsyncSession,
    order: Order,
    item_ids: list[uuid.UUID],
    method: str,
    tip_amount: Decimal | float | int = 0,
) -> Order:
    """Seçili satırları öder (kendi yediğini öde). Bahşiş opsiyonel."""
    if order.status != OrderStatus.OPEN:
        raise OrderError("Sipariş zaten kapalı")

    selected = [oi for oi in order.items if oi.id in set(item_ids)]
    if not selected:
        raise OrderError("Ödenecek satır seçilmedi")

    already = [oi for oi in selected if oi.paid_status == PaidStatus.PAID]
    if already:
        raise OrderError("Seçili satırlardan bazıları zaten ödenmiş")

    subtotal = sum((Decimal(str(i.line_total)) for i in order.items), Decimal("0"))
    total = Decimal(str(order.total))
    base = sum((Decimal(str(oi.line_total)) for oi in selected), Decimal("0"))

    # Seçim kalan tüm ödenmemiş satırları kapsıyorsa kalanı tam tahsil et (küsuratı
    # kapatır); değilse seçili satırların nihai toplamdaki oransal payı (servis
    # ücreti/indirim dahil) alınır (bkz. PLAN §6.2).
    unpaid_ids = {oi.id for oi in order.items if oi.paid_status != PaidStatus.PAID}
    if subtotal > 0 and not (unpaid_ids <= set(item_ids)):
        amount = base * total / subtotal
    else:
        amount = total - Decimal(str(order.paid_total))

    for oi in selected:
        oi.paid_status = PaidStatus.PAID

    order.payments.append(
        Payment(
            restaurant_id=order.restaurant_id,
            amount=_money(amount),
            tip_amount=_money(tip_amount),
            method=PaymentMethod(method),
            split_type=SplitType.ITEMS,
        )
    )
    recompute_totals(order)
    _maybe_close(order)
    await db.commit()
    return await get_order(db, order.restaurant_id, order.id)


async def pay_split(
    db: AsyncSession,
    order: Order,
    parts: int,
    method: str,
    tip_amount: Decimal | float | int = 0,
) -> Order:
    """Hesabı kişi sayısına böler, bir payı tahsil eder. Bahşiş opsiyonel.

    Eşit bölmede tüm satırlar paylaşıldığından, ödeme tamamlanınca satırlar
    ödenmiş sayılır. Her çağrı bir pay (total/parts) tahsil eder.
    """
    if order.status != OrderStatus.OPEN:
        raise OrderError("Sipariş zaten kapalı")

    total = Decimal(str(order.total))
    paid = Decimal(str(order.paid_total))
    remaining = total - paid
    if remaining <= 0:
        raise OrderError("Ödenecek tutar yok")

    share = _money(total / Decimal(parts))
    # Son pay küsuratı kapatır.
    amount = share if remaining > share else _money(remaining)

    order.payments.append(
        Payment(
            restaurant_id=order.restaurant_id,
            amount=amount,
            tip_amount=_money(tip_amount),
            method=PaymentMethod(method),
            split_type=SplitType.EQUAL,
        )
    )
    recompute_totals(order)

    # Tamamı ödendiyse satırları da ödenmiş işaretle ve kapat.
    if Decimal(str(order.paid_total)) >= total:
        for line in order.items:
            line.paid_status = PaidStatus.PAID
        _maybe_close(order)

    await db.commit()
    return await get_order(db, order.restaurant_id, order.id)
