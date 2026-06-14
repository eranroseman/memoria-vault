---
title: Vault eval
parent: Reference
---

# Vault eval

`vault-eval` ([ADR-11](../adr/11-vault-eval-maintenance.md)) is Memoria's system-level evaluation: a small, hand-curated **gold set** per workflow that measures whether the *deployed system* finds, extracts, links, and verifies correctly *on this vault*. It reuses existing machinery (board dispatch, the lane → profile map, the Linter's schema and broken-link checks, the golden copy), and its verdict is diagnostic, not gating — a dip informs the PI but does not pause scheduled work. The rationale for both choices is in [ADR-11](../adr/11-vault-eval-maintenance.md).

---

## The gold set

Gold tasks live in `system/eval/` as typed notes — `type: eval-task`, schema `src/.memoria/schemas/types/eval-task.yaml`. Each is self-contained: an `## Input`, an `## Expected behavior`, and a `## Scoring rubric` section, so a lane can run and score it with nothing but the card.

| Field | Kind | Meaning |
| --- | --- | --- |
| `type` | `literal:eval-task` | — |
| `title` | str | The card title fragment. |
| `lifecycle` | `proposed → current → archived` | Only `current` tasks dispatch. |
| `workflow` | str | The capability under test (`find` · `extract` · `link` · `verify` · …). |
| `lane` | enum | The board lane the eval card routes to: `catalog` · `extract` · `link` · `map` · `draft` · `verify` · `code` ([ADR-48](../adr/48-copi-and-agent-consolidation.md)). |
| `references` | list (optional) | Citekeys the task presupposes in the catalog. |
| `created` | date (optional) | — |

The shipped set (nine tasks) references well-known papers — the Transformer, BERT, ResNet, Adam, Dropout — so it works on any vault once those papers are ingested:

| Workflow | Lane | Gold tasks |
| --- | --- | --- |
| `find` | `catalog` (Librarian) | locate the Transformer paper; resolve a paraphrase to the ResNet paper |
| `extract` | `extract` (Librarian) | claim stubs from the Transformer paper; Adam's exact default hyperparameters |
| `link` | `link` (Librarian) | propose BERT builds-on Transformer; *decline* a strong dropout↔ResNet edge (negative control) |
| `verify` | `verify` (Peer-reviewer) | a supported BLEU figure (positive control); a contradicted positional-encoding claim; a BERT-Base/Large parameter swap |

Like patterns, eval tasks are authored directly — the files *are* the instances, no template. They are golden-copied ([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)), schema-checked by the Linter and the pre-commit gate, and a gold task whose wikilinked target no longer resolves surfaces as a broken-reference finding — gold-set rot is caught by machinery already running.

---

## Dispatch

`src/.memoria/engines/sweeps/eval_dispatch.py` — a sweeps-shaped engine: deterministic, no-LLM, enqueues idempotent cards and lets the board provide serialization and dedup ([ADR-30](../adr/30-deterministic-ingest-pipeline.md) discipline).

- One `hermes kanban create` per `lifecycle: current` gold task, assigned to the lane's owning profile (the same lane → profile map as the co-PI's `tasks_mcp.py`; a test guards the parity).
- **Idempotency key per (task, quarter):** `eval:<task-id>:<quarter>` — the quarterly cron and any on-demand re-runs inside a quarter converge to one card per task; a new quarter re-opens the window.
- The card body wraps the task in the **non-committing eval contract**: scratch-only writes, results reported on the card — a run never mutates the vault.
- The dispatch record is written to `system/eval/last-run.md` (plain markdown, overwritten each run).

```sh
python .memoria/engines/sweeps/eval_dispatch.py --vault <vault>            # dispatch
python .memoria/engines/sweeps/eval_dispatch.py --vault <vault> --dry-run  # print, create nothing
```

## Scoring

`src/.memoria/engines/sweeps/eval_score.py` — the deterministic scorer (zero-LLM, report-only). It closes the loop the dispatcher opens, turning each quarter's run into machine scores.

**The result contract.** A lane never writes the vault; it ends its card report with one fenced `json` block (the card body shows the exact template, pre-filled with the task id and quarter):

```json
{
  "vault_eval": "result",
  "task": "<gold-task id>",
  "quarter": "<e.g. 2026-Q2>",
  "retrieved": ["<citekey>", "..."],
  "cited": ["<citekey>", "..."],
  "claims": ["<claim-note-stem>", "..."],
  "self_score": 1.0
}
```

`retrieved` (ranked results, best first), `cited` (citekeys offered as evidence), and `claims` (claim notes used or produced; `[]` = none) are each optional — a lane reports the fields its workflow produces. The scorer reads the cards via `hermes kanban list --json` (`--from-json <file>` offline, the `board_export.py` pattern) and computes per task only what the result makes computable — **no fake scores**; a task with no result block is reported `unscored`, and a result with no computable field is `reported`.

| Metric | 0–1, higher is better | Computed when |
| --- | --- | --- |
| `recall_at_k` | Fraction of the task's gold citekeys (frontmatter `references`) in the top-*k* of `retrieved` (default k=3, the rubrics' "top 3" window; `--k`). | `retrieved` reported and the task has `references`. |
| `support_rate` | Fraction of `cited` citekeys resolving to a real catalog record (note stem or `citekey:` frontmatter under `catalog/`). | `cited` reported, non-empty. |
| `fama_clean` | 1.0 if no note in `claims` is a superseded/archived claim, else 0.0 — the FAMA check, same classification as the Linter's `fama-exposure` detector (a test guards the parity); offenders are named in `fama_exposed`. | `claims` reported (`[]` counts: no claims used → clean). |

The lane's rubric `self_score` is recorded per task for comparison but never aggregated — only the machine metrics trend.

**The log.** Each scoring run appends one JSONL line to `system/metrics/eval/runs.jsonl` — timestamp, quarter, k, per-task records, and per-metric aggregates (`mean` + `n`, plus scored/reported/unscored counts). When a quarter produced no result blocks at all, nothing is appended. The **eval-trend dashboard** (`system/dashboards/eval-trend.md`) renders the newest line per quarter as the trend, plus the latest run's per-task breakdown — see [Dashboards](dashboards.md).

```sh
python .memoria/engines/sweeps/eval_score.py --vault <vault>                       # score the current quarter
python .memoria/engines/sweeps/eval_score.py --vault <vault> --quarter previous    # what the cron runs
python .memoria/engines/sweeps/eval_score.py --vault <vault> --quarter 2026-Q2 --dry-run
```

## Cadence

The installer wires `memoria-eval` (`0 7 1 */3 *` — 07:00 on the first day of every third month) from the wrapper `src/.memoria/scripts/eval-cron.sh`, following the same pattern as the lint and metrics crons — see [Installer (bootstrap)](installer.md). The wrapper first **scores the previous quarter** (its cards have reported by then), then **dispatches** the new quarter's cards. On-demand runs are the same commands by hand.

---

## Related

- The decision: [ADR-11](../adr/11-vault-eval-maintenance.md)
- The lanes the cards route to: [Profile capabilities](profiles.md)
- The machinery that guards the gold set: [Linter: detectors and auto-fix](linter.md)
- The trend dashboard and metric bands: [Dashboards](dashboards.md)
- The other scheduled jobs: [Installer (bootstrap)](installer.md)
