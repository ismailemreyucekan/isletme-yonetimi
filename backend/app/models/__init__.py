"""SQLAlchemy modelleri. Alembic'in tabloları görebilmesi için burada toplanır."""

from app.models.base import Base
from app.models.coupon import Coupon, CouponMode
from app.models.menu import MenuCategory, MenuItem
from app.models.modifier import (
    MenuItemModifierGroup,
    Modifier,
    ModifierGroup,
    OrderItemModifier,
    SelectionType,
)
from app.models.order import (
    KitchenStatus,
    Order,
    OrderItem,
    OrderSource,
    OrderStatus,
    PaidStatus,
)
from app.models.payment import (
    Payment,
    PaymentMethod,
    PaymentStatus,
    SplitType,
)
from app.models.platform_admin import PlatformAdmin
from app.models.restaurant import Restaurant
from app.models.table import Table
from app.models.user import User, UserRole
from app.models.waiter_call import WaiterCall, WaiterCallStatus

__all__ = [
    "Base",
    "Coupon",
    "CouponMode",
    "MenuCategory",
    "MenuItem",
    "MenuItemModifierGroup",
    "Modifier",
    "ModifierGroup",
    "OrderItemModifier",
    "SelectionType",
    "KitchenStatus",
    "Order",
    "OrderItem",
    "OrderSource",
    "OrderStatus",
    "PaidStatus",
    "Payment",
    "PaymentMethod",
    "PaymentStatus",
    "PlatformAdmin",
    "Restaurant",
    "SplitType",
    "Table",
    "User",
    "UserRole",
    "WaiterCall",
    "WaiterCallStatus",
]
