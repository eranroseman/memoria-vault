#!/usr/bin/env python3
"""eval_dispatch.py — the vault-eval dispatcher (ADR-11: diagnostic, never gating).

Fans the hand-curated gold set in ``system/eval/`` out through the *deployed*
profiles: one Hermes kanban card per ``lifecycle: current`` gold task, routed to
the board lane its frontmatter names (ADR-48 lane → profile map, mirrored from
``tasks_mcp.LANE_PROFILE``; tests/test_eval.py guards the parity). It lives with
the sweeps engines because it has exactly their shape — a deterministic, no-LLM
detector-over-the-vault that enqueues idempotent cards and lets the board
provide serialization, dedup, and the failure circuit-breaker (ADR-30 discipline).

Each card carries ``--idempotency-key eval:<task-id>:<quarter>``, so the
quarterly cron and any number of on-demand re-runs inside the same quarter
converge to one card per task. The card body wraps the gold task in the
non-committing eval contract (scratch-only writes; results reported on the
card, never written to the vault). A dispatch record is written to
``system/eval/last-run.md``.

    python eval_dispatch.py --vault <path>             # dispatch (cron + on-demand)
    python eval_dispatch.py --vault <path> --dry-run   # print the card set, create nothing
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

# task lane -> the background agent that owns it (ADR-48 §4.1).
# Mirrors mcp/tasks_mcp.py LANE_PROFILE (the sweeps engines don't import from
# mcp/); tests/test_eval.py asserts the two maps stay identical.
LANE_PROFILE = {
    "catalog": "memoria-librarian",
    "extract": "memoria-librarian",
    "link": "memoria-librarian",
    "map": "memoria-librarian",
    "draft": "memoria-writer",
    "verify": "memoria-peer-reviewer",
    "code": "memoria-engineer",
}

EVAL_DIR = "system/eval"
LAST_RUN = "last-run.md"
CREATED_BY = "memoria-eval"

# the non-committing eval contract (ADR-11): a run never mutates the vault
EVAL_PREAMBLE = (
    "**Eval context (ADR-11 vault-eval — diagnostic, never gating).** This is a "
    "gold-set capability check, not real work. Do NOT write to the vault: keep "
    "any working notes in scratch and report your answer and reasoning on this "
    "card. Score yourself against the rubric below honestly — a wrong answer "
    "reported plainly is a useful data point; a polished non-answer is not."
)

# the machine-readable result drop the scorer (eval_score.py) reads off the card
RESULT_BLOCK_TEMPLATE = """\
**Machine-readable result (required).** End your report with exactly one fenced
`json` block in this shape so the deterministic scorer can score this run —
fill the fields your workflow produces and omit the rest:

```json
{{
  "vault_eval": "result",
  "task": "{task_id}",
  "quarter": "{quarter}",
  "retrieved": ["<citekey>", "..."],
  "cited": ["<citekey>", "..."],
  "claims": ["<claim-note-stem>", "..."],
  "self_score": 0.0
}}
```

