---
title: Testing
nav_order: 7
has_children: true
permalink: /testing/
topic: tests
---

# Testing

Reusable, version-agnostic test **plans** (procedures) — not the executable test code
(that's `tests/` at the repo root), and not filled-in run results. A *plan* is the steps
to validate something; a *run* is a plan executed with results recorded. **Plans live
here; runs live with their release** in `releasing/vX.Y/`, named `<plan>-run_vX.Y.md`
(e.g. `gui-test-run_0.1.0.md`) so a run is never mistaken for the reusable plan it
instantiates.

## Layout

| Path | What it is |
|---|---|
| [Test coverage matrix](coverage-matrix.md) | Keystone index: every component → coverage layer → which plan validates it → automated? → status |
| [{{Subject}} test plan](test-plan-template.md) | Copy this to author a new plan |
| [Test plans](plans/) | The reusable plans (browse the directory) |
| [Release-candidate runbook](plans/release-candidate-runbook.md) | The reusable S0–S5 + G9–G11 run sheet a release follows to gate its cut; copy its sign-off into the release's `validation-log.md` |
| [scripts/test.sh](../../scripts/test.sh) | Local **L0/L1 runner** — static checks + the L1 `pytest` suite (`tests/`, ADR-44). Run `scripts/test.sh all` before pushing; it mirrors the `lint` + `python-selftest` CI jobs. |

## Why plans and runs stay separate

Plans are **version-agnostic** and shared across every release; runs are
**version-specific** records of one cut. Merging them would tie reusable procedures
to a single version. So: reusable procedure → `testing/plans/`; completed run +
sign-off → `releasing/vX.Y/`.

## Coverage layers and gates

- **Layers (L0–L5)** — what *kind* of coverage: L0 static, L1 self-tests, L2 agent
  wiring, L3 GUI/dashboards, L4 end-to-end lifecycle, L5 output quality.
- **Stages (S0–S5)** and **Gates (G1–G11)** — release-readiness checkpoints; their
  **state** lives in the per-release **"Release vX.Y" tracking issue** (a gate checklist — the Tier-2 model), not in this folder and not in the release plan (which holds only the prose + gate *definitions*).

## Run order

```
headless ─▶ installer ─▶ cli ─┐
                        gui ─┴─▶ e2e ─▶ g9-spine ─▶ g10-ingest
```

`headless` (static + Python self-tests, CI-enforced) must be green first; `installer`
stands up a throwaway vault; `cli` and `gui` validate the wired system; `e2e` runs one
source through the full lifecycle; `g9`/`g10` prove the deterministic spine and ingest
value-loop. Per-release orchestration + sign-off: the [Release-candidate runbook](plans/release-candidate-runbook.md) — copy its sign-off template into the release's `validation-log.md`.

## Adding or changing a plan

Copy `test-plan-template.md`, keep the shared shape (preconditions → numbered
Parts/steps → results table → explicit green criteria), and add a row to
`coverage-matrix.md` so the component → plan mapping stays complete.
