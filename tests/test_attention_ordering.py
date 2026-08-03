"""Contract tests for the attention ordering contract (I1 spec §6.2).

**Producer states, named.** Every factor here is read off a card written by the
real `inbox` writer and then aged or marked the way its own producer marks it --
never by hand-writing `rank_factors` into a fixture, which would prove the
assertion and not the producer.

- `loudness` is the `loudness=` argument the writers already take.
- `created` is rewritten to a date relative to `date.today()`, the only way to
  produce age variation without a clock; the writers stamp today.
- `priority` and `stale` are the two fields spec §6.2 says readers honor and no
  writer sets, so a PI hand-edit of the card file *is* their producer. One case
  writes a card with no `loudness:` at all, the other hand-written state.
- `impact` has no producer until the graph plan's ERP-C.6 lands
  `propagation.active_project_slices`; its test installs that symbol and pins the
  call shape ERP-C.6 has to meet, exactly as I1 T.4 did for
  `state.concept_consequence`.

**Trajectories, not fixed points.** Each factor case holds every other factor
equal and inverts the alphabetical order of the filenames, so a sort that ignored
the factor -- or that fell back to the shipped alphabetical order -- reads
differently rather than identically. The `order_by` cases additionally prove a
dropped factor is really dropped, not merely reordered.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

import pytest

from memoria_vault.cli import main
from memoria_vault.engine import api as engine_api
from memoria_vault.runtime import propagation
from memoria_vault.runtime.attention.inbox import write_finding
from memoria_vault.runtime.attention_config import (
    DEFAULT_ORDER_BY,
    attention_order_by,
    normalize_order_by,
    producer_mode,
)
from memoria_vault.runtime.vaultio import (
    frontmatter_doc,
    split_frontmatter,
    write_frontmatter_doc,
)

pytestmark = pytest.mark.contract


def _aged(days: int) -> str:
    """A `created:` stamp `days` old, relative to the same local today the writers use."""
    return (datetime.date.today() - datetime.timedelta(days=days)).isoformat()


def _card(
    vault: Path,
    title: str,
    *,
    loudness: str = "notice",
    age_days: int = 0,
    priority: str = "",
    stale: bool = False,
    target: str = "notes/x.md",
    raised_by: str = "sweep",
) -> str:
    """Mint one card through the real writer, then age or mark it as its PI would."""
    path = write_finding(
        vault, "flag", title, f"finding {title}", raised_by, target=target, loudness=loudness
    )
    assert path is not None
    frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
    frontmatter["created"] = _aged(age_days)
    if priority:
        frontmatter["priority"] = priority
    if stale:
        frontmatter["stale"] = True
    write_frontmatter_doc(path, frontmatter, body)
    return path.relative_to(vault).as_posix()


def _hand_card(vault: Path, name: str, **frontmatter: Any) -> str:
    """Hand-write an `inbox/` card. `inbox/**` is a documented write target."""
    (vault / "inbox").mkdir(parents=True, exist_ok=True)
    path = vault / "inbox" / name
    base = {
        "title": name.removesuffix(".md"),
        "projection": "attention",
        "attention_kind": "flag",
        "attention_status": "open",
        "raised_by": "hand",
        "created": _aged(0),
    }
    path.write_text(frontmatter_doc({**base, **frontmatter}, "# Finding\n\nx\n"), encoding="utf-8")
    return path.relative_to(vault).as_posix()


def _order(vault: Path, **kwargs: Any) -> list[str]:
    return [card["path"] for card in engine_api.read_attention(vault, **kwargs)["attention"]]


def _factors(vault: Path, rel: str) -> dict[str, Any]:
    cards = engine_api.read_attention(vault)["attention"]
    return next(card["rank_factors"] for card in cards if card["path"] == rel)


def _write_config(vault: Path, body: str) -> None:
    config = vault / ".memoria/config/attention.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(body, encoding="utf-8")


def test_default_order_is_block_pin_then_priority_then_loudness(tmp_path: Path) -> None:
    """The full default key on one queue, with the filenames in the reverse order.

    Alphabetical -- the sort this contract replaces -- would read
    `aa, bb, mm, zz`, so this fails loudly rather than coincidentally passing on
    the shipped behaviour.
    """
    quiet = _card(tmp_path, "bb quiet", loudness="quiet", age_days=100)
    alert = _card(tmp_path, "aa alert", loudness="alert", age_days=30)
    prioritized = _card(tmp_path, "mm notice", loudness="notice", priority="high")
    blocked = _card(tmp_path, "zz block", loudness="block")

    assert _order(tmp_path) == [blocked, prioritized, alert, quiet]


def test_block_pin_outranks_a_prioritized_card(tmp_path: Path) -> None:
    """The pin is not a factor: PI priority outranks every machine-set factor
    *except* this one, so a `priority: high` card still sorts behind a block."""
    prioritized = _card(tmp_path, "aa prioritized quiet", loudness="quiet", priority="high")
    blocked = _card(tmp_path, "zz blocked", loudness="block", age_days=0)

    assert _order(tmp_path) == [blocked, prioritized]


def test_age_breaks_ties_oldest_first(tmp_path: Path) -> None:
    """Age is the tiebreaker, never the criterion: two cards equal in every other
    factor order oldest-first, and the older one is the alphabetically later."""
    new = _card(tmp_path, "aa new", loudness="alert", age_days=0)
    old = _card(tmp_path, "zz old", loudness="alert", age_days=45)

    assert _order(tmp_path) == [old, new]
    assert _factors(tmp_path, old)["age_days"] == 45


def test_age_days_is_signed_and_zero_when_unparsable(tmp_path: Path) -> None:
    """The two `created:` states with no arithmetic: unstamped reads 0 (understates
    rather than invents), future-dated reads negative and therefore newest. Both
    keep `engine.dashboard`'s `0-7d` bucket, which is what H.1 shipped."""
    future = _card(tmp_path, "future", age_days=-5)
    garbled = _hand_card(tmp_path, "garbled.md", created="last tuesday")

    assert _factors(tmp_path, future)["age_days"] == -5
    assert _factors(tmp_path, garbled)["age_days"] == 0


