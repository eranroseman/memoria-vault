"""Cockpit assembly + rendering + keep-test contract (U2 plan section C)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from memoria_vault.engine import api as engine_api
from memoria_vault.engine import cockpit
from memoria_vault.engine.surface_contract import actions_by_id
from memoria_vault.runtime import state
from memoria_vault.runtime.subsystems.lib import inbox
from tests.helpers import init_cli_workspace, write_checked_concept

PROJECT_REL = "projects/study-alpha/project.md"


@pytest.fixture
def vault(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    """U2 §7 acceptance fixture, minus the machine output (section T seeds the
    journal side): one active project, three checked notes, an outline whose
    fourth id resolves nowhere, a draft with one complete and one thin
    (zero-grounds) evidence marker, three open worklist cards and one card the
    worklist excludes.

    The worklist cards and the excluded flag are written by the *production*
    Inbox writers (`runtime.subsystems.lib.inbox`), not by hand-rolled
    frontmatter, so the worklist panel is proven against the projection shape
    the product actually emits.

    Deliberately non-degenerate, so panel assertions can bite:

    - **Two edge types, encountered out of sorted order.** `claim-one` supports
      `claim-three` and contradicts `claim-two`; `read_project_slice` returns
      edges ordered by `(source, target, type)`, so the panel's `Counter` sees
      `supports` first and only `sorted()` puts `contradicts` ahead of it.
    - **Three resolving outline members, one unresolved id.** `members` is 3, so
      a hard-coded `outline_members: 2` cannot pass; `missing` stays 1, so the
      open-gap branch stays live.
    - **The thin marker sorts first.** `evidence_sets` comes back ordered by
      `block_ref, id`, so `ev-11111111` (`evidence-incomplete`) precedes
      `ev-22222222` (`complete`) and only `sorted()` puts `complete` first.
    - **Three worklist cards whose path order matches no other key.** Path order
      is candidate/gap/work-prompt; title order is work-prompt/candidate/gap —
      neither the same nor the reverse.
    """
    workspace = init_cli_workspace(tmp_path, capsys)
    write_checked_concept(
        workspace,
        PROJECT_REL,
        "type: project\ntitle: Study Alpha\nthesis: Sleep loss impairs recall\n",
        "project",
    )
    write_checked_concept(
        workspace,
        "notes/claim-one.md",
        "type: note\ntitle: Claim one\nid: note-claim-one\n"
        "links:\n  supports:\n    - notes/claim-three.md\n"
        "  contradicts:\n    - notes/claim-two.md\n",
        "note",
    )
    write_checked_concept(
        workspace,
        "notes/claim-two.md",
        "type: note\ntitle: Claim two\nid: note-claim-two\n",
        "note",
    )
    write_checked_concept(
        workspace,
        "notes/claim-three.md",
        "type: note\ntitle: Claim three\nid: note-claim-three\n",
        "note",
    )
    (workspace / "projects/study-alpha/outline.md").write_text(
        "- note-claim-one — grounds the thesis\n"
        "- note-claim-two — the counterexample claim one rebuts\n"
        "- note-claim-three — carries claim one's grounds\n"
        "- note-claim-four — not written yet\n",
        encoding="utf-8",
    )
    state.upsert_catalog_record(
        workspace,
        work_id="work-a",
        title="Work A",
        check_status="checked",
        content_path=".memoria/blobs/source-content/work-a.md",
    )
    source_text = workspace / ".memoria/blobs/source-content/work-a.md"
    source_text.parent.mkdir(parents=True, exist_ok=True)
    source_text.write_text("Grounding passage. ^p0001\n", encoding="utf-8")
    (workspace / "projects/study-alpha/draft.md").write_text(
        "# Draft\n\n"
        "Claim one holds. %%ev: ev-22222222 items=work-a#^p0001%%\n\n"
        "Claim two is thin. %%ev: ev-11111111 items=%%\n",
        encoding="utf-8",
    )
    state.rebuild_evidence_sets_from_markers(workspace)
    inbox.write_proposal(
        workspace,
        "candidate",
        "Follow up the sleep-deprivation review",
        action="Read the 2019 review and decide whether it enters the catalog.",
        argument_for="Both checked claims lean on it.",
        argument_against="A later meta-analysis may supersede it.",
        what_tipped_it="two checked notes cite it",
        certainty="unsure",
        raised_by="u2-fixture",
    )
    inbox.write_proposal(
        workspace,
        "gap",
        "Ground claim two",
        action="Attach a source span to claim two.",
        argument_for="The claim carries no grounds at all.",
        argument_against="The draft passage may be scaffolding.",
        what_tipped_it="items= is empty",
        certainty="likely",
        raised_by="u2-fixture",
    )
    inbox.write_work_prompt(
        workspace,
        "Extend the outline",
        action="Write the third outline member.",
        what_happened="The outline names an id with no checked note.",
        raised_by="u2-fixture",
        target="projects/study-alpha/outline.md",
    )
    inbox.write_finding(
        workspace,
        "flag",
        "Draft cites an unresolved span",
        finding="A span reference did not resolve.",
        raised_by="u2-fixture",
        target="projects/study-alpha/draft.md",
    )
    return workspace


def test_active_project_resolver_uses_type_and_archived_predicate(vault: Path) -> None:
    """Spec §1: active = type: project with frontmatter archived not True.
    lifecycle is schema-retired (vaultio.py RETIRED_FRONTMATTER_FIELDS) and
    must never be consulted."""
    assert cockpit.resolve_active_project(vault) == {
        "resolution": "active",
        "project": PROJECT_REL,
    }

    write_checked_concept(
        vault,
        "projects/study-beta/project.md",
        "type: project\ntitle: Study Beta\narchived: true\nlifecycle: active\n",
        "project",
    )
    assert cockpit.resolve_active_project(vault) == {
        "resolution": "active",
        "project": PROJECT_REL,
    }

    write_checked_concept(
        vault,
        "projects/study-gamma/project.md",
        "type: project\ntitle: Study Gamma\nlifecycle: archived\n",
        "project",
    )
    # The predicate is the literal `True`, not truthiness. `archived` is declared
    # `bool` (`schemas/types/project.yaml`), so a string is malformed — and a
    # malformed value must fail *visible*: the project keeps showing up and the
    # researcher can see the typo, rather than silently vanishing from the
    # cockpit because a non-empty string happens to be truthy.
    write_checked_concept(
        vault,
        "projects/study-delta/project.md",
        'type: project\ntitle: Study Delta\narchived: "no"\n',
        "project",
    )
    ambiguous = cockpit.resolve_active_project(vault)
    assert ambiguous["resolution"] == "ambiguous"
    assert [row["path"] for row in ambiguous["projects"]] == [
        PROJECT_REL,
        "projects/study-delta/project.md",
        "projects/study-gamma/project.md",
    ]
    assert [row["title"] for row in ambiguous["projects"]] == [
        "Study Alpha",
        "Study Delta",
        "Study Gamma",
    ]
    # Panel 1 reports the same predicate rather than a constant: an archived
    # project reads True, and the malformed one reads False.
    beta = cockpit.assemble_deep(vault, "projects/study-beta/project.md")["project"]
    assert beta["archived"] is True
    assert cockpit.assemble_deep(vault, "projects/study-delta/project.md")["project"] == {
        "source_action": "concepts.get",
        "path": "projects/study-delta/project.md",
        "title": "Study Delta",
        "thesis": "",
        "archived": False,
    }


def test_draft_panel_is_honest_about_a_project_with_no_composed_draft(vault: Path) -> None:
    """`draft_present` reports what `project.draft.read` actually found. A project
    that has never been composed has no `draft.md`, so the read returns empty
    content and no outline members — a hard-coded `True` would claim a draft the
    researcher does not have."""
    write_checked_concept(
        vault,
        "projects/study-delta/project.md",
        "type: project\ntitle: Study Delta\n",
        "project",
    )

    panels = cockpit.assemble_deep(vault, "projects/study-delta/project.md")

    assert panels["draft"]["draft_present"] is False
    assert panels["draft"]["draft_path"] == "projects/study-delta/draft.md"
    assert panels["draft"]["outline_members"] == 0
    assert panels["draft"]["evidence_states"] == {}
    assert panels["slice"]["members"] == 0
    assert panels["grounds"]["total"] == 0
    assert panels["grounds"]["findings"] == []


def test_resolver_sees_projects_from_the_production_create_concept_writer(vault: Path) -> None:
    """Second producer of the same state: `memoria new-project` lands a project
    through create-concept (unchecked, no `archived` key, `_` in the slug), not
    through the test helper. The active predicate must see that one too."""
    made = engine_api.write_new_concept(
        vault,
        "project",
        "Study Delta",
        body="Delta body.",
        tags=[],
        extra={},
        actor="pi",
    )
    assert made["ok"] is True

    resolved = cockpit.resolve_active_project(vault)
    assert resolved["resolution"] == "ambiguous"
    assert [row["path"] for row in resolved["projects"]] == [PROJECT_REL, made["path"]]


def test_resolver_with_zero_active_projects_is_ambiguous(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)

    assert cockpit.resolve_active_project(workspace) == {
        "resolution": "ambiguous",
        "projects": [],
    }


def test_assemble_deep_panels_wrap_named_registry_actions(vault: Path) -> None:
    panels = cockpit.assemble_deep(vault, PROJECT_REL)

    assert list(panels) == ["project", "slice", "draft", "grounds", "trace", "context"]

    project = panels["project"]
    assert project["source_action"] == "concepts.get"
    assert project["path"] == PROJECT_REL
    assert project["title"] == "Study Alpha"
    assert project["thesis"] == "Sleep loss impairs recall"
    assert project["archived"] is False

    slice_panel = panels["slice"]
    assert slice_panel["source_action"] == "project.slice.read"
    assert slice_panel["outline_path"] == "projects/study-alpha/outline.md"
    assert slice_panel["members"] == 3
    assert slice_panel["edges_by_type"] == {"contradicts": 1, "supports": 1}
    # The breakdown is sorted, not encounter-ordered: the slice hands the panel
    # the `supports` edge first (edges come back keyed on source/target/type), so
    # dropping `sorted()` would leave `supports` in front.
    assert list(slice_panel["edges_by_type"]) == ["contradicts", "supports"]
    assert slice_panel["missing"] == 1

    draft = panels["draft"]
    assert draft["source_action"] == "project.draft.read"
    assert draft["draft_path"] == "projects/study-alpha/draft.md"
    assert draft["outline_members"] == 3
    assert draft["draft_present"] is True
    assert draft["evidence_states"] == {"complete": 1, "evidence-incomplete": 1}
    # Same: `evidence_sets` arrives ordered by block_ref, which puts the
    # `evidence-incomplete` record first.
    assert list(draft["evidence_states"]) == ["complete", "evidence-incomplete"]
    assert draft["review_required"] == 1
    # spec §1 panel 3 / §6: verification status is transient and persisted
    # nowhere readable, so the panel must not invent a line for it.
    assert all("verification" not in key for key in draft)


def test_grounds_panel_flags_thin_claims_and_unresolved_outline_ids(vault: Path) -> None:
    grounds = cockpit.assemble_deep(vault, PROJECT_REL)["grounds"]

    assert grounds["source_action"] == "project.draft.read"
    assert grounds["complete"] == 1
    assert grounds["total"] == 2
    # Spec §4: every finding says what tipped it — the honesty-card field is not
    # optional, and each one points at the datum the reader can go check.
    assert grounds["findings"] == [
        {
            "finding": (
                "open gap: outline id note-claim-four resolves to no checked note (line 4)"
            ),
            "what_tipped_it": "projects/study-alpha/outline.md line 4",
        },
        {
            "finding": "thin claim: ev-11111111 has 0 grounds items",
            "what_tipped_it": "items=",
        },
    ]


def test_read_scope_bounds_every_cockpit_read(vault: Path) -> None:
    """Scoped-trace amendment (2026-07-29) §1: every optional-scope cockpit
    surface takes *and propagates* `read_scope`. A hop that drops it silently
    *widens* a bounded read — the caller asked for a slice of the vault and got
    the whole thing — and nothing else in this file would notice.

    One case per hop, each distinguished by which read refuses first:
    `read_concepts` (the active predicate), `read_slice`, `read_draft`,
    `read_concept` (panel 1) and `read_attention` (the worklist).
    """
    outline = "projects/study-alpha/outline.md"
    draft = "projects/study-alpha/draft.md"

    # active predicate → read_concepts: scoped away from projects/, no project
    # is visible, so the resolver cannot resolve one.
    assert cockpit.resolve_active_project(vault)["resolution"] == "active"
    assert cockpit.resolve_active_project(vault, read_scope=["notes"]) == {
        "resolution": "ambiguous",
        "projects": [],
    }

    # assemble_deep reads in the order slice → draft → concept, and each read
    # names itself when the scope excludes its file. Widening any one hop lets
    # the next read raise instead, which is a different message.
    with pytest.raises(FileNotFoundError, match="project slice not found"):
        cockpit.assemble_deep(vault, PROJECT_REL, read_scope=["notes"])
    with pytest.raises(FileNotFoundError, match="project draft not found"):
        cockpit.assemble_deep(vault, PROJECT_REL, read_scope=[outline])
    with pytest.raises(FileNotFoundError, match="target not found"):
        cockpit.assemble_deep(vault, PROJECT_REL, read_scope=[outline, draft])
    assert cockpit.assemble_deep(vault, PROJECT_REL, read_scope=[outline, draft, PROJECT_REL])

    # triage worklist → read_attention: the cards live under inbox/.
    assert len(cockpit.assemble_triage(vault)["worklist"]["cards"]) == 3
    assert cockpit.assemble_triage(vault, read_scope=["notes"])["worklist"]["cards"] == []


def test_trace_panel_builder_is_reached_with_the_contract_limit_and_scope(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Binding contract 2 + scoped-trace amendment §1 pin the call C.1 makes into
    section T: `trace_panel(vault, project_path, limit=8, read_scope=...)`.

    Resolving the builder through the module globals is the both-branch seam, so
    a permanently-unresolved builder (or a widened limit, or a dropped scope) is
    otherwise invisible: the panel just stays pending and every test stays green.
    """
    # Once T.1 lands the real builder, the deep screen must actually reach it.
    if hasattr(cockpit, "trace_panel"):
        live = cockpit.assemble_deep(vault, PROJECT_REL)["trace"]
        assert "pending" not in live
        assert {"events", "total", "shown"} <= set(live)

    calls: list[tuple[Path, str, dict[str, Any]]] = []

    def recording_trace_panel(vault_arg: Path, project_arg: str, **kwargs: Any) -> dict[str, Any]:
        calls.append((vault_arg, project_arg, kwargs))
        return {"source_action": "journal.list", "events": [], "total": 0, "shown": 0}

    monkeypatch.setattr(cockpit, "trace_panel", recording_trace_panel, raising=False)
    scope = ["projects", "notes", "inbox"]

    trace = cockpit.assemble_deep(vault, PROJECT_REL, read_scope=scope)["trace"]

    assert calls == [(Path(vault), PROJECT_REL, {"limit": 8, "read_scope": scope})]
    assert "pending" not in trace
    assert trace["total"] == 0


