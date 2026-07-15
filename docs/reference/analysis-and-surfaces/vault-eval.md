---
title: Vault eval
parent: Analysis and surfaces
nav_order: 2
grand_parent: Reference
---

# Vault eval

`vault-eval` ([vault-eval as a maintenance capability](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)) is Memoria's system-level evaluation.
It can use a small, workspace-authored gold set per workflow to check whether
the deployed vault finds, extracts, links, and verifies correctly. It is
diagnostic, not gating.

---

## The gold set

Markdown gold tasks are optional workspace-authored diagnostic fixtures under
`.memoria/eval/`. The package seed ships no markdown gold tasks by default; it
ships the separate seeded-error bundle at
`.memoria/eval/alpha15-seeded-errors.json`. When a workspace adds markdown gold
tasks, they carry `type: eval-task` frontmatter for eval dispatch, but
`eval-task` is not a Concept type and has no schema under
`src/memoria_vault/product/workspace_seed/.memoria/schemas/types/`. Each fixture
is self-contained: an `## Input`, an `## Expected behavior`, and an
`## Scoring rubric` section, so a runtime eval operation can run and score it
with nothing but the file.

| Field | Kind | Meaning |
| --- | --- | --- |
| `type` | `literal:eval-task` | Diagnostic fixture marker; not a Concept schema. |
| `title` | str | The request title fragment. |
| `lifecycle` | `proposed → current → archived` | Only `current` tasks dispatch. |
| `workflow` | str | The capability under test (`find` · `extract` · `link` · `verify` · …) — this gold-task field is unrelated to the `workflow` enum on empirical events ([Empirical events](../control-and-policy/empirical-events.md#base-fields)). |
| `eval_role` | enum | Diagnostic routing bucket: `catalog` · `extract` · `link` · `map` · `verify` ([standalone engine with operations as product code, no agent tools](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)). It does not imply shipped lane packages. |
| `references` | list (optional) | Citekeys the task presupposes in the catalog. |
| `created` | date (optional) | — |

Eval tasks are authored directly: the files are the instances, not templates.
A gold task whose wikilinked target no longer resolves surfaces as a
broken-reference finding; gold-set rot is caught by machinery already running.

---

## Dispatch

`memoria eval run` /
`memoria_vault.runtime.subsystems.telemetry.eval.eval_dispatch` creates
idempotent local eval task plans. It is deterministic and no-LLM; the runtime
request queue handles serialization and deduplication ([machine judgments are layered proposals, never authorities](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)).

- One local eval task plan per workspace-authored `lifecycle: current` gold task.
- **Idempotency key per (task, quarter):** `eval:<task-id>:<quarter>` — the scheduled wrapper and any on-demand re-runs inside a quarter converge to one request per task; a new quarter re-opens the window.
- The task body wraps the task in the **non-committing eval task contract**: scratch-only task work, results reported as JSON, and no Concept or catalog writes. Dispatch itself writes `.memoria/eval/last-run.md`.
- The dispatch record is written to `.memoria/eval/last-run.md` (plain markdown, overwritten each run).

```sh
memoria eval run --workspace <vault> --json            # dispatch
memoria eval run --workspace <vault> --dry-run --json  # print, create nothing
```

## Scoring

`memoria_vault.runtime.subsystems.telemetry.eval.eval_score` is the
deterministic, report-only scorer. It turns each quarter's result payloads into
machine scores.

**The result contract.** Eval task work never writes Concepts or catalog data; it ends its report with one fenced `json` block (the task body shows the exact template, pre-filled with the task id and quarter):

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
| `support_rate` | Fraction of `cited` citekeys resolving to a real SQLite catalog Work row. | `cited` reported, non-empty. |
| `fama_clean` | 1.0 when `claims` avoids superseded claims (`status: superseded` or `superseded_by` set); 0.0 otherwise. Offenders appear in `fama_exposed`. | `claims` reported (`[]` counts: no claims used → clean). |
| `evidence_clean` | 1.0 if reported draft evidence markers resolve to catalog Works, page spans, and checked block anchors; 0.0 when any marker is unresolved or incomplete. | Draft verification or seeded-error tasks report evidence marker ids. |

The task rubric's `self_score` is recorded per task for comparison but never
aggregated - only the machine metrics trend.

`fama_clean` uses the same superseded-reuse rule as the Linter's detector; a
test guards parity with [Linter: detectors and auto-fix](linter.md#the-detectors).

**The log.** Each scoring run appends one JSONL line to `system/metrics/eval/runs.jsonl` — timestamp, quarter, k, per-task records, and per-metric aggregates (`mean` + `n`, plus scored/reported/unscored counts). When a quarter produced no result blocks at all, nothing is appended. Optional dashboard/editor views can render the newest line per quarter plus the latest run's per-task breakdown; see [Dashboards](dashboards.md).

```sh
python3 -m memoria_vault.runtime.subsystems.telemetry.eval.eval_score --vault <vault> --from-json results.json
python3 -m memoria_vault.runtime.subsystems.telemetry.eval.eval_score --vault <vault> --quarter previous --from-json results.json
python3 -m memoria_vault.runtime.subsystems.telemetry.eval.eval_score --vault <vault> --quarter 2026-Q2 --from-json results.json --dry-run
```

## Cadence

An operator-managed scheduler may call the same scoring command explicitly. The
installer does not register the schedule; see
[Installer (bootstrap)](../system/installer.md#host-scheduler-wiring). Scoring is explicit
and uses `eval_score --from-json` once result payloads exist.

---

## Related

- The decision: [vault-eval as a maintenance capability](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)
- The machinery that guards local gold tasks: [Linter: detectors and auto-fix](linter.md)
- Optional Eval trend view: [Dashboards](dashboards.md)
- Scheduler wiring boundary: [Installer (bootstrap)](../system/installer.md)
