# cassen-mcp-fluids

Cassen v1 fluids knowledge pack. MCP server exposing a curated
catalog of pumps, valves, tubing, and fittings so the agent grounds
fluid-system decisions in real, sourceable parts.

Sibling of `agent/`, `app/`, `cad/`, `mcp-electronics/`,
`mcp-mechanical/`, `mcp-cad/`, `mcp-image-gen/`.

## Tools

| name                          | params                                  | what it does |
|-------------------------------|-----------------------------------------|--------------|
| `list_categories`             | —                                       | category labels + counts (pump, valve, tubing, fitting) |
| `search_part`                 | `query`, `category?`, `limit?` (≤50)    | substring search across id, description, spec, materials, use_cases |
| `get_part`                    | `part_id`                               | full record for one part |
| `recommend_for_function`      | `function`, `context?`, `limit?`        | keyword heuristic mapping function -> candidate parts |

## Data

Curated, in-process JSON files under `src/cassen_fluids/data/`:

- `pumps.json` — DC water + air pumps (R385 / Kamoer peristaltic / 5V mini USB / aquarium air / Shurflo-style 50 PSI diaphragm).
- `valves.json` — 12V solenoid (1/2 BSP irrigation, 6 mm mini), check valves, pneumatic 5/2, motorized servo+ball.
- `tubing.json` — silicone food-safe (6×4, 8×5), vinyl PVC, PTFE Bowden (4×2), polyurethane pneumatic (6×4).
- `fittings.json` — barb tees, push-fit elbows, CPC quick-disconnects, NPT-to-barb adapters, reducers.

Each row carries `id`, `category`, `subcategory`, `spec`, `description`,
optional `voltage_v`, `flow_lpm`, `max_pressure_kpa`, `ports`,
`materials_compatible`, `duty_cycle`, `common_suppliers`, `use_cases`,
and `notes` (e.g. "needs minimum upstream pressure to seal").

PRD section 5.1 + 5.2 calls fluids one of the three launch knowledge
packs (electronics, mechanical, fluids). v1 ships ~20 entries —
focused on what a smart-planter, hydroponics, or DIY pneumatics
project picks.

## Run locally

```sh
cd mcp-fluids
uv sync
uv run python -m cassen_fluids.server
```

## Register with Claude Code

```json
{
  "mcpServers": {
    "cassen-fluids": {
      "command": "C:\\Users\\HP\\.local\\bin\\uv.exe",
      "args": [
        "run",
        "--project",
        "C:\\Users\\HP\\Cassen\\mcp-fluids",
        "python",
        "-m",
        "cassen_fluids.server"
      ]
    }
  }
}
```

## What's NOT here yet

- Live supplier pricing (Cole-Parmer, McMaster, etc. — same gap as
  mcp-mechanical).
- Sensor coverage (flow, water level, pressure). Those live in
  `mcp-electronics` because they're MCU-bus parts, not fluid parts.
- Heavy-industry components (industrial pneumatic valves, hydraulic
  rams, food-grade stainless plumbing). Out of scope for the
  smart-planter / hobby-pneumatic launch profile.
