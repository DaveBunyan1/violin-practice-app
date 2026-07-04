import asyncio
from typing import List

from app.models.events import WebSocketBroadcastEvent


class EventBus:
    def __init__(self):
        self._subscribers: List[asyncio.Queue[WebSocketBroadcastEvent]] = []
        self._lock = asyncio.Lock()

    async def subscribe(self) -> asyncio.Queue[WebSocketBroadcastEvent]:
        queue: asyncio.Queue[WebSocketBroadcastEvent] = asyncio.Queue(maxsize=100)

        async with self._lock:
            self._subscribers.append(queue)

        return queue

    async def publish(self, event: WebSocketBroadcastEvent):
        async with self._lock:
            queues = list(self._subscribers)

        for q in queues:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # Drop oldest item, then retry once
                try:
                    _ = q.get_nowait()
                    q.put_nowait(event)
                except asyncio.QueueEmpty:
                    pass

    async def unsubscribe(self, queue: asyncio.Queue[WebSocketBroadcastEvent]):
        async with self._lock:
            try:
                self._subscribers.remove(queue)
            except ValueError:
                pass
