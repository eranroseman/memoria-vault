---
topic: tests
title: Verification matrix
status: stable
parent: Testing
nav_order: 10
---

# Verification Matrix

One row per assurance. The owning source is the linked gate plan; reference docs
own command catalogs and implementation detail.

**Status:** covered, partial, or gap.

| # | Assurance | Gate | Evidence | Automated | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Source contracts pass: Python tests, lint, docs, links, generated refs, schema drift, provenance, syntax. | [Source](plans/source-gate.md) | `scripts/verify pr` summary plus CI required checks. | yes | covered |
| 2 | Policy decisions are unit-tested for allow, deny, dry-run, fail-closed, lane scope, and audit pairing. | [Source](plans/source-gate.md) | `tests/test_policy_mcp.py`, `tests/test_policy_hook.py`, policy completeness tests. | yes | covered |
| 3 | A disposable vault assembles with hooks, profiles, bundled plugins, CSS snippets, and no forbidden workflow writes. | [Package](plans/package-gate.md) | `scripts/verify package` / `scripts/e2e-smoke.sh`. | yes | covered |
| 4 | Offline workflow replay exercises the deterministic lifecycle without live model or GUI dependencies. | [Package](plans/package-gate.md) | ADR-80 Phase 1 cassette replay in the package evidence bundle. | yes | covered |
| 5 | Fresh install and re-run are idempotent on a throwaway vault. | [Package](plans/package-gate.md), [Release](plans/release-gate.md) | Dry-run plus real install evidence. | partial | partial |
| 6 | The alpha.11 worker cycle runs, and Hermes runtime, gateway, cron, profile registry, model endpoint, and MCP servers are live. | [Runtime](plans/runtime-gate.md) | `scripts/verify runtime` runs Source, Package, the deterministic alpha.11 cycle, then the live Hermes smoke; manual S4 checks cover attended service state. | partial | partial |
| 7 | Obsidian bridge writes through verified HTTPS and policy gate enforcement works in `-z`, gateway, and cron modes. | [Runtime](plans/runtime-gate.md) | Allowed/denied write evidence and `hermes_contract_doctor.py`. | partial | covered |
| 8 | Product workflow produces value: dispatch spine, ingest, classification proposal, review handoff, and review close. | [Product](plans/product-gate.md) | One real paper run and review evidence in the release issue. | no | covered |
| 9 | Product surfaces render: Obsidian plugins, Bases, dashboards, spaces, Zotero, and Agent Client. | [Manual GUI](plans/manual-gui-checks.md) | Completed GUI checklist. | no | covered |
| 10 | Telemetry emits from live activity: board state, transitions, audit, lint findings, cost, attention, and triage. | [Product](plans/product-gate.md) | JSONL row checks after live workflow. | partial | partial |
| 11 | Failure and recovery paths hold: denied writes leave no file, MCP-down fails closed, retry/reconcile works, dry-run is clean. | [Failure Recovery](plans/failure-recovery-checks.md) | Manual adversarial checks plus existing unit tests. | partial | partial |
| 12 | Agent output quality is evaluated against gold tasks, not inferred from wiring success. | [Product](plans/product-gate.md) | Vault eval evidence. | no | gap |
| 13 | Release candidate has no blocked release work, published docs links pass when required, and the formal-release or internal-checkpoint path is recorded. | [Release](plans/release-gate.md) | Release issue, live docs link check when publishing, release-please PR for formal releases or validation-log/checkpoint close-out for internal checkpoints. | partial | covered |

## Open Gaps

1. Product quality eval remains the main gap; wiring success is not quality.
2. Full clean-install evidence is manual until a stable self-hosted runner exists.
3. Failure/recovery checks need periodic attended runs, not just unit tests.
4. Performance and deployment-mode checks should be added only when they become
   release criteria.
