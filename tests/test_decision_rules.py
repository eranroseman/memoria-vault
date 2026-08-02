"""Contract tests for the pre-registered decision-rule registry (I1 spec §5).

**Three seams, tested at three levels.** `load_decision_rules`/`update_rule_status`
are the registry; `assess_decision_rules` is the pure verdict over assembled
panels; `assemble_dashboard`'s `decision_rules` panel is the wiring. The boundary
cases run against `assess_decision_rules` because a threshold deserves an exact
fixture on both sides of it, but every one of them starts from a *real*
`assemble_dashboard` payload and overrides only the counters under test (`_panels`)
-- a hand-written panel dict would keep asserting happily after the dashboard
renamed a key out from under it. At least one case per auto rule is driven
end-to-end from real telemetry rows and real `inbox/` cards, so the panel keys the
predicates read are proved to be the keys the panels write.

**Trajectory, not fixed point.** Firing is absorbing by design: a rule the PI
applies goes `armed` -> `fired` and drops out of `would_fire` forever. Sampling
only the armed state would pass for an assessor that ignores `status` entirely, so
`test_applying_a_rule_removes_it_from_would_fire_but_not_from_rules` runs the whole
trajectory -- assess, apply, assess again -- and pins both ends. The window
predicate gets the same treatment: six crossing days must not fire, seven must, and
one day of matching drain inside the window must silence it.

**Which and why, not merely whether.** Every `would_fire` entry carries the
`observed` numbers that crossed and, for `attention-throttle`, the producer to act
on. A projection that reported only rule ids would read identically for a rule
matching the wrong panel, so `observed` is asserted field-by-field rather than
through a bare `in`.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import uuid
from pathlib import Path
from typing import Any

import pytest
import yaml

import memoria_vault
from memoria_vault.engine.dashboard import assemble_dashboard
from memoria_vault.runtime import state
from memoria_vault.runtime.decision_rules import (
    AUTO_PREDICATES,
    DEFAULT_RULES_YAML,
    RULES_CONFIG,
    assess_decision_rules,
    load_decision_rules,
    update_rule_status,
)
from memoria_vault.runtime.operations import emit_explicit_disposition_event
from memoria_vault.runtime.subsystems.lib.inbox import write_finding
from memoria_vault.runtime.telemetry import record_telemetry_event

pytestmark = pytest.mark.contract

# The pre-registration itself, pinned as a literal: this list is the promise that
# every beta.1 §4 blocker has a written-down rule, so it must break when a rule is
# renamed, dropped, or quietly added rather than be re-derived from the registry.
SHIPPED_RULE_IDS = [
    "evidence-review-sizing",
    "attention-loudness",
    "reactive-substrate-priority",
    "attention-throttle",
    "srd-contract",
    "seed-corpus",
    "workspace-gate-topology",
    "export-target",
    "multi-device-topology",
    "raw-dataset-bundling",
    "mode-work-creation",
    "non-api-schema-drift",
    "fulltext-v2-shape",
    "warrant-touch-budget",
    "two-window-friction",
    "canvas-authoring",
    "staged-import",
]
AUTO_RULE_IDS = {
    "evidence-review-sizing",
    "attention-loudness",
    "reactive-substrate-priority",
    "attention-throttle",
}


def _write_registry(vault: Path, text: str) -> Path:
    path = vault / RULES_CONFIG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _utc_days(count: int) -> list[str]:
    """The last `count` UTC days, oldest first, re-derived rather than imported.

    Importing the module's own window helper would make every window case compare
    the implementation to itself.
    """
    today = datetime.datetime.now(datetime.UTC).date()
    return [
        (today - datetime.timedelta(days=offset)).isoformat() for offset in reversed(range(count))
    ]


def _admit(vault: Path, day: str, raised_by: str = "sweep") -> None:
    """One `attention-admitted` row on a chosen UTC day.

    Inserted directly because `record_telemetry_event` always stamps *now*, and a
    rolling-window rule cannot be arranged without choosing the day. The column
    list is the shipped DDL's, so schema drift breaks this loudly.
    """
    payload = {
        "card_path": f"inbox/{day}-{raised_by}.md",
        "kind": "flag",
        "loudness": "notice",
        "raised_by": raised_by,
    }
    with state.connect(vault) as conn:
        conn.execute(
            "INSERT INTO telemetry_events (event_id, ts, event_type, payload_json)"
            " VALUES (?, ?, 'attention-admitted', ?)",
            (
                hashlib.sha256(f"{day}{raised_by}".encode()).hexdigest(),
                f"{day}T09:00:00Z",
                json.dumps(payload, sort_keys=True),
            ),
        )


def _panels(vault: Path, **overrides: dict[str, Any]) -> dict[str, Any]:
    """Real assembled panels with named counters replaced.

    The base is what `assemble_dashboard` actually produces, so a renamed panel or
    counter breaks these cases instead of leaving them asserting against a shape
    nothing writes any more.
    """
    panels = assemble_dashboard(vault)
    for panel, counters in overrides.items():
        panels[panel].update(counters)
    return panels


def _ids(assessed: list[dict[str, Any]]) -> list[str]:
    return [entry["id"] for entry in assessed]


def _would_fire(vault: Path) -> list[dict[str, Any]]:
    return assemble_dashboard(vault)["decision_rules"]["would_fire"]


# --- H.3: the registry -------------------------------------------------------


def test_shipped_registry_arms_all_seventeen_rules_with_four_auto(tmp_path: Path) -> None:
    """A vault with no registry file loads the shipped pre-registration.

    Producer state named: this *is* the state that ships. `.memoria/config/` files
    are not seeded (`attention.yaml`, `policy.yaml` and `edges.yaml` are all
    code-default too), so an empty vault is where the registry has to be readable.
    """
    rules = load_decision_rules(tmp_path)

    assert [rule["id"] for rule in rules] == SHIPPED_RULE_IDS
    assert {rule["id"] for rule in rules if rule["check"] == "auto"} == AUTO_RULE_IDS
    assert all(rule["status"] == "armed" for rule in rules)
    assert all(
        rule[field] for rule in rules for field in ("blocker", "metric", "window", "threshold")
    )


def test_every_auto_rule_has_a_predicate(tmp_path: Path) -> None:
    """An `auto` rule with no predicate can never fire, which is worse than manual.

    Pinned in both directions: a fifth auto rule without an entry in
    `AUTO_PREDICATES` is a rule that silently never triggers, and a predicate whose
    rule was renamed is dead code the registry no longer reaches.
    """
    auto = {rule["id"] for rule in load_decision_rules(tmp_path) if rule["check"] == "auto"}

    assert set(AUTO_PREDICATES) == auto


def test_the_registry_has_exactly_one_source_of_truth() -> None:
    """The shipped rules live in code *or* in `workspace_seed`, never in both.

    Two copies of a pre-registration drift, and the drift is invisible: the
    dashboard would read the seeded file while review argued about the constant.
    """
    seeded = Path(memoria_vault.__file__).parent / "product/workspace_seed" / RULES_CONFIG

    assert not seeded.exists(), (
        f"{seeded} now exists alongside decision_rules.DEFAULT_RULES_YAML, so the "
        "registry has two sources that can drift. Keep one: either delete the "
        "constant and load the seeded file, or drop the seed file."
    )


def test_a_vault_registry_file_replaces_the_shipped_rules(tmp_path: Path) -> None:
    """Present, the file *is* the registry -- it is not merged with the defaults."""
    _write_registry(
        tmp_path,
        "- id: local-only\n"
        '  blocker: "Local"\n'
        '  metric: "m"\n'
        '  window: "w"\n'
        '  threshold: "t"\n'
        '  recommendation: "r"\n'
        "  check: manual\n"
        "  status: armed\n",
    )

    rules = load_decision_rules(tmp_path)

    assert [rule["id"] for rule in rules] == ["local-only"]


def test_malformed_entry_is_skipped_not_fatal(tmp_path: Path) -> None:
    _write_registry(tmp_path, DEFAULT_RULES_YAML + "- id: broken\n")

    rules = load_decision_rules(tmp_path)

    assert [rule["id"] for rule in rules] == SHIPPED_RULE_IDS


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("- id: x\n  blocker: [", "unparsable YAML"),
        ("order_by: [priority]\n", "a mapping where the registry is a list"),
        # A scalar document is the one shape that a list guard cannot fake its way
        # through: iterating an int raises, so "skipped, never fatal" only holds if
        # the document type is checked rather than merely its truthiness.
        ("42\n", "a bare scalar document"),
        ("- just a string\n", "a non-mapping entry"),
        ("- id: x\n", "an entry missing every field but id"),
        (
            "- id: x\n"
            '  blocker: "b"\n  metric: "m"\n  window: "w"\n  threshold: "t"\n'
            '  recommendation: "r"\n  check: sometimes\n  status: armed\n',
            "an unknown check",
        ),
        (
            "- id: x\n"
            '  blocker: "b"\n  metric: "m"\n  window: "w"\n  threshold: "t"\n'
            '  recommendation: "r"\n  check: auto\n  status: pending\n',
            "an unknown status",
        ),
        (
            "- id: x\n"
            '  blocker: "b"\n  metric: "m"\n  window: "  "\n  threshold: "t"\n'
            '  recommendation: "r"\n  check: auto\n  status: armed\n',
            "a whitespace-only required field",
        ),
    ],
)
def test_unusable_registry_content_reads_as_no_rules(
    tmp_path: Path, text: str, reason: str
) -> None:
    """A registry the PI broke must not be able to take a dashboard read down."""
    _write_registry(tmp_path, text)

    assert load_decision_rules(tmp_path) == [], reason


def test_update_rule_status_materializes_the_file_and_round_trips(tmp_path: Path) -> None:
    """First write creates `.memoria/config/decision-rules.yaml` from the shipped rules."""
    path = tmp_path / RULES_CONFIG
    assert not path.exists()

    update_rule_status(tmp_path, "attention-throttle", "fired")

    assert path.is_file()
    rules = {rule["id"]: rule for rule in load_decision_rules(tmp_path)}
    assert rules["attention-throttle"]["status"] == "fired"
    # The flip is one rule's, not the registry's: the other sixteen stay armed and
    # the roster is unchanged.
    assert list(rules) == SHIPPED_RULE_IDS
    assert [rule_id for rule_id, rule in rules.items() if rule["status"] != "armed"] == [
        "attention-throttle"
    ]


def test_update_rule_status_preserves_fields_this_module_does_not_know(tmp_path: Path) -> None:
    """The raw entries are rewritten, so a PI's own annotation survives the flip."""
    _write_registry(
        tmp_path,
        DEFAULT_RULES_YAML.replace("- id: seed-corpus\n", "- id: seed-corpus\n  note: mine\n"),
    )

    update_rule_status(tmp_path, "seed-corpus", "retired")

    text = (tmp_path / RULES_CONFIG).read_text(encoding="utf-8")
    assert "note: mine" in text


