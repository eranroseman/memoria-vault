#!/usr/bin/env python3
"""Disposable M0 spike for the alpha.11 reset assumptions."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).with_name("m0-spike-results.md")
ALLOWED_TYPES = {"source", "digest", "note", "hub", "project", "operation"}


@dataclass
class Check:
    name: str
    status: str
    evidence: str
    next_step: str


def scalar(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def concept(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["---", *(f"{k}: {scalar(v)}" for k, v in frontmatter.items()), "---", body]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def split_note(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}, text
    _, fm_text, body = text.split("---\n", 2)
    data: dict[str, Any] = {}
    for line in fm_text.splitlines():
        if not line.strip():
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = json.loads(value.strip())
    return data, body


def concept_id(root: Path, path: Path) -> str:
    return path.relative_to(root).with_suffix("").as_posix()


def concepts(root: Path) -> list[Path]:
    return sorted(
        p
        for p in root.rglob("*.md")
        if ".memoria" not in p.parts and p.name not in {"index.md", "log.md"}
    )


def resolve(root: Path, ref: str) -> bool:
    rel = ref.split("#", 1)[0]
    return (root / f"{rel}.md").exists()


def rewrite_frontmatter(path: Path, updates: dict[str, Any]) -> None:
    fm, body = split_note(path)
    fm.update(updates)
    concept(path, fm, body.rstrip())


def append_event(root: Path, event: dict[str, Any]) -> None:
    event.setdefault("at", datetime.now(UTC).replace(microsecond=0).isoformat())
    journal = root / ".memoria/journal/events.jsonl"
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")


def read_events(root: Path) -> list[dict[str, Any]]:
    journal = root / ".memoria/journal/events.jsonl"
    if not journal.exists():
        return []
    return [json.loads(line) for line in journal.read_text(encoding="utf-8").splitlines()]


def build_fixture() -> Path:
    root = Path("/tmp/memoria-alpha11-m0-spike-fixture")
    if root.exists():
        shutil.rmtree(root)
    for rel in (
        "catalog",
        "knowledge",
        "capabilities",
        ".memoria/staging",
        ".memoria/quarantine",
        ".memoria/journal",
    ):
        (root / rel).mkdir(parents=True, exist_ok=True)
    for rel in ("index.md", "catalog/index.md", "knowledge/index.md", "capabilities/index.md"):
        (root / rel).write_text("# Index\n", encoding="utf-8")
    for rel in ("log.md", "catalog/log.md", "knowledge/log.md", "capabilities/log.md"):
        (root / rel).write_text("# Log\n", encoding="utf-8")

    concept(
        root / "catalog/source-alpha.md",
        {
            "id": "catalog/source-alpha",
            "type": "source",
            "title": "Alpha source",
            "source_id": "source-alpha",
            "citekey": "alpha2026",
            "status": "checked",
        },
        "## Spans\n\n<span id=\"s1\">Alpha method reduces drift.</span>",
    )
    concept(
        root / "knowledge/digest-alpha.md",
        {
            "id": "knowledge/digest-alpha",
            "type": "digest",
            "title": "Alpha digest",
            "source_id": "catalog/source-alpha",
            "status": "checked",
            "derived_from": ["catalog/source-alpha#s1"],
        },
        "Alpha source says the method reduces drift.",
    )
    concept(
        root / "knowledge/note-alpha.md",
        {
            "id": "knowledge/note-alpha",
            "type": "note",
            "title": "Alpha method reduces drift",
            "status": "checked",
            "assertion": "Alpha method reduces drift.",
            "evidence_set": ["catalog/source-alpha#s1"],
        },
        "A source-backed note with an assertion.",
    )
    concept(
        root / "knowledge/note-quote.md",
        {
            "id": "knowledge/note-quote",
            "type": "note",
            "title": "Quoted annotation",
            "status": "checked",
            "annotation_ref": {
                "source": "catalog/source-alpha",
                "selector": {"type": "TextQuoteSelector", "exact": "reduces drift"},
            },
            "evidence_set": ["catalog/source-alpha#s1"],
        },
        "A note can be anchored without becoming a separate annotation type.",
    )
    concept(
        root / "knowledge/hub-drift.md",
        {
            "id": "knowledge/hub-drift",
            "type": "hub",
            "title": "Drift hub",
            "status": "checked",
            "members": ["knowledge/digest-alpha", "knowledge/note-alpha"],
        },
        "Topic hub.",
    )
    concept(
        root / "knowledge/project-alpha.md",
        {
            "id": "knowledge/project-alpha",
            "type": "project",
            "title": "Alpha project",
            "status": "checked",
            "in_project": ["knowledge/note-alpha"],
        },
        "Project direction.",
    )
    concept(
        root / "capabilities/operation-capture.md",
        {
            "id": "capabilities/operation-capture",
            "type": "operation",
            "title": "Capture operation",
            "status": "checked",
            "trust": {"source": "local-fixture", "signed": True},
        },
        "Capability fixture.",
    )
    return root


def check_storage(root: Path) -> Check:
    required = ["catalog", "knowledge", "capabilities", "index.md", "log.md"]
    missing = [rel for rel in required if not (root / rel).exists()]
    ids_match = all(split_note(p)[0].get("id") == concept_id(root, p) for p in concepts(root))
    refs = []
    for p in concepts(root):
        fm, _ = split_note(p)
        refs.extend(fm.get("derived_from") or [])
        refs.extend(fm.get("evidence_set") or [])
        refs.extend(fm.get("members") or [])
        refs.extend(fm.get("in_project") or [])
    refs_ok = all(resolve(root, ref) for ref in refs)
    exported = root.parent / "knowledge-export"
    if exported.exists():
        shutil.rmtree(exported)
    shutil.copytree(root / "knowledge", exported)
    export_ok = len(list(exported.glob("*.md"))) >= 4
    ok = not missing and ids_match and refs_ok and export_ok
    status = "partial-pass" if ok else "fail"
    evidence = (
        f"required_missing={missing}; ids_match={ids_match}; refs_ok={refs_ok}; "
        f"knowledge_export_md={len(list(exported.glob('*.md')))}. "
        "No external OKF validator was available, so this is structure-only."
    )
    return Check(
        "1. Storage shape / OKF round-trip",
        status,
        evidence,
        "Run the same fixture through a real OKF validator/importer before ADR acceptance.",
    )


def check_schema(root: Path) -> Check:
    required = {
        "source": {"id", "type", "title", "source_id", "citekey"},
        "digest": {"id", "type", "title", "source_id", "derived_from"},
        "note": {"id", "type", "title", "evidence_set"},
        "hub": {"id", "type", "title", "members"},
        "project": {"id", "type", "title", "in_project"},
        "operation": {"id", "type", "title", "trust"},
    }
    problems: list[str] = []
    for p in concepts(root):
        fm, _ = split_note(p)
        typ = fm.get("type")
        if typ not in ALLOWED_TYPES:
            problems.append(f"{concept_id(root, p)} invalid type {typ}")
            continue
        missing = sorted(required[typ] - set(fm))
        if missing:
            problems.append(f"{concept_id(root, p)} missing {missing}")

    src = root / "catalog/source-alpha.md"
    before, _ = split_note(src)
    rewrite_frontmatter(src, {"citekey": "alpha2026-renamed", "title": "Alpha source renamed"})
    after, _ = split_note(src)
    stable_id = before["id"] == after["id"] and before["source_id"] == after["source_id"]
    refs_still_resolve = resolve(root, "catalog/source-alpha#s1")
    ok = not problems and stable_id and refs_still_resolve
    return Check(
        "2. Schema reset",
        "pass" if ok else "fail",
        (
            f"schema_problems={problems}; source_id_stable_after_citekey_change={stable_id}; "
            f"refs_still_resolve={refs_still_resolve}."
        ),
        "Convert this fixture shape into JSON Schema tests for the alpha.11 type map.",
    )


def run_checks(root: Path, path: Path) -> tuple[bool, list[str]]:
    fm, body = split_note(path)
    errors: list[str] = []
    if fm.get("type") not in ALLOWED_TYPES:
        errors.append("invalid_type")
    if "UNSUPPORTED" in body:
        errors.append("unsupported_marker")
    for ref in fm.get("derived_from") or []:
        if not resolve(root, ref):
            errors.append(f"broken_ref:{ref}")
    for ref in fm.get("evidence_set") or []:
        if not resolve(root, ref):
            errors.append(f"broken_ref:{ref}")
    return not errors, errors


def staged_write(
    root: Path,
    rel_id: str,
    typ: str,
    body: str,
    inputs: list[str],
    *,
    actor: str = "operation",
) -> Path:
    path = root / ".memoria/staging" / f"{rel_id}.md"
    concept(
        path,
        {
            "id": rel_id,
            "type": typ,
            "title": rel_id.rsplit("/", 1)[-1],
            "status": "unchecked",
            "derived_from": inputs,
            "actor": actor,
        },
        body,
    )
    return path


def promote_or_quarantine(root: Path, staged: Path) -> bool:
    ok, errors = run_checks(root, staged)
    rel = staged.relative_to(root / ".memoria/staging")
    if ok:
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staged), str(dest))
        rewrite_frontmatter(dest, {"status": "checked"})
        fm, _ = split_note(dest)
        append_event(
            root,
            {
                "event": "derived",
                "output": fm["id"],
                "inputs": fm.get("derived_from") or [],
                "actor": fm.get("actor") or "operation",
            },
        )
        return True
    dest = root / ".memoria/quarantine" / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(staged), str(dest))
    fm, _ = split_note(dest)
    append_event(root, {"event": "flag", "output": fm["id"], "errors": errors})
    return False


def visible_to_consumers(root: Path) -> set[str]:
    visible = set()
    for p in (root / "knowledge").glob("*.md"):
        fm, _ = split_note(p)
        if fm.get("status") == "checked":
            visible.add(fm["id"])
    return visible


def rollback(root: Path, bad_id: str) -> dict[str, list[str]]:
    events = read_events(root)
    actors = {event["output"]: event.get("actor") for event in events if event["event"] == "derived"}
    children: dict[str, list[str]] = {}
    for event in events:
        if event.get("event") != "derived":
            continue
        for input_ref in event.get("inputs") or []:
            children.setdefault(input_ref.split("#", 1)[0], []).append(event["output"])
    pending = [bad_id]
    affected: set[str] = set()
    while pending:
        item = pending.pop()
        if item in affected:
            continue
        affected.add(item)
        pending.extend(children.get(item, []))

    rolled_back: list[str] = []
    flagged: list[str] = []
    for item in sorted(affected):
        path = root / f"{item}.md"
        if not path.exists():
            continue
        if actors.get(item) == "pi":
            rewrite_frontmatter(path, {"status": "flagged"})
            append_event(root, {"event": "flag", "output": item, "reason": "rollback-blast-radius"})
            flagged.append(item)
        else:
            rewrite_frontmatter(path, {"status": "rolled_back"})
            append_event(root, {"event": "resolved", "output": item, "reason": "cascade-rollback"})
            rolled_back.append(item)
    return {"rolled_back": rolled_back, "flagged": flagged}


def check_integrity(root: Path) -> Check:
    before_visible = visible_to_consumers(root)
    good = staged_write(
        root,
        "knowledge/digest-beta",
        "digest",
        "Supported beta digest.",
        ["catalog/source-alpha#s1"],
    )
    staging_hidden = "knowledge/digest-beta" not in visible_to_consumers(root)
    good_promoted = promote_or_quarantine(root, good)
    bad = staged_write(
        root,
        "knowledge/digest-poison",
        "digest",
        "UNSUPPORTED poisoned digest.",
        ["catalog/source-alpha#s1"],
    )
    bad_promoted = promote_or_quarantine(root, bad)
    staged_write(
        root,
        "knowledge/note-machine-beta",
        "note",
        "Machine child.",
        ["knowledge/digest-beta"],
    )
    promote_or_quarantine(root, root / ".memoria/staging/knowledge/note-machine-beta.md")
    staged_write(
        root,
        "knowledge/note-human-beta",
        "note",
        "PI-directed child.",
        ["knowledge/digest-beta"],
        actor="pi",
    )
    promote_or_quarantine(root, root / ".memoria/staging/knowledge/note-human-beta.md")
    rb = rollback(root, "knowledge/digest-beta")
    poison_hidden = "knowledge/digest-poison" not in visible_to_consumers(root)
    ok = (
        staging_hidden
        and good_promoted
        and not bad_promoted
        and poison_hidden
        and "knowledge/note-machine-beta" in rb["rolled_back"]
        and "knowledge/note-human-beta" in rb["flagged"]
    )
    evidence = (
        f"before_visible={sorted(before_visible)}; staging_hidden={staging_hidden}; "
        f"good_promoted={good_promoted}; poison_quarantined={not bad_promoted}; "
        f"poison_hidden={poison_hidden}; rollback={rb}."
    )
    return Check(
        "3. Integrity spine feasibility",
        "pass" if ok else "fail",
        evidence,
        "Replace this in-memory/file simulation with production trusted-writer and git tests.",
    )


def check_wiki_engine() -> Check:
    skill = Path.home() / ".hermes/skills/llm-wiki/SKILL.md"
    docs = (
        Path.home()
        / ".hermes/hermes-agent/website/docs/user-guide/skills/bundled/research"
        / "research-llm-wiki.md"
    )
    build = Path.home() / ".hermes/skills/llm-wiki/scripts/build.sh"
    bootstrap = Path.home() / ".hermes/skills/llm-wiki/scripts/bootstrap.sh"
    syntax = []
    for script in (build, bootstrap):
        if script.exists():
            proc = subprocess.run(
                ["bash", "-n", str(script)],
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            syntax.append((script.name, proc.returncode == 0))
    text = docs.read_text(encoding="utf-8") if docs.exists() else ""
    available = skill.exists() and docs.exists() and "5-15" in text and all(ok for _, ok in syntax)
    return Check(
        "4. Wiki engine adopt-vs-build",
        "partial-pass" if available else "fail",
        (
            f"skill_exists={skill.exists()}; docs_exist={docs.exists()}; "
            f"docs_mentions_5_15={'5-15' in text}; script_syntax={syntax}. "
            "No live compile/model quality run was attempted."
        ),
        "Run one real `llm-wiki` compile on the fixture source corpus and score output quality.",
    )


def check_plugin() -> Check:
    plugin = ROOT / "vault-template/.obsidian/plugins/memoria-inspector"
    main = plugin / "main.js"
    manifest = plugin / "manifest.json"
    text = main.read_text(encoding="utf-8") if main.exists() else ""
    has_view = "registerView" in text
    read_only = all(
        forbidden not in text
        for forbidden in (".vault.modify", ".vault.create", ".adapter.write", "fetch(")
    )
    missing_alpha11 = [token for token in ("rollback", "Co-PI", "conversation") if token not in text]
    ok = plugin.exists() and manifest.exists() and has_view and read_only
    return Check(
        "5. Obsidian plugin feasibility",
        "partial-pass" if ok else "fail",
        (
            f"plugin_exists={plugin.exists()}; has_view={has_view}; read_only={read_only}; "
            f"missing_alpha11_tokens={missing_alpha11}. Current plugin proves packaging/static "
            "view pattern only, not the alpha.11 Co-PI/rollback surface."
        ),
        "Build a disposable alpha.11 plugin pane and test it in Obsidian on Memoria-test.",
    )


def check_seeded_harness(root: Path) -> Check:
    cases = {
        "broken_ref": lambda: concept(
            root / "knowledge/broken-ref.md",
            {
                "id": "knowledge/broken-ref",
                "type": "note",
                "title": "Broken ref",
                "status": "checked",
                "evidence_set": ["catalog/missing#s9"],
            },
            "Broken evidence reference.",
        ),
        "unsupported_marker": lambda: concept(
            root / "knowledge/unsupported.md",
            {
                "id": "knowledge/unsupported",
                "type": "note",
                "title": "Unsupported",
                "status": "checked",
                "evidence_set": ["catalog/source-alpha#s1"],
            },
            "UNSUPPORTED claim.",
        ),
        "stale_as_current": lambda: concept(
            root / "knowledge/stale.md",
            {
                "id": "knowledge/stale",
                "type": "note",
                "title": "Stale",
                "status": "checked",
                "superseded_by": "knowledge/note-alpha",
                "evidence_set": ["catalog/source-alpha#s1"],
            },
            "Stale content still marked checked.",
        ),
        "unchecked_leak": lambda: staged_write(
            root,
            "knowledge/unchecked-leak",
            "note",
            "Unchecked should not be visible.",
            ["catalog/source-alpha#s1"],
        ),
    }
    for make in cases.values():
        make()

    detected: set[str] = set()
    for p in concepts(root):
        ok, errors = run_checks(root, p)
        if not ok:
            detected.update(error.split(":", 1)[0] for error in errors)
        fm, _ = split_note(p)
        if fm.get("status") == "checked" and fm.get("superseded_by"):
            detected.add("stale_as_current")
    if "knowledge/unchecked-leak" not in visible_to_consumers(root):
        detected.add("unchecked_leak")

    expected = set(cases)
    recall = len(expected & detected) / len(expected)
    ok = recall == 1.0
    return Check(
        "6. Seeded-error harness design",
        "pass" if ok else "fail",
        (
            f"expected={sorted(expected)}; detected={sorted(expected & detected)}; "
            f"recall={recall:.2f}. This validates harness shape, not semantic/NLI recall."
        ),
        "Add crafted-injection and unwarranted-claim cases once semantic detectors exist.",
    )


def report(fixture: Path, checks: list[Check]) -> str:
    rows = "\n".join(
        f"| {c.name} | {c.status} | {c.evidence} | {c.next_step} |" for c in checks
    )
    failed = [c.name for c in checks if c.status == "fail"]
    partial = [c.name for c in checks if c.status == "partial-pass"]
    verdict = "GO for implementation planning, not production build"
    if failed:
        verdict = "NO-GO until failed checks are resolved"
    elif partial:
        verdict = "GO only for narrow scaffolding; live spikes still required"
    return f"""# Alpha.11 M0 spike results

Date: {datetime.now(UTC).date().isoformat()}

Fixture: `{fixture}`

Verdict: **{verdict}**.

| Check | Status | Evidence | Next verification |
| --- | --- | --- | --- |
{rows}

## Interpretation

The disposable fixture proves the reset shape is internally coherent enough to
continue planning: nested bundles, the schema reset, the read barrier simulation,
cascade rollback semantics, and seeded-error scoring can be represented with plain
files. It does **not** prove external OKF conformance, real LLM wiki quality, or the
alpha.11 Obsidian plugin surface. Those remain the shortest live spikes before
production alpha.11 implementation.
"""


def main() -> int:
    fixture = build_fixture()
    checks = [
        check_storage(fixture),
        check_schema(fixture),
        check_integrity(fixture),
        check_wiki_engine(),
        check_plugin(),
        check_seeded_harness(fixture),
    ]
    OUT.write_text(report(fixture, checks), encoding="utf-8")
    print(f"fixture={fixture}")
    print(f"report={OUT}")
    for check in checks:
        print(f"{check.status}: {check.name}")
    return 1 if any(check.status == "fail" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
