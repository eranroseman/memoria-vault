from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from memoria_vault.runtime import indexing, state
from memoria_vault.runtime.capture import capture_source as _capture_source
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.knowledge import (
    curate_note_candidate as _curate_note_candidate,
)
from memoria_vault.runtime.knowledge import (
    curate_note_link as _curate_note_link,
)
from memoria_vault.runtime.knowledge import (
    emit_note_candidates as _emit_note_candidates,
)
from memoria_vault.runtime.operations import compile_source_digest as _compile_source_digest
from memoria_vault.runtime.read_barrier import is_consumable_checked_file
from memoria_vault.runtime.trusted_writer import mark_checked as _mark_checked
from memoria_vault.runtime.trusted_writer import observe_pi_edit_from_head
from memoria_vault.runtime.trusted_writer import promote_checked as _promote_checked
from memoria_vault.runtime.trusted_writer import stage_concept as _stage_concept
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.helpers import (
    _md,
    call_with_context,
    copy_memoria_dirs,
    git,
    init_git,
    mark_file_status,
    operation_context,
)


def _call(function, vault: Path, *args, **kwargs):
    return call_with_context(function, vault, *args, **kwargs)


def capture_source(vault: Path, *args, **kwargs):
    return _call(_capture_source, vault, *args, **kwargs)


def curate_note_candidate(vault: Path, *args, **kwargs):
    return _call(_curate_note_candidate, vault, *args, **kwargs)


def curate_note_link(vault: Path, *args, **kwargs):
    return _call(_curate_note_link, vault, *args, **kwargs)


def move_concept(vault: Path, *args, **kwargs):
    from memoria_vault.runtime.knowledge import move_concept as _move_concept

    return _call(_move_concept, vault, *args, **kwargs)


def rebuild_passage_index(vault: Path, *args, **kwargs):
    return _call(indexing.rebuild_passage_index, vault, *args, **kwargs)


def stage_concept(vault: Path, *args, **kwargs):
    return _call(_stage_concept, vault, *args, **kwargs)


def promote_checked(vault: Path, *args, **kwargs):
    return _call(_promote_checked, vault, *args, **kwargs)


def emit_note_candidates(vault: Path, *args, **kwargs):
    context = operation_context(
        vault,
        operation_id="propose-note-candidates",
        machine=str(kwargs.pop("machine", "test-machine") or "test-machine"),
        run_id=str(kwargs.pop("run_id", "test-run") or "test-run"),
    )
    return _emit_note_candidates(vault, *args, context=context, **kwargs)


def compile_source_digest(vault: Path, *args, **kwargs):
    return _call(_compile_source_digest, vault, *args, **kwargs)


def mark_checked(vault: Path, *args, **kwargs):
    return _call(_mark_checked, vault, *args, **kwargs)


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas", "config")
    init_git(tmp_path, "knowledge@example.invalid", "Knowledge")
    return tmp_path


def checked_note(vault: Path, name: str, title: str, note_id: str) -> Path:
    path = vault / "notes" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntype: note\nid: {note_id}\ntitle: {title}\ntags: []\nlinks: {{}}\n---\nBody.\n",
        encoding="utf-8",
    )
    mark_file_status(vault, path.relative_to(vault).as_posix())
    return path


def test_emit_note_candidates_promotes_checked_candidate_notes(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )
    compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="digest-machine",
    )

    result = emit_note_candidates(
        vault,
        "source-alpha",
        [
            {
                "title": "Framing changes the question",
                "description": "A candidate note from the source digest.",
                "body": "The source reframes the problem before measuring outcomes.",
                "claim_text": "Framing changes which outcomes matter.",
                "tags": ["Framing"],
            }
        ],
        machine="note-machine",
        run_id="notes-alpha",
    )

    [note_rel] = result["note_paths"]
    note = vault / note_rel
    fm = read_frontmatter(note)
    assert fm["type"] == "note"
    assert "check_status" not in fm
    assert state.concept_check_status(vault, note_rel) == "checked"
    assert "status" not in fm
    assert state.note_curation_status(vault, note_rel) == "candidate"
    assert fm["work_id"] == "catalog/sources/source-alpha"
    assert "evidence_set" not in fm
    assert "citations" not in fm
    assert fm["claim_text"] == "Framing changes which outcomes matter."

    events = list(iter_jsonl(vault / ".memoria/journal/note-machine.jsonl"))
    assert [event["event"] for event in events] == [
        "run",
        "model_call",
        "derived",
        "check-fired",
        "run",
    ]
    assert events[1]["runner"] == "pydantic-ai"
    assert events[-1]["outputs"] == [note_rel]
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, note_rel}


