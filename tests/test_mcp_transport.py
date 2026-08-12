"""MCP transport contract tests."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from memoria_vault.cli import main
from memoria_vault.engine import api as engine_api
from memoria_vault.engine.empirical_events import READ_EVENT_SCHEMA
from memoria_vault.engine.surface_contract import actions_by_id
from memoria_vault.runtime import mcp_transport, retrieval_pipeline, state, worker
from memoria_vault.runtime.attention.inbox import write_finding
from memoria_vault.runtime.mcp_transport import make_mcp_app
from tests.helpers import init_cli_workspace, write_checked_note

pytestmark = pytest.mark.contract


@pytest.fixture
def workspace(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    return init_cli_workspace(tmp_path, capsys)


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


def test_cli_mcp_passes_scope_and_agent_identity(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, Any] = {}

    def fake_server(workspace_arg: Path, *, read_scope: list[str], agent_identity: str) -> None:
        captured.update(
            {
                "workspace": workspace_arg,
                "read_scope": read_scope,
                "agent_identity": agent_identity,
            }
        )

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
        "agent_identity": "review-agent",
    }


def test_mcp_app_requires_non_root_read_scope(workspace: Path) -> None:
    with pytest.raises(ValueError, match="mcp requires at least one non-root --read-scope"):
        make_mcp_app(workspace, read_scope=[])
    with pytest.raises(ValueError, match="mcp requires at least one non-root --read-scope"):
        make_mcp_app(workspace, read_scope=["."])
    with pytest.raises(ValueError, match="mcp requires at least one non-root --read-scope"):
        make_mcp_app(workspace, read_scope=["/"])


def test_mcp_tool_roster_is_closed(workspace: Path) -> None:
    app = make_mcp_app(workspace, read_scope=["notes"], agent_identity="agent")

    assert sorted(tool.name for tool in _list_tools(app)) == [
        "attention",
        "attention_card",
        "concept",
        "concepts",
        "exploration",
        "journal",
        "journal_event",
        "operation_run",
        "operations",
        "project_draft",
        "project_slice",
        "request",
        "requests",
        "status",
        "work",
    ]


def test_mcp_tool_descriptions_match_surface_contract(workspace: Path) -> None:
    app = make_mcp_app(workspace, read_scope=["notes"], agent_identity="agent")
    actions = actions_by_id()
    tools = {tool.name: tool for tool in _list_tools(app)}

    for action in actions.values():
        mcp = action.get("mcp")
        if mcp:
            assert tools[mcp["tool"]].description == action["summary"]


def _normalized_row_params(params: dict[str, Any]) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for name, spec in params.items():
        entry: dict[str, Any] = {"type": str(spec["type"])}
        if spec.get("required"):
            entry["required"] = True
        else:
            entry["default"] = spec.get("default")
        normalized[name] = entry
    return normalized


def _normalized_tool_schema(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    required = set(schema.get("required") or [])
    normalized: dict[str, dict[str, Any]] = {}
    for name, prop in (schema.get("properties") or {}).items():
        entry: dict[str, Any] = {"type": prop.get("type")}
        if name in required:
            entry["required"] = True
        else:
            entry["default"] = prop.get("default")
        normalized[name] = entry
    return normalized


def test_mcp_read_tool_schemas_match_registry_params(workspace: Path) -> None:
    """U1 §1/§4: each served read tool's input schema == its row's params.

    The row `params` field is the single source both projections consume
    (openapi via http_transport.openapi_schema, MCP via generation).
    """
    app = make_mcp_app(workspace, read_scope=["notes"], agent_identity="agent")
    tools = {tool.name: tool for tool in _list_tools(app)}

    for action in actions_by_id().values():
        mcp_binding = action.get("mcp")
        if not isinstance(mcp_binding, dict) or action["kind"] != "read":
            continue
        served = _normalized_tool_schema(tools[mcp_binding["tool"]].input_schema)
        assert served == _normalized_row_params(action["params"]), (
            f"{action['id']}: served schema for tool {mcp_binding['tool']!r} "
            "drifts from its registry row's params"
        )


def test_mcp_tools_bind_read_engine_dispatch_class(workspace: Path) -> None:
    """U1 §6(i): every tool except operation_run binds a read engine function."""
    app = make_mcp_app(workspace, read_scope=["notes"], agent_identity="agent")
    rows_by_tool = {
        action["mcp"]["tool"]: action
        for action in actions_by_id().values()
        if isinstance(action.get("mcp"), dict)
    }

    for tool in _list_tools(app):
        row = rows_by_tool[tool.name]
        if tool.name == "operation_run":
            assert row["kind"] == "write"
            continue
        assert row["kind"] == "read"
        assert str(row["engine"]).startswith("read_")


def test_mcp_public_call_tool_serializes_structured_result(workspace: Path) -> None:
    app = make_mcp_app(workspace, read_scope=["notes"], agent_identity="agent")

    result = asyncio.run(app.call_tool("status", {}))

    assert result.is_error is False
    assert json.loads(result.content[0].text)["ok"] is True
    assert result.structured_content["ok"] is True
    assert result.structured_content["api_version"] == "engine-read-api.v1"


def test_mcp_read_tools_pass_session_scope(
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
        "read_slice",
        "read_draft",
        "read_exploration",
    ):
        monkeypatch.setattr(mcp_transport.engine_api, name, record(name))

    app = make_mcp_app(workspace, read_scope=["notes"], agent_identity="agent")
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
        "project_slice": {"project_path": "projects/a/project.md"},
        "project_draft": {"project_path": "projects/a/project.md"},
        "exploration": {},
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
        ("read_slice", ["notes"]),
        ("read_draft", ["notes"]),
        ("read_exploration", ["notes"]),
    ]


def test_mcp_reads_are_engine_scoped(workspace: Path) -> None:
    from mcp.server.mcpserver.exceptions import ToolError

    write_checked_note(workspace, "notes/alpha.md", "Alpha")
    write_checked_note(workspace, "notes/beta.md", "Beta")
    app = make_mcp_app(workspace, read_scope=["notes/alpha.md"], agent_identity="agent")

    listed = _call(app, "concepts")

    assert [row["path"] for row in listed["concepts"]] == ["notes/alpha.md"]
    with pytest.raises(ToolError, match="target not found"):
        _call(app, "concept", target="notes/beta.md")


def test_mcp_operation_run_uses_request_envelope(workspace: Path) -> None:
    app = make_mcp_app(workspace, read_scope=["notes"], agent_identity="review-agent")

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
    # Stated, not inferred from actor="agent" (#1596): bodies arriving over this
    # transport are machine-authored, so a later authority change here cannot
    # silently disable untrusted-Markdown neutralization.
    job = state.request_job(workspace, "mcp-create")
    assert job is not None
    assert job["request_envelope"]["machine_authored"] is True
    assert json.loads(row["provenance_json"]) == {
        "surface": "memoria-mcp",
        "command": "mcp:create-concept",
        "agent_identity": "review-agent",
    }
    assert json.loads(row["args_json"])["target_path"] == "notes/mcp.md"
    with state.connect(workspace) as conn:
        journal = conn.execute(
            "SELECT payload_json FROM event_log"
            " WHERE json_extract(payload_json, '$.request_id') = ?",
            ("mcp-create",),
        ).fetchall()
    assert journal
    assert {
        tuple(sorted(json.loads(event["payload_json"])["request_provenance"].items()))
        for event in journal
    } == {
        tuple(
            sorted(
                {
                    "surface": "memoria-mcp",
                    "command": "mcp:create-concept",
                    "agent_identity": "review-agent",
                }.items()
            )
        )
    }


def test_mcp_operation_run_never_carries_pi_authority(workspace: Path) -> None:
    """The loopback HTTP door's PI grant must not reach the stdio agent door."""
    attention_path = workspace / "inbox/mcp-cannot-resolve.md"
    attention_path.parent.mkdir(parents=True, exist_ok=True)
    attention_path.write_text(
        "---\n"
        "projection: attention\n"
        "title: MCP cannot resolve\n"
        "attention_kind: work-prompt\n"
        "attention_status: open\n"
        "routing_class: ask\n"
        "---\n"
        "Review.\n",
        encoding="utf-8",
    )
    app = make_mcp_app(workspace, read_scope=["inbox"], agent_identity="review-agent")

    response = _call(
        app,
        "operation_run",
        operation_id="resolve-attention",
        payload={
            "target_id": "inbox/mcp-cannot-resolve.md",
            "outcome": "apply",
            "routing_class": "ask",
            "reason": "agent disposition",
        },
        idempotency_key="mcp-cannot-resolve",
    )

    assert response["ok"] is False
    assert response["result"]["status"] == "failed"
    assert response["result"]["error"] == "resolve-attention requires PI actor authority"
    request = state.request_row(workspace, "mcp-cannot-resolve")
    assert request is not None
    assert request["actor"] == "agent"
    assert "attention_status: open" in attention_path.read_text(encoding="utf-8")


