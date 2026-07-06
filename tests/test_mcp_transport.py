"""MCP transport contract tests."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from memoria_vault.cli import main
from memoria_vault.runtime import mcp_transport, state
from memoria_vault.runtime.mcp_transport import make_mcp_app
from memoria_vault.runtime.policy.audit import sha256_file


@pytest.fixture
def workspace(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    return workspace


def test_cli_mcp_requires_read_scope(workspace: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["mcp", "--workspace", str(workspace)])
    captured = capsys.readouterr()

    assert rc == 2
    assert "mcp requires at least one --read-scope" in captured.err


@pytest.mark.parametrize(
    ("read_scope", "message"),
    [
        (".", "mcp requires at least one non-root --read-scope"),
        ("/", "mcp requires at least one non-root --read-scope"),
        ("../outside", "path escapes vault root"),
    ],
)
def test_cli_mcp_rejects_root_and_traversal_scope(
    workspace: Path,
    capsys: pytest.CaptureFixture[str],
    read_scope: str,
    message: str,
) -> None:
    rc = main(["mcp", "--workspace", str(workspace), "--read-scope", read_scope])
    captured = capsys.readouterr()

    assert rc == 2
    assert message in captured.err


def test_cli_mcp_passes_scope_and_actor(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_server(workspace_arg: Path, *, read_scope: list[str], actor: str) -> None:
        captured.update({"workspace": workspace_arg, "read_scope": read_scope, "actor": actor})

    monkeypatch.setattr("memoria_vault.runtime.mcp_transport.run_mcp_server", fake_server)

    rc = main(
        [
            "mcp",
            "--workspace",
            str(workspace),
            "--read-scope",
            "notes",
            "--actor",
            "review-agent",
        ]
    )

    assert rc == 0
    assert captured == {
        "workspace": workspace,
        "read_scope": ["notes"],
        "actor": "review-agent",
    }


def test_mcp_app_requires_non_root_read_scope(workspace: Path) -> None:
    pytest.importorskip("mcp")

    with pytest.raises(ValueError, match="mcp requires at least one non-root --read-scope"):
        make_mcp_app(workspace, read_scope=[])
    with pytest.raises(ValueError, match="mcp requires at least one non-root --read-scope"):
        make_mcp_app(workspace, read_scope=["."])
    with pytest.raises(ValueError, match="mcp requires at least one non-root --read-scope"):
        make_mcp_app(workspace, read_scope=["/"])


def test_mcp_tool_roster_is_closed(workspace: Path) -> None:
    pytest.importorskip("mcp")

    app = make_mcp_app(workspace, read_scope=["notes"], actor="agent")

    assert sorted(tool.name for tool in app._tool_manager.list_tools()) == [
        "attention",
        "attention_card",
        "concept",
        "concepts",
        "journal",
        "journal_event",
        "operation_run",
        "operations",
        "request",
        "requests",
        "status",
        "work",
    ]


def test_mcp_public_call_tool_serializes_structured_result(workspace: Path) -> None:
    pytest.importorskip("mcp")
    app = make_mcp_app(workspace, read_scope=["notes"], actor="agent")

    content, structured = asyncio.run(app.call_tool("status", {}))

    assert json.loads(content[0].text)["ok"] is True
    assert structured["ok"] is True
    assert structured["api_version"] == "engine-read-api.v1"


def test_mcp_read_tools_pass_session_scope(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("mcp")
    seen: list[tuple[str, list[str] | None]] = []

    def record(name: str):
        def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            seen.append((name, kwargs.get("read_scope")))
            return {"ok": True}

        return wrapper

    for name in (
        "read_requests",
        "read_request",
        "read_attention",
        "read_attention_card",
        "read_concepts",
        "read_concept",
        "read_work",
        "read_journal",
        "read_journal_event",
    ):
        monkeypatch.setattr(mcp_transport.engine_api, name, record(name))

    app = make_mcp_app(workspace, read_scope=["notes"], actor="agent")
    for tool_name, arguments in {
        "requests": {},
        "request": {"request_id": "r1"},
        "attention": {},
        "attention_card": {"path": "inbox/a.md"},
        "concepts": {},
        "concept": {"target": "notes/a.md"},
        "work": {"work_id": "w1"},
        "journal": {},
        "journal_event": {"event_id": 1},
    }.items():
        _call(app, tool_name, **arguments)

    assert seen == [
        ("read_requests", ["notes"]),
        ("read_request", ["notes"]),
        ("read_attention", ["notes"]),
        ("read_attention_card", ["notes"]),
        ("read_concepts", ["notes"]),
        ("read_concept", ["notes"]),
        ("read_work", ["notes"]),
        ("read_journal", ["notes"]),
        ("read_journal_event", ["notes"]),
    ]


def test_mcp_reads_are_engine_scoped(workspace: Path) -> None:
    pytest.importorskip("mcp")
    tool_error = pytest.importorskip("mcp.server.fastmcp.exceptions").ToolError

    _write_note(workspace, "notes/alpha.md", "Alpha")
    _write_note(workspace, "notes/beta.md", "Beta")
    app = make_mcp_app(workspace, read_scope=["notes/alpha.md"], actor="agent")

    listed = _call(app, "concepts")

    assert [row["path"] for row in listed["concepts"]] == ["notes/alpha.md"]
    with pytest.raises(tool_error, match="target not found"):
        _call(app, "concept", target="notes/beta.md")


def test_mcp_operation_run_uses_request_envelope(workspace: Path) -> None:
    pytest.importorskip("mcp")

    app = make_mcp_app(workspace, read_scope=["notes"], actor="agent")

    response = _call(
        app,
        "operation_run",
        operation_id="create-concept",
        payload={
            "target_path": "notes/mcp.md",
            "content": "---\ntype: note\ntitle: MCP\ntags: []\nlinks: {}\n---\nBody.\n",
            "concept_type": "note",
        },
        idempotency_key="mcp-create",
    )

    assert response["ok"] is True
    with state.connect(workspace) as conn:
        row = conn.execute(
            """
            SELECT operation_id, actor, provenance_json, args_json
            FROM operation_requests
            WHERE request_id = ?
            """,
            ("mcp-create",),
        ).fetchone()
    assert row["operation_id"] == "create-concept"
    assert row["actor"] == "agent"
    assert json.loads(row["provenance_json"]) == {
        "surface": "memoria-mcp",
        "command": "mcp:create-concept",
    }
    assert json.loads(row["args_json"])["target_path"] == "notes/mcp.md"


def _call(app: Any, name: str, **arguments: Any) -> dict[str, Any]:
    return asyncio.run(app._tool_manager.call_tool(name, arguments, convert_result=False))


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
