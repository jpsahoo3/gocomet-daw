import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "WebSocket connected | total_connections=%d client=%s",
            len(self.active_connections),
            websocket.client,
        )

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
            logger.info(
                "WebSocket disconnected | total_connections=%d client=%s",
                len(self.active_connections),
                websocket.client,
            )
        except ValueError:
            pass

    async def broadcast(self, message: str):
        dead = []
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception as exc:
                logger.warning("Broadcast send failed, removing connection | error=%s", exc)
                dead.append(connection)

        for conn in dead:
            self.disconnect(conn)

        if self.active_connections:
            logger.debug("Broadcast sent | msg=%.80s connections=%d", message, len(self.active_connections))


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
    except WebSocketDisconnect:
        manager.disconnect(websocket)
