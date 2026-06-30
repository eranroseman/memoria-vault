"""L1 component test for board_export — extracted from its former --self-test (ADR-44)."""

import json
import re
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import board_export as _m
import board_export_cost as _cost
import yaml

from memoria_vault.runtime.time import now_iso

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
            (
                session_id,
                "gpt-test",
                800,
                1200,
                11,
                22,
                33,
                0.41,
                0.42,
                "actual",
                "provider-usage",
                "openai",
                "2026-06",
            ),
        )


def test_board_export():
    def _run():
        import tempfile

        def check(name: str, cond: bool) -> None:
            assert cond, name

        sample = [
            {
                "task_id": "t_a1",
                "title": "Ingest smith2020",
                "status": "running",
                "assignee": "memoria-librarian",
                "metadata": {"review_status": "unreviewed", "retry_count": 1},
                "updated_at": "2026-05-31T10:00:00Z",
                "runs": [{"summary": "Blocker: none\nTried: lookup\nNext: enrich"}],
            },
            {
                "task_id": "t_b2",
                "title": "Draft answer",
                "status": "done",
                "assignee": "memoria-writer",
                "metadata": json.dumps({"review_status": "requested"}),  # metadata as JSON string
                "created_at": "2026-05-30T09:00:00Z",
            },
            {"task_id": "t_c3", "title": "Old", "status": "archived", "assignee": "memoria-writer"},
            {
                "task_id": "t_d4",
                "title": "Blocked card",
                "status": "blocked",
                "assignee": "memoria-librarian",
                "reason": "needs human input",
            },
            {
                "task_id": "t_e5",
                "title": "Retry card",
                "status": "ready",
                "assignee": "memoria-writer",
                "metadata": {"retry_count": 2},
            },
        ]

        # normalize: metadata-as-string parses; defaults fill in
        n = normalize(sample[1])
        check("normalize parses string metadata", n["review_status"] == "requested")
        check(
            "normalize defaults review_status",
            normalize(sample[3])["review_status"] == "unreviewed",
        )
        check("normalize pulls run summary", "enrich" in normalize(sample[0])["summary"])
        check(
            "normalize pulls run error as blocked reason",
            normalize({"status": "blocked", "runs": [{"error": "pid 123 not alive"}]})["reason"]
            == "pid 123 not alive",
        )
        check("normalize reads block reason", normalize(sample[3])["reason"] == "needs human input")
        check(
            "normalize reads renamed agent_recommendation",
            normalize({"metadata": {"agent_recommendation": "clean"}})["agent_recommendation"]
            == "clean",
        )
        check(
            "normalize ignores the legacy agent_verdict (rename is one-way)",
            normalize({"metadata": {"agent_verdict": "issues-found"}})["agent_recommendation"]
            == "",
        )
        check(
            "normalize converts epoch-seconds last_updated to ISO",
            normalize({"updated_at": 1700000000})["last_updated"] == "2023-11-14T22:13:20Z",
        )
        check(
            "normalize converts epoch-millis last_updated to ISO",
            normalize({"updated_at": 1700000000000})["last_updated"] == "2023-11-14T22:13:20Z",
        )
        check(
            "normalize passes an ISO last_updated through unchanged",
            normalize(sample[0])["last_updated"] == "2026-05-31T10:00:00Z",
        )
        check(
            "normalize passes an ISO created_at through unchanged",
            normalize(sample[1])["created_at"] == "2026-05-30T09:00:00Z",
        )
        check(
            "normalize leaves last_updated empty when no timestamp",
            normalize(sample[2])["last_updated"] == "",
        )
        check(
            "blind review sampling is deterministic",
            should_sample_blind_review("same-card") == should_sample_blind_review("same-card"),
        )

        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            ids = export_markdown(vault, sample)
            board = vault / BOARD_RELDIR
            check(
                "archived card not exported", "t_c3" not in ids and not (board / "t_c3.md").exists()
            )
            check(
                "live cards exported",
                {(board / f"{i}.md").exists() for i in ("t_a1", "t_b2", "t_d4")} == {True},
            )
            body = (board / "t_a1.md").read_text(encoding="utf-8")
            check("markdown has frontmatter task_id", 'task_id: "t_a1"' in body)
            check("markdown has retry_count int", "retry_count: 1" in body)
            check("markdown body carries summary", "Next: enrich" in body)

            # stale pruning: a second export without t_a1 should remove its file
            export_markdown(vault, [c for c in sample if c["task_id"] != "t_a1"])
            check("stale export pruned", not (board / "t_a1.md").exists())

            snap = export_snapshot(vault, sample)
            check("snapshot counts running", snap["totals"]["running"] == 1)
            check("snapshot counts blocked", snap["totals"]["blocked"] == 1)
            check(
                "snapshot counts review-queue (done+requested)", snap["totals"]["review_queue"] == 1
            )
            check("snapshot counts retrying ready cards", snap["totals"]["retrying"] == 1)
            check("snapshot per-lane present", snap["lanes"]["memoria-librarian"]["running"] == 1)
            lines = (vault / SNAPSHOT_RELPATH).read_text(encoding="utf-8").strip().splitlines()
            check("snapshot appends one JSONL line", len(lines) == 1 and json.loads(lines[0]))

        # --- telemetry events: two runs, diff the second against the first --------
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            run1 = [
                {
                    "task_id": "e1",
                    "title": "x",
                    "status": "ready",
                    "assignee": "memoria-writer",
                    "metadata": {"review_status": "unreviewed"},
                },
                {
                    "task_id": "e2",
                    "title": "y",
                    "status": "done",
                    "assignee": "memoria-writer",
                    "metadata": {"review_status": "requested"},
                },
                {
                    "task_id": "e3",
                    "title": "z",
                    "status": "done",
                    "assignee": "memoria-verifier",
                    "metadata": {"review_status": "requested"},
                },
            ]
            ev1 = export_events(vault, load_state_cache(vault), run1)
            save_state_cache(vault, run1)
            check(
                "first run seeds cache, emits no events",
                ev1
                == {
                    "transitions": 0,
                    "dispositions": 0,
                    "costs": 0,
                    "cost_misses": 0,
                    "blind_reviews": 0,
                },
            )

            hermes_home = vault / ".hermes"
            db = _session_store(hermes_home)
            _insert_session(db)
            seen_show = []

            def show_card(task_id):
                seen_show.append(task_id)
                return {"task_id": task_id, "runs": [{"metadata": {"worker_session_id": "sess-1"}}]}

            lookup = _m.HermesCostLookup(hermes_home=hermes_home, show_card=show_card)

            run2 = [
                # e1: ready -> done; cost joins through `hermes kanban show` + state.db
                {
                    "task_id": "e1",
                    "title": "x",
                    "status": "done",
                    "assignee": "memoria-writer",
                    "metadata": {"review_status": "unreviewed"},
                },
                # e2: requested -> approved => blind-review sample only; disposition is QuickAdd-owned
                {
                    "task_id": "e2",
                    "title": "y",
                    "status": "done",
                    "assignee": "memoria-writer",
                    "metadata": {
                        "review_status": "approved",
                        "agent_recommendation": "clean",
                        "blind_rereview": True,
                    },
                },
                # e3: requested -> approved; no disposition inferred from card overlay
                {
                    "task_id": "e3",
                    "title": "z",
                    "status": "done",
                    "assignee": "memoria-verifier",
                    "metadata": {"review_status": "approved", "disposition": "edited"},
                },
            ]
            ev2 = export_events(vault, load_state_cache(vault), run2, cost_lookup=lookup)
            save_state_cache(vault, run2)
            check(
                "second run logs three transitions (e1 status, e2/e3 review)",
                ev2["transitions"] == 3,
            )
            check("second run logs cost on completion", ev2["costs"] == 1)
            check("session id came from card detail", seen_show == ["e1"])
            check(
                "second run does not infer dispositions from board metadata",
                ev2["dispositions"] == 0,
            )
            check("second run has no cost misses", ev2["cost_misses"] == 0)
            check("second run samples one blind re-review", ev2["blind_reviews"] == 1)

            cost = json.loads(
                (vault / COST_RELPATH).read_text(encoding="utf-8").strip().splitlines()[-1]
            )
            check(
                "cost row carries joined spend + tokens",
                cost["session_id"] == "sess-1"
                and cost["cost"] == 0.42
                and cost["output_tokens"] == 1200
                and cost["cost_source"] == "provider-usage",
            )
            blind = json.loads(
                (vault / BLIND_REVIEW_RELPATH).read_text(encoding="utf-8").strip().splitlines()[-1]
            )
            check(
                "blind re-review row carries terminal review context",
                blind["task_id"] == "e2" and blind["sample_reason"] == "blind-rereview",
            )
            tr = [
                json.loads(ln)
                for ln in (vault / TRANSITIONS_RELPATH)
                .read_text(encoding="utf-8")
                .strip()
                .splitlines()
            ]
            check(
                "transition records status change e1 ready->done",
                any(
                    t["task_id"] == "e1" and t["from"] == "ready" and t["to"] == "done" for t in tr
                ),
            )
            check(
                "no spurious events on an unchanged re-run",
                export_events(vault, load_state_cache(vault), run2, cost_lookup=lookup)
                == {
                    "transitions": 0,
                    "dispositions": 0,
                    "costs": 0,
                    "cost_misses": 0,
                    "blind_reviews": 0,
                },
            )

    _run()


