"""Engine API read-scope contract tests."""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from memoria_vault.engine import api
from memoria_vault.runtime import state
from tests.helpers import init_cli_workspace, write_checked_concept, write_checked_note

pytestmark = pytest.mark.contract


@pytest.fixture
def workspace(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    return init_cli_workspace(tmp_path, capsys)


def test_engine_read_scope_filters_and_blocks_concepts(workspace: Path) -> None:
    write_checked_note(workspace, "notes/alpha.md", "Alpha")
    write_checked_note(workspace, "notes/beta.md", "Beta")

    listed = api.read_concepts(workspace, read_scope=["notes/alpha.md"])
    visible = api.read_concept(workspace, "notes/alpha.md", read_scope=["notes/"])

    assert listed["api_version"] == api.READ_API_VERSION
    assert visible["api_version"] == api.READ_API_VERSION
    assert [row["path"] for row in listed["concepts"]] == ["notes/alpha.md"]
    assert visible["path"] == "notes/alpha.md"
    with pytest.raises(FileNotFoundError, match="target not found"):
        api.read_concept(workspace, "notes/beta.md", read_scope=["notes/alpha.md"])


def test_engine_read_explore_wraps_the_pure_engine_payload(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: dict[str, object] = {}
    expected = {"topic": "spacing", "claims": [], "pipeline_counts": []}

    def fake_explore(vault: Path, topic: str, **kwargs: object) -> dict[str, object]:
        observed.update({"vault": vault, "topic": topic, **kwargs})
        return expected

    monkeypatch.setattr(api, "explore_topic", fake_explore)

    payload = api.read_explore(
        workspace, "spacing", versus="massed", project="memory", depth=2, trace=True
    )

    assert observed == {
        "vault": workspace,
        "topic": "spacing",
        "versus": "massed",
        "project": "memory",
        "depth": 2,
        "trace": True,
    }
    assert payload == {"ok": True, "api_version": api.READ_API_VERSION, "explore": expected}


def test_engine_read_work_preserves_unrecognized_topics_from_catalog_row(
    workspace: Path,
) -> None:
    state.upsert_catalog_record(
        workspace,
        work_id="legacy-work",
        title="Legacy Work",
        check_status="checked",
        csl_json={
            "id": "legacy-work",
            "memoria": {
                "topics": ["legacy-only"],
                "research_area": ["current-area"],
                "standing": "current",
            },
        },
    )

    work = api.read_work(workspace, "legacy-work")["work"]

    assert work["csl_json"] == {
        "id": "legacy-work",
        "memoria": {
            "topics": ["legacy-only"],
            "research_area": ["current-area"],
            "standing": "current",
        },
    }


def test_write_new_concept_replays_generated_path_and_id_for_same_key(
    workspace: Path,
) -> None:
    first = api.write_new_concept(
        workspace,
        "note",
        "Idempotent concept",
        body="Stable body.",
        tags=["stable"],
        extra={"mode": "claim", "claim_text": "Stable body."},
        idempotency_key="idempotent-concept",
        actor="pi",
    )
    second = api.write_new_concept(
        workspace,
        "note",
        "Idempotent concept",
        body="Stable body.",
        tags=["stable"],
        extra={"mode": "claim", "claim_text": "Stable body."},
        idempotency_key="idempotent-concept",
        actor="pi",
    )

    assert first["ok"] is second["ok"] is True
    assert second["path"] == first["path"]
    assert second["concept"]["id"] == first["concept"]["id"]
    assert not (workspace / "notes/idempotent-concept-2.md").exists()
    with state.connect(workspace) as conn:
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM operation_requests WHERE idempotency_key = ?",
                ("idempotent-concept",),
            ).fetchone()[0]
            == 1
        )


def test_write_new_concept_rejects_changed_body_for_same_key(workspace: Path) -> None:
    api.write_new_concept(
        workspace,
        "note",
        "Bound concept",
        body="Original body.",
        tags=[],
        extra={},
        idempotency_key="bound-concept",
        actor="pi",
    )

    with pytest.raises(ValueError, match="idempotency key is already bound"):
        api.write_new_concept(
            workspace,
            "note",
            "Bound concept",
            body="Changed body.",
            tags=[],
            extra={},
            idempotency_key="bound-concept",
            actor="pi",
        )


