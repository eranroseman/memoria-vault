"""Runtime modules must not depend on the engine layer at import time."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.static

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "src" / "memoria_vault" / "runtime"

# Entry-point transports: zero fan-in from src/ (nothing imports them), so an
# engine import there is a door binding, not an inversion. Anything else under
# runtime/ importing the engine at module level makes a surface module a
# dependency of a domain module (audit §2.3).
ENTRY_POINTS = {"http_transport.py", "mcp_transport.py"}

# cli.py is the registered console-script entry point itself
# ([project.scripts] memoria = "memoria_vault.cli:main"); its two subcommand
# handlers (_cmd_serve_http, _cmd_mcp) defer-import the transports to start
# them. That is the same entry-point chain one hop further out, not a domain
# module reaching into a transport — so it is exempt from the fan-in scan
# below, the same way the transports are exempt from importing themselves.
CLI_ENTRY_POINT = "cli.py"


def _module_level_engine_imports(path: Path) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    lines = []
    for node in tree.body:  # module level only: deferred imports are the sanctioned idiom
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
            "memoria_vault.engine"
        ):
            lines.append(node.lineno)
        if isinstance(node, ast.Import) and any(
            alias.name.startswith("memoria_vault.engine") for alias in node.names
        ):
            lines.append(node.lineno)
    return lines


def _imports_transport(path: Path, name: str) -> bool:
    """Whether ``path`` imports the named transport module, at any depth.

    Walks the whole tree (not just ``tree.body``) so a deferred import inside
    a function counts just as much as a module-level one — a deferred import
    of a transport would still be a fan-in hole for the entry-point exemption
    below. AST-based, matching ``_module_level_engine_imports``, so a comment
    or docstring that merely mentions the transport's name can't false-positive
    the way a substring match on the raw file text would.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == name or module.endswith(f".{name}"):
                return True
            if any(alias.name == name for alias in node.names):
                return True
        if isinstance(node, ast.Import):
            if any(
                alias.name == name or alias.name.endswith(f".{name}") for alias in node.names
            ):
                return True
    return False


def test_runtime_never_imports_the_engine_at_module_level() -> None:
    offenders = {}
    for path in sorted(RUNTIME.rglob("*.py")):
        if "__pycache__" in path.parts or path.name in ENTRY_POINTS:
            continue
        lines = _module_level_engine_imports(path)
        if lines:
            offenders[str(path.relative_to(ROOT))] = lines
    assert offenders == {}, f"module-level engine imports in runtime: {offenders}"


def test_the_entry_point_exemption_is_still_earned() -> None:
    """The two exempt transports must keep zero fan-in from src/.

    The day something under src/ imports a transport, its exemption above is
    a hole, not a door binding — this is the check that notices.
    """
    importers = []
    for path in sorted((ROOT / "src").rglob("*.py")):
        if (
            "__pycache__" in path.parts
            or path.name in ENTRY_POINTS
            or path.name == CLI_ENTRY_POINT
        ):
            continue
        for name in ("http_transport", "mcp_transport"):
            if _imports_transport(path, name):
                importers.append(f"{path.relative_to(ROOT)} -> {name}")
    assert importers == [], importers


def test_the_guard_itself_can_fail() -> None:
    """Kill-check: the detector flags a synthetic module-level engine import."""
    bad = "from memoria_vault.engine import api as engine_api\n"
    tree = ast.parse(bad)
    assert isinstance(tree.body[0], ast.ImportFrom)
    probe = Path(__file__).parent / "_layering_probe.py"
    probe.write_text(bad, encoding="utf-8")
    try:
        assert _module_level_engine_imports(probe) == [1]
    finally:
        probe.unlink()