def test_priority_is_disclosed_verbatim_and_only_high_ranks(tmp_path: Path) -> None:
    """A misspelled `priority:` is reported exactly as written and changes nothing.

    Two claims in one arrangement: the payload never normalizes the PI's text, and
    the reader honors only the exact value `high`, so the typo cannot be read as a
    silent promotion.
    """
    typo = _card(tmp_path, "aa typo", loudness="quiet", priority="hgih")
    plain = _card(tmp_path, "zz plain", loudness="alert")

    assert _factors(tmp_path, typo)["priority"] == "hgih"
    assert _order(tmp_path) == [plain, typo]


def test_a_bandless_card_reads_and_ranks_as_notice(tmp_path: Path) -> None:
    """A hand-written card need not carry `loudness:`. The band it is actually
    treated as is `notice` -- the same default the dashboard's counter reads --
    so it sorts between `alert` and `quiet` rather than after both."""
    alert = _card(tmp_path, "zz alert", loudness="alert")
    quiet = _card(tmp_path, "aa quiet", loudness="quiet")
    bare = _hand_card(tmp_path, "bare.md")

    assert _factors(tmp_path, bare)["loudness"] == "notice"
    assert _order(tmp_path) == [alert, bare, quiet]


def test_an_unrostered_band_is_disclosed_verbatim_and_ranks_as_notice(tmp_path: Path) -> None:
    """A band outside `inbox.LOUDNESS` is producible: `enrichment` shipped
    `loudness: normal` for a whole release, and `inbox/**` is hand-editable.

    Distinct from the bandless case above, which normalizes to `"notice"` before
    it reaches the rank map. Here the value is carried through verbatim -- the PI
    has to be able to see the typo -- and only the *rank* falls back, to the same
    band the dashboard counts a bandless card in. Ranking it last instead would
    bury a card its author meant to be loud.
    """
    alert = _card(tmp_path, "zz alert", loudness="alert")
    quiet = _card(tmp_path, "aa quiet", loudness="quiet")
    unrostered = _hand_card(tmp_path, "unrostered.md", loudness="normal")

    assert _factors(tmp_path, unrostered)["loudness"] == "normal"
    assert _order(tmp_path) == [alert, unrostered, quiet]


def test_staleness_ranks_a_marked_card_ahead_of_an_unmarked_one(tmp_path: Path) -> None:
    """Only a real YAML boolean is a staleness mark.

    The same reading `_record_attention_read` uses for `staleness_hit` and
    `feedback.yaml` uses for its flag: `stale: 1` is a truthy value, not the
    mark, and treating it as one would let any stray scalar reorder the queue.
    """
    stale = _card(tmp_path, "zz stale", stale=True)
    fresh = _card(tmp_path, "aa fresh")
    truthy = _hand_card(tmp_path, "mm truthy.md", stale=1)

    assert _factors(tmp_path, stale)["staleness"] is True
    assert _factors(tmp_path, fresh)["staleness"] is False
    assert _factors(tmp_path, truthy)["staleness"] is False
    assert _order(tmp_path)[0] == stale


