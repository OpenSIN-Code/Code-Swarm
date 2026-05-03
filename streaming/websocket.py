from __future__ import annotations
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, status
from fastapi.exceptions import WebSocketException
from typing import Optional, Dict, Set, Any
import json
import asyncio
import logging
from datetime import datetime, timezone
from collections import deque
import os

logger = logging.getLogger("code-swarm.websocket")


class WebSocketManager:
    """Production-grade WebSocket manager with auth, rate limiting, and backpressure."""
    
    def __init__(self, max_connections_per_user: int = 5, max_message_queue: int = 100):
        self.active_connections: Dict[str, Set[WebSocket]] = {}  # user_id -> set of WebSockets
        self.message_queues: Dict[WebSocket, deque] = {}
        self.user_message_counts: Dict[str, int] = {}  # For rate limiting
        self.max_connections_per_user = max_connections_per_user
        self.max_message_queue = max_message_queue
        self.rate_limit_window = 60  # seconds
        self.rate_limit_max = 100  # messages per window
        
    async def connect(self, websocket: WebSocket, user_id: str, token: str):
        """Connect a new WebSocket with authentication."""
        # Rate limit: max connections per user
        if user_id in self.active_connections:
            if len(self.active_connections[user_id]) >= self.max_connections_per_user:
                await websocket.close(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason=f"Too many connections (max {self.max_connections_per_user})"
                )
                return False
        
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.message_queues[websocket] = deque(maxlen=self.max_message_queue)
        
        logger.info(f"WebSocket connected: user={user_id}, active={len(self.active_connections[user_id])}")
        return True
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        if websocket in self.message_queues:
            del self.message_queues[websocket]
        
        logger.info(f"WebSocket disconnected: user={user_id}")
    
    def is_rate_limited(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit."""
        current_count = self.user_message_counts.get(user_id, 0)
        return current_count >= self.rate_limit_max
    
    def increment_message_count(self, user_id: str):
        """Increment user's message count for rate limiting."""
        self.user_message_counts[user_id] = self.user_message_counts.get(user_id, 0) + 1
    
    async def broadcast(self, message: dict, exclude_user: Optional[str] = None):
        """Broadcast message to all connected clients (with backpressure)."""
        message["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        disconnected = []
        for user_id, websockets in self.active_connections.items():
            if exclude_user and user_id == exclude_user:
                continue
                
            for websocket in websockets:
                try:
                    # Backpressure: queue message if buffer is full
                    queue = self.message_queues.get(websocket)
                    if queue is not None:
                        if len(queue) >= self.max_message_queue * 0.8:  # 80% threshold
                            logger.warning(f"WebSocket backpressure: user={user_id}, queue={len(queue)}")
                            await websocket.send_json({
                                "type": "backpressure",
                                "message": "Server is under high load, please slow down",
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })
                        
                        queue.append(message)
                        await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Broadcast error for user {user_id}: {e}")
                    disconnected.append((user_id, websocket))
        
        # Clean up disconnected
        for user_id, websocket in disconnected:
            self.disconnect(websocket, user_id)
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user's connections."""
        message["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        if user_id not in self.active_connections:
            logger.warning(f"User {user_id} has no active WebSocket connections")
            return
        
        disconnected = []
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Send error to user {user_id}: {e}")
                disconnected.append(websocket)
        
        for websocket in disconnected:
            self.disconnect(websocket, user_id)
    
    async def send_to(self, websocket: WebSocket, user_id: str, message: dict):
        """Send message to specific WebSocket (with rate limiting check)."""
        if self.is_rate_limited(user_id):
            await websocket.send_json({
                "type": "error",
                "message": "Rate limit exceeded",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            return
        
        self.increment_message_count(user_id)
        message["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Send error: {e}")
            self.disconnect(websocket, user_id)
    
    def get_connection_count(self, user_id: Optional[str] = None) -> int:
        """Get connection count for a user or total."""
        if user_id:
            return len(self.active_connections.get(user_id, set()))
        return sum(len(v) for v in self.active_connections.values())
    
    def get_queue_size(self, websocket: WebSocket) -> int:
        """Get message queue size for a WebSocket."""
        return len(self.message_queues.get(websocket, deque()))


manager = WebSocketManager()
app = FastAPI()


async def verify_ws_token(token: Optional[str]) -> Optional[str]:
    """Verify WebSocket authentication token and return user_id."""
    if not token:
        return None
    
    try:
        from auth.security import AuthManager
        auth = AuthManager(secret_key=os.getenv("SECRET_KEY", "dev-key"))
        payload = auth.decode_token(token)
        return payload.get("sub")  # user_id
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None


@app.websocket("/ws/agents/{agent_id}")
async def agent_status_websocket(websocket: WebSocket, agent_id: str, token: str = Query(...)):
    """Real-time agent status updates with authentication and backpressure."""
    user_id = await verify_ws_token(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
        return
    
    if not await manager.connect(websocket, user_id, token):
        return
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await manager.send_to(websocket, user_id, {
                    "type": "pong",
                    "queue_depth": manager.get_queue_size(websocket),
                    "active_connections": manager.get_connection_count(user_id)
                })
            elif message.get("type") == "subscribe":
                # Subscribe to specific agent updates
                await manager.broadcast({
                    "type": "agent_subscribe",
                    "agent_id": agent_id,
                    "user_id": user_id
                })
            elif message.get("type") == "unsubscribe":
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for agent {agent_id}: {e}")
        manager.disconnect(websocket, user_id)


@app.websocket("/ws/tasks/{task_id}")
async def task_updates_websocket(websocket: WebSocket, task_id: str, token: str = Query(...)):
    """Real-time task progress updates with authentication."""
    user_id = await verify_ws_token(token)
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
        return
    
    if not await manager.connect(websocket, user_id, token):
        return
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await manager.send_to(websocket, user_id, {
                    "type": "pong",
                    "task_id": task_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            elif message.get("type") == "subscribe":
                logger.info(f"User {user_id} subscribed to task {task_id}")
                await manager.broadcast({
                    "type": "task_subscribe",
                    "task_id": task_id,
                    "user_id": user_id
                }, exclude_user=user_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
        manager.disconnect(websocket, user_id)


@app.post("/ws/broadcast")
async def broadcast_task_update(task_id: str, status: str, message: Optional[str] = None):
    """Server-to-client broadcast for task updates (internal use only)."""
    await manager.broadcast({
        "type": "task_update",
        "task_id": task_id,
        "status": status,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return {"broadcasted": True, "connections": manager.get_connection_count()}


@app.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "total_connections": manager.get_connection_count(),
        "users": len(manager.active_connections),
        "rate_limit_window": manager.rate_limit_window,
        "rate_limit_max": manager.rate_limit_max,
        "max_queue_size": manager.max_message_queue
    }
