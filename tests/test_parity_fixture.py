"""Alpha.14 user-facing parity fixture."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.cli import _build_parser, main
from memoria_vault.runtime import state
from memoria_vault.runtime.vaultio import read_frontmatter

ADAPTER_ENV_VARS = (
    "OBSIDIAN_API_KEY",
    "OBSIDIAN_MCP_PORT",
    "OBSIDIAN_MCP_SSL_VERIFY",
    "ZOTERO_API_KEY",
    "HERMES_HOME",
)


def test_palette_actions_have_standalone_cli_parity(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in ADAPTER_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    _write_attention_fixture(workspace)
    _write_project_argument_fixture(workspace)

    assert (
        main(
            [
                "note",
                "capture",
                "--workspace",
                str(workspace),
                "--title",
                "Palette note",
                "--body",
                "Captured without an adapter.",
                "--json",
            ]
        )
        == 0
    )
    note = json.loads(capsys.readouterr().out)
    assert read_frontmatter(workspace / note["note_path"])["check_status"] == "unchecked"

    assert main(["attention", "list", "--workspace", str(workspace), "--json"]) == 0
    attention = json.loads(capsys.readouterr().out)
    assert [row["path"] for row in attention["attention"]] == [
        "inbox/dismiss-card.md",
        "inbox/resolve-card.md",
    ]

    assert (
        main(
            [
                "project",
                "trace",
                "--workspace",
                str(workspace),
                "project-alpha",
                "--json",
                "--idempotency-key",
                "palette-trace",
            ]
        )
        == 0
    )
    trace = json.loads(capsys.readouterr().out)
    assert trace["result"]["project_path"] == "knowledge/projects/project-alpha.md"
    assert trace["result"]["relation_count"] == 1

    assert (
        main(
            [
                "attention",
                "resolve",
                "--workspace",
                str(workspace),
                "inbox/resolve-card.md",
                "--outcome",
                "resolved",
                "--json",
                "--idempotency-key",
                "palette-resolve",
            ]
        )
        == 0
    )
    resolved = json.loads(capsys.readouterr().out)
    assert resolved["result"]["resolution"]["outcome"] == "resolved"

    assert (
        main(
            [
                "attention",
                "resolve",
                "--workspace",
                str(workspace),
                "inbox/dismiss-card.md",
                "--outcome",
                "dismissed",
                "--json",
                "--idempotency-key",
                "palette-dismiss",
            ]
        )
        == 0
    )
    dismissed = json.loads(capsys.readouterr().out)
    assert dismissed["result"]["resolution"]["outcome"] == "dismissed"

    with state.connect(workspace) as conn:
        rows = conn.execute(
            """
            SELECT request_id, operation_id
            FROM operation_requests
            WHERE request_id IN ('palette-trace', 'palette-resolve', 'palette-dismiss')
            ORDER BY request_id
            """
        ).fetchall()
    assert [(row["request_id"], row["operation_id"]) for row in rows] == [
        ("palette-dismiss", "resolve-attention"),
        ("palette-resolve", "resolve-attention"),
        ("palette-trace", "analyze-project-argument"),
    ]


def test_startup_shell_restore_is_adapter_only_not_core_cli() -> None:
    surface = _cli_command_surface()

    assert "memoria restore shell" not in surface
    assert "memoria workspace run" in surface
    assert "memoria workspace scan" in surface


def test_operation_parity_is_manifest_derived_and_dispatchable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    manifests = _operation_manifest_rows(workspace)
    manifest_ids = {row["operation_id"] for row in manifests}
    assert manifest_ids
    assert [row for row in manifests if row["adapter_only"] or row["dropped"]] == []

    assert main(["operation", "list", "--workspace", str(workspace), "--json"]) == 0
    listed = json.loads(capsys.readouterr().out)
    listed_ids = {row["operation_id"] for row in listed["operations"]}
    assert listed_ids == manifest_ids

    unsupported: dict[str, str] = {}
    for operation_id in sorted(manifest_ids):
        rc = main(
            [
                "operation",
                "run",
                "--workspace",
                str(workspace),
                operation_id,
                "--payload-json",
                "{}",
                "--json",
                "--idempotency-key",
                f"parity-{operation_id}",
            ]
        )
        output = json.loads(capsys.readouterr().out)
        error = str((output.get("result") or {}).get("error") or output.get("error") or "")
        if rc != 0 and "unsupported operation" in error:
            unsupported[operation_id] = error

    assert unsupported == {}


def _cli_command_surface() -> set[str]:
    parser = _build_parser()
    command_action = next(
        action for action in parser._actions if getattr(action, "dest", None) == "command"
    )
    commands: set[str] = set()
    for name, subparser in command_action.choices.items():
        child_action = next(
            (action for action in subparser._actions if getattr(action, "choices", None)),
            None,
        )
        if child_action is None:
            commands.add(f"memoria {name}")
            continue
        if not getattr(child_action, "required", False):
            commands.add(f"memoria {name}")
        commands.update(f"memoria {name} {child}" for child in child_action.choices)
    return commands


def _operation_manifest_rows(workspace: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for path in sorted((workspace / "capabilities/operations").glob("*.md")):
        frontmatter = read_frontmatter(path)
        if frontmatter.get("type") != "operation":
            continue
        rows.append(
            {
                "operation_id": str(frontmatter.get("operation_id") or path.stem),
                "adapter_only": bool(frontmatter.get("adapter_only")),
                "dropped": bool(frontmatter.get("dropped")),
                "drop_reason": str(frontmatter.get("drop_reason") or ""),
            }
        )
    return rows


def _write_attention_fixture(workspace: Path) -> None:
    inbox = workspace / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    for name, title in (
        ("dismiss-card", "Dismiss card"),
        ("resolve-card", "Resolve card"),
    ):
        (inbox / f"{name}.md").write_text(
            "---\n"
            f"title: {title}\n"
            "projection: attention\n"
            "attention_kind: flag\n"
            "attention_status: open\n"
            "target: knowledge/notes/palette.md\n"
            "---\n"
            "# Attention\n\nPalette parity fixture.\n",
            encoding="utf-8",
        )


def _write_project_argument_fixture(workspace: Path) -> None:
    project = workspace / "knowledge/projects/project-alpha.md"
    project.parent.mkdir(parents=True, exist_ok=True)
    project.write_text(
        "---\n"
        "type: project\n"
        "check_status: checked\n"
        "title: Alpha project\n"
        "thesis: knowledge/notes/thesis.md\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    thesis = workspace / "knowledge/notes/thesis.md"
    support = workspace / "knowledge/notes/support.md"
    thesis.parent.mkdir(parents=True, exist_ok=True)
    thesis.write_text(
        "---\ntype: note\ncheck_status: checked\ntitle: Thesis\nstatus: accepted\n---\nThesis.\n",
        encoding="utf-8",
    )
    support.write_text(
        "---\n"
        "type: note\n"
        "check_status: checked\n"
        "title: Support\n"
        "status: accepted\n"
        "links:\n"
        "  supports:\n"
        "    - knowledge/notes/thesis.md\n"
        "---\n"
        "Support.\n",
        encoding="utf-8",
    )
