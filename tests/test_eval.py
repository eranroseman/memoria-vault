"""vault-eval dispatches local eval tasks when a workspace authors them."""

import datetime
import json
import sys
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.subsystems.telemetry.eval import eval_dispatch
from tests.helpers import WORKSPACE_SEED, call_with_context, init_cli_workspace


def dispatch(vault: Path, *args, **kwargs):
    return call_with_context(eval_dispatch.dispatch, vault, *args, **kwargs)


def test_eval_role_assignees_cover_supported_roles():
    assert set(eval_dispatch.EVAL_ROLE_ASSIGNEE) == {
        "catalog",
        "extract",
        "link",
        "map",
        "verify",
    }


def test_package_seed_ships_no_markdown_gold_tasks():
    assert eval_dispatch.load_gold_tasks(WORKSPACE_SEED) == []


def test_gold_task_roles_match_the_routed_roles(tmp_path):
    tasks = eval_dispatch.load_gold_tasks(_fixture_vault(tmp_path))
    roles = {task["eval_role"] for task in tasks}
    assert roles <= set(eval_dispatch.EVAL_ROLE_ASSIGNEE)


def _fixture_vault(tmp_path: Path) -> Path:
    d = tmp_path / ".memoria/eval"
    d.mkdir(parents=True, exist_ok=True)
    (d / "README.md").write_text("# not a task\n", encoding="utf-8")
    (d / "find-x.md").write_text(
        "---\ntype: eval-task\ntitle: Find X\nlifecycle: current\n"
        "workflow: find\neval_role: catalog\n---\n## Input\nQ\n"
        "## Expected behavior\nE\n## Scoring rubric\nR\n",
        encoding="utf-8",
    )
    (d / "verify-y.md").write_text(
        "---\ntype: eval-task\ntitle: Verify Y\nlifecycle: current\n"
        "workflow: verify\neval_role: verify\n---\n## Input\nQ\n"
        "## Expected behavior\nE\n## Scoring rubric\nR\n",
        encoding="utf-8",
    )
    (d / "retired.md").write_text(
        "---\ntype: eval-task\ntitle: Old\nlifecycle: archived\n"
        "workflow: find\neval_role: catalog\n---\nbody\n",
        encoding="utf-8",
    )
    (d / "notes.md").write_text("---\ntopic: scratch\n---\nuntyped\n", encoding="utf-8")
    return tmp_path


def test_dry_run_produces_the_right_payload_set(tmp_path, capsys):
    v = _fixture_vault(tmp_path)
    out = dispatch(v, dry_run=True, today=datetime.date(2026, 6, 10))
    assert out["quarter"] == "2026-Q2" and out["dry_run"] is True
    rows = {r["task"]: r for r in out["dispatched"]}
    # current tasks only — README, the archived task, and untyped files skipped
    assert set(rows) == {"find-x", "verify-y"}
    assert rows["find-x"]["assignee"] == "memoria-librarian"
    assert rows["verify-y"]["assignee"] == "memoria-peer-reviewer"
    assert rows["find-x"]["idempotency_key"] == "eval:find-x:2026-Q2"
    # dry-run prints instead of creating, and writes no dispatch record
    assert "eval:verify-y:2026-Q2" in capsys.readouterr().out
    assert not (v / ".memoria/eval/last-run.md").exists()
    assert all(r["intent_id"] == "DRY" for r in out["dispatched"])


def test_dispatch_is_idempotent_per_task_and_quarter(tmp_path, monkeypatch):
    v = _fixture_vault(tmp_path)
    created: list[dict] = []
    monkeypatch.setattr(
        eval_dispatch,
        "create_task_intent",
        lambda payload: created.append(payload) or "intent-1",
    )
    day = datetime.date(2026, 5, 1)
    dispatch(v, today=day)
    dispatch(v, today=day)  # an on-demand re-run inside the quarter
    keys = [c["idempotency_key"] for c in created]
    # same quarter -> identical keys; the intent runner deduplicates per task
    assert keys[:2] == ["eval:find-x:2026-Q2", "eval:verify-y:2026-Q2"]
    assert keys[2:] == keys[:2]
    # a new quarter re-opens the window
    dispatch(v, today=datetime.date(2026, 7, 1))
    assert created[-1]["idempotency_key"] == "eval:verify-y:2026-Q3"


def test_dispatch_records_last_run(tmp_path, monkeypatch):
    v = _fixture_vault(tmp_path)
    monkeypatch.setattr(eval_dispatch, "create_task_intent", lambda payload: "k-42")
    dispatch(v, today=datetime.date(2026, 6, 10))
    text = (v / ".memoria/eval/last-run.md").read_text(encoding="utf-8")
    assert "2026-Q2" in text and "find-x" in text and "k-42" in text
    # plain markdown, no YAML frontmatter — last-run is untyped system infra
    assert not text.startswith("---")


def test_payload_body_carries_the_noncommitting_contract(tmp_path):
    tasks = eval_dispatch.load_gold_tasks(_fixture_vault(tmp_path))
    payload = eval_dispatch.payload_for(tasks[0], "2026-Q2")
    assert "Do NOT write to the vault" in payload["body"]
    assert payload["goal"].startswith("vault-eval 2026-Q2:")


def test_main_dry_run_uses_persisted_operation_context(tmp_path, capsys, monkeypatch):
    vault = _fixture_vault(init_cli_workspace(tmp_path, capsys))
    seen = _capture_dispatch_context(monkeypatch)
    monkeypatch.setattr(
        sys,
        "argv",
        ["eval_dispatch.py", "--vault", str(vault), "--dry-run"],
    )

    eval_dispatch.main()

    assert "planned (dry-run)" in capsys.readouterr().out
    _assert_main_request(vault, dry_run=True, seen=seen)
    assert not (vault / ".memoria/eval/last-run.md").exists()


def test_main_live_run_uses_persisted_operation_context(tmp_path, capsys, monkeypatch):
    vault = _fixture_vault(init_cli_workspace(tmp_path, capsys))
    seen = _capture_dispatch_context(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["eval_dispatch.py", "--vault", str(vault)])

    eval_dispatch.main()

    assert "2 gold task(s) dispatched" in capsys.readouterr().out
    _assert_main_request(vault, dry_run=False, seen=seen)
    assert (vault / ".memoria/eval/last-run.md").is_file()


def _capture_dispatch_context(monkeypatch):
    seen = {}
    original = eval_dispatch.dispatch

    def capture(vault, dry_run=False, today=None, *, context):
        seen["context"] = context
        return original(vault, dry_run=dry_run, today=today, context=context)

    monkeypatch.setattr(eval_dispatch, "dispatch", capture)
    return seen


def _assert_main_request(vault: Path, *, dry_run: bool, seen: dict) -> None:
    with state.connect(vault) as conn:
        row = conn.execute(
            """
            SELECT request_id, actor, args_json, provenance_json, status
            FROM operation_requests
            WHERE operation_id = 'eval-run'
            """
        ).fetchone()
    assert row["actor"] == "operation"
    assert json.loads(row["args_json"]) == {"dry_run": dry_run}
    assert json.loads(row["provenance_json"]) == {
        "command": "eval-dispatch",
        "surface": "memoria-eval",
    }
    assert row["status"] == "done"
    context = seen["context"]
    assert context.actor == "operation"
    assert context.request_id == row["request_id"]
    assert context.operation_id == "eval-run"
    assert context.machine == "memoria-eval"
