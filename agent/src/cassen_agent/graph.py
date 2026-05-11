"""Cassen design-agent graph — slice 1: planner only.

The planner decomposes the user's goal into structured fields:
  - product_type     : one-phrase product class
  - domains          : which knowledge-pack domains apply
  - clarifying       : 3-5 high-value clarifying questions
  - acknowledgement  : 1-2 sentence summary back to the user

Slice 1 surfaces only the acknowledgement to the visible chat
content; structured fields are stored under `thinking` so the user
can expand them via the chat thread's Thinking disclosure. Later
slices (knowledge-pack research, design, sim) consume the same
structured payload to drive downstream nodes.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Literal

from anthropic import AsyncAnthropic

from .db import (
    append_project_message,
    fetch_project,
    list_project_messages,
    update_project_status,
)
from .settings import get_settings


# Knowledge-pack vocabulary. The agent core is domain-agnostic; packs
# get loaded by name. Slice 1 only emits the chosen domain set —
# subsequent slices read this list to spawn per-domain research nodes.
KNOWN_DOMAINS: tuple[str, ...] = (
    "electronics",
    "mechanical",
    "software",
    "fluids",
    "optics",
    "thermal",
    "structural",
    "chemistry",
    "textiles",
    "woodworking",
)


PLANNER_SYSTEM = """You are the Cassen planner. The user described a \
physical product they want built; Cassen is a general-purpose agent \
that designs, validates, sources, fabricates, and ships physical \
products end-to-end.

Your job, on EVERY turn, is to decompose the user's most recent \
message in the context of the running thread, then emit:

1. A short conversational acknowledgement (1-2 sentences). This is \
   what the user SEES in the chat bubble. Tone is professional \
   engineer, not chatbot. Concrete, not generic.

2. A structured JSON block AT THE END of your reply, fenced like:
```json
{
  "product_type": "compact 250mm racing quadcopter",
  "domains": ["electronics", "mechanical"],
  "clarifying": [
    "What's the target flight time?",
    "Indoor or outdoor use?"
  ],
  "next_action": "ready_to_design"
}
```

