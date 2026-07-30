"""R2 section-5 grounded-synthesis contract, pinned before any composer exists.

The extractive composer is R1-gated (it needs passage-granular rows and
source-span-anchor); beta.1 ships the contract these tests pin: the ask
payload's allowed keys (any future prose must arrive by widening
ALLOWED_ANSWER_KEYS here, through the contract), the span-ref resolution
rule shared with the retrieval-fixture loader, and refusal honesty - when
nothing grounds, the output is the honest-empty payload, never prose
without anchors.
"""

from __future__ import annotations

from pathlib import Path

from memoria_vault.runtime import indexing, state
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.search_index import answer_query as _answer_query
from memoria_vault.runtime.span_refs import resolve_span_ref
from tests.helpers import call_with_context, copy_memoria_dirs

WORK_ID = "settles-2016-spaced-repetition"

# The full key set an ask payload may carry. query/engine/sources/unknowns/
# staleness/contradictions/project_context are the shipped answer_query
# contract (search_index.py _answer_from_hits); pipeline_counts and
# excluded_strata are the section-4 denominator fields (section P) and
# trace is the section-6 trace field - listed so this pin is order-tolerant
# against those sections. Composed prose is NOT here: a future composer
# must widen this set in the same change that satisfies section 5 (a
# resolvable span ref on every sentence). That edit is the contract gate.
ALLOWED_ANSWER_KEYS = frozenset(
    {
        "query",
        "engine",
        "sources",
        "unknowns",
        "staleness",
        "contradictions",
        "project_context",
        "pipeline_counts",
        "excluded_strata",
        "trace",
    }
)
ALLOWED_SOURCE_ROW_KEYS = frozenset({"path", "title", "type", "score"})
PROSE_KEYS = frozenset({"answer", "text", "sentences", "synthesis", "composition"})


def answer_query(vault: Path, *args, **kwargs):
    return call_with_context(_answer_query, vault, *args, **kwargs)


def workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas")
    return tmp_path


def checked_note(vault: Path, name: str, body: str) -> Path:
    path = vault / "notes" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntype: note\ncheck_status: checked\ntitle: {name}\n---\n{body}\n",
        encoding="utf-8",
    )
    rel = path.relative_to(vault).as_posix()
    state.record_observed_file_edit(
        vault, output_id=rel, concept_type="note", output_sha256=sha256_file(path)
    )
    state.set_concept_verdict(vault, rel, "checked")
    return path


def checked_fulltext_source(vault: Path, work_id: str, text: str) -> Path:
    content = vault / f".memoria/blobs/source-content/{work_id}/full-text/paper.txt"
    content.parent.mkdir(parents=True)
    content.write_text(text, encoding="utf-8")
    state.upsert_catalog_record(
        vault,
        work_id=work_id,
        title="A Trainable Spaced Repetition Model",
        provider_coverage="full",
        text_status="full-text",
        check_status="checked",
        content_path=content.relative_to(vault).as_posix(),
    )
    return content


def test_ask_payload_carries_no_prose_fields_beyond_the_contract(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    checked_note(vault, "alpha", "alpha retrieval body")

    answer = answer_query(vault, "alpha retrieval")

    assert answer["sources"], "fixture must produce at least one hit"
    assert set(answer) <= ALLOWED_ANSWER_KEYS
    assert PROSE_KEYS.isdisjoint(answer)
    for row in answer["sources"]:
        assert set(row) <= ALLOWED_SOURCE_ROW_KEYS


def test_no_grounding_output_is_the_honest_empty_refusal(tmp_path: Path) -> None:
    vault = workspace(tmp_path)
    checked_note(vault, "alpha", "alpha retrieval body")

    refusal = answer_query(vault, "zzz-absent-topic")

    assert refusal["sources"] == []
    assert refusal["unknowns"] == [
        "0 of 1 candidates matched; 0 unchecked documents were not searched"
    ]
    assert set(refusal) <= ALLOWED_ANSWER_KEYS
    assert PROSE_KEYS.isdisjoint(refusal)
    # Section P's section-4 fields ride through when the denominator
    # contract has landed (both-branch order tolerance; section P owns the
    # strict, unconditional assertions of these fields):
    strata = refusal.get("excluded_strata")
    if strata is not None:
        assert set(strata) == {"unchecked", "stale", "gated"}
    counts = refusal.get("pipeline_counts")
    if counts is not None:
        assert [entry["stage"] for entry in counts[:1]] == ["universe"]


def test_resolve_span_ref_matches_passages_then_falls_back_to_file_scan(
    tmp_path: Path,
) -> None:
    vault = workspace(tmp_path)
    content = checked_fulltext_source(
        vault, WORK_ID, "First finding. ^p0007\n\nSecond finding. ^p0009\n"
    )
    indexing.rebuild_passage_index_explicit(vault, actor="operation", machine="test-machine")

    resolved = {
        "work_id": WORK_ID,
        "anchor": "p0007",
        "path": f"fulltexts/{WORK_ID}.md",
    }
    assert resolve_span_ref(vault, f"{WORK_ID}#^p0007") == resolved
    # Shipped passages are one row per document (indexing.py _passage_row):
    # only the document's first anchor has a row, so ^p0009 resolves via
    # the interim file scan (the state.py _source_span_pages rule).
    assert resolve_span_ref(vault, f"{WORK_ID}#^p0009") == {
        "work_id": WORK_ID,
        "anchor": "p0009",
        "path": f"fulltexts/{WORK_ID}.md",
    }
    assert resolve_span_ref(vault, f"{WORK_ID}#^p0042") is None

    # Deleting the content file removes the file-scan route: ^p0007 must
    # still resolve through its passages row; ^p0009 honestly cannot.
    content.unlink()
    assert resolve_span_ref(vault, f"{WORK_ID}#^p0007") == resolved
    assert resolve_span_ref(vault, f"{WORK_ID}#^p0009") is None


def test_resolve_span_ref_refuses_malformed_and_unknown_refs(tmp_path: Path) -> None:
    vault = workspace(tmp_path)

    assert resolve_span_ref(vault, "no-separator") is None
    assert resolve_span_ref(vault, "work#p0007") is None
    assert resolve_span_ref(vault, "work#^page7") is None
    assert resolve_span_ref(vault, "work#^p007") is None
    assert resolve_span_ref(vault, "ghost-work#^p0007") is None
