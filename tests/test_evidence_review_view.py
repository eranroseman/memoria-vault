"""Contract tests for the evidence-review collector, view, and route (V2R-B.4/.5).

One collector (`_collect_evidence_review_queue`) with two projections: the
engine-direct raw queue `engine_api.evidence_review_queue` that V2R-C and U2's
cockpit consume, and `read_evidence_review_view` that the HTTP route serves as
nested view-spec cards.

The seeded matrix is built by product code — `compose_project_draft` mints the
markers, `verify_project_draft` rebuilds the rows — so the row states under test
are the ones the product actually derives. Evidence ids are minted randomly, so
every assertion here keys off the note the row came from, never a literal id.
"""

from __future__ import annotations

import json
import shutil
import threading
import urllib.error
import urllib.request
from http import HTTPStatus
from pathlib import Path
from typing import Any

import pytest

from memoria_vault.engine import api, cockpit
from memoria_vault.runtime import evidence_review, state
from memoria_vault.runtime.code.records import create_code_artifact
from memoria_vault.runtime.http_transport import (
    _dispatch,
    _nonnegative_int_query,
    make_http_server,
)
from memoria_vault.runtime.knowledge import compose_project_draft as _compose
from memoria_vault.runtime.knowledge import resolve_evidence_review as _resolve
from memoria_vault.runtime.knowledge import verify_project_draft as _verify
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.trusted_writer import append_explicit_journal_event
from tests.helpers import call_with_context, write_checked_concept

pytestmark = pytest.mark.contract

ALPHA = "projects/project-alpha/project.md"
BETA = "projects/project-beta/project.md"
ALPHA_SCOPE = ["projects/project-alpha"]
ROUTE = "/v1/views/evidence-review"

# notes/<stem>.md -> outline id. Ordered: the outline drives compose order.
NOTE_IDS = {
    "thesis": "01ARZ3NDEKTSV4RRFFQ69G5FA1",
    "support": "01ARZ3NDEKTSV4RRFFQ69G5FA2",
    "dangling": "01ARZ3NDEKTSV4RRFFQ69G5FA3",
    "hop": "01ARZ3NDEKTSV4RRFFQ69G5FA4",
    "beta-thesis": "01ARZ3NDEKTSV4RRFFQ69G5FA5",
    # notes/gamma-thesis.md belongs to the unchecked project.
    "gamma-thesis": "01ARZ3NDEKTSV4RRFFQ69G5FA6",
}
DRIFTED = "A complete source-backed claim."


def _note(vault: Path, stem: str, body: str, extra: str = "") -> None:
    write_checked_concept(
        vault,
        f"notes/{stem}.md",
        f"type: note\ncheck_status: checked\ntitle: {stem}\nid: {NOTE_IDS[stem]}\n{extra}",
        "note",
        body=body,
    )


def _source(vault: Path, work_id: str, text: str = "") -> None:
    """A checked catalog source; `text=""` leaves its content blob absent."""
    state.upsert_catalog_record(
        vault,
        work_id=work_id,
        citekey=work_id,
        title=f"{work_id} title",
        check_status="checked",
        content_path=f".memoria/blobs/source-content/{work_id}.md",
    )
    if text:
        path = vault / f".memoria/blobs/source-content/{work_id}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def _project(vault: Path, name: str, *, checked: bool = True) -> None:
    frontmatter = f"type: project\ncheck_status: checked\ntitle: {name}\n"
    if checked:
        write_checked_concept(vault, f"projects/{name}/project.md", frontmatter, "project")
        return
    # No `mark_file_status`: an unchecked project is exactly what
    # `_read_project_draft` refuses, and the collector must skip it.
    path = vault / f"projects/{name}/project.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\nBody.\n", encoding="utf-8")


def _outline(vault: Path, name: str, stems: list[str]) -> None:
    path = vault / f"projects/{name}/outline.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"- {NOTE_IDS[stem]} — {stem}\n" for stem in stems), encoding="utf-8")


def _attention(vault: Path, name: str, *, kind: str, status: str, target: str) -> str:
    rel = f"inbox/{name}.md"
    path = vault / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "projection: attention\n"
        f"title: {name}\n"
        f"attention_kind: {kind}\n"
        f"attention_status: {status}\n"
        "routing_class: ask\n"
        "loudness: notice\n"
        f"target: {target}\n"
        "---\n"
        f"{name} body.\n",
        encoding="utf-8",
    )
    return rel