@pytest.mark.parametrize(
    ("rule_id", "status"),
    [("attention-throttle", "smouldering"), ("no-such-rule", "fired")],
)
def test_update_rule_status_refuses_an_unknown_rule_or_status(
    tmp_path: Path, rule_id: str, status: str
) -> None:
    """A typo must not report success while changing nothing."""
    with pytest.raises(ValueError):
        update_rule_status(tmp_path, rule_id, status)

    assert not (tmp_path / RULES_CONFIG).exists()


# --- O2 W.3: the staged-import stop rule -------------------------------------


def test_staged_import_rule_is_seeded_manual_and_armed(tmp_path: Path) -> None:
    """O2 spec §7's stop rule is pre-registered before Phase 1's first staged run.

    Manual by construction: its evidence is whether the PI's own triage session
    fit, which no counter observes, so `AUTO_PREDICATES` must stay at four.
    """
    rules = {rule["id"]: rule for rule in load_decision_rules(tmp_path)}

    rule = rules["staged-import"]
    assert rule["check"] == "manual"
    assert rule["status"] == "armed"
    assert rule["recommendation"] == (
        "After each stage (10 works, then 100): if the run's triage worklist did not fit "
        "one session, or rebuild/query latency broke the session's flow, stop the protocol "
        "and record the observation in the diary and this rule — the observation IS the "
        "finding."
    )
    assert "import-run" in rule["metric"]
    assert "Shape-1/Shape-2 query latency" in rule["metric"]


