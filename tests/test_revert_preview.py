"""U2 spec §3: trace.revert_preview — read-only preview of cascade-rollback.

The datum is a journal `event_id` end-to-end (U2 plan scoped-trace amendment
§2): the ref `cockpit.trace_panel` puts on every line. The preview resolves
that event, then the derived output record it wrote, and names either missing
fact rather than guessing.

The mutates-nothing claim is a negative one, so it is asserted as an absence
over every surface a write would move — working-tree bytes, the staging and
quarantine trees, every SQLite row count, the journal head, `git status` and
`git rev-parse HEAD` — and then made non-degenerate by running the real
`cascade_rollback` over the same target in the same vault and showing it moves
exactly those surfaces. The same run proves the preview's three descendant
lists are the rollback's own outcome, not a second decision procedure.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from memoria_vault.cli import main
from memoria_vault.engine import api as engine_api
from memoria_vault.runtime import backup, state
from memoria_vault.runtime.capture import capture_source as _capture_source
from memoria_vault.runtime.integrity import cascade_rollback as _cascade_rollback
from memoria_vault.runtime.integrity import revert_preview
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.trusted_writer import (
    commit_writer_changes as _commit_writer_changes,
)
from memoria_vault.runtime.trusted_writer import (
    mark_checked as _mark_checked,
)
from memoria_vault.runtime.trusted_writer import observe_pi_edit
from memoria_vault.runtime.trusted_writer import (
    promote_checked as _promote_checked,
)
from memoria_vault.runtime.trusted_writer import (
    stage_concept as _stage_concept,
)
from tests.helpers import call_with_context, copy_memoria_dirs, git, init_git

pytestmark = pytest.mark.runtime

TARGET = "notes/root-claim.md"
CHILD = "notes/machine-child.md"
GONE = "notes/machine-deleted.md"
PI_NOTE = "notes/pi-downstream.md"


def _note(title: str) -> str:
    return f"---\ntype: note\ntitle: {title}\ntags: []\nlinks: {{}}\n---\n{title} body.\n"


def _write(vault: Path, rel: str, title: str, inputs: list[str] | None = None) -> str:
    call_with_context(
        _stage_concept, vault, rel, _note(title), inputs=inputs or [], machine="writer"
    )
    call_with_context(_promote_checked, vault, rel, machine="writer")
    return call_with_context(_commit_writer_changes, vault, f"write {rel}", [rel], machine="writer")


def _vault(tmp_path: Path) -> tuple[Path, str]:
    """One root claim with all three descendant arms the rollback loop decides:
    a live machine child (quarantine), a machine child whose file was removed
    (skip), and a PI-authored downstream note (flag)."""
    vault = tmp_path
    copy_memoria_dirs(vault, "schemas", "config")
    init_git(vault, "preview@example.invalid", "Preview")
    root_commit = _write(vault, TARGET, "Root claim")
    _write(vault, CHILD, "Machine child", inputs=[TARGET])
    _write(vault, GONE, "Machine deleted", inputs=[TARGET])
    (vault / GONE).unlink()

    pi_path = vault / PI_NOTE
    pi_path.parent.mkdir(parents=True, exist_ok=True)
    pi_path.write_text(_note("PI downstream"), encoding="utf-8")
    prior_sha = sha256_file(pi_path)
    pi_path.write_text(_note("PI downstream") + "\nPI edit.\n", encoding="utf-8")
    observe_pi_edit(
        vault,
        PI_NOTE,
        prior_sha,
        inputs=[{"id": TARGET, "sha256": sha256_file(vault / TARGET)}],
        machine="pi-machine",
    )
    call_with_context(_mark_checked, vault, PI_NOTE, machine="pi-machine")
    call_with_context(
        _commit_writer_changes, vault, "observe pi note", [PI_NOTE], machine="pi-machine"
    )
    return vault, root_commit


def _event_id(vault: Path, output_id: str, *, event_type: str = "derived") -> int:
    """The newest journal event of ``event_type`` naming ``output_id`` — the same
    id `journal.list` (and so the cockpit trace panel) puts on the line."""
    for event in engine_api.read_journal(vault, limit=500)["events"]:
        if event["event_type"] == event_type and event["payload"].get("output_id") == output_id:
            return int(event["event_id"])
    raise AssertionError(f"no {event_type} event for {output_id}")


def _event_type_id(vault: Path, event_type: str) -> int:
    """The newest journal event of a type, whatever it names."""
    for event in engine_api.read_journal(vault, limit=500)["events"]:
        if event["event_type"] == event_type:
            return int(event["event_id"])
    raise AssertionError(f"no {event_type} event")


def _check_fired_payload(vault: Path, target_id: str) -> dict[str, Any]:
    """The newest `check-fired` event naming ``target_id`` (its own key, not
    ``output_id``) — the record promotion journals *after* the OKF `verified`
    stamp, so its `output_sha256` is computed from the exact bytes written to
    disk (`trusted_writer._write_checked`)."""
    for event in engine_api.read_journal(vault, limit=500)["events"]:
        if event["event_type"] == "check-fired" and event["payload"].get("target_id") == target_id:
            return event["payload"]
    raise AssertionError(f"no check-fired event for {target_id}")


def _surfaces(vault: Path) -> dict[str, Any]:
    """Every surface a write moves: file bytes (staging and quarantine trees
    included), every SQLite row count, the journal head, and both git views."""
    files = {}
    for path in sorted(vault.rglob("*")):
        rel = path.relative_to(vault).as_posix()
        if not path.is_file() or rel.startswith(".git/") or rel.endswith(".sqlite-shm"):
            continue
        if rel.endswith((".sqlite", ".sqlite-wal")):
            continue  # WAL checkpointing rewrites these on a pure read
        files[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    with contextlib.closing(sqlite3.connect(state.db_path(vault))) as conn:
        tables = sorted(
            str(row[0])
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            if not str(row[0]).startswith("sqlite_")
        )
        rows = {
            table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables
        }
    return {
        "files": files,
        "rows": rows,
        "journal_head": state.journal_head(vault),
        "status": git(vault, "status", "--porcelain"),
        "head": git(vault, "rev-parse", "HEAD"),
    }


def test_revert_preview_mutates_nothing_that_cascade_rollback_moves(tmp_path: Path) -> None:
    """The negative claim, asserted as an absence and then made non-degenerate:
    the very same vault, target and operation *do* move these surfaces when the
    real rollback runs, so an unchanged digest is evidence of read-only-ness
    rather than of a fixture with nothing to write."""
    vault, _ = _vault(tmp_path)
    event_id = _event_id(vault, TARGET)

    before = _surfaces(vault)
    preview = revert_preview(vault, event_id)
    engine_api.read_revert_preview(vault, event_id)
    assert _surfaces(vault) == before
    assert preview["computable"] is True

    rollback = call_with_context(
        _cascade_rollback,
        vault,
        TARGET,
        reason="prove the preview had something to not do",
        machine="integrity-machine",
    )
    after = _surfaces(vault)

    # Non-degeneracy: every surface the preview left alone did move here.
    assert after["files"] != before["files"]
    assert after["rows"] != before["rows"]
    assert after["journal_head"] != before["journal_head"]
    assert after["head"] != before["head"]
    assert after["status"] != before["status"]
    # And the preview predicted that outcome rather than deciding it again.
    assert preview["would_quarantine"] == rollback["reverted"] == [CHILD]
    assert preview["would_flag"] == rollback["needs_human"] == [PI_NOTE]
    assert preview["would_skip"] == rollback["skipped"] == [GONE]


def test_revert_preview_reports_the_shipped_records_for_a_derived_event(tmp_path: Path) -> None:
    """A `derived` event's `output_sha256` is the *staged* bytes, recorded
    before promotion. Promotion (`_write_checked`) appends an OKF `verified`
    confirmation to the frontmatter after staging, so staged and shipped bytes
    now legitimately diverge — this was already incidental before that (body
    neutralization can also run again at promotion), just never provably so.

    The record that *is* guaranteed to match the shipped file's current bytes
    is the `check-fired` event promotion journals: its `output_sha256` is
    computed from the exact payload `_write_checked` then writes to disk.
    `revert_preview` itself refuses to compute a preview keyed on a
    `check-fired` id (it names no `output_id`, only `target_id` — see
    `test_revert_preview_names_an_event_that_derived_no_output`), so that
    record is read directly off the journal here instead."""
    vault, root_commit = _vault(tmp_path)
    event_id = _event_id(vault, TARGET)

    preview = revert_preview(vault, event_id)

    assert preview["computable"] is True
    assert preview["event_id"] == event_id
    assert preview["target"] == TARGET
    event = preview["event"]
    assert event["event_type"] == "derived"
    assert event["output_id"] == TARGET
    assert event["staging_id"] == f".memoria/staging/{TARGET}"
    assert event["inputs"] == []
    assert event["timestamp"]

    shipped_sha256 = sha256_file(vault / TARGET)
    checked = _check_fired_payload(vault, TARGET)
    assert checked["output_sha256"] == shipped_sha256
    # The derived event's own hash is the pre-stamp, staging-time snapshot —
    # a true fact about that event, no longer a proxy for the shipped file.
    assert event["output_sha256"] != shipped_sha256
    assert preview["outputs"] == {"materialized_commit": root_commit}
    assert preview["owning_operation"] == {
        "operation": "cascade-rollback",
        "signature": "cascade_rollback(vault, target_id, *, context, reason, include_target)",
    }
    assert preview["backup"] == {
        "workspace_backup_exists": False,
        "note": "restore is whole-workspace: restoring the backup reverts everything since it",
    }


def test_revert_preview_carries_the_derivation_inputs_of_a_descended_event(
    tmp_path: Path,
) -> None:
    """`inputs` is `[]` only for a root derivation. A derived child's event names
    its parent, and the preview reports that list rather than the empty default."""
    vault, _ = _vault(tmp_path)

    preview = revert_preview(vault, _event_id(vault, CHILD))

    assert preview["target"] == CHILD
    assert [row["id"] for row in preview["event"]["inputs"]] == [TARGET]
    # A leaf has no descendants; all three splits are empty for the right reason.
    assert preview["would_quarantine"] == []
    assert preview["would_flag"] == []
    assert preview["would_skip"] == []


def test_revert_preview_reports_an_existing_workspace_backup(tmp_path: Path) -> None:
    """`workspace_backup_exists` is the one preview field the vault's own history
    flips, so both sides are fixtured instead of defaulting to False forever."""
    vault, _ = _vault(tmp_path)
    event_id = _event_id(vault, TARGET)
    assert revert_preview(vault, event_id)["backup"]["workspace_backup_exists"] is False

    created = backup.create_backup(
        vault, tmp_path.parent / "preview-backup", actor="pi", machine="backup-test"
    )

    assert created["ok"] is True
    assert revert_preview(vault, event_id)["backup"]["workspace_backup_exists"] is True


def test_revert_preview_names_a_journal_event_that_is_not_there(tmp_path: Path) -> None:
    vault, _ = _vault(tmp_path)

    preview = revert_preview(vault, 9_999)

    assert preview == {
        "computable": False,
        "event_id": 9_999,
        "target": "",
        "missing": "journal event 9999",
    }


def test_revert_preview_does_not_create_a_database_to_find_nothing_in(tmp_path: Path) -> None:
    """A vault with no state database has no journal, and asking about one must
    not be the thing that creates the file — `state.connect` initializes the
    schema, which would make this read a write."""
    assert not state.db_path(tmp_path).is_file()

    preview = revert_preview(tmp_path, 1)

    assert preview["computable"] is False
    assert preview["missing"] == "journal event 1"
    assert not state.db_path(tmp_path).is_file()


def test_revert_preview_names_an_event_that_derived_no_output(tmp_path: Path) -> None:
    """`check-fired` carries `target_id` and no `output_id`: the trace panel
    refuses to offer it as a ref, and the preview refuses to invent one. The
    fixture uses a `check-fired` row the promotion itself wrote, so the branch
    is held to a producer state the product really reaches."""
    vault, _ = _vault(tmp_path)
    event_id = _event_type_id(vault, "check-fired")

    preview = revert_preview(vault, event_id)

    assert preview == {
        "computable": False,
        "event_id": event_id,
        "target": "",
        "missing": f"derived output on journal event {event_id}",
    }


def test_revert_preview_names_the_missing_output_record_of_a_db_store_derivation(
    tmp_path: Path,
) -> None:
    """The one derived event that writes no `outputs` row: quarantining a catalog
    source journals `store: "db"` under a `catalog/sources/` output id, and
    `state.record_file_output` never runs for it. There is no file output record
    to preview, and the preview names which record is missing rather than
    reporting a blank commit as though it had one."""
    vault, _ = _vault(tmp_path)
    call_with_context(
        _capture_source,
        vault,
        "source-alpha",
        "Alpha Source",
        "A fixture source.",
        "Alpha content about framing, methods, outcomes, gaps, and impact.",
        machine="capture-machine",
    )
    call_with_context(
        _cascade_rollback,
        vault,
        "catalog/sources/source-alpha",
        reason="poisoned source",
        include_target=True,
        machine="integrity-machine",
    )
    event_id = _event_id(vault, "catalog/sources/source-alpha")

    preview = revert_preview(vault, event_id)

    assert preview == {
        "computable": False,
        "event_id": event_id,
        "target": "catalog/sources/source-alpha",
        "missing": "derived output record for catalog/sources/source-alpha",
    }


def test_revert_preview_reads_the_output_record_not_a_hardcoded_event_type(
    tmp_path: Path,
) -> None:
    """A PI observation is journalled as `observed_external_edit` and *does*
    carry an output record, so it previews — and reports its own event type.
    What makes an event previewable is the record it wrote, not its name."""
    vault, _ = _vault(tmp_path)
    event_id = _event_id(vault, PI_NOTE, event_type="observed_external_edit")

    preview = revert_preview(vault, event_id)

    assert preview["computable"] is True
    assert preview["target"] == PI_NOTE
    assert preview["event"]["event_type"] == "observed_external_edit"
    assert preview["outputs"]["materialized_commit"]


def test_read_revert_preview_serves_the_envelope_and_refuses_out_of_scope_events(
    tmp_path: Path,
) -> None:
    vault, _ = _vault(tmp_path)
    event_id = _event_id(vault, TARGET)

    payload = engine_api.read_revert_preview(vault, event_id)

    assert payload["ok"] is True
    assert payload["api_version"] == "engine-read-api.v1"
    assert payload["preview"]["target"] == TARGET
    # In scope the same event resolves; out of scope it is absent, not hidden.
    assert (
        engine_api.read_revert_preview(vault, event_id, read_scope=["notes"])["preview"]["target"]
        == TARGET
    )
    with pytest.raises(FileNotFoundError, match=f"derived record not found: {event_id}"):
        engine_api.read_revert_preview(vault, event_id, read_scope=["digests"])


def test_read_revert_preview_refuses_to_confirm_an_event_id_under_a_scope(
    tmp_path: Path,
) -> None:
    """A bounded reader must not learn *whether* an event exists: an id that is
    absent and one that is out of scope raise the same refusal."""
    vault, _ = _vault(tmp_path)

    with pytest.raises(FileNotFoundError, match="derived record not found: 9999"):
        engine_api.read_revert_preview(vault, 9_999, read_scope=["notes"])


def test_cli_journal_revert_preview_serves_a_computable_preview(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The CLI leg end-to-end. The floor sweep only asserts this row's envelope,
    so an argument that reached the engine as the wrong type would still sweep
    green while every preview came back as an honest miss — the id has to
    arrive as the integer `event_id` the journal is keyed by."""
    vault, _ = _vault(tmp_path)
    event_id = _event_id(vault, TARGET)

    rc = main(["journal", "revert-preview", str(event_id), "--workspace", str(vault), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert payload["ok"] is True
    assert payload["preview"]["computable"] is True
    assert payload["preview"]["event_id"] == event_id
    assert payload["preview"]["target"] == TARGET
    assert payload["preview"]["would_quarantine"] == [CHILD]


def test_cli_journal_revert_preview_names_an_unknown_event_without_crashing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vault, _ = _vault(tmp_path)

    rc = main(["journal", "revert-preview", "9999", "--workspace", str(vault), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert payload["preview"] == {
        "computable": False,
        "event_id": 9999,
        "target": "",
        "missing": "journal event 9999",
    }
