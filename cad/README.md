# cassen-cad

Cassen v1 CAD service. Single concern for now: convert **STEP → GLB**
so the in-browser viewer can render manufacturable geometry.

Sibling of `agent/`, `app/`, `mcp-electronics/`, `mcp-image-gen/`,
`landing/`, `docs/`.

## Why a separate service

CAD work is CPU-heavy and pulls in Open Cascade (~200 MB). Keeping it
out of `agent/` means agent restarts don't trash in-flight conversions
and CAD scaling is independent of LLM-bound agent throughput.

## Run locally

```sh
cd cad
uv sync
cp .env.example .env  # fill CAD_SHARED_SECRET
uv run uvicorn cassen_cad.server:app --host 127.0.0.1 --port 8002
```

## Endpoints

| method | path                                          | auth          | notes |
|--------|-----------------------------------------------|---------------|-------|
| GET    | `/health`                                     | none          | uptime probe |
| POST   | `/convert/step-to-gltf`                       | Bearer secret | multipart `file=...` STEP/STP, returns `model/gltf-binary` (.glb) |
| GET    | `/generate/parametric`                        | none          | list of templates + each template's input JSON Schema |
| POST   | `/generate/parametric/{name}`                 | Bearer secret | JSON body of inputs, returns `model/step` |
| POST   | `/generate/script`                            | Bearer secret | Sandboxed build123d script -> `model/step` |

`/convert/step-to-gltf` rejects non-`.step` / `.stp` filenames (415),
files larger than `MAX_STEP_BYTES` (413, default 50 MB), and conversion
errors (422). Two response headers report
`X-Cassen-Source-Bytes` and `X-Cassen-Output-Bytes` so callers can log
compression ratios.

## Parametric templates (Phase 8a)

Three templates ship out of the box, each with a typed Pydantic input
schema and bounded numeric ranges:

- **enclosure_box** — rectangular hollow enclosure with open top, walls
  of uniform thickness. Inputs: `width_mm`, `depth_mm`, `height_mm`,
  `wall_thickness_mm`. Validates that the cavity has positive volume.
- **mounting_plate** — flat plate with a configurable hole pattern.
  Inputs: `width_mm`, `depth_mm`, `thickness_mm`, `default_hole_diameter_mm`,
  `holes` (list of `{x_mm, y_mm, diameter_mm?}`). Validates each hole
  fits within the plate footprint.
- **bracket_l** — 90-degree L-shaped angle bracket. Inputs:
  `arm_x_mm`, `arm_z_mm`, `width_mm`, `thickness_mm`. Horizontal arm
  along +X, vertical arm along +Z, sharing a corner at the origin.

To add a template:
1. New file under `src/cassen_cad/parametric/<name>.py`.
2. Define a Pydantic input model + a `build(inputs)` function returning
   a build123d Part / Compound.
3. Register via `register(TemplateSpec(name, description, input_model, build))`.
4. Import the module from `parametric/__init__.py`.

The endpoint reflects on the registry, so `GET /generate/parametric`
auto-discovers new templates.

## Sandboxed script execution (Phase 8b)

`POST /generate/script` lets the agent author a build123d Python script
on the fly and have cad/ execute it under a two-layer sandbox:

1. **AST allowlist** — only `import build123d` and `import math` are
   accepted. Any reference to `os`, `socket`, `subprocess`, `eval`,
   `exec`, `__import__`, `open`, dunder attribute escapes (`.__class__`,
   `.__bases__`, `.__subclasses__`) etc. is rejected at parse time with
   HTTP 400.
2. **Subprocess isolation** — validated code runs in a fresh
   `python -I -B` process with a pruned environment, no shared state,
   a wall-clock timeout (default 30s, max 60s), and on POSIX,
   `RLIMIT_CPU` + `RLIMIT_AS` (512 MB).

The script must assign a build123d shape to a top-level `result`
variable. The runner appends the export footer:

```python
# body example
{
  "code": "from build123d import Box, Cylinder\nresult = Box(40, 30, 10) - Cylinder(5, 20)",
  "timeout_s": 30
}
```

Status codes: 400 (AST rejection / missing code), 413 (>64 KB source),
422 (script ran but produced no STEP), 504 (wall-clock timeout).

The sandbox is defence-in-depth, not a container. A later phase may
move execution to Modal sandboxes; the AST gate stays in front of that.

## Caller pattern

```python
import httpx
with open("part.step", "rb") as f:
    resp = httpx.post(
        "http://127.0.0.1:8002/convert/step-to-gltf",
        headers={"Authorization": f"Bearer {CAD_SHARED_SECRET}"},
        files={"file": ("part.step", f, "model/step")},
        timeout=60,
    )
glb_bytes = resp.content
```

## What's NOT here yet (later phases)

- **Phase 8c** wraps these endpoints as MCP tools (mcp-cad/) so the
  agent can call them as first-class tools alongside electronics.
- Caching: a content-hash -> GLB map so repeat conversions are free.
- Streaming uploads / chunked responses for very large assemblies.
