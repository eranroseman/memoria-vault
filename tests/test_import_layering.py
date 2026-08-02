"""Runtime modules must not depend on the engine layer at import time."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.static

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
RUNTIME = SRC / "memoria_vault" / "runtime"

# Entry-point transports: zero fan-in from src/ (nothing imports them), so an
# engine import there is a door binding, not an inversion. Anything else under
# runtime/ importing the engine at module level makes a surface module a
# dependency of a domain module (audit §2.3).
#
# Matched by path relative to src/ (see _is_entry_point below), not by
# basename — a future src/memoria_vault/plugins/http_transport.py must not
# silently inherit this exemption just because its filename matches.
ENTRY_POINTS = {"memoria_vault/runtime/http_transport.py", "memoria_vault/runtime/mcp_transport.py"}


def _is_entry_point(path: Path) -> bool:
    return path.relative_to(SRC).as_posix() in ENTRY_POINTS


def _is_type_checking_guard(test: ast.expr) -> bool:
    """Whether an ``if`` test is (roughly) ``TYPE_CHECKING`` or ``typing.TYPE_CHECKING``.

    An import inside such a guard never executes at runtime — it must not
    count as a module-level dependency. See ``runtime/state.py:53-54`` for the
    live idiom this exists to leave alone.
    """
    if isinstance(test, ast.Name):
        return test.id == "TYPE_CHECKING"
    if isinstance(test, ast.Attribute):
        return test.attr == "TYPE_CHECKING"
    return False


def _import_time_statements(body: list[ast.stmt]) -> list[ast.stmt]:
    """Statements in ``body`` that execute at module-import time.

    Recurses into ``try``/``if``/``with`` blocks (and try's handlers/else/
    finally) — an import nested there still runs when the module is imported;
    it is just invisible to a direct-children-of-``tree.body`` scan. Does
    *not* recurse into function or class bodies: both execute at import time,
    but function bodies are rare at module level and class bodies do not occur
    in the runtime modules examined here; the skip is pragmatic and
    localized. Does not recurse into an ``if TYPE_CHECKING:`` body, which never
    executes; its ``else`` branch (if any) still does and is included.
    """
    statements: list[ast.stmt] = []
    for node in body:
        statements.append(node)
        if isinstance(node, ast.Try):
            statements.extend(_import_time_statements(node.body))
            for handler in node.handlers:
                statements.extend(_import_time_statements(handler.body))
            statements.extend(_import_time_statements(node.orelse))
            statements.extend(_import_time_statements(node.finalbody))
        elif isinstance(node, ast.If):
            if not _is_type_checking_guard(node.test):
                statements.extend(_import_time_statements(node.body))
            statements.extend(_import_time_statements(node.orelse))
        elif isinstance(node, ast.With):
            statements.extend(_import_time_statements(node.body))
    return statements


def _module_dotted_name(path: Path, root: Path) -> str:
    """Dotted module name ``path`` would have if imported from under ``root``."""
    parts = path.relative_to(root).with_suffix("").parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _resolve_import_from(path: Path, node: ast.ImportFrom, root: Path = SRC) -> str:
    """Absolute dotted module ``node`` imports from.

    ``node.level`` dots (``from .foo import x``, ``from ...foo import x``) are
    resolved against ``path``'s own package position under ``root`` — the same
    rule ``importlib`` uses at runtime — so a relative import of the engine is
    recognised as such and not missed just because ``node.module`` is
    ``"engine"`` rather than ``"memoria_vault.engine"``.
    """
    if node.level == 0:
        return node.module or ""
    dotted = _module_dotted_name(path, root)
    package = dotted if path.name == "__init__.py" else dotted.rsplit(".", 1)[0]
    base = package.rsplit(".", node.level - 1)[0]
    return f"{base}.{node.module}" if node.module else base


def _module_level_engine_imports(path: Path, root: Path = SRC) -> list[int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    lines = []
    for node in _import_time_statements(tree.body):
        if isinstance(node, ast.ImportFrom) and _resolve_import_from(path, node, root).startswith(
            "memoria_vault.engine"
        ):
            lines.append(node.lineno)
        if isinstance(node, ast.Import) and any(
            alias.name.startswith("memoria_vault.engine") for alias in node.names
        ):
            lines.append(node.lineno)
    return lines


def _imports_transport(path: Path, name: str, root: Path = SRC) -> bool:
    """Whether ``path`` imports the named transport module at module level.

    Same import-time reach as ``_module_level_engine_imports`` above — module
    level, including nested ``try``/``if``/``with`` blocks, never function or
    class bodies — so both tests in this file apply one consistent notion of
    "depends on." A deferred import inside e.g. ``cli.py``'s subcommand
    handlers is therefore invisible here, the same as any other deferred
    import; no separate exemption for an entry-point *file* is needed on top
    of the module-level-only reach.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in _import_time_statements(tree.body):
        if isinstance(node, ast.ImportFrom):
            module = _resolve_import_from(path, node, root)
            if module == name or module.endswith(f".{name}"):
                return True
            if any(alias.name == name for alias in node.names):
                return True
        if isinstance(node, ast.Import):
            if any(alias.name == name or alias.name.endswith(f".{name}") for alias in node.names):
                return True
    return False


def test_runtime_never_imports_the_engine_at_module_level() -> None:
    offenders = {}
    for path in sorted(RUNTIME.rglob("*.py")):
        if "__pycache__" in path.parts or _is_entry_point(path):
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
    for path in sorted(SRC.rglob("*.py")):
        if "__pycache__" in path.parts or _is_entry_point(path):
            continue
        for name in ("http_transport", "mcp_transport"):
            if _imports_transport(path, name):
                importers.append(f"{path.relative_to(ROOT)} -> {name}")
    assert importers == [], importers


