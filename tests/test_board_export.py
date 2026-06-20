"""L1 component test for board_export — extracted from its former --self-test (ADR-44)."""
import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import board_export as _m
import yaml
from _util import CheckHarness
from operations.lib import schema as _schema

from memoria.runtime.time import now_iso

BOARD_RELDIR = _m.BOARD_RELDIR
BLIND_REVIEW_RELPATH = _m.BLIND_REVIEW_RELPATH
COST_MISSES_RELPATH = _m.COST_MISSES_RELPATH
COST_RELPATH = _m.COST_RELPATH
DISPOSITION_RELPATH = _m.DISPOSITION_RELPATH
SNAPSHOT_RELPATH = _m.SNAPSHOT_RELPATH
TRANSITIONS_RELPATH = _m.TRANSITIONS_RELPATH
export_events = _m.export_events
export_markdown = _m.export_markdown
export_review_prompts = _m.export_review_prompts
export_snapshot = _m.export_snapshot
load_state_cache = _m.load_state_cache
normalize = _m.normalize
run_export = _m.run_export
save_state_cache = _m.save_state_cache
should_sample_blind_review = _m.should_sample_blind_review


def _session_store(root, lane="memoria-writer"):
    db = root / "profiles" / lane / "state.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    fields = {
        "id": "TEXT PRIMARY KEY",
        "model": "TEXT",
        "input_tokens": "INTEGER",
        "output_tokens": "INTEGER",
        "cache_read_tokens": "INTEGER",
        "cache_write_tokens": "INTEGER",
        "reasoning_tokens": "INTEGER",
        "estimated_cost_usd": "REAL",
        "actual_cost_usd": "REAL",
        "cost_status": "TEXT",
        "cost_source": "TEXT",
        "billing_provider": "TEXT",
        "pricing_version": "TEXT",
    }
    cols = ", ".join(f"{name} {spec}" for name, spec in fields.items())
    with sqlite3.connect(db) as con:
        con.execute(f"CREATE TABLE sessions ({cols})")
    return db