def _ids_by_note(vault: Path, name: str, stems: list[str]) -> dict[str, str]:
    """Map each outline stem to the evidence id composed under its heading."""
    text = (vault / f"projects/{name}/draft.md").read_text(encoding="utf-8")
    ids: dict[str, str] = {}
    for row in state.evidence_sets(vault):
        anchor = "^blk-" + row["id"].removeprefix("ev-")
        if anchor not in text:
            continue
        heading = text.rfind("## ", 0, text.index(anchor))
        stem = text[heading + 3 : text.index("\n", heading)].strip()
        if stem in stems:
            ids[stem] = str(row["id"])
    return ids


def _build_matrix(vault: Path) -> dict[str, str]:
    """One vault holding every routing type, a read-only drift row, two projects,
    an unchecked project, and four inbox cards of which two are open SRD gaps."""
    _source(vault, "source-alpha", "source-alpha source span. ^p0001\n")
    _source(vault, "source-missing")

    _project(vault, "project-alpha")
    _note(vault, "thesis", "An implicit synthesis claim.")
    _note(vault, "support", DRIFTED, extra="work_id: catalog/sources/source-alpha\n")
    _note(
        vault,
        "dangling",
        "A claim over a span that never resolves.",
        extra="work_id: catalog/sources/source-missing\n",
    )
    _note(vault, "hop", "A dependent multi-hop claim.")
    _outline(vault, "project-alpha", ["thesis", "support", "dangling", "hop"])
    call_with_context(_compose, vault, "project-alpha")
    ids = _ids_by_note(vault, "project-alpha", ["thesis", "support", "dangling", "hop"])

    # The hop row's grounds are a nested evidence set: only a marker edit plus a
    # verify rebuild can produce one, because compose derives items from notes.
    draft = vault / "projects/project-alpha/draft.md"
    text = draft.read_text(encoding="utf-8")
    assert f"%%ev: {ids['hop']} items=%%" in text
    draft.write_text(
        text.replace(f"%%ev: {ids['hop']} items=%%", f"%%ev: {ids['hop']} items={ids['thesis']}%%"),
        encoding="utf-8",
    )
    call_with_context(_verify, vault, "project-alpha")

    _project(vault, "project-beta")
    _note(vault, "beta-thesis", "A second project's implicit claim.")
    _outline(vault, "project-beta", ["beta-thesis"])
    call_with_context(_compose, vault, "project-beta")
    ids |= _ids_by_note(vault, "project-beta", ["beta-thesis"])

    _project(vault, "project-gamma", checked=False)
    _note(vault, "gamma-thesis", "An unchecked project's claim.")
    _outline(vault, "project-gamma", ["gamma-thesis"])

    # Drift last: the stored binding must already exist for the edit to break it.
    draft.write_text(
        draft.read_text(encoding="utf-8").replace(DRIFTED, f"{DRIFTED} Silently edited."),
        encoding="utf-8",
    )

    _attention(
        vault,
        "srd-gap-alpha",
        kind="srd-gap",
        status="open",
        target="projects/project-alpha/draft.md",
    )
    _attention(
        vault,
        "srd-gap-beta",
        kind="srd-gap",
        status="open",
        target="projects/project-beta/draft.md",
    )
    _attention(
        vault,
        "srd-gap-done",
        kind="srd-gap",
        status="resolved",
        target="projects/project-alpha/draft.md",
    )
    _attention(
        vault, "full-text-gap", kind="gap", status="open", target="projects/project-alpha/draft.md"
    )
    return ids


@pytest.fixture(scope="module")
def _matrix_template(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, str]]:
    root = tmp_path_factory.mktemp("evidence-review-template")
    vault = root / "vault"
    vault.mkdir()
    return vault, _build_matrix(vault)


@pytest.fixture
def matrix(tmp_path: Path, _matrix_template) -> tuple[Path, dict[str, str]]:
    """A private copy of the module-scoped seed: composing it costs seconds."""
    template, ids = _matrix_template
    vault = tmp_path / "vault"
    shutil.copytree(template, vault, symlinks=True)
    return vault, dict(ids)


def _rows(payload: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [row for row in payload["rows"] if row["kind"] == kind]


def _by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["evidence_id"]): row for row in rows}


def _cards(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(block["evidence_id"]): block
        for block in payload["view"]["blocks"]
        if "evidence_id" in block
    }


# --- V2R-B.4: the raw engine-direct queue -------------------------------------


