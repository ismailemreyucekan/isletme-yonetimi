"""Masa yönetimi ve masa planı (durumlu)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentRestaurant, DbSession, require_manager
from app.models.table import Table
from app.models.user import User
from app.schemas.table import TableCreate, TableOut, TableUpdate, TableWithStatus
from app.services import order_service

router = APIRouter(prefix="/tables", tags=["tables"])

RequireManager = Annotated[User, Depends(require_manager)]


@router.get("", response_model=list[TableWithStatus])
async def list_tables(db: DbSession, restaurant: CurrentRestaurant) -> list[TableWithStatus]:
    result = await db.execute(
        select(Table)
        .where(Table.restaurant_id == restaurant.id)
        .order_by(Table.sort_order, Table.name)
    )
    tables = list(result.scalars().all())

    out: list[TableWithStatus] = []
    for t in tables:
        active = await order_service.get_active_order_for_table(db, restaurant.id, t.id)
        out.append(
            TableWithStatus(
                id=t.id,
                restaurant_id=t.restaurant_id,
                name=t.name,
                sort_order=t.sort_order,
                qr_token=t.qr_token,
                status="occupied" if active else "empty",
                active_order_id=active.id if active else None,
                active_total=float(active.total) if active else 0,
                active_paid_total=float(active.paid_total) if active else 0,
            )
        )
    return out


@router.post("", response_model=TableOut, status_code=status.HTTP_201_CREATED)
async def create_table(
    data: TableCreate,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireManager,
) -> Table:
    table = Table(restaurant_id=restaurant.id, **data.model_dump())
    db.add(table)
    await db.commit()
    await db.refresh(table)
    return table


@router.patch("/{table_id}", response_model=TableOut)
async def update_table(
    table_id: uuid.UUID,
    data: TableUpdate,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireManager,
) -> Table:
    table = await db.get(Table, table_id)
    if table is None or table.restaurant_id != restaurant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Masa bulunamadı")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(table, field, value)
    await db.commit()
    await db.refresh(table)
    return table


@router.delete("/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_table(
    table_id: uuid.UUID,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireManager,
) -> None:
    table = await db.get(Table, table_id)
    if table is None or table.restaurant_id != restaurant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Masa bulunamadı")

    active = await order_service.get_active_order_for_table(db, restaurant.id, table_id)
    if active is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Açık hesabı olan masa silinemez",
        )
    await db.delete(table)
    await db.commit()


@router.post("/bulk", response_model=list[TableOut], status_code=status.HTTP_201_CREATED)
async def bulk_create_tables(
    count: int,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireManager,
    prefix: str = "Masa",
) -> list[Table]:
    """Hızlı kurulum: "Masa 1..N" şeklinde toplu masa oluşturur."""
    if count < 1 or count > 200:
        raise HTTPException(status_code=400, detail="1-200 arası bir sayı girin")

    # Mevcut en yüksek sıra numarasından devam et.
    result = await db.execute(
        select(Table).where(Table.restaurant_id == restaurant.id)
    )
    existing = len(list(result.scalars().all()))

    created: list[Table] = []
    for i in range(1, count + 1):
        t = Table(
            restaurant_id=restaurant.id,
            name=f"{prefix} {existing + i}",
            sort_order=existing + i,
        )
        db.add(t)
        created.append(t)
    await db.commit()
    for t in created:
        await db.refresh(t)
    return created