def _insert_session(db, session_id="sess-1"):
    with sqlite3.connect(db) as con:
        con.execute(
            """INSERT INTO sessions (
                id, model, input_tokens, output_tokens, cache_read_tokens,
                cache_write_tokens, reasoning_tokens, estimated_cost_usd,
                actual_cost_usd, cost_status, cost_source, billing_provider,
                pricing_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session_id, "gpt-test", 800, 1200, 11, 22, 33, 0.41, 0.42,
             "actual", "provider-usage", "openai", "2026-06"),
        )


def test_board_export():
    def _run():
        import tempfile

        t = CheckHarness()
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
            {"task_id": "t_e5", "title": "Retry card", "status": "ready",
             "assignee": "memoria-writer", "metadata": {"retry_count": 2}},
        ]

        # normalize: metadata-as-string parses; defaults fill in
        n = normalize(sample[1])
        check("normalize parses string metadata", n["review_status"] == "requested")
        check("normalize defaults review_status", normalize(sample[3])["review_status"] == "unreviewed")
        check("normalize pulls run summary", "enrich" in normalize(sample[0])["summary"])
        check("normalize reads block reason", normalize(sample[3])["reason"] == "needs human input")
        check("normalize reads renamed agent_recommendation",
              normalize({"metadata": {"agent_recommendation": "clean"}})["agent_recommendation"] == "clean")
        check("normalize ignores the legacy agent_verdict (ADR-18: the rename is one-way)",
              normalize({"metadata": {"agent_verdict": "issues-found"}})["agent_recommendation"] == "")
        check("normalize converts epoch-seconds last_updated to ISO",
              normalize({"updated_at": 1700000000})["last_updated"] == "2023-11-14T22:13:20Z")
        check("normalize converts epoch-millis last_updated to ISO",
              normalize({"updated_at": 1700000000000})["last_updated"] == "2023-11-14T22:13:20Z")
        check("normalize passes an ISO last_updated through unchanged",
              normalize(sample[0])["last_updated"] == "2026-05-31T10:00:00Z")
        check("normalize passes an ISO created_at through unchanged",
              normalize(sample[1])["created_at"] == "2026-05-30T09:00:00Z")
        check("normalize leaves last_updated empty when no timestamp",
              normalize(sample[2])["last_updated"] == "")
        check("blind review sampling is deterministic",
              should_sample_blind_review("same-card") == should_sample_blind_review("same-card"))

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
            check("snapshot counts retrying ready cards", snap["totals"]["retrying"] == 1)
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
                  ev1 == {"transitions": 0, "dispositions": 0, "costs": 0,
                          "cost_misses": 0, "blind_reviews": 0})

            hermes_home = vault / ".hermes"
            db = _session_store(hermes_home)
            _insert_session(db)
            seen_show = []

            def show_card(task_id):
                seen_show.append(task_id)
                return {"task_id": task_id,
                        "runs": [{"metadata": {"worker_session_id": "sess-1"}}]}

            lookup = _m.HermesCostLookup(hermes_home=hermes_home, show_card=show_card)

            run2 = [
                # e1: ready -> done; cost joins through `hermes kanban show` + state.db
                {"task_id": "e1", "title": "x", "status": "done", "assignee": "memoria-writer",
                 "metadata": {"review_status": "unreviewed"}},
                # e2: requested -> approved => blind-review sample only; disposition is QuickAdd-owned
                {"task_id": "e2", "title": "y", "status": "done", "assignee": "memoria-writer",
                 "metadata": {"review_status": "approved", "agent_recommendation": "clean",
                              "blind_rereview": True}},
                # e3: requested -> approved; no disposition inferred from card overlay
                {"task_id": "e3", "title": "z", "status": "done", "assignee": "memoria-verifier",
                 "metadata": {"review_status": "approved", "disposition": "edited"}},
            ]
            ev2 = export_events(vault, load_state_cache(vault), run2, cost_lookup=lookup)
            save_state_cache(vault, run2)
            check("second run logs three transitions (e1 status, e2/e3 review)", ev2["transitions"] == 3)
            check("second run logs cost on completion", ev2["costs"] == 1)
            check("session id came from card detail", seen_show == ["e1"])
            check("second run does not infer dispositions from board metadata", ev2["dispositions"] == 0)
            check("second run has no cost misses", ev2["cost_misses"] == 0)
            check("second run samples one blind re-review", ev2["blind_reviews"] == 1)

            cost = json.loads((vault / COST_RELPATH).read_text(encoding="utf-8").strip().splitlines()[-1])
            check("cost row carries joined spend + tokens",
                  cost["session_id"] == "sess-1" and cost["cost"] == 0.42
                  and cost["output_tokens"] == 1200 and cost["cost_source"] == "provider-usage")
            blind = json.loads((vault / BLIND_REVIEW_RELPATH).read_text(encoding="utf-8").strip().splitlines()[-1])
            check("blind re-review row carries terminal review context",
                  blind["task_id"] == "e2" and blind["sample_reason"] == "blind-rereview")
            tr = [json.loads(ln) for ln in (vault / TRANSITIONS_RELPATH).read_text(encoding="utf-8").strip().splitlines()]
            check("transition records status change e1 ready->done",
                  any(t["task_id"] == "e1" and t["from"] == "ready" and t["to"] == "done" for t in tr))
            check("no spurious events on an unchanged re-run",
                  export_events(vault, load_state_cache(vault), run2, cost_lookup=lookup) ==
                  {"transitions": 0, "dispositions": 0, "costs": 0,
                   "cost_misses": 0, "blind_reviews": 0})

        return t.summary()
    assert _run() == 0


def test_cost_join_missing_session_is_reported_without_cost_row(tmp_path):
    db = _session_store(tmp_path / ".hermes")
    run1 = [_card("cost-miss", "ready")]
    save_state_cache(tmp_path, run1)
    run2 = [{"task_id": "cost-miss", "title": "x", "status": "done",
             "assignee": "memoria-writer", "metadata": {"review_status": "unreviewed"},
             "runs": [{"metadata": {"worker_session_id": "missing-session"}}]}]
    lookup = _m.HermesCostLookup(hermes_home=tmp_path / ".hermes")

    ev = export_events(tmp_path, load_state_cache(tmp_path), run2, cost_lookup=lookup)

    assert ev["costs"] == 0
    assert ev["cost_misses"] == 1
    assert not (tmp_path / COST_RELPATH).exists()
    miss = json.loads((tmp_path / COST_MISSES_RELPATH).read_text(encoding="utf-8").strip())
    assert miss["reason"] == "missing-session-row"
    assert miss["session_id"] == "missing-session"
    assert db.exists()


def test_cost_doctor_fails_closed_on_session_schema_drift(tmp_path):
    db = tmp_path / ".hermes/profiles/memoria-writer/state.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as con:
        con.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY)")

    try:
        _m.run_cost_doctor(tmp_path / ".hermes")
    except _m.CostDoctorError as exc:
        assert "schema drift" in str(exc)
        assert "actual_cost_usd" in str(exc)
    else:
        raise AssertionError("schema drift should fail closed")


def test_cost_lookup_fails_closed_when_show_lacks_worker_session_id(tmp_path):
    _session_store(tmp_path / ".hermes")
    lookup = _m.HermesCostLookup(
        hermes_home=tmp_path / ".hermes",
        show_card=lambda task_id: {"task_id": task_id, "runs": [{"metadata": {}}]},
    )

    try:
        lookup({"task_id": "no-sid"}, {"task_id": "no-sid", "assignee": "memoria-writer"}, now_iso())
    except _m.CostDoctorError as exc:
        assert "runs[].metadata.worker_session_id" in str(exc)
    else:
        raise AssertionError("missing worker_session_id should fail closed")


# --------------------------------------------------------------------------- #
# Inbox review prompts — done-card → work-prompt unification (#341)
# --------------------------------------------------------------------------- #
def _card(task_id, status, *, title="Draft answer", assignee="memoria-writer",
          updated=None, metadata=None):
    c = {"task_id": task_id, "title": title, "status": status, "assignee": assignee,
         "metadata": metadata or {"review_status": "unreviewed"}}
    if updated:
        c["updated_at"] = updated
    return c


def _prompt_files(vault):
    return sorted((vault / "inbox").glob("work-prompt-*.md")) if (vault / "inbox").exists() else []


def _frontmatter(path):
    m = re.match(r"^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
    return yaml.safe_load(m.group(1))


def test_done_transition_emits_one_schema_valid_prompt(tmp_path):
    run1 = [_card("t_1", "running",
                  metadata={"expected_outputs": "projects/p1/draft.md"})]
    assert export_review_prompts(tmp_path, load_state_cache(tmp_path), run1) == 0
    save_state_cache(tmp_path, run1)

    run2 = [_card("t_1", "done", metadata={"expected_outputs": "projects/p1/draft.md"})]
    assert export_review_prompts(tmp_path, load_state_cache(tmp_path), run2) == 1
    files = _prompt_files(tmp_path)
    assert len(files) == 1
    fm = _frontmatter(files[0])
    assert _schema.validate_frontmatter(fm, _schema.load_types()["work-prompt"]) == []
    assert fm["task_id"] == "t_1" and fm["lane"] == "memoria-writer"
    assert fm["target"] == "projects/p1/draft.md"
    assert fm["lifecycle"] == "proposed"
    assert "agent_recommendation" not in fm  # ADR-51: never a verdict
    body = files[0].read_text(encoding="utf-8")
    assert "Draft answer" in body and "# Where to look" in body


def test_rerun_emits_no_second_prompt(tmp_path):
    run1 = [_card("t_1", "running")]
    save_state_cache(tmp_path, run1)
    run2 = [_card("t_1", "done")]
    assert export_review_prompts(tmp_path, load_state_cache(tmp_path), run2) == 1
    save_state_cache(tmp_path, run2)
    # the card stays done across the next cron runs — no new prompt, ever
    for _ in range(3):
        assert export_review_prompts(tmp_path, load_state_cache(tmp_path), run2) == 0
        save_state_cache(tmp_path, run2)
    assert len(_prompt_files(tmp_path)) == 1
    # belt-and-braces: even with a stale cache (re-transition), the stable
    # filename means the same card id never duplicates an existing prompt
    assert export_review_prompts(tmp_path, {"t_1": {"status": "running"}}, run2) == 0
    assert len(_prompt_files(tmp_path)) == 1


def test_non_done_transitions_emit_nothing(tmp_path):
    run1 = [_card("t_1", "todo"), _card("t_2", "ready")]
    save_state_cache(tmp_path, run1)
    run2 = [_card("t_1", "ready"), _card("t_2", "blocked")]
    assert export_review_prompts(tmp_path, load_state_cache(tmp_path), run2) == 0
    assert _prompt_files(tmp_path) == []


def test_bootstrap_guard_skips_old_done_cards(tmp_path):
    old = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    recent = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    first_run = [
        _card("t_old", "done", updated=old),          # pre-feature backlog: silent
        _card("t_recent", "done", updated=recent),    # done within 24h: prompt
        _card("t_nostamp", "done"),                   # no timestamp: silent (safe)
    ]
    assert export_review_prompts(tmp_path, load_state_cache(tmp_path), first_run) == 1
    files = _prompt_files(tmp_path)
    assert len(files) == 1 and _frontmatter(files[0])["task_id"] == "t_recent"


def test_run_export_reports_review_prompts(tmp_path):
    cards = tmp_path / "cards.json"
    cards.write_text(json.dumps([_card("t_1", "running")]), encoding="utf-8")
    run_export(tmp_path, cards)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    cards.write_text(json.dumps([_card("t_1", "done", updated=now)]), encoding="utf-8")
    assert run_export(tmp_path, cards)["review_prompts"] == 1
    assert run_export(tmp_path, cards)["review_prompts"] == 0