def test_write_new_concept_concurrent_exact_retries_share_generated_identity(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_request_job = state.request_job
    barrier = threading.Barrier(2)
    counter_lock = threading.Lock()
    initial_lookups = 0

    def synchronized_request_job(vault: Path, request_id: str):
        nonlocal initial_lookups
        with counter_lock:
            synchronize = initial_lookups < 2
            initial_lookups += 1
        result = original_request_job(vault, request_id)
        if synchronize:
            barrier.wait()
        return result

    monkeypatch.setattr(state, "request_job", synchronized_request_job)

    def create() -> dict[str, object]:
        return api.write_new_concept(
            workspace,
            "note",
            "Concurrent concept",
            body="Stable body.",
            tags=["stable"],
            extra={"mode": "claim", "claim_text": "Stable body."},
            idempotency_key="concurrent-concept",
            actor="pi",
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: create(), range(2)))

    assert all(result["ok"] is True for result in results)
    assert {result["path"] for result in results} == {"notes/concurrent_concept.md"}
    assert len({result["concept"]["id"] for result in results}) == 1
    with state.connect(workspace) as conn:
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM operation_requests WHERE idempotency_key = ?",
                ("concurrent-concept",),
            ).fetchone()[0]
            == 1
        )


def test_run_operation_concurrent_exact_retries_return_one_result(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_enqueue = api.enqueue_operation
    barrier = threading.Barrier(2)

    def synchronized_enqueue(*args, **kwargs):
        job = original_enqueue(*args, **kwargs)
        barrier.wait()
        return job

    monkeypatch.setattr(api, "enqueue_operation", synchronized_enqueue)
    payload = {
        "target_path": "notes/concurrent-operation.md",
        "content": "---\ntype: note\ntitle: Concurrent operation\n---\nBody.\n",
        "concept_type": "note",
    }

    def run() -> dict[str, object]:
        return api.run_operation(
            workspace,
            "create-concept",
            payload,
            idempotency_key="concurrent-operation",
            actor="agent",
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: run(), range(2)))

    assert all(result["ok"] is True for result in results)
    assert {result["result"]["status"] for result in results} == {"done"}
    with state.connect(workspace) as conn:
        assert (
            conn.execute(
                "SELECT COUNT(*) FROM operation_requests WHERE idempotency_key = ?",
                ("concurrent-operation",),
            ).fetchone()[0]
            == 1
        )


def test_engine_read_concept_refuses_tampered_checked_file(workspace: Path) -> None:
    path = workspace / "notes/alpha.md"
    write_checked_note(workspace, path.relative_to(workspace).as_posix(), "Alpha")
    path.write_text(
        "---\ntype: note\ntitle: Alpha\ntags: []\nlinks: {}\n---\nTampered.\n",
        encoding="utf-8",
    )

    with pytest.raises(PermissionError, match="not consumable until scan runs"):
        api.read_concept(workspace, "notes/alpha.md")
    with state.connect(workspace) as conn:
        row = conn.execute(
            """
            SELECT operation_id, status, schedule_id, args_json
            FROM operation_requests
            WHERE operation_id = 'observe-pi-edits'
            """
        ).fetchone()
    assert row is not None
    assert row["status"] == "pending"
    assert row["schedule_id"] == "read-guard"
    assert row["operation_id"] == "observe-pi-edits"
    assert json.loads(row["args_json"])["target_path"] == "notes/alpha.md"


def test_engine_read_scope_filters_attention_by_card_or_target(workspace: Path) -> None:
    _write_attention(workspace, "alpha", target="notes/alpha.md")
    _write_attention(workspace, "beta", target="notes/beta.md")

    listed = api.read_attention(workspace, read_scope=["notes/alpha.md"])

    assert [card["path"] for card in listed["attention"]] == ["inbox/alpha.md"]
    with pytest.raises(FileNotFoundError, match="attention projection not found"):
        api.read_attention_card(workspace, "inbox/beta.md", read_scope=["notes/alpha.md"])


def test_engine_attention_list_skips_an_unreadable_inbox_file(workspace: Path) -> None:
    """One undecodable `inbox/` file must not take the whole listing down.

    `inbox/**` is the one write target the reference actor policy grants a non-PI
    actor, so a stray binary or a mis-encoded adapter write lands on exactly the
    directory this globs. A raw `read_text` there raised `UnicodeDecodeError` out of
    `_attention_card`, so `memoria attention list` failed outright instead of
    listing the cards it can read -- and the card it stopped listing may be the one
    holding the PI's gate. `lifecycle._resolved_cards` reads through `safe_read` for
    this reason; this reads the same way.
    """
    _write_attention(workspace, "alpha", target="notes/alpha.md")
    (workspace / "inbox" / "corrupt.md").write_bytes(b"---\nprojection: \xff\xfe\n---\n")

    listed = api.read_attention(workspace)

    assert [card["path"] for card in listed["attention"]] == ["inbox/alpha.md"]