def test_impact_reads_active_project_slices_and_ranks_on_it(tmp_path, monkeypatch) -> None:
    """Order-tolerance with the graph plan's ERP-C.6, and the call shape it must meet.

    `active_project_slices` does not exist yet, so `impact` is False for every
    card and a test run only against today's tree would prove nothing about the
    factor. Installing the symbol turns the `ImportError` arm into the success
    arm and pins what ERP-C.6 has to ship: called with the workspace, returning
    slice id -> member paths.
    """
    calls: list[Path] = []

    def _slices(workspace: Path) -> dict[str, set[str]]:
        calls.append(Path(workspace))
        return {"projects/live": {"notes/live.md"}}

    monkeypatch.setattr(propagation, "active_project_slices", _slices, raising=False)
    off = _card(tmp_path, "aa off-slice", target="notes/off.md")
    on = _card(tmp_path, "zz on-slice", target="notes/live.md")

    order = _order(tmp_path)

    assert order == [on, off]
    assert _factors(tmp_path, on)["impact"] is True
    assert _factors(tmp_path, off)["impact"] is False
    assert calls and calls[0] == tmp_path


def test_impact_stays_false_when_the_slice_walk_raises(tmp_path, monkeypatch) -> None:
    """Ranking is an ordering, never a gate: a failing slice walk demotes the
    factor to False instead of turning the listing into an error."""

    def _boom(workspace: Path) -> dict[str, set[str]]:
        raise RuntimeError("slice walk unavailable")

    monkeypatch.setattr(propagation, "active_project_slices", _boom, raising=False)
    rel = _card(tmp_path, "card", target="notes/live.md")

    assert _factors(tmp_path, rel)["impact"] is False


def test_every_card_payload_discloses_its_factors_including_the_detail_read(
    tmp_path: Path,
) -> None:
    """The list explains its order and the card opened from it explains its place,
    with the same five keys -- `read_attention_card` does not go through
    `_attention_cards`, so this is the one place the detail path is pinned."""
    rel = _card(tmp_path, "one", loudness="alert", age_days=3)

    detail = engine_api.read_attention_card(tmp_path, rel)["attention"]

    assert detail["rank_factors"] == {
        "loudness": "alert",
        "priority": "",
        "impact": False,
        "staleness": False,
        "age_days": 3,
    }
    assert _factors(tmp_path, rel) == detail["rank_factors"]


def test_table_view_discloses_loudness_raised_by_and_created(tmp_path: Path) -> None:
    _card(tmp_path, "one", loudness="alert", age_days=2, raised_by="enrich-source")

    block = engine_api.read_attention(tmp_path)["view"]["blocks"][0]

    assert block["columns"] == [
        "title",
        "kind",
        "loudness",
        "raised_by",
        "created",
        "status",
        "target",
    ]
    # Columns and cells cannot drift apart: a column with no cell renders empty
    # and a cell with no column never renders at all.
    assert list(block["rows"][0]["cells"]) == block["columns"]
    assert block["rows"][0]["cells"]["raised_by"] == "enrich-source"
    assert block["rows"][0]["cells"]["loudness"] == "alert"
    assert block["rows"][0]["cells"]["created"] == _aged(2)


def test_config_order_by_reorders_the_factors_and_the_block_pin_survives(tmp_path: Path) -> None:
    _write_config(tmp_path, "order_by: [age, loudness]\n")
    old_quiet = _card(tmp_path, "aa old quiet", loudness="quiet", age_days=200)
    new_block = _card(tmp_path, "zz new block", loudness="block")
    new_alert = _card(tmp_path, "mm new alert", loudness="alert")

    assert _order(tmp_path) == [new_block, old_quiet, new_alert]


def test_a_dropped_factor_stops_ranking(tmp_path: Path) -> None:
    """`order_by` drops as well as reorders. With `priority` absent from the list,
    a `priority: high` card must lose to a louder one -- the same arrangement that
    orders the other way under the default."""
    _write_config(tmp_path, "order_by: [loudness]\n")
    prioritized = _card(tmp_path, "aa prioritized quiet", loudness="quiet", priority="high")
    louder = _card(tmp_path, "zz alert", loudness="alert")

    assert _order(tmp_path) == [louder, prioritized]
    assert _order(tmp_path, order_by="priority,loudness") == [prioritized, louder]


def test_age_still_breaks_ties_when_it_is_dropped_from_the_order(tmp_path: Path) -> None:
    """Dropping `age` demotes it to last; it never stops breaking ties.

    Two cards in the same band with `order_by: [loudness]` are equal on every
    configured factor, so without the closing age term their order would fall
    back to whatever the directory scan happened to yield -- alphabetical, which
    is the accidental sort this contract replaced.
    """
    _write_config(tmp_path, "order_by: [loudness]\n")
    new = _card(tmp_path, "aa new alert", loudness="alert")
    old = _card(tmp_path, "zz old alert", loudness="alert", age_days=60)

    assert _order(tmp_path) == [old, new]