def test_the_guard_itself_can_fail(tmp_path: Path) -> None:
    """Kill-check: the detector flags a synthetic module-level engine import."""
    bad = "from memoria_vault.engine import api as engine_api\n"
    tree = ast.parse(bad)
    assert isinstance(tree.body[0], ast.ImportFrom)
    probe = tmp_path / "_layering_probe.py"
    probe.write_text(bad, encoding="utf-8")
    assert _module_level_engine_imports(probe) == [1]


def test_try_except_wrapped_engine_import_is_caught(tmp_path: Path) -> None:
    """A module-level import inside try/except still executes at import time.

    Live idiom (with a harmless target) at runtime/rendezvous.py:24-31 and
    runtime/state.py:43-50 — a direct-children-of-tree.body scan would miss an
    engine import shaped like this.
    """
    bad = (
        "try:\n"
        "    from memoria_vault.engine import api as engine_api\n"
        "except ImportError:\n"
        "    engine_api = None\n"
    )
    probe = tmp_path / "_layering_probe.py"
    probe.write_text(bad, encoding="utf-8")
    assert _module_level_engine_imports(probe) == [2]


def test_relative_engine_import_is_caught(tmp_path: Path) -> None:
    """A relative import resolving to the engine package is caught too.

    ``from ...engine import api`` has ``node.module == "engine"``, which does
    not start with "memoria_vault.engine" as plain text — it only resolves to
    the engine package once ``node.level`` is resolved against the probe's own
    package position. Mirrors the depth of a file directly under
    runtime/policy/ (the live relative-import idiom, e.g.
    runtime/policy/decision.py), three packages below src/.
    """
    src_root = tmp_path / "src"
    probe = src_root / "memoria_vault" / "runtime" / "policy" / "probe.py"
    probe.parent.mkdir(parents=True)
    probe.write_text("from ...engine import api\n", encoding="utf-8")
    assert _module_level_engine_imports(probe, root=src_root) == [1]


def test_type_checking_import_is_not_caught(tmp_path: Path) -> None:
    """An import under ``if TYPE_CHECKING:`` must stay uncaught.

    It never executes at runtime, so it is not a real import-time dependency —
    live idiom at runtime/state.py:53-54. Recursing into ``if`` bodies for the
    two shapes above must not start flagging this one.
    """
    probe = tmp_path / "_layering_probe.py"
    probe.write_text(
        "from typing import TYPE_CHECKING\n"
        "\n"
        "if TYPE_CHECKING:\n"
        "    from memoria_vault.engine import api as engine_api\n",
        encoding="utf-8",
    )
    assert _module_level_engine_imports(probe) == []


def test_deferred_import_in_function_body_is_not_caught(tmp_path: Path) -> None:
    """An import inside a function body is not caught (deferred until call time).

    Functions define a new scope, and their body executes only when the
    function is called, not when the module is imported. This is the sanctioned
    idiom for breaking a layering cycle — live usage in eval_dispatch.main()
    and elsewhere. Must stay uncaught.
    """
    probe = tmp_path / "_layering_probe.py"
    probe.write_text(
        "def some_function():\n"
        "    from memoria_vault.engine import api as engine_api\n"
        "    return engine_api\n",
        encoding="utf-8",
    )
    assert _module_level_engine_imports(probe) == []


@pytest.mark.parametrize(
    ("description", "code", "expected_line"),
    [
        (
            "except_handler_body",
            (
                "try:\n"
                "    pass\n"
                "except Exception:\n"
                "    from memoria_vault.engine import api as engine_api\n"
            ),
            4,
        ),
        (
            "try_else_body",
            (
                "try:\n"
                "    pass\n"
                "except Exception:\n"
                "    pass\n"
                "else:\n"
                "    from memoria_vault.engine import api as engine_api\n"
            ),
            6,
        ),
        (
            "try_finally_body",
            (
                "try:\n"
                "    pass\n"
                "except Exception:\n"
                "    pass\n"
                "finally:\n"
                "    from memoria_vault.engine import api as engine_api\n"
            ),
            6,
        ),
        (
            "if_body",
            ("if True:\n    from memoria_vault.engine import api as engine_api\n"),
            2,
        ),
        (
            "if_else_body",
            (
                "if False:\n"
                "    pass\n"
                "else:\n"
                "    from memoria_vault.engine import api as engine_api\n"
            ),
            4,
        ),
        (
            "with_body",
            (
                "from contextlib import nullcontext\n"
                "with nullcontext():\n"
                "    from memoria_vault.engine import api as engine_api\n"
            ),
            3,
        ),
    ],
)
def test_import_time_recursion_arms_are_caught(
    tmp_path: Path, description: str, code: str, expected_line: int
) -> None:
    """Each recursion arm must catch an engine import at its target line.

    Parametrized over all shapes that execute at import time:
    - except-handler bodies
    - try/else bodies
    - try/finally bodies
    - if bodies (when not under TYPE_CHECKING)
    - if/else bodies
    - with bodies

    Each parameter defines a shape, the code to test it, and the expected
    line number where the import is detected. Deleting any recursion arm
    should cause exactly its own case to fail.
    """
    probe = tmp_path / f"_probe_{description}.py"
    probe.write_text(code, encoding="utf-8")
    result = _module_level_engine_imports(probe)
    assert result == [expected_line], (
        f"Failed to catch engine import in {description}. "
        f"Expected line {expected_line}, got {result}."
    )