def test_evidence_review_queue_emits_the_raw_discriminated_union(matrix) -> None:
    """`kind` on both arms, and the raw (never renamed) evidence field names.

    U2's cockpit selects on `kind == "evidence-set"` and counts `disposition`;
    the superseded DTO layer of the V2 plan renamed both away. Either change
    makes that panel report a confident zero, so the names are pinned here.
    """
    vault, ids = matrix

    payload = api.evidence_review_queue(vault, batch=0)

    assert payload["ok"] is True
    evidence = _by_id(_rows(payload, "evidence-set"))
    assert set(evidence) == {ids[stem] for stem in ("thesis", "support", "dangling", "hop")} | {
        ids["beta-thesis"]
    }
    hop = evidence[ids["hop"]]
    assert hop["project_path"] == ALPHA
    assert hop["draft_path"] == "projects/project-alpha/draft.md"
    assert hop["routing_type"] == "multi-hop"
    assert hop["disposition"] == "open"
    assert hop["items"] == [ids["thesis"]]  # raw v2 reference strings, not previews
    assert hop["item_count"] == 1
    assert hop["reviewable"] is True
    assert hop["age_days"] == 0
    assert hop["claim_text"] == "A dependent multi-hop claim."
    assert "cure" not in hop
    # The superseded DTO renames, asserted absent on every evidence row.
    for row in evidence.values():
        assert {"latest_decision", "routing", "project", "analysis"}.isdisjoint(row)
    srd = _rows(payload, "srd-gap")
    assert [row["card_block"]["ref"] for row in srd] == [
        "inbox/srd-gap-alpha.md",
        "inbox/srd-gap-beta.md",
    ]
    assert all(set(row) == {"kind", "card_block"} for row in srd)
    assert srd[0]["card_block"]["kind_line"] == "srd-gap"


def test_evidence_review_queue_routes_every_type_and_blocks_the_drifted_row(matrix) -> None:
    vault, ids = matrix

    evidence = _by_id(_rows(api.evidence_review_queue(vault, batch=0), "evidence-set"))

    assert evidence[ids["thesis"]]["routing_type"] == "implicit"
    assert evidence[ids["hop"]]["routing_type"] == "multi-hop"
    assert evidence[ids["dangling"]]["routing_type"] == "incomplete"
    drifted = evidence[ids["support"]]
    assert drifted["routing_type"] == ""
    assert drifted["reviewable"] is False
    assert drifted["blocked_by"] == [
        {
            "kind": "evidence-text-drift",
            "reason": "anchored block text differs from its stored binding",
        }
    ]
    assert drifted["cure"] == evidence_review.PERMANENT_BLOCK_CURE


def test_evidence_review_queue_resolves_grounds_previews_for_every_ref_kind(matrix) -> None:
    vault, ids = matrix

    evidence = _by_id(_rows(api.evidence_review_queue(vault, batch=0), "evidence-set"))

    assert evidence[ids["support"]]["item_previews"] == [
        {
            "ref": "source-alpha#^p0001",
            "kind": "source-span",
            "work_id": "source-alpha",
            "anchor": "^p0001",
            "resolves": True,
            "excerpt": "source-alpha source span.",
        }
    ]
    assert evidence[ids["dangling"]]["item_previews"] == [
        {
            "ref": "source-missing#^p0001",
            "kind": "source-span",
            "work_id": "source-missing",
            "anchor": "^p0001",
            "resolves": False,
        }
    ]
    assert evidence[ids["hop"]]["item_previews"] == [
        {
            "ref": ids["thesis"],
            "kind": "evidence-set",
            "resolves": True,
            "expansion": {
                "evidence_type": "implicit",
                "state": "evidence-incomplete",
                "item_count": 0,
            },
        }
    ]
    assert evidence[ids["thesis"]]["item_previews"] == []


def test_evidence_review_queue_facets_are_the_unfiltered_evidence_denominators(matrix) -> None:
    vault, _ids = matrix

    payload = api.evidence_review_queue(vault, batch=0)

    # The drifted row routes nowhere, so it is absent from the routing
    # denominator while still counting in `project` and `total`.
    assert payload["facet_totals"] == {
        "routing_type": {"implicit": 2, "multi-hop": 1, "incomplete": 1},
        "project": {ALPHA: 4, BETA: 1},
        "total": 5,
    }
    assert payload["total"] == 7
    assert payload["batch"] == 0


