"""Cassen v1 — electronics knowledge pack MCP server.

Tools exposed:
- list_categories()       -> all curated part categories
- search_part(query, ...) -> fuzzy match across mpn/manufacturer/description/tags
- get_part(mpn)           -> full record for a single MPN
- recommend_alternative(mpn, reason?) -> functionally-similar parts

Backed by data/parts.json today. Phase 6c will swap the data layer for
live Digi-Key + Mouser + Nexar fetches against the same tool surface.
"""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP


def _load_dataset() -> dict[str, Any]:
    candidates: list[Path] = []
    try:
        pkg_root = files("cassen_electronics")
        candidates.append(Path(str(pkg_root)) / "data" / "parts.json")
    except (ModuleNotFoundError, FileNotFoundError):
        pass
    here = Path(__file__).resolve()
    candidates.extend(
        [
            here.parent / "data" / "parts.json",
            here.parent.parent.parent / "data" / "parts.json",
        ]
    )
    for c in candidates:
        if c.exists():
            return json.loads(c.read_text(encoding="utf-8"))
    raise FileNotFoundError(
        "parts.json not found. Looked in: " + ", ".join(str(c) for c in candidates)
    )


_DATASET = _load_dataset()
_PARTS: list[dict[str, Any]] = _DATASET["parts"]
_BY_MPN: dict[str, dict[str, Any]] = {p["mpn"]: p for p in _PARTS}

server = FastMCP("cassen-electronics")


@server.tool()
def list_categories() -> dict[str, Any]:
    """List the available part categories in this knowledge pack.

    Use this when the agent wants to discover what kinds of components
    can be searched.
    """
    return {
        "categories": _DATASET.get("categories", []),
        "total_parts": len(_PARTS),
        "schema_version": _DATASET.get("schema_version"),
    }


@server.tool()
def search_part(
    query: str,
    category: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Fuzzy-search the curated electronics parts library.

    `query` matches against mpn, manufacturer, description, subcategory,
    and tags (case-insensitive substring). Optionally constrain to a
    category from list_categories().

    Returns up to `limit` matches sorted by a simple relevance score
    (exact mpn first, then mpn-prefix, then tag/description hits).
    """
    if limit < 1 or limit > 50:
        limit = 10
    q = query.strip().lower()
    if not q:
        return {"results": [], "total": 0, "query": query}

    cat_filter = category.strip().lower() if category else None

    scored: list[tuple[int, dict[str, Any]]] = []
    for p in _PARTS:
        if cat_filter and (p.get("category") or "").lower() != cat_filter:
            continue
        mpn = (p.get("mpn") or "").lower()
        haystack_parts = [
            mpn,
            (p.get("manufacturer") or "").lower(),
            (p.get("description") or "").lower(),
            (p.get("subcategory") or "").lower(),
            " ".join(t.lower() for t in p.get("tags", [])),
        ]
        haystack = " | ".join(haystack_parts)

        score = 0
        if q == mpn:
            score = 1000
        elif mpn.startswith(q):
            score = 500
        elif q in mpn:
            score = 200
        elif any(q == t.lower() for t in p.get("tags", [])):
            score = 150
        elif q in haystack:
            score = 50

        if score > 0:
            scored.append((score, p))

    scored.sort(key=lambda s: -s[0])
    results = [p for _, p in scored[:limit]]
    return {
        "query": query,
        "category": category,
        "total": len(scored),
        "returned": len(results),
        "results": results,
    }


@server.tool()
def get_part(mpn: str) -> dict[str, Any]:
    """Fetch the full record for a single part by exact MPN. Case-insensitive."""
    if not mpn:
        return {"error": "mpn is required"}
    direct = _BY_MPN.get(mpn) or _BY_MPN.get(mpn.upper()) or _BY_MPN.get(mpn.lower())
    if direct:
        return {"part": direct}
    needle = mpn.upper()
    for key, val in _BY_MPN.items():
        if key.upper() == needle:
            return {"part": val}
    return {"error": f"part not found: {mpn}"}


@server.tool()
def recommend_alternative(mpn: str, reason: str | None = None) -> dict[str, Any]:
    """Find functionally-similar alternatives to a given MPN.

    Currently uses the curated `alternatives` list for each part. Phase 6c
    will replace this with cross-distributor lookup + spec matching.

    `reason` is a free-form note (e.g. "lower BOM cost", "pin-compatible
    upgrade", "in-stock substitute"). Recorded for future ranking.
    """
    if not mpn:
        return {"error": "mpn is required"}
    found = _BY_MPN.get(mpn) or _BY_MPN.get(mpn.upper()) or _BY_MPN.get(mpn.lower())
    if not found:
        return {"error": f"part not found: {mpn}", "alternatives": []}
    alt_mpns = found.get("alternatives", []) or []
    alts = [_BY_MPN[m] for m in alt_mpns if m in _BY_MPN]
    return {
        "original_mpn": found["mpn"],
        "reason": reason,
        "alternatives": alts,
        "missing_from_dataset": [m for m in alt_mpns if m not in _BY_MPN],
    }


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
