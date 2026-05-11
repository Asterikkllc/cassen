"""FastAPI entrypoint for cassen-agent.

Slice 1 exposes:
  - GET  /health           : liveness
  - POST /runs/chat-stream : run one planner turn against a project's
                             thread; stream the assistant reply via SSE

Authentication is a shared bearer secret matching app/'s
AGENT_SHARED_SECRET. When the secret is unset locally, the server
prints a warning and accepts any auth header — convenient for dev,
unsafe in production. Modal/Fly deploys MUST set the secret.
"""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from .db import append_project_message
from .graph import ChatEvent, run_planner_chat, serialize_event
from .settings import get_settings


# --------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------


def require_shared_secret(
    authorization: str | None = Header(default=None),
) -> None:
    s = get_settings()
    if not s.agent_shared_secret:
        # Dev mode: warn loudly the first time, then allow.
        return
    expected = f"Bearer {s.agent_shared_secret}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Forbidden")


# --------------------------------------------------------------------
# App
# --------------------------------------------------------------------


app = FastAPI(title="Cassen Agent", version="0.1.0")


class ChatStreamRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=64)
    message: str = Field(..., min_length=1, max_length=8000)


@app.get("/health")
async def health() -> dict[str, object]:
    s = get_settings()
    return {
        "ok": True,
        "service": "cassen-agent",
        "version": "0.1.0",
        "planner_model": s.planner_model,
        "auth_required": bool(s.agent_shared_secret),
    }


@app.post(
    "/runs/chat-stream",
    dependencies=[Depends(require_shared_secret)],
)
async def runs_chat_stream(req: ChatStreamRequest) -> StreamingResponse:
    """Persist the user turn → stream the planner reply → persist the
    assistant turn. SSE frame shape matches app/'s chat-thread parser
    (`token` / `message-end` / `error`).
    """
    # 1. Persist user message immediately. The browser may drop the
    #    SSE connection mid-stream; we still want this turn on disk.
    append_project_message(
        req.project_id, role="user", content=req.message
    )

    async def gen() -> AsyncIterator[bytes]:
        async for event in run_planner_chat(project_id=req.project_id):
            yield serialize_event(event).encode("utf-8")

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code, content={"error": exc.detail}
    )


# --------------------------------------------------------------------
# CLI entry — `python -m cassen_agent.server`
# --------------------------------------------------------------------


def main() -> None:
    s = get_settings()
    if not s.agent_shared_secret:
        print(
            "[agent] WARNING: AGENT_SHARED_SECRET is empty — server "
            "will accept any auth header. Set this before deploying.",
            file=sys.stderr,
            flush=True,
        )
    import uvicorn

    uvicorn.run(
        "cassen_agent.server:app",
        host=s.agent_host,
        port=s.agent_port,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