def test_evidence_review_queue_batches_evidence_rows_only(matrix) -> None:
    vault, _ids = matrix

    batched = api.evidence_review_queue(vault, batch=2)

    assert [row["kind"] for row in batched["rows"]] == [
        "evidence-set",
        "evidence-set",
        "srd-gap",
        "srd-gap",
    ]
    # `total` stays the whole filtered, pre-batch union.
    assert batched["total"] == 7
    assert batched["batch"] == 2
    assert batched["facet_totals"]["total"] == 5


def test_evidence_review_queue_orders_evidence_by_project_then_srd_last(matrix) -> None:
    vault, _ids = matrix

    rows = api.evidence_review_queue(vault, batch=0)["rows"]

    assert [row["project_path"] for row in rows if row["kind"] == "evidence-set"] == (
        [ALPHA] * 4 + [BETA]
    )
    assert [row["kind"] for row in rows][-2:] == ["srd-gap", "srd-gap"]


def test_evidence_review_queue_skips_projects_a_read_cannot_consume(matrix) -> None:
    """The unchecked `project-gamma` has an outline and a note but no checked
    frontmatter: `_read_project_draft` refuses it, and one refused project must
    not take the whole queue down with it."""
    vault, _ids = matrix

    rows = api.evidence_review_queue(vault, batch=0)["rows"]

    assert (vault / "projects/project-gamma/project.md").is_file()
    assert all("project-gamma" not in str(row.get("project_path") or "") for row in rows)


def test_evidence_review_queue_carries_only_open_srd_gap_cards(matrix) -> None:
    """Selection is by attention kind *and* status: a resolved gap is not review
    work, and a full-text gap is a different kind of card entirely."""
    vault, _ids = matrix

    rows = api.evidence_review_queue(vault, batch=0)["rows"]

    refs = {row["card_block"]["ref"] for row in rows if row["kind"] == "srd-gap"}
    assert refs == {"inbox/srd-gap-alpha.md", "inbox/srd-gap-beta.md"}
    assert "inbox/srd-gap-done.md" not in refs
    assert "inbox/full-text-gap.md" not in refs


@pytest.mark.parametrize(
    ("kwargs", "shown_evidence"),
    [
        ({"routing_type": "implicit"}, 2),
        ({"project": "project-alpha"}, 4),
        ({"min_age_days": 1}, 0),
    ],
)
def test_evidence_review_queue_drops_srd_rows_when_any_filter_is_active(
    matrix, kwargs: dict[str, Any], shown_evidence: int
) -> None:
    """An SRD gap answers no evidence facet, so a filtered queue that still
    carried them would report rows the filter never considered."""
    vault, _ids = matrix

    payload = api.evidence_review_queue(vault, batch=0, **kwargs)

    assert _rows(payload, "srd-gap") == []
    assert len(_rows(payload, "evidence-set")) == shown_evidence
    assert payload["total"] == shown_evidence
    assert payload["facet_totals"]["total"] == 5


def test_evidence_review_queue_normalizes_the_project_filter_spellings(matrix) -> None:
    vault, _ids = matrix

    for spelling in ("project-beta", "projects/project-beta", BETA):
        payload = api.evidence_review_queue(vault, batch=0, project=spelling)
        assert [row["project_path"] for row in _rows(payload, "evidence-set")] == [BETA]

    with pytest.raises(ValueError, match="project must be"):
        api.evidence_review_queue(vault, project="../escape")


def test_evidence_review_queue_rejects_a_negative_batch_and_age(matrix) -> None:
    vault, _ids = matrix

    with pytest.raises(ValueError, match="batch"):
        api.evidence_review_queue(vault, batch=-1)
    with pytest.raises(ValueError, match="min_age_days"):
        api.evidence_review_queue(vault, min_age_days=-1)


def test_read_evidence_review_queue_scopes_before_assembly_and_facets(matrix, monkeypatch) -> None:
    """Scope defines the queue universe (amendment §7): an out-of-scope draft
    never reaches the assembler, so it cannot reappear in a denominator."""
    vault, ids = matrix
    seen: list[list[str]] = []
    real = evidence_review.assemble_evidence_review_queue

    def recording(drafts, dispositions, **kwargs):
        drafts = list(drafts)
        seen.append([str(draft["draft_path"]) for draft in drafts])
        return real(drafts, dispositions, **kwargs)

    monkeypatch.setattr(evidence_review, "assemble_evidence_review_queue", recording)

    payload = api.evidence_review_queue(vault, batch=0, read_scope=ALPHA_SCOPE)

    assert seen == [["projects/project-alpha/draft.md"]]
    assert payload["facet_totals"] == {
        "routing_type": {"implicit": 1, "multi-hop": 1, "incomplete": 1},
        "project": {ALPHA: 4},
        "total": 4,
    }
    assert ids["beta-thesis"] not in _by_id(_rows(payload, "evidence-set"))
    assert [row["card_block"]["ref"] for row in _rows(payload, "srd-gap")] == [
        "inbox/srd-gap-alpha.md"
    ]