# --- H.4: assessment ---------------------------------------------------------


def test_a_quiet_vault_fires_nothing_but_still_reports_the_registry(tmp_path: Path) -> None:
    panel = assemble_dashboard(tmp_path)["decision_rules"]

    assert panel["would_fire"] == []
    assert [rule["id"] for rule in panel["rules"]] == SHIPPED_RULE_IDS


def test_manual_rules_never_fire_however_loud_the_vault(tmp_path: Path) -> None:
    """Every counter over every threshold; only the four auto rules may appear."""
    panels = _panels(
        tmp_path,
        attention_flow={
            "open_total": 100,
            "open_by_loudness": {"alert": 99, "notice": 1},
            "inflow_by_day": dict.fromkeys(_utc_days(7), 5),
            "drain_by_day": {},
            "per_producer": {"sweep": 40},
        },
        reads_staleness={"reads": 100, "staleness_hits": 90},
        evidence_review={"events": 100, "actions": {"accept": 1}, "mean_duration_s": 1.0},
    )

    assessed = assess_decision_rules(panels, load_decision_rules(tmp_path))

    assert set(_ids(assessed)) == AUTO_RULE_IDS


def test_a_rule_the_pi_demoted_to_manual_stops_firing(tmp_path: Path) -> None:
    """`check:` is PI-editable, so demoting a rule has to actually demote it.

    `AUTO_PREDICATES` is keyed by rule id, so an assessor that gated on `status`
    alone would keep firing a rule the PI deliberately took off automatic and the
    field would be decoration. The registry is written through the loader rather
    than hand-composed, so the fixture is the file the product itself would write.
    """
    rules = load_decision_rules(tmp_path)
    for rule in rules:
        if rule["id"] == "attention-throttle":
            rule["check"] = "manual"
    _write_registry(tmp_path, yaml.safe_dump(rules, sort_keys=False, allow_unicode=True))
    for day in _utc_days(7):
        _admit(tmp_path, day)

    assert "attention-throttle" not in _ids(_would_fire(tmp_path))


