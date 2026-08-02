"""Contract tests for the honest dashboard (I1 spec §4): raw counts, no composite score.

Covers H.1's pure assembler and H.2's two fronts (the registered
`GET /v1/views/dashboard` view and the engine-direct `memoria dashboard`).

**Producer states, named.** A dashboard is mostly defaults, and the empty ones are
the ones that ship: a fresh vault has zero rows in both planes, so
`test_fresh_vault_assembles_seven_honestly_empty_panels` pins the whole zero
payload rather than only the populated case. The other unfixtured defaults each
get their own case: a card with no `loudness:` (`""` from `_attention_card`, read
as the `notice` band), a card with no parsable `created:` (age 0), a disposition
event with no `item_type`, an `empirical_event.v1` outside the evidence-review
workflow, a `read-observed.v1` with `staleness_hit: false`, and a telemetry row
whose grouping field is absent.

**Emptiness that is honest vs. emptiness that is degenerate.** `inflow_by_day`,
`per_producer`, `skipped_runs` and `edge_writes` have no shipped producer yet (I1
A.3/A.4, graph ERP-D.6). Every one of them is still proved against a real fixture
here -- through `record_telemetry_event` where the event type validates today, and
through a direct `telemetry_events` insert for `edge-write.v1`, whose writer lands
with ERP-D.6 -- so the query is proved to read the column and the event type it
claims, not merely to return `{}`. `decision_rules` is the exception: its producer
is the registry that ships in `runtime.decision_rules` (I1 H.3), so it is populated
from the first read and `tests/test_decision_rules.py` owns its cases.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import sqlite3
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from http import HTTPStatus
from pathlib import Path
from typing import Any

import pytest

from memoria_vault.cli import main
from memoria_vault.engine import api
from memoria_vault.engine.dashboard import DASHBOARD_PANELS, assemble_dashboard
from memoria_vault.engine.surface_contract import actions_by_id
from memoria_vault.runtime import state
from memoria_vault.runtime.http_transport import _dispatch, make_http_server
from memoria_vault.runtime.operations import emit_explicit_disposition_event
from memoria_vault.runtime.subsystems.lib.inbox import write_finding, write_proposal
from memoria_vault.runtime.telemetry import record_telemetry_event
from memoria_vault.runtime.vaultio import frontmatter_doc
from tests.helpers import init_cli_workspace

pytestmark = pytest.mark.contract

PANELS = {
    "attention_flow",
    "dispositions",
    "evidence_review",
    "reads_staleness",
    "edge_writes",
    "exploration",
    "decision_rules",
}

EMPTY_PAYLOAD: dict[str, Any] = {
    "attention_flow": {
        "open_total": 0,
        "open_by_loudness": {},
        "inflow_by_day": {},
        "drain_by_day": {},
        "net_by_day": {},
        "age_distribution": {},
        "per_producer": {},
        "skipped_runs": {},
    },
    "dispositions": {"by_decision": {}, "by_item_type": {}, "total": 0},
    "evidence_review": {"events": 0, "actions": {}, "mean_duration_s": 0},
    "reads_staleness": {"reads": 0, "staleness_hits": 0},
    "edge_writes": {},
    "exploration": {"surfaced": 0, "acted_on": 0},
}
# `decision_rules` is deliberately absent above: it is the one panel that is *not*
# empty on a fresh vault. The seventeen-rule pre-registration ships in
# `runtime.decision_rules`, so a new vault reads every blocker armed with nothing
# crossing. `tests/test_decision_rules.py` owns the roster and the thresholds; here
# only the wiring is pinned.
EMPTY_REGISTRY_RULES = 17


def _card(vault: Path, name: str, **frontmatter: Any) -> str:
    """Write one attention projection with exactly the frontmatter a case needs.

    Cards go through `frontmatter_doc` rather than `inbox`'s writers where the
    case is about a field those writers always stamp (`created`, `loudness`):
    the point of those cases is the card the writers do *not* produce -- a
    hand-edited or hand-written one, which `inbox/**` is the one tree the actor
    policy lets a non-PI agent write.
    """
    (vault / "inbox").mkdir(parents=True, exist_ok=True)
    path = vault / "inbox" / name
    path.write_text(
        frontmatter_doc(
            {"title": name, "projection": "attention", "attention_status": "open", **frontmatter},
            "# Finding\n\nbody\n",
        ),
        encoding="utf-8",
    )
    return f"inbox/{name}"


def _aged(days: int) -> str:
    return (datetime.date.today() - datetime.timedelta(days=days)).isoformat()


def _insert_telemetry(vault: Path, event_type: str, payload: dict[str, Any], ts: str) -> None:
    """Insert one telemetry row directly.

    Used only for streams whose validating writer has not landed
    (`edge-write.v1`, whose emitter is the graph plan's ERP-D.6) and for pinning a
    specific `ts` day, which `record_telemetry_event` always stamps as *now*.
    The column list is the shipped DDL's, so a schema drift breaks this loudly.
    """
    with state.connect(vault) as conn:
        conn.execute(
            "INSERT INTO telemetry_events (event_id, ts, event_type, payload_json)"
            " VALUES (?, ?, ?, ?)",
            (
                hashlib.sha256(f"{event_type}{ts}{payload}".encode()).hexdigest(),
                ts,
                event_type,
                json.dumps(payload, sort_keys=True),
            ),
        )


def _disposition(vault: Path, *, decision: str, item_type: str, item_id: str) -> None:
    emit_explicit_disposition_event(
        vault,
        decision=decision,
        item_type=item_type,
        item_id=item_id,
        actor="pi",
        machine="dash-test",
    )


def _backdate_journal(vault: Path, event_id: int, timestamp: str) -> None:
    """Move one journal row's timestamp with the append-only trigger stepped over.

    `event_log` refuses UPDATE by trigger, which is exactly right for the product
    and useless for building a multi-day drain series. Dropping and recreating the
    trigger around the write keeps the guard shipped while letting the fixture
    place a row on a chosen UTC day; the row hash is left alone because the
    dashboard reads `timestamp` and never re-verifies the chain.
    """
    with state.connect(vault) as conn:
        conn.execute("DROP TRIGGER event_log_no_update")
        conn.execute("UPDATE event_log SET timestamp = ? WHERE event_id = ?", (timestamp, event_id))
        conn.execute(
            "CREATE TRIGGER event_log_no_update BEFORE UPDATE ON event_log"
            " BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END"
        )


# --- H.1: the assembler ------------------------------------------------------


def test_fresh_vault_assembles_seven_honestly_empty_panels(tmp_path: Path) -> None:
    """The state that ships: zero rows in both planes, no `inbox/` at all.

    Pinned as the whole payload, not as `set(payload) == PANELS` -- an empty
    dashboard is the first one every PI sees, and a panel that silently omits a
    counter when its stream is empty would read as "not measured" rather than
    "measured, zero".
    """
    payload = assemble_dashboard(tmp_path)

    assert tuple(payload) == DASHBOARD_PANELS
    registry = payload.pop("decision_rules")
    assert payload == EMPTY_PAYLOAD
    assert len(registry["rules"]) == EMPTY_REGISTRY_RULES
    assert all(rule["status"] == "armed" for rule in registry["rules"])
    assert registry["would_fire"] == []


def test_dashboard_has_exactly_seven_panels_and_no_composite_score(tmp_path: Path) -> None:
    write_finding(tmp_path, "flag", "f1", "x", "sweep", target="notes/a.md")
    record_telemetry_event(
        tmp_path, "read-observed.v1", {"workflow": "attention", "staleness_hit": True}
    )
    _disposition(tmp_path, decision="accept", item_type="attention", item_id="inbox/f1.md")

    payload = assemble_dashboard(tmp_path)

    assert set(payload) == PANELS
    assert tuple(payload) == DASHBOARD_PANELS
    # Scanned over a *populated* payload: a forbidden-key scan of an empty one
    # would pass for a dashboard that grades every panel it can fill.
    flattened = json.dumps(payload).lower()
    for forbidden in ('"score"', '"health"', '"grade"'):
        assert forbidden not in flattened


def test_attention_flow_counts_open_cards_by_loudness_band(tmp_path: Path) -> None:
    """Four producer states for one counter: two bands written by a real
    producer, a hand-written card with no `loudness:` at all (the `notice`
    default), and a resolved card that must not be counted anywhere."""
    write_finding(tmp_path, "flag", "f1", "x", "sweep", target="notes/a.md")
    write_finding(tmp_path, "flag", "f2", "y", "sweep", target="notes/b.md", loudness="block")
    _card(tmp_path, "bare.md", raised_by="hand")
    _card(tmp_path, "done.md", loudness="alert", attention_status="resolved", raised_by="hand")

    flow = assemble_dashboard(tmp_path)["attention_flow"]

    assert flow["open_total"] == 3
    assert flow["open_by_loudness"] == {"alert": 1, "block": 1, "notice": 1}


def test_attention_flow_buckets_open_card_age_at_both_boundaries(tmp_path: Path) -> None:
    """Every bucket and both edges. `created` is the card's own stamp, so this
    also proves the panel reads that field rather than file mtime -- the two
    disagree here by construction, since every file is written today."""
    _card(tmp_path, "new.md", created=_aged(0))
    _card(tmp_path, "edge7.md", created=_aged(7))
    _card(tmp_path, "edge8.md", created=_aged(8))
    _card(tmp_path, "edge30.md", created=_aged(30))
    _card(tmp_path, "edge31.md", created=_aged(31))
    _card(tmp_path, "old.md", created=_aged(400))
    # No parsable `created:` at all, and a future one: both read as brand new
    # rather than inventing an age or raising.
    _card(tmp_path, "undated.md")
    _card(tmp_path, "garbled.md", created="last tuesday")
    _card(tmp_path, "future.md", created=_aged(-5))

    flow = assemble_dashboard(tmp_path)["attention_flow"]

    assert flow["age_distribution"] == {"0-7d": 5, "8-30d": 2, ">30d": 2}


def test_attention_flow_ages_only_open_cards(tmp_path: Path) -> None:
    """The age histogram is a queue-depth reading, so a resolved card leaves it.

    Separate from the loudness case above: a panel that filtered `status` in one
    counter and not the other would keep that case green.
    """
    _card(tmp_path, "open-old.md", created=_aged(90))
    _card(tmp_path, "closed-old.md", created=_aged(90), attention_status="resolved")

    flow = assemble_dashboard(tmp_path)["attention_flow"]

    assert flow["age_distribution"] == {">30d": 1}
    assert flow["open_total"] == 1


def test_attention_flow_separates_inflow_drain_and_net_per_utc_day(tmp_path: Path) -> None:
    """Three days, deliberately asymmetric: one with both streams, one with
    inflow only, one with drain only. A net computed over `inflow` alone (or over
    the intersection) drops a day here rather than reporting a signed number."""
    _insert_telemetry(
        tmp_path,
        "attention-admitted",
        {"card_path": "inbox/a.md", "kind": "flag", "loudness": "alert", "raised_by": "sweep"},
        "2026-03-01T09:00:00Z",
    )
    _insert_telemetry(
        tmp_path,
        "attention-admitted",
        {"card_path": "inbox/b.md", "kind": "flag", "loudness": "alert", "raised_by": "sweep"},
        "2026-03-01T22:00:00Z",
    )
    _insert_telemetry(
        tmp_path,
        "attention-admitted",
        {"card_path": "inbox/c.md", "kind": "gap", "loudness": "quiet", "raised_by": "gaps"},
        "2026-03-02T01:00:00Z",
    )
    _disposition(tmp_path, decision="accept", item_type="attention", item_id="inbox/a.md")
    _disposition(tmp_path, decision="reject", item_type="attention", item_id="inbox/z.md")
    _backdate_journal(tmp_path, 1, "2026-03-01T10:00:00Z")
    _backdate_journal(tmp_path, 2, "2026-03-03T10:00:00Z")

    flow = assemble_dashboard(tmp_path)["attention_flow"]

    assert flow["inflow_by_day"] == {"2026-03-01": 2, "2026-03-02": 1}
    assert flow["drain_by_day"] == {"2026-03-01": 1, "2026-03-03": 1}
    assert flow["net_by_day"] == {"2026-03-01": 1, "2026-03-02": 1, "2026-03-03": -1}


def test_attention_flow_groups_producers_and_skipped_runs_by_their_own_field(
    tmp_path: Path,
) -> None:
    """Two group-by counters over one table, and the discrimination between them.

    Both events are recorded through the shipped validating writer, and each
    counter must read *its own* event type and *its own* payload key: a
    `producer-run-skipped` row carries `producer`, never `raised_by`, so a
    counter reading the wrong field or the wrong type reports `{}` here.
    """
    for _ in range(2):
        record_telemetry_event(
            tmp_path,
            "attention-admitted",
            {
                "card_path": "inbox/a.md",
                "kind": "flag",
                "loudness": "alert",
                "raised_by": "sweep",
            },
        )
    record_telemetry_event(
        tmp_path,
        "attention-admitted",
        {"card_path": "inbox/b.md", "kind": "gap", "loudness": "quiet", "raised_by": "gaps"},
    )
    record_telemetry_event(
        tmp_path, "producer-run-skipped", {"producer": "sweep", "reason": "paused"}
    )

    flow = assemble_dashboard(tmp_path)["attention_flow"]

    assert flow["per_producer"] == {"sweep": 2, "gaps": 1}
    assert flow["skipped_runs"] == {"sweep": 1}


def test_group_counts_drop_rows_whose_grouping_field_is_absent(tmp_path: Path) -> None:
    """A row of the right type with no grouping key is not a `None` bucket."""
    _insert_telemetry(
        tmp_path, "producer-run-skipped", {"reason": "paused"}, "2026-03-01T00:00:00Z"
    )
    _insert_telemetry(
        tmp_path,
        "producer-run-skipped",
        {"producer": "sweep", "reason": "quiet"},
        "2026-03-01T01:00:00Z",
    )

    flow = assemble_dashboard(tmp_path)["attention_flow"]

    assert flow["skipped_runs"] == {"sweep": 1}


def test_dispositions_panel_splits_by_decision_and_item_type(tmp_path: Path) -> None:
    """Two item types, three decisions, and one repeat -- so `total` cannot be
    read off the number of distinct decisions, and the nested map cannot be a
    reshaping of `by_decision`."""
    _disposition(tmp_path, decision="accept", item_type="attention", item_id="inbox/a.md")
    _disposition(tmp_path, decision="accept", item_type="attention", item_id="inbox/b.md")
    _disposition(tmp_path, decision="reject", item_type="attention", item_id="inbox/c.md")
    _disposition(tmp_path, decision="defer", item_type="evidence-set", item_id="ev-1")

    panel = assemble_dashboard(tmp_path)["dispositions"]

    assert panel["by_decision"] == {"accept": 2, "reject": 1, "defer": 1}
    assert panel["by_item_type"] == {
        "attention": {"accept": 2, "reject": 1},
        "evidence-set": {"defer": 1},
    }
    assert panel["total"] == 4


def test_dispositions_panel_reads_the_journal_and_not_the_telemetry_table(
    tmp_path: Path,
) -> None:
    """The storage ruling, at the panel: `disposition.v1` is gate-read, so it is
    journal-side. A telemetry row with the same shape must not be counted."""
    _insert_telemetry(
        tmp_path,
        "disposition",
        {"decision": "accept", "item_type": "attention", "item_id": "inbox/a.md"},
        "2026-03-01T00:00:00Z",
    )
    _disposition(tmp_path, decision="reject", item_type="attention", item_id="inbox/b.md")

    panel = assemble_dashboard(tmp_path)["dispositions"]

    assert panel["by_decision"] == {"reject": 1}
    assert panel["total"] == 1


def test_evidence_review_panel_reads_only_the_evidence_review_workflow(
    tmp_path: Path,
) -> None:
    """The panel's denominator is the workflow, not the table. Two review events
    with durations, one review event without a decision, and one `ask` event
    that must not reach any of the three counters."""
    base = {
        "event_type": "disposition.recorded",
        "timestamp": "2026-03-01T00:00:00Z",
        "session_id": "s-1",
        "surface": "cli",
        "reason_code": "useful",
    }
    for index, (decision, duration) in enumerate((("accept", 10.0), ("reject", 5.0))):
        record_telemetry_event(
            tmp_path,
            "empirical_event.v1",
            {
                **base,
                "event_id": f"00000000-0000-4000-8000-00000000000{index}",
                "workflow": "evidence-review",
                "decision": decision,
                "duration_s": duration,
            },
        )
    record_telemetry_event(
        tmp_path,
        "empirical_event.v1",
        {
            **base,
            "event_id": "00000000-0000-4000-8000-000000000009",
            "event_type": "view.opened",
            "workflow": "evidence-review",
        },
    )
    record_telemetry_event(
        tmp_path,
        "empirical_event.v1",
        {
            **base,
            "event_id": "00000000-0000-4000-8000-00000000000a",
            "workflow": "ask",
            "decision": "accept",
            "duration_s": 900.0,
        },
    )

    panel = assemble_dashboard(tmp_path)["evidence_review"]

    assert panel["events"] == 3
    assert panel["actions"] == {"accept": 1, "reject": 1}
    # 7.5 over the two timed review events; the 900s `ask` event would move this
    # to 305.0 and the untimed review event would move it to 5.0.
    assert panel["mean_duration_s"] == 7.5


def test_reads_panel_counts_reads_and_staleness_hits_separately(tmp_path: Path) -> None:
    """The rate's two terms. `staleness_hit: false` is a real read, so the
    denominator moves and the numerator does not."""
    record_telemetry_event(
        tmp_path, "read-observed.v1", {"workflow": "attention", "staleness_hit": True}
    )
    record_telemetry_event(
        tmp_path, "read-observed.v1", {"workflow": "attention", "staleness_hit": False}
    )
    record_telemetry_event(
        tmp_path, "read-observed.v1", {"workflow": "ask", "staleness_hit": False}
    )

    panel = assemble_dashboard(tmp_path)["reads_staleness"]

    assert panel == {"reads": 3, "staleness_hits": 1}


def test_edge_writes_group_by_relation_type_when_the_stream_lands(tmp_path: Path) -> None:
    """Honest-empty today (the graph plan's ERP-D.6 owns the emitter), but the
    query is proved to read `edge-write.v1` grouped by `relation_type` -- not to
    return `{}` for any input. A same-table row of another type must not leak in.
    """
    assert assemble_dashboard(tmp_path)["edge_writes"] == {}

    for index, relation in enumerate(("supports", "supports", "refutes")):
        _insert_telemetry(
            tmp_path,
            "edge-write.v1",
            {"relation_type": relation, "source": f"notes/{index}.md"},
            f"2026-03-0{index + 1}T00:00:00Z",
        )
    record_telemetry_event(
        tmp_path,
        "attention-admitted",
        {"card_path": "inbox/a.md", "kind": "flag", "loudness": "alert", "raised_by": "sweep"},
    )

    payload = assemble_dashboard(tmp_path)

    assert payload["edge_writes"] == {"supports": 2, "refutes": 1}
    assert payload["attention_flow"]["per_producer"] == {"sweep": 1}


def test_exploration_panel_still_counts_a_candidate_after_it_is_acted_on(
    tmp_path: Path,
) -> None:
    """Acting on a card resolves it, so a surfaced/acted pair measured over open
    cards alone can only ever read zero. The denominator is every surfaced
    candidate on disk; the numerator is the ones a disposition names.
    """
    acted = _card(tmp_path, "gap-acted.md", raised_by="analyze-gaps", attention_status="resolved")
    _card(tmp_path, "gap-open.md", raised_by="analyze-gaps")
    _card(tmp_path, "sweep-card.md", raised_by="integrity-sweep")
    _disposition(tmp_path, decision="accept", item_type="attention", item_id=acted)
    _disposition(tmp_path, decision="reject", item_type="attention", item_id="inbox/sweep-card.md")

    panel = assemble_dashboard(tmp_path)["exploration"]

    assert panel == {"surfaced": 2, "acted_on": 1}


def test_exploration_acted_on_counts_candidates_not_dispositions(tmp_path: Path) -> None:
    """A card judged twice is one acted-on candidate, not two -- otherwise the
    numerator can exceed the denominator it is read against."""
    surfaced = _card(tmp_path, "gap.md", raised_by="analyze-gaps")
    _disposition(tmp_path, decision="defer", item_type="attention", item_id=surfaced)
    _disposition(tmp_path, decision="accept", item_type="attention", item_id=surfaced)

    panel = assemble_dashboard(tmp_path)["exploration"]

    assert panel == {"surfaced": 1, "acted_on": 1}


def test_assemble_dashboard_writes_nothing_when_called_repeatedly(tmp_path: Path) -> None:
    """Amendment 2026-07-29 §1: assessment is pure. Every vault file, and both
    planes' row counts, survive repeated assembly -- so the U1 floor guard holds
    however the read is reached."""
    write_finding(tmp_path, "flag", "f1", "x", "sweep", target="notes/a.md")
    write_proposal(tmp_path, "gap", "g1", "act", "for", "against", "tip", "likely", "analyze-gaps")
    record_telemetry_event(
        tmp_path, "read-observed.v1", {"workflow": "attention", "staleness_hit": True}
    )

    def tree() -> dict[str, str]:
        return {
            path.relative_to(tmp_path).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(tmp_path.rglob("*"))
            if path.is_file() and ".sqlite" not in path.name
        }

    def rows() -> tuple[int, int]:
        with state.connect(tmp_path) as conn:
            return (
                int(conn.execute("SELECT COUNT(*) AS n FROM event_log").fetchone()["n"]),
                int(conn.execute("SELECT COUNT(*) AS n FROM telemetry_events").fetchone()["n"]),
            )

    before_tree, before_rows = tree(), rows()
    first = assemble_dashboard(tmp_path)
    second = assemble_dashboard(tmp_path)

    assert first == second
    assert tree() == before_tree
    assert rows() == before_rows
    assert before_tree, "the read-only proof needs files to watch"


def test_assemble_dashboard_creates_the_state_db_for_a_directory_with_no_vault(
    tmp_path: Path,
) -> None:
    """`state.connect` is the only writer a read may reach, and it writes the
    gitignored DB. Pinned so the fresh-vault case above is understood as
    "creates the DB and nothing else", not as an accident."""
    assemble_dashboard(tmp_path)

    assert (tmp_path / ".memoria/memoria.sqlite").is_file()
    assert (
        sorted(
            path.relative_to(tmp_path).as_posix()
            for path in tmp_path.rglob("*")
            if path.is_file() and ".sqlite" not in path.name
        )
        == []
    )


# --- H.2: the registered HTTP view -------------------------------------------


def test_views_dashboard_row_is_http_only_with_current_shape() -> None:
    """The whole row, like `views.attention` pins its own: the floor sweep only
    checks `api_version` for rows that *declare* a `response_version`, so
    dropping the declaration removes the check instead of failing it. The
    workspace scope is load-bearing too -- it is what makes
    test_read_api_scope_walk exempt this row instead of demanding a probe."""
    assert actions_by_id()["views.dashboard"] == {
        "id": "views.dashboard",
        "job": "review",
        "summary": "Render the raw-count instrumentation dashboard view.",
        "engine": "read_dashboard_view",
        "kind": "read",
        "scope": "workspace",
        "params": {},
        "http": {"method": "GET", "path": "/v1/views/dashboard"},
        "response_version": api.READ_API_VERSION,
    }


def test_read_dashboard_view_renders_one_text_block_per_panel_in_order(
    tmp_path: Path,
) -> None:
    write_finding(tmp_path, "flag", "f1", "x", "sweep", target="notes/a.md")

    payload = api.read_dashboard_view(tmp_path)
    panels = assemble_dashboard(tmp_path)

    assert payload["ok"] is True
    assert payload["api_version"] == "engine-read-api.v1"
    assert set(payload) == {"ok", "api_version", "view"}
    view = payload["view"]
    assert set(view) == {"version", "kind", "blocks"}
    assert view["version"] == "view-spec.v1"
    assert view["kind"] == "dashboard"
    assert [block["id"] for block in view["blocks"]] == [
        f"dashboard-{panel}" for panel in DASHBOARD_PANELS
    ]
    assert {block["kind"] for block in view["blocks"]} == {"text"}
    assert {block["kind"] for block in view["blocks"]} <= set(api.VIEW_BLOCK_KINDS)
    # Every block is exactly its panel, and no block carries an action row: raw
    # counts recommend, they never act.
    for block in view["blocks"]:
        assert set(block) == {"id", "kind", "text"}
    assert [json.loads(block["text"]) for block in view["blocks"]] == [
        panels[panel] for panel in DASHBOARD_PANELS
    ]


def test_read_dashboard_view_serializes_compactly_and_sorted(tmp_path: Path) -> None:
    """The exact serialization the amendment names: sorted keys, no spaces, and
    non-escaped Unicode. A pane parses these strings back, so the separators are
    contract rather than taste."""
    _card(tmp_path, "unicode.md", loudness="alert", raised_by="sweepé")
    record_telemetry_event(
        tmp_path,
        "attention-admitted",
        {
            "card_path": "inbox/unicode.md",
            "kind": "flag",
            "loudness": "alert",
            "raised_by": "sweepé",
        },
    )

    blocks = api.read_dashboard_view(tmp_path)["view"]["blocks"]
    flow = next(block for block in blocks if block["id"] == "dashboard-attention_flow")

    assert '"per_producer":{"sweepé":1}' in flow["text"]
    assert "\\u" not in flow["text"]
    assert ", " not in flow["text"]
    assert flow["text"].index('"age_distribution"') < flow["text"].index('"drain_by_day"')


def test_http_dispatch_serves_the_dashboard_view(tmp_path: Path) -> None:
    write_finding(tmp_path, "flag", "f1", "x", "sweep", target="notes/a.md")

    payload, status = _dispatch(tmp_path, "GET", "/v1/views/dashboard", dict)

    assert status == HTTPStatus.OK
    # Verbatim: the route serializes the producer's payload, never a reshaping.
    assert payload == api.read_dashboard_view(tmp_path)
    assert json.loads(payload["view"]["blocks"][0]["text"])["open_total"] == 1


def test_http_dispatch_rejects_wrong_method_for_the_dashboard_view(tmp_path: Path) -> None:
    response, status = _dispatch(tmp_path, "POST", "/v1/views/dashboard", dict)

    assert status == HTTPStatus.METHOD_NOT_ALLOWED
    assert response == {"ok": False, "error": "method not allowed: POST /v1/views/dashboard"}


def test_dashboard_view_ignores_a_read_scope_because_the_row_is_workspace_scope(
    tmp_path: Path,
) -> None:
    """Workspace scope is a claim about the payload, not just a registry string:
    a vault-wide count that quietly narrowed under a boot scope would report a
    smaller queue than the vault has."""
    write_finding(tmp_path, "flag", "f1", "x", "sweep", target="notes/a.md")

    unscoped, _ = _dispatch(tmp_path, "GET", "/v1/views/dashboard", dict)
    scoped, status = _dispatch(
        tmp_path, "GET", "/v1/views/dashboard", dict, read_scope=["scope-walk-void"]
    )

    assert status == HTTPStatus.OK
    assert scoped == unscoped
    assert json.loads(scoped["view"]["blocks"][0]["text"])["open_total"] == 1


def test_openapi_document_describes_the_dashboard_route() -> None:
    from memoria_vault.runtime.http_transport import openapi_schema

    route = openapi_schema()["paths"]["/v1/views/dashboard"]["get"]

    assert route["operationId"] == "views.dashboard"
    assert route["summary"] == "Render the raw-count instrumentation dashboard view."
    assert route["parameters"] == []


# --- H.2: the same route through a real socket, where auth actually runs ------

LIVE_TOKEN = "dashboard-token"
UNAUTHORIZED = {"ok": False, "error": "unauthorized: missing or invalid bearer token"}


@pytest.fixture
def live_server(tmp_path: Path) -> Iterator[str]:
    """A real listener, not `_dispatch`: the bearer check lives in the request
    handler, so nothing below the socket can prove a route is authenticated."""
    write_finding(tmp_path, "flag", "f1", "x", "sweep", target="notes/a.md")
    server = make_http_server(tmp_path, host="127.0.0.1", port=0, token=LIVE_TOKEN)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _http(url: str, *, token: str | None = None, method: str = "GET") -> tuple[int, dict]:
    request = urllib.request.Request(url, method=method)
    if token is not None:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def test_live_server_refuses_the_dashboard_view_without_a_valid_bearer_token(
    live_server: str,
) -> None:
    """The seeded card matters: a refusal that only held for an empty dashboard
    would say nothing about a vault with counts worth hiding."""
    view = f"{live_server}/v1/views/dashboard"

    assert _http(view) == (HTTPStatus.UNAUTHORIZED, UNAUTHORIZED)
    assert _http(view, token="other") == (HTTPStatus.UNAUTHORIZED, UNAUTHORIZED)
    assert _http(view, token="") == (HTTPStatus.UNAUTHORIZED, UNAUTHORIZED)
    # A prefix and an extension of the real token: a door comparing with
    # `startswith` or `in` rather than the whole value would open for these.
    assert _http(view, token=LIVE_TOKEN[:-1]) == (HTTPStatus.UNAUTHORIZED, UNAUTHORIZED)
    assert _http(view, token=f"{LIVE_TOKEN}-extra") == (HTTPStatus.UNAUTHORIZED, UNAUTHORIZED)


def test_live_server_serves_the_dashboard_view_with_the_token(
    tmp_path: Path, live_server: str
) -> None:
    code, payload = _http(f"{live_server}/v1/views/dashboard", token=LIVE_TOKEN)

    assert code == HTTPStatus.OK
    assert payload["ok"] is True
    assert payload["api_version"] == "engine-read-api.v1"
    assert payload["view"]["version"] == "view-spec.v1"
    assert payload["view"]["kind"] == "dashboard"
    assert [block["id"] for block in payload["view"]["blocks"]] == [
        f"dashboard-{panel}" for panel in DASHBOARD_PANELS
    ]
    # Nonempty, and the same counts the producer computed: the panels have to
    # survive the wire, and an empty dashboard would prove nothing about that.
    assert [json.loads(block["text"]) for block in payload["view"]["blocks"]] == [
        assemble_dashboard(tmp_path)[panel] for panel in DASHBOARD_PANELS
    ]
    assert json.loads(payload["view"]["blocks"][0]["text"])["open_total"] == 1


def test_live_server_dashboard_view_grants_a_read_and_nothing_else(
    tmp_path: Path, live_server: str
) -> None:
    """The same token on the view route buys a GET; posting to it is refused by
    the route gate and enqueues nothing on the way."""

    def requests() -> int:
        with state.connect(tmp_path) as conn:
            return int(conn.execute("SELECT COUNT(*) AS n FROM operation_requests").fetchone()["n"])

    before = requests()

    code, payload = _http(f"{live_server}/v1/views/dashboard", token=LIVE_TOKEN, method="POST")

    assert code == HTTPStatus.METHOD_NOT_ALLOWED
    assert payload == {"ok": False, "error": "method not allowed: POST /v1/views/dashboard"}
    assert requests() == before


# --- H.2: the engine-direct CLI front ----------------------------------------


def test_dashboard_command_emits_seven_panels(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    write_finding(workspace, "flag", "f1", "x", "sweep", target="notes/a.md")

    assert main(["dashboard", "--workspace", str(workspace), "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert set(payload["dashboard"]) == PANELS
    # The assembler's payload whole, not the view projection: the CLI front and
    # the HTTP view must read the same counts.
    assert payload["dashboard"] == assemble_dashboard(workspace)
    assert payload["dashboard"]["attention_flow"]["open_total"] == 1


def test_dashboard_command_is_read_only_on_a_seeded_workspace(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)

    def tree() -> dict[str, str]:
        return {
            path.relative_to(workspace).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(workspace.rglob("*"))
            if path.is_file() and ".git/" not in path.as_posix() and ".sqlite" not in path.name
        }

    before = tree()
    assert main(["dashboard", "--workspace", str(workspace), "--json"]) == 0
    capsys.readouterr()

    assert tree() == before
    assert before, "the read-only proof needs files to watch"


def test_journal_append_only_trigger_is_restored_by_the_backdating_fixture(
    tmp_path: Path,
) -> None:
    """The fixture above drops and recreates a shipped guard. If it ever failed
    to put it back, every later assertion in this module would run against a
    mutable journal and say nothing about the product."""
    _disposition(tmp_path, decision="accept", item_type="attention", item_id="inbox/a.md")
    _backdate_journal(tmp_path, 1, "2026-03-01T10:00:00Z")

    with state.connect(tmp_path) as conn, pytest.raises(sqlite3.IntegrityError):
        conn.execute("UPDATE event_log SET timestamp = '2026-01-01T00:00:00Z'")
