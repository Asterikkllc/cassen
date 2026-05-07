"""90-degree L-shaped angle bracket."""

from __future__ import annotations

import build123d as bd
from pydantic import BaseModel, Field

from .base import TemplateSpec, register


class BracketLInput(BaseModel):
    arm_x_mm: float = Field(40.0, gt=5, le=300, description="length of horizontal arm")
    arm_z_mm: float = Field(40.0, gt=5, le=300, description="length of vertical arm")
    width_mm: float = Field(20.0, gt=2, le=300, description="Y dimension of both arms")
    thickness_mm: float = Field(3.0, gt=0.5, le=20)


def build(inputs: BracketLInput) -> bd.Part:
    horiz = bd.Box(inputs.arm_x_mm, inputs.width_mm, inputs.thickness_mm)
    horiz = horiz.translate(
        bd.Vector(inputs.arm_x_mm / 2, 0, inputs.thickness_mm / 2)
    )
    vert = bd.Box(inputs.thickness_mm, inputs.width_mm, inputs.arm_z_mm)
    vert = vert.translate(
        bd.Vector(inputs.thickness_mm / 2, 0, inputs.arm_z_mm / 2)
    )
    return horiz + vert


register(
    TemplateSpec(
        name="bracket_l",
        description=(
            "90-degree L-shaped angle bracket. Horizontal arm extends +X "
            "from origin, vertical arm extends +Z. Both share a corner at "
            "the origin. Common for shelf/wall mounting and chassis joinery."
        ),
        input_model=BracketLInput,
        build_fn=build,
    )
)
