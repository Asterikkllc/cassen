"""In-process TTL cache. Single dict, lazy expiry."""

from __future__ import annotations

import time
from typing import Any


class TtlCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        rec = self._store.get(key)
        if rec is None:
            return None
        expires_at, value = rec
        if expires_at < time.time():
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: float) -> Any:
        self._store[key] = (time.time() + max(0.0, ttl_seconds), value)
        return value

    def clear(self) -> None:
        self._store.clear()


CACHE = TtlCache()
