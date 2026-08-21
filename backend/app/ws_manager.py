"""
ws_manager.py — WebSocket connection manager.
Maintains the set of active dashboard connections and broadcasts
events to all of them. Thread-safe for asyncio context.
"""
import asyncio
import json
import logging
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self._connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._connections.append(ws)
        logger.info(f"WS client connected. Total: {len(self._connections)}")

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self._connections = [c for c in self._connections if c is not ws]
        logger.info(f"WS client disconnected. Total: {len(self._connections)}")

    async def broadcast(self, payload: dict[str, Any]):
        """Broadcast a JSON-serialisable dict to all connected clients."""
        message = json.dumps(payload, default=str)
        dead: list[WebSocket] = []
        async with self._lock:
            targets = list(self._connections)

        for ws in targets:
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.warning(f"WS send failed, removing client: {e}")
                dead.append(ws)

        if dead:
            async with self._lock:
                self._connections = [c for c in self._connections if c not in dead]


# Singleton shared across the entire app
manager = ConnectionManager()
