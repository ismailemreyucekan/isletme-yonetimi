"""Menü yönetimi: kategori ve ürün CRUD."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentRestaurant, DbSession, require_manager
from app.models.menu import MenuCategory, MenuItem
from app.models.user import User
from app.schemas.menu import (
    MenuCategoryCreate,
    MenuCategoryOut,
    MenuCategoryUpdate,
    MenuItemCreate,
    MenuItemOut,
    MenuItemUpdate,
)

router = APIRouter(prefix="/menu", tags=["menu"])

RequireManager = Annotated[User, Depends(require_manager)]


# ── Kategoriler ──────────────────────────────────────────────────────────────

@router.get("/categories", response_model=list[MenuCategoryOut])
async def list_categories(db: DbSession, restaurant: CurrentRestaurant) -> list[MenuCategory]:
    result = await db.execute(
        select(MenuCategory)
        .where(MenuCategory.restaurant_id == restaurant.id)
        .order_by(MenuCategory.sort_order, MenuCategory.name)
    )
    return list(result.scalars().all())


@router.post("/categories", response_model=MenuCategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: MenuCategoryCreate,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireManager,
) -> MenuCategory:
    cat = MenuCategory(restaurant_id=restaurant.id, **data.model_dump())
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.patch("/categories/{category_id}", response_model=MenuCategoryOut)
async def update_category(
    category_id: uuid.UUID,
    data: MenuCategoryUpdate,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireManager,
) -> MenuCategory:
    cat = await db.get(MenuCategory, category_id)
    if cat is None or cat.restaurant_id != restaurant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kategori bulunamadı")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(cat, field, value)

    await db.commit()
    await db.refresh(cat)
    return cat


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireManager,
) -> None:
    cat = await db.get(MenuCategory, category_id)
    if cat is None or cat.restaurant_id != restaurant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kategori bulunamadı")

    await db.delete(cat)
    await db.commit()


# ── Ürünler ──────────────────────────────────────────────────────────────────

@router.get("/items", response_model=list[MenuItemOut])
async def list_items(db: DbSession, restaurant: CurrentRestaurant) -> list[MenuItem]:
    result = await db.execute(
        select(MenuItem)
        .where(MenuItem.restaurant_id == restaurant.id)
        .order_by(MenuItem.sort_order, MenuItem.name)
    )
    return list(result.scalars().all())


@router.get("/categories/{category_id}/items", response_model=list[MenuItemOut])
async def list_items_by_category(
    category_id: uuid.UUID,
    db: DbSession,
    restaurant: CurrentRestaurant,
) -> list[MenuItem]:
    result = await db.execute(
        select(MenuItem)
        .where(
            MenuItem.restaurant_id == restaurant.id,
            MenuItem.category_id == category_id,
        )
        .order_by(MenuItem.sort_order, MenuItem.name)
    )
    return list(result.scalars().all())


@router.post("/items", response_model=MenuItemOut, status_code=status.HTTP_201_CREATED)
async def create_item(
    data: MenuItemCreate,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireManager,
) -> MenuItem:
    # Kategori bu kiracıya mı ait?
    cat = await db.get(MenuCategory, data.category_id)
    if cat is None or cat.restaurant_id != restaurant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kategori bulunamadı")

    item = MenuItem(restaurant_id=restaurant.id, **data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.patch("/items/{item_id}", response_model=MenuItemOut)
async def update_item(
    item_id: uuid.UUID,
    data: MenuItemUpdate,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireManager,
) -> MenuItem:
    item = await db.get(MenuItem, item_id)
    if item is None or item.restaurant_id != restaurant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ürün bulunamadı")

    updates = data.model_dump(exclude_none=True)
    if "category_id" in updates:
        cat = await db.get(MenuCategory, updates["category_id"])
        if cat is None or cat.restaurant_id != restaurant.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kategori bulunamadı")

    for field, value in updates.items():
        setattr(item, field, value)

    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: uuid.UUID,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireManager,
) -> None:
    item = await db.get(MenuItem, item_id)
    if item is None or item.restaurant_id != restaurant.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ürün bulunamadı")

    await db.delete(item)
    await db.commit()
