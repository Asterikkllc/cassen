"""LangGraph that drives a single project run.

Phase 5 skeleton: planner -> designer. Each node calls Claude for real
reasoning but the prompts are minimal — knowledge packs (electronics,
mechanical, fluids) come online in Phase 6+.

Tracing: Langfuse v4 (OpenTelemetry-based). Wraps the run in
`propagate_attributes` for trace-level user_id/metadata, then spans
each node via `start_as_current_observation(as_type="generation")`.
Falls through to a nullcontext when LANGFUSE keys are missing.
"""

from __future__ import annotations

import base64
import json
import sys
from collections.abc import AsyncIterator
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any

import httpx
from anthropic import AsyncAnthropic
from langfuse import Langfuse, propagate_attributes

from .db import append_version_snapshot, update_project_status
from .settings import get_settings
from .tools import mcp_session, run_tool_using_loop


async def _convert_step_to_glb(step_b64: str) -> tuple[str, int] | None:
    """Convert a base64-encoded STEP file to base64-encoded GLB bytes by
    calling cad/'s /convert/step-to-gltf endpoint.

    Returns (glb_b64, glb_byte_count) on success, None on any failure
    (missing config, network error, conversion error). Failure is non-
    fatal — the run still completes; the viewer just falls back to its
    placeholder when no GLB is in the snapshot.
    """
    if not step_b64:
        return None
    s = get_settings()
    if not (s.cad_base_url and s.cad_shared_secret):
        print("[agent] glb skip: cad_base_url / cad_shared_secret unset", file=sys.stderr)
        return None
    try:
        step_bytes = base64.b64decode(step_b64)
    except Exception as exc:  # noqa: BLE001
        print(f"[agent] glb skip: bad base64 step bytes ({exc})", file=sys.stderr)
        return None

    step_size = len(step_bytes)
    print(
        f"[agent] glb convert: posting {step_size:,} byte STEP to cad/...",
        file=sys.stderr,
    )

    import time as _time
    t0 = _time.perf_counter()

    # 240s timeout — cascadio's STEP→GLB conversion can take 1-3 minutes
    # on complex composite STEPs (e.g. a quadcopter assembly with arms,
    # landing gear, payload cradle, branding text → ~800 KB+ STEP).
    # 60s was way too tight; runs were silently failing here, leaving
    # the viewer with no GLB and falling back to electronics-MPN boxes.
    try:
        async with httpx.AsyncClient(timeout=240.0) as client:
            r = await client.post(
                f"{s.cad_base_url}/convert/step-to-gltf",
                headers={"Authorization": f"Bearer {s.cad_shared_secret}"},
                files={"file": ("part.step", step_bytes, "model/step")},
            )
    except httpx.RequestError as exc:
        elapsed = _time.perf_counter() - t0
        print(
            f"[agent] glb skip: cad request failed after {elapsed:.1f}s "
            f"({type(exc).__name__}: {exc})",
            file=sys.stderr,
        )
        return None

    elapsed = _time.perf_counter() - t0

    if r.status_code != 200:
        body_preview = (r.text or "")[:200]
        print(
            f"[agent] glb skip: cad returned HTTP {r.status_code} after "
            f"{elapsed:.1f}s: {body_preview}",
            file=sys.stderr,
        )
        return None

    glb = r.content
    if not glb:
        print(
            f"[agent] glb skip: cad returned 200 but empty body after "
            f"{elapsed:.1f}s",
            file=sys.stderr,
        )
        return None
    print(
        f"[agent] glb convert: ok — {step_size:,} byte STEP -> "
        f"{len(glb):,} byte GLB in {elapsed:.1f}s",
        file=sys.stderr,
    )
    return base64.b64encode(glb).decode("ascii"), len(glb)


@dataclass
class GraphInput:
    project_id: str
    owner_id: str
    prompt: str


@dataclass
class GraphEvent:
    """A single SSE-friendly event."""

    kind: str  # "status" | "node-start" | "token" | "node-end" | "complete" | "error"
    node: str | None = None
    data: Any = None

    def to_sse(self) -> str:
        payload = {"kind": self.kind, "node": self.node, "data": self.data}
        return f"data: {json.dumps(payload, default=str)}\n\n"


PLANNER_SYSTEM = """You are the Cassen planner. The user wants to build a physical \
product. Decompose their request into:

1. The product type (one phrase: e.g. "smart self-watering planter").
2. The relevant knowledge domains from this fixed set: electronics, mechanical, fluids. \
List EVERY domain that applies — most projects span at least two. A smart planter \
involves all three (sensors/MCU = electronics, enclosure/mounting = mechanical, \
pump/tubing = fluids). A drone is electronics + mechanical. A PCB-only project is \
electronics alone.
3. The 5-7 highest-value design questions to answer next.

Respond in compact JSON:
{
  "product_type": "...",
  "domains": ["..."],
  "questions": ["...", "..."]
}
No prose outside the JSON.
"""

DESIGNER_SYSTEM = """You are the Cassen designer. Synthesize the planner's \
decomposition and the researchers' findings into ONE coherent first-pass design.

Inputs you may receive (any subset):
- Electronics picks (real MPNs from Digi-Key/Mouser/Nexar).
- Mechanical hardware selections (DIN/ISO/ANSI part IDs from the curated catalog).
- Mechanical CAD selection (a parametric template + dimensions + STEP geometry).
- Fluid-system selections (pumps/valves/tubing/fittings part IDs from the curated catalog).

If the input says "NO_GROUNDED_PARTS" or "NO_GROUNDED_MPN" for a domain, \
the researcher returned nothing for that domain. You MUST then output \
id="NO_GROUNDED_MPN" (electronics) or id="NO_GROUNDED_PART" (mechanical/fluids) \
for every line item in that domain. **Never** fabricate an MPN, part_id, \
or supplier name to fill the gap. Hallucinated identifiers ship to a real \
sourcing pipeline and break it — a placeholder is always better.

Your output, plain markdown, no preamble:

## Components

A flat list of every part the design needs, ordered by domain (electronics, then \
mechanical hardware, then mechanical CAD geometry, then fluids). For each item:
- The exact identifier the researcher returned (MPN for electronics, part_id for \
  mechanical/fluids, template+inputs for CAD geometry). If research returned \
  nothing for a domain, write the literal placeholder shown above. NEVER \
  invent identifiers.
- One-line rationale tied to the project's actual needs.

## Cross-domain checks

A short list of compatibility checks across domains: voltage rails match between \
electronics and pumps/valves; enclosure dimensions accommodate the PCB and any \
sensor/pump mounting; tubing OD/ID matches pump and valve ports; fastener sizes \
match the CAD geometry's clearance holes.

## Risks / unknowns

3-5 bullets naming the genuine open questions: thermal headroom, sealing on \
moisture, sourcing for any borderline parts, etc.

End your turn with a compact JSON summary on a NEW LINE:
{
  "bom": [
    { "domain": "electronics|mechanical|cad|fluids", "id": "...", "function": "...", "rationale": "..." },
    ...
  ]
}

The BoM is the persisted artifact downstream consumers (UI, sourcing agent, \
firmware agent) read. Every research-grounded part MUST appear; do not silently \
drop any.
"""

FLUIDS_RESEARCH_SYSTEM = """You are the Cassen fluids researcher.

Your job is to ground the project's fluid-system decisions (pumps, \
valves, tubing, fittings) in real, sourceable parts. Tools:
- list_categories: see what kinds of parts the catalog covers \
  (pump, valve, tubing, fitting).
- search_part(query, category?, limit?): substring search by spec \
  ('R385', '12V solenoid'), description, or use case ('aquarium', \
  'irrigation', 'pneumatic').
- get_part(part_id): full record for one id (e.g. 'pump-r385-12v-water').
- recommend_for_function(function, context?): keyword heuristic — \
  useful for noun phrases like 'water a planter on a 12V line' or \
  'shut off air supply on power loss'.

HARD RULES (non-negotiable):
- DO NOT ask the user clarifying questions. The user has already left the \
  room. They cannot answer.
- DO NOT stall waiting for confirmation. Make reasonable assumptions and \
  proceed.
- State your assumptions in 1-3 bullets at the top, then IMMEDIATELY \
  start calling tools.
- Failing to call any tool is a failure. You MUST end with the trailing \
  JSON object below.

Process:
1. State your assumptions briefly (e.g. "Assuming 12V rail, 6 mm silicone \
   tubing, gravity-fed reservoir").
2. Identify the project's fluid needs (move water? dispense precisely? \
   actuate pneumatic cylinders? shut off on power loss?).
3. For each need, call recommend_for_function or search_part to find \
   candidates, then get_part for the chosen id.
4. Pay attention to compatibility: pump port (1/2 BSP, 6 mm barb) must \
   match the tubing OD/ID and the fittings; voltage must match the \
   project's power rail; max_pressure must exceed expected head.
5. End your turn with a compact JSON summary:
   {
     "fluid_picks": [
       { "function": "move water from reservoir to soil", "part_id": "...", "rationale": "..." },
       ...
     ]
   }
   No prose after the JSON.

Three to six tool calls is typical. Don't pick more parts than the \
project actually needs. Don't invent part IDs — only return ones a \
tool returned to you.
"""


