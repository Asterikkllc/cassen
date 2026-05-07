"""Cassen v1 — electronics knowledge pack MCP server.

Tools exposed (stable contract — see Aggregator for the data layer):
- list_categories()       -> categories + provider list + curated count
- search_part(query, ...) -> Nexar -> Mouser -> curated, normalized rows
- get_part(mpn)           -> Nexar -> Digi-Key -> Mouser -> curated
- recommend_alternative(mpn, reason?) -> curated alternatives list

All four were Phase 6a; Phase 6c added the live distributor providers
behind the same surface.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .aggregator import get_aggregator

server = FastMCP("cassen-electronics")


@server.tool()
def list_categories() -> dict[str, Any]:
    """List the available part categories in this knowledge pack and the
    set of configured live-data providers (Nexar, Mouser, Digi-Key, curated).

    Categories are the curated taxonomy; live providers each carry their
    own taxonomy. Use list_categories() to learn what's available; use
    search_part() to query.
    """
    return get_aggregator().list_categories()


@server.tool()
def search_part(
    query: str,
    category: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search the electronics parts library.

    Provider chain: Nexar (multi-distributor: Digi-Key, Mouser, LCSC, …)
    → Mouser keyword search → curated in-repo dataset. The first
    provider that returns ≥1 row wins; chain is logged in `attempts`.

    `query` is the free-text search (mpn, manufacturer, function,
    description). `category` optionally narrows results (case-insensitive).
    `limit` is capped at 50.
    """
    if limit < 1:
        limit = 1
    if limit > 50:
        limit = 50
    return get_aggregator().search(query, category=category, limit=limit)


@server.tool()
def get_part(mpn: str) -> dict[str, Any]:
    """Fetch the full record for a single part by exact MPN.

    Provider chain: Nexar → Digi-Key → Mouser → curated. First hit wins.
    Returns `{ part, source, attempts }` on success or
    `{ error, attempts }` if no provider knew the MPN.
    """
    return get_aggregator().get(mpn)


@server.tool()
def recommend_alternative(mpn: str, reason: str | None = None) -> dict[str, Any]:
    """Find functionally-similar alternatives to a given MPN.

    Backed by the curated `alternatives` list per part (live distributor
    APIs don't expose functional substitutes — that's a derived concept).
    `reason` is recorded for future ranking.
    """
    return get_aggregator().recommend_alternative(mpn, reason)


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
