"""Contract tests for the /v1/views/attention engine view payload (U3-ENG.1/.2/.3).

The producer here is read by two clients that must agree: the HTTP transport
(U3-ENG.4) serializes the payload verbatim, and `packages/memoria-obsidian/
viewspec.js` renders it. Assertions therefore pin the wire keys exactly, and one
test parses the plugin's own catalog so a kind the renderer cannot draw fails
here rather than in the pane.
"""

from __future__ import annotations

import datetime
import json
import re
from pathlib import Path

import pytest

from memoria_vault import __version__
from memoria_vault.engine import api
from memoria_vault.runtime.subsystems.lib import inbox
from memoria_vault.runtime.subsystems.lib.edges import LINK_RELATIONS
from tests.cli_test_helpers import write_runner_provider_config
from tests.helpers import init_cli_workspace

VIEWSPEC_JS = (
    Path(__file__).resolve().parent.parent / "packages" / "memoria-obsidian" / "viewspec.js"
)
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

    catalog = {m["frontmatter"]["operation_id"] for m in iter_capability_manifests("operation")}
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

    payload = api.read_attention_view(workspace)
    cards = {card["ref"]: card for card in payload["view"]["blocks"]}

    assert (cards[aged]["age_s"], cards[aged]["age_label"]) == (259_200, "3d")
    # A same-day card and an undated one share `age_s == 0`; only the label
    # tells the computed zero from the fallback.
    assert (cards[today]["age_s"], cards[today]["age_label"]) == (0, "0d")
    assert (cards[undated]["age_s"], cards[undated]["age_label"]) == (0, "")
    assert (cards[unparseable]["age_s"], cards[unparseable]["age_label"]) == (0, "")
    assert "raised_at" not in cards[undated]
    assert cards[unparseable]["raised_at"] == "last Tuesday"


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
    assert payload["open"] == 4
    assert payload["by_loudness"] == {"block": 1, "alert": 1, "notice": 2}
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


def test_attention_view_block_kinds_are_all_known_to_the_plugin_renderer(
    workspace: Path,
) -> None:
    """Contract 3: the pane renders whatever the engine emits.

    `viewspec.js` dispatches on `kind` and falls through to a labeled unknown
    box, so an engine-only kind would ship a payload the pane cannot draw. The
    plugin's own catalog and rank map are parsed here rather than retyped.
    """
    inbox.write_proposal(
        workspace, "candidate", "Capture", "act", "for", "against", "tip", "likely", "sweep"
    )
    inbox.write_finding(workspace, "flag", "Broken", "finding", "sweep", target="notes/alpha.md")
    source = VIEWSPEC_JS.read_text(encoding="utf-8")
    catalog = json.loads(
        re.search(r"KNOWN_BLOCK_KINDS = (\[[^\]]*\])", source).group(1).replace("'", '"')
    )
    plugin_rank = json.loads(
        re.sub(
            r"(\w+):",
            r'"\1":',
            re.search(r"LOUDNESS_RANK = (\{[^}]*\})", source).group(1),
        )
    )

    payload = api.read_attention_view(workspace)
    emitted = set()
    for card in payload["view"]["blocks"]:
        emitted.add(card["kind"])
        emitted.update(child["kind"] for child in card["blocks"])

    assert emitted == {"card", "evidence-list", "text", "action-row"}
    assert emitted <= set(catalog)
    # Both halves sort by band; a divergence would order the pane differently
    # from the payload it was handed.
    assert plugin_rank == api.ATTENTION_LOUDNESS_RANK