def test_engine_attention_read_api_returns_table_and_card_view_specs(workspace: Path) -> None:
    _write_attention(workspace, "alpha", target="notes/alpha.md")
    _write_attention(workspace, "beta", target="notes/beta.md")

    listed = api.read_attention(workspace, read_scope=["notes/alpha.md"])
    shown = api.read_attention_card(workspace, "inbox/alpha.md", read_scope=["notes/alpha.md"])

    assert listed["view"] == {
        "version": "view-spec.v1",
        "kind": "attention",
        "blocks": [
            {
                "id": "attention-table",
                "kind": "table",
                "title": "Attention",
                "check_status": "unchecked",
                "refs": ["inbox/alpha.md"],
                "columns": [
                    "title",
                    "kind",
                    "loudness",
                    "raised_by",
                    "created",
                    "status",
                    "target",
                ],
                "rows": [
                    {
                        "ref": "inbox/alpha.md",
                        "check_status": "unchecked",
                        # This fixture carries no `loudness:`, `raised_by:` or
                        # `created:`, so the three columns I1 A.1 added render
                        # empty rather than inventing a band, a producer or a date.
                        "cells": {
                            "title": "alpha",
                            "kind": "gap",
                            "loudness": "",
                            "raised_by": "",
                            "created": "",
                            "status": "open",
                            "target": "notes/alpha.md",
                        },
                    }
                ],
            }
        ],
    }
    card = shown["view"]["blocks"][0]
    assert card["kind"] == "card"
    assert card["refs"] == ["inbox/alpha.md"]
    assert card["body_data"] == {"kind": "untrusted_text", "text": "Review.\n"}
    assert "body" not in card


def test_engine_read_scope_filters_and_blocks_requests(workspace: Path) -> None:
    alpha = api.write_new_concept(
        workspace,
        "note",
        "Scoped Alpha",
        body="Alpha body.",
        tags=[],
        extra={},
        idempotency_key="create-alpha",
        actor="pi",
    )
    api.write_new_concept(
        workspace,
        "note",
        "Scoped Beta",
        body="Beta body.",
        tags=[],
        extra={},
        idempotency_key="create-beta",
        actor="pi",
    )

    listed = api.read_requests(workspace, read_scope=[alpha["path"]])

    assert [row["request_id"] for row in listed["requests"]] == ["create-alpha"]
    with pytest.raises(FileNotFoundError, match="request not found"):
        api.read_request(workspace, "create-beta", read_scope=[alpha["path"]])


def test_engine_read_slice_returns_project_slice_view(workspace: Path) -> None:
    write_checked_concept(
        workspace,
        "projects/project-alpha/project.md",
        "type: project\ntitle: Alpha project\ntags: []\nlinks: {}\nthesis: notes/thesis.md\n",
        concept_type="project",
    )
    write_checked_concept(
        workspace,
        "notes/thesis.md",
        "type: note\nid: 01ARZ3NDEKTSV4RRFFQ69G5FB1\ntitle: Thesis\ntags: []\nlinks: {}\n",
    )
    write_checked_concept(
        workspace,
        "notes/support.md",
        "type: note\n"
        "id: 01ARZ3NDEKTSV4RRFFQ69G5FB2\n"
        "title: Support\n"
        "tags: []\n"
        "links:\n"
        "  supports:\n"
        "    - notes/thesis.md\n",
    )
    outline = workspace / "projects/project-alpha/outline.md"
    outline.write_text(
        "- 01ARZ3NDEKTSV4RRFFQ69G5FB2 -- Support first\n"
        "- 01ARZ3NDEKTSV4RRFFQ69G5FB1 -- Thesis second\n",
        encoding="utf-8",
    )

    result = api.read_slice(workspace, "project-alpha")

    assert result["api_version"] == api.READ_API_VERSION
    assert [member["path"] for member in result["slice"]["members"]] == [
        "notes/support.md",
        "notes/thesis.md",
    ]
    block = result["view"]["blocks"][0]
    assert block["kind"] == "table"
    assert block["refs"] == ["notes/support.md", "notes/thesis.md"]
    assert block["rows"][0]["cells"]["reasoning"] == "Support first"


