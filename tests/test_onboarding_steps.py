"""Contract tests for onboarding-step telemetry (O1 spec §5): an observer, never a gate."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.onboarding_steps import (
    ONBOARDING_STEPS,
    answer_work_ids,
    emit_first_answer_if_seed_grounded,
    emit_onboarding_step,
    emit_onboarding_step_once,
    has_onboarding_step,
    seed_manifest_work_ids,
)

pytestmark = pytest.mark.contract


def test_onboarding_step_is_a_registered_all_string_native_type() -> None:
    from memoria_vault.runtime.telemetry import NATIVE_EVENT_FIELDS

    assert NATIVE_EVENT_FIELDS["onboarding-step"] == frozenset({"step"})


def test_onboarding_steps_roster_is_the_spec_five() -> None:
    # Literals, and nothing derived from ONBOARDING_STEPS: a test that iterates the
    # roster still passes after the roster loses an entry.
    assert ONBOARDING_STEPS == {
        "init-done",
        "onboard-done",
        "project-framed",
        "seed-installed",
        "first-answer",
    }


def test_emit_onboarding_step_records_one_server_side_row(tmp_path: Path) -> None:
    event_id = emit_onboarding_step(tmp_path, "init-done")

    assert event_id
    with state.connect(tmp_path) as conn:
        row = conn.execute(
            "SELECT event_type, session_id, surface, payload_json FROM telemetry_events"
            " WHERE event_id = ?",
            (event_id,),
        ).fetchone()
    assert row["event_type"] == "onboarding-step"
    # NULL here is the real producer state, not an unfixtured default: an onboarding
    # step is recorded server-side with no client envelope. The producer of non-NULL
    # session_id/surface is a client-submitted empirical event, fixtured by
    # tests/test_telemetry_events.py::
    # test_record_telemetry_event_keeps_client_session_and_surface_for_empirical_events.
    assert row["session_id"] is None  # spec §5: server-side, session_id NULL
    assert row["surface"] is None
    assert json.loads(row["payload_json"]) == {"step": "init-done"}
    assert has_onboarding_step(tmp_path, "init-done") is True
    assert has_onboarding_step(tmp_path, "first-answer") is False


def test_emit_onboarding_step_records_every_step_under_its_own_name(tmp_path: Path) -> None:
    # Each step name is written through, so a helper that hardcoded one step (or
    # dropped the payload) cannot pass. Literal list, not a loop over ONBOARDING_STEPS.
    for step in ("init-done", "onboard-done", "project-framed", "seed-installed", "first-answer"):
        assert emit_onboarding_step(tmp_path, step)

    with state.connect(tmp_path) as conn:
        payloads = [
            json.loads(row["payload_json"])
            for row in conn.execute(
                "SELECT payload_json FROM telemetry_events WHERE event_type = 'onboarding-step'"
                " ORDER BY payload_json"
            )
        ]
    assert payloads == [
        {"step": "first-answer"},
        {"step": "init-done"},
        {"step": "onboard-done"},
        {"step": "project-framed"},
        {"step": "seed-installed"},
    ]
    assert has_onboarding_step(tmp_path, "seed-installed") is True


def test_emit_onboarding_step_appends_nothing_to_the_journal(tmp_path: Path) -> None:
    # Proved at the writer, not at the reader: verify_journal_chain cannot see a
    # telemetry row either way, so only the event_log count shows this emitter does
    # not also journal.
    emit_onboarding_step(tmp_path, "init-done")

    with state.connect(tmp_path) as conn:
        journal = conn.execute("SELECT COUNT(*) FROM event_log").fetchone()[0]
        telemetry = conn.execute("SELECT COUNT(*) FROM telemetry_events").fetchone()[0]
    assert journal == 0
    assert telemetry == 1
    assert state.verify_journal_chain(tmp_path)["events"] == 0


def test_emit_onboarding_step_rejects_unknown_steps(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown onboarding step"):
        emit_onboarding_step(tmp_path, "made-up-step")
    with pytest.raises(ValueError, match="unknown onboarding step"):
        has_onboarding_step(tmp_path, "made-up-step")
    with pytest.raises(ValueError, match="unknown onboarding step"):
        emit_onboarding_step_once(tmp_path, "made-up-step")

    # A programmer error at the call site never reaches the sink.
    with state.connect(tmp_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM telemetry_events").fetchone()[0] == 0


def _disable_the_telemetry_sink(vault: Path) -> None:
    """Make every telemetry insert fail for real, at the sink.

    `connect()` skips the DDL on current DBs, so `DROP TABLE telemetry_events`
    would stay dropped — but that models a damaged vault, not a refusing sink.
    A `BEFORE INSERT` trigger blocks writes without mutating the schema,
    refuses only this one table, and leaves reads and the rest of the vault
    working — the shape of a sink that is present but refusing.
    """
    with state.connect(vault) as conn:
        conn.execute(
            "CREATE TRIGGER telemetry_sink_offline BEFORE INSERT ON telemetry_events"
            " BEGIN SELECT RAISE(ABORT, 'telemetry sink offline'); END"
        )


def test_emit_onboarding_step_no_ops_when_the_sink_refuses_the_insert(tmp_path: Path) -> None:
    _disable_the_telemetry_sink(tmp_path)

    # The failure is produced, not mocked: the real insert raises.
    with state.connect(tmp_path) as conn, pytest.raises(sqlite3.DatabaseError):
        conn.execute(
            "INSERT INTO telemetry_events (event_id, ts, event_type, payload_json)"
            " VALUES ('probe', 'ts', 'onboarding-step', '{}')"
        )

    assert emit_onboarding_step(tmp_path, "init-done") is None  # observer, never a gate
    assert emit_onboarding_step_once(tmp_path, "init-done") is None
    # Reads still work here, so the False is the honest "no row", not a swallowed error.
    assert has_onboarding_step(tmp_path, "init-done") is False


def test_onboarding_step_reads_no_op_on_an_unreadable_database(tmp_path: Path) -> None:
    emit_onboarding_step(tmp_path, "init-done")
    assert has_onboarding_step(tmp_path, "init-done") is True
    database = state.db_path(tmp_path)
    for suffix in ("-wal", "-shm"):
        sidecar = database.with_name(database.name + suffix)
        sidecar.unlink(missing_ok=True)
    database.write_bytes(b"not a database at all\n")

    # A corrupt vault DB is the read-side sink failure; the prior True above shows
    # the False below is the guard firing, not an empty table.
    assert has_onboarding_step(tmp_path, "init-done") is False
    assert emit_onboarding_step(tmp_path, "init-done") is None


def test_emit_onboarding_step_no_ops_without_the_telemetry_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(sys.modules, "memoria_vault.runtime.telemetry", None)

    assert emit_onboarding_step(tmp_path, "init-done") is None


def test_emit_onboarding_step_once_skips_when_a_prior_row_exists(tmp_path: Path) -> None:
    first = emit_onboarding_step_once(tmp_path, "project-framed")
    second = emit_onboarding_step_once(tmp_path, "project-framed")

    assert first
    assert second is None
    with state.connect(tmp_path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM telemetry_events WHERE event_type = 'onboarding-step'"
        ).fetchone()[0]
    assert count == 1


def test_emit_onboarding_step_once_dedupes_per_step_not_per_event_type(tmp_path: Path) -> None:
    # A prior row for a *different* step must not suppress this one, or the five
    # steps collapse into one and every §5 delta disappears.
    assert emit_onboarding_step_once(tmp_path, "init-done")
    assert emit_onboarding_step_once(tmp_path, "seed-installed")

    with state.connect(tmp_path) as conn:
        steps = sorted(
            json.loads(row["payload_json"])["step"]
            for row in conn.execute("SELECT payload_json FROM telemetry_events")
        )
    assert steps == ["init-done", "seed-installed"]


def test_emit_onboarding_step_repeats_without_the_once_guard(tmp_path: Path) -> None:
    # The plain emitter is an honest observer of real re-runs (spec-gap resolution 4);
    # only emit_onboarding_step_once dedupes.
    first = emit_onboarding_step(tmp_path, "init-done")
    second = emit_onboarding_step(tmp_path, "init-done")

    assert first != second
    with state.connect(tmp_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM telemetry_events").fetchone()[0]
    assert count == 2


def test_emit_onboarding_step_once_stays_silent_from_the_second_call_onward(
    tmp_path: Path,
) -> None:
    # `_once` is a state machine with an absorbing state, so sample the trajectory,
    # not just the first transition: call 1 emits, calls 2 and 3 must not.
    trajectory = [emit_onboarding_step_once(tmp_path, "first-answer") for _ in range(3)]

    assert trajectory[0]
    assert trajectory[1] is None
    assert trajectory[2] is None
    with state.connect(tmp_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM telemetry_events").fetchone()[0]
    assert count == 1


# --- Task T.2: the first-answer rule ---------------------------------------------


def _seed_grounded_answer() -> dict[str, object]:
    """An answer whose sources really are the seed corpus's generated work documents."""
    return {
        "sources": [
            {
                "path": "fulltexts/chen-2018-undesirable-difficulty.md",
                "title": "Undesirable Difficulty Effects",
                "type": "fulltext",
                "score": 2.0,
            }
        ]
    }


