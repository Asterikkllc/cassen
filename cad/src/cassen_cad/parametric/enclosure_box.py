"""Rectangular hollow enclosure with open top."""

from __future__ import annotations

import build123d as bd
from pydantic import BaseModel, Field, model_validator

from .base import TemplateSpec, register


class EnclosureBoxInput(BaseModel):
    width_mm: float = Field(60.0, gt=5, le=500, description="X dimension")
    depth_mm: float = Field(40.0, gt=5, le=500, description="Y dimension")
    height_mm: float = Field(30.0, gt=5, le=500, description="Z dimension")
    wall_thickness_mm: float = Field(2.0, gt=0.5, le=20)

    @model_validator(mode="after")
    def _check_walls_fit(self) -> "EnclosureBoxInput":
        clearance = min(
            self.width_mm - 2 * self.wall_thickness_mm,
            self.depth_mm - 2 * self.wall_thickness_mm,
            self.height_mm - self.wall_thickness_mm,
        )
        if clearance <= 0:
            raise ValueError(
                "wall_thickness_mm leaves no interior cavity for the given dimensions"
            )
        return self


def build(inputs: EnclosureBoxInput) -> bd.Part:
    outer = bd.Box(inputs.width_mm, inputs.depth_mm, inputs.height_mm)
    inner = bd.Box(
        inputs.width_mm - 2 * inputs.wall_thickness_mm,
        inputs.depth_mm - 2 * inputs.wall_thickness_mm,
        inputs.height_mm - inputs.wall_thickness_mm,
    )
    inner = inner.translate(bd.Vector(0, 0, inputs.wall_thickness_mm / 2))
    return outer - inner


register(
    TemplateSpec(
        name="enclosure_box",
        description=(
            "Rectangular hollow enclosure with an open top. Walls of uniform "
            "thickness on bottom + four sides. Suitable for housing PCBs / "
            "electronics; lid is a separate template (later)."
        ),
        input_model=EnclosureBoxInput,
        build_fn=build,
    )
)