@pytest.mark.parametrize(
    ("crossing_days", "fires"),
    [(7, True), (6, False), (0, False)],
)
def test_attention_throttle_needs_every_day_in_the_window(
    tmp_path: Path, crossing_days: int, fires: bool
) -> None:
    """Six crossing days is not seven. The oldest day is the one left out."""
    window = _utc_days(7)
    inflow = dict.fromkeys(window[7 - crossing_days :], 1)
    panels = _panels(tmp_path, attention_flow={"inflow_by_day": inflow, "drain_by_day": {}})

    assessed = assess_decision_rules(panels, load_decision_rules(tmp_path))

    assert ("attention-throttle" in _ids(assessed)) is fires


def test_attention_throttle_is_silenced_by_one_matching_day(tmp_path: Path) -> None:
    """Drain equal to inflow on a single day inside the window is not "exceeds"."""
    window = _utc_days(7)
    inflow = dict.fromkeys(window, 2)
    panels = _panels(
        tmp_path,
        attention_flow={"inflow_by_day": inflow, "drain_by_day": {window[3]: 2}},
    )

    assessed = assess_decision_rules(panels, load_decision_rules(tmp_path))

    assert "attention-throttle" not in _ids(assessed)


def test_attention_throttle_reports_the_window_and_the_producer_to_quiet(
    tmp_path: Path,
) -> None:
    """End-to-end from real telemetry rows: which producer, over which days, by how much.

    The busiest producer is deliberately the alphabetically *last* one: `sweep`
    admits seven and `analyze-gaps` one. A predicate that took the first key, the
    last key, or the smallest count names a different producer here, where a
    fixture whose loudest producer also sorted first would let all four read the
    same.
    """
    window = _utc_days(7)
    for day in window:
        _admit(tmp_path, day, raised_by="sweep")
    _admit(tmp_path, window[0], raised_by="analyze-gaps")

    entry = next(rule for rule in _would_fire(tmp_path) if rule["id"] == "attention-throttle")

    assert entry["observed"] == {
        "window_days": 7,
        "window_start": window[0],
        "window_end": window[-1],
        "inflow": 8,
        "drain": 0,
        "top_producer": "sweep",
        "top_producer_admissions": 7,
    }
    assert entry["observed"]["window_start"] < entry["observed"]["window_end"]
    assert "quieting or pausing the top producer" in entry["recommendation"]


