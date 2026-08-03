"""Contract tests for the /v1/views/attention engine view payload and route.

The producer here is read by two clients that must agree: the HTTP transport
(U3-ENG.4) serializes the payload verbatim, and `packages/memoria-obsidian/
viewspec.js` renders it. Assertions therefore pin the wire keys exactly, and one
test parses the plugin's own catalog so a kind the renderer cannot draw fails
here rather than in the pane.

Three layers are exercised, deliberately not folded into each other: the
producer (`api.read_attention_view`), the route gate plus dispatch
(`http_transport._dispatch`, U3-ENG.4/.5), and a real socket-served
`make_http_server` (U3-ENG.6) where the bearer check actually runs.
"""

from __future__ import annotations

import datetime
import json
import re
import subprocess
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from http import HTTPStatus
from pathlib import Path

import pytest

from memoria_vault import __version__
from memoria_vault.engine import api
from memoria_vault.runtime import state
from memoria_vault.runtime.http_transport import _dispatch, make_http_server
from memoria_vault.runtime.subsystems.lib import inbox
from memoria_vault.runtime.subsystems.lib.edges import LINK_RELATIONS, concept_edge_path_records
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.cli_test_helpers import write_runner_provider_config
from tests.helpers import ROOT, init_cli_workspace, write_checked_note

pytestmark = pytest.mark.contract

PLUGIN = ROOT / "packages" / "memoria-obsidian"
VIEWSPEC_JS = PLUGIN / "viewspec.js"
RELATE_JS = PLUGIN / "relate.js"
CREDENTIAL_ENV_NAMES = (
    "KILOCODE_API_KEY",
    "OPENALEX_API_KEY",
    "SEMANTIC_SCHOLAR_API_KEY",
    "PUBMED_API_KEY",
    "GITHUB_TOKEN",
    "NCBI_EMAIL",
)