def test_emit_note_candidates_neutralizes_every_model_derived_text_field(
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
    compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="digest-machine",
    )
    candidates = [
        {
            "title": "![Candidate](http://beacon.example/title.png)",
            "description": '<img src="http://beacon.example/description.png">',
            "body": "Body http://beacon.example/body",
            "claim_text": "[claim](http://beacon.example/claim)",
            "quote": "![quote](http://beacon.example/quote.png)",
            "tags": ["[tag](http://beacon.example/tag)"],
            "annotation_ref": {
                "work_id": "catalog/sources/source-alpha",
                "text_quote": "http://beacon.example/annotation",
            },
        }
    ]

    result = emit_note_candidates(
        vault,
        "source-alpha",
        candidates,
        machine="note-machine",
    )

    [note_rel] = result["note_paths"]
    rendered = (vault / note_rel).read_text(encoding="utf-8")
    assert "![" not in rendered
    assert "<img" not in rendered
    assert "](http://beacon.example" not in rendered
    for url in (
        "http://beacon.example/title.png",
        "http://beacon.example/description.png",
        "http://beacon.example/body",
        "http://beacon.example/claim",
        "http://beacon.example/quote.png",
        "http://beacon.example/tag",
        "http://beacon.example/annotation",
    ):
        assert f"`{url}`" in rendered


def test_emit_note_candidate_renders_composed_fenced_title_inert(tmp_path: Path) -> None:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("Pandoc is optional")
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-fenced-title",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )
    compile_source_digest(
        vault,
        "source-fenced-title",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="digest-machine",
    )

    result = emit_note_candidates(
        vault,
        "source-fenced-title",
        [
            {
                "title": '```\n<img src="https://evil.example/candidate-title">\n```',
                "body": "Candidate body.",
            }
        ],
        machine="note-machine",
    )

    [note_rel] = result["note_paths"]
    rendered = subprocess.run(
        [pandoc, "-f", "commonmark", "-t", "html"],
        input=(vault / note_rel).read_text(encoding="utf-8"),
        text=True,
        capture_output=True,
        check=True,
    ).stdout

    assert "<img" not in rendered


def test_emit_note_candidates_preserves_pdf_annotation_selector(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "pdf-source",
        "PDF Source",
        "A fixture PDF source.",
        "The PDF reports an anchored finding on page 3.",
        raw_bytes=b"%PDF-1.4 fixture bytes\n",
        raw_filename="paper.pdf",
        machine="capture-machine",
    )
    compile_source_digest(
        vault,
        "pdf-source",
        ["Anchored finding", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="digest-machine",
    )
    annotation_ref = {
        "work_id": "catalog/sources/pdf-source",
        "raw_copy_path": ".memoria/blobs/source-content/pdf-source/raw/paper.pdf",
        "page": 3,
        "text_quote": "anchored finding",
        "bbox": [72, 144, 300, 180],
    }

    result = emit_note_candidates(
        vault,
        "pdf-source",
        [
            {
                "title": "PDF anchored finding",
                "description": "A note with page/span/bbox provenance.",
                "body": "The PDF reports an anchored finding on page 3.",
                "claim_text": "The PDF reports an anchored finding.",
                "quote": "anchored finding",
                "annotation_ref": annotation_ref,
            }
        ],
        machine="note-machine",
    )

    [note_rel] = result["note_paths"]
    note_fm = read_frontmatter(vault / note_rel)
    assert note_fm["annotation_ref"] == annotation_ref
    assert note_fm["quote"] == "anchored finding"


def test_curate_note_candidate_accepts_checked_candidate_with_journal(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )
    compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="digest-machine",
    )
    notes = emit_note_candidates(
        vault,
        "source-alpha",
        [{"title": "Curated candidate", "body": "The body stays intact."}],
        machine="note-machine",
    )

    result = curate_note_candidate(
        vault,
        notes["note_paths"][0],
        "accepted",
        actor="pi",
        reason="PI approved",
        machine="curator",
    )

    note_rel = notes["note_paths"][0]
    assert result["note_path"] == note_rel
    assert result["status"] == "accepted"
    assert "status" not in read_frontmatter(vault / note_rel)
    assert state.note_curation_status(vault, note_rel) == "accepted"
    assert "The body stays intact." in (vault / note_rel).read_text(encoding="utf-8")
    event = list(iter_jsonl(vault / ".memoria/journal/curator.jsonl"))[-1]
    assert event["event"] == "resolved"
    assert event["operation"] == "curate-note-candidate"
    assert event["target_id"] == note_rel
    assert event["resolution"] == "accepted"
    assert event["reason"] == "PI approved"
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL}


