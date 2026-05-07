# cassen-mcp-mechanical

Cassen v1 mechanical knowledge pack. MCP server exposing a curated
catalog of fasteners, bearings, t-slot extrusion, standoffs, and
linear motion hardware so the agent grounds mechanical decisions in
real, sourceable parts.

Sibling of `agent/`, `app/`, `cad/`, `mcp-electronics/`,
`mcp-cad/`, `mcp-image-gen/`.

## Tools

| name                          | params                                  | what it does |
|-------------------------------|-----------------------------------------|--------------|
| `list_categories`             | —                                       | category labels + counts (fastener, bearing, extrusion, standoff, linear_motion) |
| `search_part`                 | `query`, `category?`, `limit?` (≤50)    | substring search across id, size, description, spec, use_cases |
| `get_part`                    | `part_id`                               | full record for one part |
| `recommend_for_function`      | `function`, `context?`, `limit?`        | keyword heuristic mapping function -> candidate parts |

## Data

Curated, in-process JSON files under `src/cassen_mechanical/data/`:
fasteners.json, bearings.json, extrusion.json, standoffs.json,
linear_motion.json. ~30 entries total at v1.

Each row carries:

```json
{
  "id": "din912-m3-10",
  "category": "fastener",
  "subcategory": "socket_head_cap_screw",
  "spec": "DIN 912 / ISO 4762",
  "size": "M3x10",
  "description": "...",
  "dimensions_mm": { "thread_diameter": 3.0, "length": 10.0, "...": "..." },
  "material_options": [...],
  "common_suppliers": [...],
  "use_cases": [...],
  "notes": "..."
}
```

PRD section 5.2 calls for a 5000-part McMaster mirror as the long-term
plan. The v1 dataset is intentionally tight — every entry is something
a maker project actually picks. Adding parts is a matter of editing
the relevant JSON file; the catalog reloads automatically on next
start.

## Run locally

```sh
cd mcp-mechanical
uv sync
uv run python -m cassen_mechanical.server
```

## Register with Claude Code

```json
{
  "mcpServers": {
    "cassen-mechanical": {
      "command": "C:\\Users\\HP\\.local\\bin\\uv.exe",
      "args": [
        "run",
        "--project",
        "C:\\Users\\HP\\Cassen\\mcp-mechanical",
        "python",
        "-m",
        "cassen_mechanical.server"
      ]
    }
  }
}
```

## What's NOT here yet

- Live supplier integration. Misumi has an API; McMaster-Carr does
  not. A later phase will pull live availability + pricing for parts
  whose `common_suppliers` list includes a queryable provider.
- STEP files for each part. The McMaster mirror in PRD section 5.2
  ships geometry; for now `mcp-cad/` covers parametric geometry and
  fasteners are referenced by spec only.
- Material property tables (modulus, density, thermal expansion).
  Belongs alongside fluids and physics-sandbox phases.
