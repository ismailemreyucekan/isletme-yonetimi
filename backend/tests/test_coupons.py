"""Faz 2 — kupon kodu servis testleri."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.order import Order, OrderItem, OrderStatus
from app.models.restaurant import Restaurant
from app.services import coupon_service, order_service


@pytest_asyncio.fixture
async def session(db_engine):
    maker = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        yield s


async def _restaurant(session) -> Restaurant:
    r = Restaurant(name="Kupon Kafe", slug="kupon-kafe")
    session.add(r)
    await session.flush()
    return r


async def test_create_and_find_coupon_case_insensitive(session):
    r = await _restaurant(session)
    c = await coupon_service.create_coupon(session, r.id, "INDIRIM10", "percent", 10)
    assert c.code == "INDIRIM10"
    found = await coupon_service.get_coupon_by_code(session, r.id, "indirim10")
    assert found is not None and found.id == c.id


async def test_duplicate_coupon_rejected(session):
    r = await _restaurant(session)
    await coupon_service.create_coupon(session, r.id, "X", "amount", 50)
    with pytest.raises(coupon_service.CouponError):
        await coupon_service.create_coupon(session, r.id, "x", "amount", 20)


async def test_coupon_applies_as_discount(session):
    r = await _restaurant(session)
    order = Order(restaurant_id=r.id, status=OrderStatus.OPEN)
    order.items = [OrderItem(name_snapshot="Ürün", unit_price=100, quantity=1, line_total=100)]
    order.payments = []
    session.add(order)
    await session.commit()
    order = await order_service.get_order(session, r.id, order.id)
    order_service.recompute_totals(order)
    await session.commit()

    coupon = await coupon_service.create_coupon(session, r.id, "Y20", "amount", 20)
    out = await order_service.set_discount(session, order, coupon.mode.value, coupon.value)
    assert str(out.discount_amount) == "20.00"
    assert str(out.total) == "80.00"
