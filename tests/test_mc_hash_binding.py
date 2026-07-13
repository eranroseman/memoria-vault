from __future__ import annotations

from pathlib import Path

from memoria_vault.runtime import state


def test_evidence_sets_schema_has_block_text_hash_binding(tmp_path: Path) -> None:
    with state.connect(tmp_path) as conn:
        columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(evidence_sets)")
        }

    assert "block_text_sha256" in columns
