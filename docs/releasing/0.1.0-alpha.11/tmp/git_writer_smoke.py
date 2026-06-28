#!/usr/bin/env python3
"""Git-backed trusted-writer smoke for the alpha.11 M0 spike."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SANDBOX = Path("/home/eranr/Memoria-test")
WORK = SANDBOX / ".memoria/tmp/alpha11-git-writer-smoke"
OUT = Path(__file__).with_name("git-writer-smoke-results.md")
JOURNAL = Path(".memoria/journal/events.jsonl")


def run(args: list[str]) -> str:
    proc = subprocess.run(
        args,
        cwd=WORK,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode:
        raise RuntimeError(f"{' '.join(args)}\n{proc.stdout}\n{proc.stderr}")
    return proc.stdout.strip()


def rel(path: Path) -> str:
    return path.relative_to(WORK).as_posix()


def note(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        *(f"{key}: {json.dumps(value, sort_keys=True)}" for key, value in frontmatter.items()),
        "---",
        body,
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_note(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    _, fm_text, body = text.split("---\n", 2)
    frontmatter: dict[str, Any] = {}
    for line in fm_text.splitlines():
        if line:
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = json.loads(value.strip())
    return frontmatter, body


def update(path: Path, fields: dict[str, Any]) -> None:
    frontmatter, body = read_note(path)
    frontmatter.update(fields)
    note(path, frontmatter, body.rstrip())


def append_event(event: dict[str, Any]) -> Path:
    event.setdefault("at", datetime.now(UTC).replace(microsecond=0).isoformat())
    path = WORK / JOURNAL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")
    return path


def events() -> list[dict[str, Any]]:
    path = WORK / JOURNAL
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def commit(message: str, paths: list[Path]) -> str:
    run(["git", "add", "--", *(rel(path) for path in paths)])
    run(["git", "commit", "-m", message])
    return run(["git", "rev-parse", "--short", "HEAD"])


def commit_files(commit_hash: str) -> set[str]:
    return set(run(["git", "show", "--name-only", "--format=", commit_hash]).splitlines())


def setup() -> str:
    if WORK.exists():
        shutil.rmtree(WORK)
    for folder in (
        "catalog",
        "knowledge",
        ".memoria/staging",
        ".memoria/quarantine",
        ".memoria/journal",
    ):
        (WORK / folder).mkdir(parents=True, exist_ok=True)
    run(["git", "init", "-q"])
    run(["git", "config", "user.email", "alpha11-smoke@example.invalid"])
    run(["git", "config", "user.name", "Alpha11 Smoke"])
    source = WORK / "catalog/source-alpha.md"
    note(
        source,
        {
            "id": "catalog/source-alpha",
            "type": "source",
            "title": "Alpha source",
            "status": "checked",
        },
        "Alpha source span s1 supports the fixture.",
    )
    journal = append_event({"event": "captured", "output": "catalog/source-alpha"})
    return commit("initial checked source", [source, journal])


def valid(path: Path) -> bool:
    frontmatter, body = read_note(path)
    if "UNSUPPORTED" in body:
        return False
    for input_ref in frontmatter.get("derived_from") or []:
        target = WORK / f"{input_ref.split('#', 1)[0]}.md"
        if not target.exists():
            return False
    return True


def trusted_write(
    output_id: str,
    body: str,
    inputs: list[str],
    *,
    actor: str = "operation",
) -> tuple[bool, str]:
    staged = WORK / ".memoria/staging" / f"{output_id}.md"
    note(
        staged,
        {
            "id": output_id,
            "type": "digest" if "digest" in output_id else "note",
            "title": output_id.rsplit("/", 1)[-1],
            "status": "unchecked",
            "actor": actor,
            "derived_from": inputs,
        },
        body,
    )
    if valid(staged):
        dest = WORK / f"{output_id}.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(staged, dest)
        update(dest, {"status": "checked"})
        journal = append_event(
            {
                "event": "derived",
                "actor": actor,
                "output": output_id,
                "inputs": inputs,
            }
        )
        return True, commit(f"trusted write {output_id}", [dest, journal])

    dest = WORK / ".memoria/quarantine" / f"{output_id}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(staged, dest)
    journal = append_event({"event": "flag", "output": output_id, "reason": "check-failed"})
    return False, commit(f"quarantine failed write {output_id}", [dest, journal])


def pi_edit(output_id: str, inputs: list[str]) -> str:
    path = WORK / f"{output_id}.md"
    note(
        path,
        {
            "id": output_id,
            "type": "note",
            "title": output_id.rsplit("/", 1)[-1],
            "status": "checked",
            "actor": "pi",
            "derived_from": inputs,
        },
        "PI-directed downstream note.",
    )
    journal = append_event({"event": "derived", "actor": "pi", "output": output_id, "inputs": inputs})
    return commit(f"pi backfill {output_id}", [path, journal])


def foreign_commit() -> str:
    path = WORK / "knowledge/foreign.md"
    note(
        path,
        {"id": "knowledge/foreign", "type": "note", "title": "Foreign", "status": "checked"},
        "No journal event was written for this commit.",
    )
    return commit("foreign untraced commit", [path])


def trace_integrity_scan() -> tuple[bool, str]:
    traced = {event["output"] for event in events() if event.get("event") in {"captured", "derived"}}
    moved: list[Path] = []
    removed: list[Path] = []
    for path in sorted((WORK / "knowledge").glob("*.md")):
        frontmatter, _ = read_note(path)
        if frontmatter.get("id") not in traced:
            dest = WORK / ".memoria/quarantine" / rel(path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(path, dest)
            moved.append(dest)
            removed.append(path)
            append_event(
                {
                    "event": "flag",
                    "output": frontmatter["id"],
                    "reason": "foreign-untraced",
                }
            )
    if not moved:
        return False, run(["git", "rev-parse", "--short", "HEAD"])
    return True, commit("quarantine foreign untraced content", [*removed, *moved, WORK / JOURNAL])


def rollback(bad_id: str) -> tuple[dict[str, list[str]], str]:
    actor_by_output = {
        event["output"]: event.get("actor")
        for event in events()
        if event.get("event") == "derived"
    }
    children: dict[str, list[str]] = {}
    for event in events():
        if event.get("event") != "derived":
            continue
        for input_ref in event.get("inputs") or []:
            children.setdefault(input_ref.split("#", 1)[0], []).append(event["output"])

    affected: set[str] = set()
    pending = [bad_id]
    while pending:
        item = pending.pop()
        if item in affected:
            continue
        affected.add(item)
        pending.extend(children.get(item, []))

    rolled_back: list[str] = []
    flagged: list[str] = []
    touched: list[Path] = []
    for item in sorted(affected):
        path = WORK / f"{item}.md"
        if not path.exists():
            continue
        if actor_by_output.get(item) == "pi":
            update(path, {"status": "flagged"})
            append_event({"event": "flag", "output": item, "reason": "rollback-blast-radius"})
            flagged.append(item)
        else:
            update(path, {"status": "rolled_back"})
            append_event({"event": "resolved", "output": item, "reason": "cascade-rollback"})
            rolled_back.append(item)
        touched.append(path)
    return {"rolled_back": rolled_back, "flagged": flagged}, commit(
        "inverse rollback digest-alpha",
        [*touched, WORK / JOURNAL],
    )


def checked_visible() -> set[str]:
    visible: set[str] = set()
    for path in (WORK / "knowledge").glob("*.md"):
        frontmatter, _ = read_note(path)
        if frontmatter.get("status") == "checked":
            visible.add(frontmatter["id"])
    return visible


def report(rows: list[tuple[str, bool, str]]) -> str:
    verdict = "PASS" if all(ok for _, ok, _ in rows) else "FAIL"
    table = "\n".join(
        f"| {name} | {'pass' if ok else 'fail'} | {evidence} |" for name, ok, evidence in rows
    )
    return f"""# Git-backed trusted-writer smoke results

