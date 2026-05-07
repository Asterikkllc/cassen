"""Thin HTTP client for the cad/ FastAPI service.

The MCP layer is a translation surface; all CAD work happens in cad/.
We return STEP geometry as base64 because MCP tool responses serialize
to JSON, and STEP files are binary. Callers (the agent) decode and
either route the bytes to cad/'s STEP→GLB endpoint or stash them on
project storage.
"""

from __future__ import annotations

import base64
from typing import Any

import httpx

from .config import get_settings


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {get_settings().cad_shared_secret}"}


def list_templates() -> dict[str, Any]:
    s = get_settings()
    with httpx.Client(timeout=s.request_timeout_s) as client:
        r = client.get(f"{s.cad_base_url}/generate/parametric")
        r.raise_for_status()
        return r.json()


def generate_parametric(template: str, inputs: dict[str, Any]) -> dict[str, Any]:
    s = get_settings()
    with httpx.Client(timeout=s.request_timeout_s) as client:
        r = client.post(
            f"{s.cad_base_url}/generate/parametric/{template}",
            headers=_headers(),
            json=inputs,
        )
    if r.status_code == 404:
        return {"error": f"unknown template: {template}", "status": 404}
    if r.status_code == 422:
        return {
            "error": "invalid inputs or build failure",
            "status": 422,
            "detail": _safe_json_or_text(r),
        }
    r.raise_for_status()
    step = r.content
    return {
        "template": template,
        "inputs": inputs,
        "size_bytes": len(step),
        "step_b64": base64.b64encode(step).decode("ascii"),
    }


def generate_from_script(code: str, timeout_s: float | None = None) -> dict[str, Any]:
    s = get_settings()
    body: dict[str, Any] = {"code": code}
    if timeout_s is not None:
        body["timeout_s"] = float(timeout_s)
    with httpx.Client(timeout=s.request_timeout_s) as client:
        r = client.post(
            f"{s.cad_base_url}/generate/script",
            headers=_headers(),
            json=body,
        )
    if r.status_code == 400:
        return {
            "error": "script rejected by sandbox AST allowlist",
            "status": 400,
            "detail": _safe_json_or_text(r),
        }
    if r.status_code == 413:
        return {"error": "script source exceeds 64 KB", "status": 413}
    if r.status_code == 422:
        return {
            "error": "script ran but produced no STEP",
            "status": 422,
            "detail": _safe_json_or_text(r),
        }
    if r.status_code == 504:
        return {"error": "script exceeded wall-clock timeout", "status": 504}
    r.raise_for_status()
    step = r.content
    return {
        "size_bytes": len(step),
        "duration_ms": int(r.headers.get("X-Cassen-Duration-Ms", "0") or 0),
        "step_b64": base64.b64encode(step).decode("ascii"),
    }


def generate_rodin(
    *,
    prompt: str,
    geometry_format: str = "glb",
    tier: str = "Regular",
    quality: str = "medium",
    material: str = "PBR",
    bbox_mm: list[float] | None = None,
) -> dict[str, Any]:
    """Call cad/'s POST /generate/rodin. Long-poll friendly: timeout
    is overridden to honor cad/'s own HYPER3D_MAX_WAIT_S ceiling.
    """
    s = get_settings()
    body: dict[str, Any] = {
        "prompt": prompt,
        "geometry_format": geometry_format,
        "tier": tier,
        "quality": quality,
        "material": material,
    }
    if bbox_mm is not None:
        body["bbox_mm"] = bbox_mm

    # Rodin generation can take minutes; lift the per-call timeout to
    # 700s so we sit in the connection while cad/ polls upstream.
    with httpx.Client(timeout=max(s.request_timeout_s, 700.0)) as client:
        r = client.post(
            f"{s.cad_base_url}/generate/rodin",
            headers=_headers(),
            json=body,
        )
    if r.status_code in {400, 413, 502, 503, 504}:
        return {
            "error": f"rodin failed: HTTP {r.status_code}",
            "status": r.status_code,
            "detail": _safe_json_or_text(r),
        }
    r.raise_for_status()
    data = r.content
    return {
        "size_bytes": len(data),
        "format": geometry_format,
        "task_uuid": r.headers.get("X-Cassen-Rodin-Task", ""),
        "file_name": r.headers.get("X-Cassen-Rodin-File", ""),
        "duration_ms": int(r.headers.get("X-Cassen-Duration-Ms", "0") or 0),
        "model_b64": base64.b64encode(data).decode("ascii"),
    }


def _safe_json_or_text(r: httpx.Response) -> Any:
    try:
        return r.json()
    except Exception:  # noqa: BLE001
        return r.text[:500]
