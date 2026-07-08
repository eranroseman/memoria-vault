from __future__ import annotations

from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.capture import capture_source
from memoria_vault.runtime.integrity import cascade_rollback, trace_downstream
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.knowledge import emit_note_candidates
from memoria_vault.runtime.operations import compile_source_digest
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.trusted_writer import (
    commit_writer_changes,
    mark_checked,
    observe_pi_edit,
    promote_checked,
    stage_concept,
)
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.helpers import copy_memoria_dirs, git, init_git


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas", "config")
    init_git(tmp_path, "integrity@example.invalid", "Integrity")
    return tmp_path


def note_text(title: str, *, status: str = "checked") -> str:
    return (
        "---\n"
        f"type: note\ncheck_status: {status}\ntitle: {title}\n"
        "status: accepted\n---\n"
        f"# {title}\n\nBody.\n"
    )


def test_cascade_rollback_reverts_machine_descendants_and_flags_pi_notes(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )
    digest = compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="digest-machine",
    )
    notes = emit_note_candidates(
        vault,
        "source-alpha",
        [
            {
                "title": "Framing changes the question",
                "description": "A candidate note from the source digest.",
                "body": "The source reframes the problem before measuring outcomes.",
                "claim_text": "Framing changes which outcomes matter.",
            }
        ],
        machine="note-machine",
    )
    pi_note = "notes/pi-downstream.md"
    pi_path = vault / pi_note
    pi_path.parent.mkdir(parents=True, exist_ok=True)
    pi_path.write_text(note_text("PI downstream"), encoding="utf-8")
    prior_sha = sha256_file(pi_path)
    pi_path.write_text(note_text("PI downstream") + "\nPI edit.\n", encoding="utf-8")
    observe_pi_edit(
        vault,
        pi_note,
        prior_sha,
        inputs=[
            {"id": digest["digest_path"], "sha256": sha256_file(vault / digest["digest_path"])}
        ],
        machine="pi-machine",
    )
    mark_checked(vault, pi_note, machine="pi-machine")
    commit_writer_changes(vault, "observe pi note", [pi_note], machine="pi-machine")

    downstream = {event["output_id"] for event in trace_downstream(vault, digest["digest_path"])}
    assert notes["note_paths"][0] in downstream
    assert pi_note in downstream

    result = cascade_rollback(
        vault,
        "catalog/sources/source-alpha",
        reason="seeded poisoned source",
        machine="integrity-machine",
    )

    assert digest["digest_path"] in result["reverted"]
    assert set(digest["hub_paths"]).issubset(result["reverted"])
    assert notes["note_paths"][0] in result["reverted"]
    assert pi_note in result["needs_human"]
    assert not (vault / digest["digest_path"]).exists()
    assert all(not (vault / hub_path).exists() for hub_path in digest["hub_paths"])
    assert not (vault / notes["note_paths"][0]).exists()
    assert (vault / pi_note).is_file()
    assert "check_status" not in read_frontmatter(
        vault / ".memoria/quarantine" / digest["digest_path"]
    )
    assert state.concept_check_status(vault, digest["digest_path"]) == "quarantined"
    assert "check_status" not in read_frontmatter(
        vault / ".memoria/quarantine" / notes["note_paths"][0]
    )
    assert state.concept_check_status(vault, notes["note_paths"][0]) == "quarantined"

    rollback_events = list(iter_jsonl(vault / ".memoria/journal/integrity-machine.jsonl"))
    assert [event["event"] for event in rollback_events].count("resolved") == len(
        result["reverted"]
    )
    assert any(
        event.get("event") == "derived"
        and event.get("output_id") == digest["digest_path"]
        and event.get("operation") == "cascade-rollback"
        for event in rollback_events
    )
    assert any(
        event.get("event") == "check-fired"
        and event.get("target_id") == pi_note
        and event.get("route") == "ask"
        for event in rollback_events
    )

    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {
        state.JOURNAL_HEAD_REL,
        digest["digest_path"],
        *digest["hub_paths"],
        notes["note_paths"][0],
    }


def test_cascade_rollback_restores_previous_file_version_with_git(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    target = "notes/versioned.md"
    version_one = (
        "---\ntype: note\ntitle: Version one\ntags: []\nlinks: {}\n---\nVersion one body.\n"
    )
    version_two = version_one.replace("Version one", "Version two")
    stage_concept(vault, target, version_one, machine="writer")
    promote_checked(vault, target, machine="writer")
    commit_writer_changes(vault, "write version one", [target], machine="writer")
    stage_concept(vault, target, version_two, machine="writer")
    promote_checked(vault, target, machine="writer")
    commit_writer_changes(vault, "write version two", [target], machine="writer")

    result = cascade_rollback(
        vault,
        target,
        reason="restore previous version",
        include_target=True,
        machine="integrity-machine",
    )

    assert result["reverted"] == [target]
    assert "Version one" in (vault / target).read_text(encoding="utf-8")
    assert "Version two" in (vault / ".memoria/quarantine" / target).read_text(encoding="utf-8")
    rollback_events = list(iter_jsonl(vault / ".memoria/journal/integrity-machine.jsonl"))
    resolved = next(event for event in rollback_events if event["event"] == "resolved")
    assert resolved["restore_source"]
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, target}
