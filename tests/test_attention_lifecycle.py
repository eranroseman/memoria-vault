"""Attention-card lifecycle: adopting hand-edited dispositions into the journal."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from memoria_vault.runtime import state, worker
from memoria_vault.runtime.subsystems.lib import lifecycle
from memoria_vault.runtime.trusted_writer import append_explicit_journal_event
from tests.helpers import init_cli_workspace


def _write_card(vault: Path, name: str, status: str, extra: str = "") -> Path:
    path = vault / "inbox" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "title: Stop\n"
        "projection: attention\n"
        "attention_kind: alert\n"
        f"attention_status: {status}\n"
        "loudness: block\n"
        f"{extra}"
        "---\n\n# Finding\n\nBody.\n",
        encoding="utf-8",
    )
    return path


def _dispositions(vault: Path) -> list[dict[str, Any]]:
    return state.read_event_log(vault, event_types=("resolved",))


def _run(workspace: Path, operation_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Drive one real attention operation end to end, the way the PI's pane does."""
    request = worker.enqueue_operation(
        workspace,
        operation_id,
        actor="pi",
        idempotency_key=f"pi-{operation_id}-{payload['target_id']}",
        payload=payload,
    )
    result = worker.run_request(workspace, request["job_id"], machine="PI laptop")
    assert result["status"] == "done", result
    return result


def test_adopt_journals_hand_edited_resolution(tmp_path: Path) -> None:
    _write_card(tmp_path, "alert-stop.md", "resolved")

    adopted = lifecycle.adopt_manual_dispositions(tmp_path, machine="test-machine")

    assert [event["target_id"] for event in adopted] == ["inbox/alert-stop.md"]
    events = _dispositions(tmp_path)
    assert len(events) == 1
    assert events[0]["via"] == "manual-edit"
    assert events[0]["actor"] == "pi"
    assert events[0]["outcome"] == "apply"
    assert events[0]["resolution"] == "resolved"


def test_adopt_is_idempotent(tmp_path: Path) -> None:
    _write_card(tmp_path, "alert-stop.md", "resolved")
    lifecycle.adopt_manual_dispositions(tmp_path, machine="test-machine")

    again = lifecycle.adopt_manual_dispositions(tmp_path, machine="test-machine")

    assert again == []
    assert len(_dispositions(tmp_path)) == 1


def test_open_cards_are_not_adopted(tmp_path: Path) -> None:
    _write_card(tmp_path, "alert-open.md", "open")

    adopted = lifecycle.adopt_manual_dispositions(tmp_path, machine="test-machine")

    assert adopted == []
    assert _dispositions(tmp_path) == []


def test_deferred_hand_edit_adopts_defer_outcome(tmp_path: Path) -> None:
    _write_card(tmp_path, "alert-later.md", "deferred")

    adopted = lifecycle.adopt_manual_dispositions(tmp_path, machine="test-machine")

    assert adopted[0]["outcome"] == "defer"
    assert (tmp_path / "inbox/alert-later.md").exists()  # adoption never moves files


@pytest.mark.parametrize(
    ("status", "hand_written_outcome", "expected"),
    [
        ("resolved", "reject", "reject"),
        ("resolved", "defer", "apply"),
        ("deferred", "apply", "defer"),
    ],
)
def test_adopted_outcome_keeps_status_and_outcome_consistent(
    tmp_path: Path, status: str, hand_written_outcome: str, expected: str
) -> None:
    _write_card(
        tmp_path, "alert-stop.md", status, extra=f"resolution_outcome: {hand_written_outcome}\n"
    )

    adopted = lifecycle.adopt_manual_dispositions(tmp_path, machine="test-machine")

    assert adopted[0]["outcome"] == expected
    assert adopted[0]["resolution_outcome"] == expected


def test_adopted_event_carries_no_card_text(tmp_path: Path) -> None:
    unbounded = "x" * 50_000
    _write_card(
        tmp_path,
        "alert-stop.md",
        "resolved",
        extra=f"resolution_outcome: {unbounded}\nrouting_class: {unbounded}\n",
    )

    adopted = lifecycle.adopt_manual_dispositions(tmp_path, machine="test-machine")

    # The journal forbids UPDATE and DELETE: card text that lands here is permanent.
    assert unbounded not in json.dumps(_dispositions(tmp_path))
    assert adopted[0]["outcome"] == "apply"
    assert adopted[0]["routing_class"] == "ask"


def test_a_foreign_resolved_event_does_not_speak_for_a_card(tmp_path: Path) -> None:
    """`resolved` is a shared event type: note curation, moves, and rollbacks emit it too.

    Only an attention row that resolved the card records its disposition. Matching a
    foreign row would suppress the adoption and hand the gate back its silent clear.
    """
    _write_card(tmp_path, "alert-stop.md", "resolved")
    append_explicit_journal_event(
        tmp_path,
        {
            "event": "resolved",
            "resolution": "resolved",
            "target_id": "inbox/alert-stop.md",
            "source": "note-curation",
        },
        actor="pi",
        machine="test-machine",
    )

    adopted = lifecycle.adopt_manual_dispositions(tmp_path, machine="test-machine")

    assert [event["via"] for event in adopted] == ["manual-edit"]


def test_non_attention_projections_are_not_adopted(tmp_path: Path) -> None:
    path = tmp_path / "inbox/digest.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\ntitle: Weekly\nprojection: digest\nattention_status: resolved\n---\n",
        encoding="utf-8",
    )

    adopted = lifecycle.adopt_manual_dispositions(tmp_path, machine="test-machine")

    assert adopted == []


def test_nested_inbox_files_are_not_adopted(tmp_path: Path) -> None:
    nested = tmp_path / "inbox/archive/alert-stop.md"
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_text(
        "---\ntitle: Stop\nprojection: attention\nattention_status: resolved\n---\n",
        encoding="utf-8",
    )

    adopted = lifecycle.adopt_manual_dispositions(tmp_path, machine="test-machine")

    assert adopted == []


def test_operation_resolved_card_is_not_re_adopted(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    _write_card(workspace, "alert-done.md", "open")
    _run(workspace, "resolve-attention", {"target_id": "inbox/alert-done.md", "outcome": "apply"})
    before = _dispositions(workspace)
    # The operation left behind exactly what the scan looks for: a closed card.
    assert "attention_status: resolved" in (workspace / "inbox/alert-done.md").read_text()
    assert [event["resolution"] for event in before] == ["resolved"]

    adopted = lifecycle.adopt_manual_dispositions(workspace, machine="test-machine")

    assert adopted == []
    assert _dispositions(workspace) == before


def test_acknowledged_card_hand_edited_to_resolved_is_adopted(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = init_cli_workspace(tmp_path, capsys)
    _write_card(workspace, "alert-ack.md", "open")
    _run(workspace, "acknowledge-attention", {"target_id": "inbox/alert-ack.md"})
    # An acknowledgement is a `resolved` event that closed nothing: same event type,
    # same target, card still open. Matching on the target alone would skip it.
    assert [event["resolution"] for event in _dispositions(workspace)] == ["acknowledged"]
    _write_card(workspace, "alert-ack.md", "resolved")  # the PI closes it by hand

    adopted = lifecycle.adopt_manual_dispositions(workspace, machine="test-machine")

    assert [event["target_id"] for event in adopted] == ["inbox/alert-ack.md"]
    assert adopted[0]["via"] == "manual-edit"
