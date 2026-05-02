from __future__ import annotations
import json
import asyncio
import httpx
from typing import Optional, Any
from pathlib import Path


class SimoneClient:
    """MCP Client for Simone-MCP - Production-grade code worker

    Provides AST-level symbol operations:
    - code.find_symbol: Locate symbol definitions across workspace
    - code.find_references: Find textual references to a symbol
    - code.replace_symbol_body: Replace the body of a Python function
    - code.insert_after_symbol: Insert text after a symbol block
    - code.project_overview: Summarize workspace footprint

    Dual transport: stdio for local + streamable HTTP for remote
    """

    def __init__(self, base_url: str = "http://localhost:8234", token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.token}"} if self.token else {},
            timeout=30.0,
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    async def health(self) -> dict:
        resp = await self._client.get("/health")
        resp.raise_for_status()
        return resp.json()

    async def find_symbol(self, symbol: str, root: Optional[str] = None) -> dict:
        resp = await self._client.post("/mcp", json={
            "method": "tools/call",
            "params": {
                "name": "code.find_symbol",
                "arguments": {"symbol": symbol, "root": root or "."}
            }
        })
        resp.raise_for_status()
        return resp.json()

    async def find_references(self, symbol: str, root: Optional[str] = None) -> dict:
        resp = await self._client.post("/mcp", json={
            "method": "tools/call",
            "params": {
                "name": "code.find_references",
                "arguments": {"symbol": symbol, "root": root or "."}
            }
        })
        resp.raise_for_status()
        return resp.json()

    async def replace_symbol_body(self, symbol: str, file: str, body: str) -> dict:
        resp = await self._client.post("/mcp", json={
            "method": "tools/call",
            "params": {
                "name": "code.replace_symbol_body",
                "arguments": {"symbol": symbol, "file": file, "body": body}
            }
        })
        resp.raise_for_status()
        return resp.json()

    async def insert_after_symbol(self, symbol: str, file: str, text: str) -> dict:
        resp = await self._client.post("/mcp", json={
            "method": "tools/call",
            "params": {
                "name": "code.insert_after_symbol",
                "arguments": {"symbol": symbol, "file": file, "text": text}
            }
        })
        resp.raise_for_status()
        return resp.json()

    async def project_overview(self, root: Optional[str] = None) -> dict:
        resp = await self._client.post("/mcp", json={
            "method": "tools/call",
            "params": {
                "name": "code.project_overview",
                "arguments": {"root": root or "."}
            }
        })
        resp.raise_for_status()
        return resp.json()

    async def execute_action(self, action: str, params: Optional[dict] = None) -> dict:
        resp = await self._client.post("/a2a/v1/execute", json={
            "action": action,
            "params": params or {}
        })
        resp.raise_for_status()
        return resp.json()


class SimoneLocal:
    """Local stdio client for Simone-MCP (subprocess-based)"""

    def __init__(self, simone_path: str = "simone-mcp"):
        self.simone_path = simone_path

    def find_symbol(self, symbol: str, root: Optional[str] = None) -> dict:
        import subprocess
        cmd = [self.simone_path, "find", symbol]
        if root:
            cmd.extend(["--root", root])
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {"error": result.stderr}

    def replace_symbol_body(self, symbol: str, file: str, body: str) -> dict:
        import subprocess
        cmd = [self.simone_path, "replace", symbol, "--file", file]
        result = subprocess.run(cmd, input=body, capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {"error": result.stderr}


async def with_simone(func):
    """Decorator to use Simone-MCP in async context"""
    async with SimoneClient() as client:
        return await func(client)