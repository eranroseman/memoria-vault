---
title: Testing
nav_order: 8
has_children: true
permalink: /testing/
topic: tests
---

# Testing

Reusable, version-agnostic test **plans** (procedures) — not the executable test code
(that's `tests/` at the repo root), and not routine run results. A *plan* is the
steps to validate something; a *run* is a plan executed with results recorded.
Plans live here. Routine automated run evidence lives in GitHub Actions logs and
artifacts; manual release-run state lives in the relevant release gate/stage
sub-issue. A release folder gets a `validation-log.md` only when curated evidence
is worth preserving after the GitHub trail.

## Layout

| Path | What it is |
|---|---|
| [Test coverage matrix](coverage-matrix.md) | Keystone index: every component → coverage layer → which plan validates it → automated? → status |
| [{{Subject}} test plan](test-plan-template.md) | Copy this to author a new plan |
| [Test plans](plans/) | The reusable plans (browse the directory) |
| [Release-candidate runbook](plans/release-candidate-runbook.md) | The reusable S0–S5 + G9–G11 run sheet a release follows; record state in the release gate/stage sub-issues |
| [scripts/test.sh](../../scripts/test.sh) | Local `static-contract` + `component` runner — historical L0/L1 static checks plus the `pytest` suite (`tests/`, ADR-44). Run `scripts/test.sh all` before pushing; it mirrors the `lint` + `python-selftest` CI jobs. |
| [scripts/e2e-smoke.sh](../../scripts/e2e-smoke.sh) | Offline `vault-assembly` + `workflow-replay` smoke; shell entrypoint with assertions in `scripts/e2e_smoke.py`, including the ADR-80 Phase 1 cassette replay for the model-free path. |

## Why plans and runs stay separate

Plans are **version-agnostic** and shared across every release; runs are
**version-specific** evidence for one cut. Merging them would tie reusable procedures
to a single version. So: reusable procedure -> `testing/plans/`; automated evidence
-> Actions run/artifact; manual release evidence -> the relevant gate/stage sub-issue;
curated long-lived summary -> `docs/releasing/<version>/validation-log.md` only when
the issue/Actions trail is not enough.

## Coverage model

The reader-facing test model uses behavior names; the historical layer labels remain
as compatibility aliases for ADRs, plans, and required CI checks:

| Behavior name | Historical coverage |
| --- | --- |
| `static-contract` | L0 static, schema, docs, and repo-contract checks |
| `component` | L1 `pytest tests/` component suite |
| `vault-assembly` | installer-equivalent disposable vault build and local git/hook checks |
| `workflow-replay` | ADR-80 Phase 1 model-free cassette replay across the deterministic lifecycle |
| `runtime-integration` | L3 live Hermes, Obsidian bridge, GUI, local services, and dashboards |
| `release-acceptance` | S0–S5 + G-gate release evidence |

- **Stages (S0–S5)** and **Gates (G1–G11)** — release-readiness checkpoints; their
  **state** lives in the per-release **"Release vX.Y" parent issue and sub-issues**,
  not in this folder and not in the release plan (which holds only the prose + gate
  *definitions*).

## Coverage requirements

Memoria does **not** currently enforce a global percentage gate. The requirement is
changed-code coverage: when a PR changes a doctor/governance script, add focused
positive and negative tests for every new rule; when it changes runtime behavior,
cover the success path, fail-closed/error path, idempotency, and path/schema
boundaries. Use `python -m pytest tests/ --cov=. --cov-branch` as a review aid and
treat uncovered changed branches as review findings. A hard percentage gate should
wait for a ratcheting baseline so legacy gaps do not block unrelated fixes.

## Run order

```
static-contract ─▶ component ─▶ vault-assembly ─▶ workflow-replay
                                                └▶ runtime-integration ─▶ release-acceptance
```

`static-contract` and `component` are CI-enforced first. `vault-assembly` builds a
throwaway vault, initializes git, wires hooks, and checks the local shipped config.
`workflow-replay` runs the model-free ADR-80 Phase 1 cassette through the deterministic
lifecycle. The shell-compatible smoke entrypoint delegates assertions to
`scripts/e2e_smoke.py` so the stage checks are importable and unit-covered.
`runtime-integration` is the non-PR live surface: Hermes, Obsidian bridge,
local services, GUI/Bases/dashboards, and model connectivity. `release-acceptance`
is the [Release-candidate runbook](plans/release-candidate-runbook.md); record
state/evidence in release gate/stage sub-issues and preserve only curated summaries
in `validation-log.md`.

## Adding or changing a plan

Copy `test-plan-template.md`, keep the shared shape (preconditions → numbered
Parts/steps → results table → explicit green criteria), and add a row to
`coverage-matrix.md` so the component → plan mapping stays complete.
