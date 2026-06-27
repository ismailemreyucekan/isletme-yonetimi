"""Faz 2 — indirim + servis ücreti + ödeme/hesap-kapanış servis testleri.

Servis seviyesinde test edilir (hub/Redis publish yoluna girmeden). Ödeme
fonksiyonları paid_total'ı ödeme kayıtlarından türetir; bu testler servis
ücretiyle birlikte hesabın doğru kapandığını garanti eder (bkz. PLAN §6.2).
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.order import Order, OrderItem, OrderStatus
from app.models.restaurant import Restaurant
from app.services import order_service


@pytest_asyncio.fixture
async def session(db_engine):
    maker = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        yield s


async def _order_with_items(session: AsyncSession, *, rate: int = 0) -> Order:
    """Ara toplamı 150 olan açık bir sipariş kurar (1×100 + 1×50)."""
    restaurant = Restaurant(name="Test Kafe", slug="test-kafe")
    session.add(restaurant)
    await session.flush()

    order = Order(
        restaurant_id=restaurant.id, status=OrderStatus.OPEN, service_charge_rate=rate
    )
    order.items = [
        OrderItem(name_snapshot="Kahve", unit_price=100, quantity=1, line_total=100),
        OrderItem(name_snapshot="Kek", unit_price=50, quantity=1, line_total=50),
    ]
    order.payments = []
    session.add(order)
    await session.commit()
    # payments + items yüklü bir örnek döndür ve tutarları hesapla.
    order = await order_service.get_order(session, restaurant.id, order.id)
    order_service.recompute_totals(order)
    await session.commit()
    return order


# ── İndirim ──────────────────────────────────────────────────────────────────


async def test_discount_percent(session):
    order = await _order_with_items(session)  # ara toplam 150
    out = await order_service.set_discount(session, order, "percent", 10)
    assert str(out.discount_amount) == "15.00"
    assert str(out.total) == "135.00"


async def test_discount_fixed_amount(session):
    order = await _order_with_items(session)
    out = await order_service.set_discount(session, order, "amount", 40)
    assert str(out.total) == "110.00"


async def test_discount_cannot_exceed_subtotal(session):
    order = await _order_with_items(session)
    out = await order_service.set_discount(session, order, "amount", 999)
    assert str(out.discount_amount) == "150.00"
    assert str(out.total) == "0.00"


async def test_discount_percent_over_100_rejected(session):
    order = await _order_with_items(session)
    with pytest.raises(order_service.OrderError):
        await order_service.set_discount(session, order, "percent", 150)


# ── Servis ücreti ────────────────────────────────────────────────────────────


async def test_service_charge_percent(session):
    order = await _order_with_items(session)  # ara toplam 150
    out = await order_service.set_service_charge(session, order, 10)
    assert str(out.service_charge_rate) == "10.00"
    assert str(out.service_charge_amount) == "15.00"
    assert str(out.total) == "165.00"  # 150 + 15


async def test_service_charge_with_discount(session):
    order = await _order_with_items(session)
    await order_service.set_discount(session, order, "amount", 30)
    out = await order_service.set_service_charge(session, order, 10)
    # total = 150 − 30 + 15 = 135
    assert str(out.total) == "135.00"


async def test_service_charge_rate_over_100_rejected(session):
    order = await _order_with_items(session)
    with pytest.raises(order_service.OrderError):
        await order_service.set_service_charge(session, order, 150)


# ── Ödeme + servis ücreti (hesap doğru kapanmalı) ────────────────────────────


async def test_pay_full_with_service_charge_closes(session):
    order = await _order_with_items(session)
    await order_service.set_service_charge(session, order, 10)  # total 165
    out = await order_service.pay_full(session, order, "cash")
    assert str(out.total) == "165.00"
    assert str(out.paid_total) == "165.00"
    assert out.status == "paid"


async def test_pay_split_with_service_charge_closes(session):
    order = await _order_with_items(session)
    await order_service.set_service_charge(session, order, 10)  # total 165
    o = order
    for _ in range(3):  # 3 × 55 = 165
        o = await order_service.pay_split(session, o, 3, "cash")
    assert str(o.paid_total) == "165.00"
    assert o.status == "paid"


async def test_pay_items_with_service_charge_proportional_and_closes(session):
    order = await _order_with_items(session)  # 100 + 50
    order = await order_service.set_service_charge(session, order, 10)  # total 165
    items = sorted(order.items, key=lambda i: float(i.line_total), reverse=True)
    big_id, small_id = items[0].id, items[1].id

    # İlk kalem tek başına: oransal pay = 100 × 165/150 = 110
    o = await order_service.pay_items(session, order, [big_id], "cash")
    assert str(o.paid_total) == "110.00"
    assert o.status == "open"

    # Kalan tek kalem: tam kalan = 55 → hesap kapanır
    o = await order_service.pay_items(session, o, [small_id], "cash")
    assert str(o.paid_total) == "165.00"
    assert o.status == "paid"


async def test_pay_full_without_service_charge_unchanged(session):
    """Servis ücreti yokken eski davranış korunur (regresyon)."""
    order = await _order_with_items(session)  # total 150
    out = await order_service.pay_full(session, order, "card")
    assert str(out.paid_total) == "150.00"
    assert out.status == "paid"


# ── Bahşiş ───────────────────────────────────────────────────────────────────


async def test_pay_full_with_tip_records_tip_but_not_in_paid_total(session):
    order = await _order_with_items(session)  # total 150
    out = await order_service.pay_full(session, order, "cash", 20)
    # Bahşiş ekstra paradır; hesabın paid_total'ına dahil edilmez.
    assert str(out.paid_total) == "150.00"
    assert out.status == "paid"
    assert len(out.payments) == 1
    assert str(out.payments[0].tip_amount) == "20.00"
