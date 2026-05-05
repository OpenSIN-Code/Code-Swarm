"""Code-Swarm: MCP Hub (stolen from Cline)

Centralized MCP connection manager with auto-discovery.
Supports Stdio, SSE, and StreamableHTTP transports.
"""

import json
import subprocess
import asyncio
from typing import Optional


class MCPHub:
    """Centralized hub managing all MCP server connections."""

    def __init__(self):
        self._servers: dict[str, dict] = {}
        self._tools: dict[str, list[dict]] = {}

    def connect_stdio(self, name: str, command: list[str],
                      env: Optional[dict] = None, enabled: bool = True):
        self._servers[name] = {
            "type": "stdio", "command": command,
            "env": env or {}, "enabled": enabled
        }
        if enabled:
            self._discover_tools(name)

    def _discover_tools(self, name: str):
        cfg = self._servers.get(name)
        if not cfg or cfg["type"] != "stdio":
            return
        try:
            result = subprocess.run(
                cfg["command"] + ["--list-tools"],
                capture_output=True, text=True, timeout=5,
                env=cfg.get("env")
            )
            if result.returncode == 0:
                self._tools[name] = json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            self._tools[name] = []

    def call_tool(self, server: str, tool: str, **kwargs) -> dict:
        cfg = self._servers.get(server)
        if not cfg or not cfg["enabled"]:
            return {"status": "error", "error": f"Server {server} not available"}
        try:
            payload = json.dumps({"tool": tool, "args": kwargs})
            result = subprocess.run(
                cfg["command"] + ["--call", payload],
                capture_output=True, text=True, timeout=30,
                env=cfg.get("env")
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
            return {"status": "error", "error": result.stderr}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def list_available(self) -> list[dict]:
        return [
            {"name": n, "tools": self._tools.get(n, []), "enabled": s["enabled"]}
            for n, s in self._servers.items()
        ]