def test_evidence_review_queue_scopes_on_the_draft_not_the_project_file(matrix) -> None:
    """A scope may name the draft alone, and `projects/<name>/` covers both
    files — so only a draft-only scope tells the two apart. The collector
    filters on `draft_path`, the file the evidence actually lives in; filtering
    on `project_path` would empty this queue instead."""
    vault, ids = matrix

    payload = api.evidence_review_queue(
        vault, batch=0, read_scope=["projects/project-alpha/draft.md"]
    )

    assert set(_by_id(_rows(payload, "evidence-set"))) == {
        ids[stem] for stem in ("thesis", "support", "dangling", "hop")
    }
    # The SRD card is in scope by its `target`, which is that same draft.
    assert [row["card_block"]["ref"] for row in _rows(payload, "srd-gap")] == [
        "inbox/srd-gap-alpha.md"
    ]


def test_evidence_review_queue_reads_the_latest_disposition_per_row(matrix) -> None:
    vault, ids = matrix

    _resolve(
        vault, ids["thesis"], actor="pi", machine="test", decision="reject", reason="not grounded"
    )
    payload = api.evidence_review_queue(vault, batch=0)

    evidence = _by_id(_rows(payload, "evidence-set"))
    assert evidence[ids["thesis"]]["disposition"] == "rejected"
    assert evidence[ids["thesis"]]["disposition_reason"] == "not grounded"
    assert evidence[ids["hop"]]["disposition"] == "open"


def test_evidence_review_queue_kind_and_disposition_reach_the_cockpit_panel(matrix) -> None:
    """The cross-plan consumer proof (U2 INT.1). The cockpit reads this queue
    engine-direct, selects `kind == "evidence-set"`, and counts `disposition`
    — with a *disposed* row in the fixture, so `counts.get("open", 0)` is never
    taken as an unfixtured default."""
    vault, ids = matrix

    _resolve(vault, ids["thesis"], actor="pi", machine="test", decision="reject", reason="no")
    panel = cockpit.assemble_triage(vault)["review"]

    assert panel == {
        "source_action": "views.evidence_review",
        "open": 4,
        "counts": {"open": 4, "rejected": 1},
        "srd_gaps": 2,
    }


# --- V2R-B.4: the vault-reading helpers ---------------------------------------


def test_evidence_review_reads_are_empty_before_the_state_db_exists(tmp_path: Path) -> None:
    """A vault with no database is a vault with no history, not an error: the
    collector runs over freshly initialized workspaces too."""
    assert not state.db_path(tmp_path).is_file()

    assert evidence_review.evidence_dispositions(tmp_path) == []
    assert evidence_review.evidence_minted_at(tmp_path) == {}
    assert evidence_review.span_source_index(tmp_path) == {}


def test_evidence_minted_at_keeps_the_first_mint_per_evidence_id(matrix) -> None:
    """Age is how long a claim has waited for a decision, so a later re-mint of
    the same id must not reset it."""
    vault, ids = matrix
    first = evidence_review.evidence_minted_at(vault)[ids["thesis"]]

    append_explicit_journal_event(
        vault,
        {
            "event": "evidence-minted",
            "operation": "compose-project-draft",
            "evidence_id": ids["thesis"],
            "timestamp": "2099-01-01T00:00:00Z",
        },
        actor="pi",
        machine="test-machine",
    )

    assert evidence_review.evidence_minted_at(vault)[ids["thesis"]] == first


def test_span_source_index_reports_a_source_whose_content_blob_is_absent(matrix) -> None:
    vault, _ids = matrix

    index = evidence_review.span_source_index(vault)

    assert index["source-alpha"] == ({"p0001"}, "source-alpha source span. ^p0001\n")
    assert index["source-missing"] == (set(), "")


