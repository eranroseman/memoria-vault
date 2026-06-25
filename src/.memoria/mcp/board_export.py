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
from board_export_cost import CostDoctorError, HermesCostLookup, run_cost_doctor
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
    if runs and isinstance(runs[-1], dict):
        summary = runs[-1].get("summary", "") or ""
    summary = summary or md.get("summary", "") or _first(card, "summary")
    return {
        "task_id": _first(card, "task_id", "id", default="unknown"),
        "title": _first(card, "title", default="(untitled)"),
        "status": _first(card, "status", default="unknown"),
        "assignee": _first(card, "assignee", default="none"),
        "review_status": md.get("review_status", "unreviewed"),
        "retry_count": md.get("retry_count", 0),
        "reason": _first(card, "reason") or md.get("blocked_reason", ""),
        "created_at": _iso_ts(_first(card, "created_at", default="")),
        "last_updated": _iso_ts(_first(card, "updated_at", "modified_at", "created_at")),
        "summary": summary,
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
    lines = ["---", *[f"{key}: {_yaml_scalar(value)}" for key, value in frontmatter.items()]]
    lines += ["---", "", f"# {card['title']}", ""]
    if card["summary"]:
        lines += [card["summary"], ""]
    return "\n".join(lines)


def export_markdown(vault: Path, cards: list[dict]) -> set[str]:
    board = vault / BOARD_RELDIR
    board.mkdir(parents=True, exist_ok=True)
    live = [normalize(card) for card in cards if card.get("status") in LIVE_STATUSES]
    written = set()
    for card in live:
        fname = safe_filename(card["task_id"]) + ".md"
        (board / fname).write_text(card_markdown(card), encoding="utf-8")
        written.add(fname)
    for path in board.glob("*.md"):
        if path.name not in written:
            path.unlink()
    return {card["task_id"] for card in live}


def board_snapshot(cards: list[dict]) -> dict:
    lanes: dict[str, dict] = {}
    totals = {"running": 0, "ready": 0, "blocked": 0, "review_queue": 0, "retrying": 0}
    for raw in cards:
        card = normalize(raw)
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


def export_snapshot(vault: Path, cards: list[dict]) -> dict:
    snap = board_snapshot(cards)
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
        if card["status"] != "done":
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
            title=f"Review: {card['title']}",
            action="Review the work product, then accept it or archive the board card.",
            what_happened=(
                f'Lane {card["assignee"]} finished "{card["title"]}" (card {card["task_id"]}).'
            ),
            raised_by="board-export",
            target=str(outputs or ""),
            task_id=card["task_id"],
            lane=card["assignee"],
            dedupe_slug=f"review-{card['task_id']}",
        )
        if path is not None:
            written += 1
    return written


def _set_frontmatter_fields(text: str, updates: dict[str, str]) -> str:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return text
    head = match.group(1)
    for key, value in updates.items():
        line = f"{key}: {_yaml_scalar(value)}"
        pattern = re.compile(rf"^{re.escape(key)}:.*$", re.M)
        head = pattern.sub(line, head) if pattern.search(head) else head + "\n" + line
    return "---\n" + head + text[match.end(1) :]


def update_triggered_task_receipts(vault: Path, cards: list[dict]) -> int:
    updated = 0
    for raw in cards:
        card = normalize(raw)
        if card["status"] not in {"blocked", "done"}:
            continue
        path = vault / "inbox" / f"work-prompt-{safe_filename(card['task_id'])}.md"
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if card["status"] == "done":
            new = _set_frontmatter_fields(
                text,
                {
                    "title": f"Task completed: {card['title']}",
                    "lifecycle": "archived",
                    "action": "review the result prompt if one was created",
                    "what_happened": f"Lane {card['assignee']} completed task {card['task_id']}.",
                    "loudness": "quiet",
                },
            )
            if "## Completed" not in new:
                new += (
                    f"\n## Completed\n\nTask finished at `{now_iso()}`. "
                    "Use the separate result card or artifact for review.\n"
                )
        else:
            reason = card["reason"] or "No block reason was recorded."
            new = _set_frontmatter_fields(
                text,
                {
                    "title": f"Task blocked: {card['title']}",
                    "lifecycle": "proposed",
                    "action": "resolve the blocked task or archive this receipt",
                    "what_happened": (
                        f"Lane {card['assignee']} blocked task {card['task_id']}: {reason}"
                    ),
                    "loudness": "alert",
                },
            )
            if "## Blocked" not in new:
                new += f"\n## Blocked\n\nBlocked at `{now_iso()}`.\n\nReason: {reason}\n"
        if new != text:
            path.write_text(new, encoding="utf-8")
            updated += 1
    return updated


def run_export(
    vault: Path, from_json: Path | None = None, hermes_home: Path | str | None = None
) -> dict:
    cards = load_cards(from_json)
    prev = load_state_cache(vault)
    cost_lookup = None
    if from_json is None:
        run_cost_doctor(hermes_home)
        cost_lookup = HermesCostLookup(hermes_home=hermes_home)
    events = export_events(vault, prev, cards, cost_lookup=cost_lookup)
    prompts = export_review_prompts(vault, prev, cards)
    receipts = update_triggered_task_receipts(vault, cards)
    exported = export_markdown(vault, cards)
    snap = export_snapshot(vault, cards)
    save_state_cache(vault, cards)
    return {
        "exported_cards": len(exported),
        "snapshot": snap["totals"],
        "events": events,
        "review_prompts": prompts,
        "trigger_receipts_updated": receipts,
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
