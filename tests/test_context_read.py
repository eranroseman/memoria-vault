"""U2 spec §1 panel 6 / slice 4b: the situated-context bundle (context.read).

The bundle is composed from shipped reads only. Every branch below is held to
a producer state a vault really reaches: two active projects (no single
slice), an archived project (the active predicate), a project whose outline
the caller's own `read_scope` hides (the named-unavailable slice), and more
steering tokens than the panel shows (the honest total beside the cap).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.cli import main
from memoria_vault.engine import api as engine_api
from tests.helpers import init_cli_workspace, write_checked_concept

OPEN_CARD = "inbox/open-gap.md"
RESOLVED_CARD = "inbox/resolved-gap.md"

ALPHA = "projects/project-alpha/project.md"


def _project(vault: Path, name: str, *, archived: bool = False) -> None:
    extra = "archived: true\n" if archived else ""
    write_checked_concept(
        vault,
        f"projects/{name}/project.md",
        f"type: project\ncheck_status: checked\ntitle: {name}\n{extra}",
        "project",
    )


def _attention_card(vault: Path, rel: str, *, status: str) -> None:
    path = vault / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\nprojection: attention\ntitle: A gap\nattention_kind: gap\n"
        f"attention_status: {status}\nrouting_class: ask\nloudness: notice\n"
        f"target: {ALPHA}\n---\nGap body.\n",
        encoding="utf-8",
    )


def test_read_context_reports_active_projects_slice_counts_and_open_attention(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    _project(vault, "project-alpha")
    # The active predicate, exercised: archived is True -> not active.
    _project(vault, "project-old", archived=True)
    write_checked_concept(
        vault,
        "notes/note-01.md",
        "type: note\ncheck_status: checked\ntitle: Note 1\nid: note-id-01\n",
    )
    (vault / "projects/project-alpha/outline.md").write_text(
        "- note-id-01 — first\n", encoding="utf-8"
    )
    (vault / "steering.md").write_text(
        "## Watch for\n\n- digital biomarkers\n- adherence outcomes\n", encoding="utf-8"
    )
    _attention_card(vault, OPEN_CARD, status="open")
    _attention_card(vault, RESOLVED_CARD, status="resolved")

    payload = engine_api.read_context(vault)

    assert payload["ok"] is True
    assert payload["api_version"] == "engine-read-api.v1"
    context = payload["context"]
    assert context["active_projects"] == [{"path": ALPHA, "title": "project-alpha"}]
    assert context["slice_counts"] == {
        "project_path": ALPHA,
        "members": 1,
        "edges": 0,
        "missing": 0,
    }
    # Two cards, one resolved: `attention_open` is the open count, not the
    # queue size, so dropping the status filter is visible.
    assert context["attention_open"] == 1
    assert {"biomarkers", "adherence"} <= set(context["steering_tokens"])
    assert context["steering_token_count"] == len(context["steering_tokens"])


def test_read_context_with_multiple_active_projects_reports_no_single_slice(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    _project(vault, "project-alpha")
    _project(vault, "project-beta")

    context = engine_api.read_context(vault)["context"]

    assert [row["path"] for row in context["active_projects"]] == [
        ALPHA,
        "projects/project-beta/project.md",
    ]
    assert context["slice_counts"] is None


def test_read_context_caps_the_steering_list_and_reports_the_honest_total(
    tmp_path: Path,
) -> None:
    """The cap is a display bound, not a count: a vault with more effective
    tokens than the panel shows still reports how many there really are."""
    vault = tmp_path
    _project(vault, "project-alpha")
    watch = "\n".join(f"- steeringtoken{index:03d}" for index in range(30))
    (vault / "steering.md").write_text(f"## Watch for\n\n{watch}\n", encoding="utf-8")

    context = engine_api.read_context(vault)["context"]

    assert len(context["steering_tokens"]) == engine_api.CONTEXT_STEERING_TOP_N
    assert context["steering_token_count"] > engine_api.CONTEXT_STEERING_TOP_N
    assert context["steering_tokens"] == sorted(context["steering_tokens"])


def test_read_context_withholds_steering_tokens_from_a_bounded_read(tmp_path: Path) -> None:
    """Steering is a whole-vault derivation with no scoped form, so a bounded
    reader is told it is withheld rather than handed it — or handed an empty
    list, which would read as `this vault has no steering`."""
    vault = tmp_path
    _project(vault, "project-alpha")
    (vault / "steering.md").write_text("## Watch for\n\n- digital biomarkers\n", encoding="utf-8")

    unscoped = engine_api.read_context(vault)["context"]
    scoped = engine_api.read_context(vault, read_scope=["projects"])["context"]

    assert "biomarkers" in unscoped["steering_tokens"]
    assert "steering_tokens" not in scoped
    assert "steering_token_count" not in scoped
    assert scoped["steering_unavailable"] == engine_api.CONTEXT_STEERING_WITHHELD


def test_read_context_names_a_slice_its_own_read_scope_hides(tmp_path: Path) -> None:
    """`read_slice` gates on the outline, so a scope can admit the project file
    and hide the outline beside it. The bundle names that refusal instead of
    reporting zero members as though the slice were empty."""
    vault = tmp_path
    _project(vault, "project-alpha")
    (vault / "projects/project-alpha/outline.md").write_text("", encoding="utf-8")

    context = engine_api.read_context(vault, read_scope=[ALPHA])["context"]

    assert [row["path"] for row in context["active_projects"]] == [ALPHA]
    assert context["slice_counts"] == {"unavailable": f"project slice not found: {ALPHA}"}


def test_read_context_scopes_the_active_project_list_too(tmp_path: Path) -> None:
    vault = tmp_path
    _project(vault, "project-alpha")
    _project(vault, "project-beta")

    context = engine_api.read_context(vault, read_scope=["projects/project-beta"])["context"]

    assert [row["path"] for row in context["active_projects"]] == [
        "projects/project-beta/project.md"
    ]


def test_cli_context_round_trips_the_bundle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)

    rc = main(["context", "--workspace", str(workspace), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert payload["ok"] is True
    assert payload["context"]["active_projects"] == []
    assert payload["context"]["slice_counts"] is None
