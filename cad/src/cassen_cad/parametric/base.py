"""Shared types for parametric templates."""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import build123d as bd
from pydantic import BaseModel


@dataclass
class TemplateSpec:
    name: str
    description: str
    input_model: type[BaseModel]
    build_fn: Callable[[Any], bd.Compound | bd.Part | bd.Solid]


REGISTRY: dict[str, TemplateSpec] = {}


def register(spec: TemplateSpec) -> None:
    REGISTRY[spec.name] = spec


def shape_to_step_bytes(shape: Any) -> bytes:
    """Export a build123d shape to STEP bytes via a tempfile.

    build123d.export_step writes to a path; there's no in-memory API.
    """
    with tempfile.TemporaryDirectory(prefix="cassen-cad-step-") as tmp:
        out = Path(tmp) / "out.step"
        bd.export_step(shape, str(out))
        if not out.exists() or out.stat().st_size == 0:
            raise RuntimeError("build123d produced no STEP output")
        return out.read_bytes()
