# cassen-mcp-cad

Cassen v1 mechanical-CAD knowledge pack. MCP server that wraps cad/'s
parametric and sandboxed-script endpoints so the agent can generate
real STEP geometry mid-design.

Sibling of `agent/`, `app/`, `cad/`, `mcp-electronics/`,
`mcp-image-gen/`, `landing/`, `docs/`.

## Tools

| name                          | params                            | what it does |
|-------------------------------|-----------------------------------|--------------|
| `list_parametric_templates`   | —                                 | enumerate cad/'s templates with their JSON Schemas |
| `generate_part`               | `template`, `inputs`              | build a parametric template -> base64 STEP |
| `generate_from_script`        | `code`, `timeout_s?`              | run agent-authored build123d script in cad/'s sandbox -> base64 STEP |

All three speak HTTP to cad/ at `CAD_BASE_URL`. STEP bytes are
returned base64-encoded as `step_b64` because MCP tool responses are
JSON. The caller decodes and routes the bytes through cad/'s
`/convert/step-to-gltf` for in-browser rendering, or stashes them on
project storage.

## Run locally

```sh
cd mcp-cad
uv sync
cp .env.example .env  # fill CAD_SHARED_SECRET to match cad/'s
uv run python -m cassen_cad_mcp.server
```

cad/ must be running on `CAD_BASE_URL` (default `http://127.0.0.1:8002`).

## Register with Claude Code

```json
{
  "mcpServers": {
    "cassen-cad": {
      "command": "C:\\Users\\HP\\.local\\bin\\uv.exe",
      "args": [
        "run",
        "--project",
        "C:\\Users\\HP\\Cassen\\mcp-cad",
        "python",
        "-m",
        "cassen_cad_mcp.server"
      ]
    }
  }
}
```

## What's NOT here yet

- Storage hand-off: today the tools return STEP bytes inline. A later
  phase should let cad/ stash STEP+GLB on Supabase Storage / R2 and
  return a signed URL instead, so the agent doesn't carry tens of KB
  of geometry through its context.
- Streaming: very large assemblies could exceed the JSON serialization
  ceiling. Current cap is whatever cad/ produces; templates are all
  under 50 KB.
