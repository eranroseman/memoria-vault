from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from memoria_vault.runtime import state


def test_evidence_sets_schema_lands_at_current_user_version(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == state.SCHEMA_VERSION
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'evidence_sets'"
        ).fetchone()


def test_legacy_v5_schema_is_unsupported(tmp_path: Path) -> None:
    db = tmp_path / state.DB_REL
    db.parent.mkdir(parents=True)
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA user_version = 5")

    with pytest.raises(RuntimeError, match="unsupported Memoria DB schema version: 5"):
        state.connect(tmp_path)


def test_rebuild_evidence_sets_derives_rows_from_markers(tmp_path: Path) -> None:
    vault = tmp_path
    state.upsert_catalog_record(
        vault,
        work_id="source-alpha",
        title="Alpha Source",
        check_status="checked",
        content_path=".memoria/blobs/source-content/source-alpha.md",
    )
    state.upsert_catalog_record(
        vault,
        work_id="source-beta",
        title="Beta Source",
        check_status="checked",
        content_path=".memoria/blobs/source-content/source-beta.md",
    )
    source_text = vault / ".memoria/blobs/source-content/source-alpha.md"
    source_text.parent.mkdir(parents=True)
    source_text.write_text("Alpha source span. ^p0001\n", encoding="utf-8")
    (vault / ".memoria/blobs/source-content/source-beta.md").write_text(
        "Beta source without the requested anchor.\n",
        encoding="utf-8",
    )
    note = vault / "notes" / "draft.md"
    note.parent.mkdir(parents=True)
    note.write_text(
        "Single span. %%ev: ev-11111111 items=source-alpha#^p0001%%\n"
        "Missing span. %%ev: ev-22222222 items=source-missing#^p0001%%\n"
        "Multi hop. %%ev: ev-33333333 items=ev-11111111%%\n"
        "Implicit. %%ev: ev-44444444 items=%%\n"
        "Missing anchor. %%ev: ev-55555555 items=source-beta#^p0001%%\n",
        encoding="utf-8",
    )

    result = state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
    rows = {row["id"]: row for row in state.evidence_sets(vault)}

    assert (result["deleted"], result["inserted"]) == (0, 5)
    assert {minted["evidence_id"] for minted in result["minted"]} == {
        "ev-11111111",
        "ev-22222222",
        "ev-33333333",
        "ev-44444444",
        "ev-55555555",
    }
    assert rows["ev-11111111"] == {
        "id": "ev-11111111",
        "block_ref": "notes/draft.md#^blk-11111111",
        "items": ["source-alpha#^p0001"],
        "type": "single-span",
        "state": "complete",
        "review_required": False,
        "run_id": "compose-1",
        "block_text_sha256": None,
    }
    assert rows["ev-22222222"]["state"] == "evidence-incomplete"
    assert rows["ev-33333333"]["type"] == "multi-hop"
    assert rows["ev-33333333"]["state"] == "complete"
    assert rows["ev-33333333"]["review_required"] is True
    assert rows["ev-44444444"]["type"] == "implicit"
    assert rows["ev-44444444"]["state"] == "evidence-incomplete"
    assert rows["ev-44444444"]["review_required"] is True
    assert rows["ev-55555555"]["state"] == "evidence-incomplete"


def _seed_source(vault: Path, work_id: str, text: str) -> None:
    state.upsert_catalog_record(
        vault,
        work_id=work_id,
        title=work_id,
        check_status="checked",
        content_path=f".memoria/blobs/source-content/{work_id}.md",
    )
    path = vault / f".memoria/blobs/source-content/{work_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_marker_note(vault: Path, body: str) -> None:
    note = vault / "notes" / "draft.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(body, encoding="utf-8")


def test_cross_work_two_span_marker_derives_multi_hop_and_requires_review(
    tmp_path: Path,
) -> None:
    vault = tmp_path
    _seed_source(vault, "source-alpha", "Alpha span. ^p0001\n")
    _seed_source(vault, "source-beta", "Beta span. ^p0001\n")
    _write_marker_note(
        vault,
        "Cross-work claim. %%ev: ev-aaaa0001 items=source-alpha#^p0001|source-beta#^p0001%%\n",
    )

    state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
    [row] = state.evidence_sets(vault)

    assert row["type"] == "multi-hop"
    assert row["review_required"] is True
    assert row["state"] == "complete"


def test_code_and_span_mix_derives_multi_hop(tmp_path: Path) -> None:
    vault = tmp_path
    _seed_source(vault, "source-alpha", "Alpha span. ^p0001\n")
    digest = "0" * 64
    _write_marker_note(
        vault,
        "Mixed-kind claim. %%ev: ev-aaaa0002 "
        f"items=code-grounds:run-1:artifact-1:sha256:{digest}"
        "|source-alpha#^p0001%%\n",
    )

    state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
    [row] = state.evidence_sets(vault)

    assert row["type"] == "multi-hop"
    assert row["review_required"] is True
    assert row["state"] == "evidence-incomplete"


def test_same_work_two_span_marker_stays_multi_span(tmp_path: Path) -> None:
    vault = tmp_path
    _seed_source(vault, "source-alpha", "Alpha one. ^p0001\n\nAlpha two. ^p0002\n")
    _write_marker_note(
        vault,
        "Same-work claim. %%ev: ev-aaaa0003 items=source-alpha#^p0001|source-alpha#^p0002%%\n",
    )

    state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
    [row] = state.evidence_sets(vault)

    assert row["type"] == "multi-span"
    assert row["review_required"] is False
    assert row["state"] == "complete"


