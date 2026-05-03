from __future__ import annotations
import time
from typing import Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Ultra low-latency rate limiter (50 req/sec per IP)."""

    def __init__(self, app, max_requests: int = 50, window_seconds: int = 1):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self.clients: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        if client_ip not in self.clients:
            self.clients[client_ip] = []

        self.clients[client_ip] = [
            t for t in self.clients[client_ip]
            if now - t < self.window
        ]

        if len(self.clients[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.max_requests} requests per {self.window}s"
            )

        self.clients[client_ip].append(now)
        return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request/response logging for audit trails."""

    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        response.headers["X-Response-Time"] = str(duration)
        return response
