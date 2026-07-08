"""vault-eval dispatches local eval tasks when a workspace authors them."""

import datetime
from pathlib import Path

from memoria_vault.runtime.subsystems.telemetry.eval import eval_dispatch
from tests.helpers import WORKSPACE_SEED


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
    d.mkdir(parents=True)
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


def test_dry_run_produces_the_right_card_set(tmp_path, capsys):
    v = _fixture_vault(tmp_path)
    out = eval_dispatch.dispatch(v, dry_run=True, today=datetime.date(2026, 6, 10))
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
    assert all(r["card_id"] == "DRY" for r in out["dispatched"])


def test_dispatch_is_idempotent_per_task_and_quarter(tmp_path, monkeypatch):
    v = _fixture_vault(tmp_path)
    created: list[dict] = []
    monkeypatch.setattr(eval_dispatch, "create_card", lambda card: created.append(card) or "card-1")
    day = datetime.date(2026, 5, 1)
    eval_dispatch.dispatch(v, today=day)
    eval_dispatch.dispatch(v, today=day)  # an on-demand re-run inside the quarter
    keys = [c["idempotency_key"] for c in created]
    # same quarter -> identical keys; the board dedups to one card per task
    assert keys[:2] == ["eval:find-x:2026-Q2", "eval:verify-y:2026-Q2"]
    assert keys[2:] == keys[:2]
    # a new quarter re-opens the window
    eval_dispatch.dispatch(v, today=datetime.date(2026, 7, 1))
    assert created[-1]["idempotency_key"] == "eval:verify-y:2026-Q3"


def test_dispatch_records_last_run(tmp_path, monkeypatch):
    v = _fixture_vault(tmp_path)
    monkeypatch.setattr(eval_dispatch, "create_card", lambda card: "k-42")
    eval_dispatch.dispatch(v, today=datetime.date(2026, 6, 10))
    text = (v / ".memoria/eval/last-run.md").read_text(encoding="utf-8")
    assert "2026-Q2" in text and "find-x" in text and "k-42" in text
    # plain markdown, no YAML frontmatter — last-run is untyped system infra
    assert not text.startswith("---")


def test_card_body_carries_the_noncommitting_contract(tmp_path):
    tasks = eval_dispatch.load_gold_tasks(_fixture_vault(tmp_path))
    card = eval_dispatch.card_for(tasks[0], "2026-Q2")
    assert "Do NOT write to the vault" in card["body"]
    assert card["goal"].startswith("vault-eval 2026-Q2:")