MECHANICAL_RESEARCH_SYSTEM = """You are the Cassen mechanical researcher.

Your job is to ground the project's structural / hardware decisions in \
real, sourceable parts BEFORE any CAD geometry is generated. Tools:
- list_categories: see what kinds of mechanical parts the catalog covers \
  (fastener, bearing, extrusion, standoff, linear_motion).
- search_part(query, category?, limit?): substring search the catalog by \
  size like 'M3x10' or '608', spec like 'DIN 912', or use case.
- get_part(part_id): full record for one id (e.g. 'din912-m3-10').
- recommend_for_function(function, context?): keyword heuristic — useful \
  when you know the function ('mount PCB', 'vibration-resistant nut', \
  'linear motion') but not the specific spec.

HARD RULES (non-negotiable):
- DO NOT ask the user clarifying questions. The user has already left the \
  room. They cannot answer.
- DO NOT stall waiting for confirmation. Make reasonable assumptions and \
  proceed.
- State your assumptions in 1-3 bullets at the top, then IMMEDIATELY \
  start calling tools.
- Failing to call any tool is a failure. You MUST end with the trailing \
  JSON object below.

Process:
1. State your assumptions briefly (e.g. "Assuming 3D-printed enclosure, \
   M3 fasteners throughout, no extrusion frame").
2. Identify the project's mechanical needs (assembly fasteners? \
   structural extrusion? bearings? standoffs?).
3. For each need, call recommend_for_function to discover candidates, \
   then get_part for the one you choose. Use search_part when you \
   already have a size in mind.
4. End your turn with a compact JSON summary:
   {
     "mechanical_picks": [
       { "function": "mount PCB to enclosure", "part_id": "...", "rationale": "..." },
       ...
     ]
   }
   No prose after the JSON.

Three to six tool calls is typical. Don't pick more parts than the \
project actually needs — for a small electronics enclosure that's \
usually 1-2 picks (standoffs + fasteners). Don't invent part IDs — \
only return ones a tool returned to you.
"""


