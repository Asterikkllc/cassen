"""Provider interface for parts data sources.

Each concrete provider (Nexar, Mouser, Digi-Key, curated JSON) implements
this surface. All return parts in the same normalized dict shape so the
aggregator can merge across sources without per-provider code paths.

Normalized part shape:
{
    "mpn": str,
    "manufacturer": str | None,
    "category": str | None,
    "subcategory": str | None,
    "description": str | None,
    "datasheet_url": str | None,
    "lifecycle": "active" | "nrnd" | "obsolete" | "preview" | "unknown" | None,
    "typical_unit_price_usd": float | None,
    "key_specs": dict | None,
    "packages": list[str] | None,
    "alternatives": list[str] | None,
    "tags": list[str] | None,
    "source": "nexar" | "mouser" | "digikey" | "curated",
    # Optional: provider-specific extras
    "source_url": str | None,
}
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PartProvider(ABC):
    name: str

    @property
    @abstractmethod
    def configured(self) -> bool:
        """True when the provider has the env vars it needs."""

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Return up to `limit` normalized parts. Empty list on miss."""

    @abstractmethod
    def get(self, mpn: str) -> dict[str, Any] | None:
        """Return a single normalized part by exact MPN, or None."""


def normalize_lifecycle(raw: str | None) -> str | None:
    if not raw:
        return None
    s = raw.strip().lower()
    if any(k in s for k in ("active", "production")):
        return "active"
    if any(k in s for k in ("not recommended", "nrnd")):
        return "nrnd"
    if any(k in s for k in ("obsolete", "discontinued", "eol", "end of life")):
        return "obsolete"
    if any(k in s for k in ("preview", "preliminary", "pre-release")):
        return "preview"
    return s or "unknown"