`retrieved` = your ranked results, best first (find tasks); `cited` = every
citekey you offered as evidence; `claims` = every claim note you used or
produced (`[]` if none); `self_score` = your honest rubric verdict above."""

_FM = re.compile(r"^---\n(.*?)\n---\n?", re.S)


def parse_frontmatter(text: str) -> dict:
    """YAML frontmatter -> dict ({} if absent/invalid). PyYAML is a vault dep."""
    m = _FM.match(text)
    if not m:
        return {}
    try:
        import yaml

        return yaml.safe_load(m.group(1)) or {}
    except Exception:
        return {}


def quarter_of(today: datetime.date | None = None) -> str:
    """The idempotency window: '2026-Q2'."""
    d = today or datetime.date.today()
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def load_gold_tasks(vault: Path) -> list[dict]:
    """Read the gold set: every `type: eval-task` note in system/eval/.

    Skips non-task files (README, last-run, underscore-prefixed) and tasks not
    at `lifecycle: current` — retired/proposed gold items don't dispatch.
    """
    d = vault / EVAL_DIR
    out: list[dict] = []
    if not d.is_dir():
        return out
    for p in sorted(d.glob("*.md")):
        if p.name.startswith("_") or p.name in ("README.md", LAST_RUN):
            continue
        text = p.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if fm.get("type") != "eval-task":
            continue
        if fm.get("lifecycle") != "current":
            continue
        lane = fm.get("lane")
        if lane not in LANE_PROFILE:
            print(f"[eval] {p.name}: unknown lane {lane!r} — skipped", file=sys.stderr)
            continue
        out.append({
            "id": p.stem,
            "title": str(fm.get("title") or p.stem),
            "workflow": str(fm.get("workflow") or ""),
            "lane": lane,
            "references": [str(c) for c in (fm.get("references") or [])],
            "body": _FM.sub("", text, count=1).strip(),
            "path": p,
        })
    return out


def card_for(task: dict, quarter: str) -> dict:
    """The card payload for one gold task in one quarter (pure; easy to test)."""
    goal = f"vault-eval {quarter}: {task['title']} [{task['workflow']}]"
    result_block = RESULT_BLOCK_TEMPLATE.format(task_id=task["id"], quarter=quarter)
    body = f"{EVAL_PREAMBLE}\n\n{result_block}\n\n---\n\n{task['body']}"
    return {
        "goal": goal,
        "assignee": LANE_PROFILE[task["lane"]],
        "lane": task["lane"],
        "body": body,
        "idempotency_key": f"eval:{task['id']}:{quarter}",
    }


def create_card(card: dict) -> str:
    """Shell out to `hermes kanban create` (the proven path the sweeps and
    tasks_mcp share; board semantics stay Hermes-native). Returns the card id."""
    cmd = ["hermes", "kanban", "create", card["goal"],
           "--assignee", card["assignee"],
           "--created-by", CREATED_BY, "--body", card["body"], "--json",
           "--idempotency-key", card["idempotency_key"]]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)
        obj = json.loads(r.stdout or "{}")
        return str(obj.get("id") or obj.get("task_id") or "queued")
    except subprocess.CalledProcessError as e:
        detail = (e.stderr or e.stdout or "").strip()[:200]
        print(f"[eval] enqueue failed for {card['idempotency_key']} "
              f"(exit {e.returncode}): {detail}", file=sys.stderr)
        return f"error:CalledProcessError:exit{e.returncode}"
    except subprocess.TimeoutExpired:
        print(f"[eval] enqueue timed out for {card['idempotency_key']}", file=sys.stderr)
        return "error:TimeoutExpired"
    except FileNotFoundError:
        print("[eval] 'hermes' not found on PATH", file=sys.stderr)
        return "error:FileNotFoundError:hermes-not-found"


def write_last_run(vault: Path, quarter: str, rows: list[dict]) -> Path:
    """Record what was dispatched when (plain markdown — untyped system infra)."""
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# vault-eval — last dispatch",
        "",
        "Written by `.memoria/engines/sweeps/eval_dispatch.py` (ADR-11). Do not edit;",
        "the next dispatch overwrites this file.",
        "",
        f"- **When:** {now}",
        f"- **Quarter (idempotency window):** {quarter}",
        f"- **Cards:** {len(rows)}",
        "",
        "| Gold task | Workflow | Lane | Assignee | Card |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines += [f"| {r['task']} | {r['workflow']} | {r['lane']} "
              f"| {r['assignee']} | {r['card_id']} |" for r in rows]
    out = vault / EVAL_DIR / LAST_RUN
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def dispatch(vault: Path, dry_run: bool = False,
             today: datetime.date | None = None) -> dict:
    """Fan the gold set out: one idempotent card per (current task, quarter)."""
    quarter = quarter_of(today)
    tasks = load_gold_tasks(vault)
    rows: list[dict] = []
    for t in tasks:
        card = card_for(t, quarter)
        if dry_run:
            print(f"[dry-run] {card['idempotency_key']} -> {card['assignee']}: "
                  f"{card['goal']}")
            card_id = "DRY"
        else:
            card_id = create_card(card)
        rows.append({"task": t["id"], "workflow": t["workflow"], "lane": t["lane"],
                     "assignee": card["assignee"], "card_id": card_id,
                     "idempotency_key": card["idempotency_key"]})
    if not dry_run:
        write_last_run(vault, quarter, rows)
    return {"quarter": quarter, "dispatched": rows, "dry_run": dry_run}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", required=True, help="vault root")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the card set without creating cards or writing last-run.md")
    args = ap.parse_args()
    vault = Path(args.vault).expanduser()
    if not vault.is_dir():
        sys.exit(f"not a directory: {vault}")
    result = dispatch(vault, dry_run=args.dry_run)
    n = len(result["dispatched"])
    print(f"[eval] {result['quarter']}: {n} gold task(s) "
          f"{'planned (dry-run)' if args.dry_run else 'dispatched'}")


if __name__ == "__main__":
    main()