def _off_corpus_answer() -> dict[str, object]:
    return {
        "sources": [
            {"path": "notes/my-claim.md", "title": "n", "type": "note", "score": 1.0},
            # A work document whose work id is NOT in the manifest: the rule turns on
            # the seed intersection, not on "any work document".
            {
                "path": "fulltexts/local-work-2024.md",
                "title": "l",
                "type": "fulltext",
                "score": 1.0,
            },
        ]
    }


def test_answer_work_ids_resolve_only_work_document_paths() -> None:
    answer = {
        "sources": [
            {"path": "fulltexts/oa-chen-2018.md", "title": "c", "type": "fulltext", "score": 2.0},
            {"path": "digests/oa-morrison-2020.md", "title": "d", "type": "digest", "score": 1.5},
            {
                "path": "graph-neighborhoods/oa-schmidt-2018.md",
                "title": "g",
                "type": "graph-neighborhood",
                "score": 1.1,
            },
            {"path": "notes/my-claim.md", "title": "n", "type": "note", "score": 1.0},
            {"path": "hubs/memory.md", "title": "h", "type": "hub", "score": 0.9},
        ]
    }

    # Literal, and all three roots at once: dropping any one root fails here.
    assert answer_work_ids(answer) == frozenset(
        {"oa-chen-2018", "oa-morrison-2020", "oa-schmidt-2018"}
    )


