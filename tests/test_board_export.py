"""L1 component test for board_export — extracted from its former --self-test (ADR-44)."""
import board_export as _m
from _util import TestHarness
globals().update({k: getattr(_m, k) for k in dir(_m) if not k.startswith("__")})


def test_board_export():
    def _run():
        import tempfile

        t = TestHarness()
        check = t.check

        sample = [
            {"task_id": "t_a1", "title": "Ingest smith2020", "status": "running",
             "assignee": "memoria-librarian", "metadata": {"review_status": "unreviewed", "retry_count": 1},
             "updated_at": "2026-05-31T10:00:00Z",
             "runs": [{"summary": "Blocker: none\nTried: lookup\nNext: enrich"}]},
            {"task_id": "t_b2", "title": "Draft answer", "status": "done",
             "assignee": "memoria-writer",
             "metadata": json.dumps({"review_status": "requested"}),    # metadata as JSON string
             "created_at": "2026-05-30T09:00:00Z"},
            {"task_id": "t_c3", "title": "Old", "status": "archived", "assignee": "memoria-writer"},
            {"task_id": "t_d4", "title": "Blocked card", "status": "blocked",
             "assignee": "memoria-librarian", "reason": "needs human input"},
        ]

        # normalize: metadata-as-string parses; defaults fill in
        n = normalize(sample[1])
        check("normalize parses string metadata", n["review_status"] == "requested")
        check("normalize defaults review_status", normalize(sample[3])["review_status"] == "unreviewed")
        check("normalize pulls run summary", "enrich" in normalize(sample[0])["summary"])
        check("normalize reads block reason", normalize(sample[3])["reason"] == "needs human input")
        check("normalize reads renamed agent_recommendation",
              normalize({"metadata": {"agent_recommendation": "clean"}})["agent_recommendation"] == "clean")
        check("normalize falls back to legacy agent_verdict",
              normalize({"metadata": {"agent_verdict": "issues-found"}})["agent_recommendation"] == "issues-found")
        check("normalize converts epoch-seconds last_updated to ISO",
              normalize({"updated_at": 1700000000})["last_updated"] == "2023-11-14T22:13:20Z")
        check("normalize converts epoch-millis last_updated to ISO",
              normalize({"updated_at": 1700000000000})["last_updated"] == "2023-11-14T22:13:20Z")
        check("normalize passes an ISO last_updated through unchanged",
              normalize(sample[0])["last_updated"] == "2026-05-31T10:00:00Z")
        check("normalize leaves last_updated empty when no timestamp",
              normalize(sample[2])["last_updated"] == "")

        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            ids = export_markdown(vault, sample)
            board = vault / BOARD_RELDIR
            check("archived card not exported", "t_c3" not in ids and not (board / "t_c3.md").exists())
            check("live cards exported", {(board / f"{i}.md").exists() for i in ("t_a1", "t_b2", "t_d4")} == {True})
            body = (board / "t_a1.md").read_text(encoding="utf-8")
            check("markdown has frontmatter task_id", "task_id: \"t_a1\"" in body)
            check("markdown has retry_count int", "retry_count: 1" in body)
            check("markdown body carries summary", "Next: enrich" in body)

            # stale pruning: a second export without t_a1 should remove its file
            export_markdown(vault, [c for c in sample if c["task_id"] != "t_a1"])
            check("stale export pruned", not (board / "t_a1.md").exists())

            snap = export_snapshot(vault, sample)
            check("snapshot counts running", snap["totals"]["running"] == 1)
            check("snapshot counts blocked", snap["totals"]["blocked"] == 1)
            check("snapshot counts review-queue (done+requested)", snap["totals"]["review_queue"] == 1)
            check("snapshot per-lane present", snap["lanes"]["memoria-librarian"]["running"] == 1)
            lines = (vault / SNAPSHOT_RELPATH).read_text(encoding="utf-8").strip().splitlines()
            check("snapshot appends one JSONL line", len(lines) == 1 and json.loads(lines[0]))

        # --- telemetry events: two runs, diff the second against the first --------
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            run1 = [
                {"task_id": "e1", "title": "x", "status": "ready",
                 "assignee": "memoria-writer", "metadata": {"review_status": "unreviewed"}},
                {"task_id": "e2", "title": "y", "status": "done",
                 "assignee": "memoria-writer", "metadata": {"review_status": "requested"}},
                {"task_id": "e3", "title": "z", "status": "done",
                 "assignee": "memoria-verifier", "metadata": {"review_status": "requested"}},
            ]
            ev1 = export_events(vault, load_state_cache(vault), run1)
            save_state_cache(vault, run1)
            check("first run seeds cache, emits no events",
                  ev1 == {"transitions": 0, "dispositions": 0, "costs": 0})

            run2 = [
                # e1: ready -> done, with cost + tokens
                {"task_id": "e1", "title": "x", "status": "done", "assignee": "memoria-writer",
                 "metadata": {"review_status": "unreviewed", "cost": 0.42, "tokens_in": 800, "tokens_out": 1200}},
                # e2: requested -> approved => accepted
                {"task_id": "e2", "title": "y", "status": "done", "assignee": "memoria-writer",
                 "metadata": {"review_status": "approved", "agent_recommendation": "clean"}},
                # e3: requested -> approved but human edited first => edited (explicit override)
                {"task_id": "e3", "title": "z", "status": "done", "assignee": "memoria-verifier",
                 "metadata": {"review_status": "approved", "disposition": "edited"}},
            ]
            ev2 = export_events(vault, load_state_cache(vault), run2)
            save_state_cache(vault, run2)
            check("second run logs three transitions (e1 status, e2/e3 review)", ev2["transitions"] == 3)
            check("second run logs cost on completion", ev2["costs"] == 1)
            check("second run logs two dispositions", ev2["dispositions"] == 2)

            disp = [json.loads(ln) for ln in (vault / DISPOSITION_RELPATH).read_text(encoding="utf-8").strip().splitlines()]
            by_id = {d["task_id"]: d for d in disp}
            check("approve -> accepted", by_id["e2"]["disposition"] == "accepted")
            check("explicit edited overrides accepted", by_id["e3"]["disposition"] == "edited")
            cost = json.loads((vault / COST_RELPATH).read_text(encoding="utf-8").strip().splitlines()[-1])
            check("cost row carries spend + tokens", cost["cost"] == 0.42 and cost["tokens_out"] == 1200)
            tr = [json.loads(ln) for ln in (vault / TRANSITIONS_RELPATH).read_text(encoding="utf-8").strip().splitlines()]
            check("transition records status change e1 ready->done",
                  any(t["task_id"] == "e1" and t["from"] == "ready" and t["to"] == "done" for t in tr))
            check("no spurious events on an unchanged re-run", export_events(vault, load_state_cache(vault), run2) ==
                  {"transitions": 0, "dispositions": 0, "costs": 0})

        return t.summary()
    assert _run() == 0
