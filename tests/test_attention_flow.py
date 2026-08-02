"""Contract tests for attention flow telemetry and PI-owned throttles (I1 spec §6.3-§6.4).

**Producer states, named.** Every row asserted here is inserted by a real card
writer; nothing hand-writes a `telemetry_events` row. The states that matter are
the ones where a writer *does not* admit -- a deduped slug, a fingerprint touch,
a paused producer -- because an inflow counter that counted attempts instead of
cards would read identically on the admitting path and only diverge here.

**Trajectories, not fixed points.** The dedupe and fingerprint cases run the same
writer twice and assert the count stops at one, which is the transition a
per-call counter cannot survive; the throttle cases run one producer at each mode
in the same vault, so a helper that ignored `raised_by` and throttled everything
reads differently rather than identically.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.subsystems.lib.inbox import (
    write_finding,
    write_proposal,
    write_work_prompt,
)
from memoria_vault.runtime.vaultio import split_frontmatter

pytestmark = pytest.mark.contract


def _rows(vault: Path, event_type: str) -> list[dict[str, str]]:
    # Insertion order, not `ts`: `now_iso` is second-resolution and `event_id` is a
    # random uuid4, so two rows written in the same second have no stable order of
    # their own and these assertions are about which write admitted, in sequence.
    with state.connect(vault) as conn:
        rows = conn.execute(
            "SELECT payload_json FROM telemetry_events WHERE event_type = ? ORDER BY rowid",
            (event_type,),
        ).fetchall()
    return [json.loads(str(row["payload_json"])) for row in rows]


def _admitted(vault: Path) -> list[dict[str, str]]:
    return _rows(vault, "attention-admitted")


def _configure(vault: Path, body: str) -> None:
    config = vault / ".memoria/config/attention.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(body, encoding="utf-8")


def _band(path: Path) -> str:
    frontmatter, _ = split_frontmatter(path.read_text(encoding="utf-8"))
    return str(frontmatter["loudness"])


def test_each_writer_admits_one_card_with_its_own_kind_band_and_producer(tmp_path: Path) -> None:
    """All three writers, three different kinds and bands, one vault.

    The payload is asserted field-for-field rather than by count: a helper that
    stamped one producer or one band for every card would keep a count-only
    assertion green.
    """
    write_finding(tmp_path, "flag", "f1", "finding", "sweep", target="notes/x.md")
    write_proposal(
        tmp_path, "candidate", "c1", "act", "for", "against", "tip", "likely", "analyze-gaps"
    )
    write_work_prompt(tmp_path, "w1", "act", "happened", "worklists", target="notes/y.md")

    rows = _admitted(tmp_path)

    assert [row["kind"] for row in rows] == ["flag", "candidate", "work-prompt"]
    assert [row["raised_by"] for row in rows] == ["sweep", "analyze-gaps", "worklists"]
    assert [row["loudness"] for row in rows] == ["alert", "notice", "notice"]
    assert [row["card_path"] for row in rows] == [
        "inbox/flag-f1.md",
        "inbox/candidate-c1.md",
        "inbox/work-prompt-w1.md",
    ]


def test_a_deduped_write_admits_nothing_the_second_time(tmp_path: Path) -> None:
    """Both deduping writers, run twice each. Inflow counts cards, not calls."""
    first_finding = write_finding(
        tmp_path, "flag", "f1", "finding", "sweep", target="notes/x.md", dedupe_slug="f1"
    )
    second_finding = write_finding(
        tmp_path, "flag", "f1", "finding", "sweep", target="notes/x.md", dedupe_slug="f1"
    )
    write_work_prompt(
        tmp_path, "w1", "act", "happened", "worklists", target="notes/y.md", dedupe_slug="w1"
    )
    write_work_prompt(
        tmp_path, "w1", "act", "happened", "worklists", target="notes/y.md", dedupe_slug="w1"
    )

    assert first_finding is not None
    assert second_finding is None
    # `kind` too, not only the path: the deduping branches build their own
    # filename and never route through `_write`, so they are the two places a
    # hard-coded kind would go unnoticed.
    assert [(row["card_path"], row["kind"]) for row in _admitted(tmp_path)] == [
        ("inbox/flag-f1.md", "flag"),
        ("inbox/work-prompt-w1.md", "work-prompt"),
    ]


def test_a_fingerprint_touch_admits_nothing(tmp_path: Path) -> None:
    """A standing card observed again is not new inflow -- the card never left."""
    write_finding(
        tmp_path, "flag", "f1", "finding", "sweep", target="notes/x.md", fingerprint="cond-1"
    )
    touched = write_finding(
        tmp_path, "flag", "f1", "finding again", "sweep", target="notes/x.md", fingerprint="cond-1"
    )

    assert touched is None
    assert len(_admitted(tmp_path)) == 1


def test_a_quiet_producer_mints_at_quiet_and_is_still_counted(tmp_path: Path) -> None:
    """Demotion is not suppression: the card lands, at the band that sorts last,
    and the admission row records the band it actually got rather than the one
    the producer asked for."""
    _configure(tmp_path, "producers:\n  enrich-source: quiet\n")

    path = write_finding(
        tmp_path, "flag", "e1", "note", "enrich-source", target="notes/x.md", loudness="alert"
    )

    assert path is not None
    assert _band(path) == "quiet"
    assert [row["loudness"] for row in _admitted(tmp_path)] == ["quiet"]


def test_a_paused_producer_mints_nothing_and_records_the_skip(tmp_path: Path) -> None:
    _configure(tmp_path, "producers:\n  sweep: paused\n")

    result = write_finding(tmp_path, "flag", "s1", "note", "sweep", target="notes/x.md")

    assert result is None
    assert not list((tmp_path / "inbox").glob("*.md"))
    assert _rows(tmp_path, "producer-run-skipped") == [{"producer": "sweep", "reason": "paused"}]
    assert _admitted(tmp_path) == []


def test_a_throttle_applies_to_one_producer_and_not_the_others(tmp_path: Path) -> None:
    """Three modes in one vault. A throttle that ignored `raised_by` would pause
    or demote all three here, and a config read that failed open would demote none."""
    _configure(tmp_path, "producers:\n  sweep: paused\n  enrich-source: quiet\n")

    paused = write_finding(tmp_path, "flag", "a", "n", "sweep", target="notes/a.md")
    quieted = write_finding(
        tmp_path, "flag", "b", "n", "enrich-source", target="notes/b.md", loudness="alert"
    )
    untouched = write_finding(
        tmp_path, "flag", "c", "n", "workspace-scan", target="notes/c.md", loudness="alert"
    )

    assert paused is None
    assert quieted is not None and _band(quieted) == "quiet"
    assert untouched is not None and _band(untouched) == "alert"
    assert [row["raised_by"] for row in _admitted(tmp_path)] == [
        "enrich-source",
        "workspace-scan",
    ]


def test_every_writer_honours_a_pause(tmp_path: Path) -> None:
    """One skip row per withheld run, from each of the three writers -- so the
    "runs skipped this week" reading counts every producer, not only findings."""
    _configure(tmp_path, "producers:\n  sweep: paused\n")

    finding = write_finding(tmp_path, "flag", "f", "n", "sweep", target="notes/x.md")
    proposal = write_proposal(
        tmp_path, "candidate", "c", "act", "for", "against", "tip", "likely", "sweep"
    )
    prompt = write_work_prompt(tmp_path, "w", "act", "happened", "sweep", target="notes/y.md")

    assert (finding, proposal, prompt) == (None, None, None)
    assert len(_rows(tmp_path, "producer-run-skipped")) == 3


def test_a_paused_producer_skips_before_the_dedupe_and_fingerprint_reads(tmp_path: Path) -> None:
    """A pause is a no-op run, not a suppressed write: it must not touch a
    standing card's `last_seen` either, which is the one write the fingerprint
    path performs when it returns None for its own reasons."""
    standing = write_finding(
        tmp_path, "flag", "f1", "finding", "sweep", target="notes/x.md", fingerprint="cond-1"
    )
    assert standing is not None
    before = standing.read_text(encoding="utf-8")
    _configure(tmp_path, "producers:\n  sweep: paused\n")

    again = write_finding(
        tmp_path, "flag", "f1", "finding", "sweep", target="notes/x.md", fingerprint="cond-1"
    )

    assert again is None
    assert standing.read_text(encoding="utf-8") == before
    assert len(_rows(tmp_path, "producer-run-skipped")) == 1


def test_a_nameless_producer_is_admitted_as_unknown(tmp_path: Path) -> None:
    """`raised_by` is unvalidated at the writer and `record_telemetry_event`
    rejects a blank field, so a nameless producer's admission would be dropped by
    the observer's own `except` -- losing the card from every denominator instead
    of naming it. `unknown` keeps it counted."""
    write_finding(tmp_path, "flag", "f1", "finding", "", target="notes/x.md")

    assert [row["raised_by"] for row in _admitted(tmp_path)] == ["unknown"]


def test_a_failing_telemetry_write_never_costs_the_card(tmp_path, monkeypatch) -> None:
    """Recording is an observer, never a gate. Both directions: an admission that
    cannot be written still writes the card, and a skip that cannot be recorded
    still skips -- a pause must not become a write because telemetry is down."""

    def _explode(*args: object, **kwargs: object) -> str:
        raise RuntimeError("telemetry unavailable")

    monkeypatch.setattr("memoria_vault.runtime.telemetry.record_telemetry_event", _explode)

    admitted = write_finding(tmp_path, "flag", "f1", "finding", "sweep", target="notes/x.md")
    _configure(tmp_path, "producers:\n  sweep: paused\n")
    skipped = write_finding(tmp_path, "flag", "f2", "finding", "sweep", target="notes/y.md")

    assert admitted is not None and admitted.is_file()
    assert skipped is None
    assert [path.name for path in (tmp_path / "inbox").glob("*.md")] == ["flag-f1.md"]


def test_an_unthrottled_vault_needs_no_config_file(tmp_path: Path) -> None:
    """The shipped default: no `attention.yaml` at all, every producer active."""
    path = write_finding(
        tmp_path, "flag", "f1", "finding", "sweep", target="notes/x.md", loudness="alert"
    )

    assert path is not None
    assert _band(path) == "alert"
    assert _rows(tmp_path, "producer-run-skipped") == []
