"""Cockpit assembly + rendering + keep-test contract (U2 plan section C)."""

from __future__ import annotations

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from memoria_vault.cli import main
from memoria_vault.engine import api as engine_api
from memoria_vault.engine import cockpit
from memoria_vault.engine import dashboard as dashboard_module
from memoria_vault.engine.dashboard import AGE_BUCKETS, DASHBOARD_PANELS
from memoria_vault.engine.surface_contract import actions_by_id
from memoria_vault.runtime import state
from memoria_vault.runtime.attention import inbox
from memoria_vault.runtime.knowledge import compose_project_draft as _compose_project_draft
from memoria_vault.runtime.knowledge import resolve_evidence_review as _resolve_evidence_review
from memoria_vault.runtime.operations import emit_explicit_disposition_event
from memoria_vault.runtime.telemetry import record_telemetry_event
from tests.helpers import (
    ROOT,
    call_with_context,
    git,
    init_cli_workspace,
    write_checked_concept,
)

pytestmark = pytest.mark.contract

PROJECT_REL = "projects/study-alpha/project.md"


@pytest.fixture
def vault(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    """U2 §7 acceptance fixture, minus the machine output (section T seeds the
    journal side): one active project, three checked notes, an outline whose
    fourth id resolves nowhere, a draft with one complete and one thin
    (zero-grounds) evidence marker, three open worklist cards and one card the
    worklist excludes.

    The worklist cards and the excluded flag are written by the *production*
    Inbox writers (`runtime.attention.inbox`), not by hand-rolled
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
    - **Three draft marks, two derived records.** The third mark is written
      *after* `rebuild_evidence_sets_from_markers`, so the draft is one mark
      ahead of the derived index — the ordinary state of a draft between
      rebuilds. `len(evidence_markers)` is 3 and `len(evidence_sets)` is 2, so
      counting the wrong one is visible (R2's honest denominator: panel 4's
      `total` is the marks the researcher wrote, not the rows the machine
      managed to derive).
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
    draft_path = workspace / "projects/study-alpha/draft.md"
    draft_path.write_text(
        "# Draft\n\n"
        "Claim one holds. %%ev: ev-22222222 items=work-a#^p0001%%\n\n"
        "Claim two is thin. %%ev: ev-11111111 items=%%\n",
        encoding="utf-8",
    )
    state.rebuild_evidence_sets_from_markers(workspace)
    # Written after the derivation run, so the draft carries three marks while
    # the derived index still holds two records.
    draft_path.write_text(
        draft_path.read_text(encoding="utf-8")
        + "\nClaim three is fresh. %%ev: ev-33333333 items=work-a#^p0001%%\n",
        encoding="utf-8",
    )
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
    # Nothing to review and nothing unresolved: the fixture's own counts are 1,
    # so only a project with none of either can tell a real count from a
    # hard-coded one.
    assert panels["draft"]["review_required"] == 0
    assert panels["slice"]["members"] == 0
    assert panels["slice"]["missing"] == 0
    assert panels["slice"]["edges_by_type"] == {}
    assert panels["grounds"]["total"] == 0
    assert panels["grounds"]["findings"] == []


def test_project_panel_reports_an_untitled_project_as_blank_not_as_a_stand_in(
    vault: Path,
) -> None:
    """Panel 1's `title` fallback, held against the producer state that reaches it.

    A `type: project` concept with no frontmatter `title` is not malformed —
    `read_concepts` anticipates exactly that row and substitutes `path.stem` for
    its listing (`engine/api.py`). The panel deliberately does *not* substitute:
    it reads the frontmatter the researcher wrote and reports blank when nothing
    is there, so the screen never shows a filename dressed as a title. Every
    other fixture titles its project, which leaves that fallback free to return
    any literal at all.
    """
    write_checked_concept(
        vault,
        "projects/study-epsilon/project.md",
        "type: project\n",
        "project",
    )

    panels = cockpit.assemble_deep(vault, "projects/study-epsilon/project.md")

    assert panels["project"]["title"] == ""
    out = cockpit.render_deep(
        {"screen": "deep", "project": "projects/study-epsilon/project.md", "panels": panels}
    )
    assert "  title: " in out
    assert "study-epsilon" not in _panel_body(out, "project (concepts.get)")[0]


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
        machine_authored=False,
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


def test_resolver_emits_the_producer_order_whatever_it_is(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The composer re-sorts nothing (module docstring, spec §1) — `concepts.list`
    owns listing order, here as much as in the worklist.

    Today's producer sorts concepts by path, so a cockpit-side
    `sorted(projects, key=path)` would be a no-op against the real payload and no
    assertion on the fixture could see it. Hold the guarantee against a producer
    order that matches no obvious key — not path, not title, not the reverse of
    either.
    """
    write_checked_concept(
        vault, "projects/study-beta/project.md", "type: project\ntitle: Zulu\n", "project"
    )
    write_checked_concept(
        vault, "projects/study-gamma/project.md", "type: project\ntitle: Gamma\n", "project"
    )
    natural = engine_api.read_concepts(vault, concept_type="project")["concepts"]
    rotated = natural[1:] + natural[:1]
    paths = [row["path"] for row in rotated]
    assert len(rotated) == 3
    assert paths != sorted(paths)
    assert paths != [row["path"] for row in sorted(rotated, key=lambda row: row["title"])]
    assert paths != sorted(paths, reverse=True)

    real_read_concepts = engine_api.read_concepts

    def rotated_read_concepts(workspace: Path, **kwargs: Any) -> dict[str, Any]:
        payload = dict(real_read_concepts(workspace, **kwargs))
        rows = payload["concepts"]
        payload["concepts"] = rows[1:] + rows[:1]
        return payload

    monkeypatch.setattr(engine_api, "read_concepts", rotated_read_concepts)

    assert [row["path"] for row in cockpit.active_projects(vault)] == paths
    assert [row["path"] for row in cockpit.resolve_active_project(vault)["projects"]] == paths


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
    # Panel 3 composes two reads and says so: `outline_members` comes from the
    # slice, everything else from the draft. The singular key keeps naming the
    # panel's primary read (the pinned `--json` surface); the list is the honest
    # full attribution.
    assert draft["source_actions"] == ["project.draft.read", "project.slice.read"]
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
    # The denominator is the draft's own grounds marks, not the derived records:
    # the fixture's draft carries three marks while `evidence_sets` still holds
    # two, so the two counts are distinguishable.
    assert grounds["total"] == 3
    assert len(engine_api.read_draft(vault, PROJECT_REL)["draft"]["evidence_sets"]) == 2
    # Spec §4: every finding says what tipped it — the honesty-card field is not
    # optional, and each one points at the datum the reader can go check.
    assert grounds["findings"] == [
        {
            "finding": (
                "open gap: outline id note-claim-four resolves to no checked note (line 4)"
            ),
            "what_tipped_it": "projects/study-alpha/outline.md line 4",
            "source_action": "project.slice.read",
        },
        {
            "finding": "thin claim: ev-11111111 has 0 grounds items",
            "what_tipped_it": "items=",
            "source_action": "project.draft.read",
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
    # trace_panel landed (U2 section T); the pending arm below it was dead and a
    # both-branch assert distinguishes nothing.
    assert {"events", "total", "shown"} <= set(trace)
    assert "pending" not in trace

    context = panels["context"]
    assert context["source_action"] == "context.read"
    row = actions_by_id().get("context.read")
    if row is None:
        assert context["reserved"] == "context.read is not in the surface-contract registry"
        assert "bundle" not in context
    elif not row.get("engine"):
        # The placeholder repeats the registry's own word for the row rather
        # than an empty string: `"reserved" in context` is true of `""` too, and
        # a blank line under the panel heading reads as "nothing to say here"
        # instead of "U1 declared this row and left the transport to U2".
        assert context["reserved"] == row["reserved"] == "U2"
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
    whitelists a future action id nor reaches past the registry.

    Both-branch, and the post-landing half is INT.1's endgame rule: once a seam is
    live the named-pending form must be *gone*, not merely joined by real counts.
    """
    panels = cockpit.assemble_triage(vault)

    assert "pending" not in panels["review"]
    assert panels["review"]["source_action"] == "views.evidence_review"
    assert "pending" not in panels["flow"]
    assert panels["flow"]["source_action"] == "dashboard.read"


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
        # The same rule for the two additive attribution keys C.2 introduced:
        # a panel-level list and a per-finding id are grounding claims too.
        for extra in panel.get("source_actions") or []:
            assert extra in registered, f"{name} lists an unregistered action"
        for finding in panel.get("findings") or []:
            assert finding["source_action"] in registered, (
                f"{name} finding names an unregistered action"
            )


def test_context_panel_names_the_engine_when_the_bound_row_has_no_cli_command(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Panel 6's invocation line is what the researcher pastes to re-run the read
    themselves (spec §1 panel 6). A row registered without a CLI transport — the
    registry allows it — still has to name something runnable, so the fallback
    names the engine entry point rather than going blank."""

    def probe_context(workspace: Path, *, read_scope: list[str] | None = None) -> dict[str, Any]:
        return {"ok": True, "api_version": 1, "context": {}}

    monkeypatch.setattr(engine_api, "read_context_probe", probe_context, raising=False)
    monkeypatch.setattr(
        cockpit,
        "actions_by_id",
        lambda: {
            **actions_by_id(),
            "context.read": {"id": "context.read", "engine": "read_context_probe"},
        },
    )

    context = cockpit.assemble_deep(vault, PROJECT_REL)["context"]

    assert context["invocation"] == "context.read via engine_api.read_context_probe"


def test_findings_renderer_speaks_honesty_card_grammar_only() -> None:
    """U2 spec §4: honesty-card fields verbatim; no verdict line, no
    pre-selected action; one-sided arguments drop (V2's card grammar)."""
    findings = [
        {
            "finding": "thin claim: ev-22222222 has 0 grounds items",
            "argument_for": "reads as a synthesis claim",
            "argument_against": "no grounds item was ever attached",
            "what_tipped_it": "items=",
            "certainty": "low",
            "verdict": "reject",
            "recommended_action": "quarantine now",
        },
        {"finding": "one-sided card", "argument_for": "only one side present"},
        {"action": "attach a source span to claim two"},
    ]

    lines = cockpit.render_findings(findings)
    text = "\n".join(lines)

    assert "thin claim: ev-22222222 has 0 grounds items" in text
    assert "for: reads as a synthesis claim" in text
    assert "against: no grounds item was ever attached" in text
    assert "tipped by: items=" in text
    assert "certainty: low" in text
    assert "one-sided card" in text
    # A card whose headline field is `action` (the shape V2 and the inbox
    # writers use) still gets rendered — the grammar bans a *pre-selected*
    # action, not an action the card names as its finding.
    assert "attach a source span to claim two" in text
    assert "verdict" not in text
    assert "reject" not in text
    assert "quarantine now" not in text
    assert "only one side present" not in text
    assert cockpit.render_findings([]) == []


def test_findings_renderer_emits_its_contract_fields_in_contract_order() -> None:
    """ "Per card, in order" is the renderer's contract (spec §4), and order is
    load-bearing: the headline first, then the two sides of the argument, then
    what tipped it, then how sure, then where it came from. A card whose
    attribution floats above its own headline reads as a heading for the card
    below it. `finding` outranks `action` for the headline, and a card carrying
    neither renders no bullet at all rather than an empty one.

    Two cards, because the renderer returns one flat list and the panels splice
    it straight into the screen: anything the loop emits *between* cards — a
    separator, a rule, a blank line — is invisible to a one-card fixture, and a
    blank line inside a panel body is what `_panel_body` reads as the end of the
    panel.
    """
    card = {
        "finding": "thin claim: ev-22222222 has 0 grounds items",
        "action": "quarantine the claim",
        "argument_for": "reads as a synthesis claim",
        "argument_against": "no grounds item was ever attached",
        "what_tipped_it": "items=",
        "certainty": "low",
        "source_action": "project.draft.read",
    }
    second = {"action": "attach a source span to claim two", "certainty": "likely"}

    assert cockpit.render_findings([card, second]) == [
        "  - thin claim: ev-22222222 has 0 grounds items",
        "    for: reads as a synthesis claim",
        "    against: no grounds item was ever attached",
        "    tipped by: items=",
        "    certainty: low",
        "    from: project.draft.read",
        "  - attach a source span to claim two",
        "    certainty: likely",
    ]
    assert cockpit.render_findings([{"what_tipped_it": "items="}]) == ["    tipped by: items="]


def test_findings_name_the_read_that_produced_them(vault: Path) -> None:
    """Grounding attribution is the product's whole trust claim, so a finding
    names the read that produced it rather than inheriting its panel's heading.
    Panel 4's headline numbers come from `project.draft.read`, but every open gap
    comes from `project.slice.read`'s `missing` — a reader following the panel
    heading to check one would land on a read that never produced it."""
    grounds = cockpit.assemble_deep(vault, PROJECT_REL)["grounds"]
    by_finding = {card["finding"]: card["source_action"] for card in grounds["findings"]}

    assert set(by_finding.values()) == {"project.slice.read", "project.draft.read"}
    assert (
        by_finding["open gap: outline id note-claim-four resolves to no checked note (line 4)"]
        == "project.slice.read"
    )
    assert by_finding["thin claim: ev-11111111 has 0 grounds items"] == "project.draft.read"

    text = "\n".join(cockpit.render_findings(grounds["findings"]))
    assert "from: project.slice.read" in text
    assert "from: project.draft.read" in text
    # A card with no attribution claims none — the renderer never invents one.
    assert cockpit.render_findings([{"finding": "unattributed"}]) == ["  - unattributed"]


def test_long_identifiers_render_whole_on_their_own_line() -> None:
    ident = "notes/" + "x" * 120 + ".md"

    lines = cockpit.render_findings([{"finding": f"thin claim: {ident} has 0 grounds items"}])

    assert any(line.strip() == ident for line in lines)
    for line in lines:
        assert len(line) <= 80 or line.strip() == ident


def test_the_layout_target_is_exactly_eighty_columns() -> None:
    """80 columns is the target the keep-test measures (spec §2), so the boundary
    is part of the contract: a line that fits in 80 stays whole, and the next
    character wraps it."""
    assert cockpit.LAYOUT_COLUMNS == 80
    exactly_eighty = " ".join(["x"] * 37 + ["xx"])
    assert len(f"  - {exactly_eighty}") == 80

    assert cockpit.render_findings([{"finding": exactly_eighty}]) == [f"  - {exactly_eighty}"]
    # 80 is also the width the wrapper *uses*, and the continuation lines hang
    # under the prefix. Pinning the constant alone leaves both free: `_fit` can
    # wrap at 76, or drop the hanging indent, while `LAYOUT_COLUMNS` still reads
    # 80. The split below is the one only a width of exactly 80 produces.
    assert cockpit.render_findings([{"finding": exactly_eighty + "x"}]) == [
        "  - " + " ".join(["x"] * 37),
        "    xxx",
    ]


def _panel_body(out: str, heading: str) -> list[str]:
    """The lines of one panel: everything between its heading and the blank
    separator that ends it.

    Panel-scoped assertions keep saying the same thing after T.1's trace events
    and T.3's context bundle land. A whole-screen `not in` would quietly start
    covering payloads C.2 does not own, so an unrelated key would fail a C.2
    test.
    """
    lines = out.splitlines()
    start = lines.index(heading) + 1
    end = next((i for i in range(start, len(lines)) if lines[i] == ""), len(lines))
    return lines[start:end]


def test_deep_screen_renders_panels_in_fixed_order(vault: Path) -> None:
    payload = {
        "screen": "deep",
        "project": PROJECT_REL,
        "panels": cockpit.assemble_deep(vault, PROJECT_REL),
    }

    out = cockpit.render_deep(payload)

    headings = [
        "project (concepts.get)",
        "slice (project.slice.read)",
        "draft (project.draft.read)",
        "grounds (project.draft.read)",
        "recent machine changes (journal.list)",
        "context handoff (context.read)",
    ]
    positions = [out.index(heading) for heading in headings]
    assert positions == sorted(positions)
    assert "title: Study Alpha" in out
    assert "thesis: Sleep loss impairs recall" in out
    assert "complete evidence sets: 1/3" in out
    assert "unresolved outline ids: 1" in out
    assert "edges: contradicts=1 supports=1" in out
    assert "evidence states: complete=1 evidence-incomplete=1" in out
    assert "review required: 1" in out
    assert "open gap: outline id note-claim-four" in out
    # spec §1 panel 3: no such line. Scoped to the panel that must not invent
    # it — as a whole-screen assertion this would also cover T.3's context
    # bundle and T.1's trace events, where an unrelated key containing
    # "verification" would fail a C.2 test for no C.2 reason.
    assert not any("verification" in line.lower() for line in _panel_body(out, headings[2]))
    assert out.endswith("\n")
    assert not out.endswith("\n\n")


def test_deep_screen_never_wraps_an_identifier_mid_token(vault: Path) -> None:
    """The keep-test rule (spec §2) has to hold for the screen, not only for the
    findings renderer: a panel line that interpolates a value without going
    through the wrapper emits an over-long line, and no other assertion notices.

    The fixture is the whole test. `_fit(prefix, value)` and
    `f"{prefix}{value}"` are byte-identical for every line that already fits, so
    a value that *cannot* exceed the layout cannot tell the wrapper from a bare
    f-string — which is how a `Study Long` title left every interpolated line
    below 80 and made this assertion unfailable.

    The vault supplies the over-long path, title and thesis. The other four
    interpolated values arrive as an explicit payload because today's *producers*
    hold them under the layout — `_note_edges` knows three edge types, the
    deriver two evidence states, and the two placeholder lines are constants —
    while the *renderer* bounds none of them. That gap is exactly what routing
    `edges:` and `evidence states:` through `_fit` was for, and it is not
    hypothetical: `_review_panel`'s own pending string is 91 characters today.
    """
    project_rel = f"projects/study-{'y' * 100}/project.md"
    draft_rel = f"projects/study-{'y' * 100}/draft.md"
    title = "Sleep restriction and the durable decay of recall over consecutive study nights"
    thesis = (
        "Restricting sleep degrades declarative consolidation in a dose dependent way "
        "that survives a night of recovery sleep"
    )
    assert len(f"  title: {title}") > cockpit.LAYOUT_COLUMNS
    assert len(f"  thesis: {thesis}") > cockpit.LAYOUT_COLUMNS
    write_checked_concept(
        vault, project_rel, f"type: project\ntitle: {title}\nthesis: {thesis}\n", "project"
    )
    panels = cockpit.assemble_deep(vault, project_rel)

    out = cockpit.render_deep({"screen": "deep", "project": project_rel, "panels": panels})
    lines = out.splitlines()

    assert any(line.strip() == project_rel for line in lines)
    assert any(line.strip() == draft_rel for line in lines)

    # The same rule over the four values only the payload can lengthen. The
    # vocabulary is deliberately wider than today's producers emit — the
    # renderer is what is under test, and it declares no bound on either
    # breakdown or on what a pending/reserved line may say.
    wide = cockpit.render_deep(
        {
            "screen": "deep",
            "project": project_rel,
            "panels": {
                **panels,
                "slice": {
                    **panels["slice"],
                    "edges_by_type": {
                        "contradicts": 12,
                        "extends": 34,
                        "qualifies": 5,
                        "rebuts": 6,
                        "refines": 7,
                        "supports": 89,
                        "undercuts": 10,
                    },
                },
                "draft": {
                    **panels["draft"],
                    "evidence_states": {
                        "complete": 12,
                        "evidence-incomplete": 34,
                        "quote-drifted": 5,
                        "source-withdrawn": 6,
                    },
                },
                "trace": {
                    "source_action": "journal.list",
                    "pending": (
                        "engine_api.evidence_review_queue + the views.evidence_review "
                        "registry row (V2 plan V2R-B.4)"
                    ),
                },
                # T.3 wired context.read, so panel 6's widest producer is a
                # long bundle value plus the pasteable invocation, not the
                # deleted reserved line.
                "context": {
                    "source_action": "context.read",
                    "bundle": {
                        "attention_open": 3,
                        "steering_unavailable": (
                            "steering tokens are a whole-vault read; a bounded "
                            "read_scope cannot include them"
                        ),
                    },
                    "invocation": "memoria context --workspace /a/deeply/nested/vault --json",
                },
            },
        }
    )

    for line in lines + wide.splitlines():
        # T.3 wired context.read, so panel 6's bundle now carries real paths
        # inside a json scalar — quoted, comma-separated. The pinned rule is
        # that an over-long line holds exactly one whole identifier and never
        # a mid-token break, so the json decoration is stripped before the
        # comparison rather than the rule being widened.
        assert len(line) <= cockpit.LAYOUT_COLUMNS or line.strip().strip('",') in {
            project_rel,
            draft_rel,
        }


def test_deep_screen_states_the_archived_and_draft_facts_its_panels_carry(vault: Path) -> None:
    """Two booleans the screen turns into English, plus the thesis line's guard.

    C.1 pins `archived` and `draft_present` in the *payload*; the render layer
    is the sentence the researcher actually reads, and an inverted mapping makes
    the screen state a falsehood — an archived project rendering `archived: no`.
    Held in both directions on two projects whose facts differ, so no constant
    passes.
    """
    live = cockpit.render_deep(
        {
            "screen": "deep",
            "project": PROJECT_REL,
            "panels": cockpit.assemble_deep(vault, PROJECT_REL),
        }
    )
    live_project = _panel_body(live, "project (concepts.get)")
    live_draft = _panel_body(live, "draft (project.draft.read)")

    assert "  archived: no" in live_project
    assert "  archived: yes" not in live_project
    assert "  thesis: Sleep loss impairs recall" in live_project
    assert "  draft present: yes" in live_draft
    assert "  draft present: no" not in live_draft

    write_checked_concept(
        vault,
        "projects/study-beta/project.md",
        "type: project\ntitle: Study Beta\narchived: true\n",
        "project",
    )
    panels = cockpit.assemble_deep(vault, "projects/study-beta/project.md")
    assert panels["project"]["archived"] is True
    assert panels["project"]["thesis"] == ""
    assert panels["draft"]["draft_present"] is False

    archived = cockpit.render_deep(
        {"screen": "deep", "project": "projects/study-beta/project.md", "panels": panels}
    )
    archived_project = _panel_body(archived, "project (concepts.get)")
    archived_draft = _panel_body(archived, "draft (project.draft.read)")

    assert "  archived: yes" in archived_project
    assert "  archived: no" not in archived_project
    assert "  draft present: no" in archived_draft
    assert "  draft present: yes" not in archived_draft
    # A project with no thesis prints no thesis line: an empty value under a
    # label reads as "the thesis is blank", which is a different claim from
    # "none was written yet". Same rule as panel 6's reserved line (E16).
    assert not any(line.lstrip().startswith("thesis:") for line in archived_project)


def test_deep_screen_prints_the_member_counts_both_panels_carry(vault: Path) -> None:
    """Panel 2's `members:` and panel 3's `outline members:` — the one datum the
    slice contributes to panel 3, and the whole point of deviation 2. Both lines
    were rendered and unasserted, so deleting either (or hard-coding it) kept the
    suite green. Two vaults whose counts differ, so a constant fails one."""
    panels = cockpit.assemble_deep(vault, PROJECT_REL)
    assert panels["slice"]["members"] == 3
    assert panels["draft"]["outline_members"] == 3

    out = cockpit.render_deep({"screen": "deep", "project": PROJECT_REL, "panels": panels})

    assert "  members: 3" in _panel_body(out, "slice (project.slice.read)")
    assert "  outline members: 3" in _panel_body(out, "draft (project.draft.read)")

    write_checked_concept(
        vault, "projects/study-delta/project.md", "type: project\ntitle: Study Delta\n", "project"
    )
    empty_panels = cockpit.assemble_deep(vault, "projects/study-delta/project.md")
    assert empty_panels["slice"]["members"] == 0
    assert empty_panels["draft"]["outline_members"] == 0

    empty = cockpit.render_deep(
        {"screen": "deep", "project": "projects/study-delta/project.md", "panels": empty_panels}
    )

    assert "  members: 0" in _panel_body(empty, "slice (project.slice.read)")
    assert "  outline members: 0" in _panel_body(empty, "draft (project.draft.read)")


def test_grounds_panel_says_it_found_nothing_rather_than_going_silent(vault: Path) -> None:
    """An honesty branch: "we checked and found nothing" is a claim the reader
    can act on; a panel that prints its numbers and stops is silence.

    The fallback runs on every clean project, so it was executed by other tests
    and asserted by none — dropping it, or swapping the sentence for one that
    says something else, both escaped.
    """
    write_checked_concept(
        vault, "projects/study-delta/project.md", "type: project\ntitle: Study Delta\n", "project"
    )
    panels = cockpit.assemble_deep(vault, "projects/study-delta/project.md")
    assert panels["grounds"]["findings"] == []

    clean = cockpit.render_deep(
        {"screen": "deep", "project": "projects/study-delta/project.md", "panels": panels}
    )

    assert _panel_body(clean, "grounds (project.draft.read)") == [
        "  complete evidence sets: 0/0",
        "  (no gaps or thin claims)",
    ]

    with_findings = _panel_body(
        cockpit.render_deep(
            {
                "screen": "deep",
                "project": PROJECT_REL,
                "panels": cockpit.assemble_deep(vault, PROJECT_REL),
            }
        ),
        "grounds (project.draft.read)",
    )

    # The sentence is a claim about this project, not panel furniture: a panel
    # that found gaps must not also say it found none.
    assert "  (no gaps or thin claims)" not in with_findings
    assert with_findings[0] == "  complete evidence sets: 1/3"
    assert with_findings[1].startswith("  - open gap: outline id note-claim-four")


def test_trace_lines_render_every_summary_field_and_survive_a_partial_builder(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`_trace_lines`' actual contract with T.1, which the handoff note claimed
    and no test held.

    Three things: the summary is `timestamp event_type output_id` in that order
    (no fixture event carried an `output_id`, so dropping the key from the tuple
    escaped); an event the journal gave no summary fields says so rather than
    rendering a bare `ref N:`; and the shown-of-total line needs *both* counts —
    a builder that carries one must still render, not raise.

    The first event's summary is deliberately longer than the layout. A `ref`
    line whose three fields all fit is byte-identical whether it goes through
    `_fit` or straight into an f-string, so a short-summary fixture cannot see
    the wrapper at all — and an `output_id` that names the file the run wrote is
    the ordinary case, not a contrived one.
    """
    monkeypatch.setattr(
        cockpit,
        "trace_panel",
        lambda *args, **kwargs: {
            "source_action": "journal.list",
            "events": [
                {
                    "event_id": 5,
                    "timestamp": "2026-07-30T09:00:00Z",
                    "event_type": "derived-output",
                    "output_id": "projects/study-alpha/draft.md#ev-22222222",
                },
                {"event_id": 9},
            ],
            "total": 4,
            "shown": 2,
        },
        raising=False,
    )

    body = _panel_body(
        cockpit.render_deep(
            {
                "screen": "deep",
                "project": PROJECT_REL,
                "panels": cockpit.assemble_deep(vault, PROJECT_REL),
            }
        ),
        "recent machine changes (journal.list)",
    )

    assert body == [
        "  ref 5: 2026-07-30T09:00:00Z derived-output",
        "         projects/study-alpha/draft.md#ev-22222222",
        "  ref 9: (no summary fields)",
        "  showing 2 of 4",
        "  refs preview via trace.revert_preview",
    ]

    monkeypatch.setattr(
        cockpit,
        "trace_panel",
        lambda *args, **kwargs: {"source_action": "journal.list", "events": [], "total": 4},
        raising=False,
    )

    partial = _panel_body(
        cockpit.render_deep(
            {
                "screen": "deep",
                "project": PROJECT_REL,
                "panels": cockpit.assemble_deep(vault, PROJECT_REL),
            }
        ),
        "recent machine changes (journal.list)",
    )

    # Half a count is not an honest "showing N of M", and reaching for the
    # missing half would crash the whole screen over one panel.
    assert partial == ["  (no machine changes recorded)"]


def test_both_screens_open_with_their_banner_and_one_blank_between_panels(vault: Path) -> None:
    """Screen furniture (spec §2): each screen names itself on line 1, the deep
    screen then names the project it opened, and panels are separated by exactly
    one blank line. Plain sequential text is the whole layout contract, so the
    separators are part of it."""
    panels = cockpit.assemble_deep(vault, PROJECT_REL)
    out = cockpit.render_deep({"screen": "deep", "project": PROJECT_REL, "panels": panels})
    lines = out.splitlines()

    assert lines[0] == "memoria cockpit: deep work"
    assert lines[1] == f"project: {PROJECT_REL}"
    assert lines[2] == ""
    for heading in (
        "project (concepts.get)",
        "slice (project.slice.read)",
        "draft (project.draft.read)",
        "grounds (project.draft.read)",
        "recent machine changes (journal.list)",
        "context handoff (context.read)",
    ):
        assert lines[lines.index(heading) - 1] == "", f"no separator above {heading}"
    assert "\n\n\n" not in out

    # `_buffer` terminates the screen, and collapsing the blank separators
    # `render_deep` appends between panels is the whole of its job. Editing the
    # last line is not: panel 6 ends on a string the composer took from the
    # registry and printed for the researcher to paste, and a command stub that
    # ends where its argument begins is a value, not stray whitespace. `memoria
    # cockpit | cat` is byte-identical by construction (module docstring), and
    # every screen above ends on a line that a wider strip would leave alone.
    stub = cockpit.render_deep(
        {
            "screen": "deep",
            "project": PROJECT_REL,
            "panels": {
                **panels,
                "context": {
                    "source_action": "context.read",
                    "bundle": {"project": PROJECT_REL},
                    "invocation": "memoria context --project ",
                },
            },
        }
    )

    assert stub.endswith("  invocation: memoria context --project \n")

    resolution = cockpit.render_deep(
        {"screen": "deep", "resolution": "ambiguous", "projects": []}
    ).splitlines()

    assert resolution[0] == "memoria cockpit: active-project resolution"
    assert resolution[1] == ""


def test_deep_screen_heading_says_when_a_panel_has_no_registry_row(vault: Path) -> None:
    """A heading is a grounding claim. C.3's triage panels and any pre-seam panel
    carry `source_action: ""`, and the heading must say so rather than print a
    bare label that reads as though the panel were backed by a registered read."""
    panels = cockpit.assemble_deep(vault, PROJECT_REL)
    panels["grounds"] = {**panels["grounds"], "source_action": ""}

    out = cockpit.render_deep({"screen": "deep", "project": PROJECT_REL, "panels": panels})

    assert "grounds (no registry row yet)" in out
    assert "grounds (project.draft.read)" not in out


def test_trace_panel_renders_refs_and_an_honest_shown_of_total(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Panel 5's live branch (section T lands the builder). The ref the line
    carries is the journal `event_id` §3's preview consumes, and the preview
    pointer is only honest when there is a ref to preview."""
    events = [
        {"event_id": 42, "timestamp": "2026-07-30T09:00:00Z", "event_type": "derived-output"},
        {"event_id": 7, "timestamp": "2026-07-29T09:00:00Z", "event_type": "derived-output"},
    ]
    monkeypatch.setattr(
        cockpit,
        "trace_panel",
        lambda *args, **kwargs: {
            "source_action": "journal.list",
            "events": events,
            "total": 9,
            "shown": 2,
        },
        raising=False,
    )
    payload = {
        "screen": "deep",
        "project": PROJECT_REL,
        "panels": cockpit.assemble_deep(vault, PROJECT_REL),
    }

    out = cockpit.render_deep(payload)

    assert "ref 42: 2026-07-30T09:00:00Z derived-output" in out
    assert "ref 7: 2026-07-29T09:00:00Z derived-output" in out
    assert out.index("ref 42") < out.index("ref 7")  # newest first, order preserved
    assert "showing 2 of 9" in out
    assert "refs preview via trace.revert_preview" in out

    monkeypatch.setattr(
        cockpit,
        "trace_panel",
        lambda *args, **kwargs: {
            "source_action": "journal.list",
            "events": [],
            "total": 0,
            "shown": 0,
        },
        raising=False,
    )
    payload["panels"] = cockpit.assemble_deep(vault, PROJECT_REL)

    empty = cockpit.render_deep(payload)

    assert "(no machine changes recorded)" in empty
    assert "showing 0 of 0" in empty
    # Nothing to preview, so the screen does not advertise a preview.
    assert "refs preview" not in empty


def test_trace_panel_pending_line_names_its_absent_producer(vault: Path) -> None:
    panels = cockpit.assemble_deep(vault, PROJECT_REL)
    out = cockpit.render_deep({"screen": "deep", "project": PROJECT_REL, "panels": panels})
    section = out[out.index("recent machine changes (journal.list)") :]

    if "pending" in panels["trace"]:
        assert f"pending: {panels['trace']['pending']}" in section
        assert "refs preview" not in section
    else:
        assert f"showing {panels['trace']['shown']} of {panels['trace']['total']}" in section


def test_context_handoff_block_renders_reserved_or_bundle_with_invocation(
    vault: Path,
) -> None:
    panels = cockpit.assemble_deep(vault, PROJECT_REL)
    out = cockpit.render_deep({"screen": "deep", "project": PROJECT_REL, "panels": panels})

    section = out[out.index("context handoff (context.read)") :]
    if "bundle" in panels["context"]:
        # live transport: fixed-order bundle lines, the pasteable
        # invocation line beneath them (spec §1 panel 6)
        assert "invocation: " in section
        assert section.rstrip().splitlines()[-1].lstrip().startswith("invocation: ")
    else:
        # names the reserved row honestly — the value, not a blank line
        assert panels["context"]["reserved"]
        assert f"reserved: {panels['context']['reserved']}" in section


def test_context_bundle_renders_in_fixed_key_order_with_the_invocation_last(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Panel 6's live branch, which only exists once section T binds an engine to
    the reserved row: "a short fixed-order block, one item per line, a one-line
    invocation of the underlying action beneath it for pasting" (spec §1 panel
    6). The bundle arrives as a mapping, so the block's order has to be the
    renderer's, not whatever insertion order the transport happened to use.

    Nothing in the block is short by construction: the transport owns the bundle
    values and the registry owns the command string, so one value runs past the
    layout, one carries a character outside ASCII, and the invocation is a real
    scoped command rather than a two-word stub. A block that fits in 80 columns
    and stays in ASCII cannot distinguish `_fit` from an f-string, nor
    `ensure_ascii=False` from the json default — the researcher pastes these
    lines, so both are the difference between a value and a mangling of it.
    """

    def probe_context(workspace: Path, *, read_scope: list[str] | None = None) -> dict[str, Any]:
        return {
            "ok": True,
            "api_version": 1,
            "project": "projects/study-alpha/project.md",
            "attention": {"open": 3, "kinds": ["candidate", "gap"], "tipped": "gap — one"},
            "open_question": (
                "does the 2019 review supersede the meta-analysis the draft leans on"
            ),
        }

    monkeypatch.setattr(engine_api, "read_context_probe", probe_context, raising=False)
    monkeypatch.setattr(
        cockpit,
        "actions_by_id",
        lambda: {
            **actions_by_id(),
            "context.read": {
                "id": "context.read",
                "engine": "read_context_probe",
                "cli": {
                    "commands": [
                        "memoria context --project projects/study-alpha/project.md "
                        "--scope notes,projects"
                    ]
                },
            },
        },
    )
    panels = cockpit.assemble_deep(vault, PROJECT_REL)

    out = cockpit.render_deep({"screen": "deep", "project": PROJECT_REL, "panels": panels})
    section = out[out.index("context handoff (context.read)") :].rstrip().splitlines()

    assert [line.strip() for line in section[1:]] == [
        # `attention` before `open_question` before `project` although the
        # transport emitted `project` first, and a non-scalar value rendered as
        # data — sorted keys, `—` intact — rather than as a Python repr.
        'attention: {"kinds": ["candidate", "gap"], "open": 3, "tipped": "gap — one"}',
        "open_question: does the 2019 review supersede the meta-analysis the draft",
        "leans on",
        "project: projects/study-alpha/project.md",
        "invocation: memoria context --project projects/study-alpha/project.md --scope",
        "notes,projects",
    ]


def test_ambiguous_resolution_screen_lists_active_projects(vault: Path) -> None:
    write_checked_concept(
        vault,
        "projects/study-gamma/project.md",
        "type: project\ntitle: Study Gamma\n",
        "project",
    )

    out = cockpit.render_deep({"screen": "deep", **cockpit.resolve_active_project(vault)})

    assert "2 active projects; pass --project <path>:" in out
    assert PROJECT_REL in out
    assert "projects/study-gamma/project.md" in out
    assert "Study Alpha" in out
    assert "Study Gamma" in out
    # list-and-exit: the resolution screen shows no panel content
    assert "thesis:" not in out

    # The screen prints the resolver's order, whatever it is. Every vault the
    # resolver can build lists projects in path order, so a renderer-side sort
    # would be a no-op against one — hold it against a listing that matches no
    # obvious key, which is what an I1-ranked listing will look like.
    rows = [
        {"path": "projects/study-beta/project.md", "title": "Zulu"},
        {"path": "projects/study-gamma/project.md", "title": "Alpha"},
        {"path": PROJECT_REL, "title": "Mid"},
    ]
    paths = [row["path"] for row in rows]
    assert paths != sorted(paths)
    assert paths != sorted(paths, reverse=True)
    assert paths != [row["path"] for row in sorted(rows, key=lambda row: row["title"])]

    listed = cockpit.render_deep({"screen": "deep", "resolution": "ambiguous", "projects": rows})

    assert [listed.index(path) for path in paths] == sorted(listed.index(p) for p in paths)
    assert "3 active projects; pass --project <path>:" in listed


def test_resolution_screen_never_truncates_a_project_path(vault: Path) -> None:
    """The keep-test rule (spec §2) on the one screen whose whole job is printing
    pasteable `--project <path>` values.

    §2 was asserted for the deep screen and the findings renderer but not here,
    where a truncated path is not a cosmetic wrap — it is a value the researcher
    copies and the CLI then cannot resolve. The path is longer than the layout,
    so it may only render whole on a line of its own.
    """
    long_path = f"projects/study-{'z' * 90}/project.md"
    assert len(long_path) > cockpit.LAYOUT_COLUMNS

    out = cockpit.render_deep(
        {
            "screen": "deep",
            "resolution": "ambiguous",
            "projects": [{"path": long_path, "title": "Study Long"}],
        }
    )
    lines = out.splitlines()

    assert any(line.strip() == long_path for line in lines)
    assert "(Study Long)" in out
    for line in lines:
        assert len(line) <= cockpit.LAYOUT_COLUMNS or line.strip() == long_path


def test_resolution_screen_with_no_active_projects_names_the_predicate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)

    out = cockpit.render_deep({"screen": "deep", **cockpit.resolve_active_project(workspace)})

    assert "no active projects (type: project, archived not True)" in out
    assert "pass --project <path> to open one directly" in out
    assert "active projects; pass" not in out


def _triage_panels(
    cards: list[dict[str, Any]],
    *,
    review: dict[str, Any] | None = None,
    flow: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """An explicit triage panel set for the renderer's own tests.

    The screen is under test here, not the composer: three of the four
    variable-length values it interpolates (the disposition breakdown, the
    oldest-bucket label, either pending line) are bounded by their *producers*
    and not by the renderer, exactly as C.2's `edges_by_type` was — so they are
    pinned against a payload rather than a vault.
    """
    return {
        "worklist": {"source_action": "attention.list", "cards": cards},
        "review": review or {"source_action": "", "pending": "a named review producer"},
        "flow": flow or {"source_action": "", "pending": "a named flow producer"},
    }


def test_triage_screen_renders_its_panels_in_fixed_order_with_banner_and_separators(
    vault: Path,
) -> None:
    """Screen furniture (spec §2), the triage half of C.2's deep-screen test: the
    screen names itself on line 1, the three panels come in the §1 fixed order
    worklist → review → flow, and exactly one blank line separates them."""
    out = cockpit.render_triage({"screen": "triage", "panels": cockpit.assemble_triage(vault)})
    lines = out.splitlines()

    assert lines[0] == "memoria cockpit: triage"
    assert lines[1] == ""
    labels = ("attention worklist (", "review queue (", "flow (")
    headings = [next(line for line in lines if line.startswith(label)) for label in labels]
    positions = [lines.index(heading) for heading in headings]
    assert positions == sorted(positions)
    for heading in headings:
        assert lines[lines.index(heading) - 1] == "", f"no separator above {heading}"
    assert "\n\n\n" not in out
    assert out.endswith("\n")
    assert not out.endswith("\n\n")


def test_triage_headings_name_the_row_each_panel_wrapped(vault: Path) -> None:
    """A heading is a grounding claim, on this screen as on the deep one.

    The review and flow headings change with their seams, so both forms are held
    by the both-branch test below. The worklist's row is registered today and its
    heading is therefore the same string in every vault — which is exactly what
    makes a hard-coded heading invisible. Hold it against a panel that names a
    different row, and one that names none.
    """
    panels = cockpit.assemble_triage(vault)

    unsourced = cockpit.render_triage(
        {
            "screen": "triage",
            "panels": {**panels, "worklist": {**panels["worklist"], "source_action": ""}},
        }
    )

    assert "attention worklist (no registry row yet)" in unsourced
    assert "attention worklist (attention.list)" not in unsourced

    renamed = cockpit.render_triage(
        {
            "screen": "triage",
            "panels": {
                **panels,
                "worklist": {**panels["worklist"], "source_action": "attention.get"},
            },
        }
    )

    assert "attention worklist (attention.get)" in renamed


def test_triage_worklist_rows_render_in_payload_order_verbatim(vault: Path) -> None:
    """Spec §1 triage 1 / I1 contract 6: `attention-as-projection` is satisfied
    structurally — I1 owns the order and the cockpit re-sorts nothing, at the text
    layer as much as in the payload.

    The vault's own worklist happens to arrive in path order, so a renderer-side
    `sorted()` would be a no-op against it and no assertion on the fixture could
    see it. The second half holds the guarantee against an order that matches no
    obvious key — not path, not title, not either reversed — which is what an
    I1-ranked worklist will look like.
    """
    panels = cockpit.assemble_triage(vault)
    cards = panels["worklist"]["cards"]
    assert len(cards) == 3

    out = cockpit.render_triage({"screen": "triage", "panels": panels})

    assert [out.index(card["path"]) for card in cards] == sorted(
        out.index(card["path"]) for card in cards
    )

    ranked = cards[1:] + cards[:1]
    paths = [card["path"] for card in ranked]
    assert paths != sorted(paths)
    assert paths != sorted(paths, reverse=True)
    assert paths != [card["path"] for card in sorted(ranked, key=lambda card: card["title"])]

    listed = cockpit.render_triage(
        {
            "screen": "triage",
            "panels": {**panels, "worklist": {**panels["worklist"], "cards": ranked}},
        }
    )

    assert [listed.index(path) for path in paths] == sorted(listed.index(path) for path in paths)


def test_triage_worklist_row_states_the_title_kind_and_path_it_carries() -> None:
    """One row, numbered, saying which card it is (`title`), what kind of call it
    makes (`kind`) and where it lives (`path` — the value the researcher opens).
    Dropping any of the three still renders a plausible-looking worklist."""
    out = cockpit.render_triage(
        {
            "screen": "triage",
            "panels": _triage_panels(
                [
                    {"title": "Ground claim two", "kind": "gap", "path": "inbox/gap-two.md"},
                    {"title": "Extend the outline", "kind": "work-prompt", "path": "inbox/wp.md"},
                ]
            ),
        }
    )

    assert _panel_body(out, "attention worklist (attention.list)") == [
        "  1. Ground claim two  [gap]  inbox/gap-two.md",
        "  2. Extend the outline  [work-prompt]  inbox/wp.md",
    ]


def test_triage_worklist_discloses_rank_factors_only_when_the_card_carries_them() -> None:
    """I1 contract 6, both-branch: `rank_factors` is the per-row disclosure of an
    order the cockpit does not own. A card carrying it gets one disclosure line in
    a fixed key order; a card carrying none gets no line at all — an empty `rank:`
    under a row claims the ranker weighed nothing, which is a different claim from
    "this vault has no ranker yet"."""
    out = cockpit.render_triage(
        {
            "screen": "triage",
            "panels": _triage_panels(
                [
                    {
                        "title": "Ground claim two",
                        "kind": "gap",
                        "path": "inbox/gap-two.md",
                        # Emitted in an order that is neither sorted nor its
                        # reverse, so the renderer's fixed order is load-bearing.
                        "rank_factors": {"loudness": "alert", "age_days": 12, "kind_weight": 3},
                    },
                    {"title": "Extend the outline", "kind": "work-prompt", "path": "inbox/wp.md"},
                    # Present but empty: a ranker that weighed nothing on this
                    # card. Same rule as panel 1's empty thesis — a label with
                    # no value under it is a claim, not a blank.
                    {
                        "title": "Read the 2019 review",
                        "kind": "candidate",
                        "path": "inbox/cand.md",
                        "rank_factors": {},
                    },
                    # Truthy but not a mapping. I1's own contract discloses a
                    # non-enum ranking input "verbatim in rank_factors (fail
                    # visible, never silent)", and every attention-card field is
                    # read straight off note frontmatter (`_attention_card`,
                    # engine/api.py) — so a hand-edited `rank_factors: alert`
                    # reaches this renderer as a bare string. Without the
                    # isinstance half of the guard, `sorted("alert")` succeeds
                    # and the key lookup then raises, killing the whole screen
                    # over one edited note.
                    {
                        "title": "Check the deprivation protocol",
                        "kind": "gap",
                        "path": "inbox/protocol.md",
                        "rank_factors": "alert",
                    },
                ]
            ),
        }
    )

    assert _panel_body(out, "attention worklist (attention.list)") == [
        "  1. Ground claim two  [gap]  inbox/gap-two.md",
        "     rank: age_days=12 kind_weight=3 loudness=alert",
        "  2. Extend the outline  [work-prompt]  inbox/wp.md",
        "  3. Read the 2019 review  [candidate]  inbox/cand.md",
        "  4. Check the deprivation protocol  [gap]  inbox/protocol.md",
    ]


def test_triage_worklist_says_it_is_empty_rather_than_going_silent() -> None:
    """The honesty branch C.2 met in panel 4: "the queue is empty" is a claim the
    researcher can act on, a heading with nothing under it is silence. A worklist
    that has cards must not also say it is empty."""
    empty = cockpit.render_triage({"screen": "triage", "panels": _triage_panels([])})

    assert _panel_body(empty, "attention worklist (attention.list)") == ["  (worklist empty)"]

    full = cockpit.render_triage(
        {
            "screen": "triage",
            "panels": _triage_panels(
                [{"title": "Ground claim two", "kind": "gap", "path": "inbox/gap-two.md"}]
            ),
        }
    )

    assert "(worklist empty)" not in full


def test_triage_screen_states_the_live_counts_its_panels_carry() -> None:
    """The live review and flow lines — the numbers the researcher reads. C.2's
    lesson: a count pinned in the payload and unasserted in the render can be
    dropped, swapped or hard-coded with the suite green, so both bodies are held
    as exact lists. The disposition breakdown arrives unsorted, and the empty
    queue renders `none` rather than an empty pair of brackets."""
    panels = _triage_panels(
        [],
        review={
            "source_action": "views.evidence_review",
            "open": 4,
            "counts": {"accepted": 3, "deferred": 2, "open": 4},
            "srd_gaps": 1,
        },
        flow={
            "source_action": "dashboard.read",
            "open_total": 7,
            "inflow": 5,
            "drain": 2,
            "oldest": ">30d",
        },
    )

    out = cockpit.render_triage({"screen": "triage", "panels": panels})

    assert _panel_body(out, "review queue (views.evidence_review)") == [
        "  open: 4  (accepted=3 deferred=2 open=4)",
        "  srd gaps: 1",
        "  hosted by: memoria review (V2)",
    ]
    assert _panel_body(out, "flow (dashboard.read)") == [
        "  open 7 | inflow 5 / drain 2 | oldest >30d"
    ]

    drained = cockpit.render_triage(
        {
            "screen": "triage",
            "panels": {
                **panels,
                "review": {
                    "source_action": "views.evidence_review",
                    "open": 0,
                    "counts": {},
                    "srd_gaps": 0,
                },
            },
        }
    )

    assert _panel_body(drained, "review queue (views.evidence_review)")[0] == "  open: 0  (none)"


def test_triage_review_and_flow_lines_render_their_live_producers(vault: Path) -> None:
    """The two seams C.3 composes without owning: V2R-B.4's queue and T.3's
    dashboard row. Both have landed, so both panels are pinned live — no
    named-pending arm remains to be honest about. The `memoria review`
    invocation is asserted alongside them, because the cockpit links to V2's
    review flow and never re-hosts it (spec §1 triage 2)."""
    panels = cockpit.assemble_triage(vault)
    out = cockpit.render_triage({"screen": "triage", "panels": panels})

    review = panels["review"]
    assert review["source_action"] == "views.evidence_review"
    assert {"open", "counts", "srd_gaps"} <= set(review)
    body = _panel_body(out, "review queue (views.evidence_review)")
    assert body[0] == f"  open: {review['open']}  " + (
        "(" + " ".join(f"{k}={v}" for k, v in review["counts"].items()) + ")"
        if review["counts"]
        else "(none)"
    )
    assert not any(line.lstrip().startswith("pending:") for line in body)
    assert "  hosted by: memoria review (V2)" in out

    flow = panels["flow"]
    assert flow["source_action"] == "dashboard.read"
    assert "pending" not in flow
    assert _panel_body(out, "flow (dashboard.read)") == [
        f"  open {flow['open_total']} | inflow {flow['inflow']} / "
        f"drain {flow['drain']} | oldest {flow['oldest']}"
    ]


def test_triage_screen_never_wraps_an_identifier_mid_token(vault: Path) -> None:
    """The keep-test rule (spec §2) on the triage screen, and the routing class
    C.2's second review found: `_fit(prefix, value)` and `f"{prefix}{value}"` are
    byte-identical for every line that already fits, so a call site whose value
    cannot exceed the layout is untested however many assertions surround it.

    Every interpolated value is therefore made over-long at least once: the
    worklist row (a vault can supply a long attention path), the rank disclosure,
    both live count lines and both pending lines. The last four are bounded by
    their producers rather than by the renderer — which is not hypothetical, the
    review panel's own pending string is 91 characters — so they come from an
    explicit payload.
    """
    long_path = "inbox/" + "z" * 100 + ".md"
    assert len(long_path) > cockpit.LAYOUT_COLUMNS
    live = cockpit.render_triage(
        {
            "screen": "triage",
            "panels": _triage_panels(
                [
                    {
                        "title": "Follow up the 2019 sleep restriction review before the "
                        "draft leans on it again",
                        "kind": "candidate",
                        "path": long_path,
                        "rank_factors": {
                            "age_days": 41,
                            "kind_weight": 3,
                            "loudness": "alert",
                            "open_dependents": 6,
                            "routing_class": "ask",
                            "staleness_days": 19,
                        },
                    }
                ],
                review={
                    "source_action": "views.evidence_review",
                    "open": 4,
                    "counts": {
                        "accepted": 31,
                        "deferred": 22,
                        "edited": 13,
                        "open": 4,
                        "quarantined": 5,
                        "rejected": 26,
                        "superseded": 7,
                    },
                    "srd_gaps": 2,
                },
                flow={
                    "source_action": "dashboard.read",
                    "open_total": 1240,
                    "inflow": 3175,
                    "drain": 2896,
                    "oldest": "older than the first journal entry this vault carries",
                },
            ),
        }
    )
    pending = cockpit.render_triage(
        {
            "screen": "triage",
            "panels": _triage_panels(
                [],
                review={
                    "source_action": "",
                    "pending": (
                        "engine_api.evidence_review_queue + the views.evidence_review "
                        "registry row (V2 plan V2R-B.4)"
                    ),
                },
                flow={
                    "source_action": "",
                    "pending": (
                        "a registered dashboard.read row with a live engine binding "
                        "(U2 plan T.3, after I1 H.2)"
                    ),
                },
            ),
        }
    )
    real = cockpit.render_triage({"screen": "triage", "panels": cockpit.assemble_triage(vault)})

    for line in live.splitlines() + pending.splitlines() + real.splitlines():
        assert len(line) <= cockpit.LAYOUT_COLUMNS or line.strip() == long_path
    assert any(line.strip() == long_path for line in live.splitlines())


def test_the_two_screens_never_mix(vault: Path) -> None:
    """Spec §1: deep work sees no queue; triage sees no draft. The split is
    enforced by layout, which is what makes the frame fixed and the content
    adaptive rather than the other way round."""
    deep = cockpit.render_deep(
        {
            "screen": "deep",
            "project": PROJECT_REL,
            "panels": cockpit.assemble_deep(vault, PROJECT_REL),
        }
    )
    triage = cockpit.render_triage({"screen": "triage", "panels": cockpit.assemble_triage(vault)})

    assert "attention worklist (" not in deep
    assert "review queue (" not in deep
    assert "flow (" not in deep
    assert "memoria cockpit: deep work" not in triage
    assert "draft (project.draft.read)" not in triage
    assert "grounds (project.draft.read)" not in triage
    assert "thesis" not in triage


def _queue_rows() -> list[dict[str, Any]]:
    """Twelve evidence rows plus one SRD gap and one row of a kind the panel has
    never heard of. More than ten, so an unbounded `batch=0` read is the only one
    that can produce these counts against V2's default batch of ten.

    The dispositions arrive in an order that is neither sorted nor its reverse,
    and four rows are open in four different shapes — the literal `"open"`, an
    explicit `None`, an empty string, and no `disposition` key at all — because
    "not yet decided" is what a fresh queue row looks like from every producer
    that has not written a disposition event for it.
    """
    dispositions: list[Any] = [
        "rejected",
        None,
        "accepted",
        "deferred",
        "",
        "rejected",
        "accepted",
        "deferred",
        "accepted",
        "rejected",
        "open",
    ]
    rows: list[dict[str, Any]] = [
        {
            "kind": "evidence-set",
            "evidence_id": f"ev-{index:08d}",
            "disposition": disposition,
            "claim_text": "Sleep restriction degrades declarative consolidation",
            "project": PROJECT_REL,
        }
        for index, disposition in enumerate(dispositions)
    ]
    rows.append(
        {
            "kind": "evidence-set",
            "evidence_id": "ev-00000011",
            "claim_text": "Recovery sleep does not restore the lost consolidation",
            "project": PROJECT_REL,
        }
    )
    rows.append({"kind": "srd-gap", "ref": "inbox/srd-one.md", "title": "SRD gap"})
    # One row of an unrecognised kind *among* recognised ones: there is no
    # honest count for a third variant, so it joins neither total. That is a
    # narrower claim than "an unknown row may always be dropped" — a queue in
    # which *no* row is recognised is a shape mismatch, and the panel says so
    # rather than reporting a confident zero (see the shape test below).
    rows.append({"evidence_id": "ev-99999999", "disposition": "accepted"})
    return rows


def _live_review_seam(monkeypatch: pytest.MonkeyPatch, rows: list[dict[str, Any]]) -> None:
    """Both halves of V2R-B.4's seam, serving `rows`."""

    def fake_queue(workspace: Path, **kwargs: Any) -> dict[str, Any]:
        return {"ok": True, "rows": rows, "total": len(rows), "batch": 0, "facet_totals": {}}

    monkeypatch.setattr(engine_api, "evidence_review_queue", fake_queue, raising=False)
    monkeypatch.setattr(
        cockpit,
        "actions_by_id",
        lambda: {
            **actions_by_id(),
            "views.evidence_review": {"id": "views.evidence_review", "engine": "x"},
        },
    )


def test_review_panel_reports_no_open_work_on_a_fully_triaged_queue(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The drained queue, held on the *builder* side.

    `open` falls back to `0` whenever the live queue has no `open` row, and per
    V2's own row builder that is not an edge case: a raw row's `disposition` is
    only ever `"rejected"` or `"open"` (accepted-and-cleared and defer-active
    rows leave the queue entirely), so a vault whose reviewer has worked the
    queue down takes this default on *every* read. The renderer's own drained
    case is pinned against an explicit `{"open": 0, "counts": {}}` payload,
    which is exactly what leaves the builder's default unheld: under a mutated
    default the screen reads `open: None  (rejected=3)` with the suite green.
    """
    rows = [
        {"kind": "evidence-set", "evidence_id": f"ev-{index:08d}", "disposition": "rejected"}
        for index in range(3)
    ]
    _live_review_seam(monkeypatch, rows)

    review = cockpit.assemble_triage(vault)["review"]

    assert review == {
        "source_action": "views.evidence_review",
        "open": 0,
        "counts": {"rejected": 3},
        "srd_gaps": 0,
    }
    out = cockpit.render_triage({"screen": "triage", "panels": cockpit.assemble_triage(vault)})
    assert "  open: 0  (rejected=3)" in out


def test_review_panel_says_the_queue_shape_changed_rather_than_counting_zero(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Absence and shape mismatch are different claims (spec §1 triage 2).

    The panel discriminates V2's raw union on `kind`. Two superseded layers of
    the V2 plan still describe a CLI DTO carrying no `kind` at all, and V2R-B.5
    lands independently of this consumer — so "the seam landed with a different
    row shape" is a live outcome, not a hypothetical. Counting such a queue
    yields `open: 0  (none)` under a registry-row heading: a confident number
    about rows the panel never understood. Naming the mismatch is worth more
    than a wrong zero, and it fails INT.1's endgame rule loudly.
    """
    rows = [
        {"evidence_id": "ev-00000001", "latest_decision": "accept", "project": PROJECT_REL},
        {"evidence_id": "ev-00000002", "latest_decision": "", "project": PROJECT_REL},
    ]
    _live_review_seam(monkeypatch, rows)

    review = cockpit.assemble_triage(vault)["review"]

    assert review["source_action"] == "views.evidence_review"
    assert "open" not in review
    assert review["pending"] == (
        "2 queue rows carry no evidence-set/srd-gap kind — the raw queue shape changed "
        "(V2 plan amendment 2026-07-29 §2)"
    )

    out = cockpit.render_triage({"screen": "triage", "panels": cockpit.assemble_triage(vault)})
    assert "open: 0" not in out
    assert "queue rows carry no evidence-set/srd-gap kind" in out

    # An empty queue is still absence, not mismatch: it counts to zero.
    _live_review_seam(monkeypatch, [])

    assert cockpit.assemble_triage(vault)["review"] == {
        "source_action": "views.evidence_review",
        "open": 0,
        "counts": {},
        "srd_gaps": 0,
    }


def test_review_panel_counts_the_raw_queue_once_and_never_the_view(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Raw-counts amendment (2026-07-29) §1: the live branch calls V2's
    engine-direct collector with `batch=0` and the cockpit's `read_scope`, counts
    only `kind == "evidence-set"` rows by disposition, and reports the SRD-gap
    variants as a separate read-only count. It never calls
    `read_evidence_review_view` — counting a projection means parsing cards V2
    owns, which is the re-hosting the spec forbids — so that helper is poisoned
    here and would fail the test if reached.
    """
    calls: list[dict[str, Any]] = []

    def fake_queue(workspace: Path, **kwargs: Any) -> dict[str, Any]:
        calls.append({"workspace": workspace, **kwargs})
        rows = _queue_rows()
        return {"ok": True, "rows": rows, "total": len(rows), "batch": 0, "facet_totals": {}}

    def poisoned_view(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise AssertionError("the review panel must never call read_evidence_review_view")

    monkeypatch.setattr(engine_api, "evidence_review_queue", fake_queue, raising=False)
    monkeypatch.setattr(engine_api, "read_evidence_review_view", poisoned_view, raising=False)
    monkeypatch.setattr(
        cockpit,
        "actions_by_id",
        lambda: {
            **actions_by_id(),
            "views.evidence_review": {
                "id": "views.evidence_review",
                "job": "review",
                "engine": "read_evidence_review_view",
            },
        },
    )
    scope = ["projects", "inbox"]

    review = cockpit.assemble_triage(vault, read_scope=scope)["review"]

    assert calls == [{"workspace": Path(vault), "batch": 0, "read_scope": scope}]
    assert review == {
        "source_action": "views.evidence_review",
        "open": 4,
        # Sorted, though the queue emitted `rejected` first, and the row whose
        # `kind` the panel does not recognise is in none of these counts.
        "counts": {"accepted": 3, "deferred": 2, "open": 4, "rejected": 3},
        "srd_gaps": 1,
    }
    assert list(review["counts"]) == ["accepted", "deferred", "open", "rejected"]


def test_review_panel_counts_the_queue_and_never_re_hosts_it(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Spec §1 triage 2: the triage screen *counts* V2's queue and links to it —
    it never re-hosts it. A claim rendered here would be a second review surface
    with none of V2's card grammar, so no row content may reach the screen."""

    def fake_queue(workspace: Path, **kwargs: Any) -> dict[str, Any]:
        rows = _queue_rows()
        return {"ok": True, "rows": rows, "total": len(rows), "batch": 0, "facet_totals": {}}

    monkeypatch.setattr(engine_api, "evidence_review_queue", fake_queue, raising=False)
    monkeypatch.setattr(
        cockpit,
        "actions_by_id",
        lambda: {
            **actions_by_id(),
            "views.evidence_review": {"id": "views.evidence_review", "engine": "x"},
        },
    )

    panels = cockpit.assemble_triage(vault)
    out = cockpit.render_triage({"screen": "triage", "panels": panels})

    assert _panel_body(out, "review queue (views.evidence_review)") == [
        "  open: 4  (accepted=3 deferred=2 open=4 rejected=3)",
        "  srd gaps: 1",
        "  hosted by: memoria review (V2)",
    ]
    assert "Sleep restriction degrades" not in out
    assert "ev-00000000" not in out
    assert "claim_text" not in json.dumps(panels["review"])


def test_review_panel_stays_pending_until_both_halves_of_the_seam_exist(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Either half alone is not a seam (raw-counts amendment §1). A collector with
    no registered row has no honest `source_action` to name — naming an
    unregistered id is the whitelisting §2/§3 forbids — and a registered row with
    no collector has nothing to count. The panel must not call the collector in
    either case, or a half-landed V2 turns every cockpit read into an error."""
    calls: list[Path] = []

    def fake_queue(workspace: Path, **kwargs: Any) -> dict[str, Any]:
        calls.append(workspace)
        return {"ok": True, "rows": [], "total": 0, "batch": 0, "facet_totals": {}}

    without_row = {
        key: row for key, row in actions_by_id().items() if key != "views.evidence_review"
    }
    with_row = {**without_row, "views.evidence_review": {"id": "views.evidence_review"}}

    monkeypatch.setattr(engine_api, "evidence_review_queue", fake_queue, raising=False)
    monkeypatch.setattr(cockpit, "actions_by_id", lambda: without_row)

    collector_only = cockpit.assemble_triage(vault)["review"]

    monkeypatch.delattr(engine_api, "evidence_review_queue", raising=False)
    monkeypatch.setattr(cockpit, "actions_by_id", lambda: with_row)

    row_only = cockpit.assemble_triage(vault)["review"]

    assert calls == []
    for panel in (collector_only, row_only):
        assert panel["source_action"] == ""
        assert panel["pending"] == (
            "engine_api.evidence_review_queue + the views.evidence_review registry row "
            "(V2 plan V2R-B.4)"
        )


def _dashboard_row() -> dict[str, dict[str, Any]]:
    return {
        **actions_by_id(),
        "dashboard.read": {"id": "dashboard.read", "job": "review", "engine": "read_dashboard"},
    }


def test_flow_panel_consumes_the_registered_dashboard_engine(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Registered-only composition amendment §2/§3: the panel calls whatever
    engine the `dashboard.read` row binds — never `assemble_dashboard` directly,
    which would reconstruct a view U2 does not own — and reads
    `dashboard["attention_flow"]` out of that engine's read envelope.

    Every number is distinguishable: the two day maps carry several days each, so
    a panel that reported a day count or the first day's value instead of the sum
    would pass on a one-day fixture, and inflow, drain and the open total are
    three different numbers.
    """
    seen: list[Path] = []

    def fake_read_dashboard(workspace: Path) -> dict[str, Any]:
        seen.append(workspace)
        return {
            "ok": True,
            "api_version": 1,
            "dashboard": {
                "attention_flow": {
                    "open_total": 7,
                    "open_by_loudness": {"alert": 5, "block": 2},
                    "inflow_by_day": {"2026-07-28": 2, "2026-07-29": 3, "2026-07-30": 6},
                    "drain_by_day": {"2026-07-29": 1, "2026-07-30": 3},
                    "net_by_day": {"2026-07-30": 3},
                    "age_distribution": {"0-7d": 4, "8-30d": 2, ">30d": 1},
                    "per_producer": {"sweep": 7},
                    "skipped_runs": {},
                },
                "dispositions": {"total": 9},
            },
        }

    monkeypatch.setattr(engine_api, "read_dashboard", fake_read_dashboard, raising=False)
    monkeypatch.setattr(cockpit, "actions_by_id", _dashboard_row)

    flow = cockpit.assemble_triage(vault)["flow"]

    assert seen == [Path(vault)]
    assert flow == {
        "source_action": "dashboard.read",
        "open_total": 7,
        "inflow": 11,
        "drain": 4,
        "oldest": ">30d",
    }


def test_flow_panel_names_the_oldest_non_empty_age_bucket(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """ "Oldest" is the oldest bucket that actually holds a card, so the search
    runs oldest-first and an empty bucket is not an answer: a panel that took the
    first key, or any key present, would pass on a single-bucket fixture and
    report `0-7d` for a queue whose oldest item is a month old.

    A dashboard that carries only `open_total` still renders: an I1 payload
    missing a key it declares is one panel's problem, not the whole screen's.
    """
    ages: dict[str, Any] = {}

    def fake_read_dashboard(workspace: Path) -> dict[str, Any]:
        return {"ok": True, "dashboard": {"attention_flow": {"open_total": 3, **ages}}}

    monkeypatch.setattr(engine_api, "read_dashboard", fake_read_dashboard, raising=False)
    monkeypatch.setattr(cockpit, "actions_by_id", _dashboard_row)

    ages = {"age_distribution": {"0-7d": 4, "8-30d": 2}}
    assert cockpit.assemble_triage(vault)["flow"]["oldest"] == "8-30d"

    ages = {"age_distribution": {"0-7d": 4, "8-30d": 0, ">30d": 0}}
    assert cockpit.assemble_triage(vault)["flow"]["oldest"] == "0-7d"

    ages = {"age_distribution": {}}
    assert cockpit.assemble_triage(vault)["flow"]["oldest"] == "none"

    ages = {}
    assert cockpit.assemble_triage(vault)["flow"] == {
        "source_action": "dashboard.read",
        "open_total": 3,
        "inflow": 0,
        "drain": 0,
        "oldest": "none",
    }


def test_flow_panel_reports_a_drained_dashboard_as_zero_rather_than_a_default(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The `open_total` fallback, held on the builder side.

    Every other fixture on this panel carries a truthy `open_total`, so the
    `or 0` default is only ever reached by the producer state none of them
    build: a workspace whose attention queue is drained. I1 may report that as
    `open_total: 0` (falsy, so the default fires) or by omitting the key, and
    both must read as zero rather than as whatever literal the fallback names.
    """
    flow: dict[str, Any] = {}

    def fake_read_dashboard(workspace: Path) -> dict[str, Any]:
        return {"ok": True, "dashboard": {"attention_flow": flow}}

    monkeypatch.setattr(engine_api, "read_dashboard", fake_read_dashboard, raising=False)
    monkeypatch.setattr(cockpit, "actions_by_id", _dashboard_row)

    flow = {"open_total": 0, "inflow_by_day": {"2026-07-30": 2}}
    assert cockpit.assemble_triage(vault)["flow"]["open_total"] == 0

    flow = {"inflow_by_day": {"2026-07-30": 2}}
    assert cockpit.assemble_triage(vault)["flow"]["open_total"] == 0


def test_flow_panel_stays_pending_unless_a_registered_row_binds_a_live_engine(
    vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Registered-only composition, in both directions (amendment §2/§3).

    A reserved row is not a producer: U1's registry grammar allows a row with
    no engine (`context.read` was one until U2 T.3 wired it), and a panel that
    named `dashboard.read` on the strength of the row alone would claim a read
    that cannot run — which is why the row is simulated here. And an
    engine with no row is not a producer either: I1 ships `assemble_dashboard`
    and `memoria dashboard` long before T.3 registers U2's CLI-only row, and
    consuming it then would be the reaching-past-the-registry the amendment
    forbids. Neither half may call anything.
    """
    calls: list[Path] = []

    def fake_read_dashboard(workspace: Path) -> dict[str, Any]:
        calls.append(workspace)
        return {"ok": True, "dashboard": {"attention_flow": {"open_total": 9}}}

    monkeypatch.setattr(engine_api, "read_dashboard", fake_read_dashboard, raising=False)
    monkeypatch.setattr(
        cockpit,
        "actions_by_id",
        lambda: {**actions_by_id(), "dashboard.read": {"id": "dashboard.read", "engine": None}},
    )

    unbound = cockpit.assemble_triage(vault)["flow"]

    monkeypatch.setattr(
        cockpit,
        "actions_by_id",
        lambda: {
            **actions_by_id(),
            "dashboard.read": {"id": "dashboard.read", "engine": "read_dashboard_absent"},
        },
    )

    unresolvable = cockpit.assemble_triage(vault)["flow"]

    monkeypatch.setattr(
        cockpit,
        "actions_by_id",
        lambda: {key: row for key, row in actions_by_id().items() if key != "dashboard.read"},
    )

    unregistered = cockpit.assemble_triage(vault)["flow"]

    assert calls == []
    for panel in (unbound, unresolvable, unregistered):
        assert panel["source_action"] == ""
        assert panel["pending"] == "the dashboard.read registry row (U2 plan T.3)"


def test_read_cockpit_bounds_both_screens_by_read_scope(vault: Path) -> None:
    """Scoped-trace amendment (2026-07-29) §1: `read_cockpit` is an
    optional-scope surface, so the envelope entry point has to *propagate*
    `read_scope` into whichever screen it composes.

    This is the only producer of that parameter: `memoria cockpit` carries no
    `--read-scope` flag (C.4's interface list), so a hop that accepted the
    argument and dropped it would widen every bounded caller — the MCP/HTTP
    doors T.3 registers, and U4's context handoff — with nothing in the CLI
    tests able to see it. One case per screen, each distinguished by which read
    refuses first.
    """
    outline = "projects/study-alpha/outline.md"
    draft = "projects/study-alpha/draft.md"

    # deep, resolved: the resolver's read_concepts is scoped away from projects/
    bare = engine_api.read_cockpit(vault, read_scope=["notes"])
    assert bare["resolution"] == "ambiguous"
    assert bare["projects"] == []
    assert engine_api.read_cockpit(vault)["project"] == PROJECT_REL

    # deep, explicit project: the panel reads refuse in slice → draft → concept
    # order, so each hop that keeps the scope names itself.
    with pytest.raises(FileNotFoundError, match="project slice not found"):
        engine_api.read_cockpit(vault, project_path=PROJECT_REL, read_scope=["notes"])
    with pytest.raises(FileNotFoundError, match="project draft not found"):
        engine_api.read_cockpit(vault, project_path=PROJECT_REL, read_scope=[outline])
    scoped = engine_api.read_cockpit(
        vault, project_path=PROJECT_REL, read_scope=[outline, draft, PROJECT_REL, "notes"]
    )
    assert set(scoped["panels"]) == {"project", "slice", "draft", "grounds", "trace", "context"}

    # triage: the worklist's read_attention is scoped away from inbox/
    assert len(engine_api.read_cockpit(vault, triage=True)["panels"]["worklist"]["cards"]) == 3
    assert (
        engine_api.read_cockpit(vault, triage=True, read_scope=["notes"])["panels"]["worklist"][
            "cards"
        ]
        == []
    )


def test_cli_cockpit_pipe_identity_and_valid_text_buffer(
    vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Keep-test (U2 spec §2): static photograph — two runs byte-identical;
    `memoria cockpit | cat` (a real pipe, via subprocess) byte-identical to
    both; no ANSI; a valid nano/vim buffer; 80-column layout target with
    whole-identifier overflow only.

    Both screens, because the guarantee is the cockpit's and not the deep
    screen's: the triage screen is the one whose rows come from a projection the
    cockpit does not own, and it is reached by a different renderer call.
    """
    for extra, banner in (
        (["--project", PROJECT_REL], "memoria cockpit: deep work"),
        (["--triage"], "memoria cockpit: triage"),
    ):
        argv = ["cockpit", "--workspace", str(vault), *extra]

        assert main(argv) == 0
        first = capsys.readouterr().out
        assert main(argv) == 0
        second = capsys.readouterr().out
        # The child must run *this* checkout, the way pytest's
        # `pythonpath = ["src"]` makes the in-process call do
        # (test_package_spine's idiom). Without it the subprocess resolves
        # whatever `memoria_vault` the environment installed, and the
        # comparison stops being about this code at all.
        piped = subprocess.run(
            [sys.executable, "-m", "memoria_vault.cli", *argv],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        ).stdout

        assert first == second == piped
        assert first.splitlines()[0] == banner
        assert "\x1b" not in first
        assert "\r" not in first and "\x00" not in first
        assert first.endswith("\n")
        for line in first.splitlines():
            assert len(line) <= 80 or len(line.split()) == 1


def test_cli_cockpit_json_panels_carry_source_action(
    vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The `--json` surface (spec §2): the read envelope, the two fixed panel
    key sets, and the registered-only composition rule carried through
    `json.dumps` rather than only through the builder return values.

    Registered-only composition (amendment 2026-07-29 §2/§3): a panel names a
    *currently registered* action id, or it names nothing and says what it is
    waiting for. The drafted `known_rows` whitelist for `dashboard.read` is
    superseded — whitelisting an unregistered id here is precisely what that
    amendment forbids.
    """
    assert main(["cockpit", "--workspace", str(vault), "--project", PROJECT_REL, "--json"]) == 0
    deep = json.loads(capsys.readouterr().out)
    assert main(["cockpit", "--workspace", str(vault), "--triage", "--json"]) == 0
    triage = json.loads(capsys.readouterr().out)

    for payload in (deep, triage):
        assert payload["ok"] is True
        assert payload["api_version"] == "engine-read-api.v1"
    assert deep["screen"] == "deep" and triage["screen"] == "triage"
    assert deep["project"] == PROJECT_REL
    assert set(deep["panels"]) == {"project", "slice", "draft", "grounds", "trace", "context"}
    assert set(triage["panels"]) == {"worklist", "review", "flow"}
    registered = set(actions_by_id())
    for name, panel in {**deep["panels"], **triage["panels"]}.items():
        assert "source_action" in panel, name
        if panel["source_action"]:
            assert panel["source_action"] in registered, f"{name} names an unregistered action"
        else:
            assert panel["pending"], f"{name} has neither a source action nor a pending line"


def test_cli_cockpit_bare_ambiguous_lists_and_exits_honestly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)

    assert main(["cockpit", "--workspace", str(workspace)]) == 0
    assert "no active projects" in capsys.readouterr().out

    assert main(["cockpit", "--workspace", str(workspace), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["resolution"] == "ambiguous"
    assert payload["projects"] == []
    assert "panels" not in payload


def test_cli_cockpit_refuses_mixed_screens(vault: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["cockpit", "--workspace", str(vault), "--project", PROJECT_REL, "--triage"])

    captured = capsys.readouterr()
    assert rc == 2
    assert "never mix" in captured.err
    # The refusal happens before any read: neither screen is composed, so
    # neither screen's banner reaches stdout.
    assert captured.out == ""


def test_cli_cockpit_reads_leave_tree_clean(
    vault: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """I1 T.4 pattern: reads never touch tracked state (telemetry, once I1
    lands, goes to the untracked sqlite store)."""
    before = git(vault, "status", "--porcelain")

    assert main(["cockpit", "--workspace", str(vault), "--project", PROJECT_REL]) == 0
    assert main(["cockpit", "--workspace", str(vault), "--triage"]) == 0
    assert main(["cockpit", "--workspace", str(vault), "--project", PROJECT_REL, "--json"]) == 0
    capsys.readouterr()

    assert git(vault, "status", "--porcelain") == before


# --- INT.1: post-seam triage integration -------------------------------------

INT_PROJECT = "projects/int-review/project.md"
INT_SCOPE = ["projects", "inbox"]


def _int_note(vault: Path, index: int) -> str:
    stem = f"int-claim-{index:02d}"
    write_checked_concept(
        vault,
        f"notes/{stem}.md",
        f"type: note\ncheck_status: checked\ntitle: Claim {index}\nid: int-note-{index:02d}\n",
        "note",
        body=f"An implicit synthesis claim number {index}.",
    )
    return f"int-note-{index:02d}"


def _int_review_vault(vault: Path) -> dict[str, str]:
    """Thirteen composed evidence sets over one checked project, dispositioned
    into the only queue states V2's row builder can produce, plus one open
    SRD-gap attention card.

    Thirteen, not eleven: `accept` and `defer` are *not* dispositions a queued
    row can carry (see the INT.1 counts note in the test below), so the two
    rows carrying them leave the queue entirely and eleven remain — one more
    than the ten-row presentation batch.
    """
    write_checked_concept(
        vault,
        INT_PROJECT,
        "type: project\ncheck_status: checked\ntitle: Int review\n",
        "project",
    )
    ids = [_int_note(vault, index) for index in range(13)]
    (vault / "projects/int-review/outline.md").write_text(
        "".join(f"- {note_id} — claim\n" for note_id in ids), encoding="utf-8"
    )
    call_with_context(_compose_project_draft, vault, "int-review", machine="compose-machine")

    text = (vault / "projects/int-review/draft.md").read_text(encoding="utf-8")
    evidence_ids = [str(row["id"]) for row in state.evidence_sets(vault)]
    assert len(evidence_ids) == 13, evidence_ids
    assert all(f"^blk-{eid.removeprefix('ev-')}" in text for eid in evidence_ids)

    for evidence_id in evidence_ids[:5]:
        _resolve_evidence_review(
            vault, evidence_id, actor="pi", machine="int", decision="reject", reason="not grounded"
        )
    _resolve_evidence_review(vault, evidence_ids[5], actor="pi", machine="int", decision="accept")
    _resolve_evidence_review(vault, evidence_ids[6], actor="pi", machine="int", decision="defer")

    card = vault / "inbox/int-srd-gap.md"
    card.parent.mkdir(parents=True, exist_ok=True)
    card.write_text(
        "---\nprojection: attention\ntitle: SRD gap\nattention_kind: srd-gap\n"
        "attention_status: open\nrouting_class: ask\nloudness: notice\n"
        "target: projects/int-review/draft.md\n---\nGap body.\n",
        encoding="utf-8",
    )
    return {"rejected": evidence_ids[:5], "accepted": evidence_ids[5], "deferred": evidence_ids[6]}


def test_post_seam_triage_review_uses_the_registered_raw_queue(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """U2 INT.1 (review half): with V2R-B.4/B.5 landed, triage panel 2 counts the
    raw queue engine-direct and the named-pending form is gone.

    **Corrected counts expectation.** The plan's `{"accept": 5, "defer": 5,
    "open": 1}` is unreachable against V2's shipped row builder. A queue row's
    disposition is written by exactly one expression —
    `"rejected" if decision == "reject" else "open"`
    (`runtime/evidence_review.py::_queue_entry`) — so `accept` and `defer` are
    never written to one. Both decisions instead *remove* the row: an accept
    bound to the row's items digest clears its holds and, with no permanent
    block, drops it; a defer stays active through its suppression date and
    drops it too. The fixture therefore disposes thirteen rows and asserts what
    the collector really emits: five `rejected`, six `open`, and the accepted
    and deferred rows absent from the queue altogether.

    The spy proves exactly one unfiltered all-row (`batch=0`) request under the
    caller's own `read_scope`; the poisoned view proves the panel never reaches
    for V2's card projection; thirteen rows past the ten-row presentation batch
    prove the count is the cockpit's own and not an inherited UI page.
    """
    vault = init_cli_workspace(tmp_path, capsys)
    disposed = _int_review_vault(vault)

    calls: list[dict[str, object]] = []
    real_queue = engine_api.evidence_review_queue

    def observed_queue(
        workspace: Path,
        *,
        batch: int = 10,
        read_scope: list[str] | None = None,
        **filters: object,
    ) -> dict[str, object]:
        calls.append(
            {
                "workspace": workspace,
                "batch": batch,
                "read_scope": read_scope,
                "filters": filters,
            }
        )
        return real_queue(workspace, batch=batch, read_scope=read_scope, **filters)

    monkeypatch.setattr(engine_api, "evidence_review_queue", observed_queue)
    monkeypatch.setattr(
        engine_api,
        "read_evidence_review_view",
        lambda *_args, **_kwargs: pytest.fail("cockpit must not call the evidence-review view"),
        raising=False,
    )

    panels = cockpit.assemble_triage(vault, read_scope=INT_SCOPE)

    assert calls == [{"workspace": Path(vault), "batch": 0, "read_scope": INT_SCOPE, "filters": {}}]
    review = panels["review"]
    assert review["source_action"] == "views.evidence_review"
    assert review["counts"] == {"open": 6, "rejected": 5}
    assert review["open"] == review["counts"]["open"] == 6
    assert review["srd_gaps"] == 1
    assert "pending" not in review

    # The evidence for the corrected expectation, read off the producer itself.
    rows = real_queue(vault, batch=0, read_scope=INT_SCOPE)["rows"]
    evidence = [row for row in rows if row["kind"] == "evidence-set"]
    assert len(evidence) == 11
    assert {row["disposition"] for row in evidence} == {"open", "rejected"}
    queued = {str(row["evidence_id"]) for row in evidence}
    assert disposed["accepted"] not in queued
    assert disposed["deferred"] not in queued
    assert set(disposed["rejected"]) <= queued

    rendered = cockpit.render_triage({"screen": "triage", "panels": panels})
    review_section = rendered[rendered.index("review queue (") : rendered.index("flow (")]
    assert "pending:" not in review_section
    assert "open: 6" in review_section


def test_post_seam_review_counts_the_raw_rows_not_the_view_cards(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The row shape U2 depends on, asserted against the real producer rather
    than a simulated one: `kind` must survive onto the *evidence* arm and the
    decision key must still be spelled `disposition`. The superseded V2 DTO
    layer renamed both, and either rename alone turns this panel's honest
    breakdown into a confident wrong one — a missing `kind` reads as a shape
    mismatch, a missing `disposition` reports every row as open."""
    vault = init_cli_workspace(tmp_path, capsys)
    _int_review_vault(vault)

    rows = engine_api.evidence_review_queue(vault, batch=0, read_scope=INT_SCOPE)["rows"]

    kinds = {str(row["kind"]) for row in rows}
    assert kinds == {"evidence-set", "srd-gap"}
    assert kinds <= cockpit.QUEUE_ROW_KINDS
    for row in rows:
        if row["kind"] != "evidence-set":
            continue
        assert "disposition" in row
        assert {"latest_decision", "routing", "project"}.isdisjoint(row)


def _int_flow_vault(vault: Path) -> None:
    """Four flow signals, each with a distinct producer, none of them a default.

    An all-zero dashboard is the shape a fresh vault really has, so a flow panel
    that hard-coded zeros would pass against it. Every number the panel reports
    is therefore given a producer here: a second open card aged past the widest
    bucket (so `oldest` must *choose*, not take the first bucket it finds), two
    `attention-admitted` telemetry rows on one day and two disposition events on
    one day (so a `sum` weakened to a `len` reports 1 instead of 2).
    """
    aged = (datetime.date.today() - datetime.timedelta(days=45)).isoformat()
    (vault / "inbox/int-aged-gap.md").write_text(
        "---\nprojection: attention\ntitle: Aged gap\nattention_kind: gap\n"
        f"attention_status: open\nrouting_class: ask\nloudness: quiet\ncreated: {aged}\n"
        "target: projects/int-review/draft.md\n---\nGap body.\n",
        encoding="utf-8",
    )
    for name in ("inbox/int-admitted-a.md", "inbox/int-admitted-b.md"):
        record_telemetry_event(
            vault,
            "attention-admitted",
            {"card_path": name, "kind": "gap", "loudness": "quiet", "raised_by": "analyze-gaps"},
        )
    for item_id in ("inbox/int-drained-a.md", "inbox/int-drained-b.md"):
        emit_explicit_disposition_event(
            vault,
            decision="accept",
            item_type="attention",
            item_id=item_id,
            actor="pi",
            machine="int",
        )


def test_post_seam_triage_flow_uses_the_registered_dashboard_engine(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """U2 INT.1 (flow half): with T.3's `dashboard.read` row landed, triage panel
    3 reads through the registry engine and the named-pending form is gone.

    **Why the spy perturbs instead of merely counting.** A spy that recorded only
    *that* the engine was called cannot tell the reroute from a direct
    `assemble_dashboard` call or from a stub — every number would match either
    way, because they all end at the same assembler. This one wraps the row's own
    declared engine (name read out of the registry, never hard-coded), records
    what it returned, and shifts `open_total` by a constant no vault state can
    produce. The panel then has to carry the shifted value, which only the
    registry route can supply. The recorded payload is asserted to be the real
    seven-panel envelope, so the pass-through is proven to be I1's assembler and
    not the spy's own invention.

    **Why the two poisons.** `assemble_dashboard` under every name the composer
    could import it by, and `read_dashboard_view` beside it: the panel must not
    reach past the row to the assembler, and must not re-host I1's view
    projection either — the same rule the review half's poisoned view enforces.
    """
    vault = init_cli_workspace(tmp_path, capsys)
    _int_review_vault(vault)
    _int_flow_vault(vault)

    row = actions_by_id()["dashboard.read"]
    assert row["engine"] == "read_dashboard"
    real_dashboard = getattr(engine_api, str(row["engine"]))
    unrouted = real_dashboard(vault)["dashboard"]["attention_flow"]["open_total"]
    seen: list[dict[str, Any]] = []
    shift = 100

    def observed_dashboard(workspace: Path) -> dict[str, Any]:
        payload = real_dashboard(workspace)
        payload["dashboard"]["attention_flow"]["open_total"] += shift
        seen.append({"workspace": Path(workspace), "payload": payload})
        return payload

    monkeypatch.setattr(engine_api, str(row["engine"]), observed_dashboard)
    for module in (cockpit, dashboard_module):
        monkeypatch.setattr(
            module,
            "assemble_dashboard",
            lambda *_args, **_kwargs: pytest.fail(
                "the flow panel must read through the dashboard.read engine binding"
            ),
            raising=False,
        )
    monkeypatch.setattr(
        engine_api,
        "read_dashboard_view",
        lambda *_args, **_kwargs: pytest.fail("the cockpit must not re-host the dashboard view"),
    )

    panels = cockpit.assemble_triage(vault, read_scope=INT_SCOPE)

    assert [call["workspace"] for call in seen] == [Path(vault)]
    envelope = seen[0]["payload"]
    assert set(envelope) == {"ok", "api_version", "dashboard"}
    assert tuple(envelope["dashboard"]) == DASHBOARD_PANELS
    source = envelope["dashboard"]["attention_flow"]

    flow = panels["flow"]
    assert flow["source_action"] == "dashboard.read"
    assert "pending" not in flow
    # Provenance: the panel carries the shifted count, which no other route to
    # the assembler could have produced.
    assert flow["open_total"] == source["open_total"] == unrouted + shift

    # Non-degeneracy, one producer per number.
    assert len(source["inflow_by_day"]) == 1
    assert flow["inflow"] == sum(source["inflow_by_day"].values()) == 2
    assert len(source["drain_by_day"]) == 1
    assert flow["drain"] == sum(source["drain_by_day"].values()) > 1
    assert set(source["age_distribution"]) == {AGE_BUCKETS[0], AGE_BUCKETS[2]}
    assert flow["oldest"] == AGE_BUCKETS[2]

    # Both named-pending forms are gone from the screen, not just from the flow
    # panel: this is the assertion INT.1 exists to make.
    assert "pending" not in panels["review"]
    assert "pending:" not in cockpit.render_triage({"screen": "triage", "panels": panels})
