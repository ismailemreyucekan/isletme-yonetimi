"""Faz 1 — ürün opsiyonları (modifiers): grup CRUD, atama, sipariş entegrasyonu."""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.menu import MenuCategory, MenuItem
from app.models.restaurant import Restaurant
from app.schemas.modifier import (
    ModifierCreate,
    ModifierGroupCreate,
    ModifierGroupUpdate,
    ModifierUpdate,
)
from app.services import modifier_service, order_service


@pytest_asyncio.fixture
async def session(db_engine):
    maker = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        yield s


async def _setup(session) -> tuple[Restaurant, MenuItem]:
    r = Restaurant(name="Modifier Kafe", slug="mod-kafe")
    session.add(r)
    await session.flush()
    cat = MenuCategory(restaurant_id=r.id, name="İçecek")
    session.add(cat)
    await session.flush()
    item = MenuItem(restaurant_id=r.id, category_id=cat.id, name="Latte", price=50)
    session.add(item)
    await session.commit()
    return r, item


async def test_create_assign_and_order_with_modifier(session):
    r, item = await _setup(session)
    grp = await modifier_service.create_group(
        session,
        r.id,
        ModifierGroupCreate(
            name="Boy",
            selection_type="single",
            min_select=1,
            max_select=1,
            is_required=True,
            modifiers=[
                ModifierCreate(name="Küçük", price_delta=0),
                ModifierCreate(name="Büyük", price_delta=15),
            ],
        ),
    )
    assert len(grp.modifiers) == 2

    await modifier_service.assign_groups(session, r.id, item.id, [grp.id])
    groups = await modifier_service.get_item_groups(session, r.id, item.id)
    assert len(groups) == 1
    buyuk = next(m for m in groups[0].modifiers if m.name == "Büyük")

    order = await order_service.open_order(session, r.id, None)
    order = await order_service.add_item(session, order, item.id, 2, None, [buyuk.id])
    line = order.items[0]
    # Birim fiyat 50 + 15 = 65 ; satır 65 × 2 = 130
    assert str(line.unit_price) == "65.00"
    assert str(line.line_total) == "130.00"
    assert [m.name_snapshot for m in line.modifiers] == ["Büyük"]


async def test_required_group_enforced(session):
    r, item = await _setup(session)
    grp = await modifier_service.create_group(
        session,
        r.id,
        ModifierGroupCreate(
            name="Boy",
            selection_type="single",
            min_select=1,
            is_required=True,
            modifiers=[ModifierCreate(name="Küçük", price_delta=0)],
        ),
    )
    await modifier_service.assign_groups(session, r.id, item.id, [grp.id])
    order = await order_service.open_order(session, r.id, None)
    with pytest.raises(order_service.OrderError):
        await order_service.add_item(session, order, item.id, 1, None, [])


async def test_update_modifier_and_group(session):
    r, _item = await _setup(session)
    grp = await modifier_service.create_group(
        session,
        r.id,
        ModifierGroupCreate(name="Boy", modifiers=[ModifierCreate(name="Büyük", price_delta=15)]),
    )
    mod_id = grp.modifiers[0].id

    updated = await modifier_service.update_modifier(
        session, r.id, mod_id, ModifierUpdate(name="Çok Büyük", price_delta=20)
    )
    m = updated.modifiers[0]
    assert m.name == "Çok Büyük"
    assert float(m.price_delta) == 20

    g2 = await modifier_service.update_group(
        session, r.id, grp.id, ModifierGroupUpdate(name="Ebat", is_required=True)
    )
    assert g2.name == "Ebat"
    assert g2.is_required is True


async def test_single_group_rejects_multiple_selection(session):
    r, item = await _setup(session)
    grp = await modifier_service.create_group(
        session,
        r.id,
        ModifierGroupCreate(
            name="Boy",
            selection_type="single",
            max_select=1,
            modifiers=[ModifierCreate(name="A"), ModifierCreate(name="B")],
        ),
    )
    await modifier_service.assign_groups(session, r.id, item.id, [grp.id])
    groups = await modifier_service.get_item_groups(session, r.id, item.id)
    both = [m.id for m in groups[0].modifiers]
    order = await order_service.open_order(session, r.id, None)
    with pytest.raises(order_service.OrderError):
        await order_service.add_item(session, order, item.id, 1, None, both)
