"""Cassen v1 — mechanical CAD knowledge pack MCP server.

Wraps cad/'s parametric + sandboxed-script endpoints so the agent can
generate real STEP geometry as part of a design pass.

STEP bytes are returned base64-encoded as `step_b64`; the agent should
either pass that on to cad/'s STEP→GLB endpoint or stash it on
project storage. We keep this surface stable so the agent doesn't
change when the CAD backend gains caching, async processing, or moves
to Modal sandboxes.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from . import client

server = FastMCP("cassen-cad")


@server.tool()
def list_parametric_templates() -> dict[str, Any]:
    """List every parametric CAD template the cad/ service exposes.

    Each template returns a name, description, and a JSON Schema
    describing the inputs it accepts. Use the schema to know which
    fields to send to `generate_part`.

    Templates are bounded primitives — enclosure_box, mounting_plate,
    bracket_l, etc. For shapes outside the template library, use
    `generate_from_script` to author a build123d Python script.
    """
    return client.list_templates()


@server.tool()
def generate_part(template: str, inputs: dict[str, Any]) -> dict[str, Any]:
    """Build a parametric part by template name.

    `template` is one of the names returned by list_parametric_templates.
    `inputs` is a JSON object matching that template's input_schema.

    Returns `{template, inputs, size_bytes, step_b64}` on success or
    `{error, status, detail?}` on validation failure (422) or unknown
    template (404). The base64 STEP can be routed through cad/'s
    /convert/step-to-gltf for in-browser rendering.
    """
    if not isinstance(inputs, dict):
        return {"error": "`inputs` must be a JSON object", "status": 400}
    return client.generate_parametric(template, inputs)


@server.tool()
def generate_from_script(code: str, timeout_s: float | None = None) -> dict[str, Any]:
    """Run an agent-authored build123d Python script in cad/'s sandbox.

    The script must assign a build123d shape to a top-level `result`
    variable. cad/ appends the export footer.

    Sandbox rules (enforced by cad/'s AST allowlist):
    - Imports allowed: `build123d` (any submodule), `math`. Nothing else.
    - No `os`, `socket`, `subprocess`, `urllib`, `eval`, `exec`,
      `compile`, `open`, `__import__`, dunder attribute access.
    - Wall-clock timeout: default 30s, max 60s.
    - Source ≤ 64 KB.

    Returns `{size_bytes, duration_ms, step_b64}` on success or
    `{error, status, detail?}` if the script was rejected (400),
    too big (413), failed (422), or timed out (504).

    Use this for shapes templates can't express (lofts, sweeps,
    chamfers/fillets on custom geometry, multi-body assemblies). For
    common shapes, prefer `generate_part` — it's faster and validated.
    """
    if not isinstance(code, str) or not code.strip():
        return {"error": "`code` must be a non-empty string", "status": 400}
    return client.generate_from_script(code, timeout_s=timeout_s)


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