def test_resolve_item_previews_reports_code_grounds_completeness(tmp_path: Path) -> None:
    """The v2 `code-grounds:` arm — renamed from the retired `code-warrant:`
    spelling — resolves through the real run ledger, digest and all."""
    output = tmp_path / "projects/project-alpha/code/analysis/outputs/result.txt"
    output.parent.mkdir(parents=True)
    output.write_text("42\n", encoding="utf-8")
    output_rel = output.relative_to(tmp_path).as_posix()
    output_hash = sha256_file(output)
    create_code_artifact(
        tmp_path,
        "project-alpha",
        "analysis",
        approved_command=["python3", "main.py"],
        declared_outputs=[output_rel],
    )
    state.record_code_run(
        tmp_path,
        run_id="run-1",
        artifact_id="analysis",
        command=["python3", "main.py"],
        cwd="projects/project-alpha/code/analysis/src",
        output_hashes={output_rel: output_hash},
        exit_status=0,
        sandbox_backend="bwrap",
        sandbox_profile_hash="sha256:" + "0" * 64,
        run_state="succeeded",
    )
    stale = "sha256:" + "0" * 64

    previews = evidence_review.resolve_item_previews(
        tmp_path,
        [f"code-grounds:run-1:analysis:{output_hash}", f"code-grounds:run-1:analysis:{stale}"],
        rows_by_id={},
        span_sources={},
    )

    assert previews == [
        {
            "ref": f"code-grounds:run-1:analysis:{output_hash}",
            "kind": "code-grounds",
            "run_id": "run-1",
            "artifact_id": "analysis",
            "output_sha256": output_hash,
            "resolves": True,
            "state": "complete",
        },
        {
            "ref": f"code-grounds:run-1:analysis:{stale}",
            "kind": "code-grounds",
            "run_id": "run-1",
            "artifact_id": "analysis",
            "output_sha256": stale,
            "resolves": False,
            "state": "evidence-incomplete",
        },
    ]


def test_resolve_item_previews_reports_an_unresolvable_nested_evidence_set() -> None:
    previews = evidence_review.resolve_item_previews(
        Path("/nonexistent"), ["ev-11111111"], rows_by_id={}, span_sources={}
    )

    assert previews == [{"ref": "ev-11111111", "kind": "evidence-set", "resolves": False}]


# --- V2R-B.4: the view projection ---------------------------------------------


def test_evidence_review_view_renders_one_nested_card_per_row(matrix) -> None:
    vault, ids = matrix

    payload = api.read_evidence_review_view(vault)

    assert payload["ok"] is True
    assert payload["api_version"] == api.READ_API_VERSION
    view = payload["view"]
    assert view["version"] == "view-spec.v1"
    assert view["kind"] == "evidence-review"
    assert [block["kind"] for block in view["blocks"]] == ["card"] * 7
    assert {block["kind"] for block in view["blocks"]} <= set(api.VIEW_BLOCK_KINDS)
    hop = _cards(payload)[ids["hop"]]
    assert hop["kind_line"] == "evidence-review"
    assert hop["project"] == ALPHA
    assert hop["title"] == "A dependent multi-hop claim."
    assert [child["kind"] for child in hop["blocks"]] == [
        "evidence-list",
        "text",
        "action-row",
    ]
    assert hop["blocks"][1]["text"] == "multi-hop"
    assert [action["label"] for action in hop["blocks"][2]["actions"]] == [
        "Accept",
        "Reject",
        "Edit",
        "Defer",
    ]
    assert hop["blocks"][2]["actions"][0] == {
        "label": "Accept",
        "operation_id": "resolve-evidence",
        "payload": {"evidence_id": ids["hop"], "decision": "accept"},
    }
    drifted = _cards(payload)[ids["support"]]
    assert [child["kind"] for child in drifted["blocks"]] == ["evidence-list", "text"]
    assert drifted["blocks"][1]["text"] == ("anchored block text differs from its stored binding")
    assert "cure" in drifted
    assert _cards(payload)[ids["dangling"]]["blocks"][1]["text"] == (
        "evidence-incomplete: source-missing#^p0001 does not resolve"
    )
    trailing = view["blocks"][-2:]
    assert [block["kind_line"] for block in trailing] == ["srd-gap", "srd-gap"]


def test_evidence_review_view_merges_all_evidence_facets(matrix) -> None:
    """The merge adds `kind`/`shown` and replaces `total`; it never drops the
    evidence denominator maps the pane's facet chips are drawn from."""
    vault, _ids = matrix

    payload = api.read_evidence_review_view(vault, batch=10)

    assert payload["facets"] == {
        "routing_type": {"implicit": 2, "multi-hop": 1, "incomplete": 1},
        "project": {ALPHA: 4, BETA: 1},
        "kind": {"evidence-set": 5, "srd-gap": 2},
        "total": 7,
        "shown": 7,
        "batch": 10,
    }


