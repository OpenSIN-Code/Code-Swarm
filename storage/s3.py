from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
import hashlib
import uuid


class S3Storage:
    """S3-compatible local storage (simulates S3 for local dev)"""

    def __init__(self, base_dir: str | Path = ".", bucket: str = "code-swarm"):
        self.base_dir = Path(base_dir)
        self.bucket = bucket
        self._storage_dir = self.base_dir / ".code-swarm" / "storage" / bucket
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self._storage_dir / ".index.json"
        self._index: dict[str, dict] = {}
        self._load_index()

    def _load_index(self):
        if self._index_file.exists():
            self._index = json.loads(self._index_file.read_text())

    def _save_index(self):
        self._index_file.write_text(json.dumps(self._index, indent=2))

    def _key_to_path(self, key: str) -> Path:
        return self._storage_dir / key.replace("/", "_")

    def upload(self, key: str, content: bytes | str, mime_type: Optional[str] = None) -> dict:
        if isinstance(content, str):
            content = content.encode("utf-8")
        
        path = self._key_to_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        
        checksum = hashlib.sha256(content).hexdigest()
        entry = {
            "key": key,
            "size_bytes": len(content),
            "checksum": checksum,
            "mime_type": mime_type or "application/octet-stream",
            "storage_path": str(path),
            "id": str(uuid.uuid4()),
        }
        self._index[key] = entry
        self._save_index()
        return entry

    def download(self, key: str) -> Optional[bytes]:
        path = self._key_to_path(key)
        if path.exists():
            return path.read_bytes()
        return None

    def delete(self, key: str):
        path = self._key_to_path(key)
        if path.exists():
            path.unlink()
        if key in self._index:
            del self._index[key]
            self._save_index()

    def list(self, prefix: str = "") -> list[dict]:
        return [
            entry for key, entry in self._index.items()
            if key.startswith(prefix)
        ]

    def get_metadata(self, key: str) -> Optional[dict]:
        return self._index.get(key)