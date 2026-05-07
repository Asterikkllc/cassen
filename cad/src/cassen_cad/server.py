from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response

from .convert import step_bytes_to_glb_bytes
from .settings import get_settings


def require_shared_secret(authorization: str | None = Header(default=None)) -> None:
    expected = f"Bearer {get_settings().cad_shared_secret}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Forbidden")


app = FastAPI(title="Cassen CAD", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "service": "cassen-cad", "version": "0.1.0"}


@app.post(
    "/convert/step-to-gltf",
    dependencies=[Depends(require_shared_secret)],
    responses={
        200: {"content": {"model/gltf-binary": {}}},
        413: {"description": "STEP file exceeds MAX_STEP_BYTES"},
        415: {"description": "Unsupported file extension"},
        422: {"description": "Conversion failed"},
    },
)
async def convert_step_to_gltf(file: UploadFile = File(...)) -> Response:
    settings = get_settings()
    name = (file.filename or "").lower()
    if not (name.endswith(".step") or name.endswith(".stp")):
        raise HTTPException(415, "filename must end in .step or .stp")

    data = await file.read()
    if len(data) > settings.max_step_bytes:
        raise HTTPException(
            413,
            f"STEP file is {len(data)} bytes; max is {settings.max_step_bytes}",
        )

    try:
        glb = step_bytes_to_glb_bytes(data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(422, f"Conversion failed: {exc}") from exc

    return Response(
        content=glb,
        media_type="model/gltf-binary",
        headers={
            "X-Cassen-Source-Bytes": str(len(data)),
            "X-Cassen-Output-Bytes": str(len(glb)),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


def main() -> None:
    import uvicorn

    s = get_settings()
    uvicorn.run(
        "cassen_cad.server:app",
        host=s.cad_host,
        port=s.cad_port,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
