"""Engine API read-scope contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.engine import api
from memoria_vault.runtime import state
from tests.helpers import init_cli_workspace, write_checked_concept, write_checked_note


@pytest.fixture
def workspace(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    return init_cli_workspace(tmp_path, capsys)


def test_engine_read_scope_filters_and_blocks_concepts(workspace: Path) -> None:
    write_checked_note(workspace, "notes/alpha.md", "Alpha")
    write_checked_note(workspace, "notes/beta.md", "Beta")

    listed = api.read_concepts(workspace, read_scope=["notes/alpha.md"])
    visible = api.read_concept(workspace, "notes/alpha.md", read_scope=["notes/"])

    assert listed["api_version"] == api.READ_API_VERSION
    assert visible["api_version"] == api.READ_API_VERSION
    assert [row["path"] for row in listed["concepts"]] == ["notes/alpha.md"]
    assert visible["path"] == "notes/alpha.md"
    with pytest.raises(FileNotFoundError, match="target not found"):
        api.read_concept(workspace, "notes/beta.md", read_scope=["notes/alpha.md"])


def test_engine_read_concept_refuses_tampered_checked_file(workspace: Path) -> None:
    path = workspace / "notes/alpha.md"
    write_checked_note(workspace, path.relative_to(workspace).as_posix(), "Alpha")
    path.write_text(
        "---\ntype: note\ntitle: Alpha\ntags: []\nlinks: {}\n---\nTampered.\n",
        encoding="utf-8",
    )

    with pytest.raises(PermissionError, match="not consumable until scan runs"):
        api.read_concept(workspace, "notes/alpha.md")
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
    assert json.loads(row["args_json"])["target_path"] == "notes/alpha.md"


def test_engine_read_scope_filters_attention_by_card_or_target(workspace: Path) -> None:
    _write_attention(workspace, "alpha", target="notes/alpha.md")
    _write_attention(workspace, "beta", target="notes/beta.md")

    listed = api.read_attention(workspace, read_scope=["notes/alpha.md"])

    assert [card["path"] for card in listed["attention"]] == ["inbox/alpha.md"]
    with pytest.raises(FileNotFoundError, match="attention projection not found"):
        api.read_attention_card(workspace, "inbox/beta.md", read_scope=["notes/alpha.md"])


def test_engine_attention_read_api_returns_table_and_card_view_specs(workspace: Path) -> None:
    _write_attention(workspace, "alpha", target="notes/alpha.md")
    _write_attention(workspace, "beta", target="notes/beta.md")

    listed = api.read_attention(workspace, read_scope=["notes/alpha.md"])
    shown = api.read_attention_card(workspace, "inbox/alpha.md", read_scope=["notes/alpha.md"])

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
                            "target": "notes/alpha.md",
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


def test_engine_read_slice_returns_project_slice_view(workspace: Path) -> None:
    write_checked_concept(
        workspace,
        "projects/project-alpha/project.md",
        "type: project\ntitle: Alpha project\ntags: []\nlinks: {}\nthesis: notes/thesis.md\n",
        concept_type="project",
    )
    write_checked_concept(
        workspace,
        "notes/thesis.md",
        "type: note\nid: 01ARZ3NDEKTSV4RRFFQ69G5FB1\ntitle: Thesis\ntags: []\nlinks: {}\n",
    )
    write_checked_concept(
        workspace,
        "notes/support.md",
        "type: note\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FB2\n"
        "title: Support\n"
        "tags: []\n"
        "links:\n"
        "  supports:\n"
        "    - notes/thesis.md\n",
    )
    outline = workspace / "projects/project-alpha/outline.md"
    outline.write_text(
        "- 01ARZ3NDEKTSV4RRFFQ69G5FB2 -- Support first\n"
        "- 01ARZ3NDEKTSV4RRFFQ69G5FB1 -- Thesis second\n",
        encoding="utf-8",
    )

    result = api.read_slice(workspace, "project-alpha")

    assert result["api_version"] == api.READ_API_VERSION
    assert [member["path"] for member in result["slice"]["members"]] == [
        "notes/support.md",
        "notes/thesis.md",
    ]
    block = result["view"]["blocks"][0]
    assert block["kind"] == "table"
    assert block["refs"] == ["notes/support.md", "notes/thesis.md"]
    assert block["rows"][0]["cells"]["reasoning"] == "Support first"


def test_engine_compose_and_read_draft_returns_project_draft_view(workspace: Path) -> None:
    write_checked_concept(
        workspace,
        "projects/project-alpha/project.md",
        "type: project\ntitle: Alpha project\ntags: []\nlinks: {}\nthesis: notes/thesis.md\n",
        concept_type="project",
    )
    write_checked_concept(
        workspace,
        "notes/thesis.md",
        "type: note\nid: 01ARZ3NDEKTSV4RRFFQ69G5FB1\ntitle: Thesis\ntags: []\nlinks: {}\n",
    )
    outline = workspace / "projects/project-alpha/outline.md"
    outline.write_text("- 01ARZ3NDEKTSV4RRFFQ69G5FB1 -- Draft thesis\n", encoding="utf-8")

    composed = api.compose_draft(
        workspace,
        "project-alpha",
        token_budget=400,
        idempotency_key="compose-draft",
    )
    verified = api.verify_draft(
        workspace,
        "project-alpha",
        idempotency_key="verify-draft",
    )
    readback = api.read_draft(workspace, "project-alpha")

    assert composed["ok"] is True
    assert composed["result"]["draft_path"] == "projects/project-alpha/draft.md"
    assert composed["result"]["evidence_set_count"] == 1
    assert verified["ok"] is True
    assert verified["result"]["ready"] is False
    assert readback["api_version"] == api.READ_API_VERSION
    assert "%%ev:" in readback["draft"]["content"]
    assert readback["view"]["kind"] == "project-draft"
    assert readback["view"]["blocks"][0]["rows"][0]["cells"]["state"] == "evidence-incomplete"


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