def test_cost_join_missing_session_is_reported_without_cost_row(tmp_path):
    db = _session_store(tmp_path / ".hermes")
    run1 = [_card("cost-miss", "ready")]
    save_state_cache(tmp_path, run1)
    run2 = [
        {
            "task_id": "cost-miss",
            "title": "x",
            "status": "done",
            "assignee": "memoria-writer",
            "metadata": {"review_status": "unreviewed"},
            "runs": [{"metadata": {"worker_session_id": "missing-session"}}],
        }
    ]
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


def test_cost_doctor_falls_back_to_immutable_read_only(tmp_path, monkeypatch):
    _session_store(tmp_path / ".hermes")
    real_connect = sqlite3.connect
    seen = []

    class SidecarBlockedConnection:
        def __init__(self, con):
            self.con = con

        def execute(self, sql, *args, **kwargs):
            if "sqlite_master" in sql:
                raise sqlite3.OperationalError("unable to open database file")
            return self.con.execute(sql, *args, **kwargs)

        def close(self):
            self.con.close()

    def connect(target, *args, **kwargs):
        seen.append(str(target))
        if kwargs.get("uri") and str(target).endswith("?mode=ro"):
            return SidecarBlockedConnection(real_connect(target, *args, **kwargs))
        return real_connect(target, *args, **kwargs)

    monkeypatch.setattr(_cost.sqlite3, "connect", connect)

    result = _m.run_cost_doctor(tmp_path / ".hermes")

    assert result["profiles_checked"] == ["memoria-writer"]
    assert any(target.endswith("?mode=ro&immutable=1") for target in seen)