MECHANICAL_DESIGN_SYSTEM = """You are the Cassen mechanical designer.

Your job is to PRODUCE THE PROJECT'S ACTUAL GEOMETRY — whatever the \
user is building. A smart planter renders as a planter shape. A robot \
arm renders as a robot arm. A delivery drone renders as a drone. A \
fluid manifold renders as a manifold. A jig or fixture renders as that \
jig. The geometry must visually represent the project, not the nearest \
stock primitive.

build123d is a code-first parametric CAD library. You write Python; \
the sandbox runs it; the resulting STEP gets converted to GLB and \
rendered in the user's viewer. Treat geometry the way you'd treat any \
other code-generation problem: decompose the project into primitives, \
compose them with booleans, return one final Part.

You have THREE paths to geometry; pick by what the project needs:

(A) `generate_from_script(code, timeout_s?)` — **DEFAULT for engineered \
mechanical parts.** Run an agent-authored build123d Python script in a \
sandbox. Best for: enclosures with cutouts, frames, brackets, mounting \
plates, payload bays, anything that has to be MANUFACTURABLE \
(3D-printed, CNC'd, sheet-metal). Output is precise, parametric, with \
real fastener holes and cavities. The script must end with \
`result = <build123d Part>`. Imports allowed: `build123d`, `math`. \
Default timeout 90s, max 240s — pass `timeout_s=180` for assemblies \
with >5 boolean ops.

(B) `generate_organic(prompt, geometry_format?, tier?, quality?, ...)` \
— **for VISUAL / aesthetic / showcase geometry.** Calls Hyper3D Rodin \
Gen-2, a generative AI 3D model. Best for: things the user wants to \
LOOK like a real product — sleek consumer-electronics shells, curved \
fan blades, organic planter pots, character props, stylized housings. \
Output is mesh-style geometry (GLB/STEP), not engineering-grade. \
Per PRD §5.2 tier 3, generative output is for visualization; \
manufacturable parts always route through (A) or (C). \
**CALL THIS when the user asks for "modern", "sleek", "unique design", \
"custom looking", or any phrasing that implies the visual matters \
more than the engineering.** A drone frame for analysis: use (A). \
A drone shell for the marketing render: use (B). \
Default quality is `medium`; use `quality="high"` for the final design \
artifact. Format defaults to `glb` (browser-renderable). \
Note: requires `HYPER3D_API_KEY` to be set on the cad/ service. If \
the call returns 503 with that message, fall back to (A) and tell \
the user the key is missing.

(C) `generate_part(template, inputs)` + `list_parametric_templates` — \
fall-back primitives. The library only contains 3 trivial templates \
(`enclosure_box`, `mounting_plate`, `bracket_l`). Use ONLY when one of \
them is a near-perfect fit for the WHOLE project. Don't approximate \
complex shapes with these.

# Routing rule

Most projects need BOTH (A) and (B): the engineered functional bits \
via build123d (mounting structure, payload bay, fastener holes), and \
the visible shell / aesthetic via Rodin (the part the user looks at). \
But you can only pick ONE for the trailing JSON. **Default to (A)** \
unless the project's primary deliverable is a visual concept and the \
user said "modern", "sleek", "looks like X", "custom design".

# Build123d — API CHEAT SHEET (use ONLY what's below)

Imports — ONLY:
```python
from build123d import *
import math
```

Primitives (note kwargs vs positional — get this wrong and the script 400s):
```python
Box(length, width, height)              # POSITIONAL ONLY for the 3 sizes
Cylinder(radius=8, height=20)           # kwargs OK
Sphere(radius=35)                       # kwargs OK
Vector(10, 0, 5)                        # POSITIONAL ONLY — Vector(x=10, ...) FAILS
extrude(Text("Label", font_size=8), amount=1)   # for 3D-extruded branding text
```

Methods — they RETURN a new shape, you MUST reassign:
```python
shape = shape.translate(Vector(10, 0, 5))
shape = shape.rotate(Axis.Z, 45)        # angle is a plain float in DEGREES
```

Booleans — combine into a single Part:
```python
shape = a + b                           # union
shape = a - b                           # subtract (cuts a hole)
```

# DO NOT USE — these will all fail

These are common hallucinated APIs that build123d does NOT support:

- `Vector(x=10, y=0, z=5)` — keyword args fail with `Unexpected argument(s) x, y, z`. Use `Vector(10, 0, 5)`.
- `Cone(radius=R, height=H)` — wrong signature; raises `unexpected keyword argument 'radius'`. Build a tapered shape from a Cylinder + Sphere or skip the cone entirely.
- `Angle(deg, "DEGREES")` — there is NO `Angle` class. Just pass a float in degrees: `shape.rotate(Axis.Z, 45)`.
- `Axis.z` (lowercase) — use `Axis.Z` (uppercase). Likewise `Axis.X`, `Axis.Y`.
- Skipping the `result = Part() + ...` start AND/OR the `result = Part() + result` end. Without those, complex scripts fail at STEP export with `'ShapeList' object has no attribute 'wrapped'`.

# Composition — the empirically-verified pattern

Boolean operators (`+`, `-`) on build123d shapes can produce a \
`Compound` that contains multiple disjoint `Solid`s — the STEP \
exporter rejects those with `'ShapeList' object has no attribute \
'wrapped'`. The cure is two-fold and you MUST do BOTH:

1. **START** every script with `result = Part() + <first primitive>` \
   (not `result = Cylinder(...)`). The leading `Part()` keeps `result` \
   typed as a single Part.
2. **END** every script with `result = Part() + result` as a \
   defensive cast. This flattens any accumulated Compound back into a \
   single exportable Part. Skip this and any reasonably complex \
   script will fail at the STEP export step.

Between those two lines, accumulate `result = result + <part>` ONE \
AT A TIME, and cut features with `result = result - <hole>`.

# Working template — empirically verified, copy this shape

```python
from build123d import *
import math

# 1. START with Part()-prefix
result = Part() + Cylinder(radius=40, height=3)

# 2. Fold in helper parts ONE AT A TIME
result = result + Cylinder(radius=5, height=20).translate(Vector(0, 0, 10))

# 3. Loop for arrayed features (radial arms, hole patterns, petals,
#    gear teeth, robot fingers, bolt circles, fan blades, irrigation
#    ports, etc.)
N = 4
for i in range(N):
    angle_deg = i * (360 / N)
    angle_rad = math.radians(angle_deg)
    arm = Box(80, 10, 5).translate(Vector(40, 0, 0)).rotate(Axis.Z, angle_deg)
    result = result + arm
    tip_x = 80 * math.cos(angle_rad)
    tip_y = 80 * math.sin(angle_rad)
    tip = Cylinder(radius=8, height=3).translate(Vector(tip_x, tip_y, 0))
    result = result + tip

# 4. Cut features (holes, slots, vents, cavities)
hole = Cylinder(radius=2, height=20).translate(Vector(15, 0, 0))
result = result - hole

# 5. 3D-extruded branding label (optional)
label = extrude(Text("Project", font_size=6), amount=1).translate(Vector(-15, 0, 3))
result = result + label

# 6. END with defensive cast — REQUIRED, do not skip.
#    Without this, the trailing __bd.export_step(result, "out.step")
#    fails with "'ShapeList' object has no attribute 'wrapped'".
result = Part() + result
```

# Make the design DETAILED, not skeletal

A "minimum viable shape" with no surface features looks like a CAD \
exercise, not a product. Every design should have ENOUGH detail to \
read as the real thing in a 3D viewer. After laying out the major \
volumes, add at least 4-6 of the following — pick what fits the \
project:

- **Rounded edges** via `fillet(part.edges(), radius=R)`. Use 1-3 mm \
  fillets on outer corners that a human would touch or see. Major \
  visual upgrade for almost no extra mass.
- **Chamfered openings** via `chamfer(part.edges(), length=L)` on the \
  rim of holes, hatches, lid-meets-body lines.
- **Functional cavities** — subtract Boxes/Cylinders to model the \
  battery bay, electronics compartment, motor housing internals. \
  Don't leave the body solid.
- **Ventilation slots** — a loop of subtracted thin Boxes around the \
  perimeter of an enclosure or motor housing.
- **Wire / cable channels** — small subtracted slots routed between \
  components.
- **Mounting bosses** — short Cylinders extruded inside a cavity for \
  M3 captive nuts or PCB standoffs (radius 3-4 mm, height 4-8 mm).
- **Realistic component stand-ins** — model motors as a Cylinder + \
  smaller Cylinder cap, props as thin elongated Cylinders or Boxes \
  rotated 90° on Y, batteries as a recessed rectangular pocket. \
  Visual placeholders make the design read as the real product.
- **Branding** — `extrude(Text(...), amount=...)` either raised on the \
  surface or recessed (subtract instead of add). Always include if \
  the user named the project.
- **Functional pattern details** — bolt-circle holes around motor \
  flanges, hex grip patterns on knobs, ribs on a payload bay floor, \
  drainage slots on a planter.

Aim for ≥10 distinct geometric features per script (a hub + 4 arms + \
4 motor mounts + 4 motor stubs + payload bay + nameplate is 14 — \
that's the FLOOR, not the ceiling). Prefer one detailed script over \
the simplest possible script — the user wants to see their product, \
not a stick figure.

# Build123d additional ops for detail

```python
# Round edges of a PRIMITIVE before composing — apply fillet to the
# Box/Cylinder while it is still simple. Filleting the final composite
# (after subtracts and unions) often fails with
# `OCP_NotDone: BRep_API: command not done`.
plate = Box(120, 80, 50)
plate = fillet(plate.edges().filter_by(Axis.Z), radius=3)  # round only the vertical edges
result = Part() + plate

# Subtract cavities, add bosses, etc. AFTER the primitive is filleted
cavity = Box(112, 72, 46).translate(Vector(0, 0, 1))
result = result - cavity

# Mounting boss inside a cavity (cylinder + counterbore for the bolt head)
boss = Cylinder(radius=4, height=8).translate(Vector(20, 20, 5))
result = result + boss
counterbore = Cylinder(radius=2, height=10).translate(Vector(20, 20, 3))
result = result - counterbore

# Ventilation slot ring (loop of thin subtracted boxes around an enclosure)
for i in range(8):
    angle = i * 45
    slot = Box(2, 12, 6).translate(Vector(35, 0, 10)).rotate(Axis.Z, angle)
    result = result - slot

# Chamfer also works on primitive edges:
edge_part = Cylinder(radius=10, height=20)
edge_part = chamfer(edge_part.edges(), length=1)  # bevel both rims
```

Rule of thumb: **fillet/chamfer the simple shapes, not the composite**. \
Pattern is: build primitive → fillet/chamfer it → fold into `result`.

# Curve operations — REQUIRED for non-rectilinear shapes

If the project has anything curved (vase, planter, fan housing, \
fairing, blade, organic shell), don't approximate with boxes — use \
build123d's curve operators. All four below are verified working \
end-to-end in cad/'s sandbox.

## Revolve — bowl, vase, planter, fan housing, anything axisymmetric

```python
from build123d import *

# Define a 2D side profile in XZ plane (closed polyline)
with BuildSketch(Plane.XZ) as profile:
    with BuildLine() as ln:
        Polyline(
            (0, 0), (40, 0), (45, 5), (50, 20), (45, 50),
            (35, 80), (38, 90), (38, 95), (0, 95), close=True,
        )
    make_face()

# Spin around Z axis to make a 3D solid of revolution
shell = revolve(profile.sketch, axis=Axis.Z)
result = Part() + shell

# Then subtract cavities, add features, etc. as normal
```

## Loft — smooth transition between profiles (fairings, tapered shells)

```python
from build123d import *

# Two profiles at different heights/sizes
with BuildSketch(Plane.XY) as bottom:
    Circle(radius=30)
with BuildSketch(Plane.XY.offset(50)) as top:
    Circle(radius=15)

# Smoothly transition between them
fairing = loft([bottom.sketch, top.sketch])
result = Part() + fairing
```

Loft accepts any sketches — Circle, Rectangle, Polyline-derived
shapes — as long as the profiles are compatible.

## Sweep — drag a cross-section along a path (curved arms, ducting)

```python
from build123d import *

# Path: a curved line in any plane
with BuildLine(Plane.XZ) as path:
    Spline(((0, 0), (25, 40), (50, 30)))

# Cross-section: any 2D shape (placed perpendicular to path start)
with BuildSketch(Plane.YZ) as section:
    Circle(radius=5)

curved_arm = sweep(section.sketch, path.line)
result = Part() + curved_arm
```

## Combo example — smooth fan housing with vents (verified, 274 KB STEP)

```python
from build123d import *

with BuildSketch(Plane.XZ) as profile:
    with BuildLine():
        Polyline(
            (0, 0), (40, 0), (50, 10), (55, 30), (52, 60),
            (40, 75), (0, 75), close=True,
        )
    make_face()
shell = revolve(profile.sketch, axis=Axis.Z)
result = Part() + shell

# Center cavity for the motor
result = result - Cylinder(radius=30, height=70).translate(Vector(0, 0, 5))

# 12 ventilation slots around the perimeter
for i in range(12):
    angle = i * 30
    slot = Box(4, 18, 8).translate(Vector(45, 0, 65)).rotate(Axis.Z, angle)
    result = result - slot

result = Part() + result
```

**When to reach for curves vs boxes:** if the project name contains
"fan / vase / planter / pot / shell / fairing / blade / cone / nozzle"
or the user describes anything curved or organic, USE revolve / loft /
sweep first. Do not approximate with boxes — boxes are for rectilinear
parts (enclosures, brackets, plates, frames).

# Decomposition heuristics by project type

- **Enclosure** = outer shell (`Box`) − inner cavity (`Box`, smaller, translated up by wall thickness) ± mounting bosses ± vents ± lid features.
- **Frame / chassis with arms** = central hub (`Cylinder` or `Box`) + N radial arms (`Box`, translated +X by length/2, rotated by `i * 360/N`). End-of-arm features go inside the same loop.
- **Vessel / planter / pot** = outer cylinder − inner cylinder (smaller radius, translated up by base thickness). Add ribs/grips as extra Boxes around the outside.
- **Plate with hole pattern** = `Box` − loop of `Cylinder`s at computed (x, y) offsets.
- **Multi-stage / segmented** (gripper, rocker, telescope) = build each segment separately, translate to its position, fold into `result` one at a time.

HARD RULES (non-negotiable):
- DO NOT ask the user clarifying questions. The user has already left the room. They cannot answer.
- Default to `generate_from_script`. The three parametric primitives are not enough for almost any real project.
- Pass `timeout_s=180` on every `generate_from_script` call — composite assemblies take >60s after build123d cold-import.
- Build geometry by accumulating `result = result + part` ONE AT A TIME. Start with `result = Part() + <first>` and END with `result = Part() + result` (the defensive cast that prevents the ShapeList export failure).
- Use only the API in the cheat sheet. Do NOT use `Cone`, `Angle`, `Vector(x=, y=, z=)`. If you reach for an API not in the cheat sheet, it almost certainly doesn't exist.
- Pick ONE final part. The trailing JSON has one `mechanical_part` object, not a list.
- If a script errors, READ THE STDERR. The error names the exact line and the exact API misuse. Fix THAT SPECIFIC LINE — do NOT strip other features. If a fillet on edge X fails, change the fillet edge selection or radius; keep the cavity, the ventilation slots, the bosses, the branding text intact. A simplified retry that drops 80% of the design is worse than no retry — the user gets a "cube" instead of their product. The size_bytes of a real product script should be ≥ 200 KB; if your retry produces under 100 KB you've stripped too much.
- The `rationale` JSON field MUST describe ONLY what is in the STEP that succeeded, not the original plan. If the script's first attempt had 14 features but the retry has 6, the rationale lists those 6. Never let the rationale promise more than the geometry delivers — downstream consumers (BoM, viewer caption, sourcing agent) trust this field.
- Failing to call generate_from_script (or generate_part for the rare primitive-fit case) is a failure.

Process:
1. Decide if a parametric primitive (`enclosure_box`, `mounting_plate`, \
   `bracket_l`) is the project's whole shape — usually no.
2. Otherwise sketch the decomposition: which primitives, in what \
   order, with which booleans? Match it to the heuristics above.
3. Write the build123d script. Call `generate_from_script(code=..., \
   timeout_s=180)` for non-trivial assemblies.
4. End your turn with a compact JSON summary:
   {
     "mechanical_part": {
       "template": null,                  // or template name if you used a primitive
       "inputs": {},                       // or template inputs
       "from_script": true,                // true for generate_from_script, false for primitives
       "size_bytes": 12345,
       "rationale": "what the geometry IS as a description of shapes, not what it represents — e.g. 'cylindrical 80mm hub with 4 radial 180x15x8mm arms and end pads at 90° spacing'"
     }
   }
   No prose after the JSON.
"""