def test_answer_work_ids_reject_near_miss_paths() -> None:
    # Each entry is a path shape that is NOT a generated work document. Without these
    # the two-segment/.md/root conditions can each be deleted and every other test passes.
    answer = {
        "sources": [
            {"path": "fulltexts/nested/deep.md"},  # three segments
            # Also three segments, but with a `.md` *second* segment: the discriminating
            # case for "exactly two". Relaxing the length test to `>= 2` resolves this to
            # the work id "nested", so a loose depth check cannot hide here.
            {"path": "fulltexts/nested.md/deep.md"},
            {"path": "fulltexts.md"},  # one segment
            {"path": "fulltexts/plain.txt"},  # not markdown
            {"path": "attachments/oa-chen-2018.md"},  # not a work-document root
            {"path": ""},  # no path at all
        ]
    }

    assert answer_work_ids(answer) == frozenset()


def test_answer_work_ids_tolerate_malformed_answer_shapes() -> None:
    assert answer_work_ids({"sources": []}) == frozenset()
    assert answer_work_ids({}) == frozenset()
    assert answer_work_ids({"sources": "fulltexts/oa-chen-2018.md"}) == frozenset()
    # A non-iterable `sources` is what actually exercises the list guard: a str still
    # iterates (into characters) and hides a dropped guard, an int raises through it.
    assert answer_work_ids({"sources": 7}) == frozenset()
    assert answer_work_ids({"sources": [None, 7, "fulltexts/oa-chen-2018.md"]}) == frozenset()


