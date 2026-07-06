---
title: Vault eval
parent: Agents and control
grand_parent: Reference
nav_order: 7
---

# Vault eval

`vault-eval` ([vault-eval as a maintenance capability](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)) is Memoria's system-level evaluation: a small, hand-curated gold set per workflow that measures whether the deployed system finds, extracts, links, and verifies correctly on this vault. It is diagnostic, not gating.

---

## The gold set

Gold tasks live in `system/eval/` as diagnostic markdown fixtures. They carry
`type: eval-task` frontmatter for eval dispatch, but `eval-task` is not an
alpha.15 Concept type and has no schema under
`vault-template/.memoria/schemas/types/`. Each fixture is self-contained: an
`## Input`, an `## Expected behavior`, and an `## Scoring rubric` section, so a
runtime eval operation can run and score it with nothing but the file.

| Field | Kind | Meaning |
| --- | --- | --- |
| `type` | `literal:eval-task` | Diagnostic fixture marker; not a Concept schema. |
| `title` | str | The request title fragment. |
| `lifecycle` | `proposed → current → archived` | Only `current` tasks dispatch. |
| `workflow` | str | The capability under test (`find` · `extract` · `link` · `verify` · …). |
| `eval_role` | enum | Diagnostic routing bucket: `catalog` · `extract` · `link` · `map` · `verify` ([standalone engine with operations as product code, no agent tools](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)). It does not imply shipped lane packages. Draft and code eval roles remain deferred. |
| `references` | list (optional) | Citekeys the task presupposes in the catalog. |
| `created` | date (optional) | — |

The shipped set (nine tasks) references well-known papers — the Transformer, BERT, ResNet, Adam, Dropout — so it works on any vault once those papers are ingested:

| Workflow | Eval role | Gold tasks |
| --- | --- | --- |
| `find` | `catalog` | locate the Transformer paper; resolve a paraphrase to the ResNet paper |
| `extract` | `extract` | claim stubs from the Transformer paper; Adam's exact default hyperparameters |
| `link` | `link` | propose BERT builds-on Transformer; *decline* a strong dropout↔ResNet edge (negative control) |
| `verify` | `verify` | a supported BLEU figure (positive control); a contradicted positional-encoding claim; a BERT-Base/Large parameter swap |

Eval tasks are authored directly — the files *are* the instances, no template.
They are shipped template files; product-file repair is package/template refresh.
A gold task whose wikilinked target no longer resolves surfaces as a
broken-reference finding; gold-set rot is caught by machinery already running.

---

## Dispatch

`memoria eval run` / `memoria_vault.runtime.subsystems.telemetry.eval.eval_dispatch` — a sweeps-shaped operation: deterministic, no-LLM, creates idempotent local eval task plans and lets the runtime request queue provide serialization and dedup ([machine judgments are layered proposals, never authorities](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)).

- One local eval task plan per `lifecycle: current` gold task.
- **Idempotency key per (task, quarter):** `eval:<task-id>:<quarter>` — the scheduled wrapper and any on-demand re-runs inside a quarter converge to one request per task; a new quarter re-opens the window.
- The task body wraps the task in the **non-committing eval contract**: scratch-only writes, results reported as JSON — a run never mutates the vault.
- The dispatch record is written to `system/eval/last-run.md` (plain markdown, overwritten each run).

```sh
memoria eval run --workspace <vault> --json            # dispatch
memoria eval run --workspace <vault> --dry-run --json  # print, create nothing
```

## Scoring

`memoria_vault.runtime.subsystems.telemetry.eval.eval_score` — the deterministic scorer (zero-LLM, report-only). It closes the loop the dispatcher opens, turning each quarter's run into machine scores.

**The result contract.** An eval run never writes the vault; it ends its report with one fenced `json` block (the task body shows the exact template, pre-filled with the task id and quarter):

```json
{
  "vault_eval": "result",
  "task": "<gold-task id>",
  "quarter": "<e.g. 2026-Q2>",
  "retrieved": ["<citekey>", "..."],
  "cited": ["<citekey>", "..."],
  "claims": ["<claim-bearing-note-stem>", "..."],
  "self_score": 1.0
}
```

`retrieved` (ranked results, best first), `cited` (citekeys offered as evidence),
and `claims` (claim-bearing notes used or produced; `[]` = none) are each
optional — a run reports the fields its workflow produces. The scorer reads a
local JSON payload via `--from-json <file>` and computes per task only what the
result makes computable — **no fake scores**; a task with no result block is
reported `unscored`, and a result with no computable field is `reported`.

| Metric | 0–1, higher is better | Computed when |
| --- | --- | --- |
| `recall_at_k` | Fraction of the task's gold citekeys (frontmatter `references`) in the top-*k* of `retrieved` (default k=3, the rubrics' "top 3" window; `--k`). | `retrieved` reported and the task has `references`. |
| `support_rate` | Fraction of `cited` citekeys resolving to a real catalog record (note stem or `citekey:` frontmatter under `catalog/`). | `cited` reported, non-empty. |
| `fama_clean` | 1.0 if no note in `claims` is a superseded/archived claim, else 0.0 — the same superseded-reuse check the Linter's detector enforces (a test guards the parity, see [Linter: detectors and auto-fix](linter.md#the-detectors)); offenders are named in `fama_exposed`. | `claims` reported (`[]` counts: no claims used → clean). |

The task rubric's `self_score` is recorded per task for comparison but never
aggregated - only the machine metrics trend.

**The log.** Each scoring run appends one JSONL line to `system/metrics/eval/runs.jsonl` — timestamp, quarter, k, per-task records, and per-metric aggregates (`mean` + `n`, plus scored/reported/unscored counts). When a quarter produced no result blocks at all, nothing is appended. The **eval-trend dashboard** (`system/dashboards/eval-trend.md`) renders the newest line per quarter as the trend, plus the latest run's per-task breakdown — see [Dashboards](dashboards.md).

```sh
python -m memoria_vault.runtime.subsystems.telemetry.eval.eval_score --vault <vault> --from-json results.json
python -m memoria_vault.runtime.subsystems.telemetry.eval.eval_score --vault <vault> --quarter previous --from-json results.json
python -m memoria_vault.runtime.subsystems.telemetry.eval.eval_score --vault <vault> --quarter 2026-Q2 --from-json results.json --dry-run
```

## Cadence

An operator-managed scheduler may call `.memoria/scripts/cron-runner.sh eval`.
The installer does not register the schedule; see
[Installer (bootstrap)](installer.md#host-scheduler-wiring). Scoring is explicit
and uses `eval_score --from-json` once result payloads exist.

---

## Related

- The decision: [vault-eval as a maintenance capability](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)
- The machinery that guards the gold set: [Linter: detectors and auto-fix](linter.md)
- The trend dashboard and metric bands: [Dashboards](dashboards.md)
- Scheduler wiring boundary: [Installer (bootstrap)](installer.md)
