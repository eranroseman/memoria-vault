"""Cockpit assembly + rendering + keep-test contract (U2 plan section C)."""

from __future__ import annotations

from pathlib import Path

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
    journal side): one active project, two checked notes, an outline whose third
    id resolves nowhere, a draft with one complete and one thin (zero-grounds)
    evidence marker, two open worklist cards and one card the worklist excludes.

    The two worklist cards and the excluded flag are written by the *production*
    Inbox writers (`runtime.subsystems.lib.inbox`), not by hand-rolled
    frontmatter, so the worklist panel is proven against the projection shape
    the product actually emits.
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
        "links:\n  supports:\n    - notes/claim-two.md\n",
        "note",
    )
    write_checked_concept(
        workspace,
        "notes/claim-two.md",
        "type: note\ntitle: Claim two\nid: note-claim-two\n",
        "note",
    )
    (workspace / "projects/study-alpha/outline.md").write_text(
        "- note-claim-one — grounds the thesis\n"
        "- note-claim-two — extends claim one\n"
        "- note-claim-three — not written yet\n",
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
        "Claim one holds. %%ev: ev-11111111 items=work-a#^p0001%%\n\n"
        "Claim two is thin. %%ev: ev-22222222 items=%%\n",
        encoding="utf-8",
    )
    state.rebuild_evidence_sets_from_markers(workspace)
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
    ambiguous = cockpit.resolve_active_project(vault)
    assert ambiguous["resolution"] == "ambiguous"
    assert [row["path"] for row in ambiguous["projects"]] == [
        PROJECT_REL,
        "projects/study-gamma/project.md",
    ]
    assert [row["title"] for row in ambiguous["projects"]] == ["Study Alpha", "Study Gamma"]


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
    assert slice_panel["members"] == 2
    assert slice_panel["edges_by_type"] == {"supports": 1}
    assert slice_panel["missing"] == 1

    draft = panels["draft"]
    assert draft["source_action"] == "project.draft.read"
    assert draft["draft_path"] == "projects/study-alpha/draft.md"
    assert draft["outline_members"] == 2
    assert draft["draft_present"] is True
    assert draft["evidence_states"] == {"complete": 1, "evidence-incomplete": 1}
    assert draft["review_required"] == 1
    # spec §1 panel 3 / §6: verification status is transient and persisted
    # nowhere readable, so the panel must not invent a line for it.
    assert all("verification" not in key for key in draft)


def test_grounds_panel_flags_thin_claims_and_unresolved_outline_ids(vault: Path) -> None:
    grounds = cockpit.assemble_deep(vault, PROJECT_REL)["grounds"]

    assert grounds["source_action"] == "project.draft.read"
    assert grounds["complete"] == 1
    assert grounds["total"] == 2
    assert [finding["finding"] for finding in grounds["findings"]] == [
        "open gap: outline id note-claim-three resolves to no checked note (line 3)",
        "thin claim: ev-22222222 has 0 grounds items",
    ]


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
    assert len(expected) == 2
    assert len(engine_api.read_attention(vault)["attention"]) == 3
    # Verbatim pass-through: order is I1's to own, and a card field the cockpit
    # has never heard of (I1's rank_factors) must survive the panel untouched.
    assert worklist["cards"] == expected


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
