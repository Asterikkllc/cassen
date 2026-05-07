"""Parametric template registry.

Each template module registers itself with REGISTRY at import time. The
server reflects on REGISTRY to expose `GET /generate/parametric` and to
dispatch `POST /generate/parametric/{name}`.
"""

from .base import REGISTRY, TemplateSpec, shape_to_step_bytes

# Side-effect imports populate REGISTRY.
from . import bracket_l  # noqa: F401
from . import enclosure_box  # noqa: F401
from . import mounting_plate  # noqa: F401

__all__ = ["REGISTRY", "TemplateSpec", "shape_to_step_bytes"]
