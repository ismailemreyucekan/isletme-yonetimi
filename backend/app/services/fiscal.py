"""Yasal/mali entegrasyon (ÖKC, e-fatura) için yer tutucu arayüz.

PLAN §5 ve §9 Faz 6 gereği: şimdilik boş implementasyon. İleride ödeme
tamamlandığında fiş/fatura üretimi bu arayüz üzerinden yapılacak.
"""

from __future__ import annotations

from typing import Protocol


class FiscalService(Protocol):
    async def issue_receipt(self, payment_id: str) -> str | None:
        """Mali fiş üretir, referans döner. Yer tutucu — None döner."""
        ...


class NoopFiscalService:
    """Hiçbir şey yapmayan varsayılan implementasyon (MVP)."""

    async def issue_receipt(self, payment_id: str) -> str | None:
        return None


def get_fiscal_service() -> FiscalService:
    return NoopFiscalService()
