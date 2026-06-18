---
topic: decisions
id: 29
title: A layered testing framework, not a pile of plans
status: accepted
date_proposed: 2026-06-02
date_resolved: 2026-06-02
assumes: []
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 29
---

# ADR-29: A layered testing framework

> **Amended by [ADR-44](44-tests-in-pytest-tree.md):** L1 component tests now live in a
> repo-side `pytest` tree (`tests/`), not inline `--self-test` blocks. The pyramid,
> coverage matrix, and disciplines below are unchanged; only L1's hosting moved.

## Context

Memoria has three good test plans — [headless](https://github.com/eranroseman/memoria-vault/blob/main/docs/testing/plans/headless-test-plan.md) (static + schema), [hermes-cli](https://github.com/eranroseman/memoria-vault/blob/main/docs/testing/plans/hermes-cli-test-plan.md) (agent wiring + the policy gate), and [GUI](https://github.com/eranroseman/memoria-vault/blob/main/docs/testing/plans/gui-test-plan.md) (Obsidian/Zotero/dashboards) — but no framework binding them. Three problems follow: coverage is **implicit** (nobody can answer "is component X tested?"), gaps are **invisible** until hit, and the plans **drift** from the design (e.g. the CLI plan still cited the dissolved `00-meta/04-reference/`, the GUI plan still listed a deleted root `README`). An assessment also surfaced uncovered surface: the installer end-to-end, recovery/failure-modes, security/adversarial, performance/scale, deployment modes, a cross-layer golden path, and — by design — agent *output quality*.

## Decision

Adopt a **layered test framework** — a pyramid (cheap/automated/frequent at the base, expensive/manual/rare at the top), indexed by a coverage matrix, governed by four disciplines.

**Layers**

| Layer | Covers | Plan / owner | Trigger |
| --- | --- | --- | --- |
| **L0 Static & schema** | the 5 CI checks + dashboard/telemetry schema-drift | headless | every commit (CI) |
| **L1 Component** | `pytest tests/` (gate, hook, board, metrics, ingest/verify MCP, detectors, ingest spine, repo tooling) — ADR-44 | headless §A | every commit (CI) |
| **L2 Wiring / contract** | policy gate + every agent command + board/profile/skills/cron + architecture invariants | hermes-cli | per release (cheap model, disposable vault) |
| **L3 System integration** | plugins, REST bridge, dashboards render, Zotero→bib, ACP | GUI | per release (Windows) |
| **L4 Golden-path E2E** | one full-lifecycle trace across all layers | [e2e-golden-path](https://github.com/eranroseman/memoria-vault/blob/main/docs/testing/plans/e2e-golden-path-plan.md) | per release |
| **L5 Quality / eval** | agent *output* quality (gold tasks, scored) | [ADR-11](11-vault-eval-maintenance.md) vault-eval | per release / model swap |
| **Cross-cutting** | Installer clean-install · Recovery · Security · Performance · Deployment | [installer](https://github.com/eranroseman/memoria-vault/blob/main/docs/testing/plans/installer-test-plan.md) (+ others as built) | on relevant change |

**Disciplines**

1. **Coverage matrix is the keystone.** [`coverage-matrix.md`](https://github.com/eranroseman/memoria-vault/blob/main/docs/testing/coverage-matrix.md) maps every design component → its layer/plan → automated? → release gate. Gaps are tracked, not discovered by accident.
2. **Determinism.** Below L5, assert *artifact shape and gate decision*, never prose quality. Output quality is L5's job alone.
3. **Drift control.** A check (`scripts/check_test_refs.py`) verifies every path/link a plan references resolves, so plans can't rot silently; runs in CI alongside docs-doctor.
4. **Explicit gate mapping.** Each release-plan Gate/Stage names the layer/plan that satisfies it (both directions), so "is the release tested?" is answerable from the matrix.

All plans live in [Testing](https://github.com/eranroseman/memoria-vault/tree/main/docs/testing), built from `test-plan-template.md`.

## Why

- The substrate of testing is *which behaviour is asserted where* — the same reason the memory model is scoped substrates ([ADR-23](23-scoped-memory-substrates.md)). Without an index, coverage erodes and nobody notices; the matrix makes erosion visible.
- The pyramid pushes coverage to the cheapest layer that can assert it: a `--self-test` on every commit beats a manual GUI step per release.
- Separating wiring (L0–L4) from quality (L5) keeps fast deterministic checks honest and quarantines the slow, judgement-heavy eval where it belongs.

## Consequences

- New artifacts: the coverage matrix, the installer and golden-path plans, and the drift check. The eval layer (L5) is owned by ADR-11 and ships its gold tasks separately (`99-system/eval/` is empty until then).
- The release plan's gates reference the matrix; a release is "tested" when its required layers are green per the matrix.
- Adding a test surface means adding a row to the matrix and pointing it at a layer — not inventing an unindexed plan.

## Current implementation mapping

The historical L0-L5 names remain the decision vocabulary, but the reader-facing
testing model now names the behavior each layer proves:

| Behavior name | Historical layer |
| --- | --- |
| `static-contract` | L0 static, schema, docs, and repo-contract checks |
| `component` | L1 `pytest tests/` component suite |
| `vault-assembly` | installer-equivalent disposable vault build and local git/hook checks |
| `workflow-replay` | ADR-80 Phase 1 model-free cassette replay across the deterministic lifecycle |
| `runtime-integration` | L3 live Hermes, Obsidian bridge, GUI, local services, and dashboards |
| `release-acceptance` | S0-S5 + G-gate release evidence |

This is an aliasing migration, not a required-check rename. CI status-check names stay
stable until branch protection and `ruleset-doctor` are updated deliberately.

## L2 implementation note

L2 ("wiring / contract") splits at the **model boundary**, and the two halves belong at different costs:

- **L2a — policy-gate contract (hermetic).** The gate is pure Python (`policy_mcp.py`), so every lane's allow / deny / dry_run contract is assertable with **no model, Hermes, or Obsidian**. It is already an L1 `--self-test`; folding the hermes-cli §5 write-walls for **all seven lanes** into it (Phase 1, [#73](https://github.com/eranroseman/memoria-vault/pull/73)) pushes the policy-gate half of L2 down to per-commit CI — the cheapest layer that can assert it (Discipline 2 + the pyramid).
- **L2b — agent wiring (runtime-bound).** Whether `hermes -p <profile> chat -q -s <cmd>` actually dispatches, routes through the *live* gate, and lands the right artifact needs the runtime + a cheap model + the Obsidian write path. Assert artifact **shape / placement / audit row**, never prose.

**Driver (resolved).** Hermes ships a scripted one-shot: `hermes -z "<prompt>"` (final text only, clean stdout/stderr) and `hermes chat -q` (same, but tool calls in the transcript — what L2b wants, to observe the write + the gate call). ACP is interactive/editor-only — **not** the automation path.

**Backend (resolved).** L2b does **not** need Obsidian. In production the 5 non-code lanes write only through the `obsidian` MCP → Local REST API (`file` is in their `disabled_toolsets`), but the gate is **transport-agnostic**: `policy_hook.classify` keys on the base tool-name + path at the `pre_tool_call` plugin layer ([ADR-28](28-write-gate-as-plugin.md)), gating `obsidian_*` and `file` `write_file`/`patch` identically — the REST transport itself is L3's contract (matrix #15), not L2's. So:
- **Option B (chosen for unattended).** A filesystem-backed `obsidian` MCP shim with the same tool names (`obsidian_append_content`/`patch_content`/`put_content`). Skills call the same tools, the gate fires unchanged, writes land on disk — no GUI, runs anywhere. The ADR-28 task_id objection to a wrapper MCP doesn't apply: the gate plugin still supplies task_id; the shim only executes the write.
- **Option A (production-faithful variant).** Headless Obsidian (`xvfb-run`) on a self-hosted runner — exercises the real REST path, but heavy/flaky and overlaps L3 #15, so it doesn't gate L2b.
- *(Rejected: re-enabling the `file` toolset — Memoria skills emit `obsidian_*`, so they'd break without an obsidian server.)*

**Attended vs unattended — split by slice, not all-or-nothing.** L2a is unattended already (#73). For L2b, **build the unattended Option-B harness only for the smoke core** (§3 S1–S5 + one §4 case per profile) — that's the high-frequency signal a human shouldn't babysit. **Keep the full §4 matrix + the GUI/Zotero/dashboard tail attended, per release** — automating the marginal cases (Zotero state, dashboard rendering, prose-adjacent judgment) costs the most and benefits the least, and a watching human catches the un-asserted (loops, near-miss shapes, the silent-pass class). The build decision is "is the per-PR smoke signal worth one harness?" — yes while iterating on the gate/lanes/skills, deferrable if L2 only matters at release.

**Phasing.** (1) gate-contract into `--self-test` — **done** (#73); (2) backend + driver — **resolved** (Option B; `hermes -z`/`chat -q`); (3) an opt-in `scripts/test-l2.sh` smoke set on the cheap model against a disposable vault, with teardown — **nightly, not PR-blocking**. The full hermes-cli §4 matrix stays the attended plan of record.

## Alternatives considered

**Keep ad-hoc plans (status quo).** Rejected: it's how the gaps and drift accrued — coverage is implicit and unmonitored.

**One exhaustive suite.** Rejected: a single mega-plan is unmaintainable and ignores that different surfaces need different cadences (per-commit vs per-release vs per-model-swap). The pyramid matches cadence to cost.
