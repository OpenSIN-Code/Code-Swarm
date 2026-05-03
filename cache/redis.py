from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid


@dataclass
class CacheEntry:
    key: str
    value: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None
    hits: int = 0


class RedisCache:
    """Redis-compatible in-memory cache with TTL support"""

    def __init__(self, base_dir: str | Path = ".", ttl_seconds: int = 3600):
        self.base_dir = Path(base_dir)
        self._cache_dir = self.base_dir / ".code-swarm" / "cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, CacheEntry] = {}
        self._ttl = ttl_seconds
        self._load()

    def _load(self):
        cache_file = self._cache_dir / "cache.json"
        if cache_file.exists():
            data = json.loads(cache_file.read_text())
            self._cache = {k: CacheEntry(**v) for k, v in data.items()}
            self._cleanup_expired()

    def _save(self):
        cache_file = self._cache_dir / "cache.json"
        cache_file.write_text(
            json.dumps({k: asdict(v) for k, v in self._cache.items()}, indent=2)
        )

    def _cleanup_expired(self):
        now = datetime.now(timezone.utc)
        expired = []
        for key, entry in self._cache.items():
            if entry.expires_at:
                expires = datetime.fromisoformat(entry.expires_at)
                if expires.tzinfo is None:
                    expires = expires.replace(tzinfo=timezone.utc)
                if expires < now:
                    expired.append(key)
        for key in expired:
            del self._cache[key]

    def get(self, key: str) -> Optional[str]:
        entry = self._cache.get(key)
        if not entry:
            return None
        if entry.expires_at:
            expires = datetime.fromisoformat(entry.expires_at)
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < datetime.now(timezone.utc):
                del self._cache[key]
                self._save()
                return None
        entry.hits += 1
        return entry.value

    def set(self, key: str, value: str, ttl: Optional[int] = None):
        ttl = ttl or self._ttl
        expires = None
        if ttl > 0:
            expires = (datetime.now(timezone.utc).timestamp() + ttl)
        entry = CacheEntry(
            key=key,
            value=value,
            expires_at=datetime.fromtimestamp(expires, tz=timezone.utc).isoformat() if expires else None
        )
        self._cache[key] = entry
        self._save()

    def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]
            self._save()

    def clear(self):
        self._cache.clear()
        self._save()

    def stats(self) -> dict:
        self._cleanup_expired()
        return {
            "total_keys": len(self._cache),
            "total_hits": sum(e.hits for e in self._cache.values()),
        }


def asdict(obj):
    if hasattr(obj, "__dataclass_fields__"):
        return {
            f: getattr(obj, f) 
            for f in obj.__dataclass_fields__
        }
    raise TypeError(f"Cannot convert {type(obj)}")