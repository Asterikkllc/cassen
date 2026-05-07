"""Combine providers behind a single fallback chain.

search_part: Nexar → Mouser → curated
get_part:    Nexar → Digi-Key → Mouser → curated

Each result is annotated with its `source` so the agent (or a debugger)
can tell which provider produced a row. Curated alternatives stay
authoritative for `recommend_alternative` since live distributor APIs
don't expose "functional substitutes".
"""

from __future__ import annotations

from typing import Any

from .cache import CACHE
from .config import get_settings
from .providers.base import PartProvider
from .providers.curated import CuratedProvider
from .providers.digikey import DigiKeyProvider
from .providers.mouser import MouserProvider
from .providers.nexar import NexarProvider


class Aggregator:
    def __init__(self) -> None:
        self.curated = CuratedProvider()
        self.nexar = NexarProvider()
        self.mouser = MouserProvider()
        self.digikey = DigiKeyProvider()
        self._s = get_settings()

    @property
    def search_chain(self) -> list[PartProvider]:
        return [
            p
            for p in (self.nexar, self.mouser, self.curated)
            if p.configured
        ]

    @property
    def get_chain(self) -> list[PartProvider]:
        return [
            p
            for p in (self.nexar, self.digikey, self.mouser, self.curated)
            if p.configured
        ]

    def list_categories(self) -> dict[str, Any]:
        return {
            "categories": self.curated.categories,
            "curated_part_count": len(self.curated._parts),
            "schema_version": self.curated.schema_version,
            "configured_providers": [
                p.name
                for p in (self.nexar, self.mouser, self.digikey, self.curated)
                if p.configured
            ],
        }

    def search(
        self,
        query: str,
        *,
        category: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        cache_key = f"search:{query}:{category or '*'}:{limit}"
        cached = CACHE.get(cache_key)
        if cached:
            return cached

        attempts: list[dict[str, Any]] = []
        for p in self.search_chain:
            try:
                results = p.search(query, category=category, limit=limit)
            except Exception as exc:  # noqa: BLE001
                attempts.append({"provider": p.name, "error": str(exc), "count": 0})
                continue
            attempts.append({"provider": p.name, "count": len(results)})
            if results:
                payload = {
                    "query": query,
                    "category": category,
                    "results": results,
                    "returned": len(results),
                    "source": p.name,
                    "attempts": attempts,
                }
                return CACHE.set(cache_key, payload, self._s.search_cache_ttl_s)

        return {
            "query": query,
            "category": category,
            "results": [],
            "returned": 0,
            "source": None,
            "attempts": attempts,
        }

    def get(self, mpn: str) -> dict[str, Any]:
        if not mpn:
            return {"error": "mpn is required"}
        cache_key = f"get:{mpn}"
        cached = CACHE.get(cache_key)
        if cached:
            return cached

        attempts: list[dict[str, Any]] = []
        for p in self.get_chain:
            try:
                part = p.get(mpn)
            except Exception as exc:  # noqa: BLE001
                attempts.append({"provider": p.name, "error": str(exc)})
                continue
            attempts.append({"provider": p.name, "found": bool(part)})
            if part:
                payload = {
                    "part": part,
                    "source": p.name,
                    "attempts": attempts,
                }
                return CACHE.set(cache_key, payload, self._s.part_cache_ttl_s)

        return {
            "error": f"part not found: {mpn}",
            "attempts": attempts,
        }

    def recommend_alternative(
        self,
        mpn: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        if not mpn:
            return {"error": "mpn is required"}
        # Curated alternatives only — see module docstring.
        alternatives, missing = self.curated.find_alternatives(mpn)
        # If curated has no record but live providers do, return a stub
        # so the agent gets useful context.
        if not alternatives and not missing and not self.curated.get(mpn):
            live = self.get(mpn)
            if "part" in live:
                return {
                    "original_mpn": mpn,
                    "reason": reason,
                    "alternatives": [],
                    "missing_from_dataset": [],
                    "note": (
                        "Curated dataset has no alternatives entry for this MPN. "
                        "Live data from "
                        f"{live.get('source')} is available via get_part."
                    ),
                }
        original = self.curated.get(mpn) or {}
        return {
            "original_mpn": original.get("mpn") or mpn,
            "reason": reason,
            "alternatives": alternatives,
            "missing_from_dataset": missing,
        }


_aggregator: Aggregator | None = None


def get_aggregator() -> Aggregator:
    global _aggregator
    if _aggregator is None:
        _aggregator = Aggregator()
    return _aggregator
