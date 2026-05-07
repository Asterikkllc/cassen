"""Hyper3D Rodin Gen-2 client (PRD section 5.2 tier 3).

The Rodin API is a three-call async dance:

  1. POST /api/v2/rodin (multipart) -> {uuid, jobs: {subscription_key}}
     Submits a generation job; returns identifiers used for polling.
  2. POST /api/v2/status (form) -> {jobs: [{uuid, status}, ...]}
     Polled with `subscription_key`. Status flips through
     "Queueing" / "Waiting" / "Generating" / "Done" / "Failed".
  3. POST /api/v2/download (form) -> {list: [{url, name}, ...]}
     Returns short-lived URLs to GET the actual model files.

We collapse all three behind a single sync `generate_rodin()` that
returns the final model bytes. Internal calls use httpx.

Generative output stays as visualization-grade GLB (or whatever
format was requested); manufacturable parts are PRD-mandated to
route through tier 1 (curated parts) or tier 2 (build123d) instead.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx

from .settings import get_settings


_TERMINAL_DONE = {"Done"}
_TERMINAL_FAILED = {"Failed", "Error"}

_ALLOWED_FORMATS = {"glb", "fbx", "obj", "stl", "step", "usdz"}
_ALLOWED_TIERS = {"Sketch", "Regular", "Detail", "Smooth"}
_ALLOWED_QUALITIES = {"high", "medium", "low", "extra-low"}


class RodinError(RuntimeError):
    """Any failure interacting with Hyper3D Rodin."""

    def __init__(self, message: str, *, status: int = 502) -> None:
        super().__init__(message)
        self.status = status


@dataclass(frozen=True)
class RodinResult:
    bytes_: bytes
    file_name: str
    format: str
    duration_s: float
    task_uuid: str


def _require_key() -> str:
    s = get_settings()
    key = (s.hyper3d_api_key or "").strip()
    if not key:
        raise RodinError(
            "HYPER3D_API_KEY is not configured on the cad service",
            status=503,
        )
    return key


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_require_key()}"}


def submit_job(
    *,
    prompt: str,
    geometry_format: str = "glb",
    tier: str = "Regular",
    quality: str = "medium",
    material: str = "PBR",
    bbox_mm: tuple[float, float, float] | None = None,
) -> dict[str, Any]:
    """Submit a Rodin generation request. Returns the raw response JSON.

    Important fields callers consume:
      - `uuid`             — task identifier for /download
      - `jobs.subscription_key` — token for /status polling
    """
    if geometry_format not in _ALLOWED_FORMATS:
        raise RodinError(
            f"geometry_format {geometry_format!r} not in {sorted(_ALLOWED_FORMATS)}",
            status=400,
        )
    if tier not in _ALLOWED_TIERS:
        raise RodinError(
            f"tier {tier!r} not in {sorted(_ALLOWED_TIERS)}",
            status=400,
        )
    if quality not in _ALLOWED_QUALITIES:
        raise RodinError(
            f"quality {quality!r} not in {sorted(_ALLOWED_QUALITIES)}",
            status=400,
        )
    s = get_settings()

    # Rodin's /rodin endpoint expects multipart/form-data even when only
    # text fields are submitted. httpx accepts a `files` arg with no
    # binary content, but the cleanest portable way is to build the form
    # data via `data=` for plain fields. The backend tolerates this.
    form: dict[str, str] = {
        "prompt": prompt,
        "geometry_file_format": geometry_format,
        "tier": tier,
        "quality": quality,
        "material": material,
    }
    if bbox_mm:
        x, y, z = bbox_mm
        form["bbox_condition"] = f"[{float(x)}, {float(y)}, {float(z)}]"

    with httpx.Client(timeout=60.0) as client:
        try:
            r = client.post(
                f"{s.hyper3d_base_url}/rodin",
                headers=_auth_headers(),
                # Rodin expects multipart/form-data; an empty `files`
                # tuple plus `data` produces the right wire format.
                data=form,
                files={"_marker": ("", b"", "application/octet-stream")},
            )
        except httpx.RequestError as exc:
            raise RodinError(f"submit failed: {exc}", status=502) from exc

    if r.status_code >= 400:
        raise RodinError(
            f"submit returned HTTP {r.status_code}: {r.text[:300]}",
            status=502,
        )
    try:
        body = r.json()
    except Exception as exc:  # noqa: BLE001
        raise RodinError(f"submit returned non-JSON: {r.text[:200]}", status=502) from exc

    uuid = body.get("uuid")
    sub_key = (body.get("jobs") or {}).get("subscription_key")
    if not uuid or not sub_key:
        raise RodinError(
            f"submit response missing uuid or subscription_key: {body!r}",
            status=502,
        )
    return body


def poll_until_done(subscription_key: str) -> list[dict[str, Any]]:
    """Block until every job under this subscription finishes (or fails).

    Returns the final list of job dicts. Raises `RodinError` on
    timeout, network failure, or any job in `Failed`/`Error`.
    """
    s = get_settings()
    deadline = time.monotonic() + s.hyper3d_max_wait_s
    interval = max(1.0, s.hyper3d_poll_interval_s)

    with httpx.Client(timeout=30.0) as client:
        last_jobs: list[dict[str, Any]] = []
        while time.monotonic() < deadline:
            try:
                r = client.post(
                    f"{s.hyper3d_base_url}/status",
                    headers=_auth_headers(),
                    data={"subscription_key": subscription_key},
                )
            except httpx.RequestError as exc:
                raise RodinError(f"status poll failed: {exc}", status=502) from exc
            if r.status_code >= 400:
                raise RodinError(
                    f"status returned HTTP {r.status_code}: {r.text[:200]}",
                    status=502,
                )
            try:
                body = r.json()
            except Exception as exc:  # noqa: BLE001
                raise RodinError(
                    f"status returned non-JSON: {r.text[:200]}", status=502
                ) from exc
            last_jobs = body.get("jobs") or []
            statuses = {j.get("status") for j in last_jobs}
            if statuses & _TERMINAL_FAILED:
                raise RodinError(
                    f"a Rodin job failed: {last_jobs}", status=502
                )
            if statuses and statuses.issubset(_TERMINAL_DONE):
                return last_jobs
            time.sleep(interval)

    raise RodinError(
        f"Rodin job exceeded HYPER3D_MAX_WAIT_S={s.hyper3d_max_wait_s}s; "
        f"last jobs: {last_jobs}",
        status=504,
    )


def download_first_match(task_uuid: str, *, geometry_format: str) -> tuple[bytes, str]:
    """Fetch the produced model file in the requested format.

    Returns (bytes, file_name).
    """
    s = get_settings()
    with httpx.Client(timeout=60.0) as client:
        try:
            r = client.post(
                f"{s.hyper3d_base_url}/download",
                headers=_auth_headers(),
                data={"task_uuid": task_uuid},
            )
        except httpx.RequestError as exc:
            raise RodinError(f"download list failed: {exc}", status=502) from exc
        if r.status_code >= 400:
            raise RodinError(
                f"download returned HTTP {r.status_code}: {r.text[:200]}",
                status=502,
            )
        try:
            body = r.json()
        except Exception as exc:  # noqa: BLE001
            raise RodinError(
                f"download returned non-JSON: {r.text[:200]}", status=502
            ) from exc

        items = body.get("list") or []
        suffix = "." + geometry_format.lower()
        match = next(
            (it for it in items if str(it.get("name", "")).lower().endswith(suffix)),
            None,
        )
        if match is None and items:
            match = items[0]  # fall back to whatever Rodin produced
        if match is None or not match.get("url"):
            raise RodinError(
                f"download list empty for task {task_uuid}: {body!r}",
                status=502,
            )

        url = str(match["url"])
        name = str(match.get("name") or f"rodin-{task_uuid}{suffix}")
        try:
            file_resp = client.get(url, timeout=120.0)
        except httpx.RequestError as exc:
            raise RodinError(f"file fetch failed: {exc}", status=502) from exc
        if file_resp.status_code >= 400:
            raise RodinError(
                f"file fetch HTTP {file_resp.status_code} for {name}",
                status=502,
            )
        data = file_resp.content
        if len(data) > s.max_rodin_output_bytes:
            raise RodinError(
                f"Rodin output {len(data)} bytes exceeds "
                f"max_rodin_output_bytes={s.max_rodin_output_bytes}",
                status=413,
            )
        return data, name


def generate_rodin(
    *,
    prompt: str,
    geometry_format: str = "glb",
    tier: str = "Regular",
    quality: str = "medium",
    material: str = "PBR",
    bbox_mm: tuple[float, float, float] | None = None,
) -> RodinResult:
    """Submit a job, poll, download, return result. Sync; can take minutes.

    Re-raises `RodinError` from any of the three steps. Caller (the
    HTTP route) maps `RodinError.status` to an HTTP status code.
    """
    if not (prompt or "").strip():
        raise RodinError("prompt must be non-empty", status=400)
    t0 = time.perf_counter()

    sub = submit_job(
        prompt=prompt,
        geometry_format=geometry_format,
        tier=tier,
        quality=quality,
        material=material,
        bbox_mm=bbox_mm,
    )
    task_uuid = str(sub["uuid"])
    sub_key = str(sub["jobs"]["subscription_key"])

    poll_until_done(sub_key)
    data, file_name = download_first_match(task_uuid, geometry_format=geometry_format)

    return RodinResult(
        bytes_=data,
        file_name=file_name,
        format=geometry_format,
        duration_s=time.perf_counter() - t0,
        task_uuid=task_uuid,
    )
