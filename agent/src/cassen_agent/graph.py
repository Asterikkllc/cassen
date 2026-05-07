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
from .tools import mcp_session, run_tool_using_loop


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

DESIGNER_SYSTEM = """You are the Cassen designer. Given the planner's decomposition \
and any researcher findings, produce a tight first-pass design sketch:

- key components (3-8 items). When the researcher has already grounded electronic \
parts in real MPNs, use those exact MPNs; for unresearched domains, use real \
categories/types not SKUs.
- one-line rationale for each
- principal risks / unknowns

Plain markdown, no preamble. Do not invent MPNs that the researcher didn't \
return.
"""

ELECTRONICS_RESEARCH_SYSTEM = """You are the Cassen electronics researcher.

You have tools backed by live distributor APIs (Digi-Key, Nexar/Octopart, \
Mouser). Use them to ground every electronic component choice in a real, \
available MPN. Tool results carry a `source` field so you can see which \
distributor produced each row, plus an `attempts` array showing the chain.

Process:
1. Identify the electronic functions the project needs (MCU, sensors, power, \
   communication, drivers/actuators).
2. For each function, call search_part to discover candidates, then get_part \
   for top picks. Use recommend_alternative when the obvious first choice has \
   tradeoffs worth mentioning.
3. Pick one MPN per function. Note tradeoffs in one sentence.
4. End your turn with a compact JSON object summarizing your picks:
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

                # ---- designer ---------------------------------------------
                update_project_status(input.project_id, "designing")
                yield GraphEvent(kind="status", data={"status": "designing"})
                yield GraphEvent(kind="node-start", node="designer")

                research_block = ""
                electronics_research = research_outputs.get("electronics")
                if electronics_research and electronics_research.get("final_text"):
                    research_block = (
                        f"\nElectronics research findings:\n"
                        f"{electronics_research['final_text']}\n"
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
                snapshot = {
                    "phase": 6,
                    "planner_output": "".join(plan_text_parts),
                    "planner_parsed": plan_parsed,
                    "domains": sorted(domains),
                    "research": research_outputs,
                    "designer_output": "".join(design_text_parts),
                }
                append_version_snapshot(
                    project_id=input.project_id,
                    snapshot=snapshot,
                    created_by=input.owner_id,
                    note="Phase 6b run",
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