def test_mcp_rejects_idempotency_key_bound_to_pending_pi_request(workspace: Path) -> None:
    from mcp.server.mcpserver.exceptions import ToolError

    attention_path = workspace / "inbox/pi-pending.md"
    attention_path.parent.mkdir(parents=True, exist_ok=True)
    attention_path.write_text(
        "---\n"
        "projection: attention\n"
        "title: PI pending\n"
        "attention_kind: work-prompt\n"
        "attention_status: open\n"
        "routing_class: ask\n"
        "---\n"
        "Review.\n",
        encoding="utf-8",
    )
    request = worker.enqueue_operation(
        workspace,
        "resolve-attention",
        actor="pi",
        machine_authored=False,
        idempotency_key="pi-pending-request",
        payload={
            "target_id": "inbox/pi-pending.md",
            "outcome": "apply",
            "routing_class": "ask",
            "reason": "PI decision",
        },
    )
    app = make_mcp_app(workspace, read_scope=["inbox"], agent_identity="review-agent")

    listed = _call(app, "requests", status="pending")
    detail = _call(app, "request", request_id=request["request_id"])
    with pytest.raises(ToolError, match="idempotency key is already bound"):
        _call(
            app,
            "operation_run",
            operation_id="create-concept",
            payload={"concept_type": "note"},
            idempotency_key=request["request_id"],
        )

    assert [row["request_id"] for row in listed["requests"]] == ["pi-pending-request"]
    assert detail["request"]["actor"] == "pi"
    assert state.request_job(workspace, request["request_id"])["status"] == "pending"
    assert "attention_status: open" in attention_path.read_text(encoding="utf-8")


