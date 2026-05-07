# cassen-agent

FastAPI surface around a LangGraph agent that drives a Cassen project.
Sibling of `app/` (Next.js) and `landing/`. Owns Anthropic + Supabase
writes from the server side.

## Run locally

```sh
cd agent
uv sync
cp .env.example .env  # fill in the keys; .env is gitignored
uv run uvicorn cassen_agent.server:app --reload --port 8001
```

`/health` should return `{"ok": true, ...}` once it's up.

## Endpoints

| Method | Path           | Auth                 | Notes                              |
|--------|----------------|----------------------|------------------------------------|
| GET    | `/health`      | none                 | uptime check                       |
| POST   | `/runs/stream` | Bearer shared secret | SSE; streams agent run as it goes  |

`/runs/stream` body:
```json
{ "project_id": "uuid", "owner_id": "user_clerk_id", "prompt": "..." }
```

Stream events look like:
```
data: {"kind":"status","node":null,"data":{"status":"planning"}}
data: {"kind":"node-start","node":"planner","data":null}
data: {"kind":"token","node":"planner","data":"{ \"product_type\": "}
...
data: {"kind":"node-end","node":"planner","data":{"text":"...","parsed":{...}}}
data: {"kind":"complete","data":{"status":"draft"}}
```

## How `app/` calls this

`app/` never calls Anthropic directly. The Next.js server action
`startAgentRun(projectId)` POSTs to this service with the shared bearer
secret (env var `AGENT_SHARED_SECRET`, identical on both sides). A
`/api/agent/runs/[id]/stream` route in `app/` proxies the SSE stream
back to the browser, adding Clerk auth on the public side.

## What's NOT here yet (later phases)

- Trigger.dev v3 wrapper for resumable, timeout-free execution. Right now the
  graph runs in-process; long jobs would die when the FastAPI worker recycles.
- Knowledge packs as MCP servers (electronics, mechanical, fluids). Phase 6+.
- Modal GPU calls (physics simulation, generative 3D). Phase 9–13.
- Tool calls into the parts grounding DB. Phase 6.

## Layout

```
agent/
  pyproject.toml
  .env.example
  src/cassen_agent/
    __init__.py
    settings.py     # pydantic-settings, reads .env
    db.py           # Supabase service-role wrapper
    graph.py        # LangGraph + Anthropic streaming + Langfuse tracing
    server.py       # FastAPI surface
```
