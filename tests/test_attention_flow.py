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

import ast
from pathlib import Path

import pytest

import memoria_vault
from memoria_vault.runtime.attention import inbox as inbox_lib
from memoria_vault.runtime.attention.inbox import (
    write_finding,
    write_proposal,
    write_work_prompt,
)
from memoria_vault.runtime.vaultio import split_frontmatter
from tests.helpers import admitted_cards as _admitted
from tests.helpers import attention_flow_rows as _rows
from tests.helpers import set_attention_config as _configure

pytestmark = pytest.mark.contract


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


def _mints_attention_frontmatter(node: ast.AST) -> bool:
    """True when this node builds a `projection: attention` frontmatter mapping.

    The one syntactic tell every attention-card writer in the tree shares: a dict
    literal whose `projection` key is the constant `"attention"`. It is what
    `lifecycle`, `loudness` and `engine.api` all read to decide that a file in
    `inbox/` is a card at all, so a writer that omits it has not written a card.
    """
    return any(
        isinstance(sub, ast.Dict)
        and any(
            isinstance(key, ast.Constant)
            and key.value == "projection"
            and isinstance(value, ast.Constant)
            and value.value == "attention"
            for key, value in zip(sub.keys, sub.values, strict=True)
            if key is not None
        )
        for sub in ast.walk(node)
    )


def _called_names(node: ast.AST) -> set[str]:
    names = set()
    for sub in ast.walk(node):
        if not isinstance(sub, ast.Call):
            continue
        func = sub.func
        if isinstance(func, ast.Attribute):
            names.add(func.attr)
        elif isinstance(func, ast.Name):
            names.add(func.id)
    return names


def test_no_attention_card_is_minted_outside_the_throttle_and_admission_seam() -> None:
    """Every writer of attention frontmatter calls `inbox.throttled` and `inbox.admit`.

    A rule, because the convention was already broken. Five producers wrote card
    frontmatter directly (issue #1703), so `producers: {<name>: paused}` parsed,
    validated, reported as applied and did nothing for them, and the dashboard's
    flow panel under-counted three producers while its exploration panel counted
    the same producer's cards on disk -- two numbers for one vault with nothing
    flagging the disagreement.

    The rule is deliberately *not* "only `inbox.py` may write a card". Those five
    carry keys `write_finding`/`write_proposal` cannot express (`candidate_tag`,
    `discovered_work_id`, `relation_type`, `source_count`) and deterministic
    `inbox/` filenames they return, journal and re-read for dedupe, which
    `inbox._write`'s `-2`, `-3` suffixing cannot produce. Forcing them through
    those three functions would change the card vocabulary and the filenames,
    which is a bigger and less honest change than making the seam callable. What
    must be single is the *seam*, and this asserts exactly that.

    Syntactic on purpose: it fails on the sixth producer the day it is written,
    with no vault, no fixture and no way for the producer to be added without the
    author seeing this test name.
    """
    package_root = Path(memoria_vault.__file__).parent
    offenders = []
    for path in sorted(package_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not _mints_attention_frontmatter(node):
                continue
            missing = {"throttled", "admit"} - _called_names(node)
            if missing:
                rel = path.relative_to(package_root).as_posix()
                offenders.append(f"{rel}:{node.name} never calls {sorted(missing)}")
    assert offenders == []


def test_the_guard_would_catch_a_producer_that_skipped_the_seam(tmp_path: Path) -> None:
    """The guard's own kill test: a writer shaped like the five, minus the seam.

    Without this, `_mints_attention_frontmatter` returning False for everything --
    a renamed key, a walk that never descends -- reads as a green tree-wide rule
    forever. Escape class 5: a checker whose detector is dead is not a checker.
    """
    bypass = ast.parse(
        "def _write_card(vault, path):\n"
        "    write_frontmatter_doc(path, {'projection': 'attention'}, 'body')\n"
    ).body[0]
    honest = ast.parse(
        "def _write_card(vault, path):\n"
        "    band = inbox.throttled(vault, 'p', 'notice')\n"
        "    write_frontmatter_doc(path, {'projection': 'attention'}, 'body')\n"
        "    inbox.admit(vault, path, 'flag', band, 'p')\n"
    ).body[0]

    assert _mints_attention_frontmatter(bypass)
    assert {"throttled", "admit"} - _called_names(bypass) == {"throttled", "admit"}
    assert _mints_attention_frontmatter(honest)
    assert not {"throttled", "admit"} - _called_names(honest)


def test_the_seam_rejects_a_band_no_reader_rosters(tmp_path: Path) -> None:
    """`loudness: normal` shipped once and stayed, because the five direct producers
    reached no validator at all. They reach this one now, so it has to refuse --
    ahead of the config read, so a paused producer cannot mask a bad band either."""
    with pytest.raises(ValueError, match="loudness must be one of"):
        write_finding(tmp_path, "flag", "f1", "finding", "sweep", target="x.md", loudness="normal")
    _configure(tmp_path, "producers:\n  sweep: paused\n")
    with pytest.raises(ValueError, match="loudness must be one of"):
        inbox_lib.throttled(tmp_path, "sweep", "normal")

    assert not (tmp_path / "inbox").exists()
    assert _rows(tmp_path, "producer-run-skipped") == []