def test_mcp_answer_query_hit_sources_resolve_through_read_tools(workspace: Path) -> None:
    """U4-C.3: every ref an `answer-query` hit returns resolves through a read tool."""
    write_checked_note(workspace, "notes/groundterm.md", "Groundterm note")
    content = workspace / ".memoria/blobs/source-content/source-alpha/full-text/alpha.txt"
    content.parent.mkdir(parents=True)
    content.write_text("groundterm full text evidence", encoding="utf-8")
    state.upsert_catalog_record(
        workspace,
        work_id="source-alpha",
        title="Alpha Work",
        concept_path="catalog/sources/source-alpha",
        doi="10.1000/alpha",
        identifiers={"doi": "10.1000/alpha"},
        citekey="alpha2026",
        csl_json={"id": "alpha2026", "title": "Alpha Work", "DOI": "10.1000/alpha"},
        provider_coverage="full",
        text_status="full-text",
        check_status="checked",
        content_path=content.relative_to(workspace).as_posix(),
    )
    app = make_mcp_app(workspace, read_scope=["notes", "catalog"], agent_identity="agent")

    response = _call(
        app,
        "operation_run",
        operation_id="answer-query",
        payload={"query": "groundterm"},
        idempotency_key="ask-hit",
    )

    assert response["ok"] is True
    result = response["result"]
    assert result["unknowns"] == []
    assert sorted(source["path"] for source in result["sources"]) == [
        "fulltexts/source-alpha.md",
        "notes/groundterm.md",
    ]
    for source in result["sources"]:
        if source["type"] in {"fulltext", "graph-neighborhood"}:
            resolved = _call(app, "work", work_id=Path(source["path"]).stem)
            assert resolved["work"]["work_id"] == Path(source["path"]).stem
        else:
            resolved = _call(app, "concept", target=source["path"])
            assert resolved["path"] == source["path"]
            assert resolved["check_status"] == "checked"


def test_mcp_answer_query_no_hit_payload_rides_dispatch_intact(workspace: Path) -> None:
    """U4-C.4 (amended 2026-08-01): the honest-empty triple survives worker dispatch.

    The sentence is engine-rendered per query, so the pin is structural rather
    than a wording match: the stage rows and named strata that reach the client
    must be the same ones `unknowns[0]` was rendered from. A stage row dropped
    or a stratum re-keyed in transport breaks the final equality.
    """
    write_checked_note(workspace, "notes/present.md", "Present note")
    app = make_mcp_app(workspace, read_scope=["notes"], agent_identity="agent")

    response = _call(
        app,
        "operation_run",
        operation_id="answer-query",
        payload={"query": "absentterm"},
        idempotency_key="ask-empty",
    )

    assert response["ok"] is True
    result = response["result"]
    assert result["sources"] == []
    assert result["staleness"] == []
    assert result["contradictions"] == []

    counts = result["pipeline_counts"]
    stages = [row["stage"] for row in counts]
    assert stages[0] == "universe"
    assert stages[-2:] == ["ranked", "returned"]
    assert sorted(result["excluded_strata"]) == ["gated", "stale", "unchecked"]
    # Not a degenerate empty: a real checked document entered the universe and
    # reached the ranked stage, and none came back.
    assert retrieval_pipeline.candidate_count(counts) > 0
    assert counts[-1]["count"] == 0
    assert result["unknowns"] == [
        retrieval_pipeline.honest_empty(counts, result["excluded_strata"])
    ]


