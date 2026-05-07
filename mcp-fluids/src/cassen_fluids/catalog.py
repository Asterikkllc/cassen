"""In-memory curated fluids catalog.

Mirrors `cassen_mechanical.catalog`. Categories: pump, valve, tubing,
fitting. Pure JSON loaded once via importlib.resources.
"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

_DATA_FILES: dict[str, str] = {
    "pumps.json": "pump",
    "valves.json": "valve",
    "tubing.json": "tubing",
    "fittings.json": "fitting",
}

_catalog: list[dict[str, Any]] | None = None
_by_id: dict[str, dict[str, Any]] | None = None


def _load() -> None:
    global _catalog, _by_id
    if _catalog is not None:
        return

    rows: list[dict[str, Any]] = []
    base = files("cassen_fluids.data")
    for filename, default_category in _DATA_FILES.items():
        with (base / filename).open("rb") as f:
            data = json.loads(f.read().decode("utf-8"))
        if not isinstance(data, list):
            raise RuntimeError(f"data/{filename} must be a JSON list")
        for entry in data:
            if not isinstance(entry, dict) or "id" not in entry:
                raise RuntimeError(f"data/{filename} entry missing id: {entry!r}")
            entry.setdefault("category", default_category)
            rows.append(entry)

    _catalog = rows
    _by_id = {row["id"]: row for row in rows}


def all_rows() -> list[dict[str, Any]]:
    _load()
    assert _catalog is not None
    return list(_catalog)


def get(part_id: str) -> dict[str, Any] | None:
    _load()
    assert _by_id is not None
    return _by_id.get(part_id)


def list_categories() -> dict[str, Any]:
    _load()
    assert _catalog is not None
    counts: dict[str, int] = {}
    for row in _catalog:
        c = str(row.get("category", "uncategorized"))
        counts[c] = counts.get(c, 0) + 1
    descriptions = {
        "pump": "DC water + air pumps (diaphragm, peristaltic, centrifugal)",
        "valve": "solenoid + check + motorized valves for water and air",
        "tubing": "silicone, vinyl, PTFE, polyurethane",
        "fitting": "barbs, push-fits, quick-disconnects, reducers",
    }
    return {
        "categories": [
            {
                "name": name,
                "count": counts[name],
                "description": descriptions.get(name, ""),
            }
            for name in sorted(counts.keys())
        ],
        "total_parts": len(_catalog),
    }


def search(
    query: str,
    *,
    category: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    _load()
    assert _catalog is not None
    q = (query or "").strip().lower()
    cat = (category or "").strip().lower() or None

    def _matches(row: dict[str, Any]) -> bool:
        if cat and str(row.get("category", "")).lower() != cat:
            return False
        if not q:
            return True
        haystack_parts = [
            str(row.get("id", "")),
            str(row.get("description", "")),
            str(row.get("spec", "")),
            str(row.get("subcategory", "")),
            " ".join(row.get("use_cases", []) or []),
            " ".join(row.get("materials_compatible", []) or []),
            str(row.get("notes", "")),
        ]
        haystack = " ".join(haystack_parts).lower()
        return q in haystack

    hits = [row for row in _catalog if _matches(row)]
    return hits[: max(1, min(limit, 50))]


def recommend_for_function(
    function: str,
    *,
    context: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Function -> bucket heuristic, then keyword-rank within."""
    _load()
    assert _catalog is not None

    fn = (function or "").lower()
    ctx = (context or "").lower()

    keywords_by_intent: list[tuple[list[str], list[str]]] = [
        # Watering / hydration
        (["water", "irrigat", "planter", "hydropon", "fountain"], ["pump", "valve", "tubing", "fitting"]),
        # Pumping (specific)
        (["pump", "dispens", "dose", "dosing"], ["pump"]),
        # Air / pneumatic
        (["air", "pneumatic", "vacuum", "compress"], ["pump", "valve", "tubing", "fitting"]),
        # Valve / control
        (["valve", "shut off", "shutoff", "control flow", "throttl"], ["valve"]),
        # Backflow
        (["check", "backflow", "siphon", "anti-siphon"], ["valve"]),
        # Tube / hose
        (["tube", "hose", "pipe", "line"], ["tubing", "fitting"]),
        # Connectors
        (["connect", "fitting", "tee", "elbow", "junction", "split"], ["fitting"]),
    ]

    target_categories: set[str] = set()
    for keywords, cats in keywords_by_intent:
        if any(k in fn for k in keywords):
            target_categories.update(cats)

    def score(row: dict[str, Any]) -> int:
        s = 0
        text = " ".join(
            [
                str(row.get("description", "")),
                " ".join(row.get("use_cases", []) or []),
                " ".join(row.get("materials_compatible", []) or []),
                str(row.get("subcategory", "")),
                str(row.get("notes", "")),
            ]
        ).lower()
        if fn and fn in text:
            s += 4
        for word in fn.split():
            if word and len(word) >= 3 and word in text:
                s += 1
        if ctx:
            for word in ctx.split():
                if word and len(word) >= 3 and word in text:
                    s += 1
        return s

    candidates = (
        [r for r in _catalog if r.get("category") in target_categories]
        if target_categories
        else list(_catalog)
    )
    ranked = sorted(candidates, key=score, reverse=True)
    return [r for r in ranked if score(r) > 0][: max(1, min(limit, 20))]
