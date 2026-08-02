"""Every dotted memoria_vault literal in the suite resolves to a live object.

Monkeypatch targets and sys.modules keys are strings; after a move they fail
late (or pass while patching a key nothing imports). This resolves each one at
static-test time: longest importable module prefix, then the attribute tail.
"""

from __future__ import annotations

import ast
import importlib
import re
from importlib.util import find_spec
from pathlib import Path

import pytest

from tests.paths import ROOT

pytestmark = pytest.mark.static

_DOTTED = re.compile(r"^memoria_vault(\.[A-Za-z_][A-Za-z0-9_]*)+$")

# Literals that intentionally name absent objects (e.g. a negative test that
# proves something retired stays retired). Every entry carries a reason.
ALLOWLIST: dict[str, str] = {}


def _call_string_literals(path: Path) -> list[tuple[str, int]]:
    """Dotted literals appearing as arguments in call expressions.

    Restricting to calls skips docstrings and prose while catching every
    monkeypatch.setattr / setitem / patch-style target.
    """
    found: list[tuple[str, int]] = []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for arg in [*node.args, *(kw.value for kw in node.keywords)]:
            if (
                isinstance(arg, ast.Constant)
                and isinstance(arg.value, str)
                and _DOTTED.match(arg.value)
            ):
                found.append((arg.value, arg.lineno))
    return found


def _unresolvable(literal: str) -> str | None:
    """None if the literal names a live module or module attribute; else why."""
    parts = literal.split(".")
    for cut in range(len(parts), 0, -1):
        module_name = ".".join(parts[:cut])
        try:
            if find_spec(module_name) is None:
                continue
        except (ImportError, ModuleNotFoundError):
            continue
        obj = importlib.import_module(module_name)
        for attr in parts[cut:]:
            if not hasattr(obj, attr):
                return f"{module_name!r} has no attribute chain {'.'.join(parts[cut:])!r}"
            obj = getattr(obj, attr)
        return None
    return "no importable module prefix"


def test_every_dotted_literal_resolves() -> None:
    failures = []
    for path in sorted((ROOT / "tests").rglob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        for literal, lineno in _call_string_literals(path):
            if literal in ALLOWLIST:
                continue
            why = _unresolvable(literal)
            if why is not None:
                failures.append(f"{path.name}:{lineno}: {literal} -- {why}")
    assert failures == [], "\n".join(failures)


def test_the_resolver_flags_a_missing_module() -> None:
    assert _unresolvable("memoria_vault.runtime.no_such_module.attr") is not None


def test_the_resolver_flags_a_missing_attribute() -> None:
    assert _unresolvable("memoria_vault.runtime.state.no_such_symbol") is not None


def test_the_resolver_accepts_a_live_module_and_attribute() -> None:
    assert _unresolvable("memoria_vault.runtime.state") is None
    assert _unresolvable("memoria_vault.runtime.state.SCHEMA_VERSION") is None


def test_the_collector_sees_call_arguments_not_docstrings() -> None:
    """A dotted literal sitting in a docstring must not be collected.

    The docstring text below is deliberately a *pure* dotted literal (no
    surrounding prose): with prose attached, ``_DOTTED``'s ``^...$`` anchors
    would already reject the whole string on their own, and the test would
    pass whether or not the collector actually restricted itself to call
    arguments -- a vacuous check. With no prose, a collector that walked
    every string constant (not just ``ast.Call`` arguments) would wrongly
    flag this docstring too, so this probe actually exercises the
    restriction the test's name claims.
    """
    src = (
        '"""memoria_vault.runtime.in_a_docstring"""\n'
        'monkeypatch.setitem(sys.modules, "memoria_vault.runtime.telemetry", None)\n'
    )
    probe = Path(__file__).parent / "_dotted_probe.py"
    probe.write_text(src, encoding="utf-8")
    try:
        literals = [text for text, _ in _call_string_literals(probe)]
    finally:
        probe.unlink()
    assert literals == ["memoria_vault.runtime.telemetry"]
