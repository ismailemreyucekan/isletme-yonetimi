"""Ürün opsiyonu (modifier) iş mantığı: grup/opsiyon CRUD, ürüne atama,
sipariş anında seçim doğrulama + snapshot üretimi (bkz. PLAN §6.1)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.menu import MenuItem
from app.models.modifier import (
    MenuItemModifierGroup,
    Modifier,
    ModifierGroup,
    OrderItemModifier,
    SelectionType,
)
from app.schemas.modifier import (
    ModifierCreate,
    ModifierGroupCreate,
    ModifierGroupUpdate,
    ModifierUpdate,
)


class ModifierError(Exception):
    """Modifier işlemlerinde iş kuralı hatası."""


# ── Grup / opsiyon CRUD ──────────────────────────────────────────────────────


async def list_groups(db: AsyncSession, restaurant_id: uuid.UUID) -> list[ModifierGroup]:
    result = await db.execute(
        select(ModifierGroup)
        .where(ModifierGroup.restaurant_id == restaurant_id)
        .order_by(ModifierGroup.sort_order)
        .options(selectinload(ModifierGroup.modifiers))
    )
    return list(result.scalars())


async def _get_group(
    db: AsyncSession, restaurant_id: uuid.UUID, group_id: uuid.UUID
) -> ModifierGroup:
    result = await db.execute(
        select(ModifierGroup)
        .where(ModifierGroup.id == group_id, ModifierGroup.restaurant_id == restaurant_id)
        .options(selectinload(ModifierGroup.modifiers))
    )
    group = result.scalar_one_or_none()
    if group is None:
        raise ModifierError("Opsiyon grubu bulunamadı")
    return group


async def create_group(
    db: AsyncSession, restaurant_id: uuid.UUID, data: ModifierGroupCreate
) -> ModifierGroup:
    group = ModifierGroup(
        restaurant_id=restaurant_id,
        name=data.name,
        selection_type=SelectionType(data.selection_type),
        min_select=data.min_select,
        max_select=data.max_select,
        is_required=data.is_required,
        sort_order=data.sort_order,
        is_active=data.is_active,
    )
    group.modifiers = [
        Modifier(
            name=m.name,
            price_delta=Decimal(str(m.price_delta)),
            is_available=m.is_available,
            sort_order=m.sort_order,
        )
        for m in data.modifiers
    ]
    db.add(group)
    await db.commit()
    return await _get_group(db, restaurant_id, group.id)


async def update_group(
    db: AsyncSession,
    restaurant_id: uuid.UUID,
    group_id: uuid.UUID,
    data: ModifierGroupUpdate,
) -> ModifierGroup:
    group = await _get_group(db, restaurant_id, group_id)
    fields = data.model_dump(exclude_unset=True)
    if "selection_type" in fields:
        fields["selection_type"] = SelectionType(fields["selection_type"])
    for key, value in fields.items():
        setattr(group, key, value)
    await db.commit()
    return await _get_group(db, restaurant_id, group_id)


async def delete_group(
    db: AsyncSession, restaurant_id: uuid.UUID, group_id: uuid.UUID
) -> None:
    group = await _get_group(db, restaurant_id, group_id)
    await db.delete(group)
    await db.commit()


async def add_modifier(
    db: AsyncSession, restaurant_id: uuid.UUID, group_id: uuid.UUID, data: ModifierCreate
) -> ModifierGroup:
    group = await _get_group(db, restaurant_id, group_id)
    group.modifiers.append(
        Modifier(
            name=data.name,
            price_delta=Decimal(str(data.price_delta)),
            is_available=data.is_available,
            sort_order=data.sort_order,
        )
    )
    await db.commit()
    return await _get_group(db, restaurant_id, group_id)


async def _get_modifier(
    db: AsyncSession, restaurant_id: uuid.UUID, modifier_id: uuid.UUID
) -> tuple[Modifier, ModifierGroup]:
    modifier = await db.get(Modifier, modifier_id)
    if modifier is None:
        raise ModifierError("Opsiyon bulunamadı")
    group = await db.get(ModifierGroup, modifier.modifier_group_id)
    if group is None or group.restaurant_id != restaurant_id:
        raise ModifierError("Opsiyon bulunamadı")
    return modifier, group


async def update_modifier(
    db: AsyncSession,
    restaurant_id: uuid.UUID,
    modifier_id: uuid.UUID,
    data: ModifierUpdate,
) -> ModifierGroup:
    modifier, group = await _get_modifier(db, restaurant_id, modifier_id)
    fields = data.model_dump(exclude_unset=True)
    if "price_delta" in fields and fields["price_delta"] is not None:
        fields["price_delta"] = Decimal(str(fields["price_delta"]))
    for key, value in fields.items():
        setattr(modifier, key, value)
    await db.commit()
    return await _get_group(db, restaurant_id, group.id)


async def delete_modifier(
    db: AsyncSession, restaurant_id: uuid.UUID, modifier_id: uuid.UUID
) -> None:
    modifier, _ = await _get_modifier(db, restaurant_id, modifier_id)
    await db.delete(modifier)
    await db.commit()


# ── Ürüne grup atama ─────────────────────────────────────────────────────────


async def get_item_groups(
    db: AsyncSession, restaurant_id: uuid.UUID, menu_item_id: uuid.UUID
) -> list[ModifierGroup]:
    result = await db.execute(
        select(ModifierGroup)
        .join(
            MenuItemModifierGroup,
            MenuItemModifierGroup.modifier_group_id == ModifierGroup.id,
        )
        .where(
            MenuItemModifierGroup.menu_item_id == menu_item_id,
            ModifierGroup.restaurant_id == restaurant_id,
            ModifierGroup.is_active.is_(True),
        )
        .order_by(ModifierGroup.sort_order)
        .options(selectinload(ModifierGroup.modifiers))
    )
    return list(result.scalars())


async def assign_groups(
    db: AsyncSession,
    restaurant_id: uuid.UUID,
    menu_item_id: uuid.UUID,
    group_ids: list[uuid.UUID],
) -> list[ModifierGroup]:
    item = await db.get(MenuItem, menu_item_id)
    if item is None or item.restaurant_id != restaurant_id:
        raise ModifierError("Ürün bulunamadı")

    # İstenen grupların hepsi bu işletmeye ait olmalı.
    if group_ids:
        result = await db.execute(
            select(ModifierGroup.id).where(
                ModifierGroup.id.in_(group_ids),
                ModifierGroup.restaurant_id == restaurant_id,
            )
        )
        found = {row[0] for row in result.all()}
        if found != set(group_ids):
            raise ModifierError("Geçersiz opsiyon grubu")

    # Mevcut atamaları sil, yenilerini ekle (replace).
    await db.execute(
        delete(MenuItemModifierGroup).where(
            MenuItemModifierGroup.menu_item_id == menu_item_id
        )
    )
    for idx, gid in enumerate(group_ids):
        db.add(
            MenuItemModifierGroup(
                menu_item_id=menu_item_id, modifier_group_id=gid, sort_order=idx
            )
        )
    await db.commit()
    return await get_item_groups(db, restaurant_id, menu_item_id)


# ── Sipariş entegrasyonu ─────────────────────────────────────────────────────


async def prepare_modifiers(
    db: AsyncSession,
    restaurant_id: uuid.UUID,
    menu_item_id: uuid.UUID,
    modifier_ids: list[uuid.UUID],
) -> tuple[list[OrderItemModifier], Decimal]:
    """Seçimi ürünün gruplarına göre doğrular; snapshot listesi + toplam fiyat farkı döner."""
    groups = await get_item_groups(db, restaurant_id, menu_item_id)

    valid: dict[uuid.UUID, tuple[Modifier, ModifierGroup]] = {}
    for g in groups:
        for m in g.modifiers:
            valid[m.id] = (m, g)

    selected: list[tuple[Modifier, ModifierGroup]] = []
    for mid in modifier_ids:
        if mid not in valid:
            raise ModifierError("Geçersiz opsiyon seçimi")
        modifier, group = valid[mid]
        if not modifier.is_available:
            raise ModifierError(f"'{modifier.name}' opsiyonu mevcut değil")
        selected.append((modifier, group))

    # Grup bazlı min/max/zorunlu doğrulama.
    counts: dict[uuid.UUID, int] = {}
    for _, group in selected:
        counts[group.id] = counts.get(group.id, 0) + 1
    for g in groups:
        count = counts.get(g.id, 0)
        if g.is_required and count < max(g.min_select, 1):
            raise ModifierError(f"'{g.name}' için seçim zorunlu")
        if count < g.min_select:
            raise ModifierError(f"'{g.name}' için en az {g.min_select} seçim gerekli")
        if g.selection_type == SelectionType.SINGLE and count > 1:
            raise ModifierError(f"'{g.name}' için yalnızca bir seçim yapılabilir")
        if count > g.max_select:
            raise ModifierError(f"'{g.name}' için en fazla {g.max_select} seçim yapılabilir")

    snapshots: list[OrderItemModifier] = []
    delta_sum = Decimal("0")
    for modifier, _ in selected:
        price_delta = Decimal(str(modifier.price_delta))
        snapshots.append(
            OrderItemModifier(
                modifier_id=modifier.id,
                name_snapshot=modifier.name,
                price_delta_snapshot=price_delta,
            )
        )
        delta_sum += price_delta

    return snapshots, delta_sum
