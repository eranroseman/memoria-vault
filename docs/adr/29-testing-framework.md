---
topic: decisions
id: 29
title: A layered testing framework, not a pile of plans
nav_exclude: true
status: accepted
date_proposed: 2026-06-02
date_resolved: 2026-06-02
assumes: []
supersedes: []
superseded_by: []
---

# ADR-29: A layered testing framework

> **Amended by [ADR-44](44-tests-in-pytest-tree.md):** L1 component tests now live in a
> repo-side `pytest` tree (`tests/`), not inline `--self-test` blocks. The pyramid
> and disciplines below are unchanged; only L1's hosting moved.
>
> **Amended 2026-06-23:** the release process is now described as five promotion
> gates. The historical L0-L5 labels remain coverage aliases; humans and scripts
> use Source, Package, Runtime, Product, and Release gates.
>
> **Amended 2026-06-28:** testing procedure is gate-first. The former
> tool-specific plans were collapsed into Source, Package, Runtime, Product,
> Release, Manual GUI, and Failure Recovery gates, with command catalogs left in
> Reference.
>
> **Amended 2026-06-29:** Runtime Gate may include release-specific deterministic
> runtime-cycle checks before the live Hermes smoke. For alpha.11,
> `scripts/verify runtime` runs `tests/test_alpha11_cycle.py` before
> `scripts/test-l2.sh`.
>
> **Amended 2026-06-29:** the internal testing process folder was retired. Human
> contributor guidance lives in
> [CONTRIBUTING.md](https://github.com/eranroseman/memoria-vault/blob/main/CONTRIBUTING.md);
> reusable agent procedure lives in
> [verify-change.md](https://github.com/eranroseman/memoria-vault/blob/main/.agents/playbooks/verify-change.md).

## Context

Memoria had tool-specific test plans, but the real release question is gate
confidence: what must be true before the candidate can move from Source to
Package to Runtime to Product to Release? Three problems followed from the old
shape: coverage was **implicit**, gaps were **invisible** until hit, and plans
duplicated command catalogs that belonged in Reference. An assessment also
surfaced uncovered areas: installer end-to-end, recovery/failure modes,
security/adversarial checks, performance/scale, deployment modes, cross-layer
product workflows, and — by design — agent *output quality*.

## Decision

Adopt a **promotion-gated test framework**: cheap checks run first and often,
expensive checks run only when their evidence matters, and every release promotes
from source to package to runtime to product acceptance to cut readiness. The
`scripts/verify` modes own the executable gate front doors, `CONTRIBUTING.md`
owns the human summary, and the verify-change playbook owns reusable procedure.

**Promotion gates**

| Gate | Proves | Primary command / evidence | Trigger |
| --- | --- | --- | --- |
| **Source** | the repo is internally coherent: format, lint, schema, docs, generated-file drift, secrets/provenance, and changed-code tests | `scripts/verify pr` | every PR |
| **Package** | the repo can assemble a valid disposable Memoria vault and replay the model-free lifecycle | `scripts/verify package` | vault/package-related PRs, nightly, release candidate |
| **Runtime** | release-specific runtime cycles plus Hermes, MCP, policy gates, and local service boundaries work with a disposable runtime | `scripts/verify runtime` | nightly, runtime-related PRs when available, release candidate |
| **Product** | Memoria's user workflows produce the expected artifacts and human-visible surfaces render | Product Gate evidence | release candidate |
| **Release** | the candidate is ready to cut: fresh-clone evidence, docs, blockers, versioning, close-out, and notes are ready | release issue + release-please evidence | formal release / checkpoint close |

**Coverage aliases**

| Layer | Covers | Plan / owner | Trigger |
| --- | --- | --- | --- |
| **L0 Static & schema** | required source checks + dashboard/telemetry schema-drift | `scripts/verify pr` | every commit (CI) |
| **L1 Component** | `pytest tests/` (gate, hook, board, metrics, ingest/verify MCP, detectors, ingest spine, repo tooling) — ADR-44 | `scripts/test.sh l1` via Source Gate | every commit (CI) |
| **L2 Wiring / contract** | policy gate, representative CLI behavior classes, board/profile/skills/cron, architecture invariants | `scripts/verify runtime` | per release (cheap model, disposable vault) |
| **L3 System integration** | plugins, REST bridge, dashboards render, Zotero to bib, Agent Client | verify-change manual GUI procedure | per release |
| **L4 Golden-path E2E** | one full product trace across runtime, ingest, review, telemetry, and GUI | release issue evidence | per release |
| **L5 Quality / eval** | agent *output* quality (gold tasks, scored) | [ADR-11](11-vault-eval-maintenance.md) vault-eval | per release / model swap |
| **Cross-cutting** | Installer clean-install · Recovery · Security · Performance · Deployment | `scripts/verify package` + verify-change failure/recovery procedure | on relevant change |

**Disciplines**

1. **Gate front doors stay explicit.** `scripts/verify` maps each promotion gate to executable evidence; `CONTRIBUTING.md` and the verify-change playbook explain when to use each gate.
2. **Determinism.** Below L5, assert *artifact shape and gate decision*, never prose quality. Output quality is L5's job alone.
3. **Drift control.** `status_doctor.py`, `docs_doctor.py`, and `agents_doctor.py` keep stale release/testing paths, broken links, and generated agent references from rotting silently.
4. **Explicit evidence homes.** Automated evidence lives in `scripts/verify` bundles and CI; product/manual/release evidence lives in the release parent issue and sub-issues.

Reusable testing procedure lives in the verify-change playbook; release-specific
procedure lives in the release playbook.

## Why

- The substrate of testing is *which behaviour is asserted where* — the same reason the memory model is scoped substrates ([ADR-23](23-scoped-memory-substrates.md)). Without explicit gates, coverage erodes and nobody notices.
- The pyramid pushes coverage to the cheapest layer that can assert it: a `--self-test` on every commit beats a manual GUI step per release.
- Separating wiring (L0–L4) from quality (L5) keeps fast deterministic checks honest and quarantines the slow, judgement-heavy eval where it belongs.

## Consequences

- The retired testing matrix and gate-plan folder are no longer repository artifacts. The eval layer (L5) is owned by ADR-11 and ships its gold tasks separately under `system/eval/`.
- A release is "tested" when the required `scripts/verify` gates are green and the required manual/product evidence is present in the release issue trail.
- Adding a test surface means wiring it into the appropriate gate or documenting the manual evidence in the verify-change/release playbooks — not inventing an unindexed plan.

## Current implementation mapping

The historical L0-L5 names remain coverage aliases, but the reader-facing testing
model now names the behavior each gate proves:

| Promotion gate | Behavior aliases / historical layer |
| --- | --- |
| Source | `static-contract` L0 + `component` L1 |
| Package | `vault-assembly` + `workflow-replay` |
| Runtime | release-specific deterministic runtime cycles + `runtime-integration` L2b/L3 live Hermes, MCP, local services |
| Product | golden path, quality evals, GUI/Bases/dashboard acceptance, G9-G11 |
| Release | S0-S5 + G-gate release evidence, blocker/doc/version close-out |

This is an aliasing migration, not a required-check rename. CI status-check names stay
stable until branch protection and `ruleset-doctor` are updated deliberately.

## L2 implementation note

L2 ("wiring / contract") splits at the **model boundary**, and the two halves belong at different costs:

- **L2a — policy-gate contract (hermetic).** The gate is pure Python (stable entrypoint `policy_mcp.py`, split core `memoria_vault.runtime.policy`), so every lane's allow / deny / dry_run contract is assertable with **no model, Hermes, or Obsidian**. It is already an L1 `--self-test`; folding write-wall coverage for **all seven lanes** into it (Phase 1, [#73](https://github.com/eranroseman/memoria-vault/pull/73)) pushes the policy-gate half of L2 down to per-commit CI — the cheapest layer that can assert it (Discipline 2 + the pyramid).
- **L2b — agent wiring (runtime-bound).** Whether `hermes -p <profile> chat -q -s <cmd>` actually dispatches, routes through the *live* gate, and produces the expected write-boundary outcome needs the runtime + a cheap model + the Obsidian write path. Assert file presence/absence and the audit row, never prose.

**Driver (resolved).** Hermes ships a scripted one-shot: `hermes -z "<prompt>"` (final text only, clean stdout/stderr) and `hermes chat -q` (same, but tool calls in the transcript — what L2b wants, to observe the write + the gate call). ACP is interactive/editor-only — **not** the automation path.

**Backend (resolved).** L2b does **not** need Obsidian. In production the 5 non-code lanes write only through the `obsidian` MCP → Local REST API (`file` is absent from their positive `platform_toolsets`), but the gate is **transport-agnostic**: `policy_hook.classify` keys on the base tool-name + path at the `pre_tool_call` plugin layer ([ADR-28](28-write-gate-as-plugin.md)), gating `obsidian_*` and `file` `write_file`/`patch` identically — the REST transport itself is L3's contract (matrix #15), not L2's. So:
- **Option B (chosen for unattended).** A filesystem-backed `obsidian` MCP shim with the same tool names (`obsidian_append_content`/`patch_content`/`put_content`). Skills call the same tools, the gate fires unchanged, and allowed writes land on disk — no GUI, runs anywhere. The ADR-28 task_id objection to a wrapper MCP doesn't apply: the gate plugin still supplies task_id; the shim only executes the write.
- **Option A (production-faithful variant).** Headless Obsidian (`xvfb-run`) on a self-hosted runner — exercises the real REST path, but heavy/flaky and overlaps L3 #15, so it doesn't gate L2b.
- *(Rejected: re-enabling the `file` toolset — Memoria skills emit `obsidian_*`, so they'd break without an obsidian server.)*

**Attended vs unattended — split by slice, not all-or-nothing.** L2a is unattended already (#73). ADR-80's `workflow-replay` now covers the model-free cassette slice of the deterministic L2-L4 path, but it does **not** replace L2b's live Hermes dispatch signal. For L2b, `scripts/test-l2.sh` implements the unattended Option-B smoke core: a disposable vault, temporary `HERMES_HOME`, filesystem-backed `obsidian` MCP shim, the real policy-gate plugin, a `hermes chat -q` dispatch through a local OpenAI-compatible endpoint, and policy-deny/audit assertions for a direct Obsidian MCP write. By default it starts a deterministic local smoke endpoint so the wiring proof is stable; set `MEMORIA_L2_USE_SMOKE_MODEL=0` to exercise a real cheap/local model endpoint. It remains opt-in/manual or nightly rather than required PR CI. Keep the Product Gate and Manual GUI checks attended per release — automating the marginal cases (Zotero state, dashboard rendering, prose-adjacent judgment) costs the most and benefits the least, and a watching human catches the un-asserted (loops, near-miss shapes, the silent-pass class).

**Phasing.** (1) gate-contract into `--self-test` — **done** (#73); (2) backend + driver — **resolved** (Option B; `hermes -z`/`chat -q`); (3) opt-in live smoke — **shipped as `scripts/test-l2.sh`** ([#688](https://github.com/eranroseman/memoria-vault/issues/688)), nightly/manual, not PR-blocking. `workflow-replay` remains the automated model-free evidence, while `scripts/test-l2.sh` supplies the live model/Hermes dispatch signal when runtime prerequisites are available. Runtime Gate owns the live wiring plan.

## Alternatives considered

**Keep ad-hoc plans (status quo).** Rejected: it's how the gaps and drift accrued — coverage is implicit and unmonitored.

**One exhaustive suite.** Rejected: a single mega-plan is unmaintainable and ignores that different surfaces need different cadences (per-commit vs per-release vs per-model-swap). The pyramid matches cadence to cost.
