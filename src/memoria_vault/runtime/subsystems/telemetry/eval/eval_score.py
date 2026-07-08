#!/usr/bin/env python3
"""Deterministic vault-eval scorer: diagnostic, never gating.

Closes the loop ``eval_dispatch.py`` opens: where the dispatcher fans the gold
set out as one local eval task per gold item, this operation reads the **reported
results** and turns them into machine scores — zero-LLM, report-only, the same
deterministic detector-over-the-vault shape as the dispatcher.

The non-committing result contract: an eval run never writes the vault
— it ends its report with one fenced ``json`` block::

    ```json
    {
      "vault_eval": "result",
      "task": "<gold-task id, the note stem>",
      "quarter": "<the quarter in the card title, e.g. 2026-Q2>",
      "retrieved": ["citekey", "..."],   // ranked results, best first (find tasks)
      "cited": ["citekey", "..."],       // citekeys offered as evidence
      "claims": ["note-stem", "..."],    // claim notes used or produced
      "self_score": 1.0                  // the rubric self-score from the card
    }
    ```

``retrieved`` / ``cited`` / ``claims`` are each optional — an eval role reports the
fields its workflow produces and omits the rest. The scorer reads a local JSON
export passed with ``--from-json`` and computes, per task, only what its result
makes computable — **no fake scores**; a task with no result block is reported
``unscored``:

- ``recall_at_k``  — fraction of the task's gold citekeys (frontmatter
  ``references``) present in the top-*k* of ``retrieved`` (default k=3, the
  rubric's "top 3" window).
- ``support_rate`` — fraction of ``cited`` citekeys resolving to a real SQLite
  catalog Work row (``work_id`` or ``citekey``).
- ``fama_clean``   — 1.0 if no note in ``claims`` is superseded, else 0.0
  (the FAMA check; same classification as the Linter's
  ``fama_exposure`` detector — a parity test guards it). Higher is better,
  like every other metric.
- ``self_score``   — recorded verbatim per task, never aggregated: it is the
  agent's own rubric verdict, kept for comparison, not trusted as a metric.

One JSONL line per scoring run appends to ``system/metrics/eval/runs.jsonl``
(timestamp, quarter, per-task and aggregate scores) — the eval-trend dashboard
renders the trend. When a quarter has produced no result blocks at all, the
scorer prints that and appends nothing (an empty run is noise, not data).

    python eval_score.py --vault <path> --from-json results.json
    python eval_score.py --vault <path> --quarter previous --from-json results.json
    python eval_score.py --vault <path> --quarter 2026-Q2 --from-json results.json
    python eval_score.py --vault <path> --from-json cards.json --dry-run
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.jsonl import append_jsonl
from memoria_vault.runtime.subsystems.telemetry.eval import (
    eval_dispatch,  # sibling: gold-set loader, frontmatter parser, quarter_of
)

METRICS_RELDIR = "system/metrics/eval"
RUNS_LOG = "runs.jsonl"
DEFAULT_K = 3  # the gold rubrics score a "top 3" window

_FENCED_JSON = re.compile(r"```(?:json)?\s*\n(\{.*?\})\s*```", re.S)


def catalog_citekeys(vault: Path) -> set[str]:
    """Every citekey/source id the SQLite catalog resolves."""
    keys: set[str] = set()
    for source in state.catalog_sources(vault, checked_only=False):
        for field in ("citekey", "work_id"):
            value = source.get(field)
            if value:
                keys.add(str(value))
    return keys


def superseded_claims(vault: Path) -> set[str]:
    """Claim-bearing note stems that are superseded, mirroring fama_exposure."""
    out: set[str] = set()
    for p in (vault / "notes").glob("*.md"):
        fm = eval_dispatch.parse_frontmatter(p.read_text(encoding="utf-8"))
        sup = fm.get("superseded_by")
        status = str(fm.get("status", "")).strip()
        if status == "superseded" or sup not in (None, "", [], "[]"):
            out.add(p.stem)
    return out


def load_cards(from_json: Path) -> list[dict]:
    """Read local eval result payloads from a JSON file."""
    raw = from_json.read_text(encoding="utf-8")
    data = json.loads(raw)
    cards = data.get("tasks", data) if isinstance(data, dict) else data
    return [c for c in cards if isinstance(c, dict)]


def _card_texts(card: dict) -> list[str]:
    """Every text field a worker's report can land in, oldest first: run
    summaries, then the metadata/summary fallbacks board_export.py also reads."""
    texts: list[str] = []
    for r in card.get("runs") or []:
        if isinstance(r, dict) and r.get("summary"):
            texts.append(str(r["summary"]))
    md = card.get("metadata")
    if isinstance(md, str):
        try:
            md = json.loads(md)
        except json.JSONDecodeError:
            md = {}
    if isinstance(md, dict) and md.get("summary"):
        texts.append(str(md["summary"]))
    if card.get("summary"):
        texts.append(str(card["summary"]))
    return texts


def extract_results(cards: list[dict], quarter: str) -> dict[str, dict]:
    """task id -> its result block for `quarter`. Scans every card text for
    fenced json blocks marked `"vault_eval": "result"`; the newest block per
    task wins (a re-run inside the quarter supersedes the earlier report)."""
    out: dict[str, dict] = {}
    for card in cards:
        for text in _card_texts(card):
            for m in _FENCED_JSON.finditer(text):
                try:
                    obj = json.loads(m.group(1))
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict) or obj.get("vault_eval") != "result":
                    continue
                if obj.get("quarter") != quarter or not obj.get("task"):
                    continue
                out[str(obj["task"])] = obj
    return out


def _str_list(result: dict, key: str) -> list[str] | None:
    """The result's `key` as a list of strings, or None when absent/malformed."""
    v = result.get(key)
    if not isinstance(v, list):
        return None
    return [str(x) for x in v]


