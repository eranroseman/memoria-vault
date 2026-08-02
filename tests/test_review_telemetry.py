"""Contract tests for `review_telemetry_summary` and `memoria review stats` (V2R-C).

The summary spans two planes and says so (nested-collector amendment §6): action
counts come from the **server** truth — V2R-A's `resolve-evidence-review` journal
events — while shows, dwell samples and sessions come from **client**
`empirical_event.v1` rows in `telemetry_events`, where I1 T.3 put them. A metric
read from the wrong plane is the failure these tests exist to catch, so every
fixture writes decoys into the other one.

Skip rate and reopen rate are derived, never emitted: a skip is the *absence* of
a disposition, and a reopen is a *pattern* over the stream.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import pytest

from memoria_vault.cli import main
from memoria_vault.engine import api as engine_api
from memoria_vault.runtime import state
from memoria_vault.runtime.knowledge import compose_project_draft as _compose
from memoria_vault.runtime.knowledge import resolve_evidence_review as _resolve
from memoria_vault.runtime.knowledge import review_telemetry_summary
from memoria_vault.runtime.time import now_iso
from tests.helpers import call_with_context, write_checked_concept

NOTE_IDS = (
    "01ARZ3NDEKTSV4RRFFQ69G5FA1",
    "01ARZ3NDEKTSV4RRFFQ69G5FA2",
    "01ARZ3NDEKTSV4RRFFQ69G5FA3",
)


def _implicit_project(vault: Path, *, notes: int = 1) -> list[str]:
    """Compose a draft with `notes` implicit (reviewable) evidence sets."""
    write_checked_concept(
        vault,
        "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n",
        "project",
    )
    outline = []
    for index in range(notes):
        note_id = NOTE_IDS[index]
        write_checked_concept(
            vault,
            f"notes/claim-{index}.md",
            f"type: note\ncheck_status: checked\ntitle: Claim {index}\nid: {note_id}\n",
            "note",
            body=f"Implicit claim {index} needs review.",
        )
        outline.append(f"- {note_id} — Claim {index}\n")
    path = vault / "projects/project-alpha/outline.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(outline), encoding="utf-8")
    result = call_with_context(_compose, vault, "project-alpha")
    return [str(marker["id"]) for marker in result["evidence_markers"]]


def resolve(vault: Path, evidence_id: str, decision: str) -> dict[str, Any]:
    """One PI disposition through V2R-A's seam — the server plane."""
    return _resolve(
        vault,
        evidence_id,
        decision=decision,
        reason="test",
        actor="pi",
        machine="test-machine",
    )