def test_attention_throttle_counts_a_real_disposition_as_drain(tmp_path: Path) -> None:
    """The drain series is the journal's, proved by emitting one on today's day.

    Today is inside the window either way, so a single real disposition on the
    newest day is enough to break the run -- no journal backdating needed.
    """
    for day in _utc_days(7):
        _admit(tmp_path, day)
    assert "attention-throttle" in _ids(_would_fire(tmp_path))

    emit_explicit_disposition_event(
        tmp_path,
        decision="accept",
        item_type="attention",
        item_id="inbox/a.md",
        actor="pi",
        machine="rules-test",
    )

    assert "attention-throttle" not in _ids(_would_fire(tmp_path))


@pytest.mark.parametrize(
    ("open_total", "push", "fires"),
    [(10, 6, True), (10, 5, False), (9, 9, False), (10, 0, False), (11, 6, True)],
)
def test_attention_loudness_needs_a_majority_of_at_least_ten_open_cards(
    tmp_path: Path, open_total: int, push: int, fires: bool
) -> None:
    """Exactly half is not "more than half", and nine loud cards is not a pattern."""
    panels = _panels(
        tmp_path,
        attention_flow={
            "open_total": open_total,
            "open_by_loudness": {"alert": push, "notice": open_total - push},
        },
    )

    assessed = assess_decision_rules(panels, load_decision_rules(tmp_path))

    assert ("attention-loudness" in _ids(assessed)) is fires


@pytest.mark.parametrize(
    "by_loudness",
    [
        {"alert": 3, "block": 3, "notice": 4},
        {"alert": 0, "block": 6, "notice": 4},
    ],
)
def test_attention_loudness_counts_block_as_a_push_band(
    tmp_path: Path, by_loudness: dict[str, int]
) -> None:
    """`block` pushes harder than `alert`, so it belongs in the numerator.

    Both fixtures are chosen to fail on an implementation that counts `alert`
    alone: 3/10 and 0/10 are nowhere near the threshold, and only the 6/10 the two
    bands sum to crosses it. `notice` stays out -- it is the band the writers
    default to, so counting it would make every busy vault look like a policy
    failure.
    """
    panels = _panels(
        tmp_path,
        attention_flow={"open_total": 10, "open_by_loudness": by_loudness},
    )

    entry = next(
        rule
        for rule in assess_decision_rules(panels, load_decision_rules(tmp_path))
        if rule["id"] == "attention-loudness"
    )

    assert entry["observed"] == {
        "open_total": 10,
        "push_bands": ["alert", "block"],
        "push_open": 6,
        "push_share": 0.6,
    }


def test_attention_loudness_fires_on_real_inbox_cards(tmp_path: Path) -> None:
    """End-to-end: eleven cards a real producer wrote, six of them alert-band."""
    for index in range(6):
        write_finding(tmp_path, "flag", f"loud-{index}", "x", "sweep", target=f"notes/{index}.md")
    for index in range(5):
        write_finding(
            tmp_path,
            "flag",
            f"calm-{index}",
            "x",
            "sweep",
            target=f"notes/q{index}.md",
            loudness="notice",
        )

    entry = next(rule for rule in _would_fire(tmp_path) if rule["id"] == "attention-loudness")

    assert entry["observed"]["open_total"] == 11
    assert entry["observed"]["push_open"] == 6


@pytest.mark.parametrize(
    ("reads", "hits", "fires"),
    [(20, 3, True), (20, 2, False), (19, 19, False), (20, 0, False)],
)
def test_reactive_substrate_priority_needs_felt_staleness(
    tmp_path: Path, reads: int, hits: int, fires: bool
) -> None:
    """Exactly one hit in ten is not "more than 10%", and nineteen reads is not a window."""
    panels = _panels(tmp_path, reads_staleness={"reads": reads, "staleness_hits": hits})

    assessed = assess_decision_rules(panels, load_decision_rules(tmp_path))

    assert ("reactive-substrate-priority" in _ids(assessed)) is fires


