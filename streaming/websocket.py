from __future__ import annotations
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Optional
import json
import asyncio
from datetime import datetime, timezone


class WebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

    async def send_to(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except Exception:
            pass


manager = WebSocketManager()
app = FastAPI()


@app.websocket("/ws/agents")
async def agent_status_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "ping":
                await manager.send_to(websocket, {
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/ws/tasks")
async def task_updates_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await manager.broadcast({
                "type": "task_update",
                "task_id": message.get("task_id"),
                "status": message.get("status"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/ws/broadcast")
async def broadcast_task_update(task_id: str, status: str):
    await manager.broadcast({
        "type": "task_update",
        "task_id": task_id,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return {"broadcasted": True}