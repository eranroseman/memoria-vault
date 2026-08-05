"""The evidence-review engine verbs compose dwell, operation, and telemetry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from memoria_vault.engine import api as engine_api
from memoria_vault.runtime import knowledge

pytestmark = pytest.mark.contract


def _stub_run_operation(calls: list[tuple[str, dict[str, Any], dict[str, Any]]]):
    def run_operation(
        workspace: Path, operation_id: str, payload: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        calls.append((operation_id, payload, kwargs))
        return {
            "ok": True,
            "job": {"request_id": "req-1"},
            "result": {"status": "done", "resolution": {"event": "resolved"}},
        }

    return run_operation


def test_resolve_evidence_routes_through_the_operation(monkeypatch, tmp_path) -> None:
    calls: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    monkeypatch.setattr(engine_api, "run_operation", _stub_run_operation(calls))
    monkeypatch.setattr(knowledge, "review_dwell_seconds", lambda ws, eid: 4.26)

    payload = engine_api.resolve_evidence(
        tmp_path, "ev-00000001", "accept", reason="solid", warrant="w", actor="pi"
    )

    assert payload["ok"] is True
    assert payload["event"] == {"event": "resolved"}
    ops = [op for op, _p, _k in calls]
    assert ops == ["resolve-evidence", "empirical-event-record"]
    _op, resolve_payload, _kw = calls[0]
    assert resolve_payload == {
        "evidence_id": "ev-00000001",
        "decision": "accept",
        "reason": "solid",
        "warrant": "w",
    }
    _op, event, _kw = calls[1]
    assert event["event_type"] == "disposition.recorded"
    assert event["workflow"] == "evidence-review"
    assert event["duration_s"] == 4.3
    assert payload["telemetry"]["duration_s"] == 4.3


def test_resolve_evidence_surfaces_operation_refusal(monkeypatch, tmp_path) -> None:
    calls: list[tuple[str, dict[str, Any], dict[str, Any]]] = []

    def refused(
        workspace: Path, operation_id: str, payload: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        calls.append((operation_id, payload, kwargs))
        return {
            "ok": False,
            "job": {"request_id": "req-1"},
            "result": {"status": "failed", "error": "resolve-evidence requires PI actor authority"},
        }

    monkeypatch.setattr(engine_api, "run_operation", refused)
    monkeypatch.setattr(knowledge, "review_dwell_seconds", lambda ws, eid: None)

    payload = engine_api.resolve_evidence(tmp_path, "ev-00000001", "accept", actor="agent")

    assert payload["ok"] is False
    assert "PI actor authority" in payload["error"]
    ops = [op for op, _p, _k in calls]
    assert ops == ["resolve-evidence"]


def test_evidence_review_item_unknown_id(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        engine_api,
        "evidence_review_queue",
        lambda workspace, **kwargs: {"ok": True, "rows": [], "total": 0, "facet_totals": {}},
    )

    payload = engine_api.evidence_review_item(tmp_path, "ev-deadbeef")

    assert payload["ok"] is False
    assert "not in the review queue" in payload["error"]


def test_evidence_review_item_records_view_opened(monkeypatch, tmp_path) -> None:
    calls: list[tuple[str, dict[str, Any], dict[str, Any]]] = []
    monkeypatch.setattr(engine_api, "run_operation", _stub_run_operation(calls))
    row = {
        "kind": "evidence-set",
        "evidence_id": "ev-00000002",
        "item_previews": [],
    }
    monkeypatch.setattr(
        engine_api,
        "evidence_review_queue",
        lambda workspace, **kwargs: {"ok": True, "rows": [row], "total": 1, "facet_totals": {}},
    )
    from memoria_vault.runtime import evidence_review

    monkeypatch.setattr(
        evidence_review, "detail_row", lambda r, *, show_analysis: {"evidence_id": r["evidence_id"]}
    )

    payload = engine_api.evidence_review_item(tmp_path, "ev-00000002")

    assert payload["ok"] is True
    assert payload["row"] == {"evidence_id": "ev-00000002"}
    op, event, _kw = calls[0]
    assert op == "empirical-event-record"
    assert event["event_type"] == "view.opened"
    assert event["item_id"] == "ev-00000002"
