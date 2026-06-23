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
| [scripts/verify](../../scripts/verify) | Stable verification front door: `pr`, `package`, `runtime`, `rc`, and `live`; writes a JSON evidence bundle. |
| [scripts/test.sh](../../scripts/test.sh) | Direct `static-contract` + `component` runner — historical L0/L1 static checks plus the `pytest` suite (`tests/`, ADR-44). Prefer `scripts/verify pr` before pushing; use this for bisection. |
| [scripts/e2e-smoke.sh](../../scripts/e2e-smoke.sh) | Offline `vault-assembly` + `workflow-replay` smoke; shell entrypoint with assertions in `scripts/e2e_smoke.py`, including the ADR-80 Phase 1 cassette replay for the model-free path. |

## Why plans and runs stay separate

Plans are **version-agnostic** and shared across every release; runs are
**version-specific** evidence for one cut. Merging them would tie reusable procedures
to a single version. So: reusable procedure -> `testing/plans/`; automated evidence
-> Actions run/artifact; manual release evidence -> the relevant gate/stage sub-issue;
curated long-lived summary -> `docs/releasing/<version>/validation-log.md` only when
the issue/Actions trail is not enough.

## Promotion gates

The reader-facing process uses promotion gates. Historical layer names remain
coverage aliases for ADRs, plans, and existing CI check names.

| Gate | Proves | Command / evidence |
| --- | --- | --- |
| Source | repo coherence: format, lint, schema, docs, generated-file drift, secrets/provenance, changed-code tests | `scripts/verify pr` |
| Package | disposable vault assembly, hooks, plugin bundle, and model-free lifecycle replay | `scripts/verify package` |
| Runtime | Hermes, MCP, policy gate, model endpoint, and local service boundaries | `scripts/verify runtime` |
| Product | golden workflows, eval quality, Obsidian/Bases/dashboard rendering, and telemetry signals | release-candidate runbook |
| Release | fresh-clone candidate, blockers, docs, versioning, notes, and close-out are ready | release issue + release-please |

Compatibility aliases:

| Behavior name | Historical coverage | Promotion gate |
| --- | --- | --- |
| `static-contract` | L0 static, schema, docs, and repo-contract checks | Source |
| `component` | L1 `pytest tests/` component suite | Source |
| `vault-assembly` | installer-equivalent disposable vault build and local git/hook checks | Package |
| `workflow-replay` | ADR-80 Phase 1 model-free cassette replay across the deterministic lifecycle | Package |
| `runtime-integration` | L3 live Hermes, Obsidian bridge, GUI, local services, and dashboards | Runtime / Product |
| `release-acceptance` | S0–S5 + G-gate release evidence | Release |

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
Source ─▶ Package ─▶ Runtime ─▶ Product ─▶ Release
```

`scripts/verify pr` runs the Source Gate. `scripts/verify package` runs Source
then Package. `scripts/verify runtime` runs Source, Package, then the opt-in live
Hermes smoke. `scripts/verify rc` runs the automated prefix for a release
candidate and then points to the manual Product and Release evidence still owed.
`scripts/verify live` runs only the live runtime smoke. Evidence is written as
`summary.json` under `/tmp/memoria-verify/` by default, or under
`--evidence-dir`.

## Adding or changing a plan

Copy `test-plan-template.md`, keep the shared shape (preconditions → numbered
Parts/steps → results table → explicit green criteria), and add a row to
`coverage-matrix.md` so the component → plan mapping stays complete.
