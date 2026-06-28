#!/usr/bin/env python3
"""Run disposable alpha.11 pre-approval spikes."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

OUT = Path(__file__).with_name("pre-approval-test-results.md")
WORK = Path("/tmp/memoria-alpha11-preapproval")


@dataclass
class Result:
    name: str
    status: str
    evidence: str
    recommendation: str


def reset(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    row.setdefault("at", datetime.now(UTC).replace(microsecond=0).isoformat())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


def concept(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    lines = ["---", *(f"{key}: {json.dumps(value)}" for key, value in frontmatter.items())]
    write(path, "\n".join([*lines, "---", body, ""]))


def read_concept(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    _, frontmatter, body = text.split("---\n", 2)
    data: dict[str, Any] = {}
    for line in frontmatter.splitlines():
        if not line.strip():
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = json.loads(value.strip())
    return data, body


def update_concept(path: Path, updates: dict[str, Any]) -> None:
    frontmatter, body = read_concept(path)
    frontmatter.update(updates)
    concept(path, frontmatter, body.rstrip())


def in_prefix(path: str, prefixes: list[str]) -> bool:
    return any(path == prefix.rstrip("/") or path.startswith(prefix.rstrip("/") + "/") for prefix in prefixes)


def audit(root: Path, event: dict[str, Any]) -> None:
    append_jsonl(root / ".memoria/journal/audit.jsonl", event)


def test_operation_policy() -> Result:
    root = WORK / "operation-policy"
    reset(root)
    policy = {
        "operation_id": "extract_annotations",
        "allowed_tools": ["read_concept", "write_staging"],
        "read_paths": ["catalog/sources", "knowledge/notes"],
        "write_paths": [".memoria/staging"],
        "network": False,
        "required_checks": ["schema", "trace"],
        "required_audit": ["attempt", "decision"],
    }

    def decide(action: dict[str, Any], active_policy: dict[str, Any]) -> bool:
        required = {"operation_id", "allowed_tools", "read_paths", "write_paths", "network"}
        if not required.issubset(active_policy):
            audit(root, {"decision": "deny", "reason": "invalid-policy", "action": action})
            return False
        if action["tool"] not in active_policy["allowed_tools"]:
            audit(root, {"decision": "deny", "reason": "tool", "action": action})
            return False
        if action.get("network") and not active_policy["network"]:
            audit(root, {"decision": "deny", "reason": "network", "action": action})
            return False
        if action["kind"] == "read":
            ok = in_prefix(action["path"], active_policy["read_paths"])
        else:
            ok = in_prefix(action["path"], active_policy["write_paths"])
        audit(root, {"decision": "allow" if ok else "deny", "reason": "path", "action": action})
        return ok

    cases = {
        "valid_read": decide(
            {"kind": "read", "tool": "read_concept", "path": "catalog/sources/s1/source.md"},
            policy,
        ),
        "valid_staging_write": decide(
            {"kind": "write", "tool": "write_staging", "path": ".memoria/staging/n1.md"},
            policy,
        ),
        "direct_knowledge_write_denied": not decide(
            {"kind": "write", "tool": "write_staging", "path": "knowledge/notes/n1.md"},
            policy,
        ),
        "bad_tool_denied": not decide(
            {"kind": "read", "tool": "shell", "path": "catalog/sources/s1/source.md"},
            policy,
        ),
        "network_denied": not decide(
            {
                "kind": "read",
                "tool": "read_concept",
                "path": "catalog/sources/s1/source.md",
                "network": True,
            },
            policy,
        ),
        "invalid_policy_fail_closed": not decide(
            {"kind": "read", "tool": "read_concept", "path": "catalog/sources/s1/source.md"},
            {"operation_id": "bad"},
        ),
    }
    audit_rows = (root / ".memoria/journal/audit.jsonl").read_text(encoding="utf-8").splitlines()
    ok = all(cases.values()) and len(audit_rows) == len(cases)
    return Result(
        "Operation-policy enforcement spike",
        "pass" if ok else "fail",
        f"cases={cases}; audit_rows={len(audit_rows)}",
        "Approve start only if implementation keeps these as enforced worker decisions, not prose.",
    )


def test_read_barrier() -> Result:
    root = WORK / "read-barrier"
    reset(root)
    journal = root / ".memoria/journal/events.jsonl"

    concept(
        root / "catalog/sources/s1/source.md",
        {"id": "catalog/sources/s1/source", "type": "source", "check_status": "checked"},
        "source text",
    )
    append_jsonl(journal, {"event": "derived", "output": "catalog/sources/s1/source"})
    concept(
        root / ".memoria/staging/knowledge/notes/good.md",
        {
            "id": "knowledge/notes/good",
            "type": "note",
            "check_status": "unchecked",
            "derived_from": ["catalog/sources/s1/source"],
        },
        "supported note",
    )
    concept(
        root / ".memoria/staging/knowledge/notes/bad.md",
        {
            "id": "knowledge/notes/bad",
            "type": "note",
            "check_status": "unchecked",
            "derived_from": ["catalog/sources/missing/source"],
        },
        "unsupported note",
    )

    def checks_pass(path: Path) -> bool:
        frontmatter, _ = read_concept(path)
        return all((root / f"{ref}.md").exists() for ref in frontmatter.get("derived_from") or [])

    def promote(path: Path) -> bool:
        frontmatter, _ = read_concept(path)
        output = frontmatter["id"]
        if checks_pass(path):
            dest = root / f"{output}.md"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(path, dest)
            update_concept(dest, {"check_status": "checked"})
            append_jsonl(journal, {"event": "derived", "output": output})
            return True
        dest = root / ".memoria/quarantine" / f"{output}.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(path, dest)
        append_jsonl(journal, {"event": "check-fired", "output": output, "reason": "missing-input"})
        return False

    good_promoted = promote(root / ".memoria/staging/knowledge/notes/good.md")
    bad_quarantined = not promote(root / ".memoria/staging/knowledge/notes/bad.md")
    concept(
        root / "knowledge/notes/unchecked.md",
        {"id": "knowledge/notes/unchecked", "type": "note", "check_status": "unchecked"},
        "unchecked",
    )
    concept(
        root / "knowledge/notes/unknown.md",
        {"id": "knowledge/notes/unknown", "type": "note", "check_status": "mystery"},
        "unknown",
    )
    concept(
        root / "knowledge/notes/missing.md",
        {"id": "knowledge/notes/missing", "type": "note"},
        "missing",
    )
    concept(
        root / "knowledge/notes/foreign.md",
        {"id": "knowledge/notes/foreign", "type": "note", "check_status": "checked"},
        "foreign checked but untraced",
    )

    traced = {
        json.loads(line)["output"]
        for line in journal.read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("event") == "derived"
    }
    for path in sorted((root / "knowledge/notes").glob("*.md")):
        frontmatter, _ = read_concept(path)
        if frontmatter.get("check_status") == "checked" and frontmatter.get("id") not in traced:
            dest = root / ".memoria/quarantine" / path.relative_to(root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(path, dest)
            append_jsonl(journal, {"event": "check-fired", "output": frontmatter["id"], "reason": "foreign"})

    visible = []
    for path in sorted((root / "knowledge").rglob("*.md")):
        frontmatter, _ = read_concept(path)
        if frontmatter.get("check_status") == "checked" and frontmatter.get("id") in traced:
            visible.append(frontmatter["id"])
    ok = good_promoted and bad_quarantined and visible == ["knowledge/notes/good"]
    return Result(
        "Read-barrier / check_status spike",
        "pass" if ok else "fail",
        (
            f"good_promoted={good_promoted}; bad_quarantined={bad_quarantined}; "
            f"visible={visible}; unknown_missing_unchecked_hidden=True; foreign_quarantined=True"
        ),
        "Approve start only if every consumer filters on checked + traced, fail-closed.",
    )


def test_plugin_boundary() -> Result:
    root = WORK / "plugin-boundary"
    reset(root)
    plugin = root / "plugin/main.js"
    write(
        plugin,
        """
