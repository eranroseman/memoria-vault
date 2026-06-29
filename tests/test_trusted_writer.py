from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.trusted_writer import (
    commit_writer_changes,
    mark_checked,
    observe_pi_edit,
    observe_pi_edit_from_head,
    observe_pi_edits_from_status,
    promote_checked,
    quarantine_untraced,
    quarantine_untraced_from_status,
    rebuild_trace_state,
    stage_concept,
)
from memoria_vault.runtime.vaultio import read_frontmatter

ROOT = Path(__file__).resolve().parent.parent


def workspace(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "vault-template/.memoria/schemas", tmp_path / ".memoria/schemas")
    return tmp_path


def note_text(*, status: str = "checked", title: str = "Alpha note") -> str:
    return f"---\ntype: note\ncheck_status: {status}\ntitle: {title}\n---\nAlpha body.\n"


def events(vault: Path) -> list[dict]:
    return list(iter_jsonl(vault / "journal/test-machine.jsonl"))


def git(vault: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=vault,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode:
        raise AssertionError(proc.stderr or proc.stdout)
    return proc.stdout.strip()


def test_stage_concept_forces_unchecked_and_journals_derivation(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    event = stage_concept(
        vault,
        "knowledge/notes/alpha.md",
        note_text(status="checked"),
        inputs=[{"id": "catalog/sources/source-a/source.md", "sha256": "sha256:abc"}],
        run_id="run-1",
        machine="test-machine",
    )

    staged = vault / ".memoria/staging/knowledge/notes/alpha.md"
    assert staged.is_file()
    assert not (vault / "knowledge/notes/alpha.md").exists()
    assert read_frontmatter(staged)["check_status"] == "unchecked"
    assert event["event"] == "derived"
    assert event["output_id"] == "knowledge/notes/alpha.md"
    assert events(vault) == [event]


def test_promote_checked_writes_bundle_file_and_records_check(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    stage_concept(vault, "knowledge/notes/alpha.md", note_text(), machine="test-machine")

    event = promote_checked(vault, "knowledge/notes/alpha.md", machine="test-machine")

    target = vault / "knowledge/notes/alpha.md"
    assert target.is_file()
    assert not (vault / ".memoria/staging/knowledge/notes/alpha.md").exists()
    assert read_frontmatter(target)["check_status"] == "checked"
    assert event["event"] == "check-fired"
    assert event["status"] == "passed"
    assert event["output_sha256"] == sha256_file(target)
    assert rebuild_trace_state(vault)["knowledge/notes/alpha.md"] == event
    assert quarantine_untraced(vault, ["knowledge/notes/alpha.md"], machine="test-machine") == []


def test_commit_writer_changes_couples_concept_and_journal_only(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    git(vault, "init", "-q")
    git(vault, "config", "user.email", "writer@example.invalid")
    git(vault, "config", "user.name", "Trusted Writer")
    (vault / "other.md").write_text("unrelated\n", encoding="utf-8")
    git(vault, "add", "other.md")

    stage_concept(vault, "knowledge/notes/alpha.md", note_text(), machine="test-machine")
    promote_checked(vault, "knowledge/notes/alpha.md", machine="test-machine")
    commit_hash = commit_writer_changes(
        vault,
        "trusted write alpha",
        ["knowledge/notes/alpha.md"],
        machine="test-machine",
    )

    committed = set(git(vault, "show", "--name-only", "--format=", commit_hash).splitlines())
    assert committed == {"journal/test-machine.jsonl", "knowledge/notes/alpha.md"}
    assert git(vault, "diff", "--cached", "--name-only") == "other.md"


def test_observe_pi_edit_backfills_prior_head_and_live_check(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    target = vault / "knowledge/notes/pi.md"
    target.parent.mkdir(parents=True)
    target.write_text(note_text(title="PI note"), encoding="utf-8")
    prior_sha = sha256_file(target)
    target.write_text(note_text(title="PI note") + "\nPI edit.\n", encoding="utf-8")

    event = observe_pi_edit(
        vault,
        "knowledge/notes/pi.md",
        prior_sha,
        inputs=[{"id": "catalog/sources/source-a/source.md", "sha256": "sha256:abc"}],
        machine="test-machine",
    )

    assert read_frontmatter(target)["check_status"] == "unchecked"
    assert event["actor"] == "pi"
    assert event["inputs"][-1] == {
        "id": "knowledge/notes/pi.md",
        "sha256": prior_sha,
        "role": "prior-head",
    }

    check_event = mark_checked(vault, "knowledge/notes/pi.md", machine="test-machine")

    assert read_frontmatter(target)["check_status"] == "checked"
    assert check_event["status"] == "passed"
    assert rebuild_trace_state(vault)["knowledge/notes/pi.md"] == check_event


def test_observe_pi_edit_from_head_keeps_prior_upstream_inputs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    git(vault, "init", "-q")
    git(vault, "config", "user.email", "writer@example.invalid")
    git(vault, "config", "user.name", "Trusted Writer")
    stage_concept(
        vault,
        "knowledge/notes/pi.md",
        note_text(title="PI note"),
        inputs=[{"id": "catalog/sources/source-a/source.md", "sha256": "sha256:abc"}],
        machine="test-machine",
    )
    promote_checked(vault, "knowledge/notes/pi.md", machine="test-machine")
    commit_writer_changes(
        vault, "trusted write pi", ["knowledge/notes/pi.md"], machine="test-machine"
    )
    prior_sha = sha256_file(vault / "knowledge/notes/pi.md")
    (vault / "knowledge/notes/pi.md").write_text(
        note_text(title="PI note") + "\nPI edit.\n",
        encoding="utf-8",
    )

    event = observe_pi_edit_from_head(vault, "knowledge/notes/pi.md", machine="test-machine")

    assert event["actor"] == "pi"
    assert event["inputs"] == [
        {"id": "catalog/sources/source-a/source.md", "sha256": "sha256:abc"},
        {"id": "knowledge/notes/pi.md", "sha256": prior_sha, "role": "prior-head"},
    ]
    assert read_frontmatter(vault / "knowledge/notes/pi.md")["check_status"] == "unchecked"


def test_observe_pi_edits_from_status_commits_pi_files_and_journal(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    git(vault, "init", "-q")
    git(vault, "config", "user.email", "writer@example.invalid")
    git(vault, "config", "user.name", "Trusted Writer")
    stage_concept(
        vault,
        "knowledge/notes/pi.md",
        note_text(title="PI note"),
        inputs=[{"id": "catalog/sources/source-a/source.md", "sha256": "sha256:abc"}],
        machine="test-machine",
    )
    promote_checked(vault, "knowledge/notes/pi.md", machine="test-machine")
    commit_writer_changes(
        vault, "trusted write pi", ["knowledge/notes/pi.md"], machine="test-machine"
    )
    (vault / "knowledge/notes/pi.md").write_text(
        note_text(title="PI note") + "\nPI edit.\n",
        encoding="utf-8",
    )
    new_path = vault / "knowledge/notes/pi-new.md"
    new_path.write_text(note_text(title="PI new"), encoding="utf-8")

    result = observe_pi_edits_from_status(vault, machine="test-machine")

    assert result["paths"] == ["knowledge/notes/pi-new.md", "knowledge/notes/pi.md"]
    assert [event["actor"] for event in result["observed"]] == ["pi", "pi"]
    assert (
        result["observed"][0]["inputs"][-1]["sha256"]
        == "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert result["observed"][1]["inputs"][0] == {
        "id": "catalog/sources/source-a/source.md",
        "sha256": "sha256:abc",
    }
    assert read_frontmatter(vault / "knowledge/notes/pi.md")["check_status"] == "unchecked"
    assert read_frontmatter(new_path)["check_status"] == "unchecked"
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {
        "journal/test-machine.jsonl",
        "knowledge/notes/pi-new.md",
        "knowledge/notes/pi.md",
    }
    assert git(vault, "status", "--short", "--", "journal", "knowledge") == ""


def test_promote_checked_rejects_invalid_staged_concept(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    staged = vault / ".memoria/staging/knowledge/notes/bad.md"
    staged.parent.mkdir(parents=True)
    staged.write_text("---\ntype: note\ncheck_status: unchecked\n---\nBody.\n", encoding="utf-8")

    try:
        promote_checked(vault, "knowledge/notes/bad.md", machine="test-machine")
    except ValueError as exc:
        assert "missing required field 'title'" in str(exc)
    else:
        raise AssertionError("invalid staged Concept should not promote")

    assert not (vault / "knowledge/notes/bad.md").exists()


def test_quarantine_untraced_moves_explicit_foreign_file(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    foreign = vault / "knowledge/notes/foreign.md"
    foreign.parent.mkdir(parents=True)
    foreign.write_text(note_text(title="Foreign"), encoding="utf-8")
    original_sha = sha256_file(foreign)

    [event] = quarantine_untraced(
        vault,
        ["knowledge/notes/foreign.md"],
        machine="test-machine",
    )

    quarantined = vault / ".memoria/quarantine/knowledge/notes/foreign.md"
    assert not foreign.exists()
    assert quarantined.is_file()
    assert read_frontmatter(quarantined)["check_status"] == "quarantined"
    assert event["event"] == "check-fired"
    assert event["status"] == "failed"
    assert event["reason"] == "foreign-untraced"
    assert event["target_sha256"] == original_sha
    assert event["quarantined_id"] == ".memoria/quarantine/knowledge/notes/foreign.md"


def test_quarantine_untraced_from_status_scans_bundle_changes(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    git(vault, "init", "-q")
    foreign = vault / "knowledge/notes/foreign-status.md"
    foreign.parent.mkdir(parents=True)
    foreign.write_text(note_text(title="Foreign status"), encoding="utf-8")

    [event] = quarantine_untraced_from_status(vault, machine="test-machine")

    assert event["target_id"] == "knowledge/notes/foreign-status.md"
    assert not foreign.exists()
    assert (vault / ".memoria/quarantine/knowledge/notes/foreign-status.md").is_file()


def test_two_device_git_writes_keep_per_machine_journals_mergeable(tmp_path: Path) -> None:
    seed = tmp_path / "seed"
    seed.mkdir()
    workspace(seed)
    git(seed, "init", "-q", "-b", "main")
    git(seed, "config", "user.email", "seed@example.invalid")
    git(seed, "config", "user.name", "Seed")
    git(seed, "add", "-f", ".memoria/schemas")
    git(seed, "commit", "-q", "-m", "seed schema")
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "--bare", "-q", "-b", "main", remote.as_posix())
    git(seed, "remote", "add", "origin", remote.as_posix())
    git(seed, "push", "-q", "-u", "origin", "main")

    device_a = tmp_path / "device-a"
    device_b = tmp_path / "device-b"
    git(tmp_path, "clone", "-q", remote.as_posix(), device_a.as_posix())
    git(tmp_path, "clone", "-q", remote.as_posix(), device_b.as_posix())
    for clone, email in ((device_a, "a@example.invalid"), (device_b, "b@example.invalid")):
        git(clone, "config", "user.email", email)
        git(clone, "config", "user.name", clone.name)

    stage_concept(device_a, "knowledge/notes/from-a.md", note_text(title="From A"), machine="a")
    promote_checked(device_a, "knowledge/notes/from-a.md", machine="a")
    commit_writer_changes(device_a, "device a write", ["knowledge/notes/from-a.md"], machine="a")
    git(device_a, "push", "-q", "origin", "main")

    git(device_b, "pull", "-q", "--ff-only", "origin", "main")
    stage_concept(device_b, "knowledge/notes/from-b.md", note_text(title="From B"), machine="b")
    promote_checked(device_b, "knowledge/notes/from-b.md", machine="b")
    commit_writer_changes(device_b, "device b write", ["knowledge/notes/from-b.md"], machine="b")
    git(device_b, "push", "-q", "origin", "main")

    git(device_a, "pull", "-q", "--ff-only", "origin", "main")

    assert (device_a / "journal/a.jsonl").is_file()
    assert (device_a / "journal/b.jsonl").is_file()
    assert (device_a / "knowledge/notes/from-a.md").is_file()
    assert (device_a / "knowledge/notes/from-b.md").is_file()
    state = rebuild_trace_state(device_a)
    assert set(state) >= {"knowledge/notes/from-a.md", "knowledge/notes/from-b.md"}
    assert git(device_a, "status", "--short") == ""


def test_two_device_conflicting_git_writes_fail_visibly(tmp_path: Path) -> None:
    seed = tmp_path / "seed"
    seed.mkdir()
    workspace(seed)
    git(seed, "init", "-q", "-b", "main")
    git(seed, "config", "user.email", "seed@example.invalid")
    git(seed, "config", "user.name", "Seed")
    git(seed, "add", "-f", ".memoria/schemas")
    git(seed, "commit", "-q", "-m", "seed schema")
    stage_concept(seed, "knowledge/notes/shared.md", note_text(title="Shared"), machine="seed")
    promote_checked(seed, "knowledge/notes/shared.md", machine="seed")
    commit_writer_changes(seed, "seed shared note", ["knowledge/notes/shared.md"], machine="seed")
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "--bare", "-q", "-b", "main", remote.as_posix())
    git(seed, "remote", "add", "origin", remote.as_posix())
    git(seed, "push", "-q", "-u", "origin", "main")

    device_a = tmp_path / "device-a"
    device_b = tmp_path / "device-b"
    git(tmp_path, "clone", "-q", remote.as_posix(), device_a.as_posix())
    git(tmp_path, "clone", "-q", remote.as_posix(), device_b.as_posix())
    for clone, email in ((device_a, "a@example.invalid"), (device_b, "b@example.invalid")):
        git(clone, "config", "user.email", email)
        git(clone, "config", "user.name", clone.name)

    stage_concept(device_a, "knowledge/notes/shared.md", note_text(title="From A"), machine="a")
    promote_checked(device_a, "knowledge/notes/shared.md", machine="a")
    commit_writer_changes(device_a, "device a edit", ["knowledge/notes/shared.md"], machine="a")
    stage_concept(device_b, "knowledge/notes/shared.md", note_text(title="From B"), machine="b")
    promote_checked(device_b, "knowledge/notes/shared.md", machine="b")
    commit_writer_changes(device_b, "device b edit", ["knowledge/notes/shared.md"], machine="b")

    git(device_a, "push", "-q", "origin", "main")
    rejected = subprocess.run(
        ["git", "push", "-q", "origin", "main"],
        cwd=device_b,
        check=False,
        text=True,
        capture_output=True,
    )
    assert rejected.returncode != 0

    git(device_b, "fetch", "-q", "origin", "main")
    conflict = subprocess.run(
        ["git", "merge", "--no-edit", "FETCH_HEAD"],
        cwd=device_b,
        check=False,
        text=True,
        capture_output=True,
    )
    assert conflict.returncode != 0
    assert "UU knowledge/notes/shared.md" in git(device_b, "status", "--short")
    assert "<<<<<<<" in (device_b / "knowledge/notes/shared.md").read_text(encoding="utf-8")
    assert (device_b / "journal/a.jsonl").is_file()
    assert (device_b / "journal/b.jsonl").is_file()
