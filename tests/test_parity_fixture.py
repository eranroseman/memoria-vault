"""User-facing parity fixture."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.cli import main
from memoria_vault.runtime import state
from memoria_vault.runtime.capabilities import render_capability_index
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.cli_test_helpers import _cli_command_surface
from tests.helpers import mark_file_status

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
                "new",
                "note",
                "Palette note",
                "--workspace",
                str(workspace),
                "--body",
                "Captured without an adapter.",
                "--json",
            ]
        )
        == 0
    )
    note = json.loads(capsys.readouterr().out)
    assert "check_status" not in read_frontmatter(workspace / note["path"])
    assert state.concept_check_status(workspace, note["path"]) == "unchecked"

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
    assert trace["result"]["project_path"] == "projects/project-alpha/project.md"
    assert trace["result"]["relation_count"] == 1

    assert (
        main(
            [
                "attention",
                "resolve",
                "--workspace",
                str(workspace),
                "inbox/resolve-card.md",
                "--apply",
                "--json",
                "--idempotency-key",
                "palette-resolve",
            ]
        )
        == 0
    )
    resolved = json.loads(capsys.readouterr().out)
    assert resolved["result"]["resolution"]["outcome"] == "apply"
    assert resolved["result"]["resolution"]["routing_class"] == "ask"

    assert (
        main(
            [
                "attention",
                "resolve",
                "--workspace",
                str(workspace),
                "inbox/dismiss-card.md",
                "--reject",
                "--json",
                "--idempotency-key",
                "palette-reject",
            ]
        )
        == 0
    )
    rejected = json.loads(capsys.readouterr().out)
    assert rejected["result"]["resolution"]["outcome"] == "reject"
    assert rejected["result"]["resolution"]["routing_class"] == "ask"

    with state.connect(workspace) as conn:
        rows = conn.execute(
            """
            SELECT request_id, operation_id
            FROM operation_requests
            WHERE request_id IN ('palette-trace', 'palette-resolve', 'palette-reject')
            ORDER BY request_id
            """
        ).fetchall()
    assert [(row["request_id"], row["operation_id"]) for row in rows] == [
        ("palette-reject", "resolve-attention"),
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


def _operation_manifest_rows(workspace: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for frontmatter in json.loads(render_capability_index(workspace))["capabilities"]:
        if frontmatter.get("type") != "operation":
            continue
        rows.append(
            {
                "operation_id": str(frontmatter.get("operation_id") or frontmatter["id"]),
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
            "routing_class: ask\n"
            "target: notes/palette.md\n"
            "---\n"
            "# Attention\n\nPalette parity fixture.\n",
            encoding="utf-8",
        )


def _write_project_argument_fixture(workspace: Path) -> None:
    project = workspace / "projects/project-alpha/project.md"
    project.parent.mkdir(parents=True, exist_ok=True)
    project.write_text(
        "---\n"
        "type: project\n"
        "title: Alpha project\n"
        "tags: []\n"
        "links: {}\n"
        "thesis: notes/thesis.md\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "projects/project-alpha/project.md", "project")
    thesis = workspace / "notes/thesis.md"
    support = workspace / "notes/support.md"
    thesis.parent.mkdir(parents=True, exist_ok=True)
    thesis.write_text(
        "---\ntype: note\ntitle: Thesis\ntags: []\nlinks: {}\nstatus: accepted\n---\nThesis.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "notes/thesis.md", "note")
    support.write_text(
        "---\n"
        "type: note\n"
        "title: Support\n"
        "tags: []\n"
        "status: accepted\n"
        "links:\n"
        "  supports:\n"
        "    - notes/thesis.md\n"
        "---\n"
        "Support.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "notes/support.md", "note")
