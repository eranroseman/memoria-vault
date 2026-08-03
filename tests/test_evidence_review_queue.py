"""Unit tests for evidence-review queue assembly and honesty-card blocks (V2 slice 1)."""

from __future__ import annotations

import datetime
import hashlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

from memoria_vault.runtime import evidence_review, knowledge, state

pytestmark = pytest.mark.unit

EV_OPEN = "ev-11111111"
EV_SPAN = "ev-22222222"
EV_HOP = "ev-33333333"
EV_CODE = "ev-44444444"
BLOCK_REF = "projects/project-alpha/draft.md#^blk-11111111"
SPAN_BLOCK_REF = "projects/project-alpha/draft.md#^blk-22222222"
HOP_BLOCK_REF = "projects/project-beta/draft.md#^blk-33333333"
CODE_BLOCK_REF = "projects/project-alpha/draft.md#^blk-44444444"
ALPHA = "projects/project-alpha/project.md"
BETA = "projects/project-beta/project.md"
CODE_ITEM = "code-grounds:run-1:artifact-1:sha256:" + "0" * 64
CONTENT = (
    "An implicit synthesis claim. ^blk-11111111 %%ev: ev-11111111 items=%%\n"
    "\n"
    "A single-span claim. ^blk-22222222 %%ev: ev-22222222 items=source-alpha#^p0001%%\n"
    "\n"
    f"A computed claim. ^blk-44444444 %%ev: ev-44444444 items={CODE_ITEM}%%\n"
)
BETA_CONTENT = (
    "A multi-hop claim. ^blk-33333333 %%ev: ev-33333333 items=ev-11111111|source-beta#^p0002%%\n"
)
TODAY = datetime.date(2026, 7, 16)


def _row(**overrides: Any) -> dict[str, Any]:
    """An implicit, review-required alpha row — `state._evidence_set_row` shaped."""
    row = {
        "id": EV_OPEN,
        "block_ref": BLOCK_REF,
        "items": [],
        "type": "implicit",
        "completeness_status": "evidence-incomplete",
        "review_required": True,
        "run_id": "",
        "block_text_sha256": state._block_text_sha256_from_text(CONTENT, BLOCK_REF),
    }
    row.update(overrides)
    return row


def _span_row(**overrides: Any) -> dict[str, Any]:
    """A single-span alpha row: incomplete grounds, no review flag."""
    return _row(
        **{
            "id": EV_SPAN,
            "block_ref": SPAN_BLOCK_REF,
            "items": ["source-alpha#^p0001"],
            "type": "single-span",
            "review_required": False,
            "block_text_sha256": state._block_text_sha256_from_text(CONTENT, SPAN_BLOCK_REF),
            **overrides,
        }
    )


def _code_row(**overrides: Any) -> dict[str, Any]:
    """A computed alpha row grounded in a v2 `code-grounds:` reference."""
    return _row(
        **{
            "id": EV_CODE,
            "block_ref": CODE_BLOCK_REF,
            "items": [CODE_ITEM],
            "type": "computed",
            "review_required": False,
            "block_text_sha256": state._block_text_sha256_from_text(CONTENT, CODE_BLOCK_REF),
            **overrides,
        }
    )


def _hop_row(**overrides: Any) -> dict[str, Any]:
    """A multi-hop beta row — the second project in the default queue."""
    return _row(
        **{
            "id": EV_HOP,
            "block_ref": HOP_BLOCK_REF,
            "items": ["ev-11111111", "source-beta#^p0002"],
            "type": "multi-hop",
            "block_text_sha256": state._block_text_sha256_from_text(BETA_CONTENT, HOP_BLOCK_REF),
            **overrides,
        }
    )


def _draft(
    rows: list[dict[str, Any]], content: str = CONTENT, name: str = "project-alpha"
) -> dict[str, Any]:
    """A `knowledge.read_project_draft`-shaped mapping."""
    return {
        "project_path": f"projects/{name}/project.md",
        "draft_path": f"projects/{name}/draft.md",
        "content": content,
        "evidence_sets": rows,
    }


def _drafts() -> list[dict[str, Any]]:
    """The default fixture: four rows over two projects and three routing types."""
    return [
        _draft([_row(), _span_row(), _code_row()]),
        _draft([_hop_row()], BETA_CONTENT, "project-beta"),
    ]


