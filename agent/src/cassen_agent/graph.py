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

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(
                f"{s.cad_base_url}/convert/step-to-gltf",
                headers={"Authorization": f"Bearer {s.cad_shared_secret}"},
                files={"file": ("part.step", step_bytes, "model/step")},
            )
    except httpx.RequestError as exc:
        print(f"[agent] glb skip: cad request failed ({exc})", file=sys.stderr)
        return None

    if r.status_code != 200:
        body_preview = (r.text or "")[:200]
        print(
            f"[agent] glb skip: cad returned HTTP {r.status_code}: {body_preview}",
            file=sys.stderr,
        )
        return None

    glb = r.content
    if not glb:
        return None
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

You have CAD tools backed by a build123d service:
- list_parametric_templates: enumerate the bounded primitives the service \
ships (enclosure_box, mounting_plate, bracket_l, ...) with input JSON Schemas.
- generate_part(template, inputs): build a parametric part. Returns \
{template, inputs, size_bytes, step_b64}.
- generate_from_script(code, timeout_s?): run an agent-authored \
build123d script in a sandbox. Use this only when no template fits. \
The script must end with `result = <build123d shape>`. Imports allowed: \
`build123d`, `math`. No `os`, `subprocess`, `socket`, etc.

HARD RULES (non-negotiable):
- DO NOT ask the user clarifying questions. The user has already left the \
  room. They cannot answer.
- Pick ONE template (or one custom script) and generate it. The trailing \
  JSON has a single `mechanical_part` object, NOT a list — do not return \
  multiple parts joined by commas.
- Failing to call generate_part / generate_from_script is a failure.

Process:
1. Call list_parametric_templates first to learn what's available.
2. Decide on the project's mechanical needs (enclosure? mounting plate? \
bracket? custom?). Pick the SIMPLEST tool for the job — prefer templates \
over custom scripts.
3. Generate the part with realistic dimensions tied to the project (e.g. \
size the enclosure to fit the chosen MCU + sensors from electronics \
research, if any).
4. End your turn with a compact JSON summary:
   {
     "mechanical_part": {
       "template": "...",       // null if generated from script
       "inputs": { ... },        // empty if from script
       "from_script": false,     // true when generate_from_script was used
       "size_bytes": 12345,
       "rationale": "one sentence"
     }
   }
   No prose after the JSON.

Two to four tool calls is typical — don't over-engineer. If the part \
is purely structural (e.g. just an enclosure to house electronics), one \
call is enough.
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
                                        last_b64 = _last_step_b64_from_calls(mech_calls)
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