def _read_observed_rows(vault: Path) -> list[dict[str, Any]]:
    """The `read-observed.v1` rows, from the table I1 T.1/T.3 routes them to.

    Ordered by `rowid`, not `event_id`: the id is a uuid4 hex, so ordering by it
    shuffles rows that share a timestamp.
    """
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT session_id, surface, payload_json FROM telemetry_events"
            " WHERE event_type = ? ORDER BY rowid",
            (READ_EVENT_SCHEMA,),
        ).fetchall()
    return [dict(row) for row in rows]


def _journal_plane(vault: Path) -> dict[str, Any]:
    """Every byte a journal append would move, so its absence is the assertion."""
    head = vault / state.JOURNAL_HEAD_REL
    with state.connect(vault) as conn:
        events = [tuple(row) for row in conn.execute("SELECT * FROM event_log ORDER BY event_id")]
    return {
        "event_log": events,
        "jsonl": sorted(
            (path.name, path.read_bytes()) for path in (vault / ".memoria/journal").glob("*.jsonl")
        ),
        "head": head.read_bytes() if head.is_file() else None,
    }


def test_mcp_answer_query_records_no_read_observed_row_and_leaves_the_journal_intact(
    workspace: Path,
) -> None:
    """U4-C.5 (re-specified 2026-08-02): the ask path is neither emitter nor writer.

    U4 §4's last bullet has the co-PI's reads firing `read-observed` telemetry
    "exactly as for any other consumer". They do not, and not by omission: I1's
    design keeps `answer-query`'s manifest a pure read and gives the schema only
    the view/detail emitters. So the honest contract is a double absence — no
    analytics row, no journal byte — and each half is asserted behind a positive
    control, because an unverified absence is exactly what this task originally
    got wrong: it scanned `event_log` for a row that lives in `telemetry_events`,
    where no ask-path emitter could ever have tripped it.
    """
    write_checked_note(workspace, "notes/groundterm.md", "Groundterm note")
    card = write_finding(
        workspace, "flag", "Drift check", "a note drifted", "sweep", target="notes/groundterm.md"
    )
    assert card is not None
    app = make_mcp_app(workspace, read_scope=["notes"], agent_identity="agent")

    # Control 1: a journaling write through this same door, so the identity claim
    # below is made over a populated plane and not over three empty containers.
    genesis = _journal_plane(workspace)
    seed = _call(
        app,
        "operation_run",
        operation_id="create-concept",
        payload={
            "target_path": "notes/journal-seed.md",
            "content": "---\ntype: note\ntitle: Seed\ntags: []\nlinks: {}\n---\nBody.\n",
            "concept_type": "note",
        },
        idempotency_key="ask-journal-seed",
    )
    assert seed["ok"] is True
    seeded = _journal_plane(workspace)
    assert len(seeded["event_log"]) > len(genesis["event_log"])
    assert [name for name, _ in seeded["jsonl"]] == ["memoria-mcp.jsonl"]
    assert seeded["head"] is not None
    assert seeded["head"] != genesis["head"]

    # Control 2: the one shipped `read-observed.v1` emitter (the attention detail
    # read). Without it, an empty result below is indistinguishable from a query
    # aimed at the wrong table — and it moves no journal byte either.
    engine_api.read_attention_card(workspace, card.relative_to(workspace).as_posix())
    observed = _read_observed_rows(workspace)
    assert len(observed) == 1
    assert _journal_plane(workspace) == seeded

    response = _call(
        app,
        "operation_run",
        operation_id="answer-query",
        payload={"query": "groundterm"},
        idempotency_key="ask-telemetry",
    )

    # Not a degenerate no-op: the ask really did retrieve a checked source.
    assert response["ok"] is True
    assert [source["path"] for source in response["result"]["sources"]] == ["notes/groundterm.md"]
    assert _read_observed_rows(workspace) == observed
    assert _journal_plane(workspace) == seeded


def _list_tools(app: Any) -> list[Any]:
    """The served tool roster. `MCPServer.list_tools` is public and async in mcp 2.x."""
    return asyncio.run(app.list_tools())


def _call(app: Any, name: str, **arguments: Any) -> dict[str, Any]:
    """One tool call, unwrapped to the engine payload.

    `MCPServer.call_tool` returns a `CallToolResult` whose `structured_content`
    is the dict the tool function returned — the same value mcp 1.x exposed via
    the private tool manager's `convert_result=False`.
    """
    return asyncio.run(app.call_tool(name, arguments)).structured_content
