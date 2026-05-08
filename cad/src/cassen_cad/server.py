from typing import Any

from fastapi import Body, Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError

from .convert import step_bytes_to_glb_bytes
from .parametric import REGISTRY, shape_to_step_bytes
from .rodin import RodinError, generate_rodin
from .sandbox import (
    SandboxRunError,
    SandboxValidationError,
    run_script,
)
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


@app.get("/generate/parametric")
async def list_parametric_templates() -> dict[str, Any]:
    """Return every available parametric template with its input schema."""
    return {
        "templates": [
            {
                "name": s.name,
                "description": s.description,
                "input_schema": s.input_model.model_json_schema(),
            }
            for s in REGISTRY.values()
        ]
    }


@app.post(
    "/generate/parametric/{template_name}",
    dependencies=[Depends(require_shared_secret)],
    responses={
        200: {"content": {"model/step": {}}},
        404: {"description": "Unknown template"},
        422: {"description": "Invalid inputs or build failure"},
    },
)
async def generate_parametric(
    template_name: str,
    body: dict[str, Any] = Body(default_factory=dict),
) -> Response:
    spec = REGISTRY.get(template_name)
    if not spec:
        raise HTTPException(404, f"unknown template: {template_name}")

    try:
        inputs = spec.input_model(**body)
    except ValidationError as exc:
        # pydantic includes the original Exception in `ctx`, which isn't
        # JSON-serializable. Strip context + url + input.
        raise HTTPException(
            422,
            detail=exc.errors(
                include_url=False,
                include_context=False,
                include_input=False,
            ),
        ) from exc

    try:
        shape = spec.build_fn(inputs)
        step = shape_to_step_bytes(shape)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(422, f"build failed: {exc}") from exc

    return Response(
        content=step,
        media_type="model/step",
        headers={
            "X-Cassen-Template": template_name,
            "X-Cassen-Output-Bytes": str(len(step)),
        },
    )


@app.post(
    "/generate/script",
    dependencies=[Depends(require_shared_secret)],
    responses={
        200: {"content": {"model/step": {}}},
        400: {"description": "Script rejected by AST allowlist"},
        413: {"description": "Script source exceeds size limit"},
        422: {"description": "Script ran but failed to produce STEP"},
        504: {"description": "Script exceeded wall-clock timeout"},
    },
)
async def generate_from_script(body: dict[str, Any] = Body(default_factory=dict)) -> Response:
    """Run an agent-authored build123d script in a sandbox and return STEP.

    Body: {"code": "...", "timeout_s"?: float}. The script must assign a
    build123d shape to a top-level `result` variable; the sandbox appends
    the export footer.
    """
    code = body.get("code")
    if not isinstance(code, str) or not code.strip():
        raise HTTPException(400, "missing 'code' string in body")
    if len(code) > 64 * 1024:
        raise HTTPException(413, "script exceeds 64 KB limit")

    # build123d's cold-import on Windows is ~10-15s. Defaults sized for
    # composite assemblies (drone frames, custom enclosures with cutouts):
    # 90s default leaves ~75-80s of actual geometry time after cold-import.
    # Cap is 240s for genuinely complex scripts (lofts, sweeps, branded
    # lettering as 3D extrusion, multi-arm hexacopters with cutouts).
    timeout_s = float(body.get("timeout_s") or 90.0)
    timeout_s = max(5.0, min(timeout_s, 240.0))

    try:
        result = run_script(code, timeout_s=timeout_s)
    except SandboxValidationError as exc:
        raise HTTPException(400, str(exc)) from exc
    except SandboxRunError as exc:
        msg = str(exc)
        status = 504 if "timeout" in msg.lower() else 422
        raise HTTPException(status, msg) from exc

    return Response(
        content=result.step_bytes,
        media_type="model/step",
        headers={
            "X-Cassen-Output-Bytes": str(len(result.step_bytes)),
            "X-Cassen-Duration-Ms": f"{result.duration_s * 1000:.0f}",
        },
    )


_RODIN_FORMAT_MEDIA_TYPES: dict[str, str] = {
    "glb": "model/gltf-binary",
    "fbx": "application/octet-stream",
    "obj": "model/obj",
    "stl": "model/stl",
    "step": "model/step",
    "usdz": "model/vnd.usdz+zip",
}


@app.post(
    "/generate/rodin",
    dependencies=[Depends(require_shared_secret)],
    responses={
        200: {"description": "Generated model bytes"},
        400: {"description": "Invalid prompt or option"},
        413: {"description": "Output exceeded MAX_RODIN_OUTPUT_BYTES"},
        502: {"description": "Hyper3D upstream error"},
        503: {"description": "HYPER3D_API_KEY not configured"},
        504: {"description": "Generation exceeded HYPER3D_MAX_WAIT_S"},
    },
)
async def generate_rodin_endpoint(body: dict[str, Any] = Body(default_factory=dict)) -> Response:
    """PRD section 5.2 tier 3 — generative geometry via Hyper3D Rodin Gen-2.

    Body: {prompt, geometry_format?, tier?, quality?, material?, bbox_mm?}.
    Returns the produced model file inline. Default format = glb (browser
    renderable). Generation is synchronous and can take 30s-10min.
    """
    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(400, "missing 'prompt' string in body")
    if len(prompt) > 4000:
        raise HTTPException(400, "prompt exceeds 4000 characters")

    geometry_format = str(body.get("geometry_format") or "glb").lower()
    tier = str(body.get("tier") or "Regular")
    quality = str(body.get("quality") or "medium")
    material = str(body.get("material") or "PBR")

    bbox_raw = body.get("bbox_mm")
    bbox_mm: tuple[float, float, float] | None = None
    if bbox_raw is not None:
        try:
            x, y, z = bbox_raw
            bbox_mm = (float(x), float(y), float(z))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(400, "bbox_mm must be a 3-element [x,y,z] list") from exc

    try:
        result = generate_rodin(
            prompt=prompt,
            geometry_format=geometry_format,
            tier=tier,
            quality=quality,
            material=material,
            bbox_mm=bbox_mm,
        )
    except RodinError as exc:
        raise HTTPException(exc.status, str(exc)) from exc

    media_type = _RODIN_FORMAT_MEDIA_TYPES.get(geometry_format, "application/octet-stream")
    return Response(
        content=result.bytes_,
        media_type=media_type,
        headers={
            "X-Cassen-Output-Bytes": str(len(result.bytes_)),
            "X-Cassen-Duration-Ms": f"{result.duration_s * 1000:.0f}",
            "X-Cassen-Rodin-Task": result.task_uuid,
            "X-Cassen-Rodin-File": result.file_name,
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
