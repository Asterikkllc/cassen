"""Sandbox for executing agent-authored build123d scripts.

Two layers of defense:

1. **AST allowlist** (`validate_source`) rejects imports outside a small
   safe set, dunder attribute access, and dangerous builtins. Any failure
   raises `SandboxValidationError` with the offending source line.

2. **Subprocess isolation** (`run_script`) executes the validated script
   in a fresh `python -I -B` process with a wall-clock timeout, an empty
   working directory, and no inherited environment beyond what's needed
   to import build123d. On POSIX we also set RLIMIT_CPU / RLIMIT_AS.

The user script must assign a build123d shape to a top-level `result`
variable. A short footer appended by the runner exports that shape to
STEP and prints the path on stdout.

This is defence-in-depth, not a real container. Phase 8c may move
execution to Modal sandboxes; the AST gate stays in front of that too.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path

# --- allowlist ---------------------------------------------------------------

# Only imports whose root module is in this set are accepted. Submodules
# are allowed implicitly (e.g. `build123d.objects_part`).
ALLOWED_ROOT_MODULES: frozenset[str] = frozenset({"build123d", "math"})

# Dunder names forbidden anywhere in the source (read or written). They
# are the usual escape hatches out of a Python sandbox.
FORBIDDEN_NAMES: frozenset[str] = frozenset(
    {
        "__import__",
        "__builtins__",
        "__class__",
        "__bases__",
        "__mro__",
        "__subclasses__",
        "__globals__",
        "__loader__",
        "__spec__",
        "__file__",
        "__code__",
        "__closure__",
        "__dict__",
        "__getattribute__",
    }
)

# Builtin call targets we never want a script to invoke.
FORBIDDEN_CALLS: frozenset[str] = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "open",
        "input",
        "breakpoint",
        "help",
        "globals",
        "locals",
        "vars",
        "getattr",
        "setattr",
        "delattr",
        "memoryview",
    }
)


class SandboxValidationError(Exception):
    """Script failed AST allowlist checks."""

    def __init__(self, message: str, *, lineno: int | None = None) -> None:
        super().__init__(message)
        self.lineno = lineno


class SandboxRunError(Exception):
    """Script ran but produced no STEP output, errored, or timed out."""


@dataclass(frozen=True)
class SandboxResult:
    step_bytes: bytes
    stdout: str
    stderr: str
    duration_s: float


# --- AST validation ----------------------------------------------------------


def _root_module(dotted: str) -> str:
    return dotted.split(".", 1)[0]


class _AllowlistVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.errors: list[tuple[str, int]] = []

    def _reject(self, msg: str, node: ast.AST) -> None:
        self.errors.append((msg, getattr(node, "lineno", 0)))

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = _root_module(alias.name)
            if root not in ALLOWED_ROOT_MODULES:
                self._reject(f"import of module '{alias.name}' is not allowed", node)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level and node.level > 0:
            self._reject("relative imports are not allowed", node)
        mod = node.module or ""
        if not mod or _root_module(mod) not in ALLOWED_ROOT_MODULES:
            self._reject(f"import from module '{mod or '?'}' is not allowed", node)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in FORBIDDEN_NAMES:
            self._reject(f"use of name '{node.id}' is not allowed", node)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in FORBIDDEN_NAMES or node.attr.startswith("__"):
            # Reject any dunder attribute access. build123d does not
            # require dunder reflection in user scripts.
            self._reject(f"attribute access '.{node.attr}' is not allowed", node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            self._reject(f"call to '{node.func.id}()' is not allowed", node)
        self.generic_visit(node)


def validate_source(code: str) -> None:
    """Parse `code` and reject anything outside the allowlist.

    Raises `SandboxValidationError` on the first violation; the message
    aggregates all violations found so callers can surface them at once.
    """
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as exc:
        raise SandboxValidationError(
            f"syntax error at line {exc.lineno}: {exc.msg}",
            lineno=exc.lineno,
        ) from exc

    visitor = _AllowlistVisitor()
    visitor.visit(tree)
    if visitor.errors:
        bullets = "; ".join(f"line {ln}: {msg}" for (msg, ln) in visitor.errors)
        raise SandboxValidationError(
            f"script failed allowlist: {bullets}",
            lineno=visitor.errors[0][1],
        )


# --- subprocess runner -------------------------------------------------------

_FOOTER = textwrap.dedent(
    """
    # --- cassen-cad sandbox footer -----------------------------------------
    import sys as __sys
    if "result" not in dir():
        print("CASSEN_ERROR: script did not define a top-level `result`",
              file=__sys.stderr)
        __sys.exit(2)
    import build123d as __bd
    __bd.export_step(result, "out.step")
    print("CASSEN_OK")
    """
)


def _set_posix_limits(cpu_s: int, mem_bytes: int) -> None:
    # Called as preexec_fn on POSIX only. ImportError is fine on Windows
    # because we don't pass preexec_fn there.
    import resource  # type: ignore[import-not-found]

    resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s))
    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))


def run_script(
    code: str,
    *,
    timeout_s: float = 90.0,
    cpu_s: int = 240,
    mem_bytes: int = 1024 * 1024 * 1024,
) -> SandboxResult:
    """Validate then execute `code` in an isolated subprocess.

    Returns the STEP bytes produced when the script assigns a build123d
    shape to a top-level `result` name. Raises `SandboxValidationError`
    if AST validation fails, `SandboxRunError` for runtime / timeout /
    missing-output errors.
    """
    validate_source(code)

    full = code.rstrip() + "\n" + _FOOTER

    # Minimal env: keep only what Python needs to find its stdlib +
    # build123d (which lives in the uv venv site-packages). Home /
    # SystemRoot env vars are needed because build123d transitively
    # imports OCP_vscode -> IPython -> jedi -> parso, which calls
    # `Path.expanduser()` at import time. The AST allowlist still
    # blocks user code from reaching those paths.
    env: dict[str, str] = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONIOENCODING": "utf-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "TEMP": os.environ.get("TEMP", ""),
        "TMP": os.environ.get("TMP", ""),
        "TMPDIR": os.environ.get("TMPDIR", ""),
    }
    for k in (
        "SystemRoot",
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
        "HOME",
        "APPDATA",
        "LOCALAPPDATA",
    ):
        v = os.environ.get(k)
        if v:
            env[k] = v

    with tempfile.TemporaryDirectory(prefix="cassen-cad-script-") as workdir:
        script_path = Path(workdir) / "script.py"
        script_path.write_text(full, encoding="utf-8")

        kwargs: dict = {
            "cwd": workdir,
            "env": env,
            "capture_output": True,
            "text": True,
            "timeout": timeout_s,
        }
        if sys.platform != "win32":
            kwargs["preexec_fn"] = lambda: _set_posix_limits(cpu_s, mem_bytes)

        import time

        t0 = time.perf_counter()
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "-B", str(script_path)],
                **kwargs,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise SandboxRunError(
                f"script exceeded wall-clock timeout of {timeout_s}s"
            ) from exc
        duration = time.perf_counter() - t0

        if proc.returncode != 0:
            tail = (proc.stderr or "").strip().splitlines()[-20:]
            raise SandboxRunError(
                f"script exited with code {proc.returncode}: "
                + "\n".join(tail)
            )

        out_path = Path(workdir) / "out.step"
        if not out_path.exists() or out_path.stat().st_size == 0:
            raise SandboxRunError("script produced no STEP output")

        return SandboxResult(
            step_bytes=out_path.read_bytes(),
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            duration_s=duration,
        )
