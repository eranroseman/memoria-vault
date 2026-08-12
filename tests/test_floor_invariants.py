from __future__ import annotations

import contextlib
import sqlite3
from pathlib import Path

import pytest

from tests.floor_lib import assert_invariants, read_only_guard, seed_vault, vault_digest

pytestmark = pytest.mark.floor


def test_invariants_pass_on_seed(tmp_path: Path) -> None:
    vault, _ = seed_vault(tmp_path)
    assert_invariants(vault)


def test_redaction_replaces_known_tokens() -> None:
    # Non-vacuous by construction: an identity _redact fails this. Makes the
    # "must be REDACTED" constraint falsifiable (the digest-level assertions
    # cannot, since vault_digest hashes bodies).
    from tests.floor_lib import _redact

    ulid = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    ts = "2026-07-13T12:00:00Z"
    out = _redact(f"id {ulid} at {ts}")
    assert ulid not in out and ts not in out
    assert "<ULID>" in out and "<TS>" in out


def test_digest_is_stable_and_redacted(tmp_path: Path) -> None:
    vault, _ = seed_vault(tmp_path)
    d1, d2 = vault_digest(vault), vault_digest(vault)
    assert d1 == d2
    text = str(d1)
    # No raw ULIDs or ISO timestamps may survive redaction.
    import re

    assert not re.search(r"[0-9A-HJKMNP-TV-Z]{26}", text)
    assert not re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", text)


def test_golden_drift_failure_prints_the_diff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A drifted golden must say *what* moved, not only that something did.

    #1691: three CI drifts, on three operations, none reproducible; each
    investigation had to start by reproducing because the message carried no
    content (one of them burned 22 gate runs). The drift below is produced —
    a real file written into a real seeded vault, re-digested through the
    real `vault_digest` — rather than hand-written, so an `assert_golden`
    that dropped the diff again cannot pass this.
    """
    from tests import floor_lib

    vault, _ = seed_vault(tmp_path)
    monkeypatch.setattr(floor_lib, "GOLDENS_DIR", tmp_path / "goldens")
    monkeypatch.setenv("MEMORIA_FLOOR_UPDATE_GOLDENS", "1")
    monkeypatch.delenv("CI", raising=False)
    floor_lib.assert_golden("drift-probe", vault_digest(vault))
    monkeypatch.delenv("MEMORIA_FLOOR_UPDATE_GOLDENS")

    (vault / "notes/floor-drift-probe.md").write_text("drifted\n", encoding="utf-8")
    with pytest.raises(AssertionError) as excinfo:
        floor_lib.assert_golden("drift-probe", vault_digest(vault))

    message = str(excinfo.value)
    assert "golden drift for drift-probe" in message
    added = [
        line for line in message.splitlines() if line.startswith("+") and not line.startswith("+++")
    ]
    assert any("notes/floor-drift-probe.md" in line for line in added), message
    assert "--- golden/drift-probe.json" in message, message


def test_foreign_key_breakage_is_detected(tmp_path: Path) -> None:
    vault, _ = seed_vault(tmp_path)
    db = vault / ".memoria/memoria.sqlite"
    with contextlib.closing(sqlite3.connect(db)) as conn:
        conn.execute("PRAGMA foreign_keys=OFF")
        # Orphan a child row: point a materialized-payload mirror at a
        # nonexistent output (schema.sql defines the FK on
        # materialization_payloads.output_id -> outputs.output_id). Since v16
        # the Concept graph is FK-backed too, so the runtime cannot produce an
        # orphan there — breaking it needs this deliberate foreign_keys=OFF
        # write, which is exactly what the invariant battery must catch.
        conn.execute(
            "UPDATE materialization_payloads SET output_id='floor-missing' "
            "WHERE rowid = (SELECT rowid FROM materialization_payloads LIMIT 1)"
        )
        conn.commit()
    with pytest.raises(AssertionError, match="foreign_key_check"):
        assert_invariants(vault)


def test_untracked_file_edit_is_detected(tmp_path: Path) -> None:
    vault, _ = seed_vault(tmp_path)
    # note_claim is created through the worker/queue path (enqueue_operation +
    # run_next_job), which never appends to system/logs/audit.jsonl -- that
    # log is only written by the policy-engine write path
    # through PolicyEngine.complete_write in memoria_vault.runtime.policy.engine, so
    # vault_hash_drift (which walks audit.jsonl) has nothing to compare an
    # edited note_claim against and never fires. bibliography.bib, by
    # contrast, is a tracked generated projection: check_tracked_projections
    # regenerates it and diffs byte-for-byte against the on-disk file, so an
    # out-of-band edit is always caught regardless of any audit trail.
    target = vault / "bibliography.bib"
    target.write_text(target.read_text(encoding="utf-8") + "\ndrift\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="tracked projections drift"):
        assert_invariants(vault)


def test_read_only_guard_catches_writes(tmp_path: Path) -> None:
    vault, _ = seed_vault(tmp_path)
    with pytest.raises(AssertionError):
        with read_only_guard(vault):
            (vault / "notes/sneaky.md").write_text("x", encoding="utf-8")
