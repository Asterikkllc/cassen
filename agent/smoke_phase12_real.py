"""End-to-end Phase 12 smoke (REAL LLM): cross-domain smart planter run.

Drives `run_graph` against a smart-planter prompt that should exercise
all three knowledge packs + the CAD service + the designer using a
REAL Anthropic key. No mocks; this is the truth-test of the whole
pipeline.

Run this AFTER topping up Anthropic credits.

Prerequisites:
- ANTHROPIC_API_KEY valid in agent/.env
- cad/ running on http://127.0.0.1:8002 (provides /generate/parametric*)
- mcp-electronics, mcp-mechanical, mcp-cad, mcp-fluids — paths set in
  agent/.env (already done in Phases 6c, 8c, 9, 11)
- Distributor keys set in mcp-electronics/.env (Digi-Key + Nexar +
  Mouser) — at least one must be configured for electronics_research
  to produce real MPNs

Usage:
  cd agent
  C:/Users/HP/.local/bin/uv.exe run python smoke_phase12_real.py

Expected timing:
- Cold-start: planner ~2s, each research node ~10-30s,
  mechanical_design ~30-60s (cad/ build123d cold-import dominates),
  designer ~5-10s. Total ~2-3 min on a warm cache.

Cost (rough): planner ~1k tok, each research node 10-20k tok with
tool calls, designer ~3k tok. Sonnet 4.6 + Opus 4.7 mix ≈ a few
cents per run.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

# Stub DB writes — the Phase 12 smoke is about the graph, not Supabase.
import cassen_agent.db as db

db.update_project_status = lambda *a, **kw: None  # type: ignore[assignment]
db.append_version_snapshot = lambda *a, **kw: None  # type: ignore[assignment]
import cassen_agent.graph as graph  # noqa: E402

graph.append_version_snapshot = db.append_version_snapshot  # type: ignore[assignment]

from cassen_agent.graph import GraphInput, run_graph  # noqa: E402

PROMPT = (
    "Build me a smart self-watering planter. It should sense soil moisture, "
    "pump water from a small reservoir when the soil is too dry, and report "
    "status over Wi-Fi."
)


async def main() -> int:
    failures = 0
    nodes_seen: list[str] = []
    captured_bom: list[dict] | None = None
    last_planner_text: str = ""
    research_summaries: dict[str, str] = {}
    designer_text: str = ""

    async for ev in run_graph(
        GraphInput(
            project_id="00000000-0000-0000-0000-000000000000",
            owner_id="00000000-0000-0000-0000-000000000000",
            prompt=PROMPT,
        )
    ):
        if ev.kind == "node-start" and ev.node:
            nodes_seen.append(ev.node)
            print(f"  >> {ev.node}")
        elif ev.kind == "tool-call-start":
            print(f"     tool: {(ev.data or {}).get('name')}")
        elif ev.kind == "tool-call-end":
            ok = not (ev.data or {}).get("is_error", False)
            print(f"     tool ok={ok}")
        elif ev.kind == "node-end":
            d = ev.data or {}
            if ev.node == "planner":
                last_planner_text = d.get("text", "")
            elif ev.node and "research" in ev.node:
                research_summaries[ev.node] = d.get("text", "")[:200]
            elif ev.node == "mechanical_design":
                research_summaries["mechanical_design"] = json.dumps(
                    d.get("pick", {})
                )[:300]
            elif ev.node == "designer":
                designer_text = d.get("text", "")
        elif ev.kind == "bom":
            captured_bom = (ev.data or {}).get("bom")
            print(
                f"  ## bom: {(ev.data or {}).get('count')} rows, "
                f"source={(ev.data or {}).get('source')}"
            )
        elif ev.kind == "complete":
            print("  ## complete")
        elif ev.kind == "error":
            print(f"  ## ERROR: {ev.data}")
            return 1

    print()
    print("=== summary ===")
    print(f"planner output: {last_planner_text[:200]}...")
    for node, summary in research_summaries.items():
        print(f"{node}: {summary}")
    print(f"designer (first 400 chars): {designer_text[:400]}...")
    print()
    print(f"BoM ({len(captured_bom or [])} rows):")
    for row in captured_bom or []:
        print(f"  [{row.get('domain'):<11}] {row.get('id')}  — {row.get('rationale','')[:60]}")

    expected = {
        "planner",
        "electronics_research",
        "mechanical_research",
        "mechanical_design",
        "fluids_research",
        "designer",
    }
    seen = set(nodes_seen)
    if expected <= seen:
        print(f"\n[OK] all 6 expected nodes fired")
    else:
        print(f"\n[FAIL] missing nodes: {expected - seen}")
        failures += 1

    if captured_bom and len(captured_bom) >= 4:
        domains_in_bom = {r.get("domain") for r in captured_bom}
        if {"electronics", "mechanical", "fluids"} <= domains_in_bom:
            print("[OK] BoM spans electronics + mechanical + fluids")
        else:
            print(f"[FAIL] BoM missing domains: {domains_in_bom}")
            failures += 1
    else:
        print(f"[FAIL] BoM too small or missing: {captured_bom}")
        failures += 1

    return failures


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.exit(asyncio.run(main()))
