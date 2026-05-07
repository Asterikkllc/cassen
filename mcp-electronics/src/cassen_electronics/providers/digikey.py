"""Digi-Key Production API provider.

OAuth client-credentials at https://api.digikey.com/v1/oauth2/token; cache
the bearer until 60s before expiry. v4 product search at
https://api.digikey.com/products/v4/search/keyword.

Used here as a tertiary source — Nexar usually covers Digi-Key data, but
direct Digi-Key lookup is faster + authoritative for their catalog.
"""

from __future__ import annotations

from typing import Any

import httpx

from ..cache import CACHE
from ..config import get_settings
from .base import PartProvider, normalize_lifecycle

TOKEN_URL = "https://api.digikey.com/v1/oauth2/token"
SEARCH_URL = "https://api.digikey.com/products/v4/search/keyword"

_TOKEN_KEY = "digikey:access_token"


def _normalize(item: dict[str, Any]) -> dict[str, Any]:
    desc = item.get("Description") or {}
    if isinstance(desc, dict):
        description = desc.get("ProductDescription") or desc.get("DetailedDescription")
    else:
        description = str(desc) if desc else None
    manuf = item.get("Manufacturer") or {}
    if isinstance(manuf, dict):
        manufacturer = manuf.get("Name") or manuf.get("Value")
    else:
        manufacturer = str(manuf) if manuf else None
    cat = item.get("Category") or {}
    category = cat.get("Name") if isinstance(cat, dict) else None
    unit_price = item.get("UnitPrice")
    try:
        unit_price = float(unit_price) if unit_price is not None else None
    except (TypeError, ValueError):
        unit_price = None
    status = item.get("ProductStatus") or {}
    lifecycle_raw = status.get("Status") if isinstance(status, dict) else None
    return {
        "mpn": item.get("ManufacturerProductNumber") or item.get("ManufacturerPartNumber") or "",
        "manufacturer": manufacturer,
        "category": category,
        "subcategory": None,
        "description": description,
        "datasheet_url": item.get("DatasheetUrl"),
        "lifecycle": normalize_lifecycle(lifecycle_raw),
        "typical_unit_price_usd": unit_price,
        "key_specs": None,
        "packages": None,
        "alternatives": None,
        "tags": None,
        "source": "digikey",
        "source_url": item.get("ProductUrl"),
    }


class DigiKeyProvider(PartProvider):
    name = "digikey"

    def __init__(self) -> None:
        self._s = get_settings()

    @property
    def configured(self) -> bool:
        return self._s.digikey_configured

    def _token(self) -> str | None:
        if not self.configured:
            return None
        cached = CACHE.get(_TOKEN_KEY)
        if cached:
            return cached
        try:
            resp = httpx.post(
                TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._s.digikey_client_id,
                    "client_secret": self._s.digikey_client_secret,
                },
                timeout=self._s.request_timeout_s,
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception:  # noqa: BLE001
            return None
        token = payload.get("access_token")
        expires_in = int(payload.get("expires_in", 600))
        if token:
            CACHE.set(_TOKEN_KEY, token, max(60, expires_in - 60))
        return token

    def _headers(self, token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "X-DIGIKEY-Client-Id": self._s.digikey_client_id or "",
            "X-DIGIKEY-Locale-Site": "US",
            "X-DIGIKEY-Locale-Language": "en",
            "X-DIGIKEY-Locale-Currency": "USD",
            "Accept": "application/json",
        }

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
        token = self._token()
        if not token:
            return []
        try:
            resp = httpx.post(
                SEARCH_URL,
                headers=self._headers(token),
                json={"Keywords": q, "Limit": min(max(1, limit), 50)},
                timeout=self._s.request_timeout_s,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception:  # noqa: BLE001
            return []
        products = data.get("Products") or []
        out: list[dict[str, Any]] = []
        for p in products:
            normalized = _normalize(p)
            if category and (normalized.get("category") or "").lower() != category.lower():
                continue
            out.append(normalized)
        return out[:limit]

    def get(self, mpn: str) -> dict[str, Any] | None:
        """Resolve an MPN by keyword-searching and matching.

        Digi-Key's `productdetails/{productNumber}` endpoint is strict —
        it takes a Digi-Key part number, not always a plain MPN. For
        common parts like `ESP32-WROOM-32E` it 404s because the catalog
        only carries packaged variants (`ESP32-WROOM-32E-N4`, etc.). The
        keyword search returns those variants reliably; we pick an exact
        match if present, else the closest-matching variant.
        """
        if not self.configured or not mpn:
            return None
        results = self.search(mpn, limit=10)
        if not results:
            return None
        target = mpn.upper()
        for r in results:
            if (r.get("mpn") or "").upper() == target:
                return r
        target_compact = target.replace("-", "")
        for r in results:
            candidate = (r.get("mpn") or "").upper().replace("-", "")
            if candidate.startswith(target_compact):
                return r
        return results[0]