def test_pure_code_items_derive_computed(tmp_path: Path) -> None:
    vault = tmp_path
    digest = "0" * 64
    _write_marker_note(
        vault,
        "Computed claim. %%ev: ev-aaaa0004 "
        f"items=code-grounds:run-1:artifact-1:sha256:{digest}"
        f"|code-grounds:run-2:artifact-2:sha256:{digest}%%\n",
    )

    state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
    [row] = state.evidence_sets(vault)

    assert row["type"] == "computed"
    assert row["review_required"] is False
    assert row["state"] == "evidence-incomplete"


def test_derive_evidence_type_counts_duplicate_span_items() -> None:
    assert (
        state.derive_evidence_type(["source-alpha#^p0001", "source-alpha#^p0001"]) == "multi-span"
    )


def test_derive_evidence_type_rejects_invalid_item() -> None:
    with pytest.raises(ValueError, match="invalid source-span ref"):
        state.derive_evidence_type(["not-a-valid-reference"])


def test_nested_incomplete_child_flips_parent_incomplete(tmp_path: Path) -> None:
    vault = tmp_path
    _write_marker_note(
        vault,
        "Child. %%ev: ev-bbbb0001 items=source-missing#^p0001%%\n"
        "Parent. %%ev: ev-bbbb0002 items=ev-bbbb0001%%\n",
    )

    state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
    rows = {row["id"]: row for row in state.evidence_sets(vault)}

    assert rows["ev-bbbb0001"]["state"] == "evidence-incomplete"
    assert rows["ev-bbbb0002"]["state"] == "evidence-incomplete"


def test_mutually_referencing_sets_are_both_incomplete(tmp_path: Path) -> None:
    vault = tmp_path
    _write_marker_note(
        vault,
        "One. %%ev: ev-cccc0001 items=ev-cccc0002%%\nTwo. %%ev: ev-cccc0002 items=ev-cccc0001%%\n",
    )

    state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
    rows = {row["id"]: row for row in state.evidence_sets(vault)}

    assert rows["ev-cccc0001"]["state"] == "evidence-incomplete"
    assert rows["ev-cccc0002"]["state"] == "evidence-incomplete"


def test_self_referencing_set_is_incomplete(tmp_path: Path) -> None:
    vault = tmp_path
    _write_marker_note(vault, "Loop. %%ev: ev-dddd0001 items=ev-dddd0001%%\n")

    state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
    [row] = state.evidence_sets(vault)

    assert row["state"] == "evidence-incomplete"


def test_healthy_nested_chain_stays_complete(tmp_path: Path) -> None:
    vault = tmp_path
    _seed_source(vault, "source-alpha", "Alpha span. ^p0001\n")
    _write_marker_note(
        vault,
        "Leaf. %%ev: ev-eeee0001 items=source-alpha#^p0001%%\n"
        "Chain. %%ev: ev-eeee0002 items=ev-eeee0001%%\n",
    )

    state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
    rows = {row["id"]: row for row in state.evidence_sets(vault)}

    assert rows["ev-eeee0001"]["state"] == "complete"
    assert rows["ev-eeee0002"]["state"] == "complete"
    assert rows["ev-eeee0002"]["type"] == "multi-hop"


def test_evidence_item_closure_returns_direct_and_nested_leaves_in_order() -> None:
    rows_by_id = {
        "ev-aaaa0001": {
            "items": ["source-root#^p0001", "ev-aaaa0002"],
        },
        "ev-aaaa0002": {
            "items": ["source-child#^p0001", "ev-aaaa0003"],
        },
        "ev-aaaa0003": {
            "items": ["source-grandchild#^p0001"],
        },
    }

    assert state.evidence_item_closure(rows_by_id, "ev-aaaa0001") == [
        ("source-root#^p0001", ()),
        ("source-child#^p0001", ("ev-aaaa0002",)),
        ("source-grandchild#^p0001", ("ev-aaaa0002", "ev-aaaa0003")),
    ]


def test_evidence_item_closure_ignores_missing_nested_sets() -> None:
    rows_by_id = {
        "ev-aaaa0001": {
            "items": ["ev-aaaa0002", "source-root#^p0001"],
        },
    }

    assert state.evidence_item_closure(rows_by_id, "ev-aaaa0001") == [
        ("source-root#^p0001", ()),
    ]


def test_evidence_item_closure_skips_current_path_cycles() -> None:
    rows_by_id = {
        "ev-aaaa0001": {
            "items": ["source-root#^p0001", "ev-aaaa0002"],
        },
        "ev-aaaa0002": {
            "items": ["source-child#^p0001", "ev-aaaa0001", "source-after#^p0001"],
        },
    }

    assert state.evidence_item_closure(rows_by_id, "ev-aaaa0001") == [
        ("source-root#^p0001", ()),
        ("source-child#^p0001", ("ev-aaaa0002",)),
        ("source-after#^p0001", ("ev-aaaa0002",)),
    ]


def test_evidence_item_closure_keeps_shared_leaves_for_each_path() -> None:
    rows_by_id = {
        "ev-aaaa0001": {
            "items": ["ev-aaaa0002", "ev-aaaa0003"],
        },
        "ev-aaaa0002": {
            "items": ["ev-aaaa0004"],
        },
        "ev-aaaa0003": {
            "items": ["ev-aaaa0004"],
        },
        "ev-aaaa0004": {
            "items": ["source-shared#^p0001"],
        },
    }

    assert state.evidence_item_closure(rows_by_id, "ev-aaaa0001") == [
        ("source-shared#^p0001", ("ev-aaaa0002", "ev-aaaa0004")),
        ("source-shared#^p0001", ("ev-aaaa0003", "ev-aaaa0004")),
    ]
