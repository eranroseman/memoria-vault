from __future__ import annotations

import hashlib
from pathlib import Path

from memoria_vault.runtime import state

_EVIDENCE_ID = "ev-11111111"
_BLOCK_REF = "projects/project-alpha/draft.md#^blk-11111111"
_MARKER = (
    "%%ev: ev-11111111 type=implicit state=evidence-incomplete "
    "review=true items=%%"
)


def test_evidence_sets_schema_has_block_text_hash_binding(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(evidence_sets)")
        }

    assert "block_text_sha256" in columns


def test_rebuild_binds_new_evidence_once_and_preserves_hash_after_edit(
    tmp_path: Path,
) -> None:
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    original = "First line.\nSecond line."
    draft.write_text(f"{original} ^blk-11111111 {_MARKER}\n", encoding="utf-8")

    state.rebuild_evidence_sets_from_markers(tmp_path, run_id="compose-1")
    expected = "sha256:" + hashlib.sha256(original.encode()).hexdigest()
    [row] = state.evidence_sets(tmp_path)

    assert row["block_text_sha256"] == expected

    changed = "First line.\nChanged second line."
    draft.write_text(f"{changed} ^blk-11111111 {_MARKER}\n", encoding="utf-8")
    current = state._block_text_sha256(tmp_path, _BLOCK_REF)
    state.rebuild_evidence_sets_from_markers(tmp_path, run_id="verify-1")
    [rebuilt] = state.evidence_sets(tmp_path)

    assert current == "sha256:" + hashlib.sha256(changed.encode()).hexdigest()
    assert current != expected
    assert rebuilt["block_text_sha256"] == expected


def test_rebuild_preserves_an_existing_unbound_hash(tmp_path: Path) -> None:
    draft = tmp_path / "projects/project-alpha/draft.md"
    draft.parent.mkdir(parents=True)
    draft.write_text(f"Unbound claim. {_MARKER}\n", encoding="utf-8")

    state.rebuild_evidence_sets_from_markers(tmp_path)
    [unbound] = state.evidence_sets(tmp_path)
    assert unbound["block_text_sha256"] is None

    draft.write_text(
        f"Now anchored. ^blk-11111111 {_MARKER}\n",
        encoding="utf-8",
    )
    assert state._block_text_sha256(tmp_path, _BLOCK_REF) is not None
    state.rebuild_evidence_sets_from_markers(tmp_path)
    [rebuilt] = state.evidence_sets(tmp_path)

    assert rebuilt["id"] == _EVIDENCE_ID
    assert rebuilt["block_text_sha256"] is None
