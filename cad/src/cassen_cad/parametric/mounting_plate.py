"""Flat rectangular plate with a configurable hole pattern."""

from __future__ import annotations

import build123d as bd
from pydantic import BaseModel, Field, model_validator

from .base import TemplateSpec, register


class HoleSpec(BaseModel):
    x_mm: float = Field(..., ge=-500, le=500)
    y_mm: float = Field(..., ge=-500, le=500)
    diameter_mm: float | None = Field(
        None,
        gt=0.5,
        le=50,
        description="Optional per-hole diameter; falls back to default_hole_diameter_mm.",
    )


class MountingPlateInput(BaseModel):
    width_mm: float = Field(60.0, gt=5, le=500, description="X dimension")
    depth_mm: float = Field(40.0, gt=5, le=500, description="Y dimension")
    thickness_mm: float = Field(3.0, gt=0.5, le=30)
    default_hole_diameter_mm: float = Field(3.5, gt=0.5, le=50)
    holes: list[HoleSpec] = Field(default_factory=list, max_length=128)

    @model_validator(mode="after")
    def _check_holes_inside(self) -> "MountingPlateInput":
        for h in self.holes:
            d = h.diameter_mm or self.default_hole_diameter_mm
            half_w = self.width_mm / 2
            half_d = self.depth_mm / 2
            if abs(h.x_mm) + d / 2 > half_w or abs(h.y_mm) + d / 2 > half_d:
                raise ValueError(
                    f"hole at ({h.x_mm}, {h.y_mm}) ⌀{d} extends beyond plate edge"
                )
        return self


def build(inputs: MountingPlateInput) -> bd.Part:
    plate: bd.Part = bd.Box(inputs.width_mm, inputs.depth_mm, inputs.thickness_mm)
    for hole in inputs.holes:
        d = hole.diameter_mm or inputs.default_hole_diameter_mm
        cyl = bd.Cylinder(radius=d / 2, height=inputs.thickness_mm * 2)
        cyl = cyl.translate(bd.Vector(hole.x_mm, hole.y_mm, 0))
        plate = plate - cyl
    return plate


register(
    TemplateSpec(
        name="mounting_plate",
        description=(
            "Flat rectangular plate with a configurable hole pattern. Holes "
            "are through-holes; positions are in plate-centered XY mm. "
            "Optional per-hole diameter override; default applies otherwise."
        ),
        input_model=MountingPlateInput,
        build_fn=build,
    )
)
