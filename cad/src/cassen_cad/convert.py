"""STEP -> GLB conversion. cascadio wraps Open Cascade's glTF writer.

cascadio.step_to_glb is path-in / path-out only (pybind11 builtin), so
we round-trip the upload through tempfiles. The temp dir is removed
on exit even on conversion failure.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import cascadio


def step_bytes_to_glb_bytes(
    step_data: bytes,
    *,
    tol_linear: float = 0.01,
    tol_angular: float = 0.5,
    merge_primitives: bool = True,
) -> bytes:
    """Convert STEP file bytes to GLB (binary glTF) bytes.

    `tol_linear` and `tol_angular` control mesh deflection tolerances —
    smaller values mean denser meshes. The defaults match cascadio's,
    which produce viewer-quality geometry.
    """
    if not step_data:
        raise ValueError("step_data is empty")

    with tempfile.TemporaryDirectory(prefix="cassen-cad-") as tmp:
        in_path = Path(tmp) / "in.step"
        out_path = Path(tmp) / "out.glb"
        in_path.write_bytes(step_data)
        cascadio.step_to_glb(
            str(in_path),
            str(out_path),
            tol_linear=tol_linear,
            tol_angular=tol_angular,
            merge_primitives=merge_primitives,
        )
        if not out_path.exists() or out_path.stat().st_size == 0:
            raise RuntimeError("cascadio produced no output")
        return out_path.read_bytes()
