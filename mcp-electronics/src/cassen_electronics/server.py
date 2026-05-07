"""Cassen v1 — electronics knowledge pack MCP server.

Live-only data layer (Nexar, Digi-Key, Mouser). The four tools below
share a stable contract so callers don't change when providers are
added or swapped.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .aggregator import get_aggregator

server = FastMCP("cassen-electronics")


@server.tool()
def list_categories() -> dict[str, Any]:
    """Return common electronics categories for use as the `category`
    filter on search_part, plus the list of configured live providers
    (Nexar, Mouser, Digi-Key).

    Each distributor exposes its own taxonomy; the rows returned by
    search_part / get_part carry the provider's own `category` string.
    """
    return get_aggregator().list_categories()


@server.tool()
def search_part(
    query: str,
    category: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search the live electronics catalog.

    Provider chain: Nexar (multi-distributor: Digi-Key, Mouser, LCSC, …)
    → Mouser keyword search. The first provider that returns ≥1 row
    wins; the chain is logged in `attempts`.

    `query` is the free-text search (mpn, manufacturer, function,
    description). `category` optionally narrows results
    (case-insensitive, matched on each row's `category` field).
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

    Provider chain: Nexar → Digi-Key → Mouser. First hit wins. Returns
    `{ part, source, attempts }` on success or `{ error, attempts }`
    if no provider knew the MPN.
    """
    return get_aggregator().get(mpn)


@server.tool()
def recommend_alternative(mpn: str, reason: str | None = None) -> dict[str, Any]:
    """Find functionally-similar alternatives to a given MPN.

    Best-effort live lookup: the original MPN is fetched to confirm it
    exists, a family prefix is derived from the MPN (first hyphen-
    separated chunk, capped at 6 chars — e.g. ESP32-WROOM-32E → ESP32),
    and the family is searched across the live chain. The original is
    filtered out of the result.

    Distributor APIs don't expose a structured "functional substitute"
    relationship; for a tighter list, the agent can call search_part
    with the original part's category and pick by spec.
    `reason` is recorded for future ranking.
    """
    return get_aggregator().recommend_alternative(mpn, reason)


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
