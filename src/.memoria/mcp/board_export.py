#!/usr/bin/env python3
"""Project the Hermes Kanban into vault files and telemetry logs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

_RUNTIME_ROOT = Path(__file__).resolve().parent.parent
_REPO_DIR = Path(__file__).resolve().parents[3]
for _path in (_RUNTIME_ROOT, _REPO_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from _shared import append_jsonl, load_json, now_iso, resolve_vault, safe_filename
from board_export_cost import CostDoctorError, HermesCostLookup, load_card_detail, run_cost_doctor
from operations.lib import inbox

BOARD_RELDIR = "system/board"
SNAPSHOT_RELPATH = "system/logs/board-state.jsonl"
TRANSITIONS_RELPATH = "system/logs/board-transitions.jsonl"
DISPOSITION_RELPATH = "system/logs/disposition.jsonl"
COST_RELPATH = "system/logs/cost.jsonl"
COST_MISSES_RELPATH = "system/logs/cost-misses.jsonl"
BLIND_REVIEW_RELPATH = "system/logs/blind-review-samples.jsonl"
STATE_CACHE_RELPATH = "system/logs/.board-state-cache.json"
LIVE_STATUSES = ("triage", "todo", "ready", "running", "blocked", "done")
REVIEW_QUEUE_STATES = ("requested",)
TERMINAL_REVIEW = {"approved": "accepted", "rejected": "rejected", "changes-requested": "rejected"}
REVIEW_PROMPT_FRESH_SECONDS = 24 * 3600


def load_cards(from_json: Path | None = None) -> list[dict]:
    if from_json is not None:
        raw = from_json.read_text(encoding="utf-8")
    else:
        try:
            proc = subprocess.run(
                ["hermes", "kanban", "list", "--json"], capture_output=True, text=True, check=True
            )
        except subprocess.CalledProcessError as exc:
            print(
                f"[board_export] hermes kanban list failed (exit {exc.returncode}): "
                f"{exc.stderr.strip()}",
                file=sys.stderr,
            )
            raise
        except FileNotFoundError:
            print("[board_export] 'hermes' not found on PATH", file=sys.stderr)
            raise
        raw = proc.stdout
    data = json.loads(raw)
    cards = data.get("tasks", data) if isinstance(data, dict) else data
    return [card for card in cards if isinstance(card, dict)]


def _first(card: dict, *keys: str, default=""):
    for key in keys:
        if key in card and card[key] not in (None, ""):
            return card[key]
    return default


def _iso_ts(value, default="") -> str:
    if value in (None, ""):
        return default
    if isinstance(value, str) and not value.isdigit():
        return value
    try:
        ts = float(value)
    except (TypeError, ValueError):
        return str(value)
    if ts > 1e11:
        ts /= 1000.0
    return datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _metadata(card: dict) -> dict:
    md = card.get("metadata")
    if isinstance(md, dict):
        return md
    if isinstance(md, str):
        try:
            parsed = json.loads(md)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def normalize(card: dict) -> dict:
    md = _metadata(card)
    runs = card.get("runs") or []
    summary = ""
    run_error = ""
    if runs and isinstance(runs[-1], dict):
        summary = runs[-1].get("summary", "") or ""
        run_error = runs[-1].get("error", "") or ""
    summary = (
        summary or md.get("summary", "") or _first(card, "summary", "latest_summary", "result")
    )
    outputs = md.get("expected_outputs", "")
    if isinstance(outputs, (list, tuple)):
        outputs = ", ".join(str(output) for output in outputs)
    return {
        "task_id": _first(card, "task_id", "id", default="unknown"),
        "title": _first(card, "title", default="(untitled)"),
        "status": _first(card, "status", default="unknown"),
        "assignee": _first(card, "assignee", default="none"),
        "review_status": md.get("review_status", "unreviewed"),
        "retry_count": md.get("retry_count", 0),
        "reason": _first(card, "reason") or md.get("blocked_reason", "") or run_error,
        "created_at": _iso_ts(_first(card, "created_at", default="")),
        "last_updated": _iso_ts(_first(card, "updated_at", "modified_at", "created_at")),
        "summary": summary,
        "expected_outputs": str(outputs or ""),
        "agent_recommendation": md.get("agent_recommendation", ""),
        "expanded_at": md.get("expanded_at", ""),
        "review_requested_at": md.get("review_requested_at", ""),
        "reviewed_at": md.get("reviewed_at", ""),
        "blind_rereview": md.get("blind_rereview", False),
    }


def _yaml_scalar(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def card_markdown(card: dict) -> str:
    frontmatter = {
        "title": card["title"],
        "type": "worker-card",
        "lifecycle": "current",
        "task_id": card["task_id"],
        "lane": card["assignee"],
        "status": card["status"],
        "review_status": card["review_status"],
        "retry_count": card["retry_count"],
        "reason": card["reason"],
        "as_of": card["last_updated"],
        "created": card["created_at"],
    }
    if card["expected_outputs"]:
        frontmatter["expected_outputs"] = card["expected_outputs"]
    lines = ["---", *[f"{key}: {_yaml_scalar(value)}" for key, value in frontmatter.items()]]
    lines += ["---", "", f"# {card['title']}", ""]
    if card["summary"]:
        lines += [card["summary"], ""]
    return "\n".join(lines)


def _card_from_detail(card: dict, show_card) -> dict:
    if show_card is None:
        return card
    try:
        return normalize(show_card(card["task_id"]))
    except (
        CostDoctorError,
        subprocess.CalledProcessError,
        FileNotFoundError,
        json.JSONDecodeError,
    ) as exc:
        print(
            f"[board_export] could not read task detail for {card['task_id']}: {exc}",
            file=sys.stderr,
        )
        return card


def _project_for_activity(raw: dict, show_card=None) -> dict:
    card = normalize(raw)
    if card["status"] == "blocked" and not card["reason"]:
        detail = _card_from_detail(card, show_card)
        detail_reason = detail["reason"] or detail["summary"]
        if detail_reason:
            return {**card, "reason": detail_reason, "summary": detail["summary"]}
    if card["status"] == "done" and _is_map_corpus(card) and not card["expected_outputs"]:
        detail_summary = _card_from_detail(card, show_card)["summary"]
        if "too small" in detail_summary.lower():
            return {
                **card,
                "status": "blocked",
                "reason": card["reason"] or "The corpus is too small for a stable full map.",
                "summary": detail_summary,
            }
    return card


def export_markdown(vault: Path, cards: list[dict], show_card=None) -> set[str]:
    board = vault / BOARD_RELDIR
    board.mkdir(parents=True, exist_ok=True)
    live = [
        card
        for card in (_project_for_activity(raw, show_card) for raw in cards)
        if card["status"] in LIVE_STATUSES
    ]
    written = set()
    for card in live:
        fname = safe_filename(card["task_id"]) + ".md"
        (board / fname).write_text(card_markdown(card), encoding="utf-8")
        written.add(fname)
    for path in board.glob("*.md"):
        if path.name not in written:
            path.unlink()
    return {card["task_id"] for card in live}


def board_snapshot(cards: list[dict], show_card=None) -> dict:
    lanes: dict[str, dict] = {}
    totals = {"running": 0, "ready": 0, "blocked": 0, "review_queue": 0, "retrying": 0}
    for raw in cards:
        card = _project_for_activity(raw, show_card)
        lane = lanes.setdefault(
            card["assignee"],
            {"running": 0, "ready": 0, "blocked": 0, "review_queue": 0, "retrying": 0},
        )
        status = card["status"]
        if status in ("running", "ready", "blocked"):
            lane[status] += 1
            totals[status] += 1
        if status == "done" and card["review_status"] in REVIEW_QUEUE_STATES:
            lane["review_queue"] += 1
            totals["review_queue"] += 1
        if status == "ready" and int(card.get("retry_count") or 0) > 0:
            lane["retrying"] += 1
            totals["retrying"] += 1
    return {"timestamp": now_iso(), "lanes": lanes, "totals": totals}


def export_snapshot(vault: Path, cards: list[dict], show_card=None) -> dict:
    snap = board_snapshot(cards, show_card)
    append_jsonl(vault / SNAPSHOT_RELPATH, [snap])
    return snap


def load_state_cache(vault: Path) -> dict:
    path = vault / STATE_CACHE_RELPATH
    if path.exists():
        try:
            data = load_json(path)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError as exc:
            print(f"[board_export] corrupt state cache ({path}), resetting: {exc}", file=sys.stderr)
            return {}
    return {}


def save_state_cache(vault: Path, cards: list[dict]) -> None:
    cur = {}
    for raw in cards:
        card = normalize(raw)
        cur[card["task_id"]] = {"status": card["status"], "review_status": card["review_status"]}
    path = vault / STATE_CACHE_RELPATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cur, ensure_ascii=False), encoding="utf-8")


def should_sample_blind_review(task_id: str, rate: float = 0.05) -> bool:
    if not task_id or rate <= 0:
        return False
    bucket = int(hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:8], 16) / 0xFFFFFFFF
    return bucket < rate


def compute_events(prev: dict, cards: list[dict], cost_lookup=None) -> dict:
    ts = now_iso()
    transitions: list[dict] = []
    dispositions: list[dict] = []
    costs: list[dict] = []
    cost_misses: list[dict] = []
    blind_reviews: list[dict] = []
    for raw in cards:
        card = normalize(raw)
        task_id, lane = card["task_id"], card["assignee"]
        if task_id not in prev:
            continue
        before = prev[task_id]
        old_status, old_review = before.get("status"), before.get("review_status")

        if card["status"] != old_status:
            transitions.append(
                {
                    "timestamp": ts,
                    "task_id": task_id,
                    "lane": lane,
                    "kind": "status",
                    "from": old_status,
                    "to": card["status"],
                }
            )
            if card["status"] == "done" and cost_lookup is not None:
                cost_row, miss_row = cost_lookup(raw, card, ts)
                if cost_row is not None:
                    costs.append(cost_row)
                if miss_row is not None:
                    cost_misses.append(miss_row)

        if card["review_status"] != old_review:
            transitions.append(
                {
                    "timestamp": ts,
                    "task_id": task_id,
                    "lane": lane,
                    "kind": "review",
                    "from": old_review,
                    "to": card["review_status"],
                }
            )
            if card["review_status"] in TERMINAL_REVIEW:
                disposition = TERMINAL_REVIEW[card["review_status"]]
                if card["blind_rereview"] or should_sample_blind_review(task_id):
                    blind_reviews.append(
                        {
                            "timestamp": ts,
                            "task_id": task_id,
                            "lane": lane,
                            "disposition": disposition,
                            "review_status": card["review_status"],
                            "sample_reason": "blind-rereview",
                            "agent_recommendation": card["agent_recommendation"],
                        }
                    )
    return {
        "transitions": transitions,
        "dispositions": dispositions,
        "costs": costs,
        "cost_misses": cost_misses,
        "blind_reviews": blind_reviews,
    }


def export_events(vault: Path, prev: dict, cards: list[dict], cost_lookup=None) -> dict:
    events = compute_events(prev, cards, cost_lookup=cost_lookup)
    append_jsonl(vault / TRANSITIONS_RELPATH, events["transitions"])
    append_jsonl(vault / DISPOSITION_RELPATH, events["dispositions"])
    append_jsonl(vault / COST_RELPATH, events["costs"])
    append_jsonl(vault / COST_MISSES_RELPATH, events["cost_misses"])
    append_jsonl(vault / BLIND_REVIEW_RELPATH, events["blind_reviews"])
    return {key: len(value) for key, value in events.items()}


def _recently_done(card: dict, now: datetime | None = None) -> bool:
    raw = card.get("last_updated", "")
    if not raw:
        return False
    try:
        timestamp = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return False
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    now = now or datetime.now(UTC)
    return (now - timestamp).total_seconds() <= REVIEW_PROMPT_FRESH_SECONDS


def newly_done(prev: dict, cards: list[dict]) -> list[dict]:
    out: list[dict] = []
    for raw in cards:
        card = normalize(raw)
        if card["status"] != "done" or card["review_status"] not in REVIEW_QUEUE_STATES:
            continue
        before = prev.get(card["task_id"])
        if before is not None:
            if before.get("status") == "done":
                continue
        elif not _recently_done(card):
            continue
        out.append(raw)
    return out


def export_review_prompts(vault: Path, prev: dict, cards: list[dict]) -> int:
    written = 0
    for raw in newly_done(prev, cards):
        card = normalize(raw)
        outputs = _metadata(raw).get("expected_outputs", "")
        if isinstance(outputs, (list, tuple)):
            outputs = ", ".join(str(output) for output in outputs)
        path = inbox.write_work_prompt(
            vault,
            title=f"Completed work: {card['title']}",
            action="Open the result, then dismiss this prompt when no action remains.",
            what_happened=(
                f'Lane {card["assignee"]} finished "{card["title"]}" (card {card["task_id"]}).'
            ),
            raised_by="board-export",
            target=str(outputs or ""),
            task_id=card["task_id"],
            lane=card["assignee"],
            dedupe_slug=f"review-{card['task_id']}",
            prompt_kind="review",
        )
        if path is not None:
            written += 1
    return written


def _is_map_corpus(card: dict) -> bool:
    return card["title"].lower().startswith(("map corpus", "map the corpus"))


def _map_corpus_requirement(vault: Path) -> int:
    try:
        import yaml

        data = yaml.safe_load(
            (vault / ".memoria/schemas/calibration.yaml").read_text(encoding="utf-8")
        )
        clustering = data.get("clustering", {}) if isinstance(data, dict) else {}
        mcs = int(clustering.get("hdbscan_min_cluster_size", 5))
        floor = int(clustering.get("full_cluster_min_documents", 10))
        return max(mcs * 2, floor)
    except Exception:  # noqa: BLE001 -- best-effort receipt detail; defaults keep the ticket useful.
        return 10


def _non_empty_markdown_count(folder: Path) -> int:
    if not folder.is_dir():
        return 0
    count = 0
    for path in folder.glob("*.md"):
        body = re.sub(
            r"^---\n(.*?)\n---", "", path.read_text(encoding="utf-8"), count=1, flags=re.S
        )
        if body.strip():
            count += 1
    return count


def _map_corpus_gap_body(card: dict, source_count: int, required_count: int) -> str:
    missing_count = max(required_count - source_count, 0)
    reason = card["reason"] or "The corpus is too small for a stable full map."
    return "\n".join(
        [
            "# Action",
            "",
            f"Add `{missing_count}` relevant source note(s), then retry Map corpus.",
            "",
            "# Why this is blocked",
            "",
            (
                f"Map corpus needs `{required_count}` non-empty source notes for a full map. "
                f"The current source corpus has `{source_count}`."
            ),
            "",
            "Memoria does not generate a partial corpus map here because a small-corpus map can look complete while missing the structure a full map is meant to show.",
            "",
            f"Latest task: `{card['task_id']}`. Board state at `{card['last_updated']}`. Reason: {reason}",
            "",
            "# Next actions",
            "",
            "```button",
            "name Find sources",
            "type command",
            "action QuickAdd: Memoria: assist find",
            "```",
            "",
            "If you already have a source in hand:",
            "",
            "```button",
            "name Capture source",
            "type command",
            "action QuickAdd: Memoria: capture source from URL",
            "```",
            "",
            "```button",
            "name Capture from Zotero",
            "type command",
            "action QuickAdd: Memoria: capture from Zotero selection",
            "```",
            "",
            "```button",
            "name Retry map corpus",
            "type command",
            "action QuickAdd: Memoria: retry map corpus and dismiss",
            "```",
            "",
            "```button",
            "name Dismiss",
            "type command",
            "action QuickAdd: Memoria: dismiss inbox card",
            "```",
            "",
            "```button",
            "name Back to Inbox",
            "type command",
            "action QuickAdd: Memoria: open Inbox",
            "```",
            "",
        ]
    )


def _write_map_corpus_gap(vault: Path, card: dict) -> bool:
    source_count = _non_empty_markdown_count(vault / "notes/sources")
    required_count = _map_corpus_requirement(vault)
    if source_count >= required_count:
        return _archive_map_corpus_gap(vault)
    path = vault / "inbox" / "gap-map-corpus.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    title = "Map corpus needs more sources"
    action = f"Add {required_count - source_count} source note(s), then retry Map corpus"
    today = datetime.now(UTC).date().isoformat()
    content = "\n".join(
        [
            "---",
            f"title: {_yaml_scalar(title)}",
            "type: gap",
            "lifecycle: proposed",
            f"action: {_yaml_scalar(action)}",
            'argument_for: "A full corpus map needs enough source notes to form stable clusters."',
            'argument_against: "Waiting is better than showing a partial map as if it were complete."',
            'what_tipped_it: "The map task blocked before reaching the calibrated corpus floor."',
            "certainty: confident",
            "gap_type: additive",
            "raised_by: board-export",
            "loudness: notice",
            f"created: {today}",
            "---",
            "",
            _map_corpus_gap_body(card, source_count, required_count),
        ]
    )
    if content == existing:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _archive_map_corpus_gap(vault: Path) -> bool:
    path = vault / "inbox" / "gap-map-corpus.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    head, sep, tail = text.partition("\n---\n")
    if not sep or "\nlifecycle: archived\n" in head:
        return False
    today = datetime.now(UTC).date().isoformat()
    head = re.sub(r"^lifecycle: .*$", "lifecycle: archived", head, count=1, flags=re.M)
    if not re.search(r"^resolved:", head, re.M):
        head += f"\nresolved: {today}"
    path.write_text(head + sep + tail, encoding="utf-8")
    return True


def _stable_prompt_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:60] or "card"


def _archive_proposed_card(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    head, sep, tail = text.partition("\n---\n")
    if not sep or not re.search(r"^lifecycle:\s+proposed$", head, re.M):
        return False
    today = datetime.now(UTC).date().isoformat()
    head = re.sub(r"^lifecycle: .*$", "lifecycle: archived", head, count=1, flags=re.M)
    if not re.search(r"^resolved:", head, re.M):
        head += f"\nresolved: {today}"
    path.write_text(head + sep + tail, encoding="utf-8")
    return True


def _archive_legacy_map_blocked_prompt(vault: Path, task_id: str) -> bool:
    inbox_dir = vault / "inbox"
    slug = _stable_prompt_slug(f"blocked-{task_id}")
    candidates = {
        inbox_dir / f"work-prompt-{slug}.md",
        inbox_dir / f"work-prompt-blocked-{task_id}.md",
    }
    archived = False
    for path in candidates:
        archived = _archive_proposed_card(path) or archived
    return archived


def _map_corpus_blocked_body(card: dict, source_count: int, required_count: int) -> str:
    reason = card["reason"] or card["summary"]
    reason_lines = []
    if source_count >= required_count:
        if reason:
            reason_lines = [
                (
                    "Previous block reason: the source-count floor was not met when this task ran."
                    if "too small" in reason.lower()
                    else f"Recorded block reason: {reason}"
                ),
                "",
            ]
        corpus_status = (
            "The corpus now meets the source-count floor. Retry Map corpus; the retry button "
            "also dismisses this ticket and returns to the Inbox. If it blocks again, leave the "
            "new ticket open and inspect the board/log details."
        )
    else:
        reason_lines = [f"Recorded block reason: {reason or 'No block reason was recorded.'}", ""]
        corpus_status = (
            "The corpus is still below the source-count floor. Add sources, then retry Map corpus."
        )
    return "\n".join(
        [
            "# Status",
            "",
            "Map corpus blocked before producing a map.",
            "",
            *reason_lines,
            "# Corpus",
            "",
            f"Current source corpus: `{source_count}` non-empty source notes. Full map requires `{required_count}`.",
            "",
            corpus_status,
            "",
            f"Latest task: `{card['task_id']}`. Board state at `{card['last_updated']}`.",
            "",
            "# Next actions",
            "",
            "```button",
            "name Retry map corpus",
            "type command",
            "action QuickAdd: Memoria: retry map corpus and dismiss",
            "```",
            "",
            "```button",
            "name Dismiss",
            "type command",
            "action QuickAdd: Memoria: dismiss inbox card",
            "```",
            "",
            "```button",
            "name Back to Inbox",
            "type command",
            "action QuickAdd: Memoria: open Inbox",
            "```",
            "",
        ]
    )


def _write_map_corpus_blocked_prompt(
    vault: Path, card: dict, source_count: int, required_count: int
) -> bool:
    path = vault / "inbox" / "work-prompt-map-corpus-blocked.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    title = "Map corpus blocked"
    action = "Retry Map corpus or dismiss this ticket"
    what_happened = f"Map corpus task {card['task_id']} blocked."
    today = datetime.now(UTC).date().isoformat()
    content = "\n".join(
        [
            "---",
            f"title: {_yaml_scalar(title)}",
            "type: work-prompt",
            "lifecycle: proposed",
            f"action: {_yaml_scalar(action)}",
            f"what_happened: {_yaml_scalar(what_happened)}",
            f"task_id: {_yaml_scalar(card['task_id'])}",
            f"lane: {_yaml_scalar(card['assignee'])}",
            "prompt_kind: blocked",
            "raised_by: board-export",
            "loudness: alert",
            f"created: {today}",
            "---",
            "",
            _map_corpus_blocked_body(card, source_count, required_count),
        ]
    )
    if content == existing:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _write_blocked_prompt(vault: Path, card: dict) -> bool:
    reason = card["reason"] or card["summary"] or "No block reason was recorded."
    path = inbox.write_work_prompt(
        vault,
        title=f"Blocked work: {card['title']}",
        action="Resolve the blocker, then retry or dismiss this item.",
        what_happened=(
            f'Lane {card["assignee"]} blocked "{card["title"]}" '
            f"(card {card['task_id']}). Reason: {reason}"
        ),
        raised_by="board-export",
        task_id=card["task_id"],
        lane=card["assignee"],
        loudness="alert",
        dedupe_slug=f"blocked-{card['task_id']}",
        prompt_kind="blocked",
    )
    return path is not None


def export_actionable_blockers(vault: Path, cards: list[dict], show_card=None) -> int:
    source_count = _non_empty_markdown_count(vault / "notes/sources")
    required_count = _map_corpus_requirement(vault)
    written = int(_archive_map_corpus_gap(vault)) if source_count >= required_count else 0
    map_candidates = []
    for raw in cards:
        card = _project_for_activity(raw, show_card)
        if card["status"] != "blocked":
            continue
        if _is_map_corpus(card) and source_count < required_count:
            written += int(_archive_legacy_map_blocked_prompt(vault, card["task_id"]))
            map_candidates.append(card)
        elif _is_map_corpus(card):
            written += int(_archive_legacy_map_blocked_prompt(vault, card["task_id"]))
            written += int(
                _write_map_corpus_blocked_prompt(vault, card, source_count, required_count)
            )
        else:
            written += int(_write_blocked_prompt(vault, card))
    if map_candidates:
        latest = max(map_candidates, key=lambda card: card["last_updated"] or card["created_at"])
        written += int(_write_map_corpus_gap(vault, latest))
    return written


def run_export(
    vault: Path, from_json: Path | None = None, hermes_home: Path | str | None = None
) -> dict:
    cards = load_cards(from_json)
    prev = load_state_cache(vault)
    cost_lookup = None
    if from_json is None:
        run_cost_doctor(hermes_home)
        cost_lookup = HermesCostLookup(hermes_home=hermes_home)
    show_card = load_card_detail if from_json is None else None
    events = export_events(vault, prev, cards, cost_lookup=cost_lookup)
    prompts = export_review_prompts(vault, prev, cards)
    blockers = export_actionable_blockers(vault, cards, show_card=show_card)
    exported = export_markdown(vault, cards, show_card=show_card)
    snap = export_snapshot(vault, cards, show_card=show_card)
    save_state_cache(vault, cards)
    return {
        "exported_cards": len(exported),
        "snapshot": snap["totals"],
        "events": events,
        "review_prompts": prompts,
        "actionable_blockers": blockers,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--vault", help="vault root")
    parser.add_argument("--from-json", type=Path)
    parser.add_argument("--hermes-home", type=Path)
    parser.add_argument("--cost-doctor", action="store_true")
    args = parser.parse_args()

    if args.cost_doctor:
        try:
            print(json.dumps(run_cost_doctor(args.hermes_home), indent=2))
        except CostDoctorError as exc:
            sys.exit(f"[board_export] cost doctor failed: {exc}")
        return

    if not args.vault:
        parser.error("provide --vault <path>")
    vault = resolve_vault(args.vault)

    try:
        result = run_export(vault, args.from_json, hermes_home=args.hermes_home)
    except FileNotFoundError:
        sys.exit("`hermes` not found on PATH (and no --from-json given).")
    except subprocess.CalledProcessError as exc:
        sys.exit(f"`hermes kanban list --json` failed (exit {exc.returncode}): {exc.stderr}")
    except CostDoctorError as exc:
        sys.exit(f"[board_export] cost doctor failed: {exc}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