def test_cost_lookup_missing_worker_session_id_is_a_miss_not_export_failure(tmp_path):
    _session_store(tmp_path / ".hermes")
    lookup = _m.HermesCostLookup(
        hermes_home=tmp_path / ".hermes",
        show_card=lambda task_id: {"task_id": task_id, "runs": [{"metadata": {}}]},
    )

    cost, miss = lookup(
        {"task_id": "no-sid"}, {"task_id": "no-sid", "assignee": "memoria-writer"}, now_iso()
    )

    assert cost is None
    assert miss["reason"] == "missing-worker-session-id"


# --------------------------------------------------------------------------- #
# Inbox review prompts — done-card → work-prompt unification (#341)
# --------------------------------------------------------------------------- #
def _card(
    task_id, status, *, title="Draft answer", assignee="memoria-writer", updated=None, metadata=None
):
    c = {
        "task_id": task_id,
        "title": title,
        "status": status,
        "assignee": assignee,
        "metadata": metadata or {"review_status": "unreviewed"},
    }
    if updated:
        c["updated_at"] = updated
    return c


def _prompt_files(vault):
    return sorted((vault / "inbox").glob("work-prompt-*.md")) if (vault / "inbox").exists() else []


def _frontmatter(path):
    m = re.match(r"^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.S)
    return yaml.safe_load(m.group(1))


def _checked_sources(vault, count):
    for i in range(count):
        path = vault / f"catalog/sources/source-{i}/source.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            (
                "---\n"
                "title: Source\n"
                "type: source\n"
                "check_status: checked\n"
                "description: Source fixture\n"
                "---\n"
            ),
            encoding="utf-8",
        )


