import asyncio
from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        try:
            self.active_connections.remove(websocket)
        except ValueError:
            pass

    async def broadcast(self, message: str):
        # send to all active connections, ignore send errors per connection
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                try:
                    self.disconnect(connection)
                except Exception:
                    pass


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # keep connection alive; try to receive with short timeout so
        # broadcast tasks can run concurrently and disconnects are detected
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=0.5)
            except asyncio.TimeoutError:
                # timeout is expected; continue loop to keep alive
                continue
    except WebSocketDisconnect:
        manager.disconnect(websocket)
