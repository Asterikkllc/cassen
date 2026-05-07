"""In-memory curated mechanical-hardware catalog.

Loads the JSON files in `data/` once on first call. All search /
lookup APIs operate on the cached dict-of-list-of-dicts.

This is the v1 dataset — small (~30 entries) but covers the parts a
maker project actually picks: fasteners, bearings, t-slot extrusion,
standoffs, linear motion. PRD section 5.2 talks about a "5000-part
McMaster mirror"; that's a later phase. Today's surface is what the
agent needs to ground mechanical decisions in real part numbers
without hallucinating.
"""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

# Map of source file -> default category if entries omit it.
_DATA_FILES: dict[str, str] = {
    "fasteners.json": "fastener",
    "bearings.json": "bearing",
    "extrusion.json": "extrusion",
    "standoffs.json": "standoff",
    "linear_motion.json": "linear_motion",
}


_catalog: list[dict[str, Any]] | None = None
_by_id: dict[str, dict[str, Any]] | None = None


def _load() -> None:
    global _catalog, _by_id
    if _catalog is not None:
        return

    rows: list[dict[str, Any]] = []
    base = files("cassen_mechanical.data")
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
    """Distinct categories with counts and short descriptions."""
    _load()
    assert _catalog is not None
    counts: dict[str, int] = {}
    for row in _catalog:
        c = str(row.get("category", "uncategorized"))
        counts[c] = counts.get(c, 0) + 1
    descriptions = {
        "fastener": "screws, nuts, washers (DIN/ISO/ANSI specs)",
        "bearing": "ball + linear bearings keyed by ID/OD/width",
        "extrusion": "aluminum t-slot profiles (2020, 3030, 4040, 2040)",
        "standoff": "PCB standoffs, hex spacers, heat-set inserts",
        "linear_motion": "shafts, lead screws, linear rails, timing belts",
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
    """Case-insensitive substring match across id, size, description, spec, use_cases."""
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
            str(row.get("size", "")),
            str(row.get("description", "")),
            str(row.get("spec", "")),
            str(row.get("subcategory", "")),
            " ".join(row.get("use_cases", []) or []),
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
    """Rough function-to-part heuristic.

    Not a model — just a keyword heuristic over the curated dataset.
    The agent layered on top can make finer judgements with the
    returned candidates as context.
    """
    _load()
    assert _catalog is not None

    fn = (function or "").lower()
    ctx = (context or "").lower()

    keywords_by_intent: list[tuple[list[str], list[str]]] = [
        # (intent keywords, category filter — empty = all)
        (["mount pcb", "mount board", "pcb mount", "standoff"], ["standoff"]),
        (["heat set", "heat-set", "insert", "captive"], ["standoff"]),
        (["screw", "fastener", "bolt"], ["fastener"]),
        (["nut", "lock", "vibrat"], ["fastener"]),
        (["frame", "extrusion", "t-slot", "tslot", "chassis"], ["extrusion"]),
        (["bearing", "rotat", "shaft"], ["bearing"]),
        (["linear", "slide", "rail", "belt", "lead screw", "leadscrew"], ["linear_motion"]),
    ]

    def score(row: dict[str, Any]) -> int:
        s = 0
        text = " ".join(
            [
                str(row.get("description", "")),
                " ".join(row.get("use_cases", []) or []),
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

    # Choose category bucket(s) for this function
    target_categories: set[str] = set()
    for keywords, cats in keywords_by_intent:
        if any(k in fn for k in keywords):
            target_categories.update(cats)

    candidates = (
        [r for r in _catalog if r.get("category") in target_categories]
        if target_categories
        else list(_catalog)
    )
    ranked = sorted(candidates, key=score, reverse=True)
    return [r for r in ranked if score(r) > 0][: max(1, min(limit, 20))]
