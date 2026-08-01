"""U2 spec §1 panel 5: the slice-scoped recent-machine-changes trace (U2 plan T.1)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from memoria_vault.engine import cockpit
from memoria_vault.runtime import integrity, trusted_writer
from tests.helpers import (
    call_with_context,
    init_cli_workspace,
    mark_file_status,
    write_checked_concept,
)

PROJECT_REL = "projects/study-alpha/project.md"
OUTLINE_REL = "projects/study-alpha/outline.md"
CLAIM_ONE = "notes/claim-one.md"
CLAIM_TWO = "notes/claim-two.md"
OFF_SLICE = "notes/off-slice.md"
# Outline ids are matched against note frontmatter `id`, and the trusted
# writer's schema rejects a non-ULID id -- so a slice member the *production*
# writer can derive into has to carry a real one.
CLAIM_ONE_ID = "01JAAAAAAAAAAAAAAAAAAAAAA1"
CLAIM_TWO_ID = "01JAAAAAAAAAAAAAAAAAAAAAA2"


def _note(rel: str, title: str, note_id: str) -> str:
    return f"---\ntype: note\ntitle: {title}\nid: {note_id}\n---\nDerived body for {rel}.\n"


def _derive(vault: Path, rel: str, title: str, note_id: str, *, machine: str) -> None:
    """One machine derivation through the shipped trusted writer.

    `stage_concept` is the production producer of the `derived` event this panel
    is about: it journals `derived` with the `output_id` and writes the matching
    `outputs` record that T.2's revert preview resolves.
    """
    call_with_context(
        trusted_writer.stage_concept,
        vault,
        rel,
        _note(rel, title, note_id),
        machine=machine,
    )
    # The PI checks what the machine derived. Staging records the output
    # `unchecked`, and an unchecked note is not a slice member at all
    # (`knowledge._checked_notes_by_path`), so derive-then-check is the only
    # trajectory in which a derived note is ever in a slice -- and it is the
    # ordinary one.
    mark_file_status(vault, rel, "note")


@pytest.fixture
def vault(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    """One active project whose outline resolves two checked notes, plus a
    checked note outside the outline.

    Deliberately non-degenerate: **two** in-slice notes, so "newest first" is a
    real ordering rather than a single row; the off-slice note is a *checked
    note in the same folder*, so slice membership is doing the excluding rather
    than a path prefix.
    """
    workspace = init_cli_workspace(tmp_path, capsys)
    write_checked_concept(workspace, PROJECT_REL, "type: project\ntitle: Study Alpha\n", "project")
    write_checked_concept(
        workspace, CLAIM_ONE, f"type: note\ntitle: Claim one\nid: {CLAIM_ONE_ID}\n", "note"
    )
    write_checked_concept(
        workspace, CLAIM_TWO, f"type: note\ntitle: Claim two\nid: {CLAIM_TWO_ID}\n", "note"
    )
    write_checked_concept(workspace, OFF_SLICE, "type: note\ntitle: Off slice\n", "note")
    (workspace / OUTLINE_REL).write_text(
        f"- {CLAIM_ONE_ID} — grounds the thesis\n- {CLAIM_TWO_ID} — the counterexample\n",
        encoding="utf-8",
    )
    return workspace


def _panel(vault: Path, **kwargs: Any) -> dict[str, Any]:
    return cockpit.trace_panel(vault, PROJECT_REL, **kwargs)


def test_trace_panel_shows_only_previewable_in_slice_derivations_newest_first(
    vault: Path,
) -> None:
    """Scoped-trace amendment (2026-07-29) §2: previewable *machine derived-output*
    events within the scoped project slice, newest first.

    Four things must be excluded, and each is excluded for its own reason, so
    they are seeded separately: a derivation outside the slice (scope), a
    `check-fired` verdict on a slice member (event type -- it carries `target_id`
    and no output record, so `read_revert_preview` could not preview it), and a
    PI-edit observation on a slice member (event type again -- the trace is the
    *machine* one, and an external edit writes no derivation record).
    """
    _derive(vault, CLAIM_ONE, "Claim one", CLAIM_ONE_ID, machine="note-machine")
    _derive(vault, OFF_SLICE, "Off slice", "01JAAAAAAAAAAAAAAAAAAAAAA3", machine="note-machine")
    call_with_context(
        integrity.record_integrity_check,
        vault,
        CLAIM_TWO,
        check="scan",
        status="failed",
        machine="scan-machine",
    )
    trusted_writer.observe_pi_edit(vault, CLAIM_TWO, "0" * 64, machine="pi-machine")
    _derive(vault, CLAIM_TWO, "Claim two", CLAIM_TWO_ID, machine="compose-machine")

    panel = _panel(vault)

    assert panel["source_action"] == "journal.list"
    assert panel["total"] == 2
    assert panel["shown"] == 2
    assert [event["output_id"] for event in panel["events"]] == [CLAIM_TWO, CLAIM_ONE]
    assert [event["event_type"] for event in panel["events"]] == ["derived", "derived"]
    # Newest first is the journal's own `event_id DESC`, not a re-sort here.
    ids = [event["event_id"] for event in panel["events"]]
    assert all(isinstance(value, int) for value in ids)
    assert ids == sorted(ids, reverse=True)
    # The panel projects the journal row; it does not republish it. Leaking
    # `payload`/`row_hash` into `--json` would hand the cockpit surface a shape
    # only the journal owns.
    assert set(panel["events"][0]) == {"event_id", "timestamp", "event_type", "output_id"}
    assert panel["events"][0]["timestamp"]


def test_trace_panel_counts_every_in_slice_change_and_shows_only_the_limit(
    vault: Path,
) -> None:
    """`total` is the honest count, `shown` is what the limit left -- the pair the
    binding contract asks for in place of a `truncated` flag.

    Three rows against a limit of two: a `total` computed after the slice (or a
    `shown` computed before it) still reports 2, and the newest row has to be the
    one the limit keeps rather than the one it drops.
    """
    _derive(vault, CLAIM_ONE, "Claim one", CLAIM_ONE_ID, machine="note-machine")
    _derive(vault, CLAIM_TWO, "Claim two", CLAIM_TWO_ID, machine="note-machine")
    _derive(vault, CLAIM_ONE, "Claim one again", CLAIM_ONE_ID, machine="compose-machine")

    panel = _panel(vault, limit=2)

    assert panel["total"] == 3
    assert panel["shown"] == 2
    assert len(panel["events"]) == 2
    assert [event["output_id"] for event in panel["events"]] == [CLAIM_ONE, CLAIM_TWO]
    # The contract limit, owned here (binding contract 2; C.1 passes it literally).
    assert cockpit.TRACE_PANEL_LIMIT == 8
    assert _panel(vault)["shown"] == 3


def test_trace_panel_total_is_not_a_count_of_the_journal_reads_default_window(
    vault: Path,
) -> None:
    """`journal.list` is a bounded tail whose limit is applied *before* its scope
    filter, so a panel that let the limit default would count the window rather
    than the slice.

    Sixty out-of-slice derivations after the in-slice one push it past that
    default of 50: with the default the panel reads fifty rows, every one of them
    scoped away, and reports an entirely confident `0 of 0`.
    """
    _derive(vault, CLAIM_ONE, "Claim one", CLAIM_ONE_ID, machine="note-machine")
    trusted_writer.append_explicit_event_batch(
        vault,
        [{"event": "derived", "output_id": f"notes/filler-{index:02d}.md"} for index in range(60)],
        actor="operation",
        machine="filler-machine",
    )

    panel = _panel(vault)

    assert panel["total"] == 1
    assert panel["shown"] == 1
    assert panel["events"][0]["output_id"] == CLAIM_ONE


def test_trace_panel_narrows_the_slice_by_the_callers_read_scope(vault: Path) -> None:
    """Scoped-trace amendment §1. `read_slice` scope-checks only the outline, so a
    member outside the caller's scope arrives in the slice payload anyway;
    carrying it into the journal read would *widen* a bounded read, and every
    other assertion in this file would stay green.
    """
    _derive(vault, CLAIM_ONE, "Claim one", CLAIM_ONE_ID, machine="note-machine")
    _derive(vault, CLAIM_TWO, "Claim two", CLAIM_TWO_ID, machine="note-machine")

    assert _panel(vault)["total"] == 2

    scoped = _panel(vault, read_scope=[PROJECT_REL, OUTLINE_REL, CLAIM_ONE])

    assert scoped["total"] == 1
    assert [event["output_id"] for event in scoped["events"]] == [CLAIM_ONE]

    # Nothing of the slice inside the scope: the honest empty panel, not a crash
    # and not the unscoped answer.
    assert _panel(vault, read_scope=[PROJECT_REL, OUTLINE_REL])["total"] == 0

    # A scope that cannot even reach the outline is a slice the panel cannot
    # read, and `read_slice` says so. Reporting an empty trace instead would
    # claim the machine wrote nothing here.
    with pytest.raises(FileNotFoundError, match="project slice not found"):
        _panel(vault, read_scope=["notes"])


def test_trace_panel_drops_a_derivation_that_also_wrote_outside_the_slice(
    vault: Path,
) -> None:
    """The membership rule this panel delegates rather than restates:
    `_journal_in_scope` requires *every* path a row names to be in scope, and
    `_journal_paths` sweeps the `outputs` list as well as `output_id`.

    A run whose outputs straddle the slice boundary is not a change to this
    slice. Pinning it here is what keeps the delegation honest -- the panel reads
    as though it filtered on `output_id` alone.
    """
    _derive(vault, CLAIM_ONE, "Claim one", CLAIM_ONE_ID, machine="note-machine")
    trusted_writer.append_explicit_journal_event(
        vault,
        {
            "event": "derived",
            "output_id": CLAIM_TWO,
            "outputs": [CLAIM_TWO, OFF_SLICE],
        },
        actor="operation",
        machine="straddle-machine",
    )

    panel = _panel(vault)

    assert panel["total"] == 1
    assert [event["output_id"] for event in panel["events"]] == [CLAIM_ONE]


def test_trace_panel_counts_the_projects_own_two_files_as_slice_members(vault: Path) -> None:
    """The slice is three kinds of id, not one: `project_path`, `outline_path`,
    and the resolved outline members.

    Every other case here derives into a member note, so a builder that swept
    only `members` would pass them all — while the machine writing the outline
    (`write-project-slice`) or the project file is exactly the change a
    researcher opens this panel to see.
    """
    trusted_writer.append_explicit_event_batch(
        vault,
        [
            {"event": "derived", "output_id": OUTLINE_REL},
            {"event": "derived", "output_id": PROJECT_REL},
        ],
        actor="operation",
        machine="slice-machine",
    )

    panel = _panel(vault)

    assert panel["total"] == 2
    assert [event["output_id"] for event in panel["events"]] == [PROJECT_REL, OUTLINE_REL]


def test_trace_panel_still_lists_a_derivation_that_named_no_output(vault: Path) -> None:
    """A `derived` row whose only path is a `target_id` is still a machine change
    to the slice; which record the preview cannot resolve is the preview's
    sentence to say (spec §3), not a reason for the trace to hide the row.
    """
    trusted_writer.append_explicit_journal_event(
        vault,
        {"event": "derived", "target_id": CLAIM_ONE},
        actor="operation",
        machine="targeting-machine",
    )

    panel = _panel(vault)

    assert panel["total"] == 1
    assert panel["events"][0]["output_id"] == ""
    assert panel["events"][0]["event_type"] == "derived"


def test_trace_panel_is_honestly_empty_before_any_machine_writes(vault: Path) -> None:
    panel = _panel(vault)

    assert panel == {"source_action": "journal.list", "events": [], "total": 0, "shown": 0}


def test_deep_screen_renders_the_real_trace_rows_end_to_end(vault: Path) -> None:
    """Builder and renderer against the same non-degenerate data.

    Every other `_trace_lines` test monkeypatches the builder, and every
    assembly test before T.1 met an empty journal -- so the two layers have each
    only ever been proven against a shape the other did not produce. This is the
    one place the real builder's rows reach the real screen.
    """
    _derive(vault, CLAIM_ONE, "Claim one", CLAIM_ONE_ID, machine="note-machine")
    _derive(vault, CLAIM_TWO, "Claim two", CLAIM_TWO_ID, machine="compose-machine")
    panels = cockpit.assemble_deep(vault, PROJECT_REL)
    trace = panels["trace"]

    out = cockpit.render_deep({"screen": "deep", "project": PROJECT_REL, "panels": panels})
    section = out[out.index("recent machine changes (journal.list)") :]

    assert "pending" not in trace
    assert trace["total"] == 2
    assert [event["output_id"] for event in trace["events"]] == [CLAIM_TWO, CLAIM_ONE]
    for event in trace["events"]:
        # Every field the builder emits, in the summary order `_trace_lines`
        # promises: a builder that stopped emitting `output_id` and a renderer
        # that stopped printing it are indistinguishable from either side alone.
        assert (
            f"  ref {event['event_id']}: "
            f"{event['timestamp']} {event['event_type']} {event['output_id']}"
        ) in section
    newest, oldest = (event["event_id"] for event in trace["events"])
    assert section.index(f"ref {newest}:") < section.index(f"ref {oldest}:")
    assert "showing 2 of 2" in section
    assert "refs preview via trace.revert_preview" in section
