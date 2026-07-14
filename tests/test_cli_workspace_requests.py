from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.cli import main
from memoria_vault.runtime import state
from memoria_vault.runtime.trusted_writer import append_explicit_journal_event
from memoria_vault.runtime.vaultio import read_frontmatter
from memoria_vault.runtime.worker import (
    INTEGRITY_SWEEP_OPERATIONS,
    enqueue_operation,
    enqueue_trusted_write,
    run_request,
)
from tests.helpers import mark_file_status


def append_journal_event(vault: Path, event: dict, *, machine: str):
    return append_explicit_journal_event(vault, event, actor="operation", machine=machine)


def write_runner_provider_config(
    workspace: Path, *, local_url: str = "http://model.test/v1"
) -> None:
    config = workspace / ".memoria/config/providers.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        "\n".join(
            [
                "version: 1",
                "runner_providers:",
                f"  local: {{url: {local_url}, key_env: null}}",
                "  gateway: {url: https://gateway.test/v1, key_env: KILOCODE_API_KEY}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_cli_operation_list_and_run_use_workspace_operation_concepts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    digest = workspace / "digests/source-alpha.md"
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text(
        "---\ntype: digest\ncheck_status: checked\ntitle: Alpha digest\ntags: [sleep]\n---\nBody.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "digests/source-alpha.md", "digest")

    assert main(["operation", "list", "--workspace", str(workspace), "--json"]) == 0
    listed = json.loads(capsys.readouterr().out)
    operation_ids = {row["operation_id"] for row in listed["operations"]}
    assert {"analyze-gaps", "enrich-source", "integrity-citation-survival-check"} <= operation_ids

    rc = main(
        [
            "operation",
            "run",
            "--workspace",
            str(workspace),
            "analyze-gaps",
            "--mode",
            "live",
            "--payload-json",
            json.dumps({"seed_terms": ["new area"], "dense_threshold": 1}),
            "--json",
            "--idempotency-key",
            "operation-run-gaps",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    gaps = {gap["topic"]: gap for gap in output["result"]["gaps"]}
    assert gaps["sleep"]["gap_type"] == "undigested"
    assert gaps["sleep"]["kind"] == "undigested"
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT args_json FROM operation_requests WHERE request_id = ?",
            ("operation-run-gaps",),
        ).fetchone()
    assert json.loads(row["args_json"])["mode"] == "live"
    assert gaps["sleep"]["score"] == 4
    assert gaps["new area"]["gap_type"] == "new-topic"
    assert output["result"]["summary"]["total"] == output["result"]["gap_count"]
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, args_json FROM operation_requests WHERE request_id = ?",
            ("operation-run-gaps",),
        ).fetchone()
    assert row["operation_id"] == "analyze-gaps"
    assert json.loads(row["args_json"]) == {
        "seed_terms": ["new area"],
        "dense_threshold": 1,
        "mode": "live",
    }


def test_cli_operation_list_ignores_workspace_capability_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    write_runner_provider_config(workspace)
    asset_dir = workspace / "capabilities/operations/directory-only"
    asset_dir.mkdir(parents=True)
    (asset_dir / "prompt.md").write_text("# Prompt\n", encoding="utf-8")

    rc = main(["operation", "list", "--workspace", str(workspace), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert "directory-only" not in {row["operation_id"] for row in output["operations"]}


def test_cli_workspace_run_reports_schedule_id_for_queue_drain(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    digest = workspace / "digests/source-alpha.md"
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text(
        "---\ntype: digest\ncheck_status: checked\ntitle: Alpha digest\ntags: [sleep]\n---\nBody.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "digests/source-alpha.md", "digest")
    enqueue_operation(
        workspace,
        "analyze-gaps",
        payload={"seed_terms": ["new area"], "dense_threshold": 1},
        idempotency_key="pending-gaps",
        actor="pi",
    )

    rc = main(
        [
            "workspace",
            "run",
            "--workspace",
            str(workspace),
            "--schedule-id",
            "queue-drain",
            "--limit",
            "1",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["schedule_id"] == "queue-drain"
    assert output["ran"] == 1
    assert output["results"][0]["status"] == "done"


def test_cli_workspace_scan_reports_schedule_id_for_file_watch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(
        [
            "workspace",
            "scan",
            "--workspace",
            str(workspace),
            "--schedule-id",
            "file-watch",
            "--idempotency-key",
            "scheduled-scan",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["schedule_id"] == "file-watch"
    assert output["job"]["request_envelope"]["schedule_id"] == "file-watch"
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, schedule_id, actor FROM operation_requests WHERE request_id = ?",
            ("scheduled-scan",),
        ).fetchone()
    assert tuple(row) == ("observe-pi-edits", "file-watch", "integrity")


def test_cli_serve_watch_once_runs_file_watch_scan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(
        [
            "serve",
            "--workspace",
            str(workspace),
            "--watch",
            "--once",
            "--idempotency-key",
            "serve-watch-once",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["schedule_id"] == "file-watch"
    assert output["job"]["request_envelope"]["schedule_id"] == "file-watch"
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, schedule_id, actor FROM operation_requests WHERE request_id = ?",
            ("serve-watch-once",),
        ).fetchone()
    assert tuple(row) == ("observe-pi-edits", "file-watch", "integrity")


def test_cli_workspace_scan_marks_pi_edits_unchecked_until_promoted(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    note = "---\ntype: note\ntitle: PI scan note\ntags: []\nlinks: {}\n---\nOriginal.\n"
    enqueue_trusted_write(
        workspace,
        "notes/pi-scan.md",
        note,
        idempotency_key="write-pi-scan",
        actor="operation",
    )
    main(["workspace", "run", "--workspace", str(workspace), "--limit", "1", "--json"])
    capsys.readouterr()
    path = workspace / "notes/pi-scan.md"
    assert "check_status" not in read_frontmatter(path)
    assert state.concept_check_status(workspace, "notes/pi-scan.md") == "checked"

    path.write_text(path.read_text(encoding="utf-8") + "\nPI edit.\n", encoding="utf-8")

    assert (
        main(
            [
                "workspace",
                "scan",
                "--workspace",
                str(workspace),
                "--idempotency-key",
                "scan-pi-edit",
                "--json",
            ]
        )
        == 0
    )
    scanned = json.loads(capsys.readouterr().out)

    assert scanned["needs_check_count"] == 1
    assert scanned["needs_check_paths"] == ["notes/pi-scan.md"]
    assert scanned["result"]["observed_count"] == 1
    assert "check_status" not in read_frontmatter(path)
    assert state.concept_check_status(workspace, "notes/pi-scan.md") == "unchecked"
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT check_status FROM outputs WHERE output_id = ?",
            ("notes/pi-scan.md",),
        ).fetchone()
        consumable = conn.execute(
            "SELECT output_id FROM consumable_outputs WHERE output_id = ?",
            ("notes/pi-scan.md",),
        ).fetchone()
        event = conn.execute(
            """
            SELECT event_type
            FROM event_log
            WHERE event_type = 'observed_external_edit'
            ORDER BY event_id DESC
            LIMIT 1
            """
        ).fetchone()
    assert row["check_status"] == "unchecked"
    assert consumable is None
    assert event["event_type"] == "observed_external_edit"

    assert (
        main(
            [
                "operation",
                "run",
                "--workspace",
                str(workspace),
                "mark-checked",
                "--payload-json",
                '{"target_path": "notes/pi-scan.md"}',
                "--idempotency-key",
                "mark-pi-scan",
                "--json",
            ]
        )
        == 0
    )
    promoted = json.loads(capsys.readouterr().out)

    assert promoted["ok"] is True
    assert promoted["result"]["check"]["status"] == "passed"
    assert "check_status" not in read_frontmatter(path)
    assert state.concept_check_status(workspace, "notes/pi-scan.md") == "checked"
    with state.connect(workspace) as conn:
        consumable = conn.execute(
            "SELECT output_id FROM consumable_outputs WHERE output_id = ?",
            ("notes/pi-scan.md",),
        ).fetchone()
    assert consumable["output_id"] == "notes/pi-scan.md"


def test_cli_request_list_show_and_resume_pending_request(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    digest = workspace / "digests/source-alpha.md"
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text(
        "---\ntype: digest\ncheck_status: checked\ntitle: Alpha digest\ntags: [sleep]\n---\nBody.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "digests/source-alpha.md", "digest")
    enqueue_operation(
        workspace,
        "analyze-gaps",
        payload={"seed_terms": ["new area"], "dense_threshold": 1},
        idempotency_key="resume-gaps",
        provenance={"surface": "test"},
        actor="pi",
    )

    assert (
        main(["request", "list", "--workspace", str(workspace), "--status", "pending", "--json"])
        == 0
    )
    listed = json.loads(capsys.readouterr().out)
    assert [row["request_id"] for row in listed["requests"]] == ["resume-gaps"]

    assert main(["request", "show", "--workspace", str(workspace), "resume-gaps", "--json"]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["request"]["operation_id"] == "analyze-gaps"
    assert shown["request"]["args"] == {"seed_terms": ["new area"], "dense_threshold": 1}
    assert shown["request"]["provenance"] == {"surface": "test"}
    assert shown["request"]["input_refs"] == []
    assert shown["request"]["output_intents"] == []
    assert shown["request"]["primary_target"] == ""
    assert shown["request"]["precondition_hashes"] == {}
    assert "target_path" not in shown["request"]
    assert "target_hash" not in shown["request"]

    rc = main(["request", "resume", "--workspace", str(workspace), "resume-gaps", "--json"])
    resumed = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert resumed["result"]["status"] == "done"
    gaps = {gap["topic"]: gap for gap in resumed["result"]["gaps"]}
    assert gaps["sleep"]["gap_type"] == "undigested"
    assert gaps["new area"]["gap_type"] == "new-topic"
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT status FROM operation_requests WHERE request_id = ?",
            ("resume-gaps",),
        ).fetchone()
    assert row["status"] == "done"


def test_cli_request_cancel_preserves_trusted_write_envelope_args(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    enqueue_trusted_write(
        workspace,
        "notes/queued.md",
        "---\ntype: note\ntitle: Queued\ntags: []\nlinks: {}\n---\nBody.\n",
        idempotency_key="trusted-request",
        actor="operation",
    )

    assert (
        main(
            [
                "request",
                "cancel",
                "--workspace",
                str(workspace),
                "trusted-request",
                "--json",
            ]
        )
        == 0
    )
    cancelled = json.loads(capsys.readouterr().out)

    assert cancelled["request"]["status"] == "cancelled"
    assert cancelled["request"]["args"]["target_path"] == "notes/queued.md"
    assert cancelled["request"]["job"]["request_envelope"]["args"] == cancelled["request"]["args"]


@pytest.mark.parametrize(
    ("command", "request_status"),
    [
        (["answer", "answer=approved"], "pending"),
        (["amend", "target_path=notes/amended.md"], "pending"),
        (["cancel"], "pending"),
        (["retry"], "cancelled"),
        (["resume"], "pending"),
    ],
)
def test_cli_request_controls_reject_agent_for_pi_request_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    command: list[str],
    request_status: str,
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    job = enqueue_operation(
        workspace,
        "mark-checked",
        payload={"target_path": "notes/queued.md"},
        idempotency_key=f"pi-control-{command[0]}",
        actor="pi",
    )
    request_id = str(job["job_id"])
    if request_status == "cancelled":
        state.finish_request(
            workspace,
            request_id,
            "cancelled",
            {**job, "status": "cancelled", "error": "test setup"},
        )
    before = state.request_detail(state.request_row(workspace, request_id))
    with state.connect(workspace) as conn:
        journal_count = conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0]

    assert (
        main(
            [
                "request",
                command[0],
                "--workspace",
                str(workspace),
                "--actor",
                "agent",
                request_id,
                *command[1:],
                "--json",
            ]
        )
        == 2
    )
    rejected = json.loads(capsys.readouterr().out)
    after = state.request_detail(state.request_row(workspace, request_id))

    assert rejected["ok"] is False
    assert "requires PI actor authority" in rejected["error"]
    assert after["status"] == before["status"]
    assert after["args"] == before["args"]
    assert after["job"]["request_envelope"] == before["job"]["request_envelope"]
    with state.connect(workspace) as conn:
        assert conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0] == journal_count


@pytest.mark.parametrize("status", ["running", "done", "failed", "cancelled"])
def test_cli_request_cancel_rejects_non_pending_status_without_mutation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    status: str,
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    job = enqueue_operation(
        workspace,
        "answer-query",
        payload={"query": "status"},
        idempotency_key=f"cancel-{status}",
        actor="pi",
    )
    error = "test setup" if status in {"failed", "cancelled"} else ""
    state.finish_request(
        workspace,
        str(job["job_id"]),
        status,
        {**job, "status": status, "error": error},
    )
    before = state.request_detail(state.request_row(workspace, str(job["job_id"])))

    assert (
        main(
            [
                "request",
                "cancel",
                "--workspace",
                str(workspace),
                str(job["job_id"]),
                "--json",
            ]
        )
        == 2
    )
    rejected = json.loads(capsys.readouterr().out)
    after = state.request_detail(state.request_row(workspace, str(job["job_id"])))

    assert "requires pending status" in rejected["error"]
    assert after == before


def test_cli_request_retry_rejects_superseded_source(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    source = enqueue_operation(
        workspace,
        "answer-query",
        payload={"query": "status"},
        idempotency_key="superseded-source",
        actor="pi",
        schedule_id="source-schedule",
    )
    assert (
        main(
            [
                "request",
                "amend",
                "--workspace",
                str(workspace),
                "--idempotency-key",
                "successor-request",
                str(source["job_id"]),
                "query=updated",
                "--json",
            ]
        )
        == 0
    )
    successor = json.loads(capsys.readouterr().out)["request"]

    assert successor["schedule_id"] is None
    assert (
        main(
            [
                "request",
                "retry",
                "--workspace",
                str(workspace),
                str(source["job_id"]),
                "--json",
            ]
        )
        == 2
    )
    rejected = json.loads(capsys.readouterr().out)
    source_after = state.request_job(workspace, str(source["job_id"]))

    assert "superseded by request successor-request" in rejected["error"]
    assert source_after["status"] == "cancelled"
    assert source_after["superseded_by_request_id"] == "successor-request"
    assert state.request_job(workspace, "successor-request")["status"] == "pending"


def test_cli_request_amend_rejects_scope_bearing_payload_change(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    source = enqueue_operation(
        workspace,
        "mark-checked",
        payload={"target_path": "notes/original.md"},
        idempotency_key="scoped-source",
        output_intents=[{"id": "notes/original.md", "kind": "note"}],
        primary_target="notes/original.md",
        precondition_hashes={"notes/original.md": "sha256:original"},
        actor="pi",
    )

    assert (
        main(
            [
                "request",
                "amend",
                "--workspace",
                str(workspace),
                "--idempotency-key",
                "scoped-successor",
                str(source["job_id"]),
                "target_path=notes/changed.md",
                "--json",
            ]
        )
        == 2
    )
    rejected = json.loads(capsys.readouterr().out)

    assert "scope-bearing field" in rejected["error"]
    assert state.request_job(workspace, str(source["job_id"]))["status"] == "pending"
    assert state.request_job(workspace, "scoped-successor") is None


def test_cli_request_amend_rejects_integrity_only_source_without_superseding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    source = enqueue_operation(
        workspace,
        "trace-integrity-scan",
        payload={"reason": "manual"},
        idempotency_key="integrity-source",
        actor="integrity",
    )

    assert (
        main(
            [
                "request",
                "amend",
                "--workspace",
                str(workspace),
                "--idempotency-key",
                "integrity-successor",
                str(source["job_id"]),
                "reason=corrected",
                "--json",
            ]
        )
        == 2
    )
    rejected = json.loads(capsys.readouterr().out)

    assert "integrity actor authority" in rejected["error"]
    assert state.request_job(workspace, str(source["job_id"]))["status"] == "pending"
    assert state.request_job(workspace, "integrity-successor") is None


def test_cli_request_answer_retry_repairs_missing_lifecycle_event(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from memoria_vault.runtime import trusted_writer

    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    source = enqueue_operation(
        workspace,
        "answer-query",
        payload={"query": "status"},
        idempotency_key="event-source",
        actor="pi",
    )
    command = [
        "request",
        "answer",
        "--workspace",
        str(workspace),
        "--idempotency-key",
        "event-successor",
        str(source["job_id"]),
        "note=ready",
        "--json",
    ]
    append_event = trusted_writer.append_explicit_journal_event

    def crash_before_event(*_args, **_kwargs):
        raise RuntimeError("simulated lifecycle event crash")

    monkeypatch.setattr(trusted_writer, "append_explicit_journal_event", crash_before_event)
    assert main(command) == 2
    capsys.readouterr()
    monkeypatch.setattr(trusted_writer, "append_explicit_journal_event", append_event)

    assert main(command) == 0
    capsys.readouterr()
    with state.connect(workspace) as conn:
        events = conn.execute(
            """
            SELECT COUNT(*)
            FROM event_log
            WHERE event_type = 'request_answered'
              AND json_extract(payload_json, '$.successor_request_id') = 'event-successor'
            """
        ).fetchone()[0]
    assert events == 1


@pytest.mark.parametrize("action", ["cancel", "retry"])
def test_cli_request_transition_retry_repairs_missing_lifecycle_event(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    action: str,
) -> None:
    from memoria_vault.runtime import trusted_writer

    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    job = enqueue_operation(
        workspace,
        "answer-query",
        payload={"query": action},
        idempotency_key=f"{action}-event-source",
        actor="pi",
    )
    if action == "retry":
        state.finish_request(
            workspace,
            str(job["job_id"]),
            "failed",
            {**job, "status": "failed", "error": "test failure"},
        )
    command = [
        "request",
        action,
        "--workspace",
        str(workspace),
        str(job["job_id"]),
        "--json",
    ]
    append_event = trusted_writer.append_explicit_journal_event

    def crash_before_event(*_args, **_kwargs):
        raise RuntimeError("simulated lifecycle event crash")

    monkeypatch.setattr(trusted_writer, "append_explicit_journal_event", crash_before_event)
    assert main(command) == 2
    capsys.readouterr()
    monkeypatch.setattr(trusted_writer, "append_explicit_journal_event", append_event)

    assert main(command) == 0
    capsys.readouterr()
    event_type = f"request_{'cancelled' if action == 'cancel' else 'retried'}"
    attempt_key = f"{action}_attempt"
    with state.connect(workspace) as conn:
        events = conn.execute(
            """
            SELECT COUNT(*)
            FROM event_log
            WHERE event_type = ?
              AND json_extract(payload_json, '$.request_id') = ?
              AND json_extract(payload_json, ?) = 1
            """,
            (event_type, str(job["job_id"]), f"$.{attempt_key}"),
        ).fetchone()[0]
    assert events == 1
    assert main(command) == 2
    capsys.readouterr()


def test_cli_request_cancel_and_retry_use_canonical_request_id(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    job = enqueue_operation(
        workspace,
        "answer-query",
        payload={"query": "canonical"},
        idempotency_key="unsafe/source",
        actor="pi",
    )

    assert (
        main(
            [
                "request",
                "cancel",
                "--workspace",
                str(workspace),
                "unsafe/source",
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert state.request_job(workspace, str(job["job_id"]))["status"] == "cancelled"
    assert (
        main(
            [
                "request",
                "retry",
                "--workspace",
                str(workspace),
                "unsafe/source",
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert state.request_job(workspace, str(job["job_id"]))["status"] == "pending"
    assert (
        main(
            [
                "request",
                "answer",
                "--workspace",
                str(workspace),
                "--idempotency-key",
                "canonical-successor",
                "unsafe/source",
                "note=ready",
                "--json",
            ]
        )
        == 0
    )
    successor = json.loads(capsys.readouterr().out)

    assert successor["supersedes_request_id"] == str(job["job_id"])
    assert successor["request"]["causal_refs"] == [{"id": str(job["job_id"])}]
    with state.connect(workspace) as conn:
        request_ids = {
            json.loads(row["payload_json"])["request_id"]
            for row in conn.execute(
                "SELECT payload_json FROM event_log WHERE event_type LIKE 'request_%'"
            )
        }
    assert request_ids == {str(job["job_id"])}


def test_cli_request_retry_repairs_event_after_retried_job_finishes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from memoria_vault.runtime import trusted_writer

    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    job = enqueue_operation(
        workspace,
        "regenerate-capability-index",
        payload={},
        idempotency_key="retry-finish-source",
        actor="pi",
    )
    state.finish_request(
        workspace,
        str(job["job_id"]),
        "failed",
        {**job, "status": "failed", "error": "test failure"},
    )
    command = [
        "request",
        "retry",
        "--workspace",
        str(workspace),
        str(job["job_id"]),
        "--json",
    ]
    append_event = trusted_writer.append_explicit_journal_event

    def crash_before_event(*_args, **_kwargs):
        raise RuntimeError("simulated retry event crash")

    monkeypatch.setattr(trusted_writer, "append_explicit_journal_event", crash_before_event)
    assert main(command) == 2
    capsys.readouterr()
    monkeypatch.setattr(trusted_writer, "append_explicit_journal_event", append_event)
    result = run_request(workspace, str(job["job_id"]), machine="test-machine")
    assert result["status"] == "done"

    assert main(command) == 0
    capsys.readouterr()
    assert state.request_job(workspace, str(job["job_id"]))["status"] == "done"
    with state.connect(workspace) as conn:
        events = conn.execute(
            """
            SELECT COUNT(*)
            FROM event_log
            WHERE event_type = 'request_retried'
              AND json_extract(payload_json, '$.request_id') = 'retry-finish-source'
              AND json_extract(payload_json, '$.retry_attempt') = 1
            """
        ).fetchone()[0]
    assert events == 1


def test_cli_request_amend_rejects_fork_from_superseded_source(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    source = enqueue_operation(
        workspace,
        "answer-query",
        payload={"query": "original"},
        idempotency_key="fork-source",
        actor="pi",
    )
    first = [
        "request",
        "amend",
        "--workspace",
        str(workspace),
        "--idempotency-key",
        "fork-successor-one",
        str(source["job_id"]),
        "query=first",
        "--json",
    ]
    assert main(first) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "request",
                "amend",
                "--workspace",
                str(workspace),
                "--idempotency-key",
                "fork-successor-two",
                str(source["job_id"]),
                "query=second",
                "--json",
            ]
        )
        == 2
    )
    rejected = json.loads(capsys.readouterr().out)

    assert "already superseded by request fork-successor-one" in rejected["error"]
    assert state.request_job(workspace, "fork-successor-one")["status"] == "pending"
    assert state.request_job(workspace, "fork-successor-two") is None


def test_cli_rejects_agent_edits_to_pi_owned_steering_and_vocabulary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    steering = workspace / "steering.md"
    vocabulary = workspace / "system/vocabulary.md"
    steering_before = steering.read_text(encoding="utf-8")
    vocabulary_before = vocabulary.read_text(encoding="utf-8")

    assert (
        main(
            [
                "steering",
                "edit",
                "--workspace",
                str(workspace),
                "--actor",
                "agent",
                "--body",
                "agent steering",
                "--json",
            ]
        )
        == 2
    )
    steering_error = json.loads(capsys.readouterr().out)
    assert (
        main(
            [
                "vocab",
                "add",
                "--workspace",
                str(workspace),
                "--actor",
                "agent",
                "research_area",
                "agent-term",
                "--json",
            ]
        )
        == 2
    )
    vocabulary_error = json.loads(capsys.readouterr().out)

    assert "steering edit requires PI actor authority" in steering_error["error"]
    assert "vocabulary add requires PI actor authority" in vocabulary_error["error"]
    assert steering.read_text(encoding="utf-8") == steering_before
    assert vocabulary.read_text(encoding="utf-8") == vocabulary_before
    with state.connect(workspace) as conn:
        assert conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0] == 0


@pytest.mark.parametrize(
    ("action", "values"),
    [
        ("add", ["topics", "new-topic"]),
        ("rename", ["topics", "old-topic", "new-topic"]),
        ("merge", ["topics", "old-topic", "new-topic"]),
    ],
)
def test_cli_vocabulary_rejects_inert_topics_mutations(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    action: str,
    values: list[str],
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    vocabulary = workspace / "system/vocabulary.md"
    before = vocabulary.read_text(encoding="utf-8")

    assert (
        main(
            [
                "vocab",
                action,
                "--workspace",
                str(workspace),
                *values,
                "--json",
            ]
        )
        == 2
    )
    error = json.loads(capsys.readouterr().out)

    assert "topics inherit research_area" in error["error"]
    assert vocabulary.read_text(encoding="utf-8") == before
    with state.connect(workspace) as conn:
        assert conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0] == 0


def test_cli_vocabulary_list_reports_topics_inherited_from_research_area(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    assert main(["vocab", "list", "--workspace", str(workspace), "--json"]) == 0
    vocabulary = json.loads(capsys.readouterr().out)["vocabulary"]

    assert vocabulary["topics"] == vocabulary["research_area"]


def test_cli_attention_list_show_worklist_and_resolve_projection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    attention = workspace / "inbox/flag-alpha.md"
    attention.parent.mkdir(parents=True, exist_ok=True)
    attention.write_text(
        "---\n"
        "title: Alpha flag\n"
        "projection: attention\n"
        "attention_kind: flag\n"
        "attention_status: open\n"
        "target: notes/alpha.md\n"
        "routing_class: ask\n"
        "---\n"
        "# Finding\n\nCheck this.\n",
        encoding="utf-8",
    )
    work_prompt = workspace / "inbox/work-alpha.md"
    work_prompt.write_text(
        "---\n"
        "title: Alpha work\n"
        "projection: attention\n"
        "attention_kind: work-prompt\n"
        "attention_status: open\n"
        "target: projects/alpha/project.md\n"
        "routing_class: act\n"
        "---\n"
        "# Action\n\nWork this.\n",
        encoding="utf-8",
    )

    assert main(["attention", "list", "--workspace", str(workspace), "--json"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert [row["path"] for row in listed["attention"]] == [
        "inbox/flag-alpha.md",
        "inbox/work-alpha.md",
    ]

    assert main(["attention", "worklist", "--workspace", str(workspace), "--json"]) == 0
    worklist = json.loads(capsys.readouterr().out)
    assert [row["path"] for row in worklist["attention"]] == ["inbox/work-alpha.md"]

    assert (
        main(
            [
                "attention",
                "show",
                "--workspace",
                str(workspace),
                "inbox/flag-alpha.md",
                "--json",
            ]
        )
        == 0
    )
    shown = json.loads(capsys.readouterr().out)
    assert shown["attention"]["frontmatter"]["title"] == "Alpha flag"
    assert "# Finding" in shown["attention"]["body"]

    rc = main(
        [
            "attention",
            "resolve",
            "--workspace",
            str(workspace),
            "inbox/flag-alpha.md",
            "--apply",
            "--reason",
            "PI resolved",
            "--json",
            "--idempotency-key",
            "attention-resolve",
        ]
    )
    resolved = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert resolved["result"]["resolution"]["target_id"] == "inbox/flag-alpha.md"
    assert resolved["result"]["resolution"]["reason"] == "PI resolved"
    assert resolved["result"]["resolution"]["outcome"] == "apply"
    assert resolved["result"]["resolution"]["resolution_outcome"] == "apply"
    assert resolved["result"]["resolution"]["routing_class"] == "ask"
    assert "decided_at" in resolved["result"]["resolution"]
    fm = read_frontmatter(attention)
    assert fm["attention_status"] == "resolved"
    assert fm["resolution_outcome"] == "apply"
    assert fm["routing_class"] == "ask"
    assert "resolved_at" in fm
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, args_json FROM operation_requests WHERE request_id = ?",
            ("attention-resolve",),
        ).fetchone()
    assert row["operation_id"] == "resolve-attention"
    assert json.loads(row["args_json"]) == {
        "target_id": "inbox/flag-alpha.md",
        "reason": "PI resolved",
        "outcome": "apply",
        "routing_class": "ask",
    }

    rc = main(
        [
            "attention",
            "resolve",
            "--workspace",
            str(workspace),
            "inbox/work-alpha.md",
            "--defer",
            "--json",
            "--idempotency-key",
            "attention-defer",
        ]
    )
    deferred = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert deferred["result"]["resolution"]["target_id"] == "inbox/work-alpha.md"
    assert deferred["result"]["resolution"]["resolution"] == "resolved"
    assert deferred["result"]["resolution"]["outcome"] == "defer"
    assert deferred["result"]["resolution"]["resolution_outcome"] == "defer"
    assert deferred["result"]["resolution"]["routing_class"] == "act"
    assert deferred["result"]["resolution"]["reason"] == "PI chose to defer attention"
    fm = read_frontmatter(work_prompt)
    assert fm["attention_status"] == "deferred"
    assert fm["resolution_outcome"] == "defer"
    assert fm["routing_class"] == "act"
    assert "resolved_at" in fm
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, args_json FROM operation_requests WHERE request_id = ?",
            ("attention-defer",),
        ).fetchone()
    assert row["operation_id"] == "resolve-attention"
    assert json.loads(row["args_json"]) == {
        "target_id": "inbox/work-alpha.md",
        "reason": "PI chose to defer attention",
        "outcome": "defer",
        "routing_class": "act",
    }


def test_cli_wires_maintenance_and_pi_commands(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    csl_file = tmp_path / "portable-work.csl.json"
    export_path = tmp_path / "workspace-export.json"
    csl_file.write_text(
        json.dumps(
            {
                "id": "portable-work",
                "type": "article-journal",
                "title": "Portable Exported Work",
                "DOI": "10.1000/portable",
                "abstract": "Portable CSL JSON.",
                "author": [{"family": "River", "given": "Ada"}],
                "issued": {"date-parts": [[2026]]},
            }
        ),
        encoding="utf-8",
    )

    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    assert (workspace / "steering.md").is_file()
    assert (workspace / "system/vocabulary.md").is_file()
    assert (workspace / "index.md").is_file()
    assert (workspace / "bibliography.bib").is_file()

    assert main(["doctor", "self-test", "--workspace", str(workspace), "--json"]) == 0
    self_test = json.loads(capsys.readouterr().out)
    assert self_test["checks"]["operation_catalog"] is True

    assert main(["doctor", "bundle", "--workspace", str(workspace), "--json"]) == 0
    bundle = json.loads(capsys.readouterr().out)
    assert "redacted" not in bundle

    assert (
        main(
            [
                "work",
                "import",
                "--workspace",
                str(workspace),
                "--format",
                "csl",
                "--file",
                str(csl_file),
                "--json",
                "--idempotency-key",
                "import-csl",
            ]
        )
        == 0
    )
    imported = json.loads(capsys.readouterr().out)
    assert imported["result"]["work_id"] == "portable-work"

    assert (
        main(
            [
                "work",
                "update",
                "--workspace",
                str(workspace),
                "portable-work",
                "--title",
                "Updated Portable Work",
                "--standing",
                "archived",
                "--research-area",
                "personal-informatics",
                "--json",
                "--idempotency-key",
                "update-portable",
            ]
        )
        == 0
    )
    updated = json.loads(capsys.readouterr().out)
    assert updated["result"]["work"]["title"] == "Updated Portable Work"
    assert updated["result"]["work"]["csl_json"]["memoria"]["standing"] == "archived"
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, status FROM operation_requests WHERE request_id = ?",
            ("update-portable",),
        ).fetchone()
    assert tuple(row) == ("update-work", "done")

    assert (
        main(
            [
                "new",
                "note",
                "Captured PI note",
                "--workspace",
                str(workspace),
                "--body",
                "The PI captured this.",
                "--tag",
                "personal-informatics",
                "--json",
            ]
        )
        == 0
    )
    captured = json.loads(capsys.readouterr().out)
    assert "check_status" not in read_frontmatter(workspace / captured["path"])
    assert state.concept_check_status(workspace, captured["path"]) == "unchecked"

    digest = workspace / "digests/hub-seed.md"
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text(
        "---\n"
        "type: digest\n"
        "title: Hub seed\n"
        "description: Hub seed\n"
        "work_id: hub-seed\n"
        "work_id: catalog/sources/ZOT1\n"
        "tags: [personal-informatics]\n"
        "links: {}\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "digests/hub-seed.md", "digest")
    assert (
        main(
            [
                "project",
                "suggest-hubs",
                "--workspace",
                str(workspace),
                "--min-count",
                "1",
                "--json",
            ]
        )
        == 0
    )
    hubs = json.loads(capsys.readouterr().out)
    assert hubs["suggestions"] == [{"count": 1, "topic": "personal-informatics"}]

    original_job = enqueue_operation(
        workspace,
        "answer-query",
        payload={"query": "status", "k": 1},
        idempotency_key="recoverable-request",
        actor="pi",
    )
    original_before = state.request_detail(
        state.request_row(workspace, str(original_job["job_id"]))
    )
    answer_command = [
        "request",
        "answer",
        "--workspace",
        str(workspace),
        "--idempotency-key",
        "recoverable-answer",
        "recoverable-request",
        "note=ready",
        "--json",
    ]
    assert main(answer_command) == 0
    answered = json.loads(capsys.readouterr().out)
    assert answered["request"]["request_id"] == "recoverable-answer"
    assert answered["request"]["actor"] == "pi"
    assert answered["request"]["causal_refs"] == [{"id": "recoverable-request"}]
    assert answered["request"]["args"]["answers"] == {"note": "ready"}
    assert answered["request"]["job"]["request_envelope"]["args"] == answered["request"]["args"]
    original = state.request_detail(state.request_row(workspace, "recoverable-request"))
    assert original["status"] == "cancelled"
    assert original["args"] == original_before["args"]
    assert original["job"]["request_envelope"] == original_before["job"]["request_envelope"]

    assert main(answer_command) == 0
    answer_retry = json.loads(capsys.readouterr().out)
    assert answer_retry["request"]["request_id"] == "recoverable-answer"
    assert (
        main(
            [
                *answer_command[:-2],
                "note=changed",
                "--json",
            ]
        )
        == 2
    )
    changed_retry = json.loads(capsys.readouterr().out)
    assert "idempotency key is already bound" in changed_retry["error"]
    with state.connect(workspace) as conn:
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM operation_requests WHERE request_id = 'recoverable-answer'"
            ).fetchone()[0]
            == 1
        )

    assert (
        main(
            [
                "request",
                "amend",
                "--workspace",
                str(workspace),
                "--idempotency-key",
                "recoverable-amend",
                "recoverable-answer",
                "k=3",
                "--json",
            ]
        )
        == 0
    )
    amended = json.loads(capsys.readouterr().out)
    assert amended["request"]["request_id"] == "recoverable-amend"
    assert amended["request"]["args"]["k"] == 3
    assert amended["request"]["args"]["answers"] == {"note": "ready"}
    assert amended["request"]["job"]["request_envelope"]["args"] == amended["request"]["args"]
    answered_source = state.request_detail(state.request_row(workspace, "recoverable-answer"))
    assert answered_source["status"] == "cancelled"
    assert answered_source["args"]["k"] == 1
    assert answered_source["job"]["request_envelope"]["args"] == answered_source["args"]

    assert (
        main(
            [
                "request",
                "cancel",
                "--workspace",
                str(workspace),
                "recoverable-amend",
                "--reason",
                "not needed",
                "--json",
            ]
        )
        == 0
    )
    cancelled = json.loads(capsys.readouterr().out)
    assert cancelled["request"]["status"] == "cancelled"
    assert cancelled["request"]["job"]["request_envelope"]["args"] == cancelled["request"]["args"]

    assert (
        main(
            [
                "request",
                "list",
                "--workspace",
                str(workspace),
                "--status",
                "cancelled",
                "--json",
            ]
        )
        == 0
    )
    cancelled_list = json.loads(capsys.readouterr().out)
    assert {row["request_id"] for row in cancelled_list["requests"]} == {
        "recoverable-request",
        "recoverable-answer",
        "recoverable-amend",
    }

    assert (
        main(["request", "retry", "--workspace", str(workspace), "recoverable-amend", "--json"])
        == 0
    )
    retried = json.loads(capsys.readouterr().out)
    assert retried["request"]["status"] == "pending"
    assert retried["request"]["job"]["request_envelope"]["args"] == retried["request"]["args"]

    assert (
        main(["request", "retry", "--workspace", str(workspace), "recoverable-amend", "--json"])
        == 2
    )
    retry_pending = json.loads(capsys.readouterr().out)
    assert retry_pending["ok"] is False
    assert "failed or cancelled" in retry_pending["error"]

    assert main(["steering", "show", "--workspace", str(workspace), "--json"]) == 0
    steering = json.loads(capsys.readouterr().out)
    assert steering["path"] == "steering.md"

    assert (
        main(
            [
                "steering",
                "edit",
                "--workspace",
                str(workspace),
                "--body",
                "# Steering\n\nUpdated.",
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert "Updated." in (workspace / "steering.md").read_text(encoding="utf-8")

    assert main(["vocab", "list", "--workspace", str(workspace), "--json"]) == 0
    vocabulary = json.loads(capsys.readouterr().out)
    assert "research_area" in vocabulary["vocabulary"]

    assert (
        main(
            [
                "vocab",
                "add",
                "--workspace",
                str(workspace),
                "research_area",
                "alpha-topic",
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert (
        main(
            [
                "vocab",
                "rename",
                "--workspace",
                str(workspace),
                "research_area",
                "alpha-topic",
                "beta-topic",
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert "beta-topic" in (workspace / "system/vocabulary.md").read_text(encoding="utf-8")

    assert main(["workspace", "scan", "--workspace", str(workspace), "--json"]) == 0
    scan = json.loads(capsys.readouterr().out)
    assert scan["result"]["observed_count"] == 1
    assert scan["result"]["paths"] == ["digests/hub-seed.md"]

    assert (
        main(
            [
                "workspace",
                "check",
                "--workspace",
                str(workspace),
                "--schedule-id",
                "structural-check",
                "--json",
            ]
        )
        == 0
    )
    check = json.loads(capsys.readouterr().out)
    assert check["ok"] is True
    assert check["schedule_id"] == "structural-check"
    assert {job["request_envelope"]["schedule_id"] for job in check["jobs"]} == {"structural-check"}

    assert (
        main(
            [
                "workspace",
                "export",
                "--workspace",
                str(workspace),
                "--output",
                str(export_path),
                "--json",
            ]
        )
        == 0
    )
    exported = json.loads(capsys.readouterr().out)
    assert exported["export"]["output"] == str(export_path)
    assert export_path.is_file()

    assert main(["journal", "tail", "--workspace", str(workspace), "--limit", "5", "--json"]) == 0
    journal = json.loads(capsys.readouterr().out)
    event_id = journal["events"][0]["event_id"]
    assert main(["journal", "show", "--workspace", str(workspace), str(event_id), "--json"]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["event"]["event_id"] == event_id


def test_cli_workspace_scan_fixture_quarantines_generated_projection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "workspace",
                "scan",
                "--workspace",
                str(workspace),
                "--fixture",
                "direct-write-generated-projection",
                "--idempotency-key",
                "projection-scan",
                "--json",
            ]
        )
        == 0
    )
    scan = json.loads(capsys.readouterr().out)

    assert scan["fixture"] == {
        "name": "direct-write-generated-projection",
        "path": "index.md",
    }
    assert scan["quarantine"]["finding_count"] == 1
    assert scan["quarantine"]["findings"][0]["target_id"] == "index.md"
    assert "index.md" in scan["regeneration"]["changed"]
    assert scan["result"]["observed_count"] == 0
    assert scan["job"]["job_id"] == "projection-scan"
    assert scan["quarantine_job"]["job_id"] == "projection-scan_trace-integrity-scan"
    assert scan["regeneration_job"]["job_id"] == "projection-scan_regenerate-tracked-projections"
    assert (workspace / "index.md").is_file()
    assert "direct-write-generated-projection fixture" not in (workspace / "index.md").read_text(
        encoding="utf-8"
    )
    assert (workspace / ".memoria/quarantine/index.md").is_file()
    with state.connect(workspace) as conn:
        consumable = conn.execute(
            "SELECT output_id FROM consumable_outputs WHERE output_id = 'index.md'"
        ).fetchone()
    assert consumable is None


def test_cli_workspace_check_declares_integrity_actor(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    assert main(["workspace", "check", "--workspace", str(workspace), "--json"]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["ok"] is True
    with state.connect(workspace) as conn:
        rows = conn.execute(
            "SELECT operation_id, actor FROM operation_requests ORDER BY operation_id"
        ).fetchall()
    assert {row["operation_id"] for row in rows} == set(INTEGRITY_SWEEP_OPERATIONS)
    assert {row["actor"] for row in rows} == {"integrity"}


def test_cli_workspace_check_namespaces_one_idempotency_key_per_operation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    command = [
        "workspace",
        "check",
        "--workspace",
        str(workspace),
        "--idempotency-key",
        "manual-check",
        "--json",
    ]

    assert main(command) == 0
    first = json.loads(capsys.readouterr().out)
    assert main(command) == 0
    retry = json.loads(capsys.readouterr().out)

    assert first["ok"] is True
    assert retry["ok"] is True
    with state.connect(workspace) as conn:
        rows = conn.execute(
            "SELECT request_id, operation_id FROM operation_requests ORDER BY operation_id"
        ).fetchall()
    assert len(rows) == len(INTEGRITY_SWEEP_OPERATIONS)
    assert {row["operation_id"] for row in rows} == set(INTEGRITY_SWEEP_OPERATIONS)
    assert {row["request_id"] for row in rows} == {
        f"manual-check_{operation_id}" for operation_id in INTEGRITY_SWEEP_OPERATIONS
    }


def test_cli_workspace_recover_fixture_replays_pending_materialization(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "workspace",
                "recover",
                "--workspace",
                str(workspace),
                "--fixture",
                "crash-before-materialization",
                "--json",
            ]
        )
        == 0
    )
    recovered = json.loads(capsys.readouterr().out)

    target = "notes/crash-before-materialization.md"
    assert recovered["fixture"] == {"name": "crash-before-materialization", "path": target}
    assert recovered["restored"] == [target]
    assert "check_status" not in read_frontmatter(workspace / target)
    assert state.concept_check_status(workspace, target) == "checked"
    with state.connect(workspace) as conn:
        consumable = conn.execute(
            "SELECT output_id FROM consumable_outputs WHERE output_id = ?", (target,)
        ).fetchone()
    assert consumable["output_id"] == target


def test_cli_workspace_recover_fails_running_requests_for_retry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    job = enqueue_operation(
        workspace,
        "answer-query",
        payload={"query": "status"},
        idempotency_key="stuck-request",
        actor="pi",
    )
    state.set_request_running(workspace, "stuck-request", job)

    assert main(["workspace", "recover", "--workspace", str(workspace), "--json"]) == 0
    recovered = json.loads(capsys.readouterr().out)

    assert recovered["failed_requests"] == ["stuck-request"]
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT status, error FROM operation_requests WHERE request_id = ?",
            ("stuck-request",),
        ).fetchone()
    assert tuple(row) == ("failed", "interrupted during workspace recovery; retry required")

    assert main(["request", "retry", "--workspace", str(workspace), "stuck-request", "--json"]) == 0
    retried = json.loads(capsys.readouterr().out)
    assert retried["request"]["status"] == "pending"


def test_cli_journal_list_operation_alias_includes_digest_workflow(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    append_journal_event(
        workspace,
        {"event": "run", "workflow": "compile-source-digest", "status": "done"},
        machine="memoria-cli",
    )
    append_journal_event(
        workspace,
        {"event": "run", "workflow": "regenerate-tracked-projections", "status": "done"},
        machine="memoria-cli",
    )

    assert (
        main(
            [
                "journal",
                "tail",
                "--workspace",
                str(workspace),
                "--operation",
                "work.digest",
                "--json",
            ]
        )
        == 0
    )
    journal = json.loads(capsys.readouterr().out)

    assert [event["payload"]["workflow"] for event in journal["events"]] == [
        "compile-source-digest"
    ]


def test_cli_journal_list_filters_by_request_path_decision_and_date(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    alpha = append_journal_event(
        workspace,
        {
            "event": "policy",
            "operation": "check-source-metadata",
            "request_id": "req-alpha",
            "target_id": "notes/alpha.md",
            "decision": "deny",
        },
        machine="memoria-cli",
    )
    append_journal_event(
        workspace,
        {
            "event": "policy",
            "operation": "check-source-metadata",
            "request_id": "req-beta",
            "target_id": "notes/beta.md",
            "decision": "allow",
        },
        machine="memoria-cli",
    )

    assert (
        main(
            [
                "journal",
                "tail",
                "--workspace",
                str(workspace),
                "--operation",
                "check-source-metadata",
                "--request-id",
                "req-alpha",
                "--path",
                "notes/alpha.md",
                "--decision",
                "deny",
                "--date",
                alpha["timestamp"][:10],
                "--json",
            ]
        )
        == 0
    )
    journal = json.loads(capsys.readouterr().out)

    assert [event["payload"]["request_id"] for event in journal["events"]] == ["req-alpha"]


def test_cli_workspace_rebuild_writes_checked_search_index(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    note = workspace / "notes/search.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(
        "---\ntype: note\ncheck_status: checked\ntitle: search\n---\nalpha search\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "notes/search.md", "note")

    rc = main(
        [
            "workspace",
            "rebuild",
            "--workspace",
            str(workspace),
            "--search",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["search"]["engine"] == "bm25"
    assert output["search"]["manifest"]["mode"] == "bm25"
    assert output["search"]["manifest"]["documents"][0]["path"] == "notes/search.md"
    assert (workspace / ".memoria/index/search/checked/notes/search.md").is_file()

    rc = main(["doctor", "--workspace", str(workspace), "--check", "search", "--json"])
    doctor = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert doctor["ok"] is True
    assert doctor["search_document_count"] == 1