def test_done_transition_emits_one_schema_valid_prompt(tmp_path):
    meta = {"expected_outputs": "projects/p1/draft.md", "review_status": "requested"}
    run1 = [_card("t_1", "running", metadata=meta)]
    assert export_review_prompts(tmp_path, load_state_cache(tmp_path), run1) == 0
    save_state_cache(tmp_path, run1)

    run2 = [_card("t_1", "done", metadata=meta)]
    assert export_review_prompts(tmp_path, load_state_cache(tmp_path), run2) == 1
    files = _prompt_files(tmp_path)
    assert len(files) == 1
    fm = _frontmatter(files[0])
    assert fm["projection"] == "attention"
    assert fm["attention_kind"] == "work-prompt"
    assert fm["attention_status"] == "open"
    assert "type" not in fm
    assert fm["task_id"] == "t_1" and fm["lane"] == "memoria-writer"
    assert fm["target"] == "projects/p1/draft.md"
    assert fm["prompt_kind"] == "review"
    assert fm["title"] == "Completed work: Draft answer"
    assert fm["action"] == "Open the result, then dismiss this prompt when no action remains."
    assert fm["title"] != fm["action"]
    assert "agent_recommendation" not in fm  # ADR-54: never a verdict
    body = files[0].read_text(encoding="utf-8")
    assert "Draft answer" in body and "# Where to look" in body


def test_rerun_emits_no_second_prompt(tmp_path):
    meta = {"review_status": "requested"}
    run1 = [_card("t_1", "running", metadata=meta)]
    save_state_cache(tmp_path, run1)
    run2 = [_card("t_1", "done", metadata=meta)]
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


def test_non_done_or_unrequested_done_transitions_emit_nothing(tmp_path):
    run1 = [_card("t_1", "todo"), _card("t_2", "ready")]
    save_state_cache(tmp_path, run1)
    run2 = [_card("t_1", "ready"), _card("t_2", "blocked"), _card("t_3", "done")]
    assert export_review_prompts(tmp_path, load_state_cache(tmp_path), run2) == 0
    assert _prompt_files(tmp_path) == []


def test_blocked_map_task_creates_one_source_gap(tmp_path):
    _checked_sources(tmp_path, 8)
    card = _card("t_1", "blocked", title="Map the corpus", assignee="memoria-librarian")
    assert _m.export_actionable_blockers(tmp_path, [card]) == 1
    assert _m.export_actionable_blockers(tmp_path, [card]) == 0

    files = sorted((tmp_path / "inbox").glob("gap-map-corpus*.md"))
    assert len(files) == 1
    assert files[0].name == "gap-map-corpus.md"
    fm = _frontmatter(files[0])
    assert fm["projection"] == "attention"
    assert fm["attention_kind"] == "gap"
    assert fm["attention_status"] == "open"
    assert "type" not in fm
    assert fm["title"] == "Map corpus needs more sources"
    assert fm["action"] == "Add 2 source note(s), then retry Map corpus"
    body = files[0].read_text(encoding="utf-8")
    assert "Map corpus needs `10` non-empty source notes" in body
    assert "The current source corpus has `8`." in body
    assert "partial corpus map" in body
    assert "Inspector control panel or Co-PI" in body
    assert "If you already have a source in hand:" in body
    assert "checked `source` Concept under `catalog/sources/`" in body
    assert "name Dismiss" in body
    assert "QuickAdd: Memoria: dismiss inbox card" in body
    assert "name Back to Inbox" in body
    assert "QuickAdd: Memoria: open Inbox" in body


