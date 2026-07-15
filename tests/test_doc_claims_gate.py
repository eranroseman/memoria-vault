"""Tests for the doc-claims gate (CLI paths and operation ids cited in docs)."""

from __future__ import annotations

from pathlib import Path

from scripts.checks import doc_claims_gate as gate

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
