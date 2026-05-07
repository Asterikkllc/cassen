"""Cassen v1 — mechanical knowledge pack MCP server.

Exposes a curated catalog of fasteners, bearings, t-slot extrusion,
standoffs, and linear motion hardware. Tools mirror mcp-electronics's
shape so the agent reasons about mechanical hardware the same way it
reasons about electronics.

Curated, not live. PRD section 5.2 calls for a "5000-part McMaster
mirror" — that's a later phase; v1 ships ~30 entries covering what a
maker project actually picks.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from . import catalog
from .config import get_settings

server = FastMCP("cassen-mechanical")


@server.tool()
def list_categories() -> dict[str, Any]:
    """List the mechanical hardware categories the catalog covers, with
    counts. Use these as the `category` filter on `search_part`.

    Categories: fastener, bearing, extrusion, standoff, linear_motion.
    """
    return catalog.list_categories()


@server.tool()
def search_part(
    query: str,
    category: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search the curated mechanical catalog.

    Case-insensitive substring match across id, size (e.g. 'M3x10',
    '608'), description, spec, subcategory, use_cases, and notes.
    `category` optionally narrows to one bucket (use list_categories
    for the valid set). `limit` is capped at 50.
    """
    s = get_settings()
    if limit < 1:
        limit = 1
    if limit > s.max_limit:
        limit = s.max_limit
    rows = catalog.search(query, category=category, limit=limit)
    return {
        "query": query,
        "category": category,
        "count": len(rows),
        "rows": rows,
    }


@server.tool()
def get_part(part_id: str) -> dict[str, Any]:
    """Fetch the full record for a part by exact id (e.g. 'din912-m3-10').

    Returns `{ part }` on hit or `{ error }` if no entry matches.
    """
    row = catalog.get(part_id)
    if row is None:
        return {"error": f"no part with id '{part_id}'"}
    return {"part": row}


@server.tool()
def recommend_for_function(
    function: str,
    context: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Rough heuristic: 'what part should I use for this function?'

    `function` is a short noun phrase like 'mount PCB to chassis',
    'vibration-resistant nut', '3D-printed enclosure thread insert',
    'linear motion 8 mm shaft'. `context` adds free-text such as
    project type or constraints.

    Returns up to `limit` candidate rows ranked by keyword match. The
    agent should pick one and call get_part for the chosen id to grab
    full dimensions / suppliers.
    """
    rows = catalog.recommend_for_function(function, context=context, limit=limit)
    return {
        "function": function,
        "context": context,
        "count": len(rows),
        "candidates": rows,
    }


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
