"""Curated in-repo dataset provider. Always available; no auth, no network."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

from .base import PartProvider


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
            here.parent.parent / "data" / "parts.json",
            here.parent.parent.parent.parent / "data" / "parts.json",
        ]
    )
    for c in candidates:
        if c.exists():
            return json.loads(c.read_text(encoding="utf-8"))
    raise FileNotFoundError(
        "parts.json not found. Looked in: " + ", ".join(str(c) for c in candidates)
    )


def _annotate(part: dict[str, Any]) -> dict[str, Any]:
    return {**part, "source": "curated"}


class CuratedProvider(PartProvider):
    name = "curated"

    def __init__(self) -> None:
        self._dataset = _load_dataset()
        self._parts: list[dict[str, Any]] = self._dataset["parts"]
        self._by_mpn: dict[str, dict[str, Any]] = {p["mpn"]: p for p in self._parts}

    @property
    def configured(self) -> bool:
        return True

    @property
    def categories(self) -> list[str]:
        return list(self._dataset.get("categories", []))

    @property
    def schema_version(self) -> int | None:
        return self._dataset.get("schema_version")

    def search(
        self,
        query: str,
        *,
        category: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        q = (query or "").strip().lower()
        if not q:
            return []
        cat = category.strip().lower() if category else None
        scored: list[tuple[int, dict[str, Any]]] = []
        for p in self._parts:
            if cat and (p.get("category") or "").lower() != cat:
                continue
            mpn = (p.get("mpn") or "").lower()
            haystack = " | ".join(
                [
                    mpn,
                    (p.get("manufacturer") or "").lower(),
                    (p.get("description") or "").lower(),
                    (p.get("subcategory") or "").lower(),
                    " ".join(t.lower() for t in p.get("tags", [])),
                ]
            )
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
        return [_annotate(p) for _, p in scored[:limit]]

    def get(self, mpn: str) -> dict[str, Any] | None:
        if not mpn:
            return None
        direct = (
            self._by_mpn.get(mpn)
            or self._by_mpn.get(mpn.upper())
            or self._by_mpn.get(mpn.lower())
        )
        if direct:
            return _annotate(direct)
        needle = mpn.upper()
        for key, val in self._by_mpn.items():
            if key.upper() == needle:
                return _annotate(val)
        return None

    def find_alternatives(self, mpn: str) -> tuple[list[dict[str, Any]], list[str]]:
        """Return (resolved alternatives, MPNs missing from dataset)."""
        found = self.get(mpn)
        if not found:
            return ([], [])
        alt_mpns: list[str] = found.get("alternatives", []) or []
        resolved = [self.get(m) for m in alt_mpns]
        alts = [a for a in resolved if a is not None]
        missing = [m for m, a in zip(alt_mpns, resolved, strict=True) if a is None]
        return (alts, missing)
