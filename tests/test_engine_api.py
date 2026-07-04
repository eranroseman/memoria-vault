"""Engine API read-scope contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.cli import main
from memoria_vault.engine import api
from memoria_vault.runtime import state
from memoria_vault.runtime.policy.audit import sha256_file


@pytest.fixture
def workspace(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    return workspace


def test_engine_read_scope_filters_and_blocks_concepts(workspace: Path) -> None:
    _write_note(workspace, "knowledge/notes/alpha.md", "Alpha")
    _write_note(workspace, "knowledge/notes/beta.md", "Beta")

    listed = api.read_concepts(workspace, read_scope=["knowledge/notes/alpha.md"])
    visible = api.read_concept(
        workspace, "knowledge/notes/alpha.md", read_scope=["knowledge/notes/"]
    )

    assert listed["api_version"] == api.READ_API_VERSION
    assert visible["api_version"] == api.READ_API_VERSION
    assert [row["path"] for row in listed["concepts"]] == ["knowledge/notes/alpha.md"]
    assert visible["path"] == "knowledge/notes/alpha.md"
    with pytest.raises(FileNotFoundError, match="target not found"):
        api.read_concept(
            workspace, "knowledge/notes/beta.md", read_scope=["knowledge/notes/alpha.md"]
        )


def test_engine_read_concept_refuses_tampered_checked_file(workspace: Path) -> None:
    path = workspace / "knowledge/notes/alpha.md"
    _write_note(workspace, path.relative_to(workspace).as_posix(), "Alpha")
    path.write_text(
        "---\ntype: note\ntitle: Alpha\ntags: []\nlinks: {}\n---\nTampered.\n",
        encoding="utf-8",
    )

    with pytest.raises(PermissionError, match="not consumable until scan runs"):
        api.read_concept(workspace, "knowledge/notes/alpha.md")
    with state.connect(workspace) as conn:
        row = conn.execute(
            """
            SELECT operation_id, status, schedule_id, args_json
            FROM operation_requests
            WHERE operation_id = 'observe-pi-edits'
            """
        ).fetchone()
    assert row is not None
    assert row["status"] == "pending"
    assert row["schedule_id"] == "read-guard"
    assert row["operation_id"] == "observe-pi-edits"
    assert json.loads(row["args_json"])["target_path"] == "knowledge/notes/alpha.md"


def test_engine_read_scope_filters_attention_by_card_or_target(workspace: Path) -> None:
    _write_attention(workspace, "alpha", target="knowledge/notes/alpha.md")
    _write_attention(workspace, "beta", target="knowledge/notes/beta.md")

    listed = api.read_attention(workspace, read_scope=["knowledge/notes/alpha.md"])

    assert [card["path"] for card in listed["attention"]] == ["inbox/alpha.md"]
    with pytest.raises(FileNotFoundError, match="attention projection not found"):
        api.read_attention_card(workspace, "inbox/beta.md", read_scope=["knowledge/notes/alpha.md"])


def test_engine_attention_read_api_returns_table_and_card_view_specs(workspace: Path) -> None:
    _write_attention(workspace, "alpha", target="knowledge/notes/alpha.md")
    _write_attention(workspace, "beta", target="knowledge/notes/beta.md")

    listed = api.read_attention(workspace, read_scope=["knowledge/notes/alpha.md"])
    shown = api.read_attention_card(
        workspace, "inbox/alpha.md", read_scope=["knowledge/notes/alpha.md"]
    )

    assert listed["view"] == {
        "version": "view-spec.v1",
        "kind": "attention",
        "blocks": [
            {
                "id": "attention-table",
                "kind": "table",
                "title": "Attention",
                "check_status": "unchecked",
                "refs": ["inbox/alpha.md"],
                "columns": ["title", "kind", "status", "target"],
                "rows": [
                    {
                        "ref": "inbox/alpha.md",
                        "check_status": "unchecked",
                        "cells": {
                            "title": "alpha",
                            "kind": "gap",
                            "status": "open",
                            "target": "knowledge/notes/alpha.md",
                        },
                    }
                ],
            }
        ],
    }
    card = shown["view"]["blocks"][0]
    assert card["kind"] == "card"
    assert card["refs"] == ["inbox/alpha.md"]
    assert card["body_data"] == {"kind": "untrusted_text", "text": "Review.\n"}
    assert "body" not in card


def test_engine_read_scope_filters_and_blocks_requests(workspace: Path) -> None:
    alpha = api.write_new_concept(
        workspace,
        "note",
        "Scoped Alpha",
        body="Alpha body.",
        tags=[],
        extra={},
        idempotency_key="create-alpha",
    )
    api.write_new_concept(
        workspace,
        "note",
        "Scoped Beta",
        body="Beta body.",
        tags=[],
        extra={},
        idempotency_key="create-beta",
    )

    listed = api.read_requests(workspace, read_scope=[alpha["path"]])

    assert [row["request_id"] for row in listed["requests"]] == ["create-alpha"]
    with pytest.raises(FileNotFoundError, match="request not found"):
        api.read_request(workspace, "create-beta", read_scope=[alpha["path"]])


def _write_note(workspace: Path, rel: str, title: str) -> None:
    path = workspace / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ntype: note\ntitle: {title}\ntags: []\nlinks: {{}}\n---\nBody.\n")
    state.record_observed_file_edit(
        workspace,
        output_id=rel,
        concept_type="note",
        output_sha256=sha256_file(path),
    )
    state.set_concept_verdict(workspace, rel, "checked")


def _write_attention(workspace: Path, name: str, *, target: str) -> None:
    path = workspace / "inbox" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "projection: attention",
                f"title: {name}",
                "attention_kind: gap",
                "attention_status: open",
                "routing_class: ask",
                f"target: {target}",
                "---",
                "Review.",
                "",
            ]
        ),
        encoding="utf-8",
    )
