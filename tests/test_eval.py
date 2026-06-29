"""vault-eval (ADR-11): the shipped gold set validates; dispatch fans it out
as one idempotent kanban card per (current task, quarter), never gating."""

import datetime
import re
from pathlib import Path

import tasks_mcp
import yaml
from operations.telemetry.eval import eval_dispatch

SRC = Path(__file__).resolve().parent.parent / "vault-template"
EVAL = SRC / "system" / "eval"

REQUIRED_SECTIONS = ("## Input", "## Expected behavior", "## Scoring rubric")


def _gold_files():
    return [
        p
        for p in sorted(EVAL.glob("*.md"))
        if not p.name.startswith("_") and p.name not in ("README.md", "last-run.md")
    ]


def _frontmatter(path: Path) -> dict:
    m = re.match(r"^---\n(.*?)\n---", path.read_text(encoding="utf-8"), re.S)
    assert m, f"{path.name}: no frontmatter block"
    return yaml.safe_load(m.group(1))


# --------------------------------------------------------------------------- #
# The shipped gold set                                                         #
# --------------------------------------------------------------------------- #
def test_shipped_gold_tasks_have_valid_dispatch_shape():
    files = _gold_files()
    assert len(files) >= 8, "the gold set ships ≥ 2 tasks per workflow"
    for p in files:
        fm = _frontmatter(p)
        assert fm["type"] == "eval-task", p.name
        assert fm["lane"] in eval_dispatch.LANE_PROFILE, p.name
        assert fm["lifecycle"] in {"current", "archived"}, p.name


def test_gold_tasks_are_self_contained():
    """Every task carries input, expected behavior, and a scoring rubric."""
    for p in _gold_files():
        body = p.read_text(encoding="utf-8")
        for section in REQUIRED_SECTIONS:
            assert section in body, f"{p.name} missing section {section}"


def test_gold_set_covers_the_four_minimum_workflows():
    by_workflow: dict[str, int] = {}
    for p in _gold_files():
        fm = _frontmatter(p)
        by_workflow[fm["workflow"]] = by_workflow.get(fm["workflow"], 0) + 1
    for wf in ("find", "extract", "link", "verify"):
        assert by_workflow.get(wf, 0) >= 2, f"workflow {wf} needs ≥ 2 gold tasks"


def test_lane_profile_mirrors_tasks_mcp():
    """The dispatcher's lane → profile map cannot drift from the Co-PI's (ADR-48)."""
    assert eval_dispatch.LANE_PROFILE == tasks_mcp.LANE_PROFILE


def test_gold_task_lanes_match_the_routed_lanes():
    lanes = {_frontmatter(path)["lane"] for path in _gold_files()}
    assert lanes <= set(eval_dispatch.LANE_PROFILE)


# --------------------------------------------------------------------------- #
# Dispatch                                                                     #
# --------------------------------------------------------------------------- #
def _fixture_vault(tmp_path: Path) -> Path:
    d = tmp_path / "system/eval"
    d.mkdir(parents=True)
    (d / "README.md").write_text("# not a task\n", encoding="utf-8")
    (d / "find-x.md").write_text(
        "---\ntype: eval-task\ntitle: Find X\nlifecycle: current\n"
        "workflow: find\nlane: catalog\n---\n## Input\nQ\n"
        "## Expected behavior\nE\n## Scoring rubric\nR\n",
        encoding="utf-8",
    )
    (d / "verify-y.md").write_text(
        "---\ntype: eval-task\ntitle: Verify Y\nlifecycle: current\n"
        "workflow: verify\nlane: verify\n---\n## Input\nQ\n"
        "## Expected behavior\nE\n## Scoring rubric\nR\n",
        encoding="utf-8",
    )
    (d / "retired.md").write_text(
        "---\ntype: eval-task\ntitle: Old\nlifecycle: archived\n"
        "workflow: find\nlane: catalog\n---\nbody\n",
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
    assert not (v / "system/eval/last-run.md").exists()
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
    text = (v / "system/eval/last-run.md").read_text(encoding="utf-8")
    assert "2026-Q2" in text and "find-x" in text and "k-42" in text
    # plain markdown, no YAML frontmatter — last-run is untyped system infra
    assert not text.startswith("---")


def test_card_body_carries_the_noncommitting_contract():
    tasks = eval_dispatch.load_gold_tasks(SRC)
    assert len(tasks) >= 8  # the shipped gold set loads from vault-template/
    card = eval_dispatch.card_for(tasks[0], "2026-Q2")
    assert "Do NOT write to the vault" in card["body"]
    assert card["goal"].startswith("vault-eval 2026-Q2:")
