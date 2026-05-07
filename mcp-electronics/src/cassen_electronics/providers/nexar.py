"""Nexar (Octopart) GraphQL provider.

Multi-distributor aggregator covering Digi-Key, Mouser, LCSC, and many more.
Used as the primary live-data source.

Auth: client-credentials OAuth at https://identity.nexar.com/connect/token,
scope `supply.domain`. Token cached in memory until 60s before expiry.

Endpoint: https://api.nexar.com/graphql
"""

from __future__ import annotations

from typing import Any

import httpx

from ..cache import CACHE
from ..config import get_settings
from .base import PartProvider

TOKEN_URL = "https://identity.nexar.com/connect/token"
GRAPHQL_URL = "https://api.nexar.com/graphql"

_TOKEN_KEY = "nexar:access_token"

_PART_FIELDS = """
mpn
manufacturer { name }
shortDescription
bestDatasheet { url }
category { name }
medianPrice1000 { price currency }
octopartUrl
""".strip()

SEARCH_QUERY = (
    "query Search($q: String!, $limit: Int!) {\n"
    "  supSearch(q: $q, limit: $limit, currency: \"USD\") {\n"
    "    results { part { " + _PART_FIELDS + " } }\n"
    "  }\n"
    "}\n"
)

GET_QUERY = (
    "query Get($mpn: String!) {\n"
    "  supSearchMpn(q: $mpn, limit: 5, currency: \"USD\") {\n"
    "    results { part { " + _PART_FIELDS + " } }\n"
    "  }\n"
    "}\n"
)


def _normalize(part: dict[str, Any]) -> dict[str, Any]:
    median = part.get("medianPrice1000") or {}
    price = median.get("price") if (median.get("currency") == "USD") else None
    return {
        "mpn": part.get("mpn") or "",
        "manufacturer": (part.get("manufacturer") or {}).get("name"),
        "category": (part.get("category") or {}).get("name"),
        "subcategory": None,
        "description": part.get("shortDescription"),
        "datasheet_url": (part.get("bestDatasheet") or {}).get("url"),
        "lifecycle": None,
        "typical_unit_price_usd": float(price) if price is not None else None,
        "key_specs": None,
        "packages": None,
        "alternatives": None,
        "tags": None,
        "source": "nexar",
        "source_url": part.get("octopartUrl"),
    }


class NexarProvider(PartProvider):
    name = "nexar"

    def __init__(self) -> None:
        self._s = get_settings()

    @property
    def configured(self) -> bool:
        return self._s.nexar_configured

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
                    "client_id": self._s.nexar_client_id,
                    "client_secret": self._s.nexar_client_secret,
                    "scope": "supply.domain",
                },
                timeout=self._s.request_timeout_s,
            )
            resp.raise_for_status()
            payload = resp.json()
        except Exception:  # noqa: BLE001
            return None
        token = payload.get("access_token")
        expires_in = int(payload.get("expires_in", 3600))
        if token:
            CACHE.set(_TOKEN_KEY, token, max(60, expires_in - 60))
        return token

    def _post(self, query: str, variables: dict[str, Any]) -> dict[str, Any] | None:
        token = self._token()
        if not token:
            raise RuntimeError("nexar: token exchange failed")
        resp = httpx.post(
            GRAPHQL_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"query": query, "variables": variables},
            timeout=self._s.request_timeout_s,
        )
        resp.raise_for_status()
        body = resp.json()
        errs = body.get("errors")
        if errs:
            msg = (errs[0] or {}).get("message", "nexar graphql error")
            raise RuntimeError(f"nexar: {msg}")
        return body

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
        data = self._post(SEARCH_QUERY, {"q": q, "limit": limit})
        if not data:
            return []
        results = (
            ((data.get("data") or {}).get("supSearch") or {}).get("results") or []
        )
        out: list[dict[str, Any]] = []
        for r in results:
            part = r.get("part")
            if not part:
                continue
            normalized = _normalize(part)
            if category and (normalized.get("category") or "").lower() != category.lower():
                continue
            out.append(normalized)
        return out[:limit]

    def get(self, mpn: str) -> dict[str, Any] | None:
        if not self.configured or not mpn:
            return None
        data = self._post(GET_QUERY, {"mpn": mpn})
        if not data:
            return None
        results = (
            ((data.get("data") or {}).get("supSearchMpn") or {}).get("results") or []
        )
        target = mpn.upper()
        for r in results:
            part = r.get("part")
            if not part:
                continue
            if (part.get("mpn") or "").upper() == target:
                return _normalize(part)
        if results and results[0].get("part"):
            return _normalize(results[0]["part"])
        return None