ELECTRONICS_RESEARCH_SYSTEM = """You are the Cassen electronics researcher.

You have tools backed by live distributor APIs (Digi-Key, Nexar/Octopart, \
Mouser). Use them to ground every electronic component choice in a real, \
available MPN. Tool results carry a `source` field so you can see which \
distributor produced each row, plus an `attempts` array showing the chain.

HARD RULES (non-negotiable):
- DO NOT ask the user clarifying questions. The user has already left the \
  room. They cannot answer.
- DO NOT stall waiting for confirmation. Make reasonable assumptions and \
  proceed.
- State your assumptions in 2-4 bullets at the top of your response, then \
  IMMEDIATELY start calling tools.
- Failing to call any tool is a failure. You MUST end with the trailing \
  JSON object below, populated from real tool results.

Process:
1. State your assumptions briefly (e.g. "Assuming quadcopter, 4S LiPo, \
   ~$600 budget, autonomous + manual fallback").
2. Identify the electronic functions the project needs (MCU, sensors, power, \
   communication, drivers/actuators) — typically 5-8 functions.
3. For each function, call search_part to discover candidates, then get_part \
   for top picks. Use recommend_alternative when the obvious first choice has \
   tradeoffs worth mentioning.
4. Pick one MPN per function. Note tradeoffs in one sentence.
5. End your turn with a compact JSON object summarizing your picks:
   {
     "candidate_parts": [
       { "function": "...", "mpn": "...", "rationale": "..." },
       ...
     ]
   }
   No prose after the JSON.

Do not invent MPNs — only return ones that came back from a tool. If a \
search returns no rows, rephrase and retry once before settling for a \
closest match. Three to seven calls total is typical — don't over-research.
"""


DESIGN_DOMAINS = {"electronics", "mechanical", "fluids"}


def _domains_from_plan(plan_parsed: dict | None) -> set[str]:
    if not plan_parsed:
        return set()
    raw = plan_parsed.get("domains") or []
    if not isinstance(raw, list):
        return set()
    return {str(d).strip().lower() for d in raw} & DESIGN_DOMAINS


def _extract_trailing_json(text: str) -> dict | None:
    """Pull the last balanced {...} block from `text` and json.loads it.

    Returns None if there is no balanced block or it doesn't parse.
    """
    if not text:
        return None
    end = text.rfind("}")
    if end == -1:
        return None
    depth = 0
    start = -1
    for i in range(end, -1, -1):
        ch = text[i]
        if ch == "}":
            depth += 1
        elif ch == "{":
            depth -= 1
            if depth == 0:
                start = i
                break
    if start == -1:
        return None
    blob = text[start : end + 1]
    try:
        parsed = json.loads(blob)
    except Exception:  # noqa: BLE001
        return None
    return parsed if isinstance(parsed, dict) else None


def _extract_bom(text: str) -> list[dict[str, Any]]:
    """Pull the designer's `bom` JSON list from its trailing summary.

    Returns [] when no parseable block is present — caller falls back
    to deriving a BoM from the research outputs directly.
    """
    parsed = _extract_trailing_json(text)
    if not parsed:
        return []
    raw = parsed.get("bom")
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for row in raw:
        if not isinstance(row, dict) or not row.get("id"):
            continue
        out.append(
            {
                "domain": str(row.get("domain", "")),
                "id": str(row.get("id", "")),
                "function": str(row.get("function", "")),
                "rationale": str(row.get("rationale", "")),
            }
        )
    return out


def _bom_from_research(research_outputs: dict[str, Any]) -> list[dict[str, Any]]:
    """Deterministic fallback BoM built straight from research_outputs.

    Used when the designer's trailing JSON is missing/malformed, or as
    the truth source the smoke can verify regardless of LLM behavior.
    Order: electronics, mechanical hardware, CAD geometry, fluids.
    """
    out: list[dict[str, Any]] = []

    elec = research_outputs.get("electronics") or {}
    for p in elec.get("candidate_parts") or []:
        if not isinstance(p, dict) or not p.get("mpn"):
            continue
        out.append(
            {
                "domain": "electronics",
                "id": str(p.get("mpn")),
                "function": str(p.get("function", "")),
                "rationale": str(p.get("rationale", "")),
            }
        )

    mech_hw = research_outputs.get("mechanical_research") or {}
    for p in mech_hw.get("picks") or []:
        if not isinstance(p, dict) or not p.get("part_id"):
            continue
        out.append(
            {
                "domain": "mechanical",
                "id": str(p.get("part_id")),
                "function": str(p.get("function", "")),
                "rationale": str(p.get("rationale", "")),
            }
        )

    cad = research_outputs.get("mechanical") or {}
    pick = cad.get("pick") if isinstance(cad, dict) else None
    if isinstance(pick, dict) and (pick.get("template") or pick.get("from_script")):
        cad_id = (
            f"build123d-script:{cad.get('step_b64','')[:8]}"
            if pick.get("from_script")
            else str(pick.get("template"))
        )
        out.append(
            {
                "domain": "cad",
                "id": cad_id,
                "function": "mechanical geometry (STEP produced)",
                "rationale": str(pick.get("rationale", "")),
            }
        )

    fluids = research_outputs.get("fluids") or {}
    for p in fluids.get("picks") or []:
        if not isinstance(p, dict) or not p.get("part_id"):
            continue
        out.append(
            {
                "domain": "fluids",
                "id": str(p.get("part_id")),
                "function": str(p.get("function", "")),
                "rationale": str(p.get("rationale", "")),
            }
        )

    return out


def _extract_fluid_picks(text: str) -> list[dict[str, Any]]:
    """Pull `fluid_picks` JSON list from the researcher's free-form output."""
    parsed = _extract_trailing_json(text)
    if not parsed:
        return []
    raw = parsed.get("fluid_picks")
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for p in raw:
        if isinstance(p, dict) and p.get("part_id"):
            out.append(
                {
                    "function": str(p.get("function", "")),
                    "part_id": str(p.get("part_id", "")),
                    "rationale": str(p.get("rationale", "")),
                }
            )
    return out


