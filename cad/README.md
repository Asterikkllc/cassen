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

| method | path                       | auth          | notes |
|--------|----------------------------|---------------|-------|
| GET    | `/health`                  | none          | uptime probe |
| POST   | `/convert/step-to-gltf`    | Bearer secret | multipart `file=...` STEP/STP, returns `model/gltf-binary` (.glb) |

`/convert/step-to-gltf` rejects non-`.step` / `.stp` filenames (415),
files larger than `MAX_STEP_BYTES` (413, default 50 MB), and conversion
errors (422). Two response headers report
`X-Cassen-Source-Bytes` and `X-Cassen-Output-Bytes` so callers can log
compression ratios.

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

- **Phase 7c** swaps the in-browser Canvas to WebGPU + adds postprocessing.
- **Phase 8** (Build123d parametric CAD) will produce STEP files the
  agent can route through this endpoint and stash the resulting GLB
  on Supabase Storage / Cloudflare R2 with a signed URL.
- Caching: a content-hash → GLB map so repeat conversions are free.
- Streaming uploads / chunked responses for very large assemblies.