def test_engine_compose_and_read_draft_returns_project_draft_view(workspace: Path) -> None:
    write_checked_concept(
        workspace,
        "projects/project-alpha/project.md",
        "type: project\ntitle: Alpha project\ntags: []\nlinks: {}\nthesis: notes/thesis.md\n",
        concept_type="project",
    )
    write_checked_concept(
        workspace,
        "notes/thesis.md",
        "type: note\nid: 01ARZ3NDEKTSV4RRFFQ69G5FB1\ntitle: Thesis\ntags: []\nlinks: {}\n",
    )
    outline = workspace / "projects/project-alpha/outline.md"
    outline.write_text("- 01ARZ3NDEKTSV4RRFFQ69G5FB1 -- Draft thesis\n", encoding="utf-8")

    composed = api.compose_draft(
        workspace,
        "project-alpha",
        token_budget=400,
        idempotency_key="compose-draft",
        actor="pi",
    )
    verified = api.verify_draft(
        workspace,
        "project-alpha",
        idempotency_key="verify-draft",
        actor="pi",
    )
    readback = api.read_draft(workspace, "project-alpha")

    assert composed["ok"] is True
    assert composed["result"]["draft_path"] == "projects/project-alpha/draft.md"
    assert composed["result"]["evidence_set_count"] == 1
    assert verified["ok"] is True
    assert verified["result"]["ready"] is False
    assert readback["api_version"] == api.READ_API_VERSION
    assert "%%ev:" in readback["draft"]["content"]
    assert readback["view"]["kind"] == "project-draft"
    assert readback["view"]["blocks"][0]["rows"][0]["cells"]["state"] == "evidence-incomplete"


def _write_attention(workspace: Path, name: str, *, target: str) -> None:
    path = workspace / "inbox" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "---",
                "projection: attention",
                f"title: {name}",
                "attention_kind: gap",
                "attention_status: open",
                "routing_class: ask",
                f"target: {target}",
                "---",
                "Review.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def test_journal_paths_sweeps_every_path_field_a_move_reverted_row_carries() -> None:
    """Read-scope filtering must see a move's destination and its rewritten linkers.

    `_journal_paths` is a pure function of the payload, so this needs no vault: it pins
    the two keys NID-B.6 added to the sweep. Without `new_path` a `move-reverted` row
    escapes a scope restriction via its destination; without the `outputs` list key it
    escapes via the linkers it rewrote. Both directions loosen scope, which is why they
    are asserted rather than left to the scope-walk fixtures.
    """
    payload = {
        "event": "move-reverted",
        "target_id": "notes/source.md",
        "old_path": "notes/source.md",
        "new_path": "notes/destination.md",
        "outputs": ["notes/linker-one.md", "notes/linker-two.md"],
    }

    assert set(api._journal_paths(payload)) == {
        "notes/source.md",
        "notes/destination.md",
        "notes/linker-one.md",
        "notes/linker-two.md",
    }


def _canvas_fork_project(workspace: Path) -> None:
    """A checked project whose live render carries two edges into the thesis."""
    write_checked_concept(
        workspace,
        "projects/project-alpha/project.md",
        "type: project\ntitle: Alpha project\ntags: []\nlinks: {}\nthesis: notes/thesis.md\n",
        concept_type="project",
    )
    write_checked_concept(
        workspace,
        "notes/thesis.md",
        "type: note\ntitle: Thesis\ntags: []\nlinks: {}\n",
    )
    write_checked_concept(
        workspace,
        "notes/support.md",
        "type: note\ntitle: Support\ntags: []\nlinks:\n  supports:\n    - notes/thesis.md\n",
    )
    write_checked_concept(
        workspace,
        "notes/extra.md",
        "type: note\ntitle: Extra\ntags: []\nlinks:\n  extends:\n    - notes/thesis.md\n",
    )
    # A second generated-only edge, so `added` and `removed` have different
    # sizes: at 1 and 1 the two are indistinguishable and `removed_count`
    # computed from the wrong direction reads correct.
    write_checked_concept(
        workspace,
        "notes/rebut.md",
        "type: note\ntitle: Rebut\ntags: []\nlinks:\n  rebuttal:\n    - notes/thesis.md\n",
    )


