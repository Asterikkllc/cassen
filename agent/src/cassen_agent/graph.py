"""LangGraph that drives a single project run.

Phase 5 skeleton: planner -> designer. Each node calls Claude for real
reasoning but the prompts are minimal — knowledge packs (electronics,
mechanical, fluids) come online in Phase 6+.

The graph yields events as it runs so the FastAPI surface can stream
them to the browser. Persistence (Supabase status updates, version
snapshots) happens at node boundaries.

Note on tracing: Langfuse v4 uses an OpenTelemetry-based API
(start_as_current_observation, etc.) that's incompatible with the v2
.trace()/.span() shape. Re-instrumentation is tracked under Phase 5b.
The graph runs fine without it; only loss is no Langfuse trace per run.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from anthropic import AsyncAnthropic

from .db import append_version_snapshot, update_project_status
from .settings import get_settings


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
List which apply.
3. The 5-7 highest-value design questions to answer next.

Respond in compact JSON:
{
  "product_type": "...",
  "domains": ["..."],
  "questions": ["...", "..."]
}
No prose outside the JSON.
"""

DESIGNER_SYSTEM = """You are the Cassen designer. Given the planner's decomposition, \
produce a tight first-pass design sketch:

- key components (3-8 items, real categories not SKUs)
- one-line rationale for each
- principal risks / unknowns

Plain markdown, no preamble. This is a sketch — Phase 6 will replace it with \
knowledge-pack-grounded sourcing.
"""


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
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    try:
        # ---- planner -------------------------------------------------------
        update_project_status(input.project_id, "planning")
        yield GraphEvent(kind="status", data={"status": "planning"})
        yield GraphEvent(kind="node-start", node="planner")

        plan_text_parts: list[str] = []
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
                plan_parsed: dict | None = None
                try:
                    plan_parsed = json.loads(plan_text.strip().strip("`"))
                except Exception:  # noqa: BLE001
                    pass
                yield GraphEvent(
                    kind="node-end",
                    node="planner",
                    data={"text": plan_text, "parsed": plan_parsed},
                )

        # ---- designer ------------------------------------------------------
        update_project_status(input.project_id, "designing")
        yield GraphEvent(kind="status", data={"status": "designing"})
        yield GraphEvent(kind="node-start", node="designer")

        designer_input = (
            "User request:\n"
            f"{input.prompt}\n\n"
            f"Planner decomposition:\n{''.join(plan_text_parts)}\n"
        )

        design_text_parts: list[str] = []
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
                yield GraphEvent(kind="node-end", node="designer", data={"text": design_text})

        # ---- snapshot + complete ------------------------------------------
        snapshot = {
            "phase": 5,
            "planner_output": "".join(plan_text_parts),
            "designer_output": "".join(design_text_parts),
        }
        append_version_snapshot(
            project_id=input.project_id,
            snapshot=snapshot,
            created_by=input.owner_id,
            note="Phase 5 skeleton run",
        )
        update_project_status(input.project_id, "draft")
        yield GraphEvent(kind="complete", data={"status": "draft"})
    except Exception as exc:  # noqa: BLE001
        update_project_status(input.project_id, "failed")
        yield GraphEvent(kind="error", data={"message": str(exc)})
        raise
