"""Müşteri (anonim) uçları — QR ile masa hesabı görüntüleme ve ödeme.

Güvenlik (PLAN §10): Müşteri yalnızca masanın tahmin edilemez `qr_token`'ı ile
o masanın aktif hesabına erişir. Hiçbir uç keyfi order_id kabul etmez; sipariş
her zaman token'dan çözülür. Auth gerekmez.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession
from app.core.features import Feature, is_enabled
from app.models.menu import MenuCategory, MenuItem
from app.models.restaurant import Restaurant
from app.models.table import Table
from app.schemas.menu import MenuCategoryOut, MenuItemOut
from app.schemas.modifier import ModifierGroupOut
from app.schemas.order import OrderOut
from app.schemas.public import (
    PublicMenuView,
    PublicOrderRequest,
    PublicPayItemsRequest,
    PublicRestaurant,
    PublicSplitRequest,
    PublicTableList,
    PublicTableListItem,
    PublicTableView,
)
from app.schemas.waiter import CallWaiterRequest, CallWaiterResponse
from app.services import modifier_service, order_service, waiter_service
from app.services.order_service import OrderError

router = APIRouter(prefix="/public", tags=["public"])

_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Masa bulunamadı")


def _require_qr_menu(restaurant: Restaurant) -> None:
    """QR menü kapalı işletmede müşteri uçları yokmuş gibi davran (404).

    403 yerine 404 dönmek "bu işletmenin QR'ı var ama kapalı" bilgisini sızdırmaz.
    """
    if not is_enabled(restaurant, Feature.QR_MENU):
        raise _NOT_FOUND


def _require_online_payment(restaurant: Restaurant) -> None:
    if not is_enabled(restaurant, Feature.ONLINE_PAYMENT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Online ödeme bu işletmede kapalı",
        )


async def _resolve_table(db: DbSession, qr_token: str) -> tuple[Table, Restaurant]:
    result = await db.execute(select(Table).where(Table.qr_token == qr_token))
    table = result.scalar_one_or_none()
    if table is None:
        raise _NOT_FOUND
    restaurant = await db.get(Restaurant, table.restaurant_id)
    if restaurant is None:
        raise _NOT_FOUND
    _require_qr_menu(restaurant)
    return table, restaurant


def _public_restaurant(r: Restaurant) -> PublicRestaurant:
    settings = r.settings or {}
    return PublicRestaurant(
        name=r.name, slug=r.slug, currency=settings.get("currency", "TRY")
    )


@router.get("/t/{qr_token}", response_model=PublicTableView)
async def table_view(qr_token: str, db: DbSession) -> PublicTableView:
    """Masanın aktif hesabını döner.

    Açık hesap yoksa, yakın zamanda ödenmiş hesabı (varsa) döneriz; böylece
    müşteri ödeme sonrası "tüm hesabınız ödenmiştir" görür.
    """
    table, restaurant = await _resolve_table(db, qr_token)
    order = await order_service.get_active_order_for_table(db, restaurant.id, table.id)
    if order is None:
        order = await order_service.get_recent_paid_order_for_table(
            db, restaurant.id, table.id
        )
    return PublicTableView(
        restaurant=_public_restaurant(restaurant),
        table_name=table.name,
        order=OrderOut.model_validate(order) if order else None,
    )


async def _menu_for(db: DbSession, restaurant: Restaurant) -> PublicMenuView:
    cats = await db.execute(
        select(MenuCategory)
        .where(MenuCategory.restaurant_id == restaurant.id, MenuCategory.is_active.is_(True))
        .order_by(MenuCategory.sort_order, MenuCategory.name)
    )
    items = await db.execute(
        select(MenuItem)
        .where(MenuItem.restaurant_id == restaurant.id, MenuItem.is_available.is_(True))
        .order_by(MenuItem.sort_order, MenuItem.name)
    )
    return PublicMenuView(
        restaurant=_public_restaurant(restaurant),
        categories=[MenuCategoryOut.model_validate(c) for c in cats.scalars().all()],
        items=[MenuItemOut.model_validate(i) for i in items.scalars().all()],
    )


@router.get("/r/{slug}/tables", response_model=PublicTableList)
async def tables_by_slug(slug: str, db: DbSession) -> PublicTableList:
    """İşletmenin masaları — müşteri "masanızı seçin" ekranı için.

    Not: Gerçek kullanımda her masada kendi basılı QR'ı olur; bu liste demo/masaüstü
    test kolaylığı içindir.
    """
    result = await db.execute(select(Restaurant).where(Restaurant.slug == slug))
    restaurant = result.scalar_one_or_none()
    if restaurant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İşletme bulunamadı")
    _require_qr_menu(restaurant)

    rows = await db.execute(
        select(Table)
        .where(Table.restaurant_id == restaurant.id)
        .order_by(Table.sort_order, Table.name)
    )
    tables = list(rows.scalars().all())

    out: list[PublicTableListItem] = []
    for t in tables:
        active = await order_service.get_active_order_for_table(db, restaurant.id, t.id)
        out.append(
            PublicTableListItem(
                name=t.name,
                qr_token=t.qr_token,
                status="occupied" if active else "empty",
            )
        )
    return PublicTableList(restaurant=_public_restaurant(restaurant), tables=out)


@router.get("/r/{slug}/menu", response_model=PublicMenuView)
async def menu_by_slug(slug: str, db: DbSession) -> PublicMenuView:
    """İşletmenin online menüsü (masa olmadan, sadece görüntüleme)."""
    result = await db.execute(select(Restaurant).where(Restaurant.slug == slug))
    restaurant = result.scalar_one_or_none()
    if restaurant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="İşletme bulunamadı")
    _require_qr_menu(restaurant)
    return await _menu_for(db, restaurant)


@router.get("/t/{qr_token}/menu", response_model=PublicMenuView)
async def public_menu(qr_token: str, db: DbSession) -> PublicMenuView:
    """İşletmenin online menüsü (aktif kategori + müsait ürünler)."""
    _, restaurant = await _resolve_table(db, qr_token)

    cats = await db.execute(
        select(MenuCategory)
        .where(MenuCategory.restaurant_id == restaurant.id, MenuCategory.is_active.is_(True))
        .order_by(MenuCategory.sort_order, MenuCategory.name)
    )
    items = await db.execute(
        select(MenuItem)
        .where(MenuItem.restaurant_id == restaurant.id, MenuItem.is_available.is_(True))
        .order_by(MenuItem.sort_order, MenuItem.name)
    )
    return PublicMenuView(
        restaurant=_public_restaurant(restaurant),
        categories=[MenuCategoryOut.model_validate(c) for c in cats.scalars().all()],
        items=[MenuItemOut.model_validate(i) for i in items.scalars().all()],
    )


@router.get(
    "/t/{qr_token}/menu-item/{item_id}/options",
    response_model=list[ModifierGroupOut],
)
async def public_item_options(
    qr_token: str, item_id: uuid.UUID, db: DbSession
) -> list[ModifierGroupOut]:
    """Bir ürünün seçilebilir opsiyon grupları (boy, ekstra vb.) — müşteri seçimi için."""
    _, restaurant = await _resolve_table(db, qr_token)
    groups = await modifier_service.get_item_groups(db, restaurant.id, item_id)
    return [ModifierGroupOut.model_validate(g) for g in groups]


@router.post("/t/{qr_token}/order", response_model=OrderOut)
async def self_order(
    qr_token: str, data: PublicOrderRequest, db: DbSession
) -> OrderOut:
    """Müşterinin QR'dan verdiği sipariş — masanın aktif hesabına düşer.

    Açık hesap yoksa `qr_self_order` kaynağıyla yeni hesap açılır; varsa ona
    eklenir. Böylece personel (POS) aynı masada siparişi görür.
    """
    table, restaurant = await _resolve_table(db, qr_token)

    if not data.items:
        raise HTTPException(status_code=400, detail="Sepet boş")

    try:
        order = await order_service.open_order(
            db, restaurant.id, table.id, source="qr_self_order"
        )
        for line in data.items:
            if line.quantity < 1:
                continue
            try:
                item_id = uuid.UUID(line.menu_item_id)
                modifier_ids = [uuid.UUID(m) for m in line.modifier_ids]
            except (ValueError, TypeError) as exc:
                raise HTTPException(status_code=400, detail="Geçersiz ürün") from exc
            order = await order_service.add_item(
                db, order, item_id, line.quantity, modifier_ids=modifier_ids
            )
    except OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return OrderOut.model_validate(order)


@router.post("/t/{qr_token}/call-waiter", response_model=CallWaiterResponse)
async def call_waiter(
    qr_token: str, data: CallWaiterRequest, db: DbSession
) -> CallWaiterResponse:
    """Müşteri masadan garson çağırır. QR menü kapalıysa 404 (bkz. _resolve_table)."""
    table, restaurant = await _resolve_table(db, qr_token)
    await waiter_service.call_waiter(db, restaurant.id, table.id, data.note)
    return CallWaiterResponse()


async def _active_order(db: DbSession, qr_token: str):
    """Aktif hesabı döner ve online ödemenin açık olduğunu doğrular."""
    table, restaurant = await _resolve_table(db, qr_token)
    _require_online_payment(restaurant)
    order = await order_service.get_active_order_for_table(db, restaurant.id, table.id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bu masada açık hesap yok"
        )
    return order


@router.post("/t/{qr_token}/pay", response_model=OrderOut)
async def pay_full(qr_token: str, db: DbSession) -> OrderOut:
    order = await _active_order(db, qr_token)
    try:
        order = await order_service.pay_full(db, order, method="online")
    except OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OrderOut.model_validate(order)


@router.post("/t/{qr_token}/pay-items", response_model=OrderOut)
async def pay_items(
    qr_token: str, data: PublicPayItemsRequest, db: DbSession
) -> OrderOut:
    order = await _active_order(db, qr_token)
    try:
        ids = [uuid.UUID(x) for x in data.item_ids]
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail="Geçersiz ürün") from exc
    try:
        order = await order_service.pay_items(db, order, ids, method="online")
    except OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OrderOut.model_validate(order)


@router.post("/t/{qr_token}/pay-split", response_model=OrderOut)
async def pay_split(qr_token: str, data: PublicSplitRequest, db: DbSession) -> OrderOut:
    order = await _active_order(db, qr_token)
    if data.parts < 2:
        raise HTTPException(status_code=400, detail="En az 2 kişi olmalı")
    try:
        order = await order_service.pay_split(db, order, data.parts, method="online")
    except OrderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OrderOut.model_validate(order)