def test_seed_manifest_work_ids_default_loader_reads_the_shipped_manifest() -> None:
    # The default is the *shipped* manifest, not an empty tolerance stub. Literal ids,
    # not a comprehension over load_seed_manifest(): a loader that returned [] would
    # otherwise satisfy a derived assertion.
    assert seed_manifest_work_ids() == frozenset(
        {
            "chen-2018-undesirable-difficulty",
            "moreira-2019-retrieval-practice",
            "settles-2016-spaced-repetition",
            "hu-luo-fleming-2019-metamemory-offloading",
            "ose-askvik-2020-handwriting",
            "schmidt-2018-luhmann-card-index",
            "mirzababaei-2021-toulmin-agent",
            "asai-2024-openscholar",
        }
    )


def test_seed_manifest_work_ids_skips_blank_ids_and_non_rows() -> None:
    assert seed_manifest_work_ids(lambda: [{"id": "a"}, {"id": " "}, {"title": "no id"}]) == (
        frozenset({"a"})
    )


def test_seed_manifest_work_ids_never_raises_out_of_a_broken_loader() -> None:
    def boom() -> list[dict[str, object]]:
        raise OSError("manifest unreadable")

    assert seed_manifest_work_ids(boom) == frozenset()


def test_first_answer_stays_silent_for_an_off_corpus_answer(tmp_path: Path) -> None:
    def manifest() -> list[dict[str, str]]:
        return [{"id": "chen-2018-undesirable-difficulty"}]

    assert (
        emit_first_answer_if_seed_grounded(tmp_path, _off_corpus_answer(), manifest_loader=manifest)
        is None
    )
    assert has_onboarding_step(tmp_path, "first-answer") is False


def test_first_answer_emits_once_across_a_three_call_trajectory(tmp_path: Path) -> None:
    def manifest() -> list[dict[str, str]]:
        return [{"id": "chen-2018-undesirable-difficulty"}]

    grounded = _seed_grounded_answer()
    trajectory = [
        emit_first_answer_if_seed_grounded(tmp_path, grounded, manifest_loader=manifest)
        for _ in range(3)
    ]
    # ... and the absorbing state survives an off-corpus answer arriving afterwards.
    after = emit_first_answer_if_seed_grounded(
        tmp_path, _off_corpus_answer(), manifest_loader=manifest
    )

    assert trajectory[0]
    assert trajectory[1] is None
    assert trajectory[2] is None
    assert after is None
    with state.connect(tmp_path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM telemetry_events WHERE event_type = 'onboarding-step'"
            " AND json_extract(payload_json, '$.step') = 'first-answer'"
        ).fetchone()[0]
    assert count == 1


def test_first_answer_uses_the_shipped_manifest_when_no_loader_is_injected(
    tmp_path: Path,
) -> None:
    # The default path, not the injected one: `chen-2018-undesirable-difficulty` is a
    # real shipped row, so this proves the rule is wired to the product manifest.
    assert emit_first_answer_if_seed_grounded(tmp_path, _seed_grounded_answer())
    assert has_onboarding_step(tmp_path, "first-answer") is True


def test_first_answer_never_raises_when_the_sink_refuses(tmp_path: Path) -> None:
    _disable_the_telemetry_sink(tmp_path)

    def manifest() -> list[dict[str, str]]:
        return [{"id": "chen-2018-undesirable-difficulty"}]

    assert (
        emit_first_answer_if_seed_grounded(
            tmp_path, _seed_grounded_answer(), manifest_loader=manifest
        )
        is None
    )
    assert has_onboarding_step(tmp_path, "first-answer") is False