def _queue(
    drafts: list[dict[str, Any]] | None = None,
    dispositions: Sequence[Mapping[str, Any]] = (),
    *,
    minted_at: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    return evidence_review.assemble_evidence_review_queue(
        _drafts() if drafts is None else drafts,
        dispositions,
        minted_at=minted_at,
        today=TODAY,
    )


def _open_queue(**kwargs: Any) -> list[dict[str, Any]]:
    """The one implicit alpha row alone — for the disposition rules."""
    return _queue([_draft([_row()])], **kwargs)


OPEN_DIGEST = hashlib.sha256(b"").hexdigest()


def _event(
    decision: str,
    *,
    evidence_id: str = EV_OPEN,
    timestamp: str = "2026-07-15T09:00:00Z",
    items_sha256: str | None = OPEN_DIGEST,
    **extra: Any,
) -> dict[str, Any]:
    """A `resolve-evidence-review` payload, shaped like the seam that writes it.

    `resolve_evidence_review` journals `items_sha256` on *every* decision, not
    only accept, so the default carries the digest of `_row()`'s empty items.
    `items_sha256=None` reproduces a pre-S35.4 legacy event.
    """
    event = {
        "operation": "resolve-evidence-review",
        "evidence_id": evidence_id,
        "decision": decision,
        "reason": "PI decided",
        "timestamp": timestamp,
        **extra,
    }
    if items_sha256 is not None:
        event["items_sha256"] = items_sha256
    return event


def test_block_canonical_text_excises_anchor_and_marker() -> None:
    canonical = state._block_canonical_text_from_text(CONTENT, BLOCK_REF)

    assert canonical == "An implicit synthesis claim."
    assert state._block_text_sha256_from_text(CONTENT, BLOCK_REF) == (
        "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    )


def test_block_canonical_text_returns_none_for_unresolvable_ref() -> None:
    assert state._block_canonical_text_from_text(CONTENT, "draft.md#^blk-99999999") is None
    assert state._block_text_sha256_from_text(CONTENT, "draft.md#^blk-99999999") is None


# --- V2R-B.2: pure evidence-set queue, facets, and filters --------------------


def test_queue_is_evidence_set_only_and_uses_v2_grounds() -> None:
    queue = _queue()

    assert [entry["kind"] for entry in queue] == ["evidence-set"] * 4
    assert [entry["evidence_id"] for entry in queue] == [EV_OPEN, EV_SPAN, EV_CODE, EV_HOP]
    # Raw `items` are the v2 reference strings the marker carries, verbatim.
    assert queue[2]["items"] == [CODE_ITEM]
    assert queue[3]["items"] == ["ev-11111111", "source-beta#^p0002"]
    # The SRD union left the pure assembler: only the collector unions SRD cards.
    with pytest.raises(TypeError, match="srd_cards"):
        evidence_review.assemble_evidence_review_queue(
            _drafts(),
            [],
            srd_cards=[{"id": "inbox_srd-gap.md", "kind": "card"}],
            today=TODAY,
        )


def test_queue_row_carries_the_binding_evidence_set_fields() -> None:
    queue = _queue()

    assert queue[0] == {
        "kind": "evidence-set",
        "evidence_id": EV_OPEN,
        "project_path": ALPHA,
        "draft_path": "projects/project-alpha/draft.md",
        "block_ref": BLOCK_REF,
        "claim_text": "An implicit synthesis claim.",
        "items": [],
        "item_count": 0,
        "evidence_type": "implicit",
        "routing_type": "implicit",
        "holds": ["evidence-incomplete", "review-required"],
        "blocked_by": [],
        "reviewable": True,
        "disposition": "open",
        "age_days": None,
    }
    assert queue[3]["project_path"] == BETA
    assert queue[3]["claim_text"] == "A multi-hop claim."
    assert queue[3]["item_count"] == 2


def test_queue_routing_types_follow_type_then_incomplete_state() -> None:
    assert [entry["routing_type"] for entry in _queue()] == [
        "implicit",
        "incomplete",
        "incomplete",
        "multi-hop",
    ]


def test_queue_skips_complete_unflagged_rows() -> None:
    complete = _span_row(completeness_status="complete")

    assert _queue([_draft([complete])]) == []


def test_queue_clears_hold_on_digest_matching_accept() -> None:
    assert _open_queue(dispositions=[_event("accept")]) == []


def test_queue_keeps_hold_when_accept_digest_is_stale() -> None:
    stale = hashlib.sha256(b"old-item#^p0001").hexdigest()

    queue = _open_queue(dispositions=[_event("accept", items_sha256=stale)])

    assert [entry["evidence_id"] for entry in queue] == [EV_OPEN]
    assert queue[0]["disposition"] == "open"


def test_queue_accept_without_digest_is_inert() -> None:
    # Digests form (Plan 22 S35.4 has landed: `_disposed_evidence_digests` is in
    # knowledge.py): a legacy accept with no items_sha256 fails closed.
    queue = _open_queue(dispositions=[_event("accept", items_sha256=None)])

    assert [entry["evidence_id"] for entry in queue] == [EV_OPEN]


def test_queue_accept_digest_matches_the_verify_seam_serialization() -> None:
    # Replica invariant: the queue owns its own accept-clearing rule (V2R-B is
    # independent of V2R-A's verify flip), so its digest serialization must stay
    # byte-identical to the seam that writes the events it reads.
    items = ["source-alpha#^p0001", "ev-11111111"]

    assert evidence_review._items_sha256(items) == knowledge._evidence_items_sha256(items)

    row = _span_row(items=items)
    digest = knowledge._evidence_items_sha256(items)

    assert (
        _queue([_draft([row])], [_event("accept", evidence_id=EV_SPAN, items_sha256=digest)]) == []
    )


def test_queue_accept_clearing_leaves_a_permanently_blocked_row_queued() -> None:
    drifted = CONTENT.replace("An implicit synthesis claim.", "A silently edited claim.")

    queue = _queue([_draft([_row()], drifted)], [_event("accept")])

    assert [entry["evidence_id"] for entry in queue] == [EV_OPEN]
    assert queue[0]["holds"] == []
    assert queue[0]["reviewable"] is False
    assert queue[0]["cure"] == evidence_review.PERMANENT_BLOCK_CURE


def test_queue_keeps_rejected_row_rendered_rejected() -> None:
    queue = _open_queue(dispositions=[_event("reject")])

    assert len(queue) == 1
    assert queue[0]["disposition"] == "rejected"
    assert queue[0]["disposition_reason"] == "PI decided"
    assert queue[0]["reviewable"] is True


def test_queue_omits_disposition_reason_when_the_reject_carried_none() -> None:
    # `resolve_evidence_review` stores `reason.strip()`, so a bare reject writes "".
    queue = _open_queue(dispositions=[_event("reject", reason="")])

    assert queue[0]["disposition"] == "rejected"
    assert "disposition_reason" not in queue[0]


def test_queue_keeps_the_accept_warrant_on_a_row_a_stale_digest_returned() -> None:
    stale = hashlib.sha256(b"old-item#^p0001").hexdigest()

    queue = _open_queue(
        dispositions=[_event("accept", items_sha256=stale, warrant="grounded in fig 3")]
    )

    assert queue[0]["warrant"] == "grounded in fig 3"
    assert "warrant" not in _open_queue(dispositions=[_event("reject")])


def test_queue_suppresses_deferred_row_until_next_utc_day() -> None:
    same_day = _open_queue(dispositions=[_event("defer", timestamp="2026-07-16T00:00:00Z")])
    day_end = _open_queue(dispositions=[_event("defer", timestamp="2026-07-16T23:59:59Z")])
    yesterday = _open_queue(dispositions=[_event("defer", timestamp="2026-07-15T23:59:59Z")])

    assert same_day == []
    assert day_end == []
    assert [entry["evidence_id"] for entry in yesterday] == [EV_OPEN]
    assert yesterday[0]["disposition"] == "open"


def test_queue_shows_a_defer_whose_journal_timestamp_cannot_be_read() -> None:
    # Honesty doctrine: an unparsable journal timestamp is not a suppression
    # clock, and the queue shows the row rather than silently hiding it.
    queue = _open_queue(dispositions=[_event("defer", timestamp="")])

    assert [entry["evidence_id"] for entry in queue] == [EV_OPEN]


def test_queue_latest_disposition_wins() -> None:
    deferred_then_rejected = _open_queue(
        dispositions=[
            _event("defer", timestamp="2026-07-16T01:00:00Z"),
            _event("reject", timestamp="2026-07-16T02:00:00Z"),
        ]
    )
    accepted_then_rejected = _open_queue(
        dispositions=[
            _event("accept", timestamp="2026-07-16T01:00:00Z"),
            _event("reject", timestamp="2026-07-16T02:00:00Z"),
        ]
    )

    assert [entry["disposition"] for entry in deferred_then_rejected] == ["rejected"]
    assert [entry["disposition"] for entry in accepted_then_rejected] == ["rejected"]


def test_queue_dispositions_are_matched_per_evidence_id() -> None:
    queue = _queue(dispositions=[_event("accept", evidence_id=EV_OPEN)])

    assert [entry["evidence_id"] for entry in queue] == [EV_SPAN, EV_CODE, EV_HOP]


def test_queue_renders_drifted_row_read_only_with_reason_and_cure() -> None:
    drifted = CONTENT.replace("An implicit synthesis claim.", "A silently edited claim.")

    queue = _queue([_draft([_row()], drifted)])

    assert len(queue) == 1
    entry = queue[0]
    assert entry["reviewable"] is False
    assert entry["blocked_by"] == [
        {
            "kind": "evidence-text-drift",
            "reason": "anchored block text differs from its stored binding",
        }
    ]
    # The cure is PI-facing copy: pin the words, not the constant that holds them.
    assert entry["cure"] == evidence_review.PERMANENT_BLOCK_CURE
    assert entry["cure"] == (
        "edit the draft or the grounds; no disposition clears a permanent block"
    )
    assert entry["holds"] == ["evidence-incomplete", "review-required"]
    assert entry["claim_text"] == "A silently edited claim."


def test_queue_renders_unbound_rows_read_only_with_both_reasons() -> None:
    missing = _queue([_draft([_row(block_text_sha256=None)])])
    unresolvable = _queue(
        [_draft([_row(block_ref="projects/project-alpha/draft.md#^blk-99999999")])]
    )

    assert missing[0]["reviewable"] is False
    assert missing[0]["blocked_by"] == [
        {"kind": "evidence-text-unbound", "reason": "stored block-text binding is missing"}
    ]
    assert unresolvable[0]["blocked_by"] == [
        {"kind": "evidence-text-unbound", "reason": "anchored block text cannot be resolved"}
    ]
    assert unresolvable[0]["claim_text"] == ""
    assert missing[0]["cure"] == unresolvable[0]["cure"] == evidence_review.PERMANENT_BLOCK_CURE


def test_queue_omits_cure_from_rows_that_are_not_permanently_blocked() -> None:
    assert all("cure" not in entry for entry in _queue())


def test_queue_findings_restate_the_verify_seam_reason_strings() -> None:
    # Replica invariant: the read-only queue is a second implementation of
    # verify_project_draft's permanent-block reasons (spec GAP — a GET view
    # cannot run the writer seam). Drift in either wording makes one surface lie.
    source = Path(knowledge.__file__).read_text(encoding="utf-8")
    reasons = sorted(
        finding["reason"]
        for entry in (
            _queue([_draft([_row(block_text_sha256=None)])])
            + _queue([_draft([_row(block_ref=f"{BLOCK_REF[:-8]}99999999")])])
            + _queue([_draft([_row()], CONTENT.replace("An implicit", "A silently edited"))])
        )
        for finding in entry["blocked_by"]
    )

    assert reasons == [
        "anchored block text cannot be resolved",
        "anchored block text differs from its stored binding",
        "stored block-text binding is missing",
    ]
    for reason in reasons:
        assert f'"reason": "{reason}",' in source


def test_queue_age_days_from_minted_timestamp() -> None:
    queue = _open_queue(minted_at={EV_OPEN: "2026-07-13T10:00:00Z"})

    assert queue[0]["age_days"] == 3


def test_queue_age_days_is_null_without_a_minted_event() -> None:
    # The shipped default until plan 22 S68.3 lands: every row reads this way
    # today, so `age_days` must be an honest null, never a fabricated zero.
    assert [entry["age_days"] for entry in _queue()] == [None] * 4
    assert _open_queue(minted_at={})[0]["age_days"] is None


def test_queue_age_days_clamps_a_minted_timestamp_in_the_future() -> None:
    queue = _open_queue(minted_at={EV_OPEN: "2026-07-20T10:00:00Z"})

    assert queue[0]["age_days"] == 0


def test_queue_passes_through_present_only_analysis_inputs() -> None:
    row = _row(
        argument_for="the synthesis is well supported",
        argument_against="the hop chain is long",
        certainty="low",
    )

    entry = _queue([_draft([row])])[0]

    assert entry["argument_for"] == "the synthesis is well supported"
    assert entry["argument_against"] == "the hop chain is long"
    assert entry["certainty"] == "low"
    assert not {"argument_for", "argument_against", "certainty"} & set(_queue()[0])


def test_queue_facets_are_evidence_denominators_only() -> None:
    facets = evidence_review.queue_facets(_queue())

    assert facets == {
        "routing_type": {"implicit": 1, "incomplete": 2, "multi-hop": 1},
        "project": {ALPHA: 3, BETA: 1},
        "total": 4,
    }
    assert "kind" not in facets


def test_queue_facets_omit_an_unrouted_row_from_the_routing_denominator() -> None:
    # A complete, unflagged row that drifted is permanently blocked with no
    # routing type: it is a real read-only queue row and a real facet total,
    # but it belongs to no routing bucket.
    drifted = CONTENT.replace("A single-span claim.", "A silently edited claim.")
    queue = _queue([_draft([_span_row(completeness_status="complete")], drifted)])

    assert queue[0]["routing_type"] == ""
    assert evidence_review.queue_facets(queue) == {
        "routing_type": {},
        "project": {ALPHA: 1},
        "total": 1,
    }


def test_filter_queue_normalizes_the_three_project_spellings() -> None:
    queue = _queue()

    for spelling in ("project-alpha", "projects/project-alpha", ALPHA):
        assert [
            entry["evidence_id"] for entry in evidence_review.filter_queue(queue, project=spelling)
        ] == [
            EV_OPEN,
            EV_SPAN,
            EV_CODE,
        ]
    assert [
        entry["evidence_id"]
        for entry in evidence_review.filter_queue(queue, project="project-beta")
    ] == [EV_HOP]


def test_filter_queue_rejects_invalid_project_and_negative_age() -> None:
    queue = _queue()

    for spelling in (
        "projects/project-alpha/draft.md",
        "project-alpha/project.md",
        "projects/project-alpha/",
        "projects/",
        "..",
    ):
        with pytest.raises(ValueError, match="project"):
            evidence_review.filter_queue(queue, project=spelling)
    with pytest.raises(ValueError, match="min_age_days"):
        evidence_review.filter_queue(queue, min_age_days=-1)
    with pytest.raises(ValueError, match="routing_type"):
        evidence_review.filter_queue(queue, routing_type="bogus")


def test_filter_queue_accepts_only_the_three_routing_types() -> None:
    assert evidence_review.EVIDENCE_REVIEW_ROUTING_TYPES == ("implicit", "multi-hop", "incomplete")

    queue = _queue()

    assert [
        entry["evidence_id"]
        for entry in evidence_review.filter_queue(queue, routing_type="implicit")
    ] == [EV_OPEN]
    assert [
        entry["evidence_id"]
        for entry in evidence_review.filter_queue(queue, routing_type="incomplete")
    ] == [EV_SPAN, EV_CODE]
    assert [
        entry["evidence_id"]
        for entry in evidence_review.filter_queue(queue, routing_type="multi-hop")
    ] == [EV_HOP]


def test_filter_queue_applies_every_active_facet_conjunctively() -> None:
    queue = _queue(minted_at={EV_SPAN: "2026-07-13T10:00:00Z", EV_HOP: "2026-07-01T10:00:00Z"})

    assert [
        entry["evidence_id"]
        for entry in evidence_review.filter_queue(
            queue, routing_type="incomplete", project="project-alpha", min_age_days=3
        )
    ] == [EV_SPAN]
    # Each facet alone keeps a strictly larger set — the intersection is the point.
    assert len(evidence_review.filter_queue(queue, routing_type="incomplete")) == 2
    assert len(evidence_review.filter_queue(queue, project="project-alpha")) == 3
    assert len(evidence_review.filter_queue(queue, min_age_days=3)) == 2


def test_filter_queue_treats_an_unknown_age_as_zero() -> None:
    # Pre-S68.3 every row has `age_days: None`; a min-age filter must exclude
    # them rather than count a null as infinitely old.
    queue = _queue(minted_at={EV_SPAN: "2026-07-13T10:00:00Z"})

    assert evidence_review.filter_queue(queue, min_age_days=0) == queue
    assert [
        entry["evidence_id"] for entry in evidence_review.filter_queue(queue, min_age_days=1)
    ] == [EV_SPAN]


def test_filter_queue_copies_rows_instead_of_aliasing_the_queue() -> None:
    queue = _queue()

    filtered = evidence_review.filter_queue(queue, routing_type="implicit")
    filtered[0]["disposition"] = "tampered"

    assert queue[0]["disposition"] == "open"


# --- V2R-B.3: nested evidence-review cards and grounds previews ---------------

SPAN_PREVIEW = {
    "ref": "source-beta#^p0002",
    "kind": "source-span",
    "work_id": "source-beta",
    "anchor": "^p0002",
    "resolves": True,
    "excerpt": "A beta source span.",
}
UNRESOLVED_PREVIEW = {
    "ref": "source-alpha#^p9999",
    "kind": "source-span",
    "work_id": "source-alpha",
    "anchor": "^p9999",
    "resolves": False,
}


def _srd_card(name: str) -> dict[str, Any]:
    return {
        "id": f"inbox_{name}.md",
        "kind": "card",
        "ref": f"inbox/{name}.md",
        "kind_line": "srd-gap",
        "blocks": [],
    }


def _reviewable_row(**overrides: Any) -> dict[str, Any]:
    """The multi-hop beta queue row with its shown-row previews attached."""
    row = _queue([_draft([_hop_row()], BETA_CONTENT, "project-beta")])[0]
    row["item_previews"] = [dict(SPAN_PREVIEW)]
    row.update(overrides)
    return row


def test_evidence_review_card_has_ordered_nested_semantic_children() -> None:
    row = _reviewable_row()
    row["age_days"] = 3

    card = evidence_review.evidence_review_card(row)
    children = card.pop("blocks")

    assert card == {
        "id": EV_HOP,
        "kind": "card",
        "ref": HOP_BLOCK_REF,
        "title": "A multi-hop claim.",
        "kind_line": "evidence-review",
        "review_kind": "evidence-set",
        "evidence_id": EV_HOP,
        "project": BETA,
        "routing_type": "multi-hop",
        "reviewable": True,
        "disposition": "open",
        "item_count": 2,
        "age_days": 3,
        "age_s": 3 * 86_400,
        "age_label": "3d",
        "body_data": {"kind": "untrusted_text", "text": "A multi-hop claim."},
        "tipped_by": "type=multi-hop",
    }
    assert children == [
        {
            "id": f"{EV_HOP}-grounds",
            "kind": "evidence-list",
            "ref": HOP_BLOCK_REF,
            "items": [SPAN_PREVIEW],
        },
        {"id": f"{EV_HOP}-routing", "kind": "text", "text": "multi-hop"},
        {
            "id": f"{EV_HOP}-actions",
            "kind": "action-row",
            "actions": [
                {
                    "label": "Accept",
                    "operation_id": "resolve-evidence",
                    "payload": {"evidence_id": EV_HOP, "decision": "accept"},
                },
                {
                    "label": "Reject",
                    "operation_id": "resolve-evidence",
                    "payload": {"evidence_id": EV_HOP, "decision": "reject"},
                },
                {
                    "label": "Edit",
                    "operation_id": "resolve-evidence",
                    "payload": {"evidence_id": EV_HOP, "decision": "edit"},
                },
                {
                    "label": "Defer",
                    "operation_id": "resolve-evidence",
                    "payload": {"evidence_id": EV_HOP, "decision": "defer"},
                },
            ],
        },
    ]
    # Spec §2 field 7: no pre-selected action, and no verdict anywhere.
    assert all("primary" not in action for action in children[2]["actions"])
    assert "verdict" not in card


def test_evidence_review_card_carries_parent_owned_analysis_for_holds() -> None:
    row = _reviewable_row(
        argument_for="the synthesis is well supported",
        argument_against="the hop chain is long",
        certainty="low",
    )

    card = evidence_review.evidence_review_card(row)

    assert card["argument_for"] == "the synthesis is well supported"
    assert card["argument_against"] == "the hop chain is long"
    assert card["tipped_by"] == "type=multi-hop"
    assert card["certainty"] == "low"
    # The retired flat analysis card and its field names are gone for good.
    assert [child["kind"] for child in card["blocks"]] == ["evidence-list", "text", "action-row"]
    assert "what_tipped_it" not in card
    assert "collapsed" not in card


def test_evidence_review_card_drops_one_sided_arguments() -> None:
    one_sided = evidence_review.evidence_review_card(
        _reviewable_row(argument_for="the synthesis is well supported")
    )
    other_side = evidence_review.evidence_review_card(
        _reviewable_row(argument_against="the hop chain is long")
    )

    assert "argument_for" not in one_sided
    assert "argument_against" not in one_sided
    assert "argument_for" not in other_side
    assert "argument_against" not in other_side


def test_evidence_review_cure_card_omits_actions_and_analysis() -> None:
    drifted = CONTENT.replace("An implicit synthesis claim.", "A silently edited claim.")
    row = _queue(
        [
            _draft(
                [
                    _row(
                        argument_for="the synthesis is well supported",
                        argument_against="the hop chain is long",
                        certainty="low",
                    )
                ],
                drifted,
            )
        ]
    )[0]
    row["item_previews"] = [dict(UNRESOLVED_PREVIEW)]

    card = evidence_review.evidence_review_card(row)

    # A permanently blocked row still carries holds and analysis inputs; none of
    # them may reach the card, and it offers no disposition to make.
    assert row["holds"] == ["evidence-incomplete", "review-required"]
    assert [child["kind"] for child in card["blocks"]] == ["evidence-list", "text"]
    assert card["reviewable"] is False
    assert card["cure"] == evidence_review.PERMANENT_BLOCK_CURE
    assert card["blocked_by"] == [
        {
            "kind": "evidence-text-drift",
            "reason": "anchored block text differs from its stored binding",
        }
    ]
    assert not {"argument_for", "argument_against", "tipped_by", "certainty"} & set(card)


def test_evidence_review_card_age_fields_are_honest_when_age_is_unknown() -> None:
    # Pre-S68.3 this is every row: `age_days` is null, so the derived seconds
    # are zero and the label is empty rather than a fabricated "0d".
    card = evidence_review.evidence_review_card(_reviewable_row())

    assert card["age_days"] is None
    assert card["age_s"] == 0
    assert card["age_label"] == ""


def test_evidence_review_card_carries_present_only_disposition_fields() -> None:
    rejected = _queue([_draft([_row()])], [_event("reject")])[0]
    accepted_stale = _queue(
        [_draft([_row()])],
        [
            _event(
                "accept",
                items_sha256=hashlib.sha256(b"old").hexdigest(),
                warrant="grounded in fig 3",
            )
        ],
    )[0]

    rejected_card = evidence_review.evidence_review_card(rejected)
    accepted_card = evidence_review.evidence_review_card(accepted_stale)

    assert rejected_card["disposition"] == "rejected"
    assert rejected_card["disposition_reason"] == "PI decided"
    assert "warrant" not in rejected_card
    assert accepted_card["warrant"] == "grounded in fig 3"
    assert "disposition_reason" not in accepted_card
    assert "cure" not in accepted_card
    assert "blocked_by" not in accepted_card


def test_evidence_review_card_consumes_queue_facts_instead_of_restating_them() -> None:
    # B.3 re-shapes a row; it never recomputes or restates a queue fact. The
    # count comes from the row (so a projection whose `items` were replaced by
    # previews still reports the assembled grounds count), and the cure comes
    # from the row (so a future per-finding cure reaches the card unchanged).
    row = _reviewable_row()
    del row["items"]
    row["blocked_by"] = [{"kind": "evidence-text-drift", "reason": "edited"}]
    row["cure"] = "restore the block text or rebind the grounds"

    card = evidence_review.evidence_review_card(row)

    assert card["item_count"] == 2
    assert card["cure"] == "restore the block text or rebind the grounds"


def test_evidence_review_blocks_puts_srd_cards_after_every_evidence_card() -> None:
    rows: list[dict[str, Any]] = [
        {"kind": "srd-gap", "card_block": _srd_card("gap-one")},
        *_queue(),
        {"kind": "srd-gap", "card_block": _srd_card("gap-two")},
    ]

    blocks = evidence_review.evidence_review_blocks(rows)

    assert [block["id"] for block in blocks] == [
        EV_OPEN,
        EV_SPAN,
        EV_CODE,
        EV_HOP,
        "inbox_gap-one.md",
        "inbox_gap-two.md",
    ]
    assert [block["kind"] for block in blocks] == ["card"] * 6
    assert blocks[4] == _srd_card("gap-one")
    # SRD cards arrive already normalized: passed through, never re-derived.
    assert "attention_kind" not in blocks[4]
    assert blocks[4]["kind_line"] == "srd-gap"

    blocks[4]["kind_line"] = "tampered"
    assert rows[0]["card_block"]["kind_line"] == "srd-gap"


def test_evidence_review_blocks_projects_every_evidence_row_once() -> None:
    blocks = evidence_review.evidence_review_blocks(_queue())

    assert len(blocks) == 4
    assert [block["kind_line"] for block in blocks] == ["evidence-review"] * 4
    assert [block["review_kind"] for block in blocks] == ["evidence-set"] * 4
    assert [block["project"] for block in blocks] == [ALPHA, ALPHA, ALPHA, BETA]


def test_routing_reason_names_the_first_unresolved_grounds_item() -> None:
    row = _queue()[1]
    row["item_previews"] = [dict(SPAN_PREVIEW), dict(UNRESOLVED_PREVIEW)]

    assert row["routing_type"] == "incomplete"
    assert evidence_review.routing_reason(row, row["item_previews"]) == (
        "evidence-incomplete: source-alpha#^p9999 does not resolve"
    )
    assert (
        evidence_review.evidence_review_card(row)["blocks"][1]["text"]
        == "evidence-incomplete: source-alpha#^p9999 does not resolve"
    )


def test_routing_reason_falls_back_when_no_previews_were_attached() -> None:
    # The collector attaches previews to shown rows only, so an incomplete row
    # can reach this pure helper without any: name the routing, not a ref.
    row = _queue()[1]

    assert evidence_review.routing_reason(row, []) == "evidence-incomplete"


def test_routing_reason_restates_the_block_for_a_permanently_blocked_row() -> None:
    # A complete, unflagged row that drifted has no routing type at all; its
    # only honest reason is the permanent block itself.
    drifted = CONTENT.replace("A single-span claim.", "A silently edited claim.")
    row = _queue([_draft([_span_row(completeness_status="complete")], drifted)])[0]

    assert row["routing_type"] == ""
    assert evidence_review.routing_reason(row, []) == (
        "anchored block text differs from its stored binding"
    )
    assert evidence_review.evidence_review_card(row)["blocks"][1]["text"] == (
        "anchored block text differs from its stored binding"
    )


def test_routing_reason_is_empty_for_an_unrouted_unblocked_row() -> None:
    # No queue producer emits this (review_required is derived as
    # `type in {implicit, multi-hop}`), but the helper is public and total.
    assert evidence_review.routing_reason({"routing_type": "", "blocked_by": []}, []) == ""


def test_routing_reason_names_each_routing_type_verbatim() -> None:
    assert evidence_review.routing_reason(_queue()[0], []) == "implicit"
    assert evidence_review.routing_reason(_queue()[3], []) == "multi-hop"


def test_analysis_fields_are_empty_without_a_reviewable_hold() -> None:
    drifted = CONTENT.replace("An implicit synthesis claim.", "A silently edited claim.")
    blocked = _queue([_draft([_row(certainty="low")], drifted)])[0]
    # No queue producer decouples these two (reviewable implies holds), so the
    # holds half is pinned at the public helper's boundary.
    without_holds = {**_queue()[0], "holds": [], "certainty": "low"}

    assert evidence_review.analysis_fields(blocked, []) == {}
    assert evidence_review.analysis_fields(without_holds, []) == {}


def test_analysis_fields_name_the_unresolved_item_as_the_tipping_factor() -> None:
    row = _queue()[1]

    assert evidence_review.analysis_fields(row, [dict(UNRESOLVED_PREVIEW)]) == {
        "tipped_by": "source-alpha#^p9999"
    }
    # Without attached previews the honest factor is the completeness status, not a ref.
    assert evidence_review.analysis_fields(row, []) == {
        "tipped_by": "completeness_status=evidence-incomplete"
    }
