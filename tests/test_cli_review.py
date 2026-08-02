"""Contract tests for the `memoria review` CLI cockpit (V2R-C).

The CLI front is engine-direct (spec §8 keep-test): it reads
`engine_api.evidence_review_queue` and projects raw rows for display. It never
requests the HTTP view, never reassembles a queue, and never renames a raw
field — `routing_type` and `disposition` are the only spellings (2026-07-29
raw-queue amendment §3).

The seed is one vault carrying every routing outcome, a permanently blocked
read-only row that also holds the warrant it was accepted under, a rejected
row, two projects and two open SRD gaps — all built by product code
(`compose_project_draft` mints the markers, `verify_project_draft` rebuilds
them), so a one-row queue never stands in for a list.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from memoria_vault.cli import main
from memoria_vault.engine import api as engine_api
from memoria_vault.runtime import evidence_review, state
from memoria_vault.runtime.knowledge import compose_project_draft as _compose
from memoria_vault.runtime.knowledge import resolve_evidence_review as _resolve
from memoria_vault.runtime.knowledge import verify_project_draft as _verify
from tests.helpers import call_with_context, write_checked_concept

ALPHA = "projects/project-alpha/project.md"
BETA = "projects/project-beta/project.md"

# notes/<stem>.md -> outline id. Ordered: the outline drives compose order.
NOTE_IDS = {
    "thesis": "01ARZ3NDEKTSV4RRFFQ69G5FA1",
    "support": "01ARZ3NDEKTSV4RRFFQ69G5FA2",
    "dangling": "01ARZ3NDEKTSV4RRFFQ69G5FA3",
    "hop": "01ARZ3NDEKTSV4RRFFQ69G5FA4",
    "blocked-reject": "01ARZ3NDEKTSV4RRFFQ69G5FA5",
    "beta-thesis": "01ARZ3NDEKTSV4RRFFQ69G5FA6",
}
DRIFTED = "A complete source-backed claim."
REJECTED_DRIFT = "A second complete source-backed claim."
# Two soft-wrapped lines in one markdown block: a claim is not a line.
DANGLING = "A claim over a span\nthat never resolves."
# Exactly the summary column width, so the elision boundary has a producer.
HOP_CLAIM = "A dependent multi-hop claim that just fits the column width."
LONG_CLAIM = "A second project's implicit claim that runs well past the summary column width."
WARRANT = "Institutional cost data warrants this synthesis."


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


def _project(vault: Path, name: str) -> None:
    write_checked_concept(
        vault,
        f"projects/{name}/project.md",
        f"type: project\ncheck_status: checked\ntitle: {name}\n",
        "project",
    )


def _outline(vault: Path, name: str, stems: list[str]) -> None:
    path = vault / f"projects/{name}/outline.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"- {NOTE_IDS[stem]} — {stem}\n" for stem in stems), encoding="utf-8")


def _srd_gap(vault: Path, name: str, *, status: str = "open") -> None:
    path = vault / f"inbox/{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "projection: attention\n"
        f"title: {name} title\n"
        "attention_kind: srd-gap\n"
        f"attention_status: {status}\n"
        "routing_class: ask\n"
        "loudness: notice\n"
        "target: projects/project-alpha/draft.md\n"
        "---\n"
        f"{name} body.\n",
        encoding="utf-8",
    )


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


def _build_review_vault(vault: Path) -> dict[str, str]:
    """Every list variant in one vault: four routing outcomes, two projects, a
    reviewable rejected row, a blocked rejected row, a warranted read-only row,
    and two open SRD gaps."""
    _source(vault, "source-alpha", "source-alpha source span. ^p0001\n")
    _source(vault, "source-missing")

    stems = ["thesis", "support", "dangling", "hop", "blocked-reject"]
    _project(vault, "project-alpha")
    _note(vault, "thesis", "An implicit synthesis claim.")
    _note(vault, "support", DRIFTED, extra="work_id: catalog/sources/source-alpha\n")
    _note(vault, "dangling", DANGLING, extra="work_id: catalog/sources/source-missing\n")
    _note(vault, "hop", HOP_CLAIM)
    _note(
        vault,
        "blocked-reject",
        REJECTED_DRIFT,
        extra="work_id: catalog/sources/source-alpha\n",
    )
    _outline(vault, "project-alpha", stems)
    call_with_context(_compose, vault, "project-alpha")
    ids = _ids_by_note(vault, "project-alpha", stems)

    # Only a marker edit plus a verify rebuild produces nested grounds: compose
    # derives items from notes. Marker items are `|`-separated, never commas.
    draft = vault / "projects/project-alpha/draft.md"
    text = draft.read_text(encoding="utf-8")
    assert f"%%ev: {ids['hop']} items=%%" in text
    draft.write_text(
        text.replace(f"%%ev: {ids['hop']} items=%%", f"%%ev: {ids['hop']} items={ids['thesis']}%%"),
        encoding="utf-8",
    )
    call_with_context(_verify, vault, "project-alpha")

    _project(vault, "project-beta")
    _note(vault, "beta-thesis", LONG_CLAIM)
    _outline(vault, "project-beta", ["beta-thesis"])
    call_with_context(_compose, vault, "project-beta")
    ids |= _ids_by_note(vault, "project-beta", ["beta-thesis"])

    # Three disposed rows, so neither `disposition` nor `warrant` is read from
    # an unfixtured default, and read-only outranks rejected on the one row that
    # is both. The accept clears `support`'s holds; the drift below re-raises it
    # permanently blocked, still carrying its warrant — the only way a queued
    # row shows one, since a cleared accept otherwise leaves the queue.
    _resolve(vault, ids["hop"], actor="pi", machine="test", decision="reject", reason="thin")
    _resolve(
        vault, ids["blocked-reject"], actor="pi", machine="test", decision="reject", reason="thin"
    )
    _resolve(vault, ids["support"], actor="pi", machine="test", decision="accept", warrant=WARRANT)

    # Drift last: the stored binding must already exist for the edit to break it.
    text = draft.read_text(encoding="utf-8")
    for claim in (DRIFTED, REJECTED_DRIFT):
        text = text.replace(claim, f"{claim} Silently edited.")
    draft.write_text(text, encoding="utf-8")

    _srd_gap(vault, "srd-gap-alpha")
    _srd_gap(vault, "srd-gap-beta")
    _srd_gap(vault, "srd-gap-done", status="resolved")
    return ids


@pytest.fixture(scope="module")
def _review_template(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, str]]:
    root = tmp_path_factory.mktemp("cli-review-template")
    vault = root / "vault"
    vault.mkdir()
    return vault, _build_review_vault(vault)


@pytest.fixture
def review_vault(tmp_path: Path, _review_template) -> tuple[Path, dict[str, str]]:
    """A private copy of the module-scoped seed: composing it costs seconds."""
    template, ids = _review_template
    vault = tmp_path / "vault"
    shutil.copytree(template, vault, symlinks=True)
    return vault, dict(ids)


def _payload(capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    return json.loads(capsys.readouterr().out)


def _by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row["evidence_id"]): row for row in payload["rows"] if row["kind"] == "evidence-set"
    }


def test_review_list_projects_raw_names_and_strips_items_and_analysis(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """The summary carries exactly the raw-queue amendment §3 field set.

    `routing_type`/`disposition` are the only spellings, `project` is the
    presentation name for `project_path`, and neither raw `items` nor any
    analysis field reaches a list row.
    """
    vault, ids = review_vault

    rc = main(["review", "list", "--workspace", str(vault), "--json"])
    payload = _payload(capsys)

    assert rc == 0
    assert payload["ok"] is True
    assert payload["batch"] == 10
    rows = _by_id(payload)
    assert rows[ids["thesis"]] == {
        "kind": "evidence-set",
        "evidence_id": ids["thesis"],
        "claim_text": "An implicit synthesis claim.",
        "item_count": 0,
        "routing_type": "implicit",
        "routing_reason": "implicit",
        "reviewable": True,
        "project": ALPHA,
        "age_days": 0,
        "disposition": "open",
    }
    for row in rows.values():
        assert {"items", "item_previews", "analysis", "argument_for", "tipped_by"}.isdisjoint(row)
        assert {"latest_decision", "routing", "project_path"}.isdisjoint(row)


def test_review_list_renders_every_routing_outcome_and_the_cure_row(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """Four rows, four routing outcomes — a one-row queue proves none of this,
    and only the `routing_type == ""` row surfaces a block reason."""
    vault, ids = review_vault

    rc = main(["review", "list", "--workspace", str(vault), "--json"])
    rows = _by_id(_payload(capsys))

    assert rc == 0
    assert rows[ids["thesis"]]["routing_type"] == "implicit"
    assert rows[ids["hop"]]["routing_type"] == "multi-hop"
    assert rows[ids["hop"]]["item_count"] == 1
    dangling = rows[ids["dangling"]]
    assert dangling["routing_type"] == "incomplete"
    assert (
        dangling["routing_reason"] == "evidence-incomplete: source-missing#^p0001 does not resolve"
    )
    blocked = rows[ids["support"]]
    assert blocked["routing_type"] == ""
    assert blocked["reviewable"] is False
    assert blocked["routing_reason"] == "anchored block text differs from its stored binding"
    assert blocked["cure"] == evidence_review.PERMANENT_BLOCK_CURE
    # Present-only: a reviewable row names no cure it does not need.
    assert "cure" not in rows[ids["thesis"]]


def test_review_list_carries_disposition_and_warrant_from_the_seam(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """`disposition` and present-only `warrant` are the seam's facts, read
    through the queue — the rejected row renders rejected (spec §4)."""
    vault, ids = review_vault

    rc = main(["review", "list", "--workspace", str(vault), "--json"])
    rows = _by_id(_payload(capsys))

    assert rc == 0
    assert rows[ids["hop"]]["disposition"] == "rejected"
    assert rows[ids["blocked-reject"]]["disposition"] == "rejected"
    assert rows[ids["thesis"]]["disposition"] == "open"
    assert "warrant" not in rows[ids["thesis"]]
    # An accept that cleared its holds leaves the queue; this row came back
    # permanently blocked, so the warrant it was accepted under is still true.
    assert rows[ids["support"]]["warrant"] == WARRANT
    assert rows[ids["support"]]["disposition"] == "open"


def test_review_list_srd_gaps_are_read_only_summaries_after_evidence(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """The discriminated union survives the projection: an SRD gap renders by
    its normalized card's title/ref and carries no evidence field to act on.
    A resolved gap is not review work."""
    vault, _ids = review_vault

    rc = main(["review", "list", "--workspace", str(vault), "--json"])
    payload = _payload(capsys)

    assert rc == 0
    assert [row["kind"] for row in payload["rows"]] == ["evidence-set"] * 6 + ["srd-gap"] * 2
    assert payload["rows"][-2:] == [
        {"kind": "srd-gap", "title": "srd-gap-alpha title", "ref": "inbox/srd-gap-alpha.md"},
        {"kind": "srd-gap", "title": "srd-gap-beta title", "ref": "inbox/srd-gap-beta.md"},
    ]
    assert payload["total"] == 8


def test_review_list_type_facet_filters_rows_but_not_the_denominators(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """Filtered `total` versus whole-scope `facet_totals` (spec §6), and a
    filtered queue appends no SRD gap it never considered."""
    vault, ids = review_vault

    rc = main(["review", "list", "--workspace", str(vault), "--type", "multi-hop", "--json"])
    payload = _payload(capsys)

    assert rc == 0
    assert [row["evidence_id"] for row in payload["rows"]] == [ids["hop"]]
    assert payload["total"] == 1
    assert payload["facet_totals"] == {
        "routing_type": {"implicit": 2, "multi-hop": 1, "incomplete": 1},
        "project": {ALPHA: 5, BETA: 1},
        "total": 6,
    }


def test_review_list_project_facet_accepts_the_bare_name(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    vault, ids = review_vault

    rc = main(["review", "list", "--workspace", str(vault), "--project", "project-beta", "--json"])
    payload = _payload(capsys)

    assert rc == 0
    assert [row["evidence_id"] for row in payload["rows"]] == [ids["beta-thesis"]]
    assert [row["kind"] for row in payload["rows"]] == ["evidence-set"]


def test_review_list_min_age_days_filters_on_the_queue_age(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """Every seeded row was minted today, so a one-day floor empties the queue
    while leaving the whole-scope denominators intact."""
    vault, _ids = review_vault

    rc = main(["review", "list", "--workspace", str(vault), "--min-age-days", "1", "--json"])
    payload = _payload(capsys)

    assert rc == 0
    assert payload["rows"] == []
    assert payload["total"] == 0
    assert payload["facet_totals"]["total"] == 6


def test_review_list_batch_caps_evidence_rows_with_an_honest_total(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """Batch caps evidence only; `total` still counts the whole filtered union."""
    vault, _ids = review_vault

    rc = main(["review", "list", "--workspace", str(vault), "--batch", "2", "--json"])
    payload = _payload(capsys)

    assert rc == 0
    assert [row["kind"] for row in payload["rows"]] == ["evidence-set"] * 2 + ["srd-gap"] * 2
    assert payload["total"] == 8
    assert payload["batch"] == 2

    assert main(["review", "list", "--workspace", str(vault), "--batch", "2"]) == 0
    # The footer is the only place the human front says what it withheld, so
    # shown and total must be two different numbers here.
    assert capsys.readouterr().out.splitlines()[-1] == "4 of 8 row(s) shown (batch 2)"


@pytest.mark.parametrize("argv", [["--min-age-days", "-1"], ["--batch", "0"], ["--batch", "-1"]])
def test_review_list_refuses_out_of_range_boundaries(
    review_vault, capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    """CLI boundaries are stricter than the collector: `batch=0` is the
    engine-direct id lookup, never a user-facing contract."""
    vault, _ids = review_vault

    with pytest.raises(SystemExit) as exc:
        main(["review", "list", "--workspace", str(vault), *argv])

    assert exc.value.code == 2
    assert "argument" in capsys.readouterr().err


def test_review_list_reads_the_queue_engine_direct(
    review_vault, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Spec §8 keep-test: no server, no view cards. The CLI must not reach the
    HTTP view projection even though it shares the collector underneath."""
    vault, _ids = review_vault

    def _forbidden(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise AssertionError("the CLI front must never call the view projection")

    monkeypatch.setattr(engine_api, "read_evidence_review_view", _forbidden)

    rc = main(["review", "list", "--workspace", str(vault), "--json"])

    assert rc == 0
    assert _payload(capsys)["total"] == 8


def test_review_list_human_rows_are_one_line_summaries(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """One line per row, evidence facts only — no machine analysis in list
    mode (spec §3); the read-only row names its cure instead of an action, and
    the SRD gap says so without borrowing an evidence column."""
    vault, ids = review_vault

    rc = main(["review", "list", "--workspace", str(vault)])
    lines = capsys.readouterr().out.splitlines()

    assert rc == 0
    assert lines[-1] == "8 of 8 row(s) shown (batch 10)"
    by_key = {line.split("  ")[0]: line for line in lines[:-1]}
    assert by_key[ids["thesis"]] == (
        f"{ids['thesis']}  implicit   0 item(s)  An implicit synthesis claim.  — implicit"
    )
    # Exactly the column width: elided one character shorter and the row is
    # a different row, so the boundary has a producer.
    assert by_key[ids["hop"]] == (
        f"{ids['hop']}  multi-hop  1 item(s)  {HOP_CLAIM}  — multi-hop  [rejected]"
    )
    # A claim is not a line: the soft-wrapped block collapses into one row.
    assert by_key[ids["dangling"]] == (
        f"{ids['dangling']}  incomplete  1 item(s)  A claim over a span that never resolves.  "
        "— evidence-incomplete: source-missing#^p0001 does not resolve"
    )
    cure_marker = f"[read-only: {evidence_review.PERMANENT_BLOCK_CURE}]"
    assert by_key[ids["support"]].startswith(f"{ids['support']}  -          1 item(s)  ")
    assert by_key[ids["support"]].endswith(
        f"— anchored block text differs from its stored binding  {cure_marker}"
    )
    # Read-only outranks rejected: the cure is what the PI can act on.
    assert by_key[ids["blocked-reject"]].endswith(cure_marker)
    assert by_key["inbox/srd-gap-alpha.md"] == (
        "inbox/srd-gap-alpha.md  srd-gap    srd-gap-alpha title  — read-only"
    )
    assert len(lines) == 9  # one line per row, plus the shown/total footer
    assert "argument" not in "\n".join(lines).lower()


def test_review_list_human_row_truncates_a_long_claim_the_json_keeps_verbatim(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """The one-line summary is a lossy projection; the payload is not."""
    vault, ids = review_vault

    rc = main(["review", "list", "--workspace", str(vault)])
    line = next(
        text for text in capsys.readouterr().out.splitlines() if text.startswith(ids["beta-thesis"])
    )
    assert main(["review", "list", "--workspace", str(vault), "--json"]) == 0
    row = _by_id(_payload(capsys))[ids["beta-thesis"]]

    assert rc == 0
    assert f"  {LONG_CLAIM[:59]}…  " in line
    assert LONG_CLAIM not in line
    assert row["claim_text"] == LONG_CLAIM


def test_review_list_quiet_prints_nothing_and_shares_the_json_payload(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--quiet` takes the payload branch, not the human render: the summary
    projection has exactly one producer."""
    vault, _ids = review_vault

    rc = main(["review", "list", "--workspace", str(vault), "--quiet"])

    assert rc == 0
    assert capsys.readouterr().out == ""
