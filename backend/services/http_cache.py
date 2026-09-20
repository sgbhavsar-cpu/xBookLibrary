"""File-based JSON cache with TTL for upstream HTTP responses."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional


class HttpCache:
    """Caches external API responses as JSON files in .vectors/cache/ with TTL."""

    def __init__(self, cache_dir: Path, default_ttl_seconds: int = 7 * 86400):
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl_seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _hash_key(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Retrieves cached payload if present and not expired."""
        h = self._hash_key(key)
        cache_file = self.cache_dir / f"{h}.json"
        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                entry = json.load(f)

            expires_at = entry.get("expires_at", 0)
            if time.time() > expires_at:
                cache_file.unlink(missing_ok=True)
                return None

            return entry.get("payload")
        except Exception:
            return None

    def set(self, key: str, payload: Any, ttl_seconds: Optional[int] = None) -> None:
        """Stores a JSON-serializable payload in the cache."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        h = self._hash_key(key)
        cache_file = self.cache_dir / f"{h}.json"

        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        entry = {
            "key": key,
            "created_at": time.time(),
            "expires_at": time.time() + ttl,
            "payload": payload,
        }

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2)
        except Exception:
            pass

    def clear(self) -> int:
        """Clears all cached files and returns count removed."""
        count = 0
        if self.cache_dir.exists():
            for f in self.cache_dir.glob("*.json"):
                f.unlink(missing_ok=True)
                count += 1
        return count
