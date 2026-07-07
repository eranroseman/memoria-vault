from __future__ import annotations

import sqlite3
from pathlib import Path

from memoria_vault.runtime import state


def test_evidence_sets_schema_lands_at_user_version_6(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 6
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'evidence_sets'"
        ).fetchone()


def test_v5_schema_accepts_additive_evidence_sets_table(tmp_path: Path) -> None:
    db = tmp_path / state.DB_REL
    db.parent.mkdir(parents=True)
    with sqlite3.connect(db) as conn:
        conn.execute("PRAGMA user_version = 5")

    with state.connect(tmp_path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 6
        assert conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'evidence_sets'"
        ).fetchone()


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
        "Single span. %%ev: ev-11111111 type=implicit state=evidence-incomplete "
        "review=true items=source-alpha#^p0001%%\n"
        "Missing span. %%ev: ev-22222222 type=single-span state=complete "
        "review=false items=source-missing#^p0001%%\n"
        "Multi hop. %%ev: ev-33333333 type=single-span state=complete "
        "review=false items=ev-11111111%%\n"
        "Implicit. %%ev: ev-44444444 type=implicit state=evidence-incomplete "
        "review=true items=%%\n"
        "Missing anchor. %%ev: ev-55555555 type=single-span state=complete "
        "review=false items=source-beta#^p0001%%\n",
        encoding="utf-8",
    )

    result = state.rebuild_evidence_sets_from_markers(vault, run_id="compose-1")
    rows = {row["id"]: row for row in state.evidence_sets(vault)}

    assert result == {"deleted": 0, "inserted": 5}
    assert rows["ev-11111111"] == {
        "id": "ev-11111111",
        "block_ref": "notes/draft.md#^blk-11111111",
        "items": ["source-alpha#^p0001"],
        "type": "single-span",
        "state": "complete",
        "review_required": False,
        "run_id": "compose-1",
    }
    assert rows["ev-22222222"]["state"] == "evidence-incomplete"
    assert rows["ev-33333333"]["type"] == "multi-hop"
    assert rows["ev-33333333"]["state"] == "complete"
    assert rows["ev-33333333"]["review_required"] is True
    assert rows["ev-44444444"]["type"] == "implicit"
    assert rows["ev-44444444"]["state"] == "evidence-incomplete"
    assert rows["ev-44444444"]["review_required"] is True
    assert rows["ev-55555555"]["state"] == "evidence-incomplete"
