"""Tests for the alpha.16 dogfood checkpoint report."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.policy.audit import EMPTY_SHA256
from memoria_vault.runtime.worker import enqueue_operation

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/sandbox/alpha15_dogfood_checkpoint.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("alpha15_dogfood_checkpoint", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_dogfood_checkpoint_reports_state_and_friction_metrics(tmp_path: Path) -> None:
    mod = _load_script()
    _seed_checkpoint_workspace(tmp_path, mod.REQUIRED_DONE)
    previous = tmp_path / "previous.json"
    previous.write_text(json.dumps({"state": {"unchecked_backlog": 3}}), encoding="utf-8")

    report = mod.build_report(
        tmp_path,
        previous_report=previous,
        limits={"max_model_calls": 1, "max_tool_calls": 6},
    )

    assert report["passed"] is True
    assert report["assertions"] == {
        "has_checked_work": True,
        "has_checked_digest": True,
        "has_checked_note": True,
        "has_project": True,
        "has_bibliography_bib": True,
        "required_requests_done": True,
        "seeded_error_passed": True,
        "model_calls_within_limit": True,
        "tool_calls_within_limit": True,
    }
    assert report["state"]["checked_work_count"] == 1
    assert report["state"]["unchecked_backlog"] == 1
    assert report["state"]["unchecked_output_backlog"] == 1
    assert report["state"]["output_counts"] == {"checked": 3, "unchecked": 1}
    assert report["state"]["attention_counts"] == {"open": 1, "resolved": 1}
    assert report["friction"]["operation_request_count"] == 6
    assert report["friction"]["per_work_interaction_count"] == 6.0
    assert report["friction"]["unchecked_backlog_slope"] == -2
    assert report["friction"]["open_attention_count"] == 1
    assert report["friction"]["resolved_attention_count"] == 1
    assert report["budgets"]["model_call_count"] == 1
    assert report["budgets"]["tool_call_count"] == 6
    assert report["budgets"]["limits"] == {"max_model_calls": 1, "max_tool_calls": 6}
    assert report["seeded_error_verdict"]["non_sandbox_licensed"] is True


def test_dogfood_checkpoint_fails_over_budget(tmp_path: Path) -> None:
    mod = _load_script()
    _seed_checkpoint_workspace(tmp_path, mod.REQUIRED_DONE)

    report = mod.build_report(tmp_path, limits={"max_model_calls": 0})

    assert report["passed"] is False
    assert report["assertions"]["model_calls_within_limit"] is False


def test_dogfood_checkpoint_main_returns_review_when_assertions_fail(tmp_path: Path) -> None:
    mod = _load_script()

    assert mod.main(["--workspace", str(tmp_path), "--json"]) == 1


def _seed_checkpoint_workspace(vault: Path, required_operations: set[str]) -> None:
    vault.mkdir(parents=True, exist_ok=True)
    state.upsert_catalog_record(
        vault,
        source_id="work-alpha",
        title="Work Alpha",
        description="Fixture work.",
        check_status="checked",
        citekey="alpha2026",
    )
    for rel, concept_type, check_status in (
        ("works/work-alpha/digest.md", "digest", "checked"),
        ("notes/note-alpha.md", "note", "checked"),
        ("projects/project-alpha/project.md", "project", "checked"),
        ("notes/unchecked-alpha.md", "note", "unchecked"),
    ):
        state.record_observed_file_edit(
            vault,
            output_id=rel,
            concept_type=concept_type,
            output_sha256=EMPTY_SHA256,
        )
        state.set_concept_verdict(vault, rel, check_status)
    (vault / "bibliography.bib").write_text("@article{alpha2026}\n", encoding="utf-8")
    _write_attention(vault / "inbox/open-alpha.md", "open")
    _write_attention(vault / "inbox/resolved-alpha.md", "resolved")
    state.append_journal_event(vault, {"event": "model_call", "run_id": "run-alpha"})
    for operation_id in sorted(required_operations):
        job = enqueue_operation(vault, operation_id, idempotency_key=operation_id)
        job.update({"status": "done"})
        if operation_id == "run-seeded-error-verdict":
            job.update(
                {
                    "passed": True,
                    "mode": "live",
                    "verdict_key": "sha256:fixture",
                    "non_sandbox_licensed": True,
                }
            )
        state.finish_request(vault, job["job_id"], "done", job)


def _write_attention(path: Path, status: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        f"title: {status.title()} attention\n"
        "projection: attention\n"
        "attention_kind: flag\n"
        f"attention_status: {status}\n"
        "target: notes/note-alpha.md\n"
        "routing_class: ask\n"
        "---\n"
        "# Attention\n\nFixture.\n",
        encoding="utf-8",
    )
