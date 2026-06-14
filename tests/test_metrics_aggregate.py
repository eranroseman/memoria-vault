"""L1 component test for metrics_aggregate — extracted from its former --self-test (ADR-44)."""
import metrics_aggregate as _m
from _util import CheckHarness
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith("__")})


def test_metrics_aggregate():
    def _run():
        import tempfile

        t = CheckHarness()
        check = t.check

        # trust-score math + bands
        check("clean lane -> healthy 100", trust_score(0, 0, 1.0) == (100, "healthy"))
        check("high deny -> act band", trust_score(0.8, 0, 1.0)[1] == "act")
        s_watch, b_watch = trust_score(0.0, 0.0, 0.8)               # 100 - 40*0.2 = 92? -> healthy
        check("20% failure -> 92 healthy", (s_watch, b_watch) == (92, "healthy"))
        check("50% failure -> watch", trust_score(0.0, 0.0, 0.5)[1] == "watch")
        check("rubber-stamp down-weight", trust_score(0, 0, 1.0, accept_ratio=0.95)[0] == 90)

        now = datetime(2026, 5, 28, tzinfo=timezone.utc)            # 2026-W22
        period = iso_period(now)
        check("iso_period format", period == "2026-W22")

        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            (vault / "system" / "logs").mkdir(parents=True)
            # audit: writer made 6 writes, 1 deny, this period
            audit_lines = []
            for _ in range(5):
                audit_lines.append(json.dumps({"timestamp": "2026-05-28T10:00:00Z",
                                               "profile": "memoria-writer", "action": "write", "decision": "allow"}))
            audit_lines.append(json.dumps({"timestamp": "2026-05-28T10:00:00Z",
                                           "profile": "memoria-writer", "action": "write", "decision": "deny"}))
            # an out-of-period entry that must be ignored
            audit_lines.append(json.dumps({"timestamp": "2026-01-01T10:00:00Z",
                                           "profile": "memoria-writer", "action": "write", "decision": "deny"}))
            (vault / AUDIT_RELPATH).write_text("\n".join(audit_lines), encoding="utf-8")

            cards = [
                {"task_id": "t1", "status": "done", "assignee": "memoria-writer", "metadata": {"retry_count": 1}},
                {"task_id": "t2", "status": "done", "assignee": "memoria-writer"},
                {"task_id": "t3", "status": "blocked", "assignee": "memoria-writer"},
                {"task_id": "t4", "status": "running", "assignee": "memoria-linter"},  # no done/blocked, no audit -> skipped
            ]

            res = aggregate(vault, cards, now=now)
            check("aggregated the writer lane", any(ln["lane"] == "memoria-writer" for ln in res["lanes"]))
            check("inactive lane skipped", not any(ln["lane"] == "memoria-mapper" for ln in res["lanes"]))
            note = (vault / METRICS_RELDIR / "lane-writer-2026-W22.md").read_text(encoding="utf-8")
            check("lane note has type: lane-metric", "type: \"lane-metric\"" in note)
            check("deny_rate computed in-period only (1/6)", "deny_rate: 0.167" in note)
            check("success_rate 2/3", "success_rate: 0.667" in note)
            check("note has trust_score frontmatter", "trust_score:" in note)

        # --- new telemetry: disposition, cost, decision-time --------------------
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            logs = vault / "system" / "logs"
            logs.mkdir(parents=True)
            disp_rows = ([{"timestamp": "2026-05-28T10:00:00Z", "lane": "memoria-writer", "disposition": "accepted"}] * 3
                         + [{"timestamp": "2026-05-28T10:00:00Z", "lane": "memoria-writer", "disposition": "edited"}]
                         + [{"timestamp": "2026-05-28T10:00:00Z", "lane": "memoria-writer", "disposition": "rejected"}]
                         + [{"timestamp": "2026-01-01T00:00:00Z", "lane": "memoria-writer", "disposition": "accepted"}])  # out-of-period
            (logs / "disposition.jsonl").write_text("\n".join(json.dumps(r) for r in disp_rows), encoding="utf-8")
            d = read_disposition(vault, period)
            check("disposition counts in-period only", d["memoria-writer"] == {"accepted": 3, "edited": 1, "rejected": 1})
            check("accept_ratio 3/5", round(accept_ratio_of(d["memoria-writer"]), 2) == 0.6)

            (logs / "cost.jsonl").write_text("\n".join(json.dumps(r) for r in [
                {"timestamp": "2026-05-28T10:00:00Z", "lane": "memoria-writer", "cost": 0.10, "tokens_in": 100, "tokens_out": 200},
                {"timestamp": "2026-05-28T11:00:00Z", "lane": "memoria-writer", "cost": 0.30, "tokens_in": 50, "tokens_out": 80},
            ]), encoding="utf-8")
            c = read_cost(vault, period)
            check("cost summed per lane", round(c["memoria-writer"]["cost"], 2) == 0.40 and c["memoria-writer"]["tokens_out"] == 280)

            (logs / "board-transitions.jsonl").write_text("\n".join(json.dumps(r) for r in [
                {"timestamp": "2026-05-28T10:00:00Z", "task_id": "x", "lane": "memoria-writer", "kind": "review", "from": "unreviewed", "to": "requested"},
                {"timestamp": "2026-05-28T10:30:00Z", "task_id": "x", "lane": "memoria-writer", "kind": "review", "from": "requested", "to": "approved"},
            ]), encoding="utf-8")
            check("decision time 30 min", read_decision_time(vault, period).get("memoria-writer") == 30.0)

            aggregate(vault, [], now=now)   # disposition alone (5 reviews) yields enough samples
            note = (vault / METRICS_RELDIR / "lane-writer-2026-W22.md").read_text(encoding="utf-8")
            check("note carries accept_ratio", "accept_ratio: 0.6" in note)
            check("note carries decision_time_min", "decision_time_min: 30.0" in note)
            check("note carries cost", "cost: 0.4" in note)
            check("note carries pass^k null placeholder", "consistency_passk: null" in note)

        # --- lint-verdict rollup (periodized from timestamped lint-findings) -----
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            logs = vault / "system" / "logs"
            logs.mkdir(parents=True)
            (logs / "lint-findings.jsonl").write_text("\n".join(json.dumps(r) for r in [
                {"timestamp": "2026-05-28T02:00:00Z", "detector": "broken-wikilink", "severity": "HIGH", "path": "a.md", "message": "x"},
                {"timestamp": "2026-05-28T02:00:00Z", "detector": "stale-fleeting", "severity": "LOW", "path": "b.md", "message": "y"},
                {"timestamp": "2026-01-01T02:00:00Z", "detector": "fama-exposure", "severity": "CRITICAL", "path": "c.md", "message": "z"},  # out-of-period
            ]), encoding="utf-8")
            lv = read_lint_verdict(vault, period)
            check("lint verdict REVIEW (HIGH, no CRITICAL in-period)", lv["verdict"] == "REVIEW")
            check("lint counts in-period only (1 HIGH, 1 LOW, 0 CRITICAL)",
                  (lv["HIGH"], lv["LOW"], lv["CRITICAL"], lv["total"]) == (1, 1, 0, 2))
            aggregate(vault, [], now=now)
            vnote = (vault / METRICS_RELDIR / "lint-verdict-2026-W22.md").read_text(encoding="utf-8")
            check("lint-verdict note written with type + verdict",
                  'type: "lint-verdict"' in vnote and 'verdict: "REVIEW"' in vnote)

        return t.summary()
    assert _run() == 0