def test_blocked_map_task_resolves_existing_generic_prompt(tmp_path):
    _checked_sources(tmp_path, 8)
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    prompt = inbox / "work-prompt-blocked-t-1.md"
    prompt.write_text(
        (
            "---\n"
            'title: "Blocked work: Map corpus"\n'
            "projection: attention\n"
            "attention_kind: work-prompt\n"
            "attention_status: open\n"
            'action: "Resolve the blocker."\n'
            "---\n"
        ),
        encoding="utf-8",
    )

    card = _card("t_1", "blocked", title="Map corpus", assignee="memoria-librarian")
    assert _m.export_actionable_blockers(tmp_path, [card]) == 2

    assert _frontmatter(prompt)["attention_status"] == "resolved"
    assert _frontmatter(inbox / "gap-map-corpus.md")["attention_status"] == "open"


def test_miscompleted_too_small_map_task_creates_source_gap(tmp_path):
    _checked_sources(tmp_path, 8)
    card = _card("t_1", "done", title="Map corpus", assignee="memoria-librarian")
    card["summary"] = "Corpus is too small to generate a cluster map"

    assert _m.export_actionable_blockers(tmp_path, [card]) == 1

    files = sorted((tmp_path / "inbox").glob("gap-map-corpus*.md"))
    assert len(files) == 1
    assert _frontmatter(files[0])["action"] == "Add 2 source note(s), then retry Map corpus"


def test_miscompleted_map_task_uses_show_summary_when_list_is_thin(tmp_path):
    _checked_sources(tmp_path, 8)
    card = _card("t_1", "done", title="Map corpus", assignee="memoria-librarian")

    def show_card(task_id):
        assert task_id == "t_1"
        return {**card, "latest_summary": "Corpus is too small to generate a cluster map"}

    assert _m.export_actionable_blockers(tmp_path, [card], show_card=show_card) == 1
    _m.export_markdown(tmp_path, [card], show_card=show_card)
    board_card = (tmp_path / BOARD_RELDIR / "t_1.md").read_text(encoding="utf-8")
    assert 'status: "blocked"' in board_card
    assert "Corpus is too small to generate a cluster map" in board_card
    assert len(sorted((tmp_path / "inbox").glob("gap-map-corpus*.md"))) == 1


def test_duplicate_map_blockers_share_one_stable_gap(tmp_path):
    _checked_sources(tmp_path, 8)
    old = _card(
        "t_old",
        "blocked",
        title="Map corpus",
        assignee="memoria-librarian",
        updated="2026-06-25T10:00:00Z",
    )
    new = _card(
        "t_new",
        "blocked",
        title="Map corpus",
        assignee="memoria-librarian",
        updated="2026-06-25T11:00:00Z",
    )

    assert _m.export_actionable_blockers(tmp_path, [old, new]) == 1
    body = (tmp_path / "inbox/gap-map-corpus.md").read_text(encoding="utf-8")
    assert "Latest task: `t_new`" in body
    assert not list((tmp_path / "inbox").glob("gap-map-corpus-t_*.md"))


def test_blocked_non_map_task_creates_one_blocked_prompt(tmp_path):
    card = _card(
        "t_1",
        "blocked",
        title="Draft section",
        assignee="memoria-writer",
        metadata={"blocked_reason": "Missing project thesis"},
    )
    assert _m.export_actionable_blockers(tmp_path, [card]) == 1
    assert _m.export_actionable_blockers(tmp_path, [card]) == 0

    files = _prompt_files(tmp_path)
    assert len(files) == 1
    fm = _frontmatter(files[0])
    assert fm["projection"] == "attention"
    assert fm["attention_kind"] == "work-prompt"
    assert fm["attention_status"] == "open"
    assert "type" not in fm
    assert fm["title"] == "Blocked work: Draft section"
    assert fm["action"] == "Resolve the blocker, then retry or dismiss this item."
    assert fm["prompt_kind"] == "blocked"
    assert fm["task_id"] == "t_1"
    assert fm["title"] != fm["action"]


