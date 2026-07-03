"""Loopback HTTP transport tests."""

from __future__ import annotations

import json
from http import HTTPStatus
from pathlib import Path

import pytest

from memoria_vault.cli import main
from memoria_vault.runtime import state
from memoria_vault.runtime.http_transport import _dispatch, is_authorized
from memoria_vault.runtime.jsonl import iter_jsonl


@pytest.fixture
def workspace(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    return workspace


def test_serve_http_once_reports_loopback_token(
    workspace: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeServer:
        server_address = ("127.0.0.1", 43210)

        def server_close(self) -> None:
            return

    monkeypatch.setenv("MEMORIA_HTTP_TOKEN", "test-token")
    monkeypatch.setattr(
        "memoria_vault.runtime.http_transport.make_http_server",
        lambda *args, **kwargs: FakeServer(),
    )

    rc = main(
        [
            "serve",
            "--workspace",
            str(workspace),
            "--http",
            "--port",
            "0",
            "--once",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output == {
        "ok": True,
        "token": None,
        "token_source": "env",
        "url": "http://127.0.0.1:43210",
    }


def test_serve_http_rejects_non_loopback_host(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "serve",
            "--workspace",
            str(workspace),
            "--http",
            "--host",
            "0.0.0.0",
            "--once",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output == {"ok": False, "error": "serve --http only binds loopback hosts"}


def test_http_transport_authorization_helper() -> None:
    assert is_authorized("Bearer test-token", "test-token")
    assert not is_authorized(None, "test-token")
    assert not is_authorized("Bearer other", "test-token")


def test_http_transport_reads_status(workspace: Path) -> None:
    status, http_status = _dispatch(workspace, "GET", "/status", dict)

    assert http_status == HTTPStatus.OK
    assert status["ok"] is True
    assert status["db"] == ".memoria/memoria.sqlite"
    assert status["workspace"] == str(workspace)


def test_http_transport_operation_run_uses_request_envelope(workspace: Path) -> None:
    response, http_status = _dispatch(
        workspace,
        "POST",
        "/operation/run",
        lambda: {
            "operation_id": "create-concept",
            "payload": {
                "target_path": "knowledge/notes/http.md",
                "content": ("---\ntype: note\ntitle: HTTP note\ntags: []\nlinks: {}\n---\nBody.\n"),
                "concept_type": "note",
            },
            "idempotency_key": "http-create",
            "actor": "agent",
        },
    )

    assert http_status == HTTPStatus.OK
    assert response["ok"] is True
    assert (workspace / "journal/memoria-http.jsonl").exists()
    assert [event["event"] for event in iter_jsonl(workspace / "journal/memoria-http.jsonl")] == [
        "derived"
    ]
    with state.connect(workspace) as conn:
        row = conn.execute(
            """
            SELECT operation_id, actor, provenance_json, args_json
            FROM operation_requests
            WHERE request_id = ?
            """,
            ("http-create",),
        ).fetchone()
    assert row["operation_id"] == "create-concept"
    assert row["actor"] == "agent"
    assert json.loads(row["provenance_json"]) == {
        "surface": "memoria-http",
        "command": "http:create-concept",
    }
    assert json.loads(row["args_json"])["target_path"] == "knowledge/notes/http.md"


def test_http_transport_unknown_write_does_not_create_request(workspace: Path) -> None:
    response, http_status = _dispatch(
        workspace,
        "POST",
        "/raw-sql",
        lambda: {"operation_id": "answer-query"},
    )

    assert http_status == HTTPStatus.OK
    assert response == {"ok": False, "error": "not found"}
    with state.connect(workspace) as conn:
        count = conn.execute("SELECT COUNT(*) FROM operation_requests").fetchone()[0]
    assert count == 0
