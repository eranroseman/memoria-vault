"""The consequence mark writer and the engine that drives it (EDGES section 5)."""

from __future__ import annotations

from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.jsonl import iter_jsonl
from memoria_vault.runtime.policy.audit import EMPTY_SHA256, sha256_file
from memoria_vault.runtime.propagation import (
    _target_aliases,
    active_project_slices,
    compute_consequences,
    mark_consequence,
    propagate_consequences,
    propagate_consequences_explicit,
    propagate_edge_change,
    route_consequence_cards,
)
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.helpers import call_with_context, git, write_note
from tests.helpers import worker_workspace as workspace

pytestmark = pytest.mark.runtime


def _work(vault: Path, work_id: str, **kwargs: str) -> None:
    """Seed the catalog work whose Concept parent every FK-backed mark needs.

    `set_concept_consequence` and `set_concept_flag` both carry an FK onto
    `concepts`, so a virtual `catalog/sources/<id>` target with no catalog row
    is refused before the mark writer's own rules are reached.
    """
    state.upsert_catalog_record(vault, work_id=work_id, title=f"Work {work_id}", **kwargs)


def test_mark_consequence_labels_file_and_mirrors_db(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    write_note(vault, "claim", "checked", "A claim body.")
    _work(vault, "w1")
    events: list[dict] = []

    result = mark_consequence(
        vault,
        "notes/claim.md",
        consequence="grounds-lost",
        trigger_id="catalog/sources/w1",
        reason="work w1 retracted",
        append_event=events.append,
    )

    frontmatter = read_frontmatter(vault / "notes/claim.md")
    assert frontmatter["stale"] is True
    assert frontmatter["consequence"] == "grounds-lost"
    assert state.concept_consequence(vault, "notes/claim.md") == "grounds-lost"
    assert state.concept_flags(vault, "notes/claim.md")["stale"] == {
        "reason": "work w1 retracted",
        "trigger_id": "catalog/sources/w1",
        "created_at": state.concept_flags(vault, "notes/claim.md")["stale"]["created_at"],
    }
    assert result == {
        "concept_id": "notes/claim.md",
        "consequence": "grounds-lost",
        "changed": True,
        "path": "notes/claim.md",
    }
    # Every cell of the event, not the three a summary would keep: the whole row
    # is what `rebuild_trace_state` folds, and a dropped `output_sha256` is what
    # makes the next scan read this mark as a foreign edit.
    [event] = events
    assert event == {
        "event": "check-fired",
        "check": "typed-consequence",
        "status": "failed",
        "reason": "work w1 retracted",
        "consequence": "grounds-lost",
        "target_id": "notes/claim.md",
        "target_sha256": sha256_file(vault / "notes/claim.md"),
        "output_sha256": sha256_file(vault / "notes/claim.md"),
        "trigger_id": "catalog/sources/w1",
        "shadow": False,
        "route": "log",
    }


def test_mark_consequence_re_marking_is_idempotent(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    write_note(vault, "claim", "checked", "A claim body.")
    _work(vault, "w1")
    events: list[dict] = []
    mark_consequence(
        vault,
        "notes/claim.md",
        consequence="grounds-lost",
        trigger_id="catalog/sources/w1",
        reason="work w1 retracted",
        append_event=events.append,
    )
    before = sha256_file(vault / "notes/claim.md")

    again = mark_consequence(
        vault,
        "notes/claim.md",
        consequence="grounds-lost",
        trigger_id="catalog/sources/w1",
        reason="work w1 retracted",
        append_event=events.append,
    )

    assert again == {
        "concept_id": "notes/claim.md",
        "consequence": "grounds-lost",
        "changed": False,
        "path": "",
    }
    assert len(events) == 1
    assert sha256_file(vault / "notes/claim.md") == before


def test_mark_consequence_of_a_second_type_relabels_the_file(tmp_path: Path) -> None:
    """Same file, different consequence: the label is rewritten, not left stale-only."""
    vault = workspace(tmp_path)
    write_note(vault, "claim", "checked", "A claim body.")
    _work(vault, "w1")
    events: list[dict] = []
    mark_consequence(
        vault,
        "notes/claim.md",
        consequence="grounds-lost",
        trigger_id="catalog/sources/w1",
        reason="work w1 retracted",
        append_event=events.append,
    )

    again = mark_consequence(
        vault,
        "notes/claim.md",
        consequence="warrant-lost",
        trigger_id="notes/license.md",
        reason="license note changed",
        append_event=events.append,
    )

    assert again["changed"] is True and again["path"] == "notes/claim.md"
    assert read_frontmatter(vault / "notes/claim.md")["consequence"] == "warrant-lost"
    assert state.concept_consequence(vault, "notes/claim.md") == "warrant-lost"
    assert state.concept_flags(vault, "notes/claim.md")["stale"]["trigger_id"] == "notes/license.md"
    assert len(events) == 2


def test_mark_consequence_labels_a_file_already_stale_without_a_type(tmp_path: Path) -> None:
    """A `stale: true` from the shipped scan carries no type -- this is not a re-mark."""
    vault = workspace(tmp_path)
    path = write_note(vault, "claim", "checked", "A claim body.")
    path.write_text(
        path.read_text(encoding="utf-8").replace("type: note\n", "type: note\nstale: true\n"),
        encoding="utf-8",
    )
    _work(vault, "w1")
    events: list[dict] = []

    result = mark_consequence(
        vault,
        "notes/claim.md",
        consequence="grounds-lost",
        trigger_id="catalog/sources/w1",
        reason="work w1 retracted",
        append_event=events.append,
    )

    assert result["changed"] is True
    assert read_frontmatter(vault / "notes/claim.md")["consequence"] == "grounds-lost"
    assert len(events) == 1


def test_mark_consequence_re_labels_a_file_the_pi_half_cleared(tmp_path: Path) -> None:
    """...and the other half of that conjunction: `consequence:` kept, `stale:` gone."""
    vault = workspace(tmp_path)
    path = write_note(vault, "claim", "checked", "A claim body.")
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "type: note\n", "type: note\nconsequence: grounds-lost\n"
        ),
        encoding="utf-8",
    )
    _work(vault, "w1")
    events: list[dict] = []

    result = mark_consequence(
        vault,
        "notes/claim.md",
        consequence="grounds-lost",
        trigger_id="catalog/sources/w1",
        reason="work w1 retracted",
        append_event=events.append,
    )

    assert result["changed"] is True
    assert read_frontmatter(vault / "notes/claim.md")["stale"] is True
    assert len(events) == 1


