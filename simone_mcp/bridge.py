from __future__ import annotations
from typing import Optional
import os
from .client import SimoneClient, SimoneLocal


SIMONE_TOOL_PROMPT = """
## Simone-MCP Tools (AST-level Code Operations)

Every agent MUST use Simone-MCP for code navigation and transformation:

### Available Tools
| Tool | Purpose | Use Case |
|------|---------|----------|
| `code.find_symbol` | Locate symbol definitions | "Find where isFunction is defined" |
| `code.find_references` | Find all usages | "Find all places using isFunction" |
| `code.replace_symbol_body` | Replace function body | "Update isFunction implementation" |
| `code.insert_after_symbol` | Insert after symbol | "Add logging after isFunction" |
| `code.project_overview` | Workspace summary | "Analyze project structure" |

### Usage Pattern
```python
from simone_mcp.client import SimoneClient

async with SimoneClient("http://localhost:8234") as simone:
    result = await simone.find_symbol("MyClass", root="/path/to/project")
    # result contains file:line for symbol definition
```

### Integration Points
- LangGraph nodes use simone for code analysis
- All agent prompts include simone_mcp tool descriptions
- Memory layer integrates with simone's hybrid memory (Qdrant + Neo4j)
"""


class SwarmSimoneBridge:
    """Bridge between Code-Swarm agents and Simone-MCP

    Every Code-Swarm agent gets simone-mcp capabilities via this bridge.
    Supports both:
    - Remote: configured via SIMONE_MCP_URL env var (default: OCI VM http://92.5.60.87:8234)
    - Local: /Users/jeremy/dev/Simone-MCP (development, optional)
    """

    def __init__(self, simone_url: Optional[str] = None, token: Optional[str] = None, local: bool = False):
        # Respect environment variable first
        if simone_url is None:
            simone_url = os.getenv("SIMONE_MCP_URL", "http://92.5.60.87:8234")
        self.simone_url = simone_url
        self.token = token
        self.local = local
        self._local_path = os.getenv("SIMONE_MCP_LOCAL_PATH", "/Users/jeremy/dev/Simone-MCP")
        
    def is_remote_available(self) -> bool:
        """Check if remote Simone-MCP server is available."""
        import urllib.request
        try:
            with urllib.request.urlopen(self.simone_url + "/health", timeout=5) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def analyze_code(self, symbol: str, root: str = ".") -> dict:
        async with SimoneClient(self.simone_url, self.token) as client:
            return await client.find_symbol(symbol, root)

    async def find_usages(self, symbol: str, root: str = ".") -> dict:
        async with SimoneClient(self.simone_url, self.token) as client:
            return await client.find_references(symbol, root)

    async def modify_code(self, symbol: str, file: str, body: str) -> dict:
        async with SimoneClient(self.simone_url, self.token) as client:
            return await client.replace_symbol_body(symbol, file, body)

    async def inject_code(self, symbol: str, file: str, text: str) -> dict:
        async with SimoneClient(self.simone_url, self.token) as client:
            return await client.insert_after_symbol(symbol, file, text)

    async def get_project_summary(self, root: str = ".") -> dict:
        async with SimoneClient(self.simone_url, self.token) as client:
            return await client.project_overview(root)

    def get_tools_prompt(self) -> str:
        return SIMONE_TOOL_PROMPT
