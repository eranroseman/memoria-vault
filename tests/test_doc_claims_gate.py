"""Tests for the doc-claims gate (CLI paths and operation ids cited in docs)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from scripts.checks import doc_claims_gate as gate

pytestmark = pytest.mark.static

_MINIMAL_CLI = '''
"""Minimal fixture CLI for doc_claims_gate tests."""
from __future__ import annotations

import argparse


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="memoria")
    sub = parser.add_subparsers(dest="command", required=True)
    project = sub.add_parser("project")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    project_sub.add_parser("gaps")
    project_sub.add_parser("trace")
    return parser
'''


def _init_fixture_repo(root: Path) -> None:
    cli_dir = root / "src/memoria_vault"
    cli_dir.mkdir(parents=True)
    (cli_dir / "__init__.py").write_text("", encoding="utf-8")
    (cli_dir / "cli.py").write_text(_MINIMAL_CLI, encoding="utf-8")

    operations_dir = root / "src/memoria_vault/product/capabilities/operations"
    operations_dir.mkdir(parents=True)
    (operations_dir / "capture-source.md").write_text(
        "---\noperation_id: capture-source\n---\n", encoding="utf-8"
    )

    (root / "docs").mkdir()


def test_reading_the_cli_surface_leaves_sys_path_as_it_found_it(tmp_path: Path) -> None:
    """The stub package these fixtures build must not outlive the call that imports it.

    `_init_fixture_repo` writes a `memoria_vault` with one module and no
    submodules. This process would never notice it left on `sys.path` -- the real
    package is already in `sys.modules` -- but every one of these tests prepends
    another stub, and a process spawned later in the same pytest worker starts
    clean, resolves `memoria_vault` to a stub, and dies on a missing submodule
    with no signal beyond a queue timeout. That is #1613: a red `verify` on an
    unrelated PR, reproducing only when the two files land in one worker.
    """
    _init_fixture_repo(tmp_path)
    before = list(sys.path)

    gate._load_cli_paths(tmp_path)

    assert sys.path == before


def test_flags_a_cli_path_and_operation_id_that_do_not_exist(tmp_path: Path) -> None:
    _init_fixture_repo(tmp_path)
    (tmp_path / "docs/fake.md").write_text(
        "Run `memoria project frobnicate` to do the thing.\n"
        "Worker operation `capture-nonexistent-source` stages the row.\n",
        encoding="utf-8",
    )

    violations = gate.find_violations(tmp_path)

    assert violations == [
        gate.Violation("docs/fake.md", 1, "cli-path", "memoria project frobnicate"),
        gate.Violation("docs/fake.md", 2, "operation-id", "capture-nonexistent-source"),
    ]


def test_passes_clean_on_real_cli_paths_and_operation_ids(tmp_path: Path) -> None:
    _init_fixture_repo(tmp_path)
    (tmp_path / "docs/real.md").write_text(
        "Run `memoria project gaps` or `memoria project trace`.\n"
        "Worker operation `capture-source` stages the row.\n",
        encoding="utf-8",
    )

    assert gate.find_violations(tmp_path) == []


def test_a_hyphenated_token_not_immediately_after_operation_is_not_a_claim(tmp_path: Path) -> None:
    _init_fixture_repo(tmp_path)
    # "operation" appears earlier in the sentence, but the backticked token
    # right before it is a check/event name, not an operation-id citation --
    # this must not false-positive (the bug this gate previously had).
    (tmp_path / "docs/other.md").write_text(
        "Records a committed `not-an-operation-id` journal event during the operation run.\n",
        encoding="utf-8",
    )

    assert gate.find_violations(tmp_path) == []


def test_skips_docs_superpowers_and_design_history_archive(tmp_path: Path) -> None:
    _init_fixture_repo(tmp_path)
    (tmp_path / "docs/superpowers").mkdir()
    (tmp_path / "docs/superpowers/scratch.md").write_text(
        "Run `memoria project frobnicate`.\n", encoding="utf-8"
    )

    assert gate.find_violations(tmp_path) == []


_CLI_DOC = """## Complete command roster

This roster mirrors the live argparse tree:

- `memoria project gaps`
- `memoria project trace`

## Next section
"""

_OPERATIONS_DOC = """## Operation manifest roster

Package-owned operation manifests currently ship these operation IDs:

- `capture-source`

## Detailed action catalogs
"""


def _write_roster_docs(
    root: Path, cli_doc: str = _CLI_DOC, operations_doc: str = _OPERATIONS_DOC
) -> None:
    docs_dir = root / "docs/reference/commands-and-transports"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "cli.md").write_text(cli_doc, encoding="utf-8")
    (docs_dir / "system-actions.md").write_text(operations_doc, encoding="utf-8")


def test_matching_rosters_are_clean(tmp_path: Path) -> None:
    _init_fixture_repo(tmp_path)
    _write_roster_docs(tmp_path)

    assert gate.roster_drift_errors(tmp_path) == []


def test_missing_roster_entries_fail_in_both_surfaces(tmp_path: Path) -> None:
    _init_fixture_repo(tmp_path)
    _write_roster_docs(
        tmp_path,
        cli_doc=_CLI_DOC.replace("- `memoria project trace`\n", ""),
        operations_doc=_OPERATIONS_DOC.replace("- `capture-source`", "- `capture-other`"),
    )

    assert gate.roster_drift_errors(tmp_path) == [
        "docs/reference/commands-and-transports/cli.md: roster is missing `memoria project trace`",
        "docs/reference/commands-and-transports/system-actions.md: roster is missing `capture-source`",
        "docs/reference/commands-and-transports/system-actions.md: roster lists `capture-other`, which no shipped manifest declares",
    ]


def test_stale_cli_roster_entry_fails(tmp_path: Path) -> None:
    _init_fixture_repo(tmp_path)
    _write_roster_docs(
        tmp_path,
        cli_doc=_CLI_DOC.replace(
            "- `memoria project trace`", "- `memoria project trace`\n- `memoria project frobnicate`"
        ),
    )

    assert gate.roster_drift_errors(tmp_path) == [
        "docs/reference/commands-and-transports/cli.md: roster lists `memoria project frobnicate`, "
        "which the argparse tree does not run",
    ]
