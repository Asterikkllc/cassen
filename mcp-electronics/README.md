# cassen-mcp-electronics

Cassen v1 electronics knowledge pack. MCP server exposing parts
search/lookup tools so the agent grounds designs in real components.

Sibling of `agent/` (Python LangGraph) and `app/` (Next.js).

## Tools

| name                    | params                               | what it does |
|-------------------------|--------------------------------------|--------------|
| `list_categories`       | —                                    | common category labels + configured live providers |
| `search_part`           | `query`, `category?`, `limit?` (≤50) | live keyword search via the chain |
| `get_part`              | `mpn`                                | full record for one MPN |
| `recommend_alternative` | `mpn`, `reason?`                     | family-prefix lookup, original filtered out |

## Data sources

Live-only. Provider chains:

| tool | chain (first hit wins) |
|---|---|
| `search_part`           | Nexar → Mouser |
| `get_part`              | Nexar → Digi-Key → Mouser |
| `recommend_alternative` | uses get_part + search_part |

Each row is annotated with `source` and the response carries an
`attempts` array so the caller can see which providers were tried.

## Configure

Set the live provider creds in `.env` (gitignored). At least one of
Nexar / Mouser / Digi-Key needs to be set or every tool returns a
"no providers configured" error. See `.env.example` for the shape.

## Run locally

```sh
cd mcp-electronics
uv sync
uv run python -m cassen_electronics.server
```

## Register with Claude Code

```json
{
  "mcpServers": {
    "cassen-electronics": {
      "command": "C:\\Users\\HP\\.local\\bin\\uv.exe",
      "args": [
        "run",
        "--project",
        "C:\\Users\\HP\\Cassen\\mcp-electronics",
        "python",
        "-m",
        "cassen_electronics.server"
      ]
    }
  }
}
```

Restart Claude Code. The four tools become callable as
`mcp__cassen-electronics__list_categories` etc.

## What's NOT here yet (later phases)

- Persistent cache (Redis / Supabase) so cache survives MCP restarts.
- Multi-distributor offer aggregation (sellers, prices by quantity,
  inventory levels) — Nexar already exposes this; we just don't read
  it yet. Becomes a Phase 20+ marketplace concern.
- Datasheet PDF parsing — Phase 25 (Deep Research mode) owns
  LlamaParse / Reducto.