def score_task(
    task: dict, result: dict, catalog: set[str], superseded: set[str], k: int = DEFAULT_K
) -> dict:
    """Deterministic metrics for one gold task from its result block."""
    metrics: dict[str, float] = {}
    gold = [str(c) for c in task.get("references") or []]
    retrieved = _str_list(result, "retrieved")
    if retrieved is not None and gold:
        hits = sum(1 for c in gold if c in retrieved[:k])
        metrics["recall_at_k"] = round(hits / len(gold), 3)
    cited = _str_list(result, "cited")
    if cited:  # an empty citation list scores nothing — there is no evidence to rate
        metrics["support_rate"] = round(sum(1 for c in cited if c in catalog) / len(cited), 3)
    claims = _str_list(result, "claims")
    if claims is not None:  # [] is a positive assertion: no claims used -> clean
        exposed = sorted(set(claims) & superseded)
        metrics["fama_clean"] = 0.0 if exposed else 1.0
        if exposed:
            metrics["fama_exposed"] = exposed  # name the offenders, like the Linter does
    return metrics


def score_run(vault: Path, cards: list[dict], quarter: str, k: int = DEFAULT_K) -> dict:
    """Score one quarter's eval run: per-task records + the aggregate."""
    catalog = catalog_citekeys(vault)
    superseded = superseded_claims(vault)
    results = extract_results(cards, quarter)
    tasks_out: list[dict] = []
    sums: dict[str, list[float]] = {}
    counts = {"scored": 0, "reported": 0, "unscored": 0}
    for task in eval_dispatch.load_gold_tasks(vault):
        result = results.get(task["id"])
        if result is None:
            counts["unscored"] += 1
            tasks_out.append(
                {
                    "task": task["id"],
                    "workflow": task["workflow"],
                    "eval_role": task["eval_role"],
                    "status": "unscored",
                }
            )
            continue
        metrics = score_task(task, result, catalog, superseded, k=k)
        row: dict = {
            "task": task["id"],
            "workflow": task["workflow"],
            "eval_role": task["eval_role"],
        }
        numeric = {m: v for m, v in metrics.items() if isinstance(v, (int, float))}
        if numeric:
            counts["scored"] += 1
            row["status"] = "scored"
            row["metrics"] = metrics
            for m, v in numeric.items():
                sums.setdefault(m, []).append(float(v))
        else:  # a result that exposes nothing computable is reported, not faked
            counts["reported"] += 1
            row["status"] = "reported"
        if isinstance(result.get("self_score"), (int, float)):
            row["self_score"] = result["self_score"]
        tasks_out.append(row)
    aggregate: dict = {
        m: {"mean": round(sum(vs) / len(vs), 3), "n": len(vs)} for m, vs in sorted(sums.items())
    }
    aggregate |= {
        "tasks_total": len(tasks_out),
        "tasks_scored": counts["scored"],
        "tasks_reported": counts["reported"],
        "tasks_unscored": counts["unscored"],
    }
    now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "timestamp": now,
        "quarter": quarter,
        "k": k,
        "tasks": tasks_out,
        "aggregate": aggregate,
    }


def append_run(vault: Path, run: dict) -> Path:
    """Append one JSONL line to system/metrics/eval/runs.jsonl (append-only;
    the dashboard trends on the newest line per quarter)."""
    out = vault / METRICS_RELDIR / RUNS_LOG
    append_jsonl(out, [run])
    return out


def resolve_quarter(spec: str, today: datetime.date | None = None) -> str:
    """'current' | 'previous' | an explicit 'YYYY-Qn' -> the quarter string."""
    if spec == "current":
        return eval_dispatch.quarter_of(today)
    if spec == "previous":
        d = today or datetime.date.today()
        first_month = ((d.month - 1) // 3) * 3 + 1
        prev_end = datetime.date(d.year, first_month, 1) - datetime.timedelta(days=1)
        return eval_dispatch.quarter_of(prev_end)
    if not re.fullmatch(r"\d{4}-Q[1-4]", spec):
        sys.exit(f"[eval-score] bad --quarter {spec!r} (use current, previous, or YYYY-Qn)")
    return spec


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--vault", required=True, help="vault root")
    ap.add_argument(
        "--quarter",
        default="current",
        help="quarter to score: current (default), previous, or YYYY-Qn",
    )
    ap.add_argument(
        "--k",
        type=int,
        default=DEFAULT_K,
        help=f"recall window (default {DEFAULT_K}, the rubrics' top-3)",
    )
    ap.add_argument(
        "--from-json",
        type=Path,
        required=True,
        help="read eval result payloads from a JSON file",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="print the run record without appending to the metrics log",
    )
    args = ap.parse_args()
    vault = Path(args.vault).expanduser()
    if not vault.is_dir():
        sys.exit(f"not a directory: {vault}")
    quarter = resolve_quarter(args.quarter)
    cards = load_cards(args.from_json)
    run = score_run(vault, cards, quarter, k=args.k)
    agg = run["aggregate"]
    if agg["tasks_scored"] == 0 and agg["tasks_reported"] == 0:
        print(
            f"[eval-score] {quarter}: no result blocks on the board — nothing scored, log untouched"
        )
        return
    if args.dry_run:
        print(json.dumps(run, indent=2, ensure_ascii=False))
        return
    out = append_run(vault, run)
    print(
        f"[eval-score] {quarter}: {agg['tasks_scored']} scored, "
        f"{agg['tasks_reported']} reported, {agg['tasks_unscored']} unscored "
        f"-> {out}"
    )


if __name__ == "__main__":
    main()
