"""Allowlist validator tests for cassen_cad.sandbox.

Run with: uv run python -m pytest tests/test_sandbox.py -q
"""

from __future__ import annotations

import pytest

from cassen_cad.sandbox import (
    SandboxValidationError,
    validate_source,
)


# --- accepted scripts --------------------------------------------------------

ALLOWED_SCRIPTS = [
    # canonical: build a box
    "from build123d import Box\nresult = Box(20, 20, 20)\n",
    # alias import
    "import build123d as bd\nresult = bd.Box(10, 10, 10)\n",
    # math is on the allowlist
    "from math import pi\nfrom build123d import Cylinder\nresult = Cylinder(5, 10, rotation=(0, 0, pi))\n",
    # submodule path of an allowed root is fine
    "from build123d.objects_part import Box\nresult = Box(1, 2, 3)\n",
    # plain expressions / comprehensions are fine
    "from build123d import Box\nsizes = [s for s in (10, 20, 30)]\nresult = Box(*sizes)\n",
]


@pytest.mark.parametrize("src", ALLOWED_SCRIPTS)
def test_validator_accepts_safe_script(src: str) -> None:
    validate_source(src)  # should not raise


# --- rejected scripts --------------------------------------------------------

REJECTED_SCRIPTS = {
    "import os": "import os\nresult = None\n",
    "import socket": "import socket\nresult = None\n",
    "from subprocess import run": "from subprocess import run\nresult = None\n",
    "from urllib.request import urlopen": "from urllib.request import urlopen\nresult = None\n",
    "use of eval": "result = eval('1+1')\n",
    "use of exec": "exec('print(1)')\nresult = None\n",
    "use of __import__": "result = __import__('os')\n",
    "use of open()": "result = open('/etc/passwd').read()\n",
    "dunder attribute escape": "result = ().__class__.__bases__\n",
    "subclasses escape": "result = ().__class__.__subclasses__()\n",
    "globals() leak": "result = globals()\n",
    "compile()": "result = compile('1', '', 'eval')\n",
    "relative import": "from . import something\nresult = None\n",
}


@pytest.mark.parametrize(
    "src",
    list(REJECTED_SCRIPTS.values()),
    ids=list(REJECTED_SCRIPTS.keys()),
)
def test_validator_rejects_unsafe_script(src: str) -> None:
    with pytest.raises(SandboxValidationError):
        validate_source(src)


def test_validator_rejects_syntax_error() -> None:
    with pytest.raises(SandboxValidationError) as exc:
        validate_source("def (\n")
    assert "syntax error" in str(exc.value).lower()