@pytest.fixture
def workspace(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    return init_cli_workspace(tmp_path, capsys)


def _write_view_card(
    workspace: Path,
    name: str,
    *,
    loudness: str,
    created: str,
    kind: str = "gap",
    status: str = "open",
    extra: tuple[str, ...] = (),
) -> str:
    """Hand-write an attention projection.

    Real writers (`inbox.write_proposal`/`write_finding`) always stamp today and
    validate the loudness band, so states the queue genuinely holds — an aged
    card, a hand-edited band, a resolved card — have no other producer. Hand
    edits are first-class here: U3-SUB.1 adopts them at the policy gate.
    """
    path = workspace / "inbox" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "projection: attention",
        f"title: {name}",
        f"attention_kind: {kind}",
        f"attention_status: {status}",
        "routing_class: ask",
    ]
    if loudness:
        lines.append(f"loudness: {loudness}")
    if created:
        lines.append(f"created: {created}")
    lines += [*extra, "---", f"Review {name}.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return f"inbox/{name}.md"


def _days_ago(days: int) -> str:
    return (datetime.date.today() - datetime.timedelta(days=days)).isoformat()


def _refs(payload: dict) -> list[str]:
    return [card["ref"] for card in payload["view"]["blocks"]]


def test_attention_view_returns_the_nested_view_envelope(workspace: Path) -> None:
    _write_view_card(workspace, "one", loudness="alert", created=_days_ago(1))
    _write_view_card(workspace, "two", loudness="notice", created=_days_ago(2))

    payload = api.read_attention_view(workspace)

    assert payload["ok"] is True
    assert payload["api_version"] == api.READ_API_VERSION
    assert payload["view"]["version"] == api.VIEW_SPEC_VERSION
    assert payload["view"]["kind"] == "attention"
    assert "spec" not in payload
    assert "blocks" not in payload
    assert set(payload) == {"ok", "api_version", "view"}
    assert set(payload["view"]) == {"version", "kind", "blocks"}
    assert [card["kind"] for card in payload["view"]["blocks"]] == ["card", "card"]


def test_attention_view_card_keys_are_exactly_the_public_grammar(workspace: Path) -> None:
    """Present-only honesty fields, and none of the writer-only names."""
    written = inbox.write_proposal(
        workspace,
        "candidate",
        "Capture Smith 2024",
        "Capture it into the catalog",
        "Cited twice in the hub",
        "Might be out of scope",
        "hub cross-reference",
        "likely",
        "capture-sweep",
    )
    proposal_ref = written.relative_to(workspace).as_posix()
    finding = inbox.write_finding(
        workspace,
        "flag",
        "Broken citation",
        "Citekey resolves nowhere",
        "integrity-sweep",
        target="notes/alpha.md",
    )
    assert finding is not None
    finding_ref = finding.relative_to(workspace).as_posix()

    payload = api.read_attention_view(workspace)
    cards = {card["ref"]: card for card in payload["view"]["blocks"]}

    assert set(cards) == {proposal_ref, finding_ref}
    assert set(cards[proposal_ref]) == {
        "id",
        "kind",
        "ref",
        "title",
        "kind_line",
        "loudness",
        "age_s",
        "age_label",
        "blocks",
        "argument_for",
        "argument_against",
        "tipped_by",
        "certainty",
        "raised_by",
        "raised_at",
    }
    proposal = cards[proposal_ref]
    assert proposal["ref"] == "inbox/candidate-capture-smith-2024.md"
    assert proposal["id"] == "inbox_candidate-capture-smith-2024.md"
    assert proposal["kind"] == "card"
    assert proposal["title"] == "Capture Smith 2024"
    assert proposal["kind_line"] == "candidate"
    assert proposal["loudness"] == "notice"
    assert proposal["argument_for"] == "Cited twice in the hub"
    assert proposal["argument_against"] == "Might be out of scope"
    assert proposal["tipped_by"] == "hub cross-reference"
    assert proposal["certainty"] == "likely"
    assert proposal["raised_by"] == "capture-sweep"
    assert proposal["raised_at"] == datetime.date.today().isoformat()

    # A finding carries none of the proposal-only honesty fields, so the
    # present-only branch is the difference between the two key sets.
    finding_card = cards[finding_ref]
    assert set(finding_card) == {
        "id",
        "kind",
        "ref",
        "title",
        "kind_line",
        "loudness",
        "age_s",
        "age_label",
        "blocks",
        "raised_by",
        "raised_at",
    }
    assert finding_card["kind_line"] == "flag"
    assert finding_card["loudness"] == "alert"
    assert finding_card["raised_by"] == "integrity-sweep"


def test_attention_view_drops_blank_and_nonstring_honesty_values(workspace: Path) -> None:
    """A hand-edited card can leave an honesty field blank or non-textual."""
    ref = _write_view_card(
        workspace,
        "hand-edited",
        loudness="alert",
        created=_days_ago(1),
        extra=(
            'argument_for: "   "',
            "argument_against: Real counterweight",
            "what_tipped_it: 42",
            "certainty: []",
            "raised_by: ''",
        ),
    )

    payload = api.read_attention_view(workspace)
    card = next(card for card in payload["view"]["blocks"] if card["ref"] == ref)

    assert card["argument_against"] == "Real counterweight"
    assert "argument_for" not in card
    assert "what_tipped_it" not in card
    assert "tipped_by" not in card
    assert "certainty" not in card
    assert "raised_by" not in card


def test_attention_view_coerces_hand_edited_scalars_to_strings(workspace: Path) -> None:
    """YAML types a hand edit can introduce must not reach the JSON wire."""
    path = workspace / "inbox" / "numeric.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "projection: attention",
                "title: 2024",
                "attention_kind: 7",
                "attention_status: open",
                "loudness: 3",
                "target: 2024",
                f"created: {_days_ago(1)}",
                "---",
                "Body.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    payload = api.read_attention_view(workspace)
    card = payload["view"]["blocks"][0]

    assert card["title"] == "2024"
    assert card["kind_line"] == "7"
    assert card["loudness"] == "3"
    assert card["blocks"][0]["items"] == [{"label": "2024", "ref": "2024"}]


def test_attention_view_card_nests_evidence_body_and_actions_in_order(
    workspace: Path,
) -> None:
    targeted = inbox.write_finding(
        workspace,
        "flag",
        "Broken citation",
        "Citekey `smith2024` resolves **nowhere**",
        "integrity-sweep",
        target="notes/alpha.md",
    )
    assert targeted is not None
    targeted_ref = targeted.relative_to(workspace).as_posix()
    untargeted = inbox.write_finding(
        workspace,
        "alert",
        "Vault check failed",
        "Integrity sweep found drift",
        "integrity-sweep",
    )
    assert untargeted is not None
    untargeted_ref = untargeted.relative_to(workspace).as_posix()

    payload = api.read_attention_view(workspace)
    cards = {card["ref"]: card for card in payload["view"]["blocks"]}

    card = cards[targeted_ref]
    assert [child["kind"] for child in card["blocks"]] == [
        "evidence-list",
        "text",
        "action-row",
    ]
    assert card["id"] == "inbox_flag-broken-citation.md"
    assert [child["id"] for child in card["blocks"]] == [
        "inbox_flag-broken-citation.md-evidence",
        "inbox_flag-broken-citation.md-body",
        "inbox_flag-broken-citation.md-actions",
    ]
    assert card["blocks"][0]["items"] == [{"label": "notes/alpha.md", "ref": "notes/alpha.md"}]
    # Verbatim body text, markup unrendered and frontmatter excluded: the
    # renderer materializes this as text, so any escaping owed is the pane's.
    assert card["blocks"][1] == {
        "id": "inbox_flag-broken-citation.md-body",
        "kind": "text",
        "text": "# Finding\n\nCitekey `smith2024` resolves **nowhere**\n",
    }
    # A card with no target still carries the evidence block, empty.
    assert cards[untargeted_ref]["blocks"][0] == {
        "id": "inbox_alert-vault-check-failed.md-evidence",
        "kind": "evidence-list",
        "items": [],
    }


def test_attention_view_nests_exact_supported_actions(workspace: Path) -> None:
    written = inbox.write_proposal(
        workspace,
        "candidate",
        "Capture Smith 2024",
        "Capture it into the catalog",
        "Cited twice in the hub",
        "Might be out of scope",
        "hub cross-reference",
        "likely",
        "capture-sweep",
    )
    ref = written.relative_to(workspace).as_posix()

    payload = api.read_attention_view(workspace)
    card = next(card for card in payload["view"]["blocks"] if card["ref"] == ref)

    assert [child["kind"] for child in card["blocks"]] == [
        "evidence-list",
        "text",
        "action-row",
    ]
    assert card["blocks"][2] == {
        "id": "inbox_candidate-capture-smith-2024.md-actions",
        "kind": "action-row",
        "actions": [
            {
                "label": "Resolve",
                "operation_id": "resolve-attention",
                "payload": {"target_id": ref},
                "primary": True,
            },
            {
                "label": "Acknowledge",
                "operation_id": "acknowledge-attention",
                "payload": {"target_id": ref},
            },
            {
                "label": "Defer",
                "operation_id": "resolve-attention",
                "payload": {"target_id": ref, "outcome": "defer"},
            },
        ],
    }


def test_attention_view_gives_every_kind_the_same_action_row(workspace: Path) -> None:
    """No Curate, and no kind-conditional row.

    `curate-note-candidate` needs a checked candidate note's `note_path` and an
    accepted/rejected status, neither of which a proposal card carries, so the
    proposal-only Curate button of the drafting history would enqueue an
    operation the worker must refuse.
    """
    inbox.write_proposal(
        workspace,
        "gap",
        "Missing counterevidence",
        "Find it",
        "for",
        "against",
        "tip",
        "unsure",
        "gap-sweep",
    )
    inbox.write_finding(
        workspace, "alert", "Vault check failed", "Integrity sweep found drift", "integrity-sweep"
    )

    payload = api.read_attention_view(workspace)
    cards = payload["view"]["blocks"]

    assert [card["kind_line"] for card in cards] == ["alert", "gap"]
    rows = [card["blocks"][2] for card in cards]
    assert [[action["operation_id"] for action in row["actions"]] for row in rows] == [
        ["resolve-attention", "acknowledge-attention", "resolve-attention"],
        ["resolve-attention", "acknowledge-attention", "resolve-attention"],
    ]
    assert "curate-note-candidate" not in json.dumps(payload)


def test_attention_view_actions_name_cataloged_operation_ids(workspace: Path) -> None:
    from memoria_vault.runtime.capabilities import iter_capability_manifests

    inbox.write_proposal(
        workspace, "candidate", "Capture", "act", "for", "against", "tip", "likely", "sweep"
    )

    payload = api.read_attention_view(workspace)

    catalog = {m["frontmatter"]["operation_id"] for m in iter_capability_manifests()}
    named = {
        action["operation_id"]
        for card in payload["view"]["blocks"]
        for action in card["blocks"][2]["actions"]
    }
    assert named == {"resolve-attention", "acknowledge-attention"}
    assert named <= catalog


def test_attention_view_ranks_every_band_the_writers_produce(workspace: Path) -> None:
    """Each of `inbox.LOUDNESS` reached through its real writer, same day.

    `notice` is the default band for a written proposal, so it is the commonest
    card in the queue rather than an edge case; omitting any band lets a rank
    swap pass.
    """
    inbox.write_proposal(
        workspace, "candidate", "Quiet one", "a", "f", "a", "t", "likely", "sweep", loudness="quiet"
    )
    inbox.write_proposal(
        workspace, "candidate", "Noticed one", "a", "f", "a", "t", "likely", "sweep"
    )
    inbox.write_finding(workspace, "alert", "Alerting one", "finding", "sweep", loudness="alert")
    inbox.write_finding(workspace, "alert", "Blocking one", "finding", "sweep", loudness="block")

    payload = api.read_attention_view(workspace)

    assert [card["loudness"] for card in payload["view"]["blocks"]] == [
        "block",
        "alert",
        "notice",
        "quiet",
    ]
    assert [card["title"] for card in payload["view"]["blocks"]] == [
        "Blocking one",
        "Alerting one",
        "Noticed one",
        "Quiet one",
    ]


def test_attention_view_sorts_rank_then_age_then_path_and_skips_closed(
    workspace: Path,
) -> None:
    _write_view_card(workspace, "new-notice", loudness="notice", created=_days_ago(1))
    _write_view_card(workspace, "old-notice", loudness="notice", created=_days_ago(9))
    _write_view_card(workspace, "undated-notice", loudness="notice", created="")
    _write_view_card(workspace, "b-tied", loudness="alert", created=_days_ago(4))
    _write_view_card(workspace, "a-tied", loudness="alert", created=_days_ago(4))
    _write_view_card(workspace, "blocker", loudness="block", created=_days_ago(1))
    _write_view_card(workspace, "quiet-recent", loudness="quiet", created=_days_ago(1))
    # Both unrecognized bands rank after `quiet` despite being far older, so
    # dropping `quiet` from the rank map moves the recent quiet card last.
    _write_view_card(workspace, "shouty", loudness="shout", created=_days_ago(30))
    _write_view_card(workspace, "unbanded", loudness="", created=_days_ago(20))
    _write_view_card(workspace, "closed", loudness="block", created=_days_ago(9), status="resolved")

    payload = api.read_attention_view(workspace)

    assert _refs(payload) == [
        "inbox/blocker.md",
        "inbox/a-tied.md",
        "inbox/b-tied.md",
        "inbox/old-notice.md",
        "inbox/new-notice.md",
        "inbox/undated-notice.md",
        "inbox/quiet-recent.md",
        "inbox/shouty.md",
        "inbox/unbanded.md",
    ]


def test_attention_view_ages_cards_from_created(workspace: Path) -> None:
    aged = _write_view_card(workspace, "aged", loudness="alert", created=_days_ago(3))
    today = _write_view_card(workspace, "today", loudness="alert", created=_days_ago(0))
    undated = _write_view_card(workspace, "undated", loudness="alert", created="")
    unparseable = _write_view_card(
        workspace, "unparseable", loudness="alert", created="last Tuesday"
    )
    # A hand-edited future date is the one input that makes age negative. The
    # producer keeps the signed value (the label must show `-3d`, not `0d`);
    # U3-PLUG.7 reconciled the divergence on the plugin side, where `sortCards`
    # now clamps a negative `age_s` to 0 so both orders agree.
    future = _write_view_card(workspace, "future", loudness="alert", created=_days_ago(-3))

    payload = api.read_attention_view(workspace)
    cards = {card["ref"]: card for card in payload["view"]["blocks"]}

    assert (cards[aged]["age_s"], cards[aged]["age_label"]) == (259_200, "3d")
    # A same-day card and an undated one share `age_s == 0`; only the label
    # tells the computed zero from the fallback.
    assert (cards[today]["age_s"], cards[today]["age_label"]) == (0, "0d")
    assert (cards[undated]["age_s"], cards[undated]["age_label"]) == (0, "")
    assert (cards[unparseable]["age_s"], cards[unparseable]["age_label"]) == (0, "")
    assert (cards[future]["age_s"], cards[future]["age_label"]) == (-259_200, "-3d")
    assert "raised_at" not in cards[undated]
    assert cards[unparseable]["raised_at"] == "last Tuesday"
    # The engine orders on the full `created` string, so the future card sorts
    # ahead of the undated sentinel. `sortCards` reproduces exactly this row
    # order -- see `test-viewspec.mjs`, "a future-dated card keeps the engine's
    # row order".
    assert _refs(payload) == [aged, today, future, undated, unparseable]


def test_attention_view_reads_unquoted_yaml_date_scalars(workspace: Path) -> None:
    """Hand-edited `created:` loads as a date/datetime, not the writers' string."""
    dated = _write_view_card(workspace, "dated", loudness="alert", created=_days_ago(2))
    stamped = _write_view_card(
        workspace, "stamped", loudness="alert", created=f"{_days_ago(5)} 09:30:00"
    )

    payload = api.read_attention_view(workspace)
    cards = {card["ref"]: card for card in payload["view"]["blocks"]}

    assert cards[dated]["raised_at"] == _days_ago(2)
    assert cards[dated]["age_label"] == "2d"
    assert cards[stamped]["raised_at"] == f"{_days_ago(5)}T09:30:00"
    assert cards[stamped]["age_label"] == "5d"
    assert _refs(payload) == [stamped, dated]


def test_attention_view_respects_read_scope(workspace: Path) -> None:
    inbox.write_finding(
        workspace, "flag", "In scope", "finding text", "sweep", target="notes/alpha.md"
    )
    inbox.write_finding(
        workspace, "flag", "Out of scope", "finding text", "sweep", target="notes/beta.md"
    )

    payload = api.read_attention_view(workspace, read_scope=["notes/alpha.md"])

    assert [card["title"] for card in payload["view"]["blocks"]] == ["In scope"]


def test_attention_view_summary_returns_cheap_counts(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_view_card(workspace, "blocker", loudness="block", created=_days_ago(9))
    _write_view_card(workspace, "alerting", loudness="alert", created=_days_ago(9))
    _write_view_card(workspace, "noticed", loudness="notice", created=_days_ago(9))
    _write_view_card(workspace, "noticed-too", loudness="notice", created=_days_ago(8))
    # A hand-edited card with no band at all: the poll still has to bucket it,
    # and the pill renders whatever key it is given.
    _write_view_card(workspace, "unbanded", loudness="", created=_days_ago(8))
    _write_view_card(workspace, "closed", loudness="alert", created=_days_ago(9), status="resolved")

    monkeypatch.setattr(
        api,
        "credential_report",
        lambda _workspace: [
            {"name": "MODEL_KEY", "class": "required-for-operation", "status": "unset"},
            {"name": "ANOTHER_KEY", "class": "required-for-operation", "status": "unset"},
            {"name": "SET_KEY", "class": "required-for-operation", "status": "set"},
            {"name": "OPTIONAL_KEY", "class": "enhancing", "status": "unset"},
            {"name": "", "class": "required-for-operation", "status": "unset"},
            # A row with no `name` key at all -- one step past the blank one, and
            # the difference between dropping it and nagging about "None".
            {"class": "required-for-operation", "status": "unset"},
        ],
    )
    monkeypatch.setattr(api, "now_iso", lambda: "2011-02-03T04:05:06Z")
    monkeypatch.setattr(api, "__version__", "9.9.9-probe")
    payload = api.read_attention_view(workspace, summary=True)

    assert set(payload) == {
        "ok",
        "api_version",
        "open",
        "by_loudness",
        "as_of",
        "engine_version",
        "link_relations",
        "missing_required_credentials",
    }
    assert payload["ok"] is True
    assert payload["api_version"] == api.READ_API_VERSION
    assert payload["open"] == 5
    assert payload["by_loudness"] == {"block": 1, "alert": 1, "notice": 2, "": 1}
    assert "view" not in payload
    assert payload["as_of"] == "2011-02-03T04:05:06Z"
    assert payload["engine_version"] == "9.9.9-probe"
    assert payload["link_relations"] == [
        "contradicts",
        "extends",
        "qualifier",
        "rebuttal",
        "supports",
        "warrant",
    ]
    assert payload["link_relations"] == sorted(LINK_RELATIONS)
    assert "tension" not in payload["link_relations"]
    # Sorted, so the pill's nag lists the same names in the same order every poll.
    assert payload["missing_required_credentials"] == ["ANOTHER_KEY", "MODEL_KEY"]


def test_attention_view_summary_derives_link_relations_from_the_edge_roster(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Asserting today's six proves nothing a literal six would not also satisfy.

    The roster is the one summary field a *different* plan owns: when the graph
    section activates a seventh relation, an engine that froze the six would keep
    the plugin's link picker offering six with every suite green.
    """
    monkeypatch.setattr(api, "LINK_RELATIONS", frozenset({"zeta", "alpha", "mu"}))

    payload = api.read_attention_view(workspace, summary=True)

    assert payload["link_relations"] == ["alpha", "mu", "zeta"]


def test_attention_view_summary_stamps_the_running_engine_and_clock(workspace: Path) -> None:
    """Unmocked: the poll payload dates itself, so a stale pill is visible."""
    before = datetime.datetime.now(datetime.UTC).replace(microsecond=0)

    payload = api.read_attention_view(workspace, summary=True)

    assert payload["engine_version"] == __version__
    assert payload["as_of"].endswith("Z")
    as_of = datetime.datetime.fromisoformat(payload["as_of"].replace("Z", "+00:00"))
    assert before <= as_of <= datetime.datetime.now(datetime.UTC)


def test_attention_view_summary_uses_the_real_credential_report(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The unmocked producer: a runner provider names a key nothing has set."""
    for name in CREDENTIAL_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    write_runner_provider_config(workspace)

    payload = api.read_attention_view(workspace, summary=True)

    # KILOCODE_API_KEY is the provider config's `key_env` (required-for-operation);
    # the static registry rows are enhancing/identity and stay out however unset.
    assert payload["missing_required_credentials"] == ["KILOCODE_API_KEY"]
    monkeypatch.setenv("KILOCODE_API_KEY", "set-now")
    assert api.read_attention_view(workspace, summary=True)["missing_required_credentials"] == []


def test_attention_view_summary_counts_only_open_cards_in_scope(workspace: Path) -> None:
    inbox.write_finding(
        workspace, "flag", "In scope", "finding text", "sweep", target="notes/alpha.md"
    )
    inbox.write_finding(
        workspace, "flag", "Out of scope", "finding text", "sweep", target="notes/beta.md"
    )

    payload = api.read_attention_view(workspace, summary=True, read_scope=["notes/alpha.md"])

    assert payload["open"] == 1
    assert payload["by_loudness"] == {"alert": 1}


def test_attention_loudness_rank_pins_every_written_band() -> None:
    # Pinned against literals first: a test that only iterates the constant
    # still passes after the constant shrinks.
    assert api.ATTENTION_LOUDNESS_RANK == {"block": 0, "alert": 1, "notice": 2, "quiet": 3}
    # ... and cross-checked against the writer's roster, which is the reason the
    # ranking has to be total: every band `inbox` can write must rank.
    assert set(api.ATTENTION_LOUDNESS_RANK) == set(inbox.LOUDNESS)


def test_attention_honesty_fields_pin_the_wire_names() -> None:
    assert api.ATTENTION_HONESTY_FIELDS == (
        ("argument_for", "argument_for"),
        ("argument_against", "argument_against"),
        ("what_tipped_it", "tipped_by"),
        ("certainty", "certainty"),
        ("raised_by", "raised_by"),
    )


def _js_code(source: str) -> str:
    """Strip `//` comments so a scan reads code, never prose about code.

    A read deleted but named in a passing comment is otherwise indistinguishable
    from a read still made: the floor below is satisfied by the comment and the
    subset never sees the removed field.
    """
    return re.sub(r"//.*", "", source)


def _js_function(source: str, name: str) -> str:
    """Return one top-level `viewspec.js` function's code, comments removed.

    Chunking on column-zero `function` is enough for that module's style and
    fails loudly if the name ever moves, which is the point: a silently empty
    match would make every subset assertion below vacuous.
    """
    for chunk in re.split(r"^function ", source, flags=re.MULTILINE):
        if chunk.startswith(f"{name}("):
            return _js_code(chunk)
    raise AssertionError(f"viewspec.js has no top-level function {name}")


def test_attention_view_payload_matches_what_the_plugin_renderer_reads(
    workspace: Path,
) -> None:
    """Contract 3, both halves: the kinds it dispatches and the fields it reads.

    It is also where `api.VIEW_BLOCK_KINDS` is held to the dispatch, so the
    engine-side catalog cannot drift from the switch that has to draw it.

    Comparing the two sides' declared catalogs is not enough -- a renderer that
    renames its read of `kind_line` draws every card with a blank kind line, no
    unknown-block box, nothing logged, and green suites on both sides. So this
    parses `renderBlock`'s `switch` (the mechanism, not the declaration) and the
    `block.<field>` reads of whatever function that switch actually reaches, and
    holds the payload to both. Every scan is over comment-stripped code and is
    reached by following the dispatch, never by naming a function: a scan that
    trusted names would happily validate a renderer no card is routed to.
    """
    inbox.write_proposal(
        workspace, "candidate", "Capture", "act", "for", "against", "tip", "likely", "sweep"
    )
    inbox.write_finding(workspace, "flag", "Broken", "finding", "sweep", target="notes/alpha.md")
    source = _js_code(VIEWSPEC_JS.read_text(encoding="utf-8"))
    catalog = json.loads(
        re.search(r"KNOWN_BLOCK_KINDS = (\[[^\]]*\])", source).group(1).replace("'", '"')
    )
    dispatch = _js_function(source, "renderBlock")
    dispatched = set(re.findall(r'case "([^"]+)":', dispatch))
    # Follow `case "card":` to its callee, then that callee to the helpers it
    # hands the whole block to, so the reads scanned are the reads on the path.
    card_renderer = re.search(r'case "card":\s*return (\w+)\(', dispatch)
    assert card_renderer is not None, 'viewspec.js no longer routes "card" to a renderer'
    card_source = _js_function(source, card_renderer.group(1))
    for helper in set(re.findall(r"\b(\w+)\(block\)", card_source)):
        card_source += _js_function(source, helper)
    card_reads = set(re.findall(r"\bblock\.(\w+)", card_source))
    plugin_rank = json.loads(
        re.sub(r"(\w+):", r'"\1":', re.search(r"LOUDNESS_RANK = (\{[^}]*\})", source).group(1))
    )
    fallback_band = re.search(r"LOUDNESS_RANK\.(\w+) \+ 1", _js_function(source, "sortCards"))

    payload = api.read_attention_view(workspace)
    emitted = set()
    for card in payload["view"]["blocks"]:
        emitted.add(card["kind"])
        emitted.update(child["kind"] for child in card["blocks"])
    # The proposal card is the one that carries every present-only field, so it
    # is the only card that can answer for the whole read set.
    proposal = next(card for card in payload["view"]["blocks"] if card["kind_line"] == "candidate")

    assert emitted == {"card", "evidence-list", "text", "action-row"}
    # Dispatchable, not merely cataloged: renaming a `case` label fails here.
    assert emitted <= dispatched
    # One equality, three declarations: the switch that draws the kinds, the
    # plugin's exported catalog, and the engine's. U3-ENG.5's `VIEW_BLOCK_KINDS`
    # joins here rather than sitting beside it -- a fourth kind added to any one
    # of the three, or renamed in any one of them, fails this line.
    assert dispatched == set(catalog) == set(api.VIEW_BLOCK_KINDS)
    # Every field the card renderer reads is a field this producer emits. The
    # floor keeps the subset from passing vacuously if the regex stops matching.
    assert {"kind_line", "title", "loudness", "ref", "blocks"} <= card_reads
    assert card_reads <= set(proposal), sorted(card_reads - set(proposal))
    # Both halves sort by band; a divergence would order the pane differently
    # from the payload it was handed.
    assert plugin_rank == api.ATTENTION_LOUDNESS_RANK
    # ... and both must rank an unrecognized band after every known one. The two
    # sides spell that fallback differently (`len(map)` here, `quiet + 1` there),
    # so a fifth band would silently tie unknown with it on the plugin side.
    assert fallback_band is not None, "viewspec.js no longer ranks unknown from LOUDNESS_RANK"
    assert plugin_rank[fallback_band.group(1)] + 1 == len(api.ATTENTION_LOUDNESS_RANK)


# --- U3-ENG.4: the registered route, at the route-gate/dispatch layer --------


def _seed_two_open_cards(workspace: Path) -> None:
    """Two open cards, exactly one of them targeted.

    The smallest fixture that separates the three ways this route's argument
    wiring can be wrong: dropping `read_scope` leaves both cards, passing an
    empty scope leaves neither, and only passing the real one leaves the
    targeted card alone. Two cards also mean a truncated block list is visible.
    """
    inbox.write_proposal(
        workspace, "candidate", "Capture", "act", "for", "against", "tip", "likely", "sweep"
    )
    inbox.write_finding(
        workspace, "flag", "Broken citation", "finding", "integrity-sweep", target="notes/alpha.md"
    )


def _titles(payload: dict) -> list[str]:
    return [card["title"] for card in payload["view"]["blocks"]]


def _request_count(workspace: Path) -> int:
    with state.connect(workspace) as conn:
        return int(conn.execute("SELECT COUNT(*) AS n FROM operation_requests").fetchone()["n"])


def test_http_dispatch_serves_attention_view(workspace: Path) -> None:
    _seed_two_open_cards(workspace)

    full, full_status = _dispatch(workspace, "GET", "/v1/views/attention", dict)
    summary, summary_status = _dispatch(workspace, "GET", "/v1/views/attention?summary=true", dict)
    scoped, scoped_status = _dispatch(
        workspace, "GET", "/v1/views/attention?read_scope=notes/alpha.md", dict
    )

    assert full_status == HTTPStatus.OK
    # Verbatim: the route serializes the producer's payload, never a reshaping
    # of it, so the card grammar pinned above is the grammar that reaches HTTP.
    assert full == api.read_attention_view(workspace)
    assert full["view"]["version"] == "view-spec.v1"
    assert [block["kind"] for block in full["view"]["blocks"]] == ["card", "card"]
    assert _titles(full) == ["Broken citation", "Capture"]
    assert [child["kind"] for child in full["view"]["blocks"][0]["blocks"]] == [
        "evidence-list",
        "text",
        "action-row",
    ]
    assert summary_status == HTTPStatus.OK
    assert "view" not in summary
    assert summary["open"] == 2
    assert summary["by_loudness"] == {"alert": 1, "notice": 1}
    # Narrowed, not emptied -- see `_seed_two_open_cards`.
    assert scoped_status == HTTPStatus.OK
    assert _titles(scoped) == ["Broken citation"]


def test_http_dispatch_reads_the_summary_flag_in_every_written_form(workspace: Path) -> None:
    """The flag's producer states: absent (the pane's own render request),
    an explicit `false` from a client that always sends the param, and the
    capitalized `True` a naive client serializes -- the last one is why the
    route lowercases before comparing. Scope reaches the summary mode too;
    the poll pill must never count cards the boot scope hides."""
    _seed_two_open_cards(workspace)

    absent, _ = _dispatch(workspace, "GET", "/v1/views/attention", dict)
    explicit_false, _ = _dispatch(workspace, "GET", "/v1/views/attention?summary=false", dict)
    capitalized, _ = _dispatch(workspace, "GET", "/v1/views/attention?summary=True", dict)
    scoped_summary, scoped_status = _dispatch(
        workspace, "GET", "/v1/views/attention?summary=true&read_scope=notes/alpha.md", dict
    )

    assert _titles(absent) == ["Broken citation", "Capture"]
    assert _titles(explicit_false) == ["Broken citation", "Capture"]
    assert "view" not in capitalized
    assert capitalized["open"] == 2
    assert scoped_status == HTTPStatus.OK
    assert scoped_summary["open"] == 1
    assert scoped_summary["by_loudness"] == {"alert": 1}


def test_http_dispatch_rejects_wrong_method_for_attention_view(workspace: Path) -> None:
    response, status = _dispatch(workspace, "POST", "/v1/views/attention", dict)

    assert status == HTTPStatus.METHOD_NOT_ALLOWED
    assert response == {"ok": False, "error": "method not allowed: POST /v1/views/attention"}


# --- U3-ENG.5: the block-kind catalog, and tolerance of additive blocks ------


def _descendants(blocks: list[dict]) -> list[dict]:
    found: list[dict] = []
    for block in blocks:
        found.append(block)
        children = block.get("blocks")
        if isinstance(children, list):
            found.extend(_descendants(children))
    return found


def test_attention_view_emits_only_cataloged_block_kinds(workspace: Path) -> None:
    """`VIEW_BLOCK_KINDS` is pinned twice, and never against itself.

    Here against a literal, so narrowing or renaming the catalog fails; and in
    `test_attention_view_payload_matches_what_the_plugin_renderer_reads`
    against `viewspec.js`'s `renderBlock` dispatch, so it cannot become a third
    declaration drifting from the switch that has to draw these kinds. The
    subset below is the third leg: it is the emitted kinds that must stay
    inside the catalog, so the exact difference is named rather than implied.
    """
    _seed_two_open_cards(workspace)

    payload = api.read_attention_view(workspace)
    emitted = {str(block["kind"]) for block in _descendants(payload["view"]["blocks"])}

    assert api.VIEW_BLOCK_KINDS == ("card", "text", "badge", "action-row", "evidence-list")
    assert emitted == {"card", "evidence-list", "text", "action-row"}
    assert emitted <= set(api.VIEW_BLOCK_KINDS)
    # `badge` is cataloged for other views (the loudness chip) and this producer
    # never emits it. Naming it is what makes a silently widened catalog fail.
    assert set(api.VIEW_BLOCK_KINDS) - emitted == {"badge"}


def test_http_dispatch_passes_additive_unknown_blocks_through(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A deliberate regression pin: the transport imposes no block whitelist.

    A later engine adds a block kind this route does not know; the transport
    must carry it, and its unknown fields, verbatim rather than filtering the
    payload down to today's catalog. The pane's half of the same claim -- an
    additive block joins the view visibly instead of vanishing or displacing
    its neighbours -- is pinned in
    `packages/memoria-obsidian/scripts/test-viewspec.mjs`, because that is the
    side that decides it.
    """
    _seed_two_open_cards(workspace)
    real = api.read_attention_view
    future_top_level = {"id": "future", "kind": "sparkline", "points": [1, 2, 3]}
    future_child = {"id": "future-child", "kind": "timeline", "at": {"nested": True}}

    def future_view(*args: object, **kwargs: object) -> dict[str, object]:
        payload = real(*args, **kwargs)
        view = dict(payload["view"])
        cards = [dict(card) for card in view["blocks"]]
        cards[0]["blocks"] = [*cards[0]["blocks"], future_child]
        return {**payload, "view": {**view, "blocks": [*cards, future_top_level]}}

    monkeypatch.setattr(
        "memoria_vault.runtime.http_transport.engine_api.read_attention_view",
        future_view,
    )

    response, status = _dispatch(workspace, "GET", "/v1/views/attention", dict)

    assert status == HTTPStatus.OK
    assert response["view"]["version"] == "view-spec.v1"
    # The known cards keep their place ahead of the future block, and the
    # future block arrives whole -- unknown keys and nesting included.
    assert [block["kind"] for block in response["view"]["blocks"]] == [
        "card",
        "card",
        "sparkline",
    ]
    assert response["view"]["blocks"][-1] == future_top_level
    assert response["view"]["blocks"][0]["blocks"][-1] == future_child
    assert [child["kind"] for child in response["view"]["blocks"][0]["blocks"]] == [
        "evidence-list",
        "text",
        "action-row",
        "timeline",
    ]


# --- U3-ENG.6: the same route through a real socket, where auth actually runs -


LIVE_TOKEN = "view-token"


def _serve(workspace: Path, read_scope: list[str] | None) -> Iterator[str]:
    server = make_http_server(
        workspace, host="127.0.0.1", port=0, token=LIVE_TOKEN, read_scope=read_scope
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture
def live_server(workspace: Path) -> Iterator[str]:
    """A real listener, not `_dispatch`: the bearer check lives in the request
    handler, so nothing below the socket can prove a route is authenticated."""
    yield from _serve(workspace, read_scope=None)


@pytest.fixture
def scoped_live_server(workspace: Path) -> Iterator[str]:
    """The same server booted with `--read-scope notes/alpha.md`."""
    yield from _serve(workspace, read_scope=["notes/alpha.md"])


def _http(url: str, *, token: str | None = None, method: str = "GET") -> tuple[int, dict]:
    request = urllib.request.Request(url, method=method)
    if token is not None:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def _http_post(url: str, body: dict, token: str) -> tuple[int, dict]:
    """POST with no `actor` argument, so this client cannot send one.

    The signature is the assertion: the door's PI authority (contract 5) has to
    come from the door, and a helper that could pass `actor` would let a green
    test coexist with a client that supplies it.

    The timeout is a worker's budget, not a reader's: this door runs the whole
    operation inline -- frontmatter write, vault commit, journal append -- before
    it answers, where `_http` above only reads. Measured at 1.5s per request on
    an idle machine and 10s under a saturated one, so the 10s a read is given
    would make this test fail for load rather than for behaviour.
    """
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


UNAUTHORIZED = {"ok": False, "error": "unauthorized: missing or invalid bearer token"}


def test_live_server_refuses_the_attention_view_without_a_valid_bearer_token(
    workspace: Path, live_server: str
) -> None:
    """Both modes, and every near miss. The seeded cards matter: a refusal that
    only holds for an empty queue would say nothing about a real vault."""
    _seed_two_open_cards(workspace)
    view = f"{live_server}/v1/views/attention"
    summary = f"{view}?summary=true"

    assert _http(view) == (HTTPStatus.UNAUTHORIZED, UNAUTHORIZED)
    assert _http(summary) == (HTTPStatus.UNAUTHORIZED, UNAUTHORIZED)
    assert _http(view, token="other") == (HTTPStatus.UNAUTHORIZED, UNAUTHORIZED)
    assert _http(view, token="") == (HTTPStatus.UNAUTHORIZED, UNAUTHORIZED)
    # A prefix and an extension of the real token: a door that compared with
    # `startswith` or `in` rather than the whole value would open for these.
    assert _http(view, token=LIVE_TOKEN[:-1]) == (HTTPStatus.UNAUTHORIZED, UNAUTHORIZED)
    assert _http(view, token=f"{LIVE_TOKEN}-extra") == (HTTPStatus.UNAUTHORIZED, UNAUTHORIZED)


def test_live_server_serves_the_view_and_the_summary_with_the_token(
    workspace: Path, live_server: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    _seed_two_open_cards(workspace)
    # A fresh vault's seeded runner provider names KILOCODE_API_KEY as
    # required-for-operation, so clearing the environment pins the nagging
    # state deterministically rather than depending on the developer's shell.
    for name in CREDENTIAL_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)

    view_code, view = _http(f"{live_server}/v1/views/attention", token=LIVE_TOKEN)
    summary_code, summary = _http(
        f"{live_server}/v1/views/attention?summary=true", token=LIVE_TOKEN
    )

    assert view_code == HTTPStatus.OK
    assert view["ok"] is True
    assert view["api_version"] == "engine-read-api.v1"
    assert view["view"]["version"] == "view-spec.v1"
    assert [block["kind"] for block in view["view"]["blocks"]] == ["card", "card"]
    assert _titles(view) == ["Broken citation", "Capture"]
    # The proposal is the card carrying every present-only field, so it is the
    # one that shows JSON serialization did not flatten the nesting away.
    card = view["view"]["blocks"][1]
    assert [child["kind"] for child in card["blocks"]] == [
        "evidence-list",
        "text",
        "action-row",
    ]
    assert card["argument_for"] == "for"
    assert card["blocks"][2]["actions"][0] == {
        "label": "Resolve",
        "operation_id": "resolve-attention",
        "payload": {"target_id": card["ref"]},
        "primary": True,
    }
    assert summary_code == HTTPStatus.OK
    assert "view" not in summary
    assert summary["open"] == 2
    assert summary["by_loudness"] == {"alert": 1, "notice": 1}
    assert summary["as_of"].endswith("Z")
    assert summary["engine_version"] == __version__
    assert summary["link_relations"] == sorted(LINK_RELATIONS)
    # Nonempty, and the same names the producer computed: the pill's nag has to
    # survive the wire, and an empty list would prove nothing about that.
    assert summary["missing_required_credentials"] == ["KILOCODE_API_KEY"]


def test_live_server_attention_view_grants_a_read_and_nothing_else(
    workspace: Path, live_server: str
) -> None:
    """SEAM.1 raised this door to PI authority, but the door is
    `POST /operation/run`. The same token on the view route buys a GET; posting
    to it is refused by the route gate and enqueues nothing on the way.
    """
    _seed_two_open_cards(workspace)
    before = _request_count(workspace)

    code, payload = _http(f"{live_server}/v1/views/attention", token=LIVE_TOKEN, method="POST")

    assert code == HTTPStatus.METHOD_NOT_ALLOWED
    assert payload == {"ok": False, "error": "method not allowed: POST /v1/views/attention"}
    assert _request_count(workspace) == before


def test_live_server_attention_view_cannot_widen_the_startup_read_scope(
    workspace: Path, scoped_live_server: str
) -> None:
    """A boot read-scope is the PI's own narrowing of the pane. A valid token
    does not lift it, and neither does asking for a wider scope in the query --
    which is the one request a compromised pane would actually make."""
    _seed_two_open_cards(workspace)
    view = f"{scoped_live_server}/v1/views/attention"

    scoped_code, scoped = _http(view, token=LIVE_TOKEN)
    widened_code, widened = _http(f"{view}?read_scope=inbox", token=LIVE_TOKEN)
    summary_code, summary = _http(f"{view}?summary=true", token=LIVE_TOKEN)

    # The finding targets notes/alpha.md and survives; the proposal targets
    # nothing and is already outside the boot scope.
    assert scoped_code == HTTPStatus.OK
    assert _titles(scoped) == ["Broken citation"]
    # Asking for `inbox` does not add it -- it intersects to nothing.
    assert widened_code == HTTPStatus.OK
    assert _titles(widened) == []
    assert summary_code == HTTPStatus.OK
    assert summary["open"] == 1
    assert summary["by_loudness"] == {"alert": 1}


def test_live_server_runs_each_served_note_link_as_pi_and_rejects_tension(
    workspace: Path, live_server: str
) -> None:
    """The pane's own path, end to end: served roster in, PI-authored edge out.

    The loop is derived from the HTTP summary rather than from a second
    client-side roster, because the served list is exactly what the plugin's
    relation control renders; the one direct `LINK_RELATIONS` assertion is what
    pins the server as the graph's owner. `tension` is checked from both sides
    -- never served, and refused when submitted anyway.
    """
    write_checked_note(workspace, "notes/source.md", "Source")
    write_checked_note(workspace, "notes/target.md", "Target")
    summary_code, summary = _http(
        f"{live_server}/v1/views/attention?summary=true", token=LIVE_TOKEN
    )

    assert summary_code == HTTPStatus.OK
    assert summary["link_relations"] == sorted(LINK_RELATIONS)
    assert "tension" not in summary["link_relations"]
    for relation in summary["link_relations"]:
        body = {
            "operation_id": "curate-note-link",
            "payload": {
                "source_note_path": "notes/source.md",
                "link_type": relation,
                "target_path": "notes/target.md",
            },
            "idempotency_key": f"live-served-link-{relation}",
        }
        assert "actor" not in body
        code, response = _http_post(f"{live_server}/operation/run", body, LIVE_TOKEN)

        assert code == HTTPStatus.OK
        assert response["ok"] is True
        assert response["result"]["status"] == "done"
        request = state.request_row(workspace, response["job"]["job_id"])
        assert request is not None and request["actor"] == "pi"
        assert read_frontmatter(workspace / "notes/source.md")["links"][relation] == [
            "notes/target.md"
        ]

    tension_code, tension = _http_post(
        f"{live_server}/operation/run",
        {
            "operation_id": "curate-note-link",
            "payload": {
                "source_note_path": "notes/source.md",
                "link_type": "tension",
                "target_path": "notes/target.md",
            },
            "idempotency_key": "live-served-link-tension",
        },
        LIVE_TOKEN,
    )

    assert tension_code == HTTPStatus.OK
    assert tension["ok"] is False
    assert tension["result"]["status"] == "failed"


# The payload the relate modal submits, produced by the module the modal calls
# rather than retyped here. A hand-written Python copy would keep passing after
# the plugin renamed `warrant` to the legacy `reason` alias -- it would prove
# only that the engine accepts a key nothing sends. The one thing this file
# supplies is what the PI typed into the form.
_RELATE_BUILDER = """
const { buildRelateOperation } = require(process.argv[1]);
process.stdout.write(JSON.stringify(buildRelateOperation(JSON.parse(process.argv[2]))));
"""


def _plugin_relate_operation(**typed: object) -> dict:
    result = subprocess.run(
        ["node", "-e", _RELATE_BUILDER, str(RELATE_JS), json.dumps(typed)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    return dict(json.loads(result.stdout))


def test_live_server_carries_the_modal_warrant_text_to_the_edge_attribute(
    workspace: Path, live_server: str
) -> None:
    """The hop nothing proved: plugin payload -> HTTP door -> worker -> attribute.

    U3-PLUG.5 pinned `payload.warrant` at the builder and graph ERP-D.5 pinned
    `attributes_json.warrant` at the worker, but the live proof above posts only
    the three required keys, so the two halves met nowhere. This submits what
    the modal builds, over the socket, and reads the edge back.

    The two senses of "warrant" are separated by the fixture rather than
    asserted about: the `warrant` *relation* is sent with no text and the
    Warrant *text* is sent on a `supports` edge, so a builder that treated the
    relation as the text's owner (or the text as a relation-specific field)
    could not produce this pair.
    """
    write_checked_note(workspace, "notes/source.md", "Source")
    write_checked_note(workspace, "notes/target.md", "Target")
    typed = {
        "fromPath": "notes/source.md",
        "toPath": "notes/target.md",
        "roster": sorted(LINK_RELATIONS),
    }
    annotated = _plugin_relate_operation(**typed, relation="supports", warrant="  the RCT   ")
    licensed = _plugin_relate_operation(**typed, relation="warrant", warrant="")

    # What travels is the builder's, key for key: no `reason`, no `actor`, and
    # no empty `warrant` on the edge that carries none.
    assert annotated == {
        "operationId": "curate-note-link",
        "payload": {
            "source_note_path": "notes/source.md",
            "link_type": "supports",
            "target_path": "notes/target.md",
            "warrant": "the RCT",
        },
    }
    assert licensed["payload"] == {
        "source_note_path": "notes/source.md",
        "link_type": "warrant",
        "target_path": "notes/target.md",
    }

    responses = []
    for index, operation in enumerate((annotated, licensed)):
        body = {
            "operation_id": operation["operationId"],
            "payload": operation["payload"],
            "idempotency_key": f"live-relate-{index}",
        }
        assert "actor" not in body
        responses.append(_http_post(f"{live_server}/operation/run", body, LIVE_TOKEN))

    assert [code for code, _ in responses] == [HTTPStatus.OK, HTTPStatus.OK]
    assert [payload["result"]["status"] for _, payload in responses] == ["done", "done"]
    assert [
        state.request_row(workspace, payload["job"]["job_id"])["actor"] for _, payload in responses
    ] == ["pi", "pi"]
    # Both relations reached the frontmatter graph...
    assert read_frontmatter(workspace / "notes/source.md")["links"] == {
        "supports": ["notes/target.md"],
        "warrant": ["notes/target.md"],
    }
    # ... and exactly one edge row carries an attribute: the annotated one. The
    # `warrant` relation wrote no attribute, and the trimmed text arrived whole.
    assert concept_edge_path_records(workspace, checked_only=False) == [
        {
            "source_path": "notes/source.md",
            "target_path": "notes/target.md",
            "relation_type": "supports",
            "attributes": {"warrant": "the RCT"},
        }
    ]