Date: {datetime.now(UTC).date().isoformat()}

Sandbox: `{WORK}`

Verdict: **{verdict}**.

| Check | Status | Evidence |
| --- | --- | --- |
{table}

## Notes

This is a disposable smoke in `~/Memoria-test`; it is not production alpha.11
code. It proves the core writer contract can be represented as real git history:
trusted writes commit file + journal together, failed writes quarantine, foreign
commits are detected and quarantined, and rollback is an inverse traced commit.
"""


def main() -> int:
    initial = setup()
    good_ok, good_commit = trusted_write(
        "knowledge/digest-alpha",
        "Supported digest.",
        ["catalog/source-alpha#s1"],
    )
    poison_ok, poison_commit = trusted_write(
        "knowledge/digest-poison",
        "UNSUPPORTED poisoned digest.",
        ["catalog/source-alpha#s1"],
    )
    machine_ok, machine_commit = trusted_write(
        "knowledge/note-machine-alpha",
        "Machine downstream note.",
        ["knowledge/digest-alpha"],
    )
    pi_commit = pi_edit("knowledge/note-human-alpha", ["knowledge/digest-alpha"])
    foreign = foreign_commit()
    moved_foreign, quarantine_foreign = trace_integrity_scan()
    rb, rollback_commit = rollback("knowledge/digest-alpha")

    digest_status = read_note(WORK / "knowledge/digest-alpha.md")[0]["status"]
    machine_status = read_note(WORK / "knowledge/note-machine-alpha.md")[0]["status"]
    human_status = read_note(WORK / "knowledge/note-human-alpha.md")[0]["status"]
    rows = [
        (
            "trusted write commit couples file and journal",
            good_ok
            and {"knowledge/digest-alpha.md", JOURNAL.as_posix()} <= commit_files(good_commit),
            f"commit={good_commit}; files={sorted(commit_files(good_commit))}",
        ),
        (
            "failed write is quarantined and hidden",
            (not poison_ok)
            and (WORK / ".memoria/quarantine/knowledge/digest-poison.md").exists()
            and "knowledge/digest-poison" not in checked_visible(),
            f"commit={poison_commit}; visible={sorted(checked_visible())}",
        ),
        (
            "PI edit is backfilled as traced commit",
            {"knowledge/note-human-alpha.md", JOURNAL.as_posix()} <= commit_files(pi_commit),
            f"commit={pi_commit}; files={sorted(commit_files(pi_commit))}",
        ),
        (
            "foreign untraced commit is quarantined by scan",
            moved_foreign and (WORK / ".memoria/quarantine/knowledge/foreign.md").exists(),
            f"foreign_commit={foreign}; quarantine_commit={quarantine_foreign}",
        ),
        (
            "cascade rollback is inverse traced commit",
            digest_status == "rolled_back"
            and machine_status == "rolled_back"
            and human_status == "flagged"
            and {"knowledge/digest-alpha.md", "knowledge/note-machine-alpha.md", JOURNAL.as_posix()}
            <= commit_files(rollback_commit),
            (
                f"commit={rollback_commit}; rollback={rb}; "
                f"statuses={{digest:{digest_status}, machine:{machine_status}, human:{human_status}}}"
            ),
        ),
        (
            "smoke repo ends clean",
            run(["git", "status", "--short"]) == "",
            f"commits={run(['git', 'rev-list', '--count', 'HEAD'])}; "
            f"initial={initial}; machine_commit={machine_commit}",
        ),
    ]
    OUT.write_text(report(rows), encoding="utf-8")
    print(f"sandbox={WORK}")
    print(f"report={OUT}")
    for name, ok, _ in rows:
        print(f"{'pass' if ok else 'fail'}: {name}")
    return 0 if all(ok for _, ok, _ in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