def test_order_by_argument_overrides_the_configured_order(tmp_path: Path) -> None:
    _write_config(tmp_path, "order_by: [loudness]\n")
    new_alert = _card(tmp_path, "aa new alert", loudness="alert")
    old_quiet = _card(tmp_path, "zz old quiet", loudness="quiet", age_days=90)

    assert _order(tmp_path) == [new_alert, old_quiet]
    assert _order(tmp_path, order_by="age") == [old_quiet, new_alert]


def test_cli_order_by_flag_reaches_the_engine(tmp_path, capsys) -> None:
    """Through argparse and the real handler, with nothing monkeypatched: a flag
    that never reached `read_attention` would leave the default order standing."""
    new_alert = _card(tmp_path, "aa new alert", loudness="alert")
    old_quiet = _card(tmp_path, "zz old quiet", loudness="quiet", age_days=90)

    assert main(["attention", "list", "--workspace", str(tmp_path), "--json"]) == 0
    default = [card["path"] for card in json.loads(capsys.readouterr().out)["attention"]]
    assert (
        main(["attention", "list", "--workspace", str(tmp_path), "--order-by", "age", "--json"])
        == 0
    )
    by_age = [card["path"] for card in json.loads(capsys.readouterr().out)["attention"]]

    assert default == [new_alert, old_quiet]
    assert by_age == [old_quiet, new_alert]


def test_attention_order_by_falls_back_on_every_unusable_config(tmp_path: Path) -> None:
    """Seven separate ways the file can be wrong, one answer. A config typo must
    not be able to take the queue down, and `[]` is not an order."""
    assert attention_order_by(tmp_path) == DEFAULT_ORDER_BY  # no file at all

    _write_config(tmp_path, "order_by: {broken\n")  # unparsable YAML
    assert attention_order_by(tmp_path) == DEFAULT_ORDER_BY

    _write_config(tmp_path, "- not a mapping\n- at all\n")  # top level is a list
    assert attention_order_by(tmp_path) == DEFAULT_ORDER_BY
    assert producer_mode(tmp_path, "sweep") == "active"

    _write_config(tmp_path, "order_by: age\n")  # a scalar where a list belongs
    assert attention_order_by(tmp_path) == DEFAULT_ORDER_BY

    _write_config(tmp_path, "order_by: 7\n")  # not even iterable
    assert attention_order_by(tmp_path) == DEFAULT_ORDER_BY

    _write_config(tmp_path, "order_by: [invented, 7]\n")  # nothing known survives
    assert attention_order_by(tmp_path) == DEFAULT_ORDER_BY

    _write_config(tmp_path, "order_by: [age, invented]\n")  # partial: keep what is known
    assert attention_order_by(tmp_path) == ("age",)


def test_normalize_order_by_is_the_one_rule_for_both_fronts() -> None:
    """The flag and the file cannot disagree about what a factor name means."""
    assert normalize_order_by(["age", "loudness"]) == ("age", "loudness")
    assert normalize_order_by(["block"]) == DEFAULT_ORDER_BY  # the pin is not a factor
    assert normalize_order_by("age") == DEFAULT_ORDER_BY  # a bare string is not a list
    assert normalize_order_by({"age": 1}) == DEFAULT_ORDER_BY  # nor is a mapping
    assert normalize_order_by(7) == DEFAULT_ORDER_BY
    assert normalize_order_by([]) == DEFAULT_ORDER_BY


def test_producer_mode_reads_the_map_and_fails_safe_to_active(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        "producers:\n  sweep: paused\n  enrich-source: quiet\n  typo-producer: loud\n",
    )

    assert producer_mode(tmp_path, "sweep") == "paused"
    assert producer_mode(tmp_path, "enrich-source") == "quiet"
    assert producer_mode(tmp_path, "typo-producer") == "active"  # unknown mode
    assert producer_mode(tmp_path, "unlisted") == "active"  # absent producer
    assert producer_mode(tmp_path / "nowhere", "sweep") == "active"  # no config at all


def test_attention_yaml_has_exactly_one_source_of_truth() -> None:
    """`attention.yaml` ships as a code default, never as a seeded file (I1 A.1 ruling).

    A seeded `order_by: [priority, loudness, impact, staleness, age]` is a second
    copy of `DEFAULT_ORDER_BY` that is *authoritative* wherever it exists: change
    the constant and every vault seeded before the change keeps the old ranking,
    silently. `attention_config` has no writer at all, so unlike the decision-rule
    registry there is nothing a per-vault file has to store.
    """
    import memoria_vault
    from memoria_vault.runtime.attention_config import ATTENTION_CONFIG

    seeded = Path(memoria_vault.__file__).parent / "product/workspace_seed" / ATTENTION_CONFIG

    assert not seeded.exists(), (
        f"{seeded} now exists alongside attention_config.DEFAULT_ORDER_BY, so the "
        "ranking order has two sources that can drift. Keep one: either delete the "
        "constant and load the seeded file, or drop the seed file."
    )