def _extract_mechanical_picks(text: str) -> list[dict[str, Any]]:
    """Pull `mechanical_picks` JSON list from the researcher's free-form output."""
    parsed = _extract_trailing_json(text)
    if not parsed:
        return []
    raw = parsed.get("mechanical_picks")
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for p in raw:
        if isinstance(p, dict) and p.get("part_id"):
            out.append(
                {
                    "function": str(p.get("function", "")),
                    "part_id": str(p.get("part_id", "")),
                    "rationale": str(p.get("rationale", "")),
                }
            )
    return out


def _extract_mechanical_pick(text: str) -> dict[str, Any] | None:
    parsed = _extract_trailing_json(text)
    if not parsed:
        return None
    pick = parsed.get("mechanical_part")
    if not isinstance(pick, dict):
        return None
    return {
        "template": pick.get("template"),
        "inputs": pick.get("inputs") if isinstance(pick.get("inputs"), dict) else {},
        "from_script": bool(pick.get("from_script", False)),
        "size_bytes": int(pick.get("size_bytes") or 0),
        "rationale": str(pick.get("rationale", "")),
    }


def _redact_step_b64(call: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of a tool-call record with `step_b64` replaced by a
    size hint, so SSE frames and snapshots don't bloat with binary blobs.
    The full bytes are captured separately on `research_outputs.mechanical.step_b64`.
    """
    out = dict(call)
    text = out.get("output_text") or ""
    if not text or "step_b64" not in text:
        return out
    try:
        parsed = json.loads(text)
    except Exception:  # noqa: BLE001
        return out
    if isinstance(parsed, dict) and isinstance(parsed.get("step_b64"), str):
        n = len(parsed["step_b64"])
        parsed["step_b64"] = f"<redacted {n} chars>"
        out["output_text"] = json.dumps(parsed)
    return out


def _last_step_b64_from_calls(calls: list[dict[str, Any]]) -> str | None:
    """Return the most recent step_b64 produced by a generate_* tool call.

    The tool result is JSON-as-text; parse and pull `step_b64` if present.
    """
    for call in reversed(calls):
        name = call.get("name", "")
        if name not in {"generate_part", "generate_from_script"}:
            continue
        text = call.get("output_text") or ""
        try:
            parsed = json.loads(text)
        except Exception:  # noqa: BLE001
            continue
        b64 = parsed.get("step_b64")
        if isinstance(b64, str) and b64:
            return b64
    return None


def _step_b64_for_pick(
    calls: list[dict[str, Any]],
    pick: dict[str, Any] | None,
) -> str | None:
    """Find the step_b64 from the call that matches the model's declared pick.

    Models often explore multiple templates before settling — e.g. they
    call generate_part(bracket_l), then generate_part(mounting_plate),
    then write JSON saying their pick is bracket_l. _last_step_b64...
    would return the mounting_plate STEP, mismatching the JSON. This
    helper looks up the call whose `input.template` matches the pick's
    declared template, so the rendered GLB is the one the agent claims
    to have chosen.

    Falls back to the last step_b64 if no match (custom script picks,
    template name typos, missing pick metadata).
    """
    if not isinstance(pick, dict):
        return _last_step_b64_from_calls(calls)
    if pick.get("from_script"):
        # Script picks don't have a template name to match on.
        return _last_step_b64_from_calls(calls)
    target_template = pick.get("template")
    if not isinstance(target_template, str) or not target_template:
        return _last_step_b64_from_calls(calls)

    for call in reversed(calls):
        if call.get("name") != "generate_part":
            continue
        input_data = call.get("input")
        if not isinstance(input_data, dict):
            continue
        if input_data.get("template") != target_template:
            continue
        text = call.get("output_text") or ""
        try:
            parsed = json.loads(text)
        except Exception:  # noqa: BLE001
            continue
        b64 = parsed.get("step_b64")
        if isinstance(b64, str) and b64:
            return b64

    # No matching call — model named a template it never actually
    # generated. Fall back to whatever STEP we do have so the viewer
    # at least shows something (the model's narrative will be off,
    # but the geometry is still valid).
    return _last_step_b64_from_calls(calls)


def _extract_candidate_parts(text: str) -> list[dict[str, Any]]:
    """Pull `candidate_parts` JSON from the researcher's free-form output.

    The researcher's system prompt asks for a trailing JSON block; we
    locate the last balanced {...} in the text and try to parse it. Best
    effort — a malformed block returns an empty list and the markdown is
    still stored in research.final_text.
    """
    if not text:
        return []
    end = text.rfind("}")
    if end == -1:
        return []
    depth = 0
    start = -1
    for i in range(end, -1, -1):
        ch = text[i]
        if ch == "}":
            depth += 1
        elif ch == "{":
            depth -= 1
            if depth == 0:
                start = i
                break
    if start == -1:
        return []
    blob = text[start : end + 1]
    try:
        parsed = json.loads(blob)
    except Exception:  # noqa: BLE001
        return []
    if not isinstance(parsed, dict):
        return []
    parts = parsed.get("candidate_parts")
    if not isinstance(parts, list):
        return []
    out: list[dict[str, Any]] = []
    for p in parts:
        if isinstance(p, dict) and p.get("mpn"):
            out.append(
                {
                    "function": str(p.get("function", "")),
                    "mpn": str(p.get("mpn", "")),
                    "rationale": str(p.get("rationale", "")),
                }
            )
    return out


def _build_langfuse() -> Langfuse | None:
    s = get_settings()
    if not (s.langfuse_public_key and s.langfuse_secret_key):
        return None
    return Langfuse(
        public_key=s.langfuse_public_key,
        secret_key=s.langfuse_secret_key,
        host=s.langfuse_host,
    )


def _maybe_propagate(langfuse: Langfuse | None, **attrs: Any):
    if langfuse is None:
        return nullcontext()
    return propagate_attributes(**attrs)


def _maybe_span(
    langfuse: Langfuse | None,
    *,
    name: str,
    as_type: str = "span",
    **kw: Any,
):
    if langfuse is None:
        return nullcontext(None)
    return langfuse.start_as_current_observation(name=name, as_type=as_type, **kw)


async def _stream_text(
    client: AsyncAnthropic,
    *,
    system: str,
    prompt: str,
    model: str,
    max_tokens: int,
) -> AsyncIterator[tuple[str, str]]:
    """Yield ("token", chunk) for each delta. Final yield: ("full", complete_text)."""
    full: list[str] = []
    async with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        async for text in stream.text_stream:
            full.append(text)
            yield ("token", text)
    yield ("full", "".join(full))


async def run_graph(input: GraphInput) -> AsyncIterator[GraphEvent]:
    settings = get_settings()
    # Tier 1 ITPM caps (30K/min on Sonnet 4.6) bite a multi-node run
    # — planner -> 4 research nodes -> designer in sequence will blow
    # through the rolling-window budget mid-run. SDK default
    # max_retries=2 isn't enough: token-bucket recovery needs ~60s,
    # so we want the SDK to honor `retry-after` for several cycles
    # before giving up. 8 retries with the SDK's exponential backoff +
    # retry-after handling typically rides out a single bucket-empty
    # event without surfacing a 429. Independent of caching — cache
    # reads count against ITPM at full rate, so caching cuts cost not
    # rate-limit pressure.
    client = AsyncAnthropic(
        api_key=settings.anthropic_api_key,
        max_retries=8,
    )
    langfuse = _build_langfuse()

    try:
        with _maybe_propagate(
            langfuse,
            user_id=input.owner_id,
            metadata={"project_id": input.project_id},
            trace_name="project.run",
        ):
            with _maybe_span(
                langfuse,
                name="project.run",
                as_type="span",
                input={"prompt": input.prompt},
            ) as root_span:
                # ---- planner ----------------------------------------------
                update_project_status(input.project_id, "planning")
                yield GraphEvent(kind="status", data={"status": "planning"})
                yield GraphEvent(kind="node-start", node="planner")

                plan_text_parts: list[str] = []
                plan_parsed: dict | None = None
                with _maybe_span(
                    langfuse,
                    name="planner",
                    as_type="generation",
                    input={"prompt": input.prompt},
                    model=settings.primary_model,
                    model_parameters={"max_tokens": settings.planner_max_tokens},
                ) as plan_span:
                    async for kind, chunk in _stream_text(
                        client,
                        system=PLANNER_SYSTEM,
                        prompt=input.prompt,
                        model=settings.primary_model,
                        max_tokens=settings.planner_max_tokens,
                    ):
                        if kind == "token":
                            plan_text_parts.append(chunk)
                            yield GraphEvent(kind="token", node="planner", data=chunk)
                        elif kind == "full":
                            plan_text = chunk
                            # Claude often wraps the JSON in a ```json ... ```
                            # fence even when told not to. _extract_trailing_json
                            # walks back from the last `}` to a balanced `{`,
                            # which finds the JSON regardless of fences or
                            # surrounding prose.
                            plan_parsed = _extract_trailing_json(plan_text)
                            yield GraphEvent(
                                kind="node-end",
                                node="planner",
                                data={"text": plan_text, "parsed": plan_parsed},
                            )
                            if plan_span is not None:
                                plan_span.update(
                                    output={"text": plan_text, "parsed": plan_parsed},
                                )

                # ---- electronics research (conditional) -------------------
                domains = _domains_from_plan(plan_parsed)
                research_outputs: dict[str, dict[str, Any]] = {}

                if "electronics" in domains and settings.mcp_electronics_path:
                    update_project_status(input.project_id, "researching")
                    yield GraphEvent(kind="status", data={"status": "researching"})
                    yield GraphEvent(kind="node-start", node="electronics_research")

                    research_user = (
                        "Project request:\n"
                        f"{input.prompt}\n\n"
                        f"Planner decomposition (JSON):\n{''.join(plan_text_parts)}\n"
                    )

                    research_calls: list[dict[str, Any]] = []
                    research_text_parts: list[str] = []

                    with _maybe_span(
                        langfuse,
                        name="electronics_research",
                        as_type="generation",
                        input={"prompt": input.prompt},
                        model=settings.research_model,
                        model_parameters={
                            "max_tokens": settings.research_max_tokens,
                            "max_iterations": settings.research_max_iterations,
                        },
                    ) as research_span:
                        try:
                            async with mcp_session(
                                command=settings.uv_command,
                                args=[
                                    "run",
                                    "--project",
                                    settings.mcp_electronics_path,
                                    "python",
                                    "-m",
                                    "cassen_electronics.server",
                                ],
                                # pydantic-settings resolves env_file relative
                                # to CWD; without cwd= the subprocess inherits
                                # agent/'s CWD and never reads
                                # mcp-electronics/.env (where distributor keys
                                # live). Same fix applied to every MCP spawn.
                                cwd=settings.mcp_electronics_path,
                            ) as session:
                                async for event_kind, payload in run_tool_using_loop(
                                    client=client,
                                    session=session,
                                    system=ELECTRONICS_RESEARCH_SYSTEM,
                                    user_prompt=research_user,
                                    model=settings.research_model,
                                    max_tokens=settings.research_max_tokens,
                                    max_iterations=settings.research_max_iterations,
                                ):
                                    if event_kind == "iteration":
                                        yield GraphEvent(
                                            kind="iteration",
                                            node="electronics_research",
                                            data=payload,
                                        )
                                    elif event_kind == "assistant-text":
                                        research_text_parts.append(payload["text"])
                                        yield GraphEvent(
                                            kind="token",
                                            node="electronics_research",
                                            data=payload["text"],
                                        )
                                    elif event_kind == "tool-call-start":
                                        yield GraphEvent(
                                            kind="tool-call-start",
                                            node="electronics_research",
                                            data=payload,
                                        )
                                    elif event_kind == "tool-call-end":
                                        research_calls.append(payload)
                                        yield GraphEvent(
                                            kind="tool-call-end",
                                            node="electronics_research",
                                            data=payload,
                                        )
                                    elif event_kind == "tool-error":
                                        yield GraphEvent(
                                            kind="tool-error",
                                            node="electronics_research",
                                            data=payload,
                                        )
                                    elif event_kind == "done":
                                        final_text = payload.get("final_text", "")
                                        candidates = _extract_candidate_parts(final_text)
                                        research_outputs["electronics"] = {
                                            "final_text": final_text,
                                            "candidate_parts": candidates,
                                            "calls": research_calls,
                                            "stop_reason": payload.get("stop_reason"),
                                        }
                                        yield GraphEvent(
                                            kind="node-end",
                                            node="electronics_research",
                                            data={
                                                "text": final_text,
                                                "candidate_parts": candidates,
                                                "calls_made": len(research_calls),
                                            },
                                        )
                                        if research_span is not None:
                                            research_span.update(
                                                output={
                                                    "candidate_parts": candidates,
                                                    "calls_made": len(research_calls),
                                                },
                                            )
                        except Exception as exc:  # noqa: BLE001
                            yield GraphEvent(
                                kind="tool-error",
                                node="electronics_research",
                                data={"error": str(exc)},
                            )
                            research_outputs["electronics"] = {
                                "error": str(exc),
                                "calls": research_calls,
                            }

                # ---- mechanical research (conditional) -------------------
                # Picks fasteners/bearings/extrusion from the curated
                # catalog before CAD generation, so mechanical_design
                # can size geometry against real part dimensions.
                if "mechanical" in domains and settings.mcp_mechanical_path:
                    # DB schema's projects_status_chk only allows the
                    # coarse-grained set (draft/planning/researching/
                    # designing/...). The fine-grained "phase" lives in
                    # the SSE event below for UI display.
                    update_project_status(input.project_id, "researching")
                    yield GraphEvent(
                        kind="status", data={"status": "researching-mechanical"}
                    )
                    yield GraphEvent(kind="node-start", node="mechanical_research")

                    mech_research_user = (
                        "Project request:\n"
                        f"{input.prompt}\n\n"
                        f"Planner decomposition (JSON):\n{''.join(plan_text_parts)}\n"
                    )
                    mech_research_calls: list[dict[str, Any]] = []
                    mech_research_text_parts: list[str] = []

                    with _maybe_span(
                        langfuse,
                        name="mechanical_research",
                        as_type="generation",
                        input={"prompt": input.prompt},
                        model=settings.research_model,
                        model_parameters={
                            "max_tokens": settings.research_max_tokens,
                            "max_iterations": settings.research_max_iterations,
                        },
                    ) as mech_research_span:
                        try:
                            async with mcp_session(
                                command=settings.uv_command,
                                args=[
                                    "run",
                                    "--project",
                                    settings.mcp_mechanical_path,
                                    "python",
                                    "-m",
                                    "cassen_mechanical.server",
                                ],
                                cwd=settings.mcp_mechanical_path,
                            ) as session:
                                async for event_kind, payload in run_tool_using_loop(
                                    client=client,
                                    session=session,
                                    system=MECHANICAL_RESEARCH_SYSTEM,
                                    user_prompt=mech_research_user,
                                    model=settings.research_model,
                                    max_tokens=settings.research_max_tokens,
                                    max_iterations=settings.research_max_iterations,
                                ):
                                    if event_kind == "iteration":
                                        yield GraphEvent(
                                            kind="iteration",
                                            node="mechanical_research",
                                            data=payload,
                                        )
                                    elif event_kind == "assistant-text":
                                        mech_research_text_parts.append(payload["text"])
                                        yield GraphEvent(
                                            kind="token",
                                            node="mechanical_research",
                                            data=payload["text"],
                                        )
                                    elif event_kind == "tool-call-start":
                                        yield GraphEvent(
                                            kind="tool-call-start",
                                            node="mechanical_research",
                                            data=payload,
                                        )
                                    elif event_kind == "tool-call-end":
                                        mech_research_calls.append(payload)
                                        yield GraphEvent(
                                            kind="tool-call-end",
                                            node="mechanical_research",
                                            data=payload,
                                        )
                                    elif event_kind == "tool-error":
                                        yield GraphEvent(
                                            kind="tool-error",
                                            node="mechanical_research",
                                            data=payload,
                                        )
                                    elif event_kind == "done":
                                        final_text = payload.get("final_text", "")
                                        picks = _extract_mechanical_picks(final_text)
                                        research_outputs["mechanical_research"] = {
                                            "final_text": final_text,
                                            "picks": picks,
                                            "calls": mech_research_calls,
                                            "stop_reason": payload.get("stop_reason"),
                                        }
                                        yield GraphEvent(
                                            kind="node-end",
                                            node="mechanical_research",
                                            data={
                                                "text": final_text,
                                                "picks": picks,
                                                "calls_made": len(mech_research_calls),
                                            },
                                        )
                                        if mech_research_span is not None:
                                            mech_research_span.update(
                                                output={
                                                    "picks": picks,
                                                    "calls_made": len(mech_research_calls),
                                                },
                                            )
                        except Exception as exc:  # noqa: BLE001
                            yield GraphEvent(
                                kind="tool-error",
                                node="mechanical_research",
                                data={"error": str(exc)},
                            )
                            research_outputs["mechanical_research"] = {
                                "error": str(exc),
                                "calls": mech_research_calls,
                            }

                # ---- mechanical design (conditional) ---------------------
                if "mechanical" in domains and settings.mcp_cad_path:
                    update_project_status(input.project_id, "designing")
                    yield GraphEvent(
                        kind="status", data={"status": "designing-mechanical"}
                    )
                    yield GraphEvent(kind="node-start", node="mechanical_design")

                    elec = research_outputs.get("electronics") or {}
                    elec_summary = elec.get("final_text", "") if isinstance(elec, dict) else ""

                    mech_research = research_outputs.get("mechanical_research") or {}
                    mech_research_summary = (
                        mech_research.get("final_text", "")
                        if isinstance(mech_research, dict)
                        else ""
                    )

                    mech_user = (
                        "Project request:\n"
                        f"{input.prompt}\n\n"
                        f"Planner decomposition (JSON):\n{''.join(plan_text_parts)}\n"
                        + (
                            f"\nElectronics picks (size enclosure to fit):\n{elec_summary}\n"
                            if elec_summary
                            else ""
                        )
                        + (
                            "\nMechanical hardware picks (account for these dims):\n"
                            f"{mech_research_summary}\n"
                            if mech_research_summary
                            else ""
                        )
                    )

                    mech_calls: list[dict[str, Any]] = []
                    mech_text_parts: list[str] = []

                    with _maybe_span(
                        langfuse,
                        name="mechanical_design",
                        as_type="generation",
                        input={"prompt": input.prompt},
                        model=settings.research_model,
                        model_parameters={
                            "max_tokens": settings.research_max_tokens,
                            "max_iterations": settings.research_max_iterations,
                        },
                    ) as mech_span:
                        try:
                            async with mcp_session(
                                command=settings.uv_command,
                                args=[
                                    "run",
                                    "--project",
                                    settings.mcp_cad_path,
                                    "python",
                                    "-m",
                                    "cassen_cad_mcp.server",
                                ],
                                cwd=settings.mcp_cad_path,
                            ) as session:
                                async for event_kind, payload in run_tool_using_loop(
                                    client=client,
                                    session=session,
                                    system=MECHANICAL_DESIGN_SYSTEM,
                                    user_prompt=mech_user,
                                    model=settings.research_model,
                                    max_tokens=settings.research_max_tokens,
                                    max_iterations=settings.research_max_iterations,
                                ):
                                    if event_kind == "iteration":
                                        yield GraphEvent(
                                            kind="iteration",
                                            node="mechanical_design",
                                            data=payload,
                                        )
                                    elif event_kind == "assistant-text":
                                        mech_text_parts.append(payload["text"])
                                        yield GraphEvent(
                                            kind="token",
                                            node="mechanical_design",
                                            data=payload["text"],
                                        )
                                    elif event_kind == "tool-call-start":
                                        yield GraphEvent(
                                            kind="tool-call-start",
                                            node="mechanical_design",
                                            data=payload,
                                        )
                                    elif event_kind == "tool-call-end":
                                        # Strip step_b64 from the streamed event
                                        # so the SSE channel doesn't carry tens
                                        # of KB per call. We still capture the
                                        # full record in `mech_calls` for the
                                        # snapshot.
                                        mech_calls.append(payload)
                                        public = _redact_step_b64(payload)
                                        yield GraphEvent(
                                            kind="tool-call-end",
                                            node="mechanical_design",
                                            data=public,
                                        )
                                    elif event_kind == "tool-error":
                                        yield GraphEvent(
                                            kind="tool-error",
                                            node="mechanical_design",
                                            data=payload,
                                        )
                                    elif event_kind == "done":
                                        final_text = payload.get("final_text", "")
                                        pick = _extract_mechanical_pick(final_text)
                                        last_b64 = _step_b64_for_pick(mech_calls, pick)
                                        research_outputs["mechanical"] = {
                                            "final_text": final_text,
                                            "pick": pick,
                                            "calls": [
                                                _redact_step_b64(c) for c in mech_calls
                                            ],
                                            "step_b64": last_b64,
                                            "stop_reason": payload.get("stop_reason"),
                                        }
                                        yield GraphEvent(
                                            kind="node-end",
                                            node="mechanical_design",
                                            data={
                                                "text": final_text,
                                                "pick": pick,
                                                "calls_made": len(mech_calls),
                                                "step_size_bytes": (
                                                    len(last_b64) * 3 // 4 if last_b64 else 0
                                                ),
                                            },
                                        )
                                        if mech_span is not None:
                                            mech_span.update(
                                                output={
                                                    "pick": pick,
                                                    "calls_made": len(mech_calls),
                                                },
                                            )
                        except Exception as exc:  # noqa: BLE001
                            yield GraphEvent(
                                kind="tool-error",
                                node="mechanical_design",
                                data={"error": str(exc)},
                            )
                            research_outputs["mechanical"] = {
                                "error": str(exc),
                                "calls": [_redact_step_b64(c) for c in mech_calls],
                            }

                # ---- fluids research (conditional) -----------------------
                if "fluids" in domains and settings.mcp_fluids_path:
                    update_project_status(input.project_id, "researching")
                    yield GraphEvent(
                        kind="status", data={"status": "researching-fluids"}
                    )
                    yield GraphEvent(kind="node-start", node="fluids_research")

                    fluids_user = (
                        "Project request:\n"
                        f"{input.prompt}\n\n"
                        f"Planner decomposition (JSON):\n{''.join(plan_text_parts)}\n"
                    )
                    fluids_calls: list[dict[str, Any]] = []
                    fluids_text_parts: list[str] = []

                    with _maybe_span(
                        langfuse,
                        name="fluids_research",
                        as_type="generation",
                        input={"prompt": input.prompt},
                        model=settings.research_model,
                        model_parameters={
                            "max_tokens": settings.research_max_tokens,
                            "max_iterations": settings.research_max_iterations,
                        },
                    ) as fluids_span:
                        try:
                            async with mcp_session(
                                command=settings.uv_command,
                                args=[
                                    "run",
                                    "--project",
                                    settings.mcp_fluids_path,
                                    "python",
                                    "-m",
                                    "cassen_fluids.server",
                                ],
                                cwd=settings.mcp_fluids_path,
                            ) as session:
                                async for event_kind, payload in run_tool_using_loop(
                                    client=client,
                                    session=session,
                                    system=FLUIDS_RESEARCH_SYSTEM,
                                    user_prompt=fluids_user,
                                    model=settings.research_model,
                                    max_tokens=settings.research_max_tokens,
                                    max_iterations=settings.research_max_iterations,
                                ):
                                    if event_kind == "iteration":
                                        yield GraphEvent(
                                            kind="iteration",
                                            node="fluids_research",
                                            data=payload,
                                        )
                                    elif event_kind == "assistant-text":
                                        fluids_text_parts.append(payload["text"])
                                        yield GraphEvent(
                                            kind="token",
                                            node="fluids_research",
                                            data=payload["text"],
                                        )
                                    elif event_kind == "tool-call-start":
                                        yield GraphEvent(
                                            kind="tool-call-start",
                                            node="fluids_research",
                                            data=payload,
                                        )
                                    elif event_kind == "tool-call-end":
                                        fluids_calls.append(payload)
                                        yield GraphEvent(
                                            kind="tool-call-end",
                                            node="fluids_research",
                                            data=payload,
                                        )
                                    elif event_kind == "tool-error":
                                        yield GraphEvent(
                                            kind="tool-error",
                                            node="fluids_research",
                                            data=payload,
                                        )
                                    elif event_kind == "done":
                                        final_text = payload.get("final_text", "")
                                        picks = _extract_fluid_picks(final_text)
                                        research_outputs["fluids"] = {
                                            "final_text": final_text,
                                            "picks": picks,
                                            "calls": fluids_calls,
                                            "stop_reason": payload.get("stop_reason"),
                                        }
                                        yield GraphEvent(
                                            kind="node-end",
                                            node="fluids_research",
                                            data={
                                                "text": final_text,
                                                "picks": picks,
                                                "calls_made": len(fluids_calls),
                                            },
                                        )
                                        if fluids_span is not None:
                                            fluids_span.update(
                                                output={
                                                    "picks": picks,
                                                    "calls_made": len(fluids_calls),
                                                },
                                            )
                        except Exception as exc:  # noqa: BLE001
                            yield GraphEvent(
                                kind="tool-error",
                                node="fluids_research",
                                data={"error": str(exc)},
                            )
                            research_outputs["fluids"] = {
                                "error": str(exc),
                                "calls": fluids_calls,
                            }

                # ---- designer ---------------------------------------------
                update_project_status(input.project_id, "designing")
                yield GraphEvent(kind="status", data={"status": "designing"})
                yield GraphEvent(kind="node-start", node="designer")

                # Build the research block. Only inject FINDINGS when a node
                # produced structured picks; if a node ran but produced
                # nothing (e.g. asked clarifying questions instead of
                # calling tools), inject a FAILURE marker so the designer
                # doesn't read prose research and fabricate identifiers
                # to fill the void.
                research_block = ""
                electronics_research = research_outputs.get("electronics")
                if electronics_research and electronics_research.get("candidate_parts"):
                    research_block += "\nElectronics picks (grounded by live distributors):\n"
                    for p in electronics_research["candidate_parts"]:
                        research_block += (
                            f"- {p.get('mpn')}: {p.get('function')}"
                            f" — {p.get('rationale','')}\n"
                        )
                elif "electronics" in domains:
                    research_block += (
                        "\nElectronics research: NO_GROUNDED_PARTS. The "
                        "researcher returned no MPNs. Mark every electronic "
                        "line item in the BoM as id=\"NO_GROUNDED_MPN\" — "
                        "do NOT invent MPNs.\n"
                    )

                mechanical_hw = research_outputs.get("mechanical_research")
                if mechanical_hw and mechanical_hw.get("picks"):
                    research_block += "\nMechanical hardware selections (curated catalog):\n"
                    for p in mechanical_hw["picks"]:
                        research_block += (
                            f"- {p.get('part_id')}: {p.get('function')}"
                            f" — {p.get('rationale','')}\n"
                        )
                elif "mechanical" in domains:
                    research_block += (
                        "\nMechanical hardware research: NO_GROUNDED_PARTS. "
                        "Mark every mechanical hardware line item as "
                        "id=\"NO_GROUNDED_PART\" — do NOT invent part_ids.\n"
                    )

                fluids_research = research_outputs.get("fluids")
                if fluids_research and fluids_research.get("picks"):
                    research_block += "\nFluid-system selections (curated catalog):\n"
                    for p in fluids_research["picks"]:
                        research_block += (
                            f"- {p.get('part_id')}: {p.get('function')}"
                            f" — {p.get('rationale','')}\n"
                        )
                elif "fluids" in domains:
                    research_block += (
                        "\nFluids research: NO_GROUNDED_PARTS. Mark every "
                        "fluid line item as id=\"NO_GROUNDED_PART\".\n"
                    )

                mechanical_design = research_outputs.get("mechanical")
                if mechanical_design and mechanical_design.get("pick"):
                    pick = mechanical_design["pick"]
                    research_block += (
                        "\nMechanical CAD selection (real STEP geometry produced):\n"
                        f"- template: {pick.get('template') or 'custom build123d script'}\n"
                        f"- inputs: {json.dumps(pick.get('inputs') or {})}\n"
                        f"- size: {pick.get('size_bytes')} bytes\n"
                        f"- rationale: {pick.get('rationale','')}\n"
                    )

                designer_input = (
                    "User request:\n"
                    f"{input.prompt}\n\n"
                    f"Planner decomposition:\n{''.join(plan_text_parts)}\n"
                    f"{research_block}"
                )

                design_text_parts: list[str] = []
                with _maybe_span(
                    langfuse,
                    name="designer",
                    as_type="generation",
                    input={
                        "prompt": input.prompt,
                        "planner_output": "".join(plan_text_parts),
                    },
                    model=settings.primary_model,
                    model_parameters={"max_tokens": settings.designer_max_tokens},
                ) as design_span:
                    async for kind, chunk in _stream_text(
                        client,
                        system=DESIGNER_SYSTEM,
                        prompt=designer_input,
                        model=settings.primary_model,
                        max_tokens=settings.designer_max_tokens,
                    ):
                        if kind == "token":
                            design_text_parts.append(chunk)
                            yield GraphEvent(kind="token", node="designer", data=chunk)
                        elif kind == "full":
                            design_text = chunk
                            yield GraphEvent(
                                kind="node-end",
                                node="designer",
                                data={"text": design_text},
                            )
                            if design_span is not None:
                                design_span.update(output={"text": design_text})

                # ---- snapshot + complete ----------------------------------
                # Strip the bulky mechanical step_b64 from the persisted
                # snapshot, but BEFORE stripping, convert it through
                # cad/'s /convert/step-to-gltf so the persisted snapshot
                # carries glb_b64 for the in-browser viewer to render.
                # GLB is what three.js loads; STEP is engineering-CAD-
                # only and unrenderable client-side.
                research_for_snapshot = {**research_outputs}
                if "mechanical" in research_for_snapshot:
                    mech = dict(research_for_snapshot["mechanical"])
                    step_b64 = mech.pop("step_b64", None)
                    if step_b64:
                        glb_result = await _convert_step_to_glb(step_b64)
                        if glb_result is not None:
                            glb_b64, glb_size = glb_result
                            mech["glb_b64"] = glb_b64
                            mech["glb_size_bytes"] = glb_size
                            yield GraphEvent(
                                kind="status",
                                data={
                                    "status": "designing",
                                    "geometry_glb_size_bytes": glb_size,
                                },
                            )
                    research_for_snapshot["mechanical"] = mech

                # Cross-domain BoM. Prefer the designer's JSON block;
                # fall back to deterministic derivation from research
                # outputs so downstream consumers (sourcing agent,
                # firmware agent, UI) always have a unified list.
                designer_bom = _extract_bom("".join(design_text_parts))
                fallback_bom = _bom_from_research(research_for_snapshot)
                bom = designer_bom or fallback_bom
                bom_source = (
                    "designer_json" if designer_bom else "research_fallback"
                )

                snapshot = {
                    "phase": 12,
                    "planner_output": "".join(plan_text_parts),
                    "planner_parsed": plan_parsed,
                    "domains": sorted(domains),
                    "research": research_for_snapshot,
                    "designer_output": "".join(design_text_parts),
                    "bom": bom,
                    "bom_source": bom_source,
                }

                # Surface what's actually going to disk so we can debug
                # "viewer shows old data" disconnects from the agent logs.
                _elec = research_for_snapshot.get("electronics") or {}
                _mech = research_for_snapshot.get("mechanical") or {}
                _candidate_parts = _elec.get("candidate_parts") if isinstance(_elec, dict) else None
                _glb = _mech.get("glb_b64") if isinstance(_mech, dict) else None
                print(
                    f"[agent] snapshot summary for project={input.project_id}: "
                    f"candidate_parts={len(_candidate_parts) if isinstance(_candidate_parts, list) else 'absent'}, "
                    f"glb_b64={'present (' + str(len(_glb)) + ' chars)' if isinstance(_glb, str) else 'absent'}, "
                    f"bom_rows={len(bom)}, bom_source={bom_source}",
                    file=sys.stderr,
                )

                # Emit the in-memory artifact BEFORE persistence so the
                # client never loses the result if the snapshot insert
                # flakes. Persistence failures get their own event and
                # surface in agent stderr — they don't kill the stream.
                yield GraphEvent(
                    kind="bom",
                    data={"bom": bom, "source": bom_source, "count": len(bom)},
                )

                persist_error: str | None = None
                try:
                    append_version_snapshot(
                        project_id=input.project_id,
                        snapshot=snapshot,
                        created_by=input.owner_id,
                        note="Phase 12 cross-domain run",
                    )
                except Exception as exc:  # noqa: BLE001
                    persist_error = str(exc)
                    print(
                        f"[agent] WARNING: append_version_snapshot failed: {exc}",
                        file=__import__("sys").stderr,
                    )
                    yield GraphEvent(
                        kind="warning",
                        data={
                            "stage": "persist_snapshot",
                            "message": persist_error,
                        },
                    )

                final_status = "draft" if persist_error is None else "failed"
                try:
                    update_project_status(input.project_id, final_status)
                except Exception as exc:  # noqa: BLE001
                    print(
                        f"[agent] WARNING: update_project_status({final_status}) failed: {exc}",
                        file=__import__("sys").stderr,
                    )
                yield GraphEvent(kind="complete", data={"status": final_status})

                if root_span is not None:
                    root_span.update(output=snapshot)
    except Exception as exc:  # noqa: BLE001
        update_project_status(input.project_id, "failed")
        if langfuse is not None:
            try:
                langfuse.update_current_span(level="ERROR", status_message=str(exc))
            except Exception:  # noqa: BLE001
                pass
        yield GraphEvent(kind="error", data={"message": str(exc)})
        raise
    finally:
        if langfuse is not None:
            try:
                langfuse.flush()
            except Exception:  # noqa: BLE001
                pass