def test_blocked_map_task_with_enough_sources_creates_blocked_prompt(tmp_path):
    _checked_sources(tmp_path, 10)
    card = _card("t_1", "blocked", title="Map corpus", assignee="memoria-librarian")

    def show_card(task_id):
        assert task_id == "t_1"
        return {**card, "latest_summary": "Corpus is too small to generate a cluster map"}

    assert _m.export_actionable_blockers(tmp_path, [card], show_card=show_card) == 1
    files = _prompt_files(tmp_path)
    assert [path.name for path in files] == ["work-prompt-map-corpus-blocked.md"]
    fm = _frontmatter(files[0])
    assert fm["title"] == "Map corpus blocked"
    assert fm["action"] == "Retry Map corpus or dismiss this ticket"
    assert fm["prompt_kind"] == "blocked"
    body = files[0].read_text(encoding="utf-8")
    assert "Previous block reason: the source-count floor was not met when this task ran." in body
    assert "Corpus is too small to generate a cluster map" not in body
    assert "Current source corpus: `10` non-empty source notes" in body
    assert "The corpus now meets the source-count floor" in body
    assert "Enqueue Map corpus again from the Inspector or Co-PI" in body
    assert "Inspector control panel to enqueue Map corpus again" in body
    assert "name Dismiss" in body
    assert "QuickAdd: Memoria: dismiss inbox card" in body
    assert "name Back to Inbox" in body
    assert "QuickAdd: Memoria: open Inbox" in body


def test_blocked_map_task_uses_hermes_run_error(tmp_path):
    _checked_sources(tmp_path, 10)
    card = _card("t_1", "blocked", title="Map corpus", assignee="memoria-librarian")

    def show_card(task_id):
        assert task_id == "t_1"
        return {**card, "runs": [{"error": "pid 123 not alive"}]}

    assert _m.export_actionable_blockers(tmp_path, [card], show_card=show_card) == 1
    body = (tmp_path / "inbox/work-prompt-map-corpus-blocked.md").read_text(encoding="utf-8")
    assert "Recorded block reason: pid 123 not alive" in body
    assert "The corpus now meets the source-count floor" in body
    assert "No block reason was recorded" not in body


def test_map_gap_archives_when_source_floor_is_met(tmp_path):
    _checked_sources(tmp_path, 10)
    inbox = tmp_path / "inbox"
    inbox.mkdir()
    gap = inbox / "gap-map-corpus.md"
    gap.write_text(
        (
            "---\ntitle: Map corpus needs more sources\nprojection: attention\n"
            "attention_kind: gap\nattention_status: open\n---\n"
        ),
        encoding="utf-8",
    )

    assert _m.export_actionable_blockers(tmp_path, []) == 1
    fm = _frontmatter(gap)
    assert fm["attention_status"] == "resolved"
    assert "resolved" in fm


def test_bootstrap_guard_skips_old_done_cards(tmp_path):
    old = (datetime.now(UTC) - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    recent = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    first_run = [
        _card("t_old", "done", updated=old),  # pre-feature backlog: silent
        _card(
            "t_recent", "done", updated=recent, metadata={"review_status": "requested"}
        ),  # done within 24h: prompt
        _card("t_nostamp", "done"),  # no timestamp: silent (safe)
    ]
    assert export_review_prompts(tmp_path, load_state_cache(tmp_path), first_run) == 1
    files = _prompt_files(tmp_path)
    assert len(files) == 1 and _frontmatter(files[0])["task_id"] == "t_recent"


def test_run_export_reports_review_prompts(tmp_path):
    cards = tmp_path / "cards.json"
    cards.write_text(json.dumps([_card("t_1", "running")]), encoding="utf-8")
    run_export(tmp_path, cards)
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    cards.write_text(
        json.dumps([_card("t_1", "done", updated=now, metadata={"review_status": "requested"})]),
        encoding="utf-8",
    )
    assert run_export(tmp_path, cards)["review_prompts"] == 1
    assert run_export(tmp_path, cards)["review_prompts"] == 0
