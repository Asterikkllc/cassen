"""Live-only provider chain. No in-repo dataset.

Chains:
    search_part:           Nexar -> Mouser
    get_part:              Nexar -> Digi-Key -> Mouser
    recommend_alternative: get_part -> derive an MPN family prefix ->
                           search the chain again, drop the original

Each result is annotated with `source` so the caller (or a debugger) can
tell which provider produced the row, and a full `attempts` trace
documents every provider that was tried.
"""

from __future__ import annotations

from typing import Any

from .cache import CACHE
from .config import get_settings
from .providers.base import PartProvider
from .providers.digikey import DigiKeyProvider
from .providers.mouser import MouserProvider
from .providers.nexar import NexarProvider

# Distributors don't share a single taxonomy. We surface a small handful of
# common categories so the agent has sensible defaults to filter by; the
# actual category strings on returned rows come from each distributor.
_COMMON_CATEGORIES = [
    "microcontroller",
    "sensor",
    "power",
    "communication",
    "driver",
    "actuator",
    "passive",
    "connector",
]


def _mpn_family(mpn: str) -> str:
    """Heuristic family prefix used to seed alternative lookups.

    Takes the first hyphen-separated chunk and caps at 6 characters.
    Examples:
      ESP32-WROOM-32E -> ESP32
      ATmega328P-PU   -> ATmega
      STM32F103C8T6   -> STM32F
      L298N           -> L298N
    """
    if not mpn:
        return ""
    head = mpn.split("-", 1)[0]
    return head[:6]


class Aggregator:
    def __init__(self) -> None:
        self.nexar = NexarProvider()
        self.mouser = MouserProvider()
        self.digikey = DigiKeyProvider()
        self._s = get_settings()

    @property
    def search_chain(self) -> list[PartProvider]:
        # Digi-Key first because Nexar's free tier has a tight daily quota
        # (10 parts/day) — Digi-Key's keyword search is more generous in
        # practice. Mouser slots in as the third option once its key is
        # activated.
        return [
            p
            for p in (self.digikey, self.nexar, self.mouser)
            if p.configured
        ]

    @property
    def get_chain(self) -> list[PartProvider]:
        return [
            p
            for p in (self.digikey, self.nexar, self.mouser)
            if p.configured
        ]

    def list_categories(self) -> dict[str, Any]:
        configured = [
            p.name
            for p in (self.nexar, self.mouser, self.digikey)
            if p.configured
        ]
        return {
            "common_categories": _COMMON_CATEGORIES,
            "configured_providers": configured,
            "note": (
                "Each distributor uses its own taxonomy; rows returned by "
                "search_part / get_part carry the provider's category string. "
                "common_categories are sensible defaults to use as the "
                "`category` filter on search_part."
            ),
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

        if not self.search_chain:
            return {
                "query": query,
                "category": category,
                "results": [],
                "returned": 0,
                "source": None,
                "attempts": [],
                "error": "No live providers configured (set NEXAR_* or MOUSER_API_KEY).",
            }

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

        if not self.get_chain:
            return {
                "error": "No live providers configured (set NEXAR_*, DIGIKEY_*, or MOUSER_API_KEY).",
                "attempts": [],
            }

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
        limit: int = 5,
    ) -> dict[str, Any]:
        """Family-prefix search across live providers, with the original
        MPN filtered out. Best-effort — distributor APIs don't expose a
        first-class 'functional substitute' relationship.
        """
        if not mpn:
            return {"error": "mpn is required"}

        original = self.get(mpn)
        if "error" in original:
            return {
                "original_mpn": mpn,
                "reason": reason,
                "alternatives": [],
                "error": original["error"],
                "attempts": original.get("attempts", []),
            }

        family = _mpn_family(mpn)
        sr = self.search(family, limit=max(limit + 3, 6))
        target = mpn.upper()
        original_part = original.get("part") or {}
        candidates = [
            r
            for r in (sr.get("results") or [])
            if (r.get("mpn") or "").upper() != target
            and (r.get("mpn") or "").upper() != (original_part.get("mpn") or "").upper()
        ][:limit]

        return {
            "original_mpn": original_part.get("mpn") or mpn,
            "reason": reason,
            "family_query": family,
            "alternatives": candidates,
            "search_attempts": sr.get("attempts", []),
            "get_attempts": original.get("attempts", []),
            "note": (
                "Family-prefix heuristic. For a tighter list, call search_part "
                "with the same category as the original (returned in the part "
                "body) and review by spec."
            ),
        }


_aggregator: Aggregator | None = None


def get_aggregator() -> Aggregator:
    global _aggregator
    if _aggregator is None:
        _aggregator = Aggregator()
    return _aggregator


