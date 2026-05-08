"""MCP client wiring for the agent.

`mcp_session(command, args, ...)` is an async context manager that
spawns an MCP server as a subprocess (over stdio), initializes the
client session, and yields it. Use it inside an `async with`.

`run_tool_using_loop(...)` is the core Anthropic tool-use loop: send
the user prompt to Claude with the MCP server's tools available, dispatch
any tool_use blocks back through the session, feed tool_results to
Claude, and repeat until end_turn (or `max_iterations` is hit).

The loop is an async generator that yields lightweight events the graph
turns into SSE frames. The final `("done", {...})` event carries the
full assistant text + a structured trace of tool calls so the calling
node can put it into a project_versions snapshot.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from anthropic import AsyncAnthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@asynccontextmanager
async def mcp_session(
    *,
    command: str,
    args: list[str],
    env: dict[str, str] | None = None,
    cwd: str | None = None,
) -> AsyncIterator[ClientSession]:
    params = StdioServerParameters(command=command, args=args, env=env, cwd=cwd)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


def mcp_tools_to_anthropic(tools: list[Any]) -> list[dict[str, Any]]:
    """Convert MCP tool defs to the Anthropic Messages API tool schema."""
    out: list[dict[str, Any]] = []
    for t in tools:
        out.append(
            {
                "name": t.name,
                "description": t.description or "",
                "input_schema": t.inputSchema or {"type": "object", "properties": {}},
            }
        )
    return out


def _extract_text(blocks: Any) -> str:
    parts: list[str] = []
    for b in blocks or []:
        if getattr(b, "type", None) == "text":
            parts.append(getattr(b, "text", "") or "")
        elif isinstance(b, dict) and b.get("type") == "text":
            parts.append(b.get("text", "") or "")
    return "".join(parts)


def _tool_result_text(result: Any) -> str:
    """Pull the textual content out of an MCP CallToolResult."""
    out: list[str] = []
    for c in getattr(result, "content", None) or []:
        text = getattr(c, "text", None)
        if isinstance(text, str):
            out.append(text)
    return "\n".join(out) if out else ""


async def run_tool_using_loop(
    *,
    client: AsyncAnthropic,
    session: ClientSession,
    system: str,
    user_prompt: str,
    model: str,
    max_tokens: int,
    max_iterations: int = 8,
) -> AsyncIterator[tuple[str, dict[str, Any]]]:
    """Yield events as Claude tool-uses against the MCP session.

    Event kinds (first element of the tuple):
      - "iteration"        : data = {"i": int}
      - "assistant-text"   : data = {"text": str}    (incremental between tool turns)
      - "tool-call-start"  : data = {"id", "name", "input"}
      - "tool-call-end"    : data = {"id", "name", "output_text", "is_error"}
      - "tool-error"       : data = {"id", "name", "error"}
      - "done"             : data = {"final_text": str, "calls": [...], "stop_reason": str}
    """
    tools_resp = await session.list_tools()
    anthropic_tools = mcp_tools_to_anthropic(tools_resp.tools)

    messages: list[dict[str, Any]] = [{"role": "user", "content": user_prompt}]
    calls: list[dict[str, Any]] = []
    final_text_parts: list[str] = []

    for i in range(max_iterations):
        yield ("iteration", {"i": i})
        msg = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=anthropic_tools,
            messages=messages,
            # Top-level auto-caching: the SDK places one cache_control
            # breakpoint on the last cacheable block of the request,
            # which is the most recent user-turn block (tool_result on
            # iter 2+, the initial prompt on iter 1). Caching is prefix-
            # based, so the breakpoint covers tools -> system -> all
            # prior assistant/user turns. From iteration 2 onward the
            # request reads ~80%+ of its input tokens at ~0.1x cost
            # instead of paying full price each time.
            #
            # Sonnet 4.6's minimum cacheable prefix is 2048 tokens, so
            # iteration 1 (system + tools + initial prompt ≈ 1500 tok)
            # silently doesn't cache. The first cache write happens on
            # iter 2 once the first tool_result lands; iters 3+ read it.
            cache_control={"type": "ephemeral"},
        )

        text_chunk = _extract_text(msg.content)
        if text_chunk:
            yield ("assistant-text", {"text": text_chunk})
            final_text_parts.append(text_chunk)

        if msg.stop_reason != "tool_use":
            yield (
                "done",
                {
                    "final_text": "".join(final_text_parts),
                    "calls": calls,
                    "stop_reason": msg.stop_reason or "end_turn",
                },
            )
            return

        # Append the assistant turn (with tool_use blocks) to history
        messages.append({"role": "assistant", "content": msg.content})

        tool_results: list[dict[str, Any]] = []
        for block in msg.content:
            if getattr(block, "type", None) != "tool_use":
                continue
            call_id = getattr(block, "id", "")
            tool_name = getattr(block, "name", "")
            tool_input = getattr(block, "input", {}) or {}
            yield (
                "tool-call-start",
                {"id": call_id, "name": tool_name, "input": tool_input},
            )

            try:
                result = await session.call_tool(tool_name, tool_input)
                output_text = _tool_result_text(result)
                is_error = bool(getattr(result, "isError", False))
                yield (
                    "tool-call-end",
                    {
                        "id": call_id,
                        "name": tool_name,
                        "output_text": output_text,
                        "is_error": is_error,
                    },
                )
                calls.append(
                    {
                        "id": call_id,
                        "name": tool_name,
                        "input": tool_input,
                        "output_text": output_text,
                        "is_error": is_error,
                    }
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": call_id,
                        "content": output_text or "(no content)",
                        **({"is_error": True} if is_error else {}),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                err = str(exc)
                yield ("tool-error", {"id": call_id, "name": tool_name, "error": err})
                calls.append(
                    {
                        "id": call_id,
                        "name": tool_name,
                        "input": tool_input,
                        "error": err,
                    }
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": call_id,
                        "content": f"Tool execution error: {err}",
                        "is_error": True,
                    }
                )

        messages.append({"role": "user", "content": tool_results})

    # Hit max_iterations without a clean end_turn.
    yield (
        "done",
        {
            "final_text": "".join(final_text_parts),
            "calls": calls,
            "stop_reason": "max_iterations",
        },
    )
