"""Loopback HTTP transport tests."""

from __future__ import annotations

import json
from http import HTTPStatus
from pathlib import Path

import pytest

from memoria_vault.cli import main
from memoria_vault.engine.surface_contract import http_routes
from memoria_vault.runtime import state
from memoria_vault.runtime.http_transport import PayloadTooLarge, _dispatch, is_authorized
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
    monkeypatch.setattr("memoria_vault.runtime.http_transport.make_http_server", fake_server)

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

    assert (unknown, unknown_status) == ({"ok": False, "error": "not found"}, HTTPStatus.NOT_FOUND)
    assert (wrong_method, wrong_status) == (
        {"ok": False, "error": "method not allowed"},
        HTTPStatus.METHOD_NOT_ALLOWED,
    )
    assert (wrong_write_method, wrong_write_status) == (
        {"ok": False, "error": "method not allowed"},
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
    assert row["actor"] == "agent"
    assert json.loads(row["provenance_json"]) == {
        "surface": "memoria-http",
        "command": "http:create-concept",
    }
    assert json.loads(row["args_json"])["target_path"] == "notes/http.md"


def test_http_transport_unknown_write_does_not_create_request(workspace: Path) -> None:
    response, http_status = _dispatch(
        workspace,
        "POST",
        "/raw-sql",
        lambda: {"operation_id": "answer-query"},
    )

    assert http_status == HTTPStatus.NOT_FOUND
    assert response == {"ok": False, "error": "not found"}
    with state.connect(workspace) as conn:
        count = conn.execute("SELECT COUNT(*) FROM operation_requests").fetchone()[0]
    assert count == 0


def _raise(exc: Exception) -> None:
    raise exc


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
