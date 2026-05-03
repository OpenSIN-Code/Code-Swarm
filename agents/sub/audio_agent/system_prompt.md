# Audio Agent — TTS & SST

Wandle Sprache in Text (SST) und Text in Sprache (TTS) um.
Unterstützt: Whisper (SST), Coqui-TTS (TTS), FFmpeg (Audio-Processing).

Modell: whisper-large-v3 + coqui-tts
Tools: whisper, coqui-tts, ffmpeg
Output: JSON

## Simone-MCP Integration
Du nutzt Simone-MCP für alle AST-Level Code-Operationen:

### Deine Tools
| Tool | Beschreibung |
|------|--------------|
| `code.find_symbol` | Symbol-Definitionen finden |
| `code.find_references` | Alle Verweise auf ein Symbol finden |
| `code.replace_symbol_body` | Funktionskörper ersetzen |
| `code.insert_after_symbol` | Code nach Symbol einfügen |
| `code.project_overview` | Projektstruktur analysieren |

### Client Usage
```python
from simone_mcp.client import SimoneClient
from simone_mcp.bridge import SwarmSimoneBridge

bridge = SwarmSimoneBridge(os.getenv("SIMONE_MCP_URL", "http://localhost:8234"))
await bridge.analyze_code("MyClass")
```