def test_pi_can_edit_candidate_text_before_accepting(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    capture_source(
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )
    compile_source_digest(
        vault,
        "source-alpha",
        ["Framing", "Methods", "Outcomes", "Gaps", "Impact"],
        machine="digest-machine",
    )
    notes = emit_note_candidates(
        vault,
        "source-alpha",
        [{"title": "Editable candidate", "body": "Machine draft."}],
        machine="note-machine",
    )
    note_rel = notes["note_paths"][0]
    note = vault / note_rel

    note.write_text(
        note.read_text(encoding="utf-8").replace("Machine draft.", "PI-edited claim."),
        encoding="utf-8",
    )
    observed = observe_pi_edit_from_head(vault, note_rel, machine="pi-machine")
    check = mark_checked(vault, note_rel, machine="pi-machine")
    result = curate_note_candidate(
        vault,
        note_rel,
        "accepted",
        actor="pi",
        reason="PI edited then accepted",
        machine="curator",
    )

    assert observed["actor"] == "pi"
    assert check["status"] == "passed"
    assert result["status"] == "accepted"
    assert "status" not in read_frontmatter(note)
    assert state.note_curation_status(vault, note_rel) == "accepted"
    assert "PI-edited claim." in note.read_text(encoding="utf-8")


def test_curate_note_candidate_rejects_non_candidate_status(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _md(
        vault / "notes/already.md",
        "type: note\ncheck_status: checked\ntitle: Already\n",
    )

    try:
        curate_note_candidate(vault, "already", "rejected", actor="pi", machine="curator")
    except ValueError as exc:
        assert "not a candidate note" in str(exc)
    else:
        raise AssertionError("curating an accepted note should fail")


def test_curate_note_link_records_typed_link_on_checked_note(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    checked_note(vault, "source", "Source", "01KBN6V6KX0000000000000001")
    checked_note(vault, "target", "Target", "01KBN6V6KX0000000000000002")

    result = curate_note_link(
        vault,
        "source",
        "supports",
        "target",
        actor="pi",
        reason="PI linked claims",
        machine="curator",
    )

    source_fm = read_frontmatter(vault / "notes/source.md")
    assert source_fm["links"] == {"supports": ["notes/target.md"]}
    assert result["source_note_path"] == "notes/source.md"
    assert result["target_path"] == "notes/target.md"
    assert result["link_type"] == "supports"
    assert result["changed"] is True
    event = list(iter_jsonl(vault / ".memoria/journal/curator.jsonl"))[-1]
    assert event["event"] == "resolved"
    assert event["operation"] == "curate-note-link"
    assert event["linked_id"] == "notes/target.md"
    assert event["reason"] == "PI linked claims"
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, "notes/source.md"}


def test_curate_note_link_rejects_invalid_source_without_mutation(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    source = checked_note(vault, "source", "Source", "01KBN6V6KX0000000000000001")
    checked_note(vault, "target", "Target", "01KBN6V6KX0000000000000002")
    source.write_text(
        source.read_text(encoding="utf-8").replace(
            "type: note\n", "type: note\ncheck_status: checked\n"
        ),
        encoding="utf-8",
    )
    mark_file_status(vault, "notes/source.md")
    before = source.read_text(encoding="utf-8")
    journal = vault / ".memoria/journal/curator.jsonl"
    assert not journal.exists()

    with pytest.raises(ValueError, match="retired frontmatter field is ignored: check_status"):
        curate_note_link(vault, "source", "supports", "target", actor="pi", machine="curator")

    assert source.read_text(encoding="utf-8") == before
    assert not journal.exists()
    assert state.concept_check_status(vault, "notes/source.md") == "checked"


def linked_note(vault: Path, name: str, note_id: str, link_type: str, target: str) -> Path:
    """A checked note holding one links: entry in the surface form it was written in."""
    path = vault / "notes" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntype: note\nid: {note_id}\ntitle: {name}\ntags: []\n"
        f'links:\n  {link_type}:\n    - "{target}"\n---\nBody.\n',
        encoding="utf-8",
    )
    mark_file_status(vault, f"notes/{name}.md")
    return path


def commit_notes(vault: Path) -> None:
    """Track the fixture bundle, the standing `memoria mv` moves a file from."""
    git(vault, "add", "--", "notes")
    git(vault, "commit", "-q", "-m", "seed notes")


def test_move_concept_rewrites_inbound_links_and_path_in_one_transaction(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    checked_note(vault, "target", "Target", "01KBN6V6KX0000000000000010")
    linked_note(
        vault,
        "wiki-linker",
        "01KBN6V6KX0000000000000011",
        "supports",
        "[[notes/target|the target]]",
    )
    linked_note(vault, "bare-linker", "01KBN6V6KX0000000000000012", "extends", "notes/target.md")
    commit_notes(vault)

    result = move_concept(
        vault, "notes/target.md", "notes/target-moved.md", actor="pi", machine="curator"
    )

    assert result["old_path"] == "notes/target.md"
    assert result["new_path"] == "notes/target-moved.md"
    assert result["rewritten"] == ["notes/bare-linker.md", "notes/wiki-linker.md"]
    assert not (vault / "notes/target.md").exists()
    assert (vault / "notes/target-moved.md").is_file()
    # Surface forms preserved: wikilink keeps its alias, bare path stays bare.
    wiki = read_frontmatter(vault / "notes/wiki-linker.md")
    assert wiki["links"]["supports"] == ["[[notes/target-moved|the target]]"]
    bare = read_frontmatter(vault / "notes/bare-linker.md")
    assert bare["links"]["extends"] == ["notes/target-moved.md"]
    with state.connect(vault) as conn:
        row = conn.execute(
            "SELECT concept_id FROM concepts WHERE path = 'notes/target-moved.md'"
        ).fetchone()
    assert row is not None
    # A ULID identity is untouched by its path moving.
    assert row["concept_id"] == "01KBN6V6KX0000000000000010"
    # Every file the move edited is re-signed, so none of them silently drops out
    # of the sha256 read barrier the way an out-of-band edit would.
    for rel in ("notes/target-moved.md", "notes/wiki-linker.md", "notes/bare-linker.md"):
        assert is_consumable_checked_file(vault, rel, enqueue_scan=False), rel
    # One trusted-writer commit carries the move and every rewrite.
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert {
        "notes/target-moved.md",
        "notes/wiki-linker.md",
        "notes/bare-linker.md",
    } <= committed


def test_move_concept_refuses_bad_targets(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _md(
        vault / "notes/a.md",
        "type: note\ncheck_status: checked\ntitle: A\nstatus: accepted\n",
    )
    _md(
        vault / "notes/b.md",
        "type: note\ncheck_status: checked\ntitle: B\nstatus: accepted\n",
    )
    with pytest.raises(FileNotFoundError):
        move_concept(vault, "notes/missing.md", "notes/x.md", actor="pi", machine="m")
    with pytest.raises(FileExistsError):
        move_concept(vault, "notes/a.md", "notes/b.md", actor="pi", machine="m")
    with pytest.raises(ValueError, match="bundle"):
        move_concept(vault, "notes/a.md", "hubs/a.md", actor="pi", machine="m")
    with pytest.raises(ValueError, match="notes/, hubs/, and projects/"):
        move_concept(vault, "digests/a.md", "digests/b.md", actor="pi", machine="m")


def test_move_concept_carries_every_path_keyed_row_for_a_writer_authored_concept(
    tmp_path: Path,
) -> None:
    """Drive the move through the `outputs` writer that lands a payload child.

    `outputs` has two writers. `record_observed_file_edit` — the one behind every
    `_md`/`write_checked_concept` fixture — writes the parent row and no
    `materialization_payloads` child, which is the single write shape under which
    NID-B.4's missing `ON UPDATE CASCADE` stayed invisible across 2,862 tests.
    `record_file_output`, reached through `stage_concept`, is the mainline for
    machine-authored notes and lands the child. The full table set is proven here,
    against the row shape that actually has attachments to strand.
    """
    vault = workspace(tmp_path)
    rel = "notes/writer-authored.md"
    stage_concept(
        vault,
        rel,
        "---\ntype: note\ntitle: Writer authored\ntags: []\n"
        'links:\n  supports:\n    - "notes/anchor.md"\n---\n'
        "# Writer authored\n\nrarealpha the machine-authored body.\n",
        machine="writer",
    )
    promote_checked(vault, rel, machine="writer")
    state.mark_materialized(vault, rel)
    checked_note(vault, "anchor", "Anchor", "01KBN6V6KX0000000000000020")
    linked_note(vault, "linker", "01KBN6V6KX0000000000000021", "supports", rel)
    rebuild_passage_index(vault)
    commit_notes(vault)
    before = state.output_record(vault, rel)
    assert before is not None

    moved = "notes/writer-moved.md"
    result = move_concept(vault, rel, moved, actor="pi", machine="curator")

    assert result["rewritten"] == ["notes/linker.md"]
    with state.connect(vault) as conn:
        concept = conn.execute(
            "SELECT concept_id, path FROM concepts WHERE path = ?", (moved,)
        ).fetchone()
        output = conn.execute(
            "SELECT output_id, target_path, output_sha256 FROM outputs WHERE output_id = ?",
            (moved,),
        ).fetchone()
        payloads = {
            str(row["output_id"])
            for row in conn.execute("SELECT output_id FROM materialization_payloads")
        }
        passages = {str(row["path"]) for row in conn.execute("SELECT path FROM passages")}
        indexed = {str(row["path"]) for row in conn.execute("SELECT path FROM file_index_state")}
        edges = {
            (str(row["source_path"]), str(row["relation_type"]), str(row["target_path"]))
            for row in conn.execute(
                "SELECT source_path, relation_type, target_path FROM concept_edges"
            )
        }
    # concepts.path moved; the frontmatter ULID identity did not.
    assert concept is not None
    assert concept["concept_id"] == read_frontmatter(vault / moved)["id"]
    # outputs.output_id/target_path moved, and the payload child rode the key.
    assert (output["output_id"], output["target_path"]) == (moved, moved)
    assert payloads == {moved}
    # The move never re-hashes: the bytes are identical at the new path, so the
    # sha256 barrier keeps holding without the move touching output_sha256.
    assert output["output_sha256"] == before["output_sha256"]
    assert is_consumable_checked_file(vault, moved, enqueue_scan=False)
    # passages.path and file_index_state.path moved (the latter is the row the
    # out-of-band reconcile strands, and refresh_stale_passages reads).
    assert rel not in passages and moved in passages
    assert rel not in indexed and moved in indexed
    # concept_edges moved on both sides: outbound source_path and inbound target_path.
    assert (moved, "supports", "notes/anchor.md") in edges
    assert ("notes/linker.md", "supports", moved) in edges
    assert not [edge for edge in edges if rel in edge]


def test_move_concept_rolls_back_when_an_inbound_rewrite_refuses(tmp_path: Path) -> None:
    """A partial move that commits is worse than a refusal.

    The second linker carries a retired frontmatter field, so re-signing it through
    the trusted writer refuses — after the rename and the first linker's rewrite have
    already landed. Nothing may survive that: not the rename, not the first rewrite,
    not the DB path move, not a commit. The refusal has to name the offending *file*
    too: the writer's own message carries only the field, and a move plans its
    rewrites from a vault-wide scan the PI never named a file to.
    """
    vault = workspace(tmp_path)
    target = checked_note(vault, "target", "Target", "01KBN6V6KX0000000000000030")
    first = linked_note(
        vault, "a-linker", "01KBN6V6KX0000000000000031", "supports", "notes/target.md"
    )
    doomed = linked_note(
        vault, "z-linker", "01KBN6V6KX0000000000000032", "supports", "notes/target.md"
    )
    doomed.write_text(
        doomed.read_text(encoding="utf-8").replace("type: note\n", "type: note\nstatus: draft\n"),
        encoding="utf-8",
    )
    mark_file_status(vault, "notes/z-linker.md")
    commit_notes(vault)
    head = git(vault, "rev-parse", "HEAD")
    before = {path: path.read_bytes() for path in (target, first, doomed)}

    with pytest.raises(
        ValueError,
        match=r"notes/z-linker\.md: retired frontmatter field is ignored: status",
    ):
        move_concept(
            vault, "notes/target.md", "notes/target-moved.md", actor="pi", machine="curator"
        )

    assert not (vault / "notes/target-moved.md").exists()
    assert {path: path.read_bytes() for path in before} == before
    assert git(vault, "rev-parse", "HEAD") == head
    for rel in ("notes/target.md", "notes/a-linker.md", "notes/z-linker.md"):
        assert is_consumable_checked_file(vault, rel, enqueue_scan=False), rel
    with state.connect(vault) as conn:
        paths = {str(row["path"]) for row in conn.execute("SELECT path FROM concepts")}
        outputs = {str(row["output_id"]) for row in conn.execute("SELECT output_id FROM outputs")}
    assert "notes/target-moved.md" not in paths
    assert outputs == {"notes/target.md", "notes/a-linker.md", "notes/z-linker.md"}


def test_move_concept_rekeys_a_path_keyed_concept_off_the_vacated_path(
    tmp_path: Path,
) -> None:
    """An id-less file keys by its path, so the move has to carry the key too.

    Leave the key behind and `concepts.concept_id` still reads the old path: the next
    file dropped there resolves onto the moved Concept's row and inherits the PI's
    verdict, which is exactly the identity hijack contract 10 refuses everywhere else.
    """
    vault = workspace(tmp_path)
    _md(
        vault / "notes/hand-written.md",
        "type: note\ncheck_status: checked\ntitle: Hand written\n",
    )
    commit_notes(vault)

    move_concept(
        vault, "notes/hand-written.md", "notes/hand-moved.md", actor="pi", machine="curator"
    )

    with state.connect(vault) as conn:
        rows = {
            str(row["concept_id"]): str(row["path"])
            for row in conn.execute("SELECT concept_id, path FROM concepts")
        }
    assert rows == {"notes/hand-moved.md": "notes/hand-moved.md"}

    # A new file at the vacated path is a new Concept, not the moved one's verdict.
    _md(
        vault / "notes/hand-written.md",
        "type: note\ncheck_status: unchecked\ntitle: Newcomer\n",
    )
    with state.connect(vault) as conn:
        rows = {
            str(row["concept_id"]): str(row["path"])
            for row in conn.execute("SELECT concept_id, path FROM concepts")
        }
    assert rows == {
        "notes/hand-moved.md": "notes/hand-moved.md",
        "notes/hand-written.md": "notes/hand-written.md",
    }
    assert state.concept_check_status(vault, "notes/hand-moved.md") == "checked"
    assert state.concept_check_status(vault, "notes/hand-written.md") == "unchecked"


def test_move_concept_rekeys_every_identity_keyed_row_without_a_foreign_key(
    tmp_path: Path,
) -> None:
    """`concepts.concept_id` is not the only column keyed by a path-keyed identity.

    `passages.concept_id` and `derivations.input_id` key by the same identity and
    neither declares a foreign key, so nothing carries them. Strand
    `passages.concept_id` at the vacated path and the verdict-cascade triggers
    (`WHERE concept_id = NEW.concept_id`) hand the *moved* note's passages to
    whatever file lands there next, while `concept_check_status` still reads
    `checked` — the layers disagree, and only a full `rebuild_passage_index` heals
    it, never `refresh_stale_passages`.
    """
    vault = workspace(tmp_path)
    _md(
        vault / "notes/hand-written.md",
        "type: note\ncheck_status: checked\ntitle: Hand written\n",
    )
    # A path-keyed note used as a derivation input: the one live writer of
    # `derivations.input_id` at a path rather than a ULID.
    stage_concept(
        vault,
        "notes/derived.md",
        "---\ntype: note\ntitle: Derived\ntags: []\nlinks: {}\n---\n# Derived\n\nDerived body.\n",
        inputs=["notes/hand-written.md"],
        machine="writer",
    )
    rebuild_passage_index(vault)
    commit_notes(vault)

    move_concept(
        vault, "notes/hand-written.md", "notes/hand-moved.md", actor="pi", machine="curator"
    )

    with state.connect(vault) as conn:
        passages = {
            (str(row["concept_id"]), str(row["path"]), str(row["check_status"]))
            for row in conn.execute("SELECT concept_id, path, check_status FROM passages")
        }
        inputs = {str(row["input_id"]) for row in conn.execute("SELECT input_id FROM derivations")}
    assert ("notes/hand-moved.md", "notes/hand-moved.md", "checked") in passages
    assert not [row for row in passages if "notes/hand-written.md" in row]
    assert inputs == {"notes/hand-moved.md"}

    # The vacated path is now a different Concept. Its verdict must not reach the
    # moved note's passages.
    _md(
        vault / "notes/hand-written.md",
        "type: note\ncheck_status: unchecked\ntitle: Newcomer\n",
    )
    with state.connect(vault) as conn:
        moved_status = {
            str(row["check_status"])
            for row in conn.execute(
                "SELECT check_status FROM passages WHERE path = 'notes/hand-moved.md'"
            )
        }
    assert moved_status == {"checked"}
    assert state.concept_check_status(vault, "notes/hand-moved.md") == "checked"


def test_move_concept_does_not_re_sign_a_drifted_checked_linker(tmp_path: Path) -> None:
    """A `checked` verdict is not the trust gate; `is_consumable_checked_file` is.

    A linker whose bytes changed out of band still holds a `checked` verdict while
    the sha256 read barrier already refuses it. `mark_checked` re-validates the
    schema and nothing about the content — unlike `promote_checked`, it has no
    content-integrity check — so gating the re-sign on the raw verdict launders the
    out-of-band edit straight back into consumption. `curate_note_link` re-signs one
    file the PI named; a move re-signs every linker a vault-wide scan finds, on an
    action having nothing to do with them.
    """
    vault = workspace(tmp_path)
    checked_note(vault, "target", "Target", "01KBN6V6KX0000000000000040")
    drifted = linked_note(
        vault, "drifted-linker", "01KBN6V6KX0000000000000041", "supports", "notes/target.md"
    )
    linked_note(vault, "clean-linker", "01KBN6V6KX0000000000000042", "supports", "notes/target.md")
    # Out-of-band edit: the bytes change, the recorded hash does not.
    drifted.write_text(
        drifted.read_text(encoding="utf-8") + "\nSmuggled body text.\n", encoding="utf-8"
    )
    commit_notes(vault)
    assert state.concept_check_status(vault, "notes/drifted-linker.md") == "checked"
    assert not is_consumable_checked_file(vault, "notes/drifted-linker.md", enqueue_scan=False)

    result = move_concept(
        vault, "notes/target.md", "notes/target-moved.md", actor="pi", machine="curator"
    )

    # The move proceeds and rewrites both linkers...
    assert result["rewritten"] == ["notes/clean-linker.md", "notes/drifted-linker.md"]
    assert read_frontmatter(drifted)["links"]["supports"] == ["notes/target-moved.md"]
    # ...but the drifted one stays exactly as unconsumable as it already was, with
    # the smuggled text still sitting in it unsigned.
    assert "Smuggled body text." in drifted.read_text(encoding="utf-8")
    assert not is_consumable_checked_file(vault, "notes/drifted-linker.md", enqueue_scan=False)
    # A linker that really is checked is still re-signed, so the move demotes nothing.
    assert is_consumable_checked_file(vault, "notes/clean-linker.md", enqueue_scan=False)
