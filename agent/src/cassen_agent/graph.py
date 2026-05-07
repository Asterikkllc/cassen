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

import json
from collections.abc import AsyncIterator
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any

from anthropic import AsyncAnthropic
from langfuse import Langfuse, propagate_attributes

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
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
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
                            try:
                                plan_parsed = json.loads(plan_text.strip().strip("`"))
                            except Exception:  # noqa: BLE001
                                plan_parsed = None
                            yield GraphEvent(
                                kind="node-end",
                                node="planner",
                                data={"text": plan_text, "parsed": plan_parsed},
                            )
                            if plan_span is not None:
                                plan_span.update(
                                    output={"text": plan_text, "parsed": plan_parsed},
                                )

                # ---- designer ---------------------------------------------
                update_project_status(input.project_id, "designing")
                yield GraphEvent(kind="status", data={"status": "designing"})
                yield GraphEvent(kind="node-start", node="designer")

                designer_input = (
                    "User request:\n"
                    f"{input.prompt}\n\n"
                    f"Planner decomposition:\n{''.join(plan_text_parts)}\n"
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
                snapshot = {
                    "phase": 5,
                    "planner_output": "".join(plan_text_parts),
                    "planner_parsed": plan_parsed,
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
