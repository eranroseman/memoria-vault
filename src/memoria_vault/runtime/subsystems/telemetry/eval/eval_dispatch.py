#!/usr/bin/env python3
"""Vault-eval dispatcher: diagnostic, never gating.

Fans the hand-curated gold set in ``.memoria/eval/`` into one local eval payload
per ``lifecycle: current`` gold task, routed to the eval role named in frontmatter.
It lives with the sweeps operations because it has exactly their shape — a
deterministic, no-LLM detector-over-the-vault that creates idempotent work
intents for the local engine.

Each payload carries ``eval:<task-id>:<quarter>``, so scheduled and on-demand
re-runs inside the same quarter converge to one task intent. The body wraps the
gold task in the non-committing eval contract (scratch-only writes; results are
reported back as JSON, never written directly to the vault). A dispatch record
is written to ``.memoria/eval/last-run.md``.

    python eval_dispatch.py --vault <path>             # dispatch (cron + on-demand)
    python eval_dispatch.py --vault <path> --dry-run   # print the card set, create nothing
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

from memoria_vault.runtime.vaultio import parse_frontmatter, strip_frontmatter

# eval role -> the local role label that owns it.
# Kept local so vault-eval can run without importing adapter or profile code.
EVAL_ROLE_ASSIGNEE = {
    "catalog": "memoria-librarian",
    "extract": "memoria-librarian",
    "link": "memoria-librarian",
    "map": "memoria-librarian",
    "verify": "memoria-peer-reviewer",
}

EVAL_DIR = ".memoria/eval"
LAST_RUN = "last-run.md"
CREATED_BY = "memoria-eval"

# the non-committing eval contract: a run never mutates the vault
EVAL_PREAMBLE = (
    "**Eval context (vault-eval — diagnostic, never gating).** This is a "
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
  "task": "{task}",
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


def quarter_of(today: datetime.date | None = None) -> str:
    """The idempotency window: '2026-Q2'."""
    d = today or datetime.date.today()
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def load_gold_tasks(vault: Path) -> list[dict]:
    """Read the gold set: every `type: eval-task` note in .memoria/eval/.

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
        eval_role = fm.get("eval_role")
        if eval_role not in EVAL_ROLE_ASSIGNEE:
            print(f"[eval] {p.name}: unknown eval_role {eval_role!r} — skipped", file=sys.stderr)
            continue
        out.append(
            {
                "id": p.stem,
                "title": str(fm.get("title") or p.stem),
                "workflow": str(fm.get("workflow") or ""),
                "eval_role": eval_role,
                "references": [str(c) for c in (fm.get("references") or [])],
                "body": strip_frontmatter(text).strip(),
                "path": p,
            }
        )
    return out


def card_for(task: dict, quarter: str) -> dict:
    """The card payload for one gold task in one quarter (pure; easy to test)."""
    goal = f"vault-eval {quarter}: {task['title']} [{task['workflow']}]"
    result_block = RESULT_BLOCK_TEMPLATE.format(task=task["id"], quarter=quarter)
    body = f"{EVAL_PREAMBLE}\n\n{result_block}\n\n---\n\n{task['body']}"
    return {
        "goal": goal,
        "assignee": EVAL_ROLE_ASSIGNEE[task["eval_role"]],
        "eval_role": task["eval_role"],
        "body": body,
        "idempotency_key": f"eval:{task['id']}:{quarter}",
    }


def create_card(card: dict) -> str:
    """Return the local planned-card id for one eval task."""
    return f"planned:{card['idempotency_key']}"


def write_last_run(vault: Path, quarter: str, rows: list[dict]) -> Path:
    """Record what was dispatched when (plain markdown — untyped system infra)."""
    now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# vault-eval — last dispatch",
        "",
        "Written by `memoria_vault.runtime.subsystems.telemetry.eval.eval_dispatch` "
        "using the non-committing eval contract. Do not edit;",
        "the next dispatch overwrites this file.",
        "",
        f"- **When:** {now}",
        f"- **Quarter (idempotency window):** {quarter}",
        f"- **Cards:** {len(rows)}",
        "",
        "| Gold task | Workflow | Eval role | Assignee | Card |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines += [
        f"| {r['task']} | {r['workflow']} | {r['eval_role']} | {r['assignee']} | {r['card_id']} |"
        for r in rows
    ]
    out = vault / EVAL_DIR / LAST_RUN
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def dispatch(vault: Path, dry_run: bool = False, today: datetime.date | None = None) -> dict:
    """Fan the gold set out: one idempotent card per (current task, quarter)."""
    quarter = quarter_of(today)
    tasks = load_gold_tasks(vault)
    rows: list[dict] = []
    for t in tasks:
        card = card_for(t, quarter)
        if dry_run:
            print(f"[dry-run] {card['idempotency_key']} -> {card['assignee']}: {card['goal']}")
            card_id = "DRY"
        else:
            card_id = create_card(card)
        rows.append(
            {
                "task": t["id"],
                "workflow": t["workflow"],
                "eval_role": t["eval_role"],
                "assignee": card["assignee"],
                "card_id": card_id,
                "idempotency_key": card["idempotency_key"],
            }
        )
    if not dry_run:
        write_last_run(vault, quarter, rows)
    return {"quarter": quarter, "dispatched": rows, "dry_run": dry_run}


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--vault", required=True, help="vault root")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="print the card set without creating cards or writing last-run.md",
    )
    args = ap.parse_args()
    vault = Path(args.vault).expanduser()
    if not vault.is_dir():
        sys.exit(f"not a directory: {vault}")
    result = dispatch(vault, dry_run=args.dry_run)
    n = len(result["dispatched"])
    print(
        f"[eval] {result['quarter']}: {n} gold task(s) "
        f"{'planned (dry-run)' if args.dry_run else 'dispatched'}"
    )


if __name__ == "__main__":
    main()