def test_mark_consequence_normalizes_both_of_its_path_arguments(tmp_path: Path) -> None:
    """Caller-supplied ids are raw: an operation payload names whatever it names."""
    vault = workspace(tmp_path)
    write_note(vault, "claim", "checked", "A claim body.")
    _work(vault, "w1")
    events: list[dict] = []

    result = mark_consequence(
        vault,
        "./notes/claim.md",
        consequence="grounds-lost",
        trigger_id="/catalog/sources/w1",
        reason="work w1 retracted",
        append_event=events.append,
    )

    assert result["concept_id"] == "notes/claim.md"
    assert result["path"] == "notes/claim.md"
    [event] = events
    assert event["target_id"] == "notes/claim.md"
    assert event["trigger_id"] == "catalog/sources/w1"


def test_mark_consequence_of_a_mirrored_note_whose_file_is_gone_is_db_only(
    tmp_path: Path,
) -> None:
    """A verdict-bearing Concept survives its file (`rebuild_file_concept_mirror`)."""
    vault = workspace(tmp_path)
    write_note(vault, "claim", "checked", "A claim body.")
    _work(vault, "w1")
    (vault / "notes/claim.md").unlink()

    result = mark_consequence(
        vault,
        "notes/claim.md",
        consequence="grounds-lost",
        trigger_id="catalog/sources/w1",
        reason="work w1 retracted",
        append_event=lambda event: event,
    )

    assert result["changed"] is True and result["path"] == ""
    assert state.concept_consequence(vault, "notes/claim.md") == "grounds-lost"


def test_mark_consequence_never_writes_frontmatter_into_a_non_markdown_file(
    tmp_path: Path,
) -> None:
    """`split_frontmatter` is total: on plain text it returns the whole file as body.

    A Concept whose store is a file but whose file is not Markdown would come
    back from a label pass with a YAML header prepended to its contents.
    """
    vault = workspace(tmp_path)
    artifact = vault / "fulltext/w1.txt"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("Plain extracted text.\n", encoding="utf-8")
    state.rebuild_file_concept_mirror(
        vault,
        [{"concept_id": "fulltext/w1.txt", "concept_type": "note", "path": "fulltext/w1.txt"}],
    )

    result = mark_consequence(
        vault,
        "fulltext/w1.txt",
        consequence="grounds-lost",
        trigger_id="catalog/sources/w1",
        reason="work w1 retracted",
        append_event=lambda event: event,
    )

    assert result["changed"] is True and result["path"] == ""
    assert artifact.read_text(encoding="utf-8") == "Plain extracted text.\n"
    assert state.concept_consequence(vault, "fulltext/w1.txt") == "grounds-lost"


