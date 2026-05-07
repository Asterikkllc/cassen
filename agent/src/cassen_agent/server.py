from collections.abc import AsyncIterator

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from .graph import GraphInput, run_graph
from .settings import get_settings


class RunRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=64)
    owner_id: str = Field(..., min_length=1, max_length=64)
    prompt: str = Field(..., min_length=1, max_length=8000)


def require_shared_secret(authorization: str | None = Header(default=None)) -> None:
    expected = f"Bearer {get_settings().agent_shared_secret}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Forbidden")


app = FastAPI(title="Cassen Agent", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "service": "cassen-agent", "version": "0.1.0"}


@app.post("/runs/stream", dependencies=[Depends(require_shared_secret)])
async def run_stream(req: RunRequest) -> StreamingResponse:
    async def gen() -> AsyncIterator[bytes]:
        async for event in run_graph(
            GraphInput(
                project_id=req.project_id,
                owner_id=req.owner_id,
                prompt=req.prompt,
            )
        ):
            yield event.to_sse().encode("utf-8")

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
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


def main() -> None:
    import uvicorn

    s = get_settings()
    uvicorn.run(
        "cassen_agent.server:app",
        host=s.agent_host,
        port=s.agent_port,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
