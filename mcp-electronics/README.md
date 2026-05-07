# cassen-mcp-electronics

First Cassen v1 knowledge pack: **electronics**. MCP server exposing
parts search/lookup tools so the agent can ground designs in real
components instead of hallucinating SKUs.

Sibling of `agent/` (Python LangGraph) and `app/` (Next.js).

## Tools

| name                    | params                               | what it does |
|-------------------------|--------------------------------------|--------------|
| `list_categories`       | —                                    | available categories + part count |
| `search_part`           | `query`, `category?`, `limit?` (≤50) | fuzzy search across mpn/maker/desc/tags |
| `get_part`              | `mpn`                                | full record for one MPN |
| `recommend_alternative` | `mpn`, `reason?`                     | substitutes per the curated `alternatives` list |

## Data

`data/parts.json` is a curated seed of ~25 popular real parts spanning
MCU, sensor, power, comms, and driver categories. Schema is documented
inline.

Replace with live distributor lookups in Phase 6c — keep the **tool
contract identical**, just swap the `_load_dataset()` /
`recommend_alternative()` internals.

## Run locally

```sh
cd mcp-electronics
uv sync
uv run python -m cassen_electronics.server
```

Or via the registered script:

```sh
uv run cassen-mcp-electronics
```

## Register with Claude Code

Add to `~/.claude.json` under `mcpServers`:

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

- **Phase 6b** wires this server into the agent's LangGraph as an
  `electronics_research` node. Right now the server is callable from
  Claude Code but the production agent doesn't talk to it.
- **Phase 6c** swaps the JSON data source for live Digi-Key Product
  Information API + Mouser Search API + Nexar GraphQL aggregation.
- **Phase 31** captures simulation outcomes back into a parts-grounding
  corpus so search ranks better as more projects ship.