Fields:
- `product_type` : one-phrase product class.
- `domains` : choose from %(domains)s. Pick every domain the project \
  genuinely needs. Most projects span 2-4 domains. A drone is \
  electronics + mechanical (+ thermal if it's high-power). A smart \
  planter is electronics + mechanical + fluids. A custom controller \
  is electronics + mechanical + software.
- `clarifying` : 3-5 highest-value clarifying questions. Pick ones \
  that meaningfully change the design (form factor, performance \
  target, environment), NOT ones the agent could safely assume \
  (default to industry-standard part choices).
- `next_action` : "ask_user" if you must hear back before the design \
  pass can start, OR "ready_to_design" if the brief is rich enough \
  that the platform should proceed with reasonable defaults.

If the user is replying to one of your previous clarifying questions, \
fold their answer into your understanding and re-emit the updated \
decomposition.

Output rules:
- ALWAYS finish your reply with the fenced JSON block; nothing after it.
- Don't restate the user's prompt back to them — assume they read it.
- Don't ask more than 4 clarifying questions; pick the highest-value ones.
- Don't ask questions the user already answered earlier in the thread.
""" % {"domains": ", ".join(KNOWN_DOMAINS)}


# ----------------------------------------------------------------------
# SSE event shape (matches the slice-0 chat-thread parser)
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class ChatEvent:
    kind: Literal["token", "message-end", "error", "system"]
    data: dict[str, Any]


def serialize_event(ev: ChatEvent) -> str:
    """Format an event as one SSE frame."""
    payload = {"kind": ev.kind, **ev.data}
    return f"data: {json.dumps(payload, default=str)}\n\n"


# ----------------------------------------------------------------------
# Planner runner
# ----------------------------------------------------------------------


def _strip_trailing_json(text: str) -> tuple[str, dict[str, Any] | None]:
    """Pull the trailing JSON block out of the planner's reply.

    Returns `(visible_text, parsed_json | None)`. Looks for the LAST
    closing brace and walks back to a balanced opening brace, so the
    same logic works whether the planner used fenced ```json``` or
    not. Visible text is everything before the JSON, trimmed of any
    leading/trailing fences.
    """
    if not text:
        return text, None
    end = text.rfind("}")
    if end == -1:
        return text, None
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
        return text, None
    blob = text[start : end + 1]
    try:
        parsed = json.loads(blob)
    except Exception:  # noqa: BLE001
        return text, None
    visible = text[:start]
    # Strip any leftover ```json fence wrappers around the visible part.
    visible = visible.rstrip()
    if visible.endswith("```"):
        visible = visible[:-3].rstrip()
    if visible.endswith("```json"):
        visible = visible[:-7].rstrip()
    # Also walk back through opening fence on its own line.
    lines = visible.splitlines()
    while lines and lines[-1].strip() in {"```", "```json"}:
        lines.pop()
    visible = "\n".join(lines).rstrip()
    return visible, parsed if isinstance(parsed, dict) else None


async def run_planner_chat(
    *,
    project_id: str,
) -> AsyncIterator[ChatEvent]:
    """Run one planner turn on the project's existing thread; stream
    tokens, persist the assistant turn, end with `message-end`.

    The visible content (what the user reads in the bubble) is the
    planner's acknowledgement; the structured JSON block at the tail
    of the LLM response is captured into `thinking` so the chat
    thread can expose it via the Thinking disclosure.
    """
    settings = get_settings()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key, max_retries=4)

    # Pull the persisted thread. The /chat-stream endpoint persisted
    # the user's most recent message BEFORE invoking us, so the tail
    # of `history` is the message we're replying to.
    history = list_project_messages(project_id, limit=50)
    api_messages: list[dict[str, Any]] = []
    for m in history:
        role = m.get("role")
        if role not in ("user", "assistant"):
            continue
        text = (m.get("content") or "").strip()
        if not text:
            continue
        api_messages.append({"role": role, "content": text})
    if not api_messages:
        # Defensive: shouldn't happen because the proxy always
        # persists the user turn first.
        project = fetch_project(project_id)
        if project and project.get("prompt"):
            api_messages.append(
                {"role": "user", "content": str(project["prompt"])}
            )

    # Status: planning. App page surfaces this via the sidebar +
    # project status pill.
    try:
        update_project_status(project_id, "planning")
    except Exception:  # noqa: BLE001
        # Status writes are best-effort; pipeline still runs.
        pass

    raw_parts: list[str] = []
    visible_so_far = ""
    try:
        async with client.messages.stream(
            model=settings.planner_model,
            max_tokens=settings.planner_max_tokens,
            system=PLANNER_SYSTEM,
            messages=api_messages,
        ) as stream:
            async for chunk in stream.text_stream:
                if not chunk:
                    continue
                raw_parts.append(chunk)
                # Recompute the visible-only slice each chunk so the
                # JSON tail never appears in the user's bubble. This
                # is O(n) per chunk but the planner replies are short.
                combined = "".join(raw_parts)
                visible, _ = _strip_trailing_json(combined)
                # Only stream the NEW delta of visible text since
                # last chunk; otherwise the client would render the
                # whole reply repeatedly.
                if visible.startswith(visible_so_far):
                    delta = visible[len(visible_so_far) :]
                    if delta:
                        visible_so_far = visible
                        yield ChatEvent(kind="token", data={"text": delta})
                else:
                    # Visible shrank (planner rewrote tail; rare but
                    # possible when the JSON fence boundary shifts).
                    # Send a replacement: clear by emitting the new
                    # full text minus what we sent. Simpler approach:
                    # update visible_so_far and skip; the final
                    # message-end carries the correct full text.
                    visible_so_far = visible
    except Exception as exc:  # noqa: BLE001
        yield ChatEvent(kind="error", data={"error": str(exc)})
        return

    full_raw = "".join(raw_parts)
    visible, parsed = _strip_trailing_json(full_raw)

    # Build the persisted Thinking blob from the structured fields so
    # the user can expand it later.
    thinking: str | None = None
    if parsed:
        thinking_lines = []
        if pt := parsed.get("product_type"):
            thinking_lines.append(f"Product type: {pt}")
        if doms := parsed.get("domains"):
            thinking_lines.append(f"Domains: {', '.join(map(str, doms))}")
        if cq := parsed.get("clarifying"):
            thinking_lines.append("Clarifying questions:")
            for q in cq:
                thinking_lines.append(f"  • {q}")
        if na := parsed.get("next_action"):
            thinking_lines.append(f"Next action: {na}")
        thinking = "\n".join(thinking_lines) if thinking_lines else None

    final_text = visible.strip() or "Planning the project."
    append_project_message(
        project_id,
        role="assistant",
        content=final_text,
        thinking=thinking,
    )

    yield ChatEvent(
        kind="message-end",
        data={"text": final_text, "planner_parsed": parsed},
    )
