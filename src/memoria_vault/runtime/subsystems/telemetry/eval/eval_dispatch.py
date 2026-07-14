#!/usr/bin/env python3
"""Vault-eval dispatcher: diagnostic, never gating.

Fans the workspace-authored gold set in ``.memoria/eval/`` into one local eval
payload per ``lifecycle: current`` gold task, routed to the eval role named in
frontmatter.
It lives with the sweeps operations because it has exactly their shape — a
deterministic, no-LLM detector-over-the-vault that creates idempotent work
intents for the local engine.

Each payload carries ``eval:<task-id>:<quarter>``, so scheduled and on-demand
re-runs inside the same quarter converge to one task intent. The body wraps the
workspace-authored gold task in the non-committing eval task contract
(scratch-only task work; results are reported back as JSON, never written
directly to Concepts or catalog data). A dispatch record is written to
``.memoria/eval/last-run.md``.

    python eval_dispatch.py --vault <path>             # dispatch (scheduled + on-demand)
    python eval_dispatch.py --vault <path> --dry-run   # print payloads; no intents/last-run
"""

from __future__ import annotations

import argparse
import datetime
import sys
from pathlib import Path

from memoria_vault.engine import api as engine_api
from memoria_vault.runtime.trusted_writer import OperationContext, validate_operation_context
from memoria_vault.runtime.vaultio import parse_frontmatter, strip_frontmatter, write_text_durable

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

# the non-committing eval task contract: task work never mutates Concepts/catalog data
EVAL_PREAMBLE = (
    "**Eval context (vault-eval — diagnostic, never gating).** This is a "
    "workspace-authored eval check, not real work. Do NOT write to the vault: keep "
    "any working notes in scratch and report your answer and reasoning in this "
    "payload. Score yourself against the rubric below honestly — a wrong answer "
    "reported plainly is a useful data point; a polished non-answer is not."
)

# the machine-readable result drop the scorer (eval_score.py) reads from the payload
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
    """Read current workspace-authored `type: eval-task` notes in .memoria/eval/.

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


def payload_for(task: dict, quarter: str) -> dict:
    """The eval payload for one gold task in one quarter (pure; easy to test)."""
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


def create_task_intent(payload: dict) -> str:
    """Return the local planned-intent id for one eval task."""
    return f"planned:{payload['idempotency_key']}"


def write_last_run(
    vault: Path, quarter: str, rows: list[dict], *, context: OperationContext
) -> Path:
    """Record what was dispatched when (plain markdown — untyped system infra)."""
    validate_operation_context(vault, context)
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
        f"- **Payloads:** {len(rows)}",
        "",
        "| Gold task | Workflow | Eval role | Assignee | Intent |",
        "| --- | --- | --- | --- | --- |",
    ]
    lines += [
        f"| {r['task']} | {r['workflow']} | {r['eval_role']} | {r['assignee']} | {r['intent_id']} |"
        for r in rows
    ]
    out = vault / EVAL_DIR / LAST_RUN
    write_text_durable(out, "\n".join(lines) + "\n")
    return out


def dispatch(
    vault: Path,
    dry_run: bool = False,
    today: datetime.date | None = None,
    *,
    context: OperationContext,
) -> dict:
    """Fan current local gold tasks out: one idempotent intent per task and quarter."""
    validate_operation_context(vault, context)
    quarter = quarter_of(today)
    tasks = load_gold_tasks(vault)
    rows: list[dict] = []
    for t in tasks:
        payload = payload_for(t, quarter)
        if dry_run:
            print(
                f"[dry-run] {payload['idempotency_key']} -> "
                f"{payload['assignee']}: {payload['goal']}"
            )
            intent_id = "DRY"
        else:
            intent_id = create_task_intent(payload)
        rows.append(
            {
                "task": t["id"],
                "workflow": t["workflow"],
                "eval_role": t["eval_role"],
                "assignee": payload["assignee"],
                "intent_id": intent_id,
                "idempotency_key": payload["idempotency_key"],
            }
        )
    if not dry_run:
        write_last_run(vault, quarter, rows, context=context)
    return {"quarter": quarter, "dispatched": rows, "dry_run": dry_run}


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--vault", required=True, help="vault root")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="print payloads without creating intents or writing last-run.md",
    )
    args = ap.parse_args()
    vault = Path(args.vault).expanduser()
    if not vault.is_dir():
        sys.exit(f"not a directory: {vault}")
    run = engine_api.run_operation(
        vault,
        "eval-run",
        {"dry_run": args.dry_run},
        actor="operation",
        command="eval-dispatch",
        surface="memoria-eval",
        machine="memoria-eval",
    )
    result = run.get("result") if isinstance(run.get("result"), dict) else {}
    if not run["ok"]:
        sys.exit(str(result.get("error") or "eval dispatch failed"))
    n = len(result["dispatched"])
    print(
        f"[eval] {result['quarter']}: {n} gold task(s) "
        f"{'planned (dry-run)' if args.dry_run else 'dispatched'}"
    )


if __name__ == "__main__":
    main()
