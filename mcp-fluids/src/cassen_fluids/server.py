"""Cassen v1 — fluids knowledge pack MCP server.

Exposes a curated catalog of pumps, valves, tubing, and fittings —
the parts a smart planter / hydroponics / pneumatic project actually
picks. Tools mirror mcp-mechanical / mcp-electronics so the agent's
mental model is consistent across knowledge packs.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from . import catalog
from .config import get_settings

server = FastMCP("cassen-fluids")


@server.tool()
def list_categories() -> dict[str, Any]:
    """List the fluid hardware categories the catalog covers, with
    counts. Use these as the `category` filter on `search_part`.

    Categories: pump, valve, tubing, fitting.
    """
    return catalog.list_categories()


@server.tool()
def search_part(
    query: str,
    category: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search the curated fluids catalog.

    Case-insensitive substring match across id, description, spec,
    subcategory, materials_compatible, use_cases, and notes.
    `category` optionally narrows to one bucket. `limit` is capped
    at 50.
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
    """Fetch a single part by id (e.g. 'pump-r385-12v-water')."""
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
    """'What part should I use for this function?'

    `function` is a short noun phrase like 'water a planter on a 12V
    line', 'shut off air supply on power loss', '6 mm hose to 1/2 BSP
    pump'. `context` adds project specifics. Returns up to `limit`
    candidates ranked by keyword match.
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