def test_reactive_substrate_priority_fires_on_real_read_events(tmp_path: Path) -> None:
    """End-to-end: twenty recorded reads, three of them staleness hits."""
    for index in range(20):
        record_telemetry_event(
            tmp_path,
            "read-observed.v1",
            {"workflow": "attention", "staleness_hit": index < 3},
        )

    entry = next(
        rule for rule in _would_fire(tmp_path) if rule["id"] == "reactive-substrate-priority"
    )

    assert entry["observed"] == {"reads": 20, "staleness_hits": 3, "staleness_share": 0.15}


@pytest.mark.parametrize(
    ("events", "decided", "fires"),
    [(10, 4, True), (10, 5, False), (9, 0, False), (10, 10, False)],
)
def test_evidence_review_sizing_fires_when_the_gate_is_skipped(
    tmp_path: Path, events: int, decided: int, fires: bool
) -> None:
    """Half the items decided is not a skipped gate; fewer than half is."""
    panels = _panels(
        tmp_path,
        evidence_review={
            "events": events,
            "actions": {"accept": decided} if decided else {},
            "mean_duration_s": 3.0,
        },
    )

    assessed = assess_decision_rules(panels, load_decision_rules(tmp_path))

    assert ("evidence-review-sizing" in _ids(assessed)) is fires


def test_evidence_review_sizing_fires_on_real_review_events(tmp_path: Path) -> None:
    """End-to-end: ten review events, four carrying a decision."""
    base = {
        "timestamp": "2026-03-01T00:00:00Z",
        "session_id": "s-1",
        "surface": "cli",
        "workflow": "evidence-review",
    }
    for index in range(10):
        decided = index < 4
        record_telemetry_event(
            tmp_path,
            "empirical_event.v1",
            {
                **base,
                "event_id": str(uuid.uuid4()),
                "event_type": "disposition.recorded" if decided else "view.opened",
                **({"decision": "accept", "reason_code": "useful"} if decided else {}),
            },
        )

    entry = next(rule for rule in _would_fire(tmp_path) if rule["id"] == "evidence-review-sizing")

    assert entry["observed"] == {"events": 10, "decided": 4, "skip_rate": 0.6}


def test_applying_a_rule_removes_it_from_would_fire_but_not_from_rules(tmp_path: Path) -> None:
    """The whole trajectory, because firing is absorbing.

    An assessor that ignored `status` entirely would look identical at the armed
    end of this test, so the point is the second half: after the PI applies the
    recommendation the rule keeps reporting the same crossed numbers forever
    unless `status` gates it. `rules` still carries it -- retired evidence is
    still evidence.
    """
    for day in _utc_days(7):
        _admit(tmp_path, day)
    assert "attention-throttle" in _ids(_would_fire(tmp_path))

    update_rule_status(tmp_path, "attention-throttle", "fired")

    panel = assemble_dashboard(tmp_path)["decision_rules"]
    assert "attention-throttle" not in _ids(panel["would_fire"])
    statuses = {rule["id"]: rule["status"] for rule in panel["rules"]}
    assert statuses["attention-throttle"] == "fired"
    assert [rule["id"] for rule in panel["rules"]] == SHIPPED_RULE_IDS


def test_a_retired_rule_never_fires_again(tmp_path: Path) -> None:
    for day in _utc_days(7):
        _admit(tmp_path, day)
    update_rule_status(tmp_path, "attention-throttle", "retired")

    assert "attention-throttle" not in _ids(_would_fire(tmp_path))


def test_assembly_recommends_and_never_acts(tmp_path: Path) -> None:
    """Assessment is a read (plan amendment 2026-07-29 §1).

    Repeated assembly over a vault whose rule is crossing its threshold must mint
    no card and flip no status -- the whole difference between this panel and the
    `apply-decision-rule-notices` operation that owns those effects.
    """
    for day in _utc_days(7):
        _admit(tmp_path, day)

    for _ in range(3):
        assert "attention-throttle" in _ids(_would_fire(tmp_path))

    assert list(tmp_path.glob("inbox/*.md")) == []
    assert not (tmp_path / RULES_CONFIG).exists()
    assert all(rule["status"] == "armed" for rule in load_decision_rules(tmp_path))