def test_evidence_review_view_batch_caps_evidence_cards_only(matrix) -> None:
    vault, _ids = matrix

    payload = api.read_evidence_review_view(vault, batch=2)

    assert [block["kind_line"] for block in payload["view"]["blocks"]] == [
        "evidence-review",
        "evidence-review",
        "srd-gap",
        "srd-gap",
    ]
    assert payload["facets"]["shown"] == 4
    assert payload["facets"]["batch"] == 2
    assert payload["facets"]["total"] == 7


def test_evidence_review_view_omits_srd_cards_from_a_filtered_view(matrix) -> None:
    vault, _ids = matrix

    payload = api.read_evidence_review_view(vault, routing_type="implicit")

    assert [block["kind_line"] for block in payload["view"]["blocks"]] == [
        "evidence-review",
        "evidence-review",
    ]
    assert payload["facets"]["kind"] == {"evidence-set": 5, "srd-gap": 0}
    assert payload["facets"]["total"] == 5
    assert payload["facets"]["shown"] == 2


def test_read_evidence_review_view_scopes_evidence_and_srd_before_counts(matrix) -> None:
    vault, ids = matrix

    payload = api.read_evidence_review_view(vault, read_scope=ALPHA_SCOPE)

    cards = _cards(payload)
    assert ids["beta-thesis"] not in cards
    assert set(cards) == {ids[stem] for stem in ("thesis", "support", "dangling", "hop")}
    assert [block["ref"] for block in payload["view"]["blocks"][-1:]] == ["inbox/srd-gap-alpha.md"]
    assert payload["facets"] == {
        "routing_type": {"implicit": 1, "multi-hop": 1, "incomplete": 1},
        "project": {ALPHA: 4},
        "kind": {"evidence-set": 4, "srd-gap": 1},
        "total": 5,
        "shown": 5,
        "batch": 10,
    }


def test_evidence_review_view_requires_a_positive_batch(matrix) -> None:
    vault, _ids = matrix

    with pytest.raises(ValueError, match="batch must be positive"):
        api.read_evidence_review_view(vault, batch=0)
    with pytest.raises(ValueError, match="batch must be positive"):
        api.read_evidence_review_view(vault, batch=-1)


def test_evidence_review_view_collects_once_and_previews_shown_rows_only(
    matrix, monkeypatch
) -> None:
    """One collector, one assembly, and preview resolution paid only for the
    rows the batch actually shows."""
    vault, _ids = matrix
    assemblies = 0
    previewed: list[list[str]] = []
    real_assemble = evidence_review.assemble_evidence_review_queue
    real_previews = evidence_review.resolve_item_previews

    def counting_assemble(*args, **kwargs):
        nonlocal assemblies
        assemblies += 1
        return real_assemble(*args, **kwargs)

    def recording_previews(vault_arg, items, **kwargs):
        items = list(items)
        previewed.append(items)
        return real_previews(vault_arg, items, **kwargs)

    monkeypatch.setattr(evidence_review, "assemble_evidence_review_queue", counting_assemble)
    monkeypatch.setattr(evidence_review, "resolve_item_previews", recording_previews)

    api.read_evidence_review_view(vault, batch=2)

    assert assemblies == 1
    assert len(previewed) == 2


# --- V2R-B.5: the registered route --------------------------------------------


def test_nonnegative_int_query_accepts_zero_and_rejects_negative() -> None:
    assert _nonnegative_int_query({}, "min_age_days", 7) == 7
    assert _nonnegative_int_query({"min_age_days": [""]}, "min_age_days", 7) == 7
    assert _nonnegative_int_query({"min_age_days": ["0"]}, "min_age_days", 7) == 0
    assert _nonnegative_int_query({"min_age_days": ["3"]}, "min_age_days", 7) == 3
    with pytest.raises(ValueError, match="min_age_days must be nonnegative"):
        _nonnegative_int_query({"min_age_days": ["-1"]}, "min_age_days", 7)
    with pytest.raises(ValueError, match="min_age_days must be an integer"):
        _nonnegative_int_query({"min_age_days": ["soon"]}, "min_age_days", 7)


