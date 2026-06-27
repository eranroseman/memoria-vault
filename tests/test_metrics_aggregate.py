"""L1 component tests for metrics_aggregate (ADR-44)."""

import metrics_aggregate as _m

AUDIT_RELPATH = _m.AUDIT_RELPATH
ATTENTION_RELPATH = _m.ATTENTION_RELPATH
BLIND_REVIEW_RELPATH = _m.BLIND_REVIEW_RELPATH
METRICS_RELDIR = _m.METRICS_RELDIR
accept_ratio_of = _m.accept_ratio_of
aggregate = _m.aggregate
datetime = _m.datetime
iso_period = _m.iso_period
json = _m.json
read_cost = _m.read_cost
read_decision_time = _m.read_decision_time
read_disposition = _m.read_disposition
read_attention = _m.read_attention
read_blind_reviews = _m.read_blind_reviews
read_lint_verdict = _m.read_lint_verdict
UTC = _m.UTC
trust_score = _m.trust_score

NOW = datetime(2026, 5, 28, tzinfo=UTC)
PERIOD = "2026-W22"


def test_trust_score_math_and_bands():
    assert trust_score(0, 0, 1.0) == (100, "healthy")
    assert trust_score(0.8, 0, 1.0)[1] == "act"
    assert trust_score(0.0, 0.0, 0.8) == (92, "healthy")
    assert trust_score(0.0, 0.0, 0.5)[1] == "watch"
    assert trust_score(0, 0, 1.0, accept_ratio=0.95)[0] == 90
    assert iso_period(NOW) == PERIOD


def test_aggregate_rolls_up_audit_and_cards_by_lane(tmp_path):
    (tmp_path / "system" / "logs").mkdir(parents=True)
    audit_lines = [
        json.dumps(
            {
                "timestamp": "2026-05-28T10:00:00Z",
                "profile": "memoria-writer",
                "action": "write",
                "decision": "allow",
            }
        )
        for _ in range(5)
    ]
    audit_lines.append(
        json.dumps(
            {
                "timestamp": "2026-05-28T10:00:00Z",
                "profile": "memoria-writer",
                "action": "write",
                "decision": "deny",
            }
        )
    )
    audit_lines.append(
        json.dumps(
            {
                "timestamp": "2026-01-01T10:00:00Z",
                "profile": "memoria-writer",
                "action": "write",
                "decision": "deny",
            }
        )
    )
    (tmp_path / AUDIT_RELPATH).write_text("\n".join(audit_lines), encoding="utf-8")
    cards = [
        {
            "task_id": "t1",
            "status": "done",
            "assignee": "memoria-writer",
            "metadata": {"retry_count": 1},
        },
        {"task_id": "t2", "status": "done", "assignee": "memoria-writer"},
        {"task_id": "t3", "status": "blocked", "assignee": "memoria-writer"},
        {"task_id": "t4", "status": "running", "assignee": "memoria-linter"},
    ]

    res = aggregate(tmp_path, cards, now=NOW)
    note = (tmp_path / METRICS_RELDIR / "lane-writer-2026-W22.md").read_text(encoding="utf-8")

    assert any(ln["lane"] == "memoria-writer" for ln in res["lanes"])
    assert not any(ln["lane"] == "memoria-mapper" for ln in res["lanes"])
    assert 'type: "lane-metric"' in note
    assert "deny_rate: 0.167" in note
    assert "success_rate: 0.667" in note
    assert "trust_score:" in note


def test_disposition_cost_and_decision_time_feed_lane_metrics(tmp_path):
    logs = tmp_path / "system" / "logs"
    logs.mkdir(parents=True)
    disp_rows = (
        [{"timestamp": "2026-05-28T10:00:00Z", "lane": "memoria-writer", "disposition": "accepted"}]
        * 3
        + [{"timestamp": "2026-05-28T10:00:00Z", "lane": "memoria-writer", "disposition": "edited"}]
        + [
            {
                "timestamp": "2026-05-28T10:00:00Z",
                "lane": "memoria-writer",
                "disposition": "rejected",
            }
        ]
        + [
            {
                "timestamp": "2026-01-01T00:00:00Z",
                "lane": "memoria-writer",
                "disposition": "accepted",
            }
        ]
    )
    (logs / "disposition.jsonl").write_text(
        "\n".join(json.dumps(r) for r in disp_rows), encoding="utf-8"
    )
    (logs / "cost.jsonl").write_text(
        "\n".join(
            json.dumps(r)
            for r in [
                {
                    "timestamp": "2026-05-28T10:00:00Z",
                    "lane": "memoria-writer",
                    "cost": 0.10,
                    "input_tokens": 100,
                    "output_tokens": 200,
                },
                {
                    "timestamp": "2026-05-28T11:00:00Z",
                    "lane": "memoria-writer",
                    "cost": 0.30,
                    "input_tokens": 50,
                    "output_tokens": 80,
                },
            ]
        ),
        encoding="utf-8",
    )
    (logs / "board-transitions.jsonl").write_text(
        "\n".join(
            json.dumps(r)
            for r in [
                {
                    "timestamp": "2026-05-28T10:00:00Z",
                    "task_id": "x",
                    "lane": "memoria-writer",
                    "kind": "review",
                    "from": "unreviewed",
                    "to": "requested",
                },
                {
                    "timestamp": "2026-05-28T10:30:00Z",
                    "task_id": "x",
                    "lane": "memoria-writer",
                    "kind": "review",
                    "from": "requested",
                    "to": "approved",
                },
            ]
        ),
        encoding="utf-8",
    )

    disposition = read_disposition(tmp_path, PERIOD)
    cost = read_cost(tmp_path, PERIOD)
    aggregate(tmp_path, [], now=NOW)
    note = (tmp_path / METRICS_RELDIR / "lane-writer-2026-W22.md").read_text(encoding="utf-8")

    assert disposition["memoria-writer"] == {"accepted": 3, "edited": 1, "rejected": 1}
    assert round(accept_ratio_of(disposition["memoria-writer"]), 2) == 0.6
    assert round(cost["memoria-writer"]["cost"], 2) == 0.40
    assert cost["memoria-writer"]["output_tokens"] == 280
    assert read_decision_time(tmp_path, PERIOD).get("memoria-writer") == 30.0
    assert "accept_ratio: 0.6" in note
    assert "decision_time_min: 30.0" in note
    assert "cost: 0.4" in note
    assert "consistency_passk" not in note


