"""Ürün opsiyonu (modifier) uçları: grup/opsiyon CRUD + ürüne atama."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentRestaurant, DbSession, require_manager, require_staff
from app.models.user import User
from app.schemas.modifier import (
    AssignGroupsRequest,
    ModifierCreate,
    ModifierGroupCreate,
    ModifierGroupOut,
    ModifierGroupUpdate,
    ModifierUpdate,
)
from app.services import modifier_service
from app.services.modifier_service import ModifierError

router = APIRouter(tags=["modifiers"])

RequireStaff = Annotated[User, Depends(require_staff)]
RequireManager = Annotated[User, Depends(require_manager)]


def _not_found(exc: ModifierError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/modifier-groups", response_model=list[ModifierGroupOut])
async def list_groups(
    db: DbSession, restaurant: CurrentRestaurant, _: RequireStaff
) -> list[ModifierGroupOut]:
    groups = await modifier_service.list_groups(db, restaurant.id)
    return [ModifierGroupOut.model_validate(g) for g in groups]


@router.post(
    "/modifier-groups", response_model=ModifierGroupOut, status_code=status.HTTP_201_CREATED
)
async def create_group(
    data: ModifierGroupCreate, db: DbSession, restaurant: CurrentRestaurant, _: RequireManager
) -> ModifierGroupOut:
    group = await modifier_service.create_group(db, restaurant.id, data)
    return ModifierGroupOut.model_validate(group)


@router.patch("/modifier-groups/{group_id}", response_model=ModifierGroupOut)
async def update_group(
    group_id: uuid.UUID,
    data: ModifierGroupUpdate,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireManager,
) -> ModifierGroupOut:
    try:
        group = await modifier_service.update_group(db, restaurant.id, group_id, data)
    except ModifierError as exc:
        raise _not_found(exc) from exc
    return ModifierGroupOut.model_validate(group)


@router.delete("/modifier-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: uuid.UUID, db: DbSession, restaurant: CurrentRestaurant, _: RequireManager
) -> None:
    try:
        await modifier_service.delete_group(db, restaurant.id, group_id)
    except ModifierError as exc:
        raise _not_found(exc) from exc


@router.post("/modifier-groups/{group_id}/modifiers", response_model=ModifierGroupOut)
async def add_modifier(
    group_id: uuid.UUID,
    data: ModifierCreate,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireManager,
) -> ModifierGroupOut:
    try:
        group = await modifier_service.add_modifier(db, restaurant.id, group_id, data)
    except ModifierError as exc:
        raise _not_found(exc) from exc
    return ModifierGroupOut.model_validate(group)


@router.patch("/modifiers/{modifier_id}", response_model=ModifierGroupOut)
async def update_modifier(
    modifier_id: uuid.UUID,
    data: ModifierUpdate,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireManager,
) -> ModifierGroupOut:
    try:
        group = await modifier_service.update_modifier(db, restaurant.id, modifier_id, data)
    except ModifierError as exc:
        raise _not_found(exc) from exc
    return ModifierGroupOut.model_validate(group)


@router.delete("/modifiers/{modifier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_modifier(
    modifier_id: uuid.UUID, db: DbSession, restaurant: CurrentRestaurant, _: RequireManager
) -> None:
    try:
        await modifier_service.delete_modifier(db, restaurant.id, modifier_id)
    except ModifierError as exc:
        raise _not_found(exc) from exc


@router.get("/menu-items/{item_id}/modifier-groups", response_model=list[ModifierGroupOut])
async def get_item_groups(
    item_id: uuid.UUID, db: DbSession, restaurant: CurrentRestaurant, _: RequireStaff
) -> list[ModifierGroupOut]:
    groups = await modifier_service.get_item_groups(db, restaurant.id, item_id)
    return [ModifierGroupOut.model_validate(g) for g in groups]


@router.put("/menu-items/{item_id}/modifier-groups", response_model=list[ModifierGroupOut])
async def assign_item_groups(
    item_id: uuid.UUID,
    data: AssignGroupsRequest,
    db: DbSession,
    restaurant: CurrentRestaurant,
    _: RequireManager,
) -> list[ModifierGroupOut]:
    try:
        groups = await modifier_service.assign_groups(
            db, restaurant.id, item_id, data.group_ids
        )
    except ModifierError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return [ModifierGroupOut.model_validate(g) for g in groups]
