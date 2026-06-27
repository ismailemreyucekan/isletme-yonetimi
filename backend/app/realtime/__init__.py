"""Gerçek zamanlı altyapı: WebSocket bağlantı yöneticisi + Redis pub/sub.

Çoklu instance ölçeklemesi için olaylar Redis kanalına yayınlanır; her instance
kendi WebSocket istemcilerine dağıtır (bkz. PLAN §7).
"""

from app.realtime.hub import hub

__all__ = ["hub"]
