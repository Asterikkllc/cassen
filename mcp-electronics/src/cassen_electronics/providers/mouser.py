"""Mouser keyword search provider. Single API key, no OAuth dance."""

from __future__ import annotations

import re
from typing import Any

import httpx

from ..config import get_settings
from .base import PartProvider, normalize_lifecycle

KEYWORD_URL = "https://api.mouser.com/api/v2/search/keyword"
PARTNUM_URL = "https://api.mouser.com/api/v2/search/partnumber"

_PRICE_RE = re.compile(r"([\d,]+\.?\d*)")


def _parse_unit_price_usd(price_breaks: list[dict[str, Any]] | None) -> float | None:
    if not price_breaks:
        return None
    first = price_breaks[0]
    if first.get("Currency") not in (None, "USD", "$"):
        return None
    raw = first.get("Price") or ""
    m = _PRICE_RE.search(str(raw).replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


def _normalize(part: dict[str, Any]) -> dict[str, Any]:
    return {
        "mpn": part.get("ManufacturerPartNumber") or "",
        "manufacturer": part.get("Manufacturer"),
        "category": part.get("Category"),
        "subcategory": None,
        "description": part.get("Description"),
        "datasheet_url": part.get("DataSheetUrl"),
        "lifecycle": normalize_lifecycle(part.get("LifecycleStatus")),
        "typical_unit_price_usd": _parse_unit_price_usd(part.get("PriceBreaks") or []),
        "key_specs": None,
        "packages": None,
        "alternatives": None,
        "tags": None,
        "source": "mouser",
        "source_url": part.get("ProductDetailUrl"),
    }


class MouserProvider(PartProvider):
    name = "mouser"

    def __init__(self) -> None:
        self._s = get_settings()

    @property
    def configured(self) -> bool:
        return self._s.mouser_configured

    def _post(self, url: str, body: dict[str, Any]) -> dict[str, Any] | None:
        if not self.configured:
            return None
        try:
            resp = httpx.post(
                url,
                params={"apiKey": self._s.mouser_api_key},
                json=body,
                timeout=self._s.request_timeout_s,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:  # noqa: BLE001
            return None

    def search(
        self,
        query: str,
        *,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        if not self.configured:
            return []
        q = (query or "").strip()
        if not q:
            return []
        body = {
            "SearchByKeywordRequest": {
                "keyword": q,
                "records": min(max(1, limit), 50),
                "startingRecord": 0,
                "searchOptions": "InStock",
            }
        }
        data = self._post(KEYWORD_URL, body)
        if not data:
            return []
        parts = ((data.get("SearchResults") or {}).get("Parts")) or []
        out: list[dict[str, Any]] = []
        for p in parts:
            normalized = _normalize(p)
            if category and (normalized.get("category") or "").lower() != category.lower():
                continue
            out.append(normalized)
        return out[:limit]

    def get(self, mpn: str) -> dict[str, Any] | None:
        if not self.configured or not mpn:
            return None
        body = {"SearchByPartRequest": {"mouserPartNumber": mpn, "partSearchOptions": "Exact"}}
        data = self._post(PARTNUM_URL, body)
        if not data:
            return None
        parts = ((data.get("SearchResults") or {}).get("Parts")) or []
        target = mpn.upper()
        for p in parts:
            if (p.get("ManufacturerPartNumber") or "").upper() == target:
                return _normalize(p)
        if parts:
            return _normalize(parts[0])
        return None
