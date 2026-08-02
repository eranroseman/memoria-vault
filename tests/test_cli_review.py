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

`memoria review show` also writes: its `view.opened` client event lands in
`telemetry_events` and nowhere else (I1 T.3; nested-collector amendment §6), so
every telemetry assertion here reads that table and pins the journal plane
byte-for-byte on the same call — the negative half of the claim, taken at the
writer, because a reader-side proof cannot see a writer that also journals.
"""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from memoria_vault.cli import main
from memoria_vault.engine import api as engine_api
from memoria_vault.runtime import evidence_review, knowledge, state
from memoria_vault.runtime.knowledge import compose_project_draft as _compose
from memoria_vault.runtime.knowledge import resolve_evidence_review as _resolve
from memoria_vault.runtime.knowledge import review_dwell_seconds
from memoria_vault.runtime.knowledge import verify_project_draft as _verify
from memoria_vault.runtime.time import utc_z
from tests.helpers import call_with_context, write_checked_concept

pytestmark = pytest.mark.contract

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


def _wide_project(vault: Path, count: int) -> list[str]:
    """`count` implicit rows in one project — deliberately past the default batch."""
    _project(vault, "project-wide")
    outline = []
    for index in range(count):
        note_id = f"01ARZ3NDEKTSV4RRFFQ69G5F{index:02d}"
        write_checked_concept(
            vault,
            f"notes/wide-{index}.md",
            f"type: note\ncheck_status: checked\ntitle: wide {index}\nid: {note_id}\n",
            "note",
            body=f"Wide implicit claim {index}.",
        )
        outline.append(f"- {note_id} — wide {index}\n")
    path = vault / "projects/project-wide/outline.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(outline), encoding="utf-8")
    result = call_with_context(_compose, vault, "project-wide")
    return [str(marker["id"]) for marker in result["evidence_markers"]]


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


def _clock_pinned_at(instant: datetime) -> type[datetime]:
    """A `datetime` whose `now` is `instant`, for code that reads the wall clock.

    `knowledge` calls `datetime.now` in exactly one place -- the dwell
    subtraction -- so this pins that one input and nothing else.
    """

    class _Pinned(datetime):
        @classmethod
        def now(cls, tz: Any = None) -> datetime:
            return instant

    return _Pinned


def _payload(capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    return json.loads(capsys.readouterr().out)


def _by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row["evidence_id"]): row for row in payload["rows"] if row["kind"] == "evidence-set"
    }


def _telemetry_rows(vault: Path) -> list[dict[str, Any]]:
    """Client events where T.3 puts them: the analytics table, not the journal.

    Insertion order, not `ts`: two shows inside one second share a timestamp and
    the `event_id` tiebreak is a random uuid, which ordered them arbitrarily.
    """
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT event_id, event_type, session_id, surface, payload_json"
            " FROM telemetry_events ORDER BY rowid"
        ).fetchall()
    return [dict(row) for row in rows]


def _journal_plane(vault: Path) -> dict[str, Any]:
    """Every byte a journal append would move, so its absence is the assertion.

    This vault already carries a journal (the seam's `resolved` events), so an
    empty-journal proof is unavailable: identity across the call is the claim.
    """
    head = vault / state.JOURNAL_HEAD_REL
    with state.connect(vault) as conn:
        events = [tuple(row) for row in conn.execute("SELECT * FROM event_log ORDER BY event_id")]
    return {
        "event_log": events,
        "jsonl": sorted(
            (path.name, path.read_bytes()) for path in (vault / ".memoria/journal").glob("*.jsonl")
        ),
        "head": head.read_bytes() if head.is_file() else None,
    }


def _client_events(vault: Path, event_type: str) -> list[dict[str, Any]]:
    """The `empirical_event.v1` payloads of one client event type, in write order."""
    return [
        payload
        for payload in (json.loads(row["payload_json"]) for row in _telemetry_rows(vault))
        if payload["event_type"] == event_type
    ]


def _seam_events(vault: Path) -> list[dict[str, Any]]:
    """The server plane: `resolved` journal events V2R-A's seam writes."""
    return [
        event
        for event in state.read_event_log(vault, event_types=["resolved"])
        if event.get("operation") == "resolve-evidence-review"
    ]


def _record_client_event(vault: Path, *, seconds_ago: int, **fields: Any) -> None:
    """Record one client event through the real door, dated `seconds_ago`.

    Produced, never hand-inserted: the door validates, so a fixture that the
    schema would refuse cannot quietly stand in for one it accepts.
    """
    event: dict[str, Any] = {
        "event_id": str(uuid.uuid4()),
        "event_type": "view.opened",
        "timestamp": utc_z(datetime.now(UTC) - timedelta(seconds=seconds_ago)),
        "session_id": uuid.uuid4().hex,
        "surface": "cli",
        "workflow": "evidence-review",
        "item_type": "evidence-set",
    }
    event.update(fields)
    result = engine_api.run_operation(
        vault,
        "empirical-event-record",
        event,
        idempotency_key=f"empirical-event:{event['event_id']}",
        actor="pi",
        machine="test-machine",
    )
    assert result["ok"] is True


def _disable_the_telemetry_sink(vault: Path) -> None:
    """Refuse every telemetry insert for real, at the sink.

    A `BEFORE INSERT` trigger survives `state._init`'s re-run of `schema.sql`
    (which a dropped table would not), refuses only this one table, and leaves
    reads and the rest of the vault working: a sink that is present but
    refusing, which is what the CLI has to report honestly.
    """
    with state.connect(vault) as conn:
        conn.execute(
            "CREATE TRIGGER telemetry_sink_offline BEFORE INSERT ON telemetry_events"
            " BEGIN SELECT RAISE(ABORT, 'telemetry sink offline'); END"
        )


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


# --- V2R-C.2: `memoria review show` ---------------------------------------


def test_review_show_adds_resolved_previews_to_the_summary_and_folds_analysis(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """The detail is the list summary plus `items=item_previews` — the resolved
    preview dictionaries, never the raw reference strings the row carries, and
    never the raw `item_previews` spelling (raw-queue amendment §3)."""
    vault, ids = review_vault

    rc = main(["review", "show", ids["dangling"], "--workspace", str(vault), "--json"])
    payload = _payload(capsys)

    assert rc == 0
    assert payload["ok"] is True
    row = payload["row"]
    assert row["items"] == [
        {
            "ref": "source-missing#^p0001",
            "kind": "source-span",
            "work_id": "source-missing",
            "anchor": "^p0001",
            "resolves": False,
        }
    ]
    assert row["item_count"] == 1
    assert row["routing_type"] == "incomplete"
    assert row["routing_reason"] == "evidence-incomplete: source-missing#^p0001 does not resolve"
    assert row["disposition"] == "open"
    assert row["project"] == ALPHA
    assert "analysis" not in row  # folded by default (spec §3)
    # The detail is a projection, not the raw row: no assembler internals, no
    # superseded DTO spellings, and no second name for the previews.
    assert {"item_previews", "draft_path", "block_ref", "holds", "blocked_by"}.isdisjoint(row)
    assert {"latest_decision", "routing", "project_path"}.isdisjoint(row)


def test_review_show_analysis_expands_to_the_shared_helper_output(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--show-analysis` publishes `analysis_fields(row, previews)` verbatim.

    Two rows with different tipping factors, because a single row cannot tell a
    passed-through mapping from a constant.
    """
    vault, ids = review_vault

    rc = main(
        ["review", "show", ids["thesis"], "--workspace", str(vault), "--show-analysis", "--json"]
    )
    implicit = _payload(capsys)["row"]
    assert (
        main(
            [
                "review",
                "show",
                ids["dangling"],
                "--workspace",
                str(vault),
                "--show-analysis",
                "--json",
            ]
        )
        == 0
    )
    incomplete = _payload(capsys)["row"]

    assert rc == 0
    assert implicit["analysis"] == {"tipped_by": "type=implicit"}
    assert incomplete["analysis"] == {"tipped_by": "source-missing#^p0001"}


def test_review_show_cure_row_expands_to_no_analysis_and_keeps_cure_and_warrant(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """A permanently blocked row has no analysis to act on, so the key is absent
    even under `--show-analysis` — while its cure and its warrant survive."""
    vault, ids = review_vault

    rc = main(
        ["review", "show", ids["support"], "--workspace", str(vault), "--show-analysis", "--json"]
    )
    row = _payload(capsys)["row"]

    assert rc == 0
    assert "analysis" not in row
    assert row["reviewable"] is False
    assert row["routing_type"] == ""
    assert row["cure"] == evidence_review.PERMANENT_BLOCK_CURE
    assert row["warrant"] == WARRANT
    assert row["items"][0]["excerpt"] == "source-alpha source span."


def test_review_show_human_output_is_evidence_first(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """Structural order (spec §3): claim, then grounds, then routing, and only
    then the machine's opinion. Each grounds line says whether its ref resolves,
    which is the fact the routing sentence is derived from — and the claim keeps
    its own soft-wrapped lines, which the list summary collapsed into one."""
    vault, ids = review_vault

    rc = main(["review", "show", ids["dangling"], "--workspace", str(vault), "--show-analysis"])
    out = capsys.readouterr().out

    assert rc == 0
    assert out.index("Claim") < out.index("Grounds items")
    assert out.index("Grounds items") < out.index("Why routed")
    assert out.index("Why routed") < out.index("Machine analysis")
    assert out.splitlines() == [
        f"Claim ({ids['dangling']}, incomplete):",
        "  A claim over a span",
        "  that never resolves.",
        "Grounds items (1):",
        "  - source-missing#^p0001  [does not resolve]",
        "Why routed: evidence-incomplete: source-missing#^p0001 does not resolve",
        "Disposition: open",
        "Machine analysis:",
        "  tipped_by: source-missing#^p0001",
    ]


def test_review_show_human_output_names_the_cure_and_the_empty_analysis(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """The read-only row renders its cure, its warrant, a resolving grounds line
    with its excerpt, `-` for the routing it has none of, and an expanded
    analysis that honestly says there is none."""
    vault, ids = review_vault

    rc = main(["review", "show", ids["support"], "--workspace", str(vault), "--show-analysis"])
    lines = capsys.readouterr().out.splitlines()

    assert rc == 0
    assert lines[0] == f"Claim ({ids['support']}, -):"
    assert lines[2] == "Grounds items (1):"
    assert lines[3] == "  - source-alpha#^p0001  [resolves]  source-alpha source span."
    assert lines[-4:] == [
        "Disposition: open",
        f"Read-only: {evidence_review.PERMANENT_BLOCK_CURE}",
        f"Warrant: {WARRANT}",
        "Machine analysis: none recorded for this row.",
    ]


def test_review_show_folds_analysis_and_names_the_flag_by_default(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without the flag the fold is stated, not silent, and the rejected row
    still renders its disposition (spec §4)."""
    vault, ids = review_vault

    rc = main(["review", "show", ids["hop"], "--workspace", str(vault)])
    out = capsys.readouterr().out

    assert rc == 0
    assert "Machine analysis folded — pass --show-analysis to expand." in out
    assert "tipped_by" not in out
    assert "Disposition: rejected" in out
    assert "  - ev-" in out  # the nested evidence-set ref is a grounds item


def test_review_show_quiet_prints_nothing_and_shares_the_json_payload(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--quiet` takes the payload branch, not the human render."""
    vault, ids = review_vault

    rc = main(["review", "show", ids["thesis"], "--workspace", str(vault), "--quiet"])

    assert rc == 0
    assert capsys.readouterr().out == ""


def test_review_show_records_one_client_event_in_telemetry_and_none_in_the_journal(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """The whole telemetry claim, both halves, taken at the writer.

    Positive: exactly one `empirical_event.v1` row whose payload is the
    `view.opened` fact, with the indexed `session_id`/`surface` columns filled.
    Negative: the journal plane — `event_log`, the per-machine JSONL, and the
    head anchor — is byte-identical across the call.
    """
    vault, ids = review_vault
    before = _journal_plane(vault)
    assert _telemetry_rows(vault) == []

    rc = main(["review", "show", ids["thesis"], "--workspace", str(vault), "--json"])
    payload = _payload(capsys)

    assert rc == 0
    (stored,) = _telemetry_rows(vault)
    assert stored["event_type"] == "empirical_event.v1"
    event = json.loads(stored["payload_json"])
    assert event["event_type"] == "view.opened"
    assert event["workflow"] == "evidence-review"
    assert event["surface"] == "cli"
    assert event["item_type"] == "evidence-set"
    assert event["item_id"] == ids["thesis"]
    assert event["session_id"]
    # The columns a reader indexes on, not just the blob.
    assert stored["session_id"] == event["session_id"]
    assert stored["surface"] == "cli"
    # The command reports the client event id it minted, so a caller can join.
    assert payload["telemetry"] == {"ok": True, "event_id": event["event_id"]}
    assert _journal_plane(vault) == before


def test_review_show_mints_a_fresh_session_and_event_per_invocation(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """One `view.opened` per show, each its own session: `items_per_session` in
    V2R-C.4 counts shows, so a hoisted constant would fuse every show into one."""
    vault, ids = review_vault

    assert main(["review", "show", ids["thesis"], "--workspace", str(vault), "--json"]) == 0
    assert main(["review", "show", ids["hop"], "--workspace", str(vault), "--json"]) == 0
    capsys.readouterr()

    events = [json.loads(row["payload_json"]) for row in _telemetry_rows(vault)]

    assert len(events) == 2
    assert [event["item_id"] for event in events] == [ids["thesis"], ids["hop"]]
    assert len({event["session_id"] for event in events}) == 2
    assert len({event["event_id"] for event in events}) == 2


def test_review_show_unknown_id_fails_and_records_no_client_event(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """The lookup precedes the emission, so a refused show leaves no telemetry
    row and no journal byte behind."""
    vault, _ids = review_vault
    before = _journal_plane(vault)

    rc = main(["review", "show", "ev-deadbeef", "--workspace", str(vault), "--json"])
    payload = _payload(capsys)

    assert rc == 2
    assert payload["ok"] is False
    assert "ev-deadbeef" in payload["error"]
    assert _telemetry_rows(vault) == []
    assert _journal_plane(vault) == before


def test_review_show_refuses_an_srd_gap_and_records_no_client_event(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """The lookup selects the evidence arm of the union only (raw-queue
    amendment §4): an SRD gap is in the same queue and is not evidence."""
    vault, _ids = review_vault

    rc = main(["review", "show", "inbox/srd-gap-alpha.md", "--workspace", str(vault), "--json"])
    payload = _payload(capsys)

    assert rc == 2
    assert payload["ok"] is False
    assert "inbox/srd-gap-alpha.md" in payload["error"]
    assert _telemetry_rows(vault) == []


def test_review_show_reports_a_refusing_telemetry_sink_instead_of_a_detail(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """A show that did not record its required client event is not a successful
    show: the failed operation's own error is retained and `_emit` exits 1."""
    vault, ids = review_vault
    _disable_the_telemetry_sink(vault)

    rc = main(["review", "show", ids["thesis"], "--workspace", str(vault), "--json"])
    payload = _payload(capsys)

    assert rc == 1
    assert payload["ok"] is False
    assert payload["error"] == "telemetry sink offline"  # the sink's words, not the CLI's
    assert payload["telemetry"]["ok"] is False
    assert payload["telemetry"]["result"]["status"] == "failed"
    assert _telemetry_rows(vault) == []
    # The detail was read honestly, so it rides along — the command just refuses
    # to call the show successful.
    assert payload["row"]["evidence_id"] == ids["thesis"]


def test_review_show_names_the_unrecorded_event_when_the_operation_gives_no_error(
    review_vault, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """An operation that fails without saying why still produces an honest
    refusal rather than a blank one."""
    vault, ids = review_vault

    def _silent_failure(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"ok": False, "job": {}, "result": None}

    monkeypatch.setattr(engine_api, "run_operation", _silent_failure)

    rc = main(["review", "show", ids["thesis"], "--workspace", str(vault), "--json"])
    payload = _payload(capsys)

    assert rc == 1
    assert payload["error"] == "evidence detail was read but view.opened was not recorded"


def test_review_show_reads_the_queue_engine_direct(
    review_vault, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Spec §8 keep-test, for the detail front too: no server, no view cards."""
    vault, ids = review_vault

    def _forbidden(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise AssertionError("the CLI front must never call the view projection")

    monkeypatch.setattr(engine_api, "read_evidence_review_view", _forbidden)

    rc = main(["review", "show", ids["thesis"], "--workspace", str(vault), "--json"])

    assert rc == 0
    assert _payload(capsys)["row"]["evidence_id"] == ids["thesis"]


def test_review_show_reaches_a_row_beyond_the_default_batch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`batch=0` is why the lookup is unbounded: a row the default list page
    never reaches is still showable by id.

    Which row gets cut is the queue's business, not the outline's — evidence ids
    are minted per block, so compose order is not queue order. The test asks the
    list which row it withheld instead of assuming.
    """
    ids = _wide_project(tmp_path, 11)

    assert main(["review", "list", "--workspace", str(tmp_path), "--json"]) == 0
    listed = _payload(capsys)
    assert listed["total"] == 11
    assert len(_by_id(listed)) == 10
    (withheld,) = [evidence_id for evidence_id in ids if evidence_id not in _by_id(listed)]

    rc = main(["review", "show", withheld, "--workspace", str(tmp_path), "--json"])
    payload = _payload(capsys)

    assert rc == 0
    assert payload["row"]["evidence_id"] == withheld


# --- V2R-C.3: `memoria review accept|reject|edit|defer` --------------------


@pytest.mark.parametrize("decision", ["accept", "reject", "edit", "defer"])
def test_review_action_drives_the_seam_and_records_one_client_disposition(
    review_vault, capsys: pytest.CaptureFixture[str], decision: str
) -> None:
    """Two planes, one action (nested-collector amendment §6): the server fact
    (`resolved` + its `disposition.v1` companion) is journaled by V2R-A's seam,
    while the CLI's own `disposition.recorded` is client telemetry."""
    vault, ids = review_vault
    before = len(_seam_events(vault))

    rc = main(["review", decision, ids["thesis"], "--workspace", str(vault), "--json"])
    payload = _payload(capsys)

    assert rc == 0
    assert payload["ok"] is True
    assert payload["evidence_id"] == ids["thesis"]
    assert payload["decision"] == decision
    seam = [event for event in _seam_events(vault) if event["evidence_id"] == ids["thesis"]]
    assert len(_seam_events(vault)) == before + 1
    assert [event["decision"] for event in seam] == [decision]
    # The seam's own server-side companion still rides the journal.
    companion = [
        event
        for event in state.read_event_log(vault, event_types=["disposition"])
        if event.get("item_id") == ids["thesis"]
    ]
    assert [event["decision"] for event in companion] == [decision]
    (client,) = _client_events(vault, "disposition.recorded")
    assert client["decision"] == decision
    assert client["workflow"] == "evidence-review"
    assert client["surface"] == "cli"
    assert client["item_type"] == "evidence-set"
    assert client["item_id"] == ids["thesis"]
    assert client["reason_code"] == "other"
    assert "duration_s" not in client  # never shown — no fabricated dwell
    assert "duration_s" not in payload["telemetry"]
    assert payload["telemetry"] == {"ok": True, "event_id": client["event_id"]}


def test_review_accept_records_the_warrant_on_the_seam_not_the_client_event(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """The warrant is grounding structure, so it rides the journaled seam event;
    the client event's field set is closed and carries no free text at all."""
    vault, ids = review_vault

    rc = main(
        [
            "review",
            "accept",
            ids["thesis"],
            "--workspace",
            str(vault),
            "--warrant",
            WARRANT,
            "--reason",
            "PI accepted",
            "--reason-code",
            "useful",
            "--json",
        ]
    )
    payload = _payload(capsys)

    assert rc == 0
    (seam,) = [event for event in _seam_events(vault) if event["evidence_id"] == ids["thesis"]]
    assert seam["decision"] == "accept"
    assert seam["warrant"] == WARRANT
    assert seam["reason"] == "PI accepted"
    (client,) = _client_events(vault, "disposition.recorded")
    assert client["reason_code"] == "useful"
    assert {"warrant", "reason"}.isdisjoint(client)
    assert payload["event"]["decision"] == "accept"


@pytest.mark.parametrize("decision", ["reject", "edit", "defer"])
def test_review_warrant_is_offered_only_on_accept(review_vault, decision: str) -> None:
    """The seam raises on a warrant riding a non-accept decision, so the parser
    never offers one — the refusal is structural, not a runtime surprise."""
    vault, ids = review_vault

    with pytest.raises(SystemExit) as exc:
        main(["review", decision, ids["thesis"], "--workspace", str(vault), "--warrant", WARRANT])

    assert exc.value.code == 2


def test_review_action_reason_code_is_the_closed_enum(review_vault) -> None:
    """`reason_code` is the I1 vocabulary, refused at the parser (SPEC GAP: the
    CLI defaults to `other` rather than growing the enum)."""
    vault, ids = review_vault

    with pytest.raises(SystemExit) as exc:
        main(
            ["review", "defer", ids["thesis"], "--workspace", str(vault), "--reason-code", "great"]
        )

    assert exc.value.code == 2


def test_review_action_dwell_rides_the_client_event(
    review_vault, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Dwell is the gap from the latest detail-open to the decision (spec §4).

    The clock is pinned against the timestamp the door stored, so the gap is a
    function of the fixture rather than of how long the run took. The live-clock
    form asserted a 91-second window (`89 <= x <= 180`) and still went red under
    a loaded gate -- and a range that wide could not have caught an off-by-one
    basis error anyway.
    """
    vault, ids = review_vault
    _record_client_event(vault, seconds_ago=90, item_id=ids["thesis"])
    (opened,) = _client_events(vault, "view.opened")
    opened_at = datetime.fromisoformat(str(opened["timestamp"]).replace("Z", "+00:00"))
    monkeypatch.setattr(knowledge, "datetime", _clock_pinned_at(opened_at + timedelta(seconds=90)))

    rc = main(["review", "defer", ids["thesis"], "--workspace", str(vault), "--json"])
    payload = _payload(capsys)

    assert rc == 0
    (client,) = _client_events(vault, "disposition.recorded")
    assert client["duration_s"] == 90.0
    assert client["duration_s"] == round(client["duration_s"], 1)  # tenths, not float noise
    assert payload["telemetry"]["duration_s"] == client["duration_s"]


@pytest.mark.parametrize(
    ("dwell_seconds", "reported"),
    [(0.4, False), (0.999, False), (1.0, True), (1.6, True)],
)
def test_review_action_reports_a_dwell_only_from_one_whole_second(
    review_vault,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    dwell_seconds: float,
    reported: bool,
) -> None:
    """A look shorter than a second is not a look: the schema would accept the
    fraction, and reporting it would put noise in the dwell distribution.

    The clock the reader consults is pinned, so the dwell is a function of the
    fixture rather than of how long the run took. `seconds_ago=0` against a live
    clock was a race, not a sub-second dwell -- under CI load the read landed
    almost two seconds after the write and the fraction became a 1.9. Pinning it
    also makes the boundary itself testable, which the wall-clock form could not
    do at all: 0.999 is withheld and 1.0 is reported by the same code path.
    """
    vault, ids = review_vault
    _record_client_event(vault, seconds_ago=600, item_id=ids["thesis"])
    # Pin the clock against the timestamp the door actually stored, not against a
    # separately computed one: `utc_z` truncates to whole seconds, so recomputing
    # it here lands up to a second away and reintroduces the race by other means.
    (opened,) = _client_events(vault, "view.opened")
    opened_at = datetime.fromisoformat(str(opened["timestamp"]).replace("Z", "+00:00"))
    monkeypatch.setattr(
        knowledge, "datetime", _clock_pinned_at(opened_at + timedelta(seconds=dwell_seconds))
    )

    rc = main(["review", "defer", ids["thesis"], "--workspace", str(vault), "--json"])
    payload = _payload(capsys)

    assert rc == 0
    assert review_dwell_seconds(vault, ids["thesis"]) is not None  # there *was* a dwell
    (client,) = _client_events(vault, "disposition.recorded")
    assert ("duration_s" in client) is reported
    assert ("duration_s" in payload["telemetry"]) is reported


def test_review_dwell_measures_the_latest_open_not_the_first(
    review_vault, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A row reopened after a long first look measures the *second* look: an
    absorbing first timestamp would report the whole trajectory as one dwell.

    Pinned against the *latest* stored open, so the assertion is exact. The
    live-clock form (`20 <= dwell < 100`) went red under a loaded gate, and its
    80-second slack was also wide enough to pass on a wrong basis.
    """
    vault, ids = review_vault
    _record_client_event(vault, seconds_ago=600, item_id=ids["thesis"])
    _record_client_event(vault, seconds_ago=20, item_id=ids["thesis"])
    latest = _client_events(vault, "view.opened")[-1]
    opened_at = datetime.fromisoformat(str(latest["timestamp"]).replace("Z", "+00:00"))
    monkeypatch.setattr(knowledge, "datetime", _clock_pinned_at(opened_at + timedelta(seconds=25)))

    dwell = review_dwell_seconds(vault, ids["thesis"])

    # Exactly the second look. Reading the *first* open would report ~605.
    assert dwell == 25.0


@pytest.mark.parametrize(
    "decoy",
    [
        pytest.param({"item_id": "ev-00000000"}, id="another-item"),
        pytest.param({"workflow": "draft"}, id="another-workflow"),
        pytest.param(
            {"event_type": "disposition.recorded", "decision": "defer", "reason_code": "other"},
            id="another-event-type",
        ),
    ],
)
def test_review_dwell_ignores_a_later_event_that_is_not_this_rows_open(
    review_vault, decoy: dict[str, Any]
) -> None:
    """Each predicate of the lookup has its own decoy, recorded *after* the real
    open, so dropping any one of them reports the decoy's near-zero gap."""
    vault, ids = review_vault
    _record_client_event(vault, seconds_ago=600, item_id=ids["thesis"])
    _record_client_event(vault, seconds_ago=1, **{"item_id": ids["thesis"], **decoy})

    dwell = review_dwell_seconds(vault, ids["thesis"])

    assert dwell is not None
    assert dwell >= 599


def test_review_dwell_is_none_when_the_row_was_never_shown(review_vault) -> None:
    vault, ids = review_vault

    assert review_dwell_seconds(vault, ids["thesis"]) is None


def test_review_dwell_is_none_when_the_open_is_in_the_future(review_vault) -> None:
    """A clock-skewed open would otherwise report a negative dwell as real."""
    vault, ids = review_vault
    _record_client_event(vault, seconds_ago=-120, item_id=ids["thesis"])

    assert review_dwell_seconds(vault, ids["thesis"]) is None


def test_review_dwell_is_none_without_a_database(tmp_path: Path) -> None:
    """A directory that is not a vault has no telemetry to read — and reading it
    must not *create* one, which `state.connect` would do on the way past."""
    assert review_dwell_seconds(tmp_path, "ev-00000000") is None
    assert not state.db_path(tmp_path).exists()


@pytest.mark.parametrize(
    "opened_at", ["2026-08-01T12:00:00", "not-a-timestamp"], ids=["naive", "unparseable"]
)
def test_review_dwell_is_none_for_an_open_it_cannot_place_in_time(
    review_vault, opened_at: str
) -> None:
    """`telemetry_events` is a plain table, so a row the door never validated can
    exist. An unplaceable open is no dwell, not a crash inside a decision."""
    vault, ids = review_vault
    payload = {
        "event_id": str(uuid.uuid4()),
        "event_type": "view.opened",
        "timestamp": opened_at,
        "session_id": "session-legacy",
        "surface": "cli",
        "workflow": "evidence-review",
        "item_type": "evidence-set",
        "item_id": ids["thesis"],
    }
    with state.connect(vault) as conn:
        conn.execute(
            "INSERT INTO telemetry_events (event_id, ts, event_type, payload_json)"
            " VALUES (?, ?, 'empirical_event.v1', ?)",
            (uuid.uuid4().hex, utc_z(), json.dumps(payload)),
        )

    assert review_dwell_seconds(vault, ids["thesis"]) is None


def test_review_action_requires_pi_actor(review_vault, capsys: pytest.CaptureFixture[str]) -> None:
    """The disposition is the one judgment reserved to the human: an agent actor
    is refused before either plane is written."""
    vault, ids = review_vault
    before = len(_seam_events(vault))

    rc = main(
        ["review", "accept", ids["thesis"], "--workspace", str(vault), "--actor", "agent", "--json"]
    )
    payload = _payload(capsys)

    assert rc == 2
    assert payload["ok"] is False
    assert "review-accept" in payload["error"]
    assert len(_seam_events(vault)) == before
    assert _telemetry_rows(vault) == []


def test_review_action_unknown_id_writes_neither_plane(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """The seam owns evidence-id validation (contract item 2), and it runs
    before the client event, so a refused decision records no telemetry."""
    vault, _ids = review_vault
    before = len(_seam_events(vault))

    rc = main(["review", "reject", "ev-deadbeef", "--workspace", str(vault), "--json"])
    payload = _payload(capsys)

    assert rc == 2
    assert payload["ok"] is False
    assert payload["error"] == "unknown evidence id: ev-deadbeef"
    assert len(_seam_events(vault)) == before
    assert _telemetry_rows(vault) == []


def test_review_action_reports_a_refusing_sink_after_a_successful_seam(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    """The decision is real and journaled, but a required client event that was
    not recorded is not a success: `_emit` exits 1 with the sink's own words."""
    vault, ids = review_vault
    _disable_the_telemetry_sink(vault)

    rc = main(["review", "accept", ids["thesis"], "--workspace", str(vault), "--json"])
    payload = _payload(capsys)

    assert rc == 1
    assert payload["ok"] is False
    assert payload["error"] == "telemetry sink offline"
    assert payload["telemetry"]["ok"] is False
    assert payload["telemetry"]["result"]["status"] == "failed"
    # The seam ran and stays run — the CLI reports, it does not roll back.
    assert payload["event"]["decision"] == "accept"
    (seam,) = [event for event in _seam_events(vault) if event["evidence_id"] == ids["thesis"]]
    assert seam["decision"] == "accept"


def test_review_action_names_the_unrecorded_client_event_when_the_operation_is_silent(
    review_vault, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """An operation that fails without saying why still yields an honest refusal."""
    vault, ids = review_vault

    def _silent_failure(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"ok": False, "job": {}, "result": None}

    monkeypatch.setattr(engine_api, "run_operation", _silent_failure)

    rc = main(["review", "edit", ids["thesis"], "--workspace", str(vault), "--json"])
    payload = _payload(capsys)

    assert rc == 1
    assert payload["error"] == "disposition succeeded but client telemetry was not recorded"


@pytest.mark.parametrize(
    ("argv", "suffix"), [(["--reason", "thin"], "  — thin"), ([], "")], ids=["reason", "bare"]
)
def test_review_action_human_front_names_the_decision(
    review_vault, capsys: pytest.CaptureFixture[str], argv: list[str], suffix: str
) -> None:
    """The default front names the decision it recorded, in the list's own row
    grammar — `_emit`'s generic success line says only "completed"."""
    vault, ids = review_vault

    rc = main(["review", "reject", ids["thesis"], "--workspace", str(vault), *argv])
    out = capsys.readouterr().out

    assert rc == 0
    assert out == f"reject {ids['thesis']}{suffix}\n"


def test_review_action_quiet_prints_nothing(
    review_vault, capsys: pytest.CaptureFixture[str]
) -> None:
    vault, ids = review_vault

    rc = main(["review", "defer", ids["thesis"], "--workspace", str(vault), "--quiet"])

    assert rc == 0
    assert capsys.readouterr().out == ""
    assert len(_client_events(vault, "disposition.recorded")) == 1
