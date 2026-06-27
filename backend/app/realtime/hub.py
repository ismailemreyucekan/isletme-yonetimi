"""WebSocket hub: kiracı bazlı kanallara abonelik + Redis pub/sub yayını.

Kanal yapısı (bkz. PLAN §7): `restaurant:{id}:{topic}` — örn. topic = "kds" | "pos".
Bir olay yayınlanınca: (1) Redis kanalına basılır, (2) Redis dinleyicisi tüm
instance'larda ilgili WebSocket'lere dağıtır.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from typing import Any

import redis.asyncio as redis
from fastapi import WebSocket

from app.core.config import settings

logger = logging.getLogger(__name__)

REDIS_CHANNEL = "kasa:events"


class RealtimeHub:
    def __init__(self) -> None:
        # channel -> bağlı WebSocket'ler
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._redis: redis.Redis | None = None
        self._pubsub_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Uygulama açılışında Redis pub/sub dinleyicisini başlatır."""
        self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        self._pubsub_task = asyncio.create_task(self._listen())
        logger.info("RealtimeHub başlatıldı")

    async def stop(self) -> None:
        if self._pubsub_task:
            self._pubsub_task.cancel()
        if self._redis:
            await self._redis.aclose()

    async def _listen(self) -> None:
        """Redis kanalını dinler; timeout/kopmada dayanıklı şekilde yeniden bağlanır."""
        assert self._redis is not None
        while True:
            try:
                pubsub = self._redis.pubsub()
                await pubsub.subscribe(REDIS_CHANNEL)
                while True:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=1.0
                    )
                    if message is None:
                        continue
                    try:
                        payload = json.loads(message["data"])
                    except (ValueError, TypeError):
                        continue
                    await self._dispatch(
                        payload.get("channel", ""), payload.get("event", {})
                    )
            except asyncio.CancelledError:
                raise
            except Exception:  # pragma: no cover - dayanıklılık
                logger.warning("Redis pubsub yeniden bağlanıyor", exc_info=True)
                await asyncio.sleep(1.0)

    async def _dispatch(self, channel: str, event: dict[str, Any]) -> None:
        """Bu instance'taki ilgili WebSocket'lere olayı gönderir."""
        conns = list(self._connections.get(channel, set()))
        for ws in conns:
            try:
                await ws.send_json(event)
            except Exception:
                await self.disconnect(channel, ws)

    @staticmethod
    def channel(restaurant_id: str, topic: str) -> str:
        return f"restaurant:{restaurant_id}:{topic}"

    async def connect(self, channel: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections[channel].add(ws)

    async def disconnect(self, channel: str, ws: WebSocket) -> None:
        async with self._lock:
            self._connections[channel].discard(ws)
            if not self._connections[channel]:
                self._connections.pop(channel, None)

    async def publish(self, channel: str, event: dict[str, Any]) -> None:
        """Olayı Redis'e basar; tüm instance'lar kendi istemcilerine dağıtır."""
        if self._redis is None:
            # Redis yoksa (ör. test) doğrudan yerel dağıt.
            await self._dispatch(channel, event)
            return
        await self._redis.publish(
            REDIS_CHANNEL, json.dumps({"channel": channel, "event": event})
        )


hub = RealtimeHub()
