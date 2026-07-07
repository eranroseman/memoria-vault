#!/usr/bin/env python3
"""Report alpha.16 dogfood checkpoint state for an existing workspace."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT / "src", ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from memoria_vault.engine import api as engine_api
from memoria_vault.runtime import state

REQUIRED_DONE = {
    "capture-source",
    "enrich-source",
    "compile-source-digest",
    "answer-query",
    "export-project",
    "run-seeded-error-verdict",
}


def snapshot_workspace(workspace: Path) -> dict[str, Any]:
    workspace = Path(workspace)
    concept_counts, unchecked_backlog = _concept_counts(workspace)
    output_counts, unchecked_outputs = _output_counts(workspace)
    requests, request_counts = _request_counts(workspace)
    works = state.catalog_sources(workspace, checked_only=False)
    checked_works = [
        row
        for row in works
        if state.concept_check_status(workspace, f"catalog/sources/{row['work_id']}") == "checked"
    ]
    attention = engine_api.read_attention(workspace)["attention"]
    attention_counts = _status_counts(attention)
    return {
        "workspace": str(workspace),
        "status": _read_status(workspace),
        "catalog_work_count": len(works),
        "checked_work_count": len(checked_works),
        "concept_counts": concept_counts,
        "output_counts": output_counts,
        "unchecked_backlog": unchecked_backlog,
        "unchecked_output_backlog": unchecked_outputs,
        "attention": attention,
        "attention_counts": attention_counts,
        "requests": requests,
        "request_counts": request_counts,
        "model_call_count": _journal_event_count(workspace, "model_call"),
        "final_state": {
            "has_checked_work": bool(checked_works),
            "has_checked_digest": concept_counts.get("digest", {}).get("checked", 0) > 0,
            "has_checked_note": concept_counts.get("note", {}).get("checked", 0) > 0,
            "has_project": sum(concept_counts.get("project", {}).values()) > 0,
            "has_bibliography_bib": (workspace / "bibliography.bib").is_file(),
        },
    }


def dogfood_report(
    snapshot: dict[str, Any],
    *,
    previous_report: Path | None = None,
    limits: dict[str, int | None] | None = None,
) -> dict[str, Any]:
    request_counts = snapshot["request_counts"]
    seeded_verdict = _latest_seeded_verdict(snapshot["requests"])
    assertions = dict(snapshot["final_state"])
    assertions.update(
        {
            "required_requests_done": REQUIRED_DONE <= set(request_counts.get("done", {})),
            "seeded_error_passed": bool(seeded_verdict and seeded_verdict.get("passed") is True),
        }
    )
    request_total = len(snapshot["requests"])
    checked_work_count = int(snapshot["checked_work_count"])
    model_calls = int(snapshot["model_call_count"])
    assertions.update(assert_dogfood_checkpoint(model_calls, request_total, limits=limits))
    return {
        "schema_version": 1,
        "workspace": snapshot["workspace"],
        "passed": all(assertions.values()),
        "assertions": assertions,
        "state": {
            "catalog_work_count": snapshot["catalog_work_count"],
            "checked_work_count": checked_work_count,
            "concept_counts": snapshot["concept_counts"],
            "output_counts": snapshot["output_counts"],
            "unchecked_backlog": snapshot["unchecked_backlog"],
            "unchecked_output_backlog": snapshot["unchecked_output_backlog"],
            "attention_counts": snapshot["attention_counts"],
        },
        "friction": {
            "operation_request_count": request_total,
            "per_work_interaction_count": _rate(request_total, checked_work_count),
            "unchecked_backlog_slope": _unchecked_backlog_slope(
                snapshot["unchecked_backlog"], previous_report
            ),
            "open_attention_count": snapshot["attention_counts"].get("open", 0),
            "resolved_attention_count": snapshot["attention_counts"].get("resolved", 0),
        },
        "budgets": {
            "model_call_count": model_calls,
            "tool_call_count": request_total,
            "limits": _clean_limits(limits),
            "cost_observed": False,
        },
        "requests": snapshot["request_counts"],
        "seeded_error_verdict": seeded_verdict or {},
    }


def build_report(
    workspace: Path,
    *,
    previous_report: Path | None = None,
    limits: dict[str, int | None] | None = None,
) -> dict[str, Any]:
    return dogfood_report(
        snapshot_workspace(workspace), previous_report=previous_report, limits=limits
    )


def assert_dogfood_checkpoint(
    model_call_count: int,
    tool_call_count: int,
    *,
    limits: dict[str, int | None] | None = None,
) -> dict[str, bool]:
    limits = limits or {}
    assertions: dict[str, bool] = {}
    if limits.get("max_model_calls") is not None:
        assertions["model_calls_within_limit"] = model_call_count <= int(limits["max_model_calls"])
    if limits.get("max_tool_calls") is not None:
        assertions["tool_calls_within_limit"] = tool_call_count <= int(limits["max_tool_calls"])
    return assertions


def _read_status(workspace: Path) -> dict[str, Any]:
    if not state.db_path(workspace).is_file():
        return {
            "workspace": str(workspace),
            "db": state.DB_REL,
            "requests": {},
        }
    return engine_api.read_status(workspace)


def _concept_counts(workspace: Path) -> tuple[dict[str, dict[str, int]], int]:
    if not state.db_path(workspace).is_file():
        return {}, 0
    counts: dict[str, dict[str, int]] = {}
    unchecked = 0
    with state.connect(workspace) as conn:
        rows = conn.execute(
            """
            SELECT concept_type, check_status, COUNT(*) AS count
            FROM concept_status
            GROUP BY concept_type, check_status
            """
        ).fetchall()
    for row in rows:
        concept_type = str(row["concept_type"])
        check_status = str(row["check_status"])
        count = int(row["count"])
        counts.setdefault(concept_type, {})[check_status] = count
        if check_status == "unchecked":
            unchecked += count
    sorted_counts = {key: dict(sorted(value.items())) for key, value in sorted(counts.items())}
    return sorted_counts, unchecked


def _output_counts(workspace: Path) -> tuple[dict[str, int], int]:
    if not state.db_path(workspace).is_file():
        return {}, 0
    with state.connect(workspace) as conn:
        rows = conn.execute(
            """
            SELECT check_status, COUNT(*) AS count
            FROM outputs
            GROUP BY check_status
            """
        ).fetchall()
    counts = {str(row["check_status"]): int(row["count"]) for row in rows}
    return dict(sorted(counts.items())), counts.get("unchecked", 0)


def _request_counts(workspace: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    if not state.db_path(workspace).is_file():
        return [], {}
    with state.connect(workspace) as conn:
        rows = conn.execute(
            """
            SELECT request_id, operation_id, status, job_json
            FROM operation_requests
            ORDER BY created_at, request_id
            """
        ).fetchall()
    requests = [
        {
            "request_id": str(row["request_id"]),
            "operation_id": str(row["operation_id"]),
            "status": str(row["status"]),
            "job": json.loads(row["job_json"]),
        }
        for row in rows
    ]
    counts: dict[str, Counter[str]] = {}
    for row in requests:
        counts.setdefault(row["status"], Counter())[row["operation_id"]] += 1
    return requests, {
        status: dict(sorted(counter.items())) for status, counter in sorted(counts.items())
    }


def _journal_event_count(workspace: Path, event_type: str) -> int:
    if not state.db_path(workspace).is_file():
        return 0
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM event_log WHERE event_type = ?",
            (event_type,),
        ).fetchone()
    return int(row["count"] if row is not None else 0)


def _status_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(row.get("status") or "") for row in rows)
    counts.pop("", None)
    return dict(sorted(counts.items()))


def _latest_seeded_verdict(requests: list[dict[str, Any]]) -> dict[str, Any] | None:
    for row in reversed(requests):
        if row["operation_id"] == "run-seeded-error-verdict" and row["status"] == "done":
            job = row["job"]
            return {
                "passed": bool(job.get("passed")),
                "mode": str(job.get("mode") or ""),
                "verdict_key": str(job.get("verdict_key") or ""),
                "non_sandbox_licensed": bool(job.get("non_sandbox_licensed")),
            }
    return None


def _unchecked_backlog_slope(current: int, previous_report: Path | None) -> int | None:
    if previous_report is None:
        return None
    previous = json.loads(Path(previous_report).read_text(encoding="utf-8"))
    previous_count = int(previous.get("state", {}).get("unchecked_backlog", current))
    return current - previous_count


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 3) if denominator else 0.0


def _clean_limits(limits: dict[str, int | None] | None) -> dict[str, int]:
    return {key: int(value) for key, value in (limits or {}).items() if value is not None}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace", type=Path, default=Path("~/memoria-vault/sandbox/vault").expanduser()
    )
    parser.add_argument("--previous-report", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--max-model-calls", type=int)
    parser.add_argument("--max-tool-calls", type=int)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = build_report(
        args.workspace,
        previous_report=args.previous_report,
        limits={
            "max_model_calls": args.max_model_calls,
            "max_tool_calls": args.max_tool_calls,
        },
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(
        payload if args.json else f"dogfood-checkpoint: {'PASS' if report['passed'] else 'REVIEW'}"
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