def test_engine_read_canvas_forks_reports_edge_diff(workspace: Path) -> None:
    """One pass over every arm of the diff: added, removed, unresolved, unreadable.

    The `removed` arm matters on its own: with `removed_count` pinned at 0 the
    reported `diff_count` cannot tell `len(added)` from `len(added) +
    len(removed)`, so the divergence badge would read low forever on a fork
    that only deletes.
    """
    _canvas_fork_project(workspace)
    scratch_dir = workspace / "projects/project-alpha"
    scratch_dir.mkdir(parents=True, exist_ok=True)
    (scratch_dir / "scratch-manual.canvas").write_text(
        json.dumps(
            {
                "nodes": [
                    {"id": "a", "type": "file", "file": "notes/support.md"},
                    {"id": "b", "type": "file", "file": "notes/thesis.md"},
                    {"id": "t", "type": "text", "text": "a sticky note"},
                    # Not a `file` node, but carrying a `file` key: a
                    # hand-edited canvas is untrusted input, and a member map
                    # keyed on the key alone would adopt this as notes/extra.md
                    # and silently resolve the edge below.
                    {"id": "g", "type": "group", "file": "notes/extra.md"},
                ],
                "edges": [
                    # Padding and case are the PI's, not the projector's: both
                    # normalize, so this one matches the generated edge and is
                    # neither added nor removed.
                    {"id": "e1", "fromNode": "a", "toNode": "b", "label": " Supports "},
                    {"id": "e2", "fromNode": "a", "toNode": "b", "label": "contradicts"},
                    {"id": "e3", "fromNode": "a", "toNode": "b"},
                    {"id": "e4", "fromNode": "a", "toNode": "t", "label": "supports"},
                    {"id": "e5", "fromNode": "g", "toNode": "b", "label": "extends"},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (scratch_dir / "scratch-broken.canvas").write_text("{not json", encoding="utf-8")
    (scratch_dir / "scratch-list.canvas").write_text("[]\n", encoding="utf-8")
    # A stale on-disk render must not become the comparison basis: the fork is
    # diffed against the graph as it is now, which is what makes the badge a
    # staleness signal rather than a copy check.
    (scratch_dir / "argument.canvas").write_text(
        json.dumps({"nodes": [], "edges": []}) + "\n", encoding="utf-8"
    )

    result = api.read_canvas_forks(workspace, "project-alpha")

    assert result["ok"] is True
    assert result["api_version"] == api.READ_API_VERSION
    status = result["canvas_forks"]
    assert status["project_path"] == "projects/project-alpha/project.md"
    assert status["canvas_path"] == "projects/project-alpha/argument.canvas"
    assert [fork["path"] for fork in status["forks"]] == [
        "projects/project-alpha/scratch-broken.canvas",
        "projects/project-alpha/scratch-list.canvas",
        "projects/project-alpha/scratch-manual.canvas",
    ]
    assert status["forks"][0] == {
        "path": "projects/project-alpha/scratch-broken.canvas",
        "error": "unreadable scratch canvas",
    }
    assert status["forks"][1] == {
        "path": "projects/project-alpha/scratch-list.canvas",
        "error": "unreadable scratch canvas",
    }
    assert status["forks"][2] == {
        "path": "projects/project-alpha/scratch-manual.canvas",
        "added": [
            {
                "source_note_path": "notes/support.md",
                "link_type": "contradicts",
                "target_path": "notes/thesis.md",
            }
        ],
        # notes/extra.md --extends--> and notes/rebut.md --rebuttal--> are both
        # in the live render and neither is on the fork. Two removed against one
        # added, so the two arms of `diff_count` cannot be swapped unnoticed —
        # and `e5` is not one of them: the group node never became a member, so
        # its edge is unresolved rather than a third graduated relation.
        "removed_count": 2,
        "diff_count": 3,
        "unresolved": [
            {"edge_id": "e3", "reason": "unknown relation label"},
            {"edge_id": "e4", "reason": "edge endpoint is not a file node"},
            {"edge_id": "e5", "reason": "edge endpoint is not a file node"},
        ],
    }


def test_engine_read_canvas_forks_reports_an_empty_list_when_nothing_is_forked(
    workspace: Path,
) -> None:
    _canvas_fork_project(workspace)

    status = api.read_canvas_forks(workspace, "project-alpha")["canvas_forks"]

    assert status["forks"] == []


def test_engine_read_canvas_forks_respects_read_scope(workspace: Path) -> None:
    _canvas_fork_project(workspace)

    assert api.read_canvas_forks(workspace, "project-alpha", read_scope=["projects"])["ok"]
    with pytest.raises(FileNotFoundError):
        api.read_canvas_forks(workspace, "project-alpha", read_scope=["notes"])