def test_attention_and_blind_review_metrics_feed_lane_notes(tmp_path):
    logs = tmp_path / "system" / "logs"
    logs.mkdir(parents=True)
    (tmp_path / ATTENTION_RELPATH).write_text(
        "\n".join(
            json.dumps(r)
            for r in [
                {
                    "timestamp": "2026-05-28T10:30:00Z",
                    "event": "inbox_card_resolved",
                    "path": "inbox/work-prompt-review-x.md",
                    "lane": "memoria-writer",
                    "task_id": "x",
                    "outcome": "Dismiss",
                    "lifecycle_to": "archived",
                    "opened_at": "2026-05-28T10:00:00Z",
                    "resolved_at": "2026-05-28T10:30:00Z",
                    "duration_minutes": 30.0,
                },
                {
                    "timestamp": "2026-05-28T11:45:00Z",
                    "event": "inbox_card_resolved",
                    "path": "inbox/work-prompt-review-y.md",
                    "lane": "memoria-writer",
                    "task_id": "y",
                    "outcome": "Dismiss",
                    "lifecycle_to": "archived",
                    "opened_at": "2026-05-28T11:00:00Z",
                    "resolved_at": "2026-05-28T11:45:00Z",
                },
            ]
        ),
        encoding="utf-8",
    )
    (tmp_path / BLIND_REVIEW_RELPATH).write_text(
        "\n".join(
            json.dumps(r)
            for r in [
                {"timestamp": "2026-05-28T12:00:00Z", "task_id": "x", "lane": "memoria-writer"},
                {"timestamp": "2026-01-01T12:00:00Z", "task_id": "old", "lane": "memoria-writer"},
            ]
        ),
        encoding="utf-8",
    )
    cards = [
        {
            "task_id": "x",
            "status": "done",
            "assignee": "memoria-writer",
            "created_at": "2026-05-28T09:00:00Z",
            "updated_at": "2026-05-28T12:00:00Z",
            "metadata": {
                "review_status": "approved",
                "expanded_at": "2026-05-28T10:00:00Z",
                "reviewed_at": "2026-05-28T10:20:00Z",
            },
        }
    ]

    attention = read_attention(tmp_path, PERIOD)
    blind = read_blind_reviews(tmp_path, PERIOD)
    aggregate(tmp_path, cards, now=NOW)
    note = (tmp_path / METRICS_RELDIR / "lane-writer-2026-W22.md").read_text(encoding="utf-8")

    assert attention["memoria-writer"]["card_open_resolve_min"] == 37.5
    assert attention["memoria-writer"]["expand_then_accept_min"] is None
    assert blind["memoria-writer"] == 1
    assert "time_on_gate_min: 180.0" in note
    assert "expand_then_accept_min: 20.0" in note
    assert "card_open_resolve_min: 37.5" in note
    assert "blind_rereview_samples: 1" in note


def test_lint_verdict_rollup_writes_periodized_verdict_note(tmp_path):
    logs = tmp_path / "system" / "logs"
    logs.mkdir(parents=True)
    (logs / "lint-findings.jsonl").write_text(
        "\n".join(
            json.dumps(r)
            for r in [
                {
                    "timestamp": "2026-05-28T02:00:00Z",
                    "detector": "broken-wikilink",
                    "severity": "HIGH",
                    "path": "a.md",
                    "message": "x",
                },
                {
                    "timestamp": "2026-05-28T02:00:00Z",
                    "detector": "stale-fleeting",
                    "severity": "LOW",
                    "path": "b.md",
                    "message": "y",
                },
                {
                    "timestamp": "2026-01-01T02:00:00Z",
                    "detector": "fama-exposure",
                    "severity": "CRITICAL",
                    "path": "c.md",
                    "message": "z",
                },
            ]
        ),
        encoding="utf-8",
    )

    verdict = read_lint_verdict(tmp_path, PERIOD)
    aggregate(tmp_path, [], now=NOW)
    vnote = (tmp_path / METRICS_RELDIR / "lint-verdict-2026-W22.md").read_text(encoding="utf-8")

    assert verdict["verdict"] == "REVIEW"
    assert (verdict["HIGH"], verdict["LOW"], verdict["CRITICAL"], verdict["total"]) == (1, 1, 0, 2)
    assert 'type: "lint-verdict"' in vnote
    assert 'verdict: "REVIEW"' in vnote