def _record(vault: Path, **fields: Any) -> None:
    """One client event through the real door, which validates it."""
    event: dict[str, Any] = {
        "event_id": str(uuid.uuid4()),
        "timestamp": now_iso(),
        "session_id": "session-a",
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


def _view_opened(vault: Path, item_id: str | None = None, **fields: Any) -> None:
    if item_id is not None:
        fields.setdefault("item_id", item_id)
    _record(vault, event_type="view.opened", **fields)


def _disposition_recorded(vault: Path, item_id: str, **fields: Any) -> None:
    fields.setdefault("decision", "accept")
    fields.setdefault("reason_code", "other")
    _record(vault, event_type="disposition.recorded", item_id=item_id, **fields)


def test_summary_counts_actions_from_the_seam_not_the_client_copies(tmp_path: Path) -> None:
    """The server plane owns `actions`.

    The client copy is a *report* that a decision was taken; the journal is the
    decision. The decoy `reject` here has no seam event, so a summary counting
    client events would report a rejection that never happened.
    """
    first, second = _implicit_project(tmp_path, notes=2)
    resolve(tmp_path, first, "accept")
    resolve(tmp_path, second, "defer")
    _disposition_recorded(tmp_path, first, decision="reject")

    summary = review_telemetry_summary(tmp_path)

    assert summary["actions"] == {"accept": 1, "reject": 0, "edit": 0, "defer": 1}
    assert summary["disposed_items"] == 2
    # The same decoy is not a show either: `view.opened` is a predicate.
    assert summary["shows"] == 0


def test_summary_aggregates_dwell_from_the_client_durations(tmp_path: Path) -> None:
    """Dwell is a client fact carried by dispositions; only samples that carry
    one are samples, and an open's own duration is not a decision's dwell.

    Three skewed samples, so mean and median are different numbers: dwell is the
    metric a single long look distorts, which is why both are reported.
    """
    (evidence_id,) = _implicit_project(tmp_path)
    _disposition_recorded(tmp_path, evidence_id, duration_s=10.0)
    _disposition_recorded(tmp_path, evidence_id, duration_s=20.0)
    _disposition_recorded(tmp_path, evidence_id, duration_s=300.0)
    _disposition_recorded(tmp_path, evidence_id)  # never shown: no fabricated zero
    _view_opened(tmp_path, evidence_id, duration_s=9000.0)

    summary = review_telemetry_summary(tmp_path)

    assert summary["dwell_s"] == {"count": 3, "mean": 110.0, "median": 20.0}
    assert isinstance(summary["dwell_s"]["mean"], float)


def test_summary_dwell_ignores_another_workflows_duration(tmp_path: Path) -> None:
    """`workflow` is a predicate, not decoration: an export's dwell is not a
    review's, and the decoy is large enough to move both statistics."""
    (evidence_id,) = _implicit_project(tmp_path)
    _disposition_recorded(tmp_path, evidence_id, duration_s=30.0)
    _disposition_recorded(tmp_path, evidence_id, workflow="draft", duration_s=9000.0)

    summary = review_telemetry_summary(tmp_path)

    assert summary["dwell_s"] == {"count": 1, "mean": 30.0, "median": 30.0}


def test_summary_computes_skip_rate_from_shown_undisposed(tmp_path: Path) -> None:
    """A skip is the absence of a disposition on a row the PI actually looked at."""
    first, second = _implicit_project(tmp_path, notes=2)
    _view_opened(tmp_path, first)
    _view_opened(tmp_path, second)
    resolve(tmp_path, first, "accept")

    summary = review_telemetry_summary(tmp_path)

    assert summary["items_shown"] == 2
    assert summary["skip_rate"] == 0.5


def test_summary_skip_rate_ignores_a_disposition_on_an_unshown_row(tmp_path: Path) -> None:
    """The denominator is shown items, so disposing a row nobody opened cannot
    push the rate below zero-shown reality."""
    first, second = _implicit_project(tmp_path, notes=2)
    _view_opened(tmp_path, first)
    resolve(tmp_path, second, "accept")

    summary = review_telemetry_summary(tmp_path)

    assert summary["items_shown"] == 1
    assert summary["disposed_items"] == 1
    assert summary["skip_rate"] == 1.0


def test_summary_groups_items_per_session(tmp_path: Path) -> None:
    """Distinct items per session, so reopening one row twice in a sitting is
    one item — `items_per_session` measures breadth, not clicks."""
    first, second = _implicit_project(tmp_path, notes=2)
    _view_opened(tmp_path, first, session_id="session-a")
    _view_opened(tmp_path, second, session_id="session-a")
    _view_opened(tmp_path, first, session_id="session-b")
    _view_opened(tmp_path, first, session_id="session-b")

    summary = review_telemetry_summary(tmp_path)

    assert summary["sessions"] == 2
    assert summary["shows"] == 4
    assert summary["items_shown"] == 2
    assert summary["items_per_session"] == 1.5
    assert isinstance(summary["items_per_session"], float)


@pytest.mark.parametrize(
    "decoy",
    [
        pytest.param({"workflow": "draft"}, id="another-workflow"),
        pytest.param({"item_id": None}, id="no-item"),
    ],
)
def test_summary_ignores_a_show_that_is_not_an_evidence_review_item(
    tmp_path: Path, decoy: dict[str, Any]
) -> None:
    """Each predicate of the show lookup has its own decoy in its own session, so
    dropping one inflates `sessions`, `shows` and `items_shown` together."""
    (evidence_id,) = _implicit_project(tmp_path)
    _view_opened(tmp_path, evidence_id, session_id="session-a")
    fields = {"session_id": "session-decoy", "item_id": evidence_id, **decoy}
    _view_opened(tmp_path, **{key: value for key, value in fields.items() if value is not None})

    summary = review_telemetry_summary(tmp_path)

    assert summary["sessions"] == 1
    assert summary["shows"] == 1
    assert summary["items_shown"] == 1


def test_summary_is_all_zero_on_an_untouched_vault(tmp_path: Path) -> None:
    """An honest zero, not a division by one: nothing shown is not a 100% skip."""
    _implicit_project(tmp_path)

    summary = review_telemetry_summary(tmp_path)

    assert summary["sessions"] == 0
    assert summary["shows"] == 0
    assert summary["items_shown"] == 0
    assert summary["items_per_session"] == 0.0
    assert summary["actions"] == {"accept": 0, "reject": 0, "edit": 0, "defer": 0}
    assert summary["disposed_items"] == 0
    assert summary["dwell_s"] == {"count": 0, "mean": 0.0, "median": 0.0}
    assert summary["skip_rate"] == 0.0


def test_summary_is_all_zero_without_a_state_database(tmp_path: Path) -> None:
    """A directory that is not a vault reads as empty, and reading it does not
    create the database `state.connect` would otherwise make on the way past."""
    assert review_telemetry_summary(tmp_path)["shows"] == 0
    assert not state.db_path(tmp_path).exists()


def test_review_stats_cli_surfaces_the_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (evidence_id,) = _implicit_project(tmp_path)
    _view_opened(tmp_path, evidence_id)
    resolve(tmp_path, evidence_id, "accept")

    rc = main(["review", "stats", "--workspace", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert payload["ok"] is True
    assert payload["telemetry"] == review_telemetry_summary(tmp_path)
    assert payload["telemetry"]["actions"]["accept"] == 1
    assert payload["telemetry"]["skip_rate"] == 0.0


def test_review_stats_human_front_prints_every_metric(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`_emit`'s generic success line says only "completed", which is useless for
    a verb whose entire product is numbers."""
    (evidence_id,) = _implicit_project(tmp_path)
    _view_opened(tmp_path, evidence_id)
    _disposition_recorded(tmp_path, evidence_id, duration_s=42.0)
    resolve(tmp_path, evidence_id, "accept")

    rc = main(["review", "stats", "--workspace", str(tmp_path)])
    lines = capsys.readouterr().out.splitlines()

    assert rc == 0
    assert lines == [
        "sessions: 1",
        "shows: 1",
        "items_shown: 1",
        "items_per_session: 1.0",
        "actions: accept 1  reject 0  edit 0  defer 0",
        "disposed_items: 1",
        "dwell_s: count 1  mean 42.0  median 42.0",
        "skip_rate: 0.0",
        "reopens: defer_then_disposed 0  accept_voided 0",
        "reopen_rate: 0.0",
    ]


def test_review_stats_quiet_prints_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _implicit_project(tmp_path)

    rc = main(["review", "stats", "--workspace", str(tmp_path), "--quiet"])

    assert rc == 0
    assert capsys.readouterr().out == ""


def test_reopen_counts_a_deferred_row_disposed_later(tmp_path: Path) -> None:
    """A defer that came back is the reopen the metric exists to count."""
    (evidence_id,) = _implicit_project(tmp_path)
    resolve(tmp_path, evidence_id, "defer")
    resolve(tmp_path, evidence_id, "accept")

    summary = review_telemetry_summary(tmp_path)

    assert summary["reopens"] == {"defer_then_disposed": 1, "accept_voided": 0}
    assert summary["reopen_rate"] == 1.0


def test_reopen_counts_a_deferred_row_once_however_often_it_returns(tmp_path: Path) -> None:
    """Per id, not per event: three returns are one row that keeps coming back."""
    (evidence_id,) = _implicit_project(tmp_path)
    resolve(tmp_path, evidence_id, "defer")
    resolve(tmp_path, evidence_id, "edit")
    resolve(tmp_path, evidence_id, "reject")

    summary = review_telemetry_summary(tmp_path)

    assert summary["reopens"]["defer_then_disposed"] == 1


def test_a_defer_after_a_decision_is_not_a_reopen(tmp_path: Path) -> None:
    """Order is the whole claim: deferring an already-decided row is a new
    decision, not a row that came back."""
    (evidence_id,) = _implicit_project(tmp_path)
    resolve(tmp_path, evidence_id, "reject")
    resolve(tmp_path, evidence_id, "defer")

    summary = review_telemetry_summary(tmp_path)

    assert summary["reopens"]["defer_then_disposed"] == 0


def test_reopen_counts_an_accept_voided_by_an_item_edit(tmp_path: Path) -> None:
    """S35.4 semantics: an accept binds the items it was given, so changing them
    re-routes the row on the next verify — the accept no longer holds."""
    (evidence_id,) = _implicit_project(tmp_path)
    resolve(tmp_path, evidence_id, "accept")

    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.write_text(
        draft.read_text(encoding="utf-8").replace("items=%%", "items=source-missing#^p0001%%"),
        encoding="utf-8",
    )
    state.rebuild_evidence_sets_from_markers(tmp_path)

    summary = review_telemetry_summary(tmp_path)

    assert summary["reopens"] == {"defer_then_disposed": 0, "accept_voided": 1}
    assert summary["reopen_rate"] == 1.0


def test_an_intact_accept_is_not_a_reopen(tmp_path: Path) -> None:
    (evidence_id,) = _implicit_project(tmp_path)
    resolve(tmp_path, evidence_id, "accept")

    summary = review_telemetry_summary(tmp_path)

    assert summary["reopens"] == {"defer_then_disposed": 0, "accept_voided": 0}
    assert summary["reopen_rate"] == 0.0


def test_an_accept_superseded_by_a_reject_is_not_accept_voided(tmp_path: Path) -> None:
    """Only the *latest* decision can be voided: a row already rejected is not
    additionally an unheld accept."""
    (evidence_id,) = _implicit_project(tmp_path)
    resolve(tmp_path, evidence_id, "accept")
    resolve(tmp_path, evidence_id, "reject")

    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.write_text(
        draft.read_text(encoding="utf-8").replace("items=%%", "items=source-missing#^p0001%%"),
        encoding="utf-8",
    )
    state.rebuild_evidence_sets_from_markers(tmp_path)

    summary = review_telemetry_summary(tmp_path)

    assert summary["reopens"]["accept_voided"] == 0


def test_an_accepted_row_that_vanished_is_not_a_reopen(tmp_path: Path) -> None:
    """Fail closed, matching S35.4's inert-legacy rule: an id with no current
    evidence set has no current digest to disagree with."""
    (evidence_id,) = _implicit_project(tmp_path)
    resolve(tmp_path, evidence_id, "accept")
    state.replace_evidence_sets(tmp_path, [])

    summary = review_telemetry_summary(tmp_path)

    assert state.evidence_sets(tmp_path) == []
    assert summary["reopens"]["accept_voided"] == 0
    assert summary["disposed_items"] == 1


def test_reopen_rate_is_reopened_ids_over_disposed_ids(tmp_path: Path) -> None:
    """One reopened row among three disposed, so the rate cannot be read off a
    single row that is both numerator and denominator."""
    first, second, third = _implicit_project(tmp_path, notes=3)
    resolve(tmp_path, first, "defer")
    resolve(tmp_path, first, "accept")
    resolve(tmp_path, second, "reject")
    resolve(tmp_path, third, "edit")

    summary = review_telemetry_summary(tmp_path)

    assert summary["disposed_items"] == 3
    assert summary["reopens"] == {"defer_then_disposed": 1, "accept_voided": 0}
    assert summary["reopen_rate"] == pytest.approx(1 / 3)