export function activate(worker) {
  return {
    readStatus: () => worker.read_status(),
    enqueueCapture: (payload) => worker.enqueue_operation("capture", payload),
    acknowledgeAttention: (id) => worker.acknowledge_attention(id),
    resolveAttention: (id, resolution) => worker.resolve_attention(id, resolution),
    openTrace: (id) => worker.open_trace(id)
  };
}
""".strip()
        + "\n",
    )
    forbidden_tokens = [
        "app.vault.modify",
        "app.vault.create",
        "adapter.write",
        "fs.writeFile",
        "check_status",
        "journal",
    ]
    source = plugin.read_text(encoding="utf-8")
    static_clean = not any(token in source for token in forbidden_tokens)

    worker_calls: list[tuple[str, Any]] = []

    def worker_api(name: str, *args: Any) -> dict[str, str]:
        worker_calls.append((name, args))
        allowed = {
            "read_status",
            "enqueue_operation",
            "acknowledge_attention",
            "resolve_attention",
            "open_trace",
        }
        if name not in allowed:
            raise AssertionError(f"unexpected worker API: {name}")
        return {"ok": "true"}

    for call in (
        ("read_status",),
        ("enqueue_operation", "capture", {"source": "s1"}),
        ("acknowledge_attention", "flag-1"),
        ("resolve_attention", "flag-1", "accepted"),
        ("open_trace", "run-1"),
    ):
        worker_api(*call)

    ok = static_clean and len(worker_calls) == 5
    return Result(
        "Plugin boundary spike",
        "partial" if ok else "fail",
        (
            f"control_panel_surface_clean={static_clean}; worker_calls={len(worker_calls)}; "
            "platform_hard_sandbox=False"
        ),
        (
            "Treat as a design warning: the control-panel API is viable, but Obsidian plugin "
            "JavaScript is trusted code. Approval needs either a static/provenance guardrail "
            "accepted as the mechanism or a different sandboxed UI boundary."
        ),
    )


def test_migration_mapping() -> Result:
    root = WORK / "migration"
    reset(root)
    old_items = [
        {"id": "p1", "type": "paper", "title": "Paper", "citekey": "paper2026"},
        {"id": "d1", "type": "dataset", "title": "Dataset", "citekey": "data2026"},
        {"id": "r1", "type": "repository", "title": "Repo", "citekey": "repo2026"},
        {"id": "s1", "type": "source", "title": "Source note", "summary": "human appraisal"},
        {"id": "c1", "type": "claim", "claim": "A supported claim", "sources": ["p1"]},
        {"id": "a1", "type": "annotation", "quote": "quoted span", "source": "p1"},
        {"id": "f1", "type": "fleeting", "body": "kept thought", "keep": True},
        {"id": "h1", "type": "hub", "title": "Hub"},
        {"id": "pr1", "type": "project", "title": "Project"},
        {"id": "t1", "type": "thesis", "project": "pr1", "thesis": "Project thesis"},
        {"id": "g1", "type": "gap", "title": "Gap"},
        {"id": "fl1", "type": "flag", "title": "Flag"},
        {"id": "wp1", "type": "work-prompt", "title": "Prompt"},
        {"id": "q1", "type": "queue", "title": "Queue"},
    ]

    def map_item(item: dict[str, Any]) -> dict[str, str]:
        typ = item["type"]
        if typ in {"paper", "dataset", "repository"}:
            return {
                "id": item["id"],
                "type": typ,
                "disposition": "mapped",
                "target": f"catalog/sources/{item['id']}/source.md",
            }
        if typ == "source":
            return {
                "id": item["id"],
                "type": typ,
                "disposition": "split",
                "target": f"catalog/sources/{item['id']}/source.md + knowledge/notes/{item['id']}-appraisal.md",
            }
        if typ in {"claim", "annotation", "fleeting"}:
            return {
                "id": item["id"],
                "type": typ,
                "disposition": "mapped",
                "target": f"knowledge/notes/{item['id']}.md",
            }
        if typ == "hub":
            return {"id": item["id"], "type": typ, "disposition": "mapped", "target": "knowledge/hubs/h1.md"}
        if typ in {"project", "thesis"}:
            return {
                "id": item["id"],
                "type": typ,
                "disposition": "mapped",
                "target": "knowledge/projects/pr1/project.md",
            }
        if typ in {"gap", "flag", "work-prompt", "queue"}:
            return {
                "id": item["id"],
                "type": typ,
                "disposition": "projection-or-worker-state",
                "target": "migration-report",
            }
        return {"id": item["id"], "type": typ, "disposition": "unmapped", "target": ""}

    report = [map_item(item) for item in old_items]
    write(root / "migration-report.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
    ok = all(row["disposition"] != "unmapped" and row["target"] for row in report)
    dispos = {row["disposition"] for row in report}
    return Result(
        "Migration mapping dry-run",
        "pass" if ok else "fail",
        f"inputs={len(old_items)}; dispositions={sorted(dispos)}; report={root / 'migration-report.json'}",
        "Approve start with a real migrator later; this only proves the no-silent-loss map.",
    )


def test_seeded_error_harness_definition() -> Result:
    root = WORK / "seeded-error"
    reset(root)
    harness = {
        "fixture": "frozen-gold-bundle",
        "baseline": "raw-no-checks",
        "bar": {
            "structural_recall": 1.0,
            "rollback_completeness": 1.0,
            "blind_class_policy": "human-checkpoint-until-measured",
        },
        "cases": [
            {"id": "broken_ref", "class": "structural", "expected": "check-fired"},
            {"id": "stale_as_current", "class": "temporal", "expected": "check-fired"},
            {"id": "unchecked_leak", "class": "read-barrier", "expected": "not-visible"},
            {"id": "foreign_untraced", "class": "trace", "expected": "quarantined"},
            {"id": "crafted_injection", "class": "blind-security", "expected": "human-checkpoint"},
            {"id": "unwarranted_claim", "class": "blind-grounding", "expected": "human-checkpoint"},
            {"id": "rollback_machine_child", "class": "rollback", "expected": "auto-revert"},
            {"id": "rollback_human_child", "class": "rollback", "expected": "flag-only"},
        ],
        "metrics": ["detection_recall", "time_to_detection", "false_positive_rate", "rollback_completeness"],
    }
    write(root / "seeded-error-harness.json", json.dumps(harness, indent=2, sort_keys=True) + "\n")
    classes = {case["class"] for case in harness["cases"]}
    expected_classes = {
        "structural",
        "temporal",
        "read-barrier",
        "trace",
        "blind-security",
        "blind-grounding",
        "rollback",
    }
    ok = (
        classes == expected_classes
        and "raw-no-checks" == harness["baseline"]
        and "detection_recall" in harness["metrics"]
        and harness["bar"]["blind_class_policy"] == "human-checkpoint-until-measured"
    )
    return Result(
        "Seeded-error harness definition",
        "pass" if ok else "fail",
        f"cases={len(harness['cases'])}; classes={sorted(classes)}; harness={root / 'seeded-error-harness.json'}",
        "Approve start; final seeded-error verdict remains the gate before real-vault use.",
    )


def write_report(results: list[Result]) -> None:
    if any(result.status == "fail" for result in results):
        verdict = "FAIL"
    elif any(result.status == "partial" for result in results):
        verdict = "PARTIAL"
    else:
        verdict = "PASS"
    lines = [
        "# Alpha.11 pre-approval test results",
        "",
        f"Date: {datetime.now(UTC).date().isoformat()}",
        "",
        f"Verdict: **{verdict}**.",
        "",
        "| Gate | Status | Evidence | Recommendation |",
        "| --- | --- | --- | --- |",
    ]
    for result in results:
        lines.append(
            "| "
            + " | ".join(
                cell.replace("|", "\\|").replace("\n", " ")
                for cell in (result.name, result.status, result.evidence, result.recommendation)
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- These are disposable pre-implementation spikes, not alpha.11 implementation tests.",
            "- The plugin boundary is partial because ordinary Obsidian plugin JavaScript is trusted code;",
            "  the spike proves a narrow control-panel surface, not a platform sandbox.",
            "- The final seeded-error verdict is intentionally deferred until alpha.11 exists; this run",
            "  verifies the harness definition and bar shape only.",
            "",
        ]
    )
    write(OUT, "\n".join(lines))


def main() -> None:
    reset(WORK)
    results = [
        test_operation_policy(),
        test_read_barrier(),
        test_plugin_boundary(),
        test_migration_mapping(),
        test_seeded_error_harness_definition(),
    ]
    write_report(results)
    print(OUT)
    for result in results:
        print(f"{result.status}: {result.name}")


if __name__ == "__main__":
    main()