def test_context_panel_hands_read_scope_to_the_bound_engine(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Panel 6's live branch, which only exists once T.3 binds an engine to the
    reserved `context.read` row (scoped-trace amendment §1/§4). Simulating the
    bound row is the only way to hold the branch to its contract before then: the
    transport is called with the cockpit's `read_scope`, never unscoped."""
    seen: list[list[str] | None] = []

    def recording_context(
        workspace: Path, *, read_scope: list[str] | None = None
    ) -> dict[str, Any]:
        seen.append(read_scope)
        return {"ok": True, "api_version": 1, "context": {"project": str(workspace.name)}}

    monkeypatch.setattr(engine_api, "read_context_probe", recording_context, raising=False)
    monkeypatch.setattr(
        cockpit,
        "actions_by_id",
        lambda: {
            **actions_by_id(),
            "context.read": {
                "id": "context.read",
                "engine": "read_context_probe",
                "cli": {"commands": ["memoria context"]},
            },
        },
    )
    scope = ["projects", "notes", "inbox"]

    context = cockpit.assemble_deep(vault, PROJECT_REL, read_scope=scope)["context"]

    assert seen == [scope]
    assert context == {
        "source_action": "context.read",
        "bundle": {"context": {"project": vault.name}},
        "invocation": "memoria context",
    }


def test_trace_and_context_panels_are_both_branch_honest(vault: Path) -> None:
    panels = cockpit.assemble_deep(vault, PROJECT_REL)

    trace = panels["trace"]
    assert trace["source_action"] == "journal.list"
    # Section T lands engine.cockpit.trace_panel in this module; before that
    # the panel is a named pending line. Both branches are legal here.
    if hasattr(cockpit, "trace_panel"):
        assert {"events", "total", "shown"} <= set(trace)
    else:
        assert trace["pending"] == "engine.cockpit.trace_panel (U2 plan section T)"
        assert "events" not in trace

    context = panels["context"]
    assert context["source_action"] == "context.read"
    row = actions_by_id().get("context.read")
    if row is None or not row.get("engine"):
        assert "reserved" in context  # honest placeholder naming the row
        assert "bundle" not in context
    else:
        assert "bundle" in context
        assert "invocation" in context


def test_assemble_triage_worklist_preserves_payload_order(vault: Path) -> None:
    panels = cockpit.assemble_triage(vault)

    assert list(panels) == ["worklist", "review", "flow"]
    worklist = panels["worklist"]
    assert worklist["source_action"] == "attention.list"
    expected = engine_api.read_attention(vault, worklist=True)["attention"]
    assert len(expected) == 3
    assert len(engine_api.read_attention(vault)["attention"]) == 4
    # Verbatim pass-through: order is I1's to own, and a card field the cockpit
    # has never heard of (I1's rank_factors) must survive the panel untouched.
    assert worklist["cards"] == expected


def test_worklist_panel_emits_the_producer_order_whatever_it_is(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """I1 owns worklist ordering (spec §1 triage 1); the cockpit re-sorts nothing.

    Today's producer happens to emit inbox cards in path order (`_attention_cards`
    sorts the glob), so a cockpit-side `sorted(cards, key=path)` would be a no-op
    against the real payload and no assertion above could see it. Hold the
    guarantee against a producer order that matches no obvious key — not path,
    not title, not the reverse of either — which is what I1's ranked order will
    look like.
    """
    natural = engine_api.read_attention(vault, worklist=True)["attention"]
    ranked = natural[1:] + natural[:1]
    by_path = sorted(ranked, key=lambda card: card["path"])
    assert len(ranked) == 3
    assert ranked != by_path
    assert ranked != sorted(ranked, key=lambda card: card["title"])
    assert ranked != list(reversed(by_path))

    real_read_attention = engine_api.read_attention

    def ranked_read_attention(workspace: Path, **kwargs: Any) -> dict[str, Any]:
        payload = dict(real_read_attention(workspace, **kwargs))
        cards = payload["attention"]
        payload["attention"] = cards[1:] + cards[:1]
        return payload

    monkeypatch.setattr(engine_api, "read_attention", ranked_read_attention)

    assert cockpit.assemble_triage(vault)["worklist"]["cards"] == ranked


def test_named_pending_triage_panels_name_their_absent_producer(vault: Path) -> None:
    """Reconciliation amendment (2026-07-29) §2/§3: a panel with no registered
    producer carries an empty source_action and names what is missing — it never
    whitelists a future action id nor reaches past the registry."""
    panels = cockpit.assemble_triage(vault)

    assert panels["review"]["source_action"] == ""
    assert panels["review"]["pending"] == (
        "engine_api.evidence_review_queue + the views.evidence_review registry row "
        "(V2 plan V2R-B.4)"
    )
    assert panels["flow"]["source_action"] == ""
    assert panels["flow"]["pending"] == "the dashboard.read registry row (U2 plan T.3)"


def test_every_panel_source_action_is_registered_or_named_pending(vault: Path) -> None:
    """The architecture constraint, asserted through the real seam: a builder may
    only name a currently registered registry row, and an empty source_action is
    legal only for a named-pending panel."""
    registered = set(actions_by_id())
    panels = {**cockpit.assemble_deep(vault, PROJECT_REL), **cockpit.assemble_triage(vault)}

    for name, panel in panels.items():
        source_action = panel["source_action"]
        if source_action:
            assert source_action in registered, f"{name} names an unregistered action"
        else:
            assert panel["pending"], f"{name} has neither a source action nor a pending line"
