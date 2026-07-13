from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from memoria_vault.runtime import state, trusted_writer
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.trusted_writer import (
    commit_writer_changes as _commit_writer_changes,
)
from memoria_vault.runtime.trusted_writer import (
    mark_checked as _mark_checked,
)
from memoria_vault.runtime.trusted_writer import (
    observe_pi_edit,
    observe_pi_edit_from_head,
    rebuild_trace_state,
)
from memoria_vault.runtime.trusted_writer import (
    observe_pi_edits_from_status as _observe_pi_edits_from_status,
)
from memoria_vault.runtime.trusted_writer import (
    promote_checked as _promote_checked,
)
from memoria_vault.runtime.trusted_writer import (
    quarantine_untraced as _quarantine_untraced,
)
from memoria_vault.runtime.trusted_writer import (
    quarantine_untraced_from_status as _quarantine_untraced_from_status,
)
from memoria_vault.runtime.trusted_writer import (
    stage_concept as _stage_concept,
)
from memoria_vault.runtime.vaultio import is_ulid, read_frontmatter
from tests.helpers import WORKSPACE_SEED, call_with_context, copy_memoria_dirs, git, init_git


def stage_concept(vault: Path, *args, **kwargs):
    return call_with_context(_stage_concept, vault, *args, **kwargs)


def promote_checked(vault: Path, *args, **kwargs):
    return call_with_context(_promote_checked, vault, *args, **kwargs)


def mark_checked(vault: Path, *args, **kwargs):
    return call_with_context(_mark_checked, vault, *args, **kwargs)


def quarantine_untraced(vault: Path, *args, **kwargs):
    return call_with_context(_quarantine_untraced, vault, *args, **kwargs)


def quarantine_untraced_from_status(vault: Path, *args, **kwargs):
    return call_with_context(_quarantine_untraced_from_status, vault, *args, **kwargs)


def commit_writer_changes(vault: Path, *args, **kwargs):
    return call_with_context(_commit_writer_changes, vault, *args, **kwargs)


def observe_pi_edits_from_status(vault: Path, *args, **kwargs):
    kwargs.setdefault("actor", "integrity")
    return call_with_context(_observe_pi_edits_from_status, vault, *args, **kwargs)


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas")
    shutil.copyfile(WORKSPACE_SEED / ".gitignore", tmp_path / ".gitignore")
    return tmp_path


def note_text(*, title: str = "Alpha note") -> str:
    return (
        "---\n"
        "type: note\n"
        "id: 01KBN6V6KX0000000000000001\n"
        f"title: {title}\n"
        "tags: []\n"
        "links: {}\n"
        "---\n"
        "Alpha body.\n"
    )


def events(vault: Path) -> list[dict]:
    return list(iter_jsonl(vault / ".memoria/journal/test-machine.jsonl"))