def test_mark_consequence_db_only_for_virtual_targets(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _work(vault, "w1")
    _work(vault, "w2")
    events: list[dict] = []

    result = mark_consequence(
        vault,
        "catalog/sources/w2",
        consequence="grounds-lost",
        trigger_id="catalog/sources/w1",
        reason="work w1 retracted",
        append_event=events.append,
    )

    assert result == {
        "concept_id": "catalog/sources/w2",
        "consequence": "grounds-lost",
        "changed": True,
        "path": "",
    }
    assert state.concept_consequence(vault, "catalog/sources/w2") == "grounds-lost"
    assert "stale" in state.concept_flags(vault, "catalog/sources/w2")
    # A virtual target has no bytes to hash; the event still carries the pair.
    [event] = events
    assert event["target_sha256"] == EMPTY_SHA256
    assert event["output_sha256"] == EMPTY_SHA256
    assert not (vault / "catalog/sources/w2").exists()


def test_mark_consequence_re_marking_a_virtual_target_is_idempotent(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _work(vault, "w1")
    _work(vault, "w2")
    events: list[dict] = []
    for _ in range(2):
        result = mark_consequence(
            vault,
            "catalog/sources/w2",
            consequence="grounds-lost",
            trigger_id="catalog/sources/w1",
            reason="work w1 retracted",
            append_event=events.append,
        )

    assert result == {
        "concept_id": "catalog/sources/w2",
        "consequence": "grounds-lost",
        "changed": False,
        "path": "",
    }
    assert len(events) == 1


def test_mark_consequence_of_a_second_type_remirrors_a_virtual_target(tmp_path: Path) -> None:
    """The DB-only re-mark test is a conjunction; this is its consequence half."""
    vault = workspace(tmp_path)
    _work(vault, "w1")
    _work(vault, "w2")
    events: list[dict] = []
    mark_consequence(
        vault,
        "catalog/sources/w2",
        consequence="grounds-lost",
        trigger_id="catalog/sources/w1",
        reason="work w1 retracted",
        append_event=events.append,
    )

    again = mark_consequence(
        vault,
        "catalog/sources/w2",
        consequence="qualifier-regression",
        trigger_id="catalog/sources/w1",
        reason="work w1 bounded",
        append_event=events.append,
    )

    assert again["changed"] is True
    assert state.concept_consequence(vault, "catalog/sources/w2") == "qualifier-regression"
    assert len(events) == 2


def test_mark_consequence_re_flags_a_virtual_target_whose_compat_flag_is_gone(
    tmp_path: Path,
) -> None:
    """...and its flag half: the mirror and the shipped compat row are two writes."""
    vault = workspace(tmp_path)
    _work(vault, "w1")
    _work(vault, "w2")
    events: list[dict] = []
    mark_consequence(
        vault,
        "catalog/sources/w2",
        consequence="grounds-lost",
        trigger_id="catalog/sources/w1",
        reason="work w1 retracted",
        append_event=events.append,
    )
    with state.connect(vault) as conn:
        conn.execute("DELETE FROM concept_flags")
    assert state.concept_flags(vault, "catalog/sources/w2") == {}

    again = mark_consequence(
        vault,
        "catalog/sources/w2",
        consequence="grounds-lost",
        trigger_id="catalog/sources/w1",
        reason="work w1 retracted",
        append_event=events.append,
    )

    assert again["changed"] is True
    assert "stale" in state.concept_flags(vault, "catalog/sources/w2")
    assert len(events) == 2


def test_mark_consequence_skips_a_concept_the_mirror_does_not_hold(tmp_path: Path) -> None:
    """A pending edge's target is a legal graph node with no `concepts` row.

    Every FK-backed writer refuses it, so the mark writer has to answer before it
    writes: one dangling forward link must not abort a whole propagation run.
    """
    vault = workspace(tmp_path)
    events: list[dict] = []

    result = mark_consequence(
        vault,
        "notes/never-written.md",
        consequence="grounds-lost",
        trigger_id="catalog/sources/w1",
        reason="work w1 retracted",
        append_event=events.append,
    )

    assert result == {
        "concept_id": "notes/never-written.md",
        "consequence": "grounds-lost",
        "changed": False,
        "path": "",
    }
    assert events == []
    assert state.concept_consequence(vault, "notes/never-written.md") == ""
    assert state.concept_flags(vault, "notes/never-written.md") == {}
    assert not (vault / "notes/never-written.md").exists()


def test_mark_consequence_rejects_a_consequence_outside_the_roster(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    write_note(vault, "claim", "checked", "A claim body.")

    with pytest.raises(ValueError, match="unknown consequence type"):
        mark_consequence(
            vault,
            "notes/claim.md",
            consequence="grounds-shaken",
            trigger_id="catalog/sources/w1",
            reason="not a spec type",
            append_event=lambda event: event,
        )

    assert read_frontmatter(vault / "notes/claim.md").get("stale") is None


def test_mark_consequence_refreshes_pi_file_baseline(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    write_note(vault, "claim", "checked", "A claim body.")
    stale_sha = sha256_file(vault / "notes/claim.md")
    state.upsert_file_baseline(
        vault,
        "notes/claim.md",
        human_sha256=stale_sha,
        restriction_keys=["quote"],
    )

    mark_consequence(
        vault,
        "notes/claim.md",
        consequence="qualifier-regression",
        trigger_id="notes/bound.md",
        reason="bounding note changed",
        append_event=lambda event: event,
    )

    baseline = state.file_baseline(vault, "notes/claim.md")
    assert baseline["human_sha256"] == sha256_file(vault / "notes/claim.md")
    assert baseline["human_sha256"] != stale_sha
    assert baseline["restriction_keys"] == ["quote"]


def test_marking_a_checked_note_leaves_it_consumable_as_checked(tmp_path: Path) -> None:
    """A label is not a verdict: the mark moves bytes the PI did check.

    `outputs.output_sha256` is the hash the read barrier compares the file
    against, so a mark that leaves it behind makes the writer's own write read
    as a foreign edit — every later reader refuses the note and enqueues a scan
    for it, and the scan demotes it and cascades another propagation.
    """
    from memoria_vault.runtime.read_barrier import is_consumable_checked_file

    vault = workspace(tmp_path)
    write_note(vault, "claim", "checked", "A claim body.")
    _work(vault, "w1")
    assert is_consumable_checked_file(vault, "notes/claim.md", enqueue_scan=False)

    mark_consequence(
        vault,
        "notes/claim.md",
        consequence="grounds-lost",
        trigger_id="catalog/sources/w1",
        reason="work w1 retracted",
        append_event=lambda event: event,
    )

    assert is_consumable_checked_file(vault, "notes/claim.md", enqueue_scan=False)
    assert state.concept_check_status(vault, "notes/claim.md") == "checked"


def test_mark_consequence_does_not_mint_a_baseline_the_pi_never_had(tmp_path: Path) -> None:
    """Only a file the PI already baselined gets its baseline moved forward."""
    vault = workspace(tmp_path)
    write_note(vault, "claim", "checked", "A claim body.")
    assert state.file_baseline(vault, "notes/claim.md") is None

    mark_consequence(
        vault,
        "notes/claim.md",
        consequence="qualifier-regression",
        trigger_id="notes/bound.md",
        reason="bounding note changed",
        append_event=lambda event: event,
    )

    assert state.file_baseline(vault, "notes/claim.md") is None


def test_target_aliases_expand_a_catalog_work_to_its_renderings(tmp_path: Path) -> None:
    """The bare `work_id` is the dangerous member: `normalize_path` returns it unchanged."""
    vault = workspace(tmp_path)
    _work(vault, "settles-2016", concept_path="catalog/sources/settles-2016/source.md")

    assert _target_aliases(vault, "catalog/sources/settles-2016") == {
        "catalog/sources/settles-2016",
        "catalog/sources/settles-2016/source.md",
    }
    assert _target_aliases(vault, "settles-2016") == {
        "settles-2016",
        "catalog/sources/settles-2016",
        "catalog/sources/settles-2016/source.md",
    }


def test_target_aliases_of_a_reference_no_catalog_row_claims_are_itself(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    write_note(vault, "claim", "checked", "A claim body.")

    assert _target_aliases(vault, "notes/claim.md") == {"notes/claim.md"}


# --- ERP-C.5: engine orchestration + trigger seams -------------------------


def _edge_row(source: str, relation: str, target: str) -> dict[str, str]:
    return {
        "source_concept_id": source,
        "source_path": source,
        "relation_type": relation,
        "target_path": target,
        "check_status": "checked",
    }


def _seed_retraction_graph(vault: Path) -> None:
    """One work, one evidence hop, then two edge hops of two different types.

    Two consequence types, not one: a same-type closure cannot tell a walk that
    types every hop from one that types the first and copies it outward, and the
    typed count is exactly what ERP-D.1's report card is.
    """
    _work(vault, "settles-2016")
    for name in ("c1", "c2", "thesis"):
        write_note(vault, name, "checked", f"Body of {name}.")
    state.replace_evidence_sets(
        vault,
        [
            {
                "id": "ev-22222222",
                "block_ref": "notes/c1.md#^blk-22222222",
                "items": ["settles-2016#^p0001"],
                "type": "single-span",
                "state": "complete",
                "review_required": False,
                "bind": False,
            }
        ],
    )
    state.replace_concept_edges(
        vault,
        [
            _edge_row("notes/c1.md", "supports", "notes/c2.md"),
            _edge_row("notes/c2.md", "qualifier", "notes/thesis.md"),
        ],
    )


# The blast radius of retracting `settles-2016`, every cell the closure decides:
# which node, which type, which hop carried it, and how far out it is. ERP-D.1
# counts the second column; the third and fourth are what distinguish this walk
# from one that reached the same set by another route.
_RETRACTION_CLOSURE = {
    "notes/c1.md": {"consequence": "grounds-lost", "via": "evidence", "depth": 1},
    "notes/c2.md": {"consequence": "grounds-lost", "via": "supports", "depth": 2},
    "notes/thesis.md": {"consequence": "qualifier-regression", "via": "qualifier", "depth": 3},
}


def test_compute_consequences_reports_the_blast_radius_and_writes_nothing(
    tmp_path: Path,
) -> None:
    """ERP-D.1's report input: the typed closure, before any label exists."""
    vault = workspace(tmp_path)
    _seed_retraction_graph(vault)

    marked = compute_consequences(vault, "catalog/sources/settles-2016", trigger="standing-changed")

    assert marked == _RETRACTION_CLOSURE
    for rel in marked:
        assert read_frontmatter(vault / rel).get("stale") is None
        assert state.concept_consequence(vault, rel) == ""


def test_compute_consequences_expands_a_bare_work_id_to_its_rendered_start(
    tmp_path: Path,
) -> None:
    """`normalize_path("settles-2016")` returns it unchanged, so the alias pass is load-bearing.

    Without `_target_aliases` the bare identity is a plausible node the path-space
    graph does not contain, and the walk fails closed and silent.
    """
    vault = workspace(tmp_path)
    _seed_retraction_graph(vault)

    assert compute_consequences(vault, "settles-2016", trigger="standing-changed") == (
        _RETRACTION_CLOSURE
    )


def test_compute_consequences_types_nothing_when_every_seed_hop_is_quiet(
    tmp_path: Path,
) -> None:
    """`edge-added` is a grounds *gain* through supports: same graph, empty answer."""
    vault = workspace(tmp_path)
    _seed_retraction_graph(vault)

    assert compute_consequences(vault, "notes/c1.md", trigger="edge-added") == {}
    assert compute_consequences(vault, "notes/c1.md", trigger="claim-changed") == {
        "notes/c2.md": {"consequence": "grounds-lost", "via": "supports", "depth": 1},
        "notes/thesis.md": {"consequence": "qualifier-regression", "via": "qualifier", "depth": 2},
    }


def test_retraction_sweep_labels_every_reached_claim_and_commits_them(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _seed_retraction_graph(vault)

    result = propagate_consequences_explicit(
        vault,
        "catalog/sources/settles-2016",
        trigger="standing-changed",
        reason="work settles-2016 retracted",
        actor="integrity",
        machine="test-machine",
    )

    assert result["target_id"] == "catalog/sources/settles-2016"
    assert result["trigger"] == "standing-changed"
    assert result["marked"] == {
        rel: mark["consequence"] for rel, mark in _RETRACTION_CLOSURE.items()
    }
    for rel, mark in _RETRACTION_CLOSURE.items():
        frontmatter = read_frontmatter(vault / rel)
        assert frontmatter["stale"] is True
        assert frontmatter["consequence"] == mark["consequence"]
        assert state.concept_consequence(vault, rel) == mark["consequence"]
        assert state.concept_flags(vault, rel)["stale"]["trigger_id"] == (
            "catalog/sources/settles-2016"
        )
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, *_RETRACTION_CLOSURE}
    # One run writes one journal event per mark, in the order the run applied
    # them. `marked` is keyed in discovery order, so the sort is what keeps the
    # hash-chained journal a function of the closure and not of the walk.
    journal = [
        row
        for row in iter_jsonl(vault / ".memoria/journal/test-machine.jsonl")
        if row.get("check") == "typed-consequence"
    ]
    assert [row["target_id"] for row in journal] == sorted(_RETRACTION_CLOSURE)
    # Quiet tier (ERP-C.6): this vault holds no project, so nothing the sweep
    # marked lands in an active slice and the whole run is labels plus journal.
    assert result["cards"] == []


def test_re_running_a_sweep_re_decides_the_same_closure_and_writes_nothing(
    tmp_path: Path,
) -> None:
    """Idempotence is about the writes, not the answer: the closure is unconditional."""
    vault = workspace(tmp_path)
    _seed_retraction_graph(vault)
    arguments = {
        "trigger": "standing-changed",
        "reason": "work settles-2016 retracted",
        "actor": "integrity",
        "machine": "test-machine",
    }
    first = propagate_consequences_explicit(vault, "catalog/sources/settles-2016", **arguments)
    head = git(vault, "rev-parse", "HEAD")

    again = propagate_consequences_explicit(vault, "catalog/sources/settles-2016", **arguments)

    assert again["marked"] == first["marked"]
    assert again["commit"] == ""
    assert git(vault, "rev-parse", "HEAD") == head


def test_a_sweep_survives_a_dependent_the_mirror_never_saw(tmp_path: Path) -> None:
    """A forward link to an unwritten note is legal, and it is still in the closure."""
    vault = workspace(tmp_path)
    write_note(vault, "c1", "checked", "Body of c1.")
    state.replace_concept_edges(vault, [_edge_row("notes/c1.md", "supports", "notes/unwritten.md")])

    result = propagate_consequences_explicit(
        vault,
        "notes/c1.md",
        trigger="claim-retracted",
        reason="claim c1 retracted",
        actor="integrity",
        machine="test-machine",
    )

    assert result["marked"] == {"notes/unwritten.md": "grounds-lost"}
    assert result["commit"] == ""
    assert state.concept_consequence(vault, "notes/unwritten.md") == ""


def test_propagate_consequences_inside_an_envelope_marks_and_commits(tmp_path: Path) -> None:
    """The context wrapper is a second call path, not a rename of the explicit one."""
    vault = workspace(tmp_path)
    _seed_retraction_graph(vault)

    result = call_with_context(
        propagate_consequences,
        vault,
        "catalog/sources/settles-2016",
        trigger="standing-changed",
        reason="work settles-2016 retracted",
    )

    assert result["marked"] == {
        rel: mark["consequence"] for rel, mark in _RETRACTION_CLOSURE.items()
    }
    assert result["commit"]
    assert read_frontmatter(vault / "notes/thesis.md")["consequence"] == "qualifier-regression"


def test_edge_added_on_rebuttal_seeds_the_target_and_expands_transitively(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    _seed_retraction_graph(vault)

    result = call_with_context(
        propagate_edge_change,
        vault,
        source="notes/rebuttal.md",
        relation_type="rebuttal",
        target="notes/c1.md",
        added=True,
        reason="PI recorded a rebuttal",
    )

    assert result["target_id"] == "notes/c1.md"
    assert result["trigger"] == "edge-added"
    # The seed's own type comes from the decision table's seed row; everything
    # past it is an ordinary transitive hop.
    assert result["marked"] == {
        "notes/c1.md": "rebuttal-strengthened",
        "notes/c2.md": "grounds-lost",
        "notes/thesis.md": "qualifier-regression",
    }
    assert read_frontmatter(vault / "notes/c1.md")["consequence"] == "rebuttal-strengthened"


def test_edge_change_on_extends_seeds_the_source_not_the_target(tmp_path: Path) -> None:
    """`extends` is the one relation whose dependent is the source end."""
    vault = workspace(tmp_path)
    _seed_retraction_graph(vault)

    result = call_with_context(
        propagate_edge_change,
        vault,
        source="notes/c1.md",
        relation_type="extends",
        target="notes/base.md",
        added=False,
        reason="PI retracted an extends link",
    )

    assert result["trigger"] == "edge-removed"
    assert result["target_id"] == "notes/c1.md"
    assert result["marked"] == {
        "notes/c1.md": "grounds-lost",
        "notes/c2.md": "grounds-lost",
        "notes/thesis.md": "qualifier-regression",
    }


def test_edge_change_whose_seed_hop_types_nothing_writes_nothing(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _seed_retraction_graph(vault)

    result = call_with_context(
        propagate_edge_change,
        vault,
        source="notes/c1.md",
        relation_type="supports",
        target="notes/c2.md",
        added=True,
        reason="PI linked claims",
    )

    assert result == {
        "target_id": "notes/c2.md",
        "trigger": "edge-added",
        "marked": {},
        "cards": [],
        "commit": "",
    }
    assert read_frontmatter(vault / "notes/c2.md").get("stale") is None


def test_scan_demotion_wrappers_attach_grounding_consequences(tmp_path: Path) -> None:
    from memoria_vault.runtime.grounding import (
        propagate_scan_demotion,
        propagate_scan_demotion_explicit,
    )

    vault = workspace(tmp_path)
    write_note(vault, "edited", "checked", "Edited claim.")
    write_note(vault, "dependent", "checked", "Dependent claim.")
    state.replace_concept_edges(
        vault, [_edge_row("notes/edited.md", "supports", "notes/dependent.md")]
    )

    result = propagate_scan_demotion_explicit(
        vault,
        "notes/edited.md",
        reason="scan observed unchecked edit: notes/edited.md",
        actor="integrity",
        machine="test-machine",
    )

    assert result["consequences"]["trigger"] == "claim-changed"
    assert result["consequences"]["marked"] == {"notes/dependent.md": "grounds-lost"}
    assert read_frontmatter(vault / "notes/dependent.md")["stale"] is True
    # The shipped demotion result is preserved, not replaced.
    assert result["target_id"] == "notes/edited.md"
    assert result["demoted"] == []

    write_note(vault, "second", "checked", "Second dependent.")
    state.replace_concept_edges(
        vault,
        [
            _edge_row("notes/edited.md", "supports", "notes/dependent.md"),
            _edge_row("notes/edited.md", "warrant", "notes/second.md"),
        ],
    )
    inside = call_with_context(
        propagate_scan_demotion,
        vault,
        "notes/edited.md",
        reason="scan observed unchecked edit: notes/edited.md",
    )

    assert inside["consequences"]["trigger"] == "claim-changed"
    assert inside["consequences"]["marked"] == {
        "notes/dependent.md": "grounds-lost",
        "notes/second.md": "warrant-lost",
    }
    assert read_frontmatter(vault / "notes/second.md")["consequence"] == "warrant-lost"


# --- ERP-C.6: active-project slices + loudness routing ---------------------
#
# Both functions answer in **path space** — the space `marked` is keyed in and
# the space `edges.concept_edge_path_pairs` publishes. The fixtures below keep
# that distinguishable from identity space on purpose: `_N1_ULID` is a file
# Concept whose `concepts.path` is not its id, and `notes/pending.md` is a
# target the mirror has never resolved, so `concept_edges.target_concept_id` is
# NULL for it. An adjacency built from those two columns instead would drop the
# first member and give every pending edge in the vault the same blank node to
# join through.
_N1_ULID = "01JXAAAAAAAAAAAAAAAAAAAAA1"


def _project(vault: Path, slug: str, *, thesis: str, archived: bool = False) -> str:
    """Write one `type: project` file; return its vault-relative path."""
    rel = f"projects/{slug}.md"
    path = vault / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    shelved = "archived: true\n" if archived else ""
    path.write_text(
        f"---\ntype: project\ntitle: {slug}\ntags: []\nlinks: {{}}\n"
        f"thesis: {thesis}\n{shelved}---\nBody.\n",
        encoding="utf-8",
    )
    return rel


def _slice_rows() -> list[dict[str, str]]:
    """The thesis neighbourhood: one ULID-keyed source, one unresolved target.

    The second row is deliberately **unchecked**. A project's slice is its
    topology, not its verified topology: an edge the PI has not confirmed still
    says which work the cascade would reach, and the loudness question is where
    the blast lands, not whether the graph is settled.
    """
    return [
        {
            "source_concept_id": _N1_ULID,
            "source_path": "notes/n1.md",
            "relation_type": "supports",
            "target_path": "notes/thesis.md",
            "check_status": "checked",
        },
        {
            **_edge_row("notes/thesis.md", "supports", "notes/pending.md"),
            "check_status": "unchecked",
        },
    ]


def _seed_active_project(vault: Path) -> str:
    """One active project over a thesis reached undirected from both sides."""
    write_note(vault, "thesis", "checked", "Thesis body.")
    (vault / "notes/n1.md").write_text(
        "---\ntype: note\ntitle: n1\ntags: []\nlinks: {}\n---\nBody of n1.\n", encoding="utf-8"
    )
    # A verdict-bearing row survives this rebuild's prune, so the thesis keeps
    # its own path-keyed identity while `n1` takes a ULID.
    state.rebuild_file_concept_mirror(
        vault, [{"concept_id": _N1_ULID, "concept_type": "note", "path": "notes/n1.md"}]
    )
    state.replace_concept_edges(vault, _slice_rows())
    return _project(vault, "thesis-a", thesis="notes/thesis.md")


def _seed_second_project(vault: Path) -> str:
    """A second active project whose slice shares nothing with the first.

    Its home is the nested `projects/<slug>/project.md` shape, and its slug
    sorts *before* the flat project's while `iter_markdown` yields it *after* —
    a directory walk hands back a directory's own files ahead of its subtrees.
    So the two orders disagree here, which is what makes the router's project
    order observable at all.
    """
    write_note(vault, "thesis-b", "checked", "Second thesis body.")
    state.replace_concept_edges(
        vault,
        [*_slice_rows(), _edge_row("notes/thesis-b.md", "supports", "notes/pending-b.md")],
    )
    return _project(vault, "a-nested/project", thesis="notes/thesis-b.md")


def test_active_project_slice_reaches_the_thesis_neighbourhood_in_path_space(
    tmp_path: Path,
) -> None:
    """Exact membership, both directions, and neither endpoint read as an identity."""
    vault = workspace(tmp_path)
    project_rel = _seed_active_project(vault)

    assert active_project_slices(vault) == {
        project_rel: {project_rel, "notes/thesis.md", "notes/n1.md", "notes/pending.md"}
    }


def test_two_active_projects_slice_separately(tmp_path: Path) -> None:
    """One entry each, and an unresolved target on both sides does not fuse them."""
    vault = workspace(tmp_path)
    first = _seed_active_project(vault)
    second = _seed_second_project(vault)

    slices = active_project_slices(vault)

    assert set(slices) == {first, second}
    assert slices[first] == {first, "notes/thesis.md", "notes/n1.md", "notes/pending.md"}
    assert slices[second] == {second, "notes/thesis-b.md", "notes/pending-b.md"}


def test_an_archived_project_is_not_an_active_slice(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    _seed_active_project(vault)
    _project(vault, "thesis-a", thesis="notes/thesis.md", archived=True)

    assert active_project_slices(vault) == {}


def test_a_thesis_that_is_not_path_space_seeds_nothing(tmp_path: Path) -> None:
    """`thesis:` has one normalizer and it is `edges.thesis_rel` (issue #1623).

    A title is alias space: completing it here by hand would mint
    `notes/Toulmin: the warrant.md`, a node no graph contains, and the project
    would slice to a neighbourhood of one either way — silently, and for the
    wrong reason.
    """
    vault = workspace(tmp_path)
    _seed_active_project(vault)
    titled = _project(vault, "titled", thesis="'Toulmin: the warrant'")

    assert active_project_slices(vault)[titled] == {titled}


def test_a_flood_of_marks_routes_one_alert_card_for_the_project_it_touched(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    project_rel = _seed_active_project(vault)
    marked = {
        "notes/n1.md": "grounds-lost",
        "notes/pending.md": "grounds-lost",
        "notes/thesis.md": "warrant-lost",
    }
    marked.update({f"notes/off-slice-{index}.md": "grounds-lost" for index in range(5)})

    cards = route_consequence_cards(
        vault, marked, trigger_id="catalog/sources/w1", reason="work w1 retracted"
    )

    assert len(cards) == 1
    frontmatter = read_frontmatter(vault / cards[0])
    assert frontmatter["loudness"] == "alert"
    assert frontmatter["attention_kind"] == "flag"
    assert frontmatter["target"] == project_rel
    # Counted over the slice, not over the flood: eight marks, three of them here,
    # and the whole sentence, because the counts are the deliverable.
    assert frontmatter["finding"] == (
        "3 concept(s) in this project's slice were marked stale "
        "(grounds-lost: 2, warrant-lost: 1) after: work w1 retracted"
    )
    assert "off-slice" not in (vault / cards[0]).read_text(encoding="utf-8")
    # Re-run: the dedupe slug keeps it to the same single card.
    again = route_consequence_cards(
        vault, marked, trigger_id="catalog/sources/w1", reason="work w1 retracted"
    )
    assert again == []
    assert len(list((vault / "inbox").glob("flag-*.md"))) == 1


def test_every_touched_active_project_gets_its_own_card(tmp_path: Path) -> None:
    """One card per (trigger, project) is a bound, not a total: two here, not one."""
    vault = workspace(tmp_path)
    first = _seed_active_project(vault)
    second = _seed_second_project(vault)

    cards = route_consequence_cards(
        vault,
        {"notes/thesis.md": "grounds-lost", "notes/thesis-b.md": "warrant-lost"},
        trigger_id="catalog/sources/w1",
        reason="work w1 retracted",
    )

    # By project, not by whatever order the vault walk happened to yield: the
    # nested home sorts first and walks last (see `_seed_second_project`).
    assert [read_frontmatter(vault / card)["target"] for card in cards] == [second, first]


def test_marks_outside_every_active_slice_route_no_card(tmp_path: Path) -> None:
    """The quiet tier: labels and journal, and the inbox is never touched."""
    vault = workspace(tmp_path)
    _seed_active_project(vault)

    cards = route_consequence_cards(
        vault,
        {"notes/elsewhere.md": "grounds-lost"},
        trigger_id="catalog/sources/w1",
        reason="work w1 retracted",
    )

    assert cards == []
    assert not list((vault / "inbox").glob("*.md"))


def test_a_sweep_that_reaches_an_active_project_commits_its_alert_card(tmp_path: Path) -> None:
    """The engine seam C.5 left empty: the card rides the same trusted-writer commit."""
    vault = workspace(tmp_path)
    _seed_retraction_graph(vault)
    project_rel = _project(vault, "thesis-a", thesis="notes/thesis.md")
    arguments = {
        "trigger": "standing-changed",
        "reason": "work settles-2016 retracted",
        "actor": "integrity",
        "machine": "test-machine",
    }

    result = propagate_consequences_explicit(vault, "catalog/sources/settles-2016", **arguments)

    [card] = result["cards"]
    # The dedupe key is per (trigger, project), so the trigger the engine passes
    # is the fallen target and not the trigger *type* every sweep shares.
    assert "settles-2016" in card
    frontmatter = read_frontmatter(vault / card)
    assert frontmatter["target"] == project_rel
    assert frontmatter["loudness"] == "alert"
    assert "grounds-lost: 2" in frontmatter["finding"]
    assert "qualifier-regression: 1" in frontmatter["finding"]
    committed = set(git(vault, "show", "--name-only", "--format=", result["commit"]).splitlines())
    assert committed == {state.JOURNAL_HEAD_REL, card, *_RETRACTION_CLOSURE}

    again = propagate_consequences_explicit(vault, "catalog/sources/settles-2016", **arguments)

    assert again["cards"] == [] and again["commit"] == ""
