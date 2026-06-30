"""Tenant (işletme) özellik bayrakları — opsiyonel modüllerin aç/kapa kontrolü.

Çekirdek POS (hesap açma/kapatma, ödeme alma) her zaman açıktır ve burada yer
almaz. Yalnızca *opsiyonel* modüller (QR menü, online ödeme vb.) bayraklanır;
böylece platform yöneticisi her işletmeye anlaşmaya göre özellik açıp kapatabilir.

Bir özelliğin etkin olup olmadığı şu sırayla belirlenir (ilk bulunan kazanır):
  1. `restaurant.settings["features"][<feature>]` — işletmeye özel override
  2. `PLAN_FEATURES[restaurant.plan][<feature>]` — paketin varsayılanı
  3. `DEFAULTS[<feature>]` — global güvenli varsayılan (genelde kapalı)
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.restaurant import Restaurant


class Feature(StrEnum):
    """Aç/kapa yapılabilen opsiyonel modüller."""

    QR_MENU = "qr_menu"  # müşterinin QR'dan menüyü görmesi + self-order
    ONLINE_PAYMENT = "online_payment"  # QR'dan online ödeme (pay / pay-items / split)
    KDS = "kds"  # mutfak ekranı (Kitchen Display System)
    COUPONS = "coupons"  # kupon / indirim modülü


# Anlaşma yapılmamış işletme için güvenli global varsayılanlar.
DEFAULTS: dict[Feature, bool] = {
    Feature.QR_MENU: False,
    Feature.ONLINE_PAYMENT: False,
    Feature.KDS: True,
    Feature.COUPONS: True,
}

# Paket bazlı varsayılanlar — işletmeye özel override yoksa bunlar uygulanır.
PLAN_FEATURES: dict[str, dict[Feature, bool]] = {
    "free": {
        Feature.QR_MENU: False,
        Feature.ONLINE_PAYMENT: False,
    },
    "pro": {
        Feature.QR_MENU: True,
        Feature.ONLINE_PAYMENT: True,
    },
}


def is_enabled(restaurant: Restaurant, feature: Feature) -> bool:
    """Verilen işletmede özelliğin etkin olup olmadığını döner."""
    overrides = (restaurant.settings or {}).get("features", {})
    if isinstance(overrides, dict) and feature.value in overrides:
        return bool(overrides[feature.value])

    plan_defaults = PLAN_FEATURES.get(restaurant.plan, {})
    if feature in plan_defaults:
        return plan_defaults[feature]

    return DEFAULTS[feature]


def effective_features(restaurant: Restaurant) -> dict[str, bool]:
    """Tüm özelliklerin işletme için nihai (çözülmüş) durumunu döner.

    Frontend'in butonları gösterip gizlemesi ve admin panelinin mevcut durumu
    göstermesi için kullanılır.
    """
    return {f.value: is_enabled(restaurant, f) for f in Feature}