def test_journal_path_does_not_normalize_machine(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_normalization(_value: str) -> str:
        raise AssertionError("journal path must not normalize machine")

    monkeypatch.setattr(trusted_writer, "safe_filename", fail_normalization)

    assert trusted_writer._journal_path(tmp_path, "already_normalized") == (
        tmp_path / ".memoria/journal/already_normalized.jsonl"
    )


def test_stage_concept_forces_unchecked_and_journals_derivation(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    event = stage_concept(
        vault,
        "notes/alpha.md",
        note_text(),
        inputs=[{"id": "catalog/sources/source-a/source.md", "sha256": "sha256:abc"}],
        run_id="run-1",
        machine="test-machine",
    )

    staged = vault / ".memoria/staging/notes/alpha.md"
    assert staged.is_file()
    assert not (vault / "notes/alpha.md").exists()
    frontmatter = read_frontmatter(staged)
    assert "check_status" not in frontmatter
    assert is_ulid(frontmatter["id"])
    assert "standing" not in frontmatter
    assert frontmatter["links"] == {}
    assert event["event"] == "derived"
    assert event["output_id"] == "notes/alpha.md"
    assert events(vault) == [event]


def test_stage_concept_preserves_mixed_author_caller_content(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    payload = "Human-selected ![figure](https://example.test/figure.png)."
    content = note_text().replace("Alpha body.", payload)

    stage_concept(vault, "notes/alpha.md", content, machine="test-machine")

    staged = (vault / ".memoria/staging/notes/alpha.md").read_text(encoding="utf-8")
    assert payload in staged


def test_stage_concept_rejects_retired_frontmatter_fields(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    with pytest.raises(ValueError, match="retired frontmatter field is ignored: check_status"):
        stage_concept(
            vault,
            "notes/alpha.md",
            "---\ntype: note\ncheck_status: checked\ntitle: Alpha note\ntags: []\nlinks: {}\n---\nAlpha body.\n",
            machine="test-machine",
        )
    with pytest.raises(ValueError, match="retired frontmatter field is ignored: status"):
        stage_concept(
            vault,
            "notes/alpha.md",
            "---\ntype: note\ntitle: Alpha note\nstatus: candidate\ntags: []\nlinks: {}\n---\nAlpha body.\n",
            machine="test-machine",
        )


def test_promote_checked_writes_bundle_file_and_records_check(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    stage_concept(vault, "notes/alpha.md", note_text(), machine="test-machine")

    event = promote_checked(vault, "notes/alpha.md", machine="test-machine")

    target = vault / "notes/alpha.md"
    assert target.is_file()
    assert not (vault / ".memoria/staging/notes/alpha.md").exists()
    assert "check_status" not in read_frontmatter(target)
    assert state.concept_check_status(vault, "notes/alpha.md") == "checked"
    assert event["event"] == "check-fired"
    assert event["status"] == "passed"
    assert event["output_sha256"] == sha256_file(target)
    for path in (vault / ".memoria/journal").glob("*.jsonl"):
        path.unlink()
    assert rebuild_trace_state(vault)["notes/alpha.md"] == event
    assert quarantine_untraced(vault, ["notes/alpha.md"], machine="test-machine") == []


def test_promote_checked_records_payload_before_bundle_file_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vault = workspace(tmp_path)
    target = "notes/crash.md"
    stage_concept(vault, target, note_text(title="Crash"), machine="test-machine")

    def crash_write(*_args, **_kwargs) -> None:
        raise RuntimeError("simulated materialization crash")

    monkeypatch.setattr(trusted_writer, "write_frontmatter_doc", crash_write)

    with pytest.raises(RuntimeError, match="simulated materialization crash"):
        promote_checked(vault, target, machine="test-machine")

    assert not (vault / target).exists()
    with state.connect(vault) as conn:
        row = conn.execute(
            """
            SELECT o.check_status, o.materialization_status, p.payload_text
            FROM outputs o
            JOIN materialization_payloads p ON p.output_id = o.output_id
            WHERE o.output_id = ?
            """,
            (target,),
        ).fetchone()
    assert row["check_status"] == "checked"
    assert row["materialization_status"] == "pending"
    assert "Crash" in row["payload_text"]
    assert state.recover_pending_materializations(vault) == []
    assert not (vault / target).exists()
    with state.connect(vault) as conn:
        failed = conn.execute(
            "SELECT materialization_status, failure_reason FROM outputs WHERE output_id = ?",
            (target,),
        ).fetchone()
    assert tuple(failed) == ("failed", "materialization target is not committed")


def test_promote_checked_rejects_unsupported_promotion_check(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    stage_concept(vault, "notes/alpha.md", note_text(), machine="test-machine")

    with pytest.raises(ValueError, match="unsupported promotion checks: later-integrity"):
        promote_checked(
            vault,
            "notes/alpha.md",
            checks=["later-integrity"],
            machine="test-machine",
        )

    assert not (vault / "notes/alpha.md").exists()
    assert (vault / ".memoria/staging/notes/alpha.md").is_file()


def test_commit_writer_changes_couples_concept_and_journal_only(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    init_git(vault, "writer@example.invalid", "Trusted Writer")
    (vault / "other.md").write_text("unrelated\n", encoding="utf-8")
    git(vault, "add", "other.md")

    stage_concept(vault, "notes/alpha.md", note_text(), machine="test-machine")
    promote_checked(vault, "notes/alpha.md", machine="test-machine")
    commit_hash = commit_writer_changes(
        vault,
        "trusted write alpha",
        ["notes/alpha.md"],
        machine="test-machine",
    )

    committed = set(git(vault, "show", "--name-only", "--format=", commit_hash).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, "notes/alpha.md"}
    assert (vault / state.JOURNAL_HEAD_REL).read_text(
        encoding="utf-8"
    ).strip() == state.journal_head(vault)
    assert git(vault, "diff", "--cached", "--name-only") == "other.md"


def test_commit_writer_extracts_typed_edge_candidates_without_mutating_links(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    init_git(vault, "writer@example.invalid", "Trusted Writer")
    content = note_text().replace(
        "Alpha body.",
        "Typed [[supports::notes/beta.md]] and bare [[notes/gamma.md]].",
    )

    stage_concept(vault, "notes/alpha.md", content, machine="test-machine")
    promote_checked(vault, "notes/alpha.md", machine="test-machine")
    commit_hash = commit_writer_changes(
        vault,
        "trusted write alpha",
        ["notes/alpha.md"],
        machine="test-machine",
    )

    prompts = sorted((vault / "inbox").glob("work-prompt-edge-candidate-*.md"))
    assert len(prompts) == 1
    prompt_text = prompts[0].read_text(encoding="utf-8")
    assert "supports" in prompt_text
    assert "notes/beta.md" in prompt_text
    assert "notes/gamma.md" not in prompt_text
    assert read_frontmatter(vault / "notes/alpha.md")["links"] == {}
    committed = set(git(vault, "show", "--name-only", "--format=", commit_hash).splitlines())
    assert prompts[0].relative_to(vault).as_posix() in committed


def test_edge_candidate_prompt_renders_composed_code_span_target_inert(tmp_path: Path) -> None:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("Pandoc is optional")
    vault = workspace(tmp_path)
    init_git(vault, "writer@example.invalid", "Trusted Writer")
    content = note_text().replace(
        "Alpha body.",
        'Typed [[supports::target ` <img src="https://evil.example/x"> `]].',
    )

    stage_concept(vault, "notes/alpha.md", content, machine="test-machine")
    promote_checked(vault, "notes/alpha.md", machine="test-machine")
    commit_writer_changes(
        vault,
        "trusted write alpha",
        ["notes/alpha.md"],
        machine="test-machine",
    )

    [prompt] = sorted((vault / "inbox").glob("work-prompt-edge-candidate-*.md"))
    rendered = subprocess.run(
        [pandoc, "-f", "commonmark", "-t", "html"],
        input=prompt.read_text(encoding="utf-8"),
        text=True,
        capture_output=True,
        check=True,
    ).stdout

    assert "<img" not in rendered


def test_edge_candidate_prompt_neutralizes_code_owned_note_title(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    init_git(vault, "writer@example.invalid", "Trusted Writer")
    content = note_text(title="bad` ![title](http://beacon.example/title.png)").replace(
        "Alpha body.",
        "Typed [[supports::notes/beta.md]].",
    )

    stage_concept(vault, "notes/alpha.md", content, machine="test-machine")
    promote_checked(vault, "notes/alpha.md", machine="test-machine")
    commit_writer_changes(
        vault,
        "trusted write alpha",
        ["notes/alpha.md"],
        machine="test-machine",
    )

    [prompt] = sorted((vault / "inbox").glob("work-prompt-edge-candidate-*.md"))
    prompt_text = prompt.read_text(encoding="utf-8")
    assert "![title]" not in prompt_text
    assert "`http://beacon.example/title.png`" in prompt_text


def test_observe_pi_edit_backfills_prior_head_and_live_check(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    target = vault / "notes/pi.md"
    target.parent.mkdir(parents=True)
    target.write_text(note_text(title="PI note"), encoding="utf-8")
    prior_sha = sha256_file(target)
    target.write_text(note_text(title="PI note") + "\nPI edit.\n", encoding="utf-8")

    event = observe_pi_edit(
        vault,
        "notes/pi.md",
        prior_sha,
        inputs=[{"id": "catalog/sources/source-a/source.md", "sha256": "sha256:abc"}],
        machine="test-machine",
    )

    frontmatter = read_frontmatter(target)
    assert "check_status" not in frontmatter
    assert is_ulid(frontmatter["id"])
    assert "standing" not in frontmatter
    assert frontmatter["links"] == {}
    assert event["event"] == "observed_external_edit"
    assert event["actor"] == "pi"
    assert event["inputs"][-1] == {
        "id": "notes/pi.md",
        "sha256": prior_sha,
        "role": "prior-head",
    }
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT check_status FROM outputs WHERE output_id = 'notes/pi.md'"
        ).fetchone()
        consumable = conn.execute(
            "SELECT output_id FROM consumable_outputs WHERE output_id = 'notes/pi.md'"
        ).fetchone()
    assert row["check_status"] == "unchecked"
    assert consumable is None

    check_event = mark_checked(vault, "notes/pi.md", machine="test-machine")

    assert "check_status" not in read_frontmatter(target)
    assert state.concept_check_status(vault, "notes/pi.md") == "checked"
    assert check_event["status"] == "passed"
    assert rebuild_trace_state(vault)["notes/pi.md"] == check_event


def test_observe_pi_edit_from_head_keeps_prior_upstream_inputs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    init_git(vault, "writer@example.invalid", "Trusted Writer")
    stage_concept(
        vault,
        "notes/pi.md",
        note_text(title="PI note"),
        inputs=[{"id": "catalog/sources/source-a/source.md", "sha256": "sha256:abc"}],
        machine="test-machine",
    )
    promote_checked(vault, "notes/pi.md", machine="test-machine")
    commit_writer_changes(vault, "trusted write pi", ["notes/pi.md"], machine="test-machine")
    prior_sha = sha256_file(vault / "notes/pi.md")
    (vault / "notes/pi.md").write_text(
        note_text(title="PI note") + "\nPI edit.\n",
        encoding="utf-8",
    )
    for path in (vault / ".memoria/journal").glob("*.jsonl"):
        path.unlink()

    event = observe_pi_edit_from_head(vault, "notes/pi.md", machine="test-machine")

    assert event["event"] == "observed_external_edit"
    assert event["actor"] == "pi"
    assert event["inputs"] == [
        {"id": "catalog/sources/source-a/source.md", "sha256": "sha256:abc"},
        {"id": "notes/pi.md", "sha256": prior_sha, "role": "prior-head"},
    ]
    assert "check_status" not in read_frontmatter(vault / "notes/pi.md")
    assert state.concept_check_status(vault, "notes/pi.md") == "unchecked"


def test_observe_pi_edits_from_status_commits_pi_files_and_journal(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    init_git(vault, "writer@example.invalid", "Trusted Writer")
    stage_concept(
        vault,
        "notes/pi.md",
        note_text(title="PI note"),
        inputs=[{"id": "catalog/sources/source-a/source.md", "sha256": "sha256:abc"}],
        machine="test-machine",
    )
    promote_checked(vault, "notes/pi.md", machine="test-machine")
    commit_writer_changes(vault, "trusted write pi", ["notes/pi.md"], machine="test-machine")
    (vault / "notes/pi.md").write_text(
        note_text(title="PI note") + "\nPI edit.\n",
        encoding="utf-8",
    )
    new_path = vault / "notes/pi-new.md"
    new_path.write_text(note_text(title="PI new"), encoding="utf-8")

    result = observe_pi_edits_from_status(vault, machine="test-machine")

    assert result["paths"] == ["notes/pi-new.md", "notes/pi.md"]
    assert [event["event"] for event in result["observed"]] == [
        "observed_external_edit",
        "observed_external_edit",
    ]
    assert [event["actor"] for event in result["observed"]] == ["pi", "pi"]
    assert (
        result["observed"][0]["inputs"][-1]["sha256"]
        == "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    assert result["observed"][1]["inputs"][0] == {
        "id": "catalog/sources/source-a/source.md",
        "sha256": "sha256:abc",
    }
    assert "check_status" not in read_frontmatter(vault / "notes/pi.md")
    assert "check_status" not in read_frontmatter(new_path)
    assert state.concept_check_status(vault, "notes/pi.md") == "unchecked"
    assert state.concept_check_status(vault, "notes/pi-new.md") == "unchecked"
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {
        state.JOURNAL_HEAD_REL,
        "notes/pi-new.md",
        "notes/pi.md",
    }
    assert git(vault, "status", "--short", "--", "journal", "knowledge") == ""


def test_promote_checked_rejects_invalid_staged_concept(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    staged = vault / ".memoria/staging/notes/bad.md"
    staged.parent.mkdir(parents=True)
    staged.write_text("---\ntype: note\ntags: []\nlinks: {}\n---\nBody.\n", encoding="utf-8")

    try:
        promote_checked(vault, "notes/bad.md", machine="test-machine")
    except ValueError as exc:
        assert "missing required field: title" in str(exc)
    else:
        raise AssertionError("invalid staged Concept should not promote")

    assert not (vault / "notes/bad.md").exists()


def test_quarantine_untraced_moves_explicit_foreign_file(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    foreign = vault / "notes/foreign.md"
    foreign.parent.mkdir(parents=True)
    foreign.write_text(note_text(title="Foreign"), encoding="utf-8")
    original_sha = sha256_file(foreign)

    [event] = quarantine_untraced(
        vault,
        ["notes/foreign.md"],
        machine="test-machine",
    )

    quarantined = vault / ".memoria/quarantine/notes/foreign.md"
    assert not foreign.exists()
    assert quarantined.is_file()
    assert "check_status" not in read_frontmatter(quarantined)
    assert state.concept_check_status(vault, "notes/foreign.md") == "quarantined"
    assert event["event"] == "check-fired"
    assert event["status"] == "failed"
    assert event["reason"] == "foreign-untraced"
    assert event["target_sha256"] == original_sha
    assert event["quarantined_id"] == ".memoria/quarantine/notes/foreign.md"


def test_quarantine_untraced_from_status_scans_bundle_changes(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    git(vault, "init", "-q")
    foreign = vault / "notes/foreign-status.md"
    foreign.parent.mkdir(parents=True)
    foreign.write_text(note_text(title="Foreign status"), encoding="utf-8")

    [event] = quarantine_untraced_from_status(vault, machine="test-machine")

    assert event["target_id"] == "notes/foreign-status.md"
    assert not foreign.exists()
    assert (vault / ".memoria/quarantine/notes/foreign-status.md").is_file()


def test_two_device_git_writes_keep_per_machine_journals_mergeable(tmp_path: Path) -> None:
    seed = tmp_path / "seed"
    seed.mkdir()
    workspace(seed)
    git(seed, "init", "-q", "-b", "main")
    git(seed, "config", "user.email", "seed@example.invalid")
    git(seed, "config", "user.name", "Seed")
    git(seed, "add", "-f", ".gitignore", ".memoria/schemas")
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

    stage_concept(device_a, "notes/from-a.md", note_text(title="From A"), machine="a")
    promote_checked(device_a, "notes/from-a.md", machine="a")
    commit_writer_changes(device_a, "device a write", ["notes/from-a.md"], machine="a")
    git(device_a, "push", "-q", "origin", "main")

    git(device_b, "pull", "-q", "--ff-only", "origin", "main")
    stage_concept(device_b, "notes/from-b.md", note_text(title="From B"), machine="b")
    promote_checked(device_b, "notes/from-b.md", machine="b")
    commit_writer_changes(device_b, "device b write", ["notes/from-b.md"], machine="b")
    git(device_b, "push", "-q", "origin", "main")

    git(device_a, "pull", "-q", "--ff-only", "origin", "main")

    assert (device_a / ".memoria/journal/a.jsonl").is_file()
    assert (device_a / state.JOURNAL_HEAD_REL).is_file()
    assert (device_a / "notes/from-a.md").is_file()
    assert (device_a / "notes/from-b.md").is_file()
    trace_state = rebuild_trace_state(device_a)
    assert set(trace_state) == {"notes/from-a.md"}
    assert git(device_a, "status", "--short") == ""


def test_two_device_conflicting_git_writes_fail_visibly(tmp_path: Path) -> None:
    seed = tmp_path / "seed"
    seed.mkdir()
    workspace(seed)
    git(seed, "init", "-q", "-b", "main")
    git(seed, "config", "user.email", "seed@example.invalid")
    git(seed, "config", "user.name", "Seed")
    git(seed, "add", "-f", ".gitignore", ".memoria/schemas")
    git(seed, "commit", "-q", "-m", "seed schema")
    stage_concept(seed, "notes/shared.md", note_text(title="Shared"), machine="seed")
    promote_checked(seed, "notes/shared.md", machine="seed")
    commit_writer_changes(seed, "seed shared note", ["notes/shared.md"], machine="seed")
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

    stage_concept(device_a, "notes/shared.md", note_text(title="From A"), machine="a")
    promote_checked(device_a, "notes/shared.md", machine="a")
    commit_writer_changes(device_a, "device a edit", ["notes/shared.md"], machine="a")
    stage_concept(device_b, "notes/shared.md", note_text(title="From B"), machine="b")
    promote_checked(device_b, "notes/shared.md", machine="b")
    commit_writer_changes(device_b, "device b edit", ["notes/shared.md"], machine="b")

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
    assert "UU .memoria/journal-head" in git(device_b, "status", "--short")
    assert "UU notes/shared.md" in git(device_b, "status", "--short")
    assert "<<<<<<<" in (device_b / "notes/shared.md").read_text(encoding="utf-8")
    assert (device_b / ".memoria/journal/b.jsonl").is_file()
