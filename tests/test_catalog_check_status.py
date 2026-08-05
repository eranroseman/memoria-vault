"""One writer for a catalog Work's verdict: state.set_catalog_check_status."""

from __future__ import annotations

from pathlib import Path

import pytest

from memoria_vault.runtime import state
from tests.helpers import worker_workspace

pytestmark = pytest.mark.runtime


def _seed_work(vault: Path, work_id: str) -> None:
    state.upsert_catalog_record(
        vault,
        work_id=work_id,
        title="Quarantine Target",
        check_status="checked",
    )
    state.replace_indexed_passages(
        vault,
        [
            {
                "origin": "file",
                "text": "a passage from the work",
                "path": f"fulltexts/{work_id}.md",
                "work_id": work_id,
                "check_status": "checked",
            }
        ],
    )


def test_quarantine_updates_catalog_verdict_and_passages(tmp_path: Path) -> None:
    vault = worker_workspace(tmp_path)
    _seed_work(vault, "w-quarantine")

    state.set_catalog_check_status(vault, "w-quarantine", "quarantined")

    row = state.catalog_source(vault, "w-quarantine")
    assert row is not None and row["check_status"] == "quarantined"
    assert state.concept_check_status(vault, "w-quarantine") == "quarantined"
    with state.connect(vault) as conn:
        passage_statuses = {
            str(r["check_status"])
            for r in conn.execute(
                "SELECT check_status FROM passages WHERE work_id = ?",
                ("w-quarantine",),
            )
        }
    assert passage_statuses == {"quarantined"}


def test_recheck_clears_stale_flag_and_consequence(tmp_path: Path) -> None:
    vault = worker_workspace(tmp_path)
    _seed_work(vault, "w-recheck")
    state.set_catalog_check_status(vault, "w-recheck", "quarantined")
    state.set_concept_flag(vault, "catalog/sources/w-recheck", "stale", reason="test seeded stale")

    state.set_catalog_check_status(vault, "w-recheck", "checked")

    assert state.concept_check_status(vault, "w-recheck") == "checked"
    with state.connect(vault) as conn:
        target = state.resolve_concept_id(conn, "w-recheck")
        flags = [
            str(r["flag"])
            for r in conn.execute("SELECT flag FROM concept_flags WHERE concept_id = ?", (target,))
        ]
        consequence = conn.execute(
            "SELECT consequence FROM concept_verdicts WHERE concept_id = ?", (target,)
        ).fetchone()
    assert "stale" not in flags
    assert consequence is not None and str(consequence["consequence"] or "") == ""


def test_invalid_status_is_refused(tmp_path: Path) -> None:
    vault = worker_workspace(tmp_path)
    _seed_work(vault, "w-invalid")

    with pytest.raises(ValueError, match="invalid check_status"):
        state.set_catalog_check_status(vault, "w-invalid", "bogus")