def test_evidence_review_route_serves_nested_cards_and_facets(matrix) -> None:
    vault, ids = matrix

    payload, status = _dispatch(vault, "GET", ROUTE, dict)

    assert status == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["api_version"] == api.READ_API_VERSION
    assert payload["view"]["kind"] == "evidence-review"
    assert payload["facets"]["total"] == 7
    assert payload["facets"]["kind"] == {"evidence-set": 5, "srd-gap": 2}
    hop = _cards(payload)[ids["hop"]]
    assert [child["kind"] for child in hop["blocks"]] == [
        "evidence-list",
        "text",
        "action-row",
    ]
    assert hop["blocks"][2]["actions"][1]["payload"] == {
        "evidence_id": ids["hop"],
        "decision": "reject",
    }


def test_evidence_review_route_filters_and_refuses_an_unknown_routing_type(matrix) -> None:
    vault, _ids = matrix

    filtered, filtered_status = _dispatch(vault, "GET", f"{ROUTE}?routing_type=multi-hop", dict)
    invalid, invalid_status = _dispatch(vault, "GET", f"{ROUTE}?routing_type=bogus", dict)

    assert filtered_status == HTTPStatus.OK
    assert filtered["facets"]["shown"] == 1
    assert filtered["facets"]["total"] == 5
    assert invalid_status == HTTPStatus.BAD_REQUEST
    assert invalid["ok"] is False
    assert "routing_type" in invalid["error"]


def test_evidence_review_route_rejects_zero_batch(matrix) -> None:
    """`batch=0` means "all rows" for the engine-direct queue only; the route
    keeps the positive-only parser so an unbounded page is never served."""
    vault, _ids = matrix

    zero, zero_status = _dispatch(vault, "GET", f"{ROUTE}?batch=0", dict)
    positive, positive_status = _dispatch(vault, "GET", f"{ROUTE}?batch=1", dict)

    assert zero_status == HTTPStatus.BAD_REQUEST
    assert zero["error"] == "batch must be positive"
    assert positive_status == HTTPStatus.OK
    assert positive["facets"]["shown"] == 3  # one evidence card plus both SRD cards


def test_evidence_review_route_accepts_zero_min_age_and_rejects_negative(matrix) -> None:
    vault, _ids = matrix

    zero, zero_status = _dispatch(vault, "GET", f"{ROUTE}?min_age_days=0", dict)
    negative, negative_status = _dispatch(vault, "GET", f"{ROUTE}?min_age_days=-1", dict)

    assert zero_status == HTTPStatus.OK
    assert zero["facets"]["shown"] == 7  # an explicit zero is "no age filter"
    assert negative_status == HTTPStatus.BAD_REQUEST
    assert negative["error"] == "min_age_days must be nonnegative"


def test_evidence_review_http_scope_excludes_evidence_and_srd(matrix) -> None:
    vault, ids = matrix

    payload, status = _dispatch(vault, "GET", f"{ROUTE}?scope=projects/project-alpha", dict)

    assert status == HTTPStatus.OK
    body = json.dumps(payload)
    assert ids["beta-thesis"] not in body
    assert "inbox/srd-gap-beta.md" not in body
    assert "inbox/srd-gap-alpha.md" in body
    assert payload["facets"] == {
        "routing_type": {"implicit": 1, "multi-hop": 1, "incomplete": 1},
        "project": {ALPHA: 4},
        "kind": {"evidence-set": 4, "srd-gap": 1},
        "total": 5,
        "shown": 5,
        "batch": 10,
    }


def test_evidence_review_route_refuses_a_write_method(matrix) -> None:
    vault, _ids = matrix

    payload, status = _dispatch(vault, "POST", ROUTE, dict)

    assert status == HTTPStatus.METHOD_NOT_ALLOWED
    assert payload == {"ok": False, "error": f"method not allowed: POST {ROUTE}"}


def test_evidence_review_view_requires_bearer_token(matrix) -> None:
    vault, ids = matrix
    server = make_http_server(vault, host="127.0.0.1", port=0, token="test-token")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}{ROUTE}"
        with pytest.raises(urllib.error.HTTPError) as denied:
            urllib.request.urlopen(url)
        assert denied.value.code == HTTPStatus.UNAUTHORIZED
        assert json.loads(denied.value.read().decode("utf-8")) == {
            "ok": False,
            "error": "unauthorized: missing or invalid bearer token",
        }
        request = urllib.request.Request(url, headers={"Authorization": "Bearer test-token"})
        with urllib.request.urlopen(request) as response:
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["ok"] is True
        assert payload["view"]["kind"] == "evidence-review"
        assert [child["kind"] for child in _cards(payload)[ids["hop"]]["blocks"]] == [
            "evidence-list",
            "text",
            "action-row",
        ]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
