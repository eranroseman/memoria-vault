---
title: Testing
nav_order: 8
has_children: true
permalink: /testing/
topic: tests
---

# Testing

Testing is organized by promotion gate, not by tool. Each gate answers one
question: what confidence is needed before the candidate can move forward?

Reusable procedures live here. Run results do not. Automated evidence lives in
Actions artifacts or the `scripts/verify` evidence bundle; manual release evidence
lives in the relevant release readiness/stage issue. A release folder gets a
`validation-log.md` only when a curated summary is worth keeping.

## Gate Order

| Gate | Proves | Front door |
| --- | --- | --- |
| Source | Repo contracts, docs, schemas, Python tests, and static checks are coherent. | `scripts/verify pr` |
| Package | A disposable vault can be assembled and the offline workflow replay works. | `scripts/verify package` |
| Runtime | Release-specific runtime cycles run, and Hermes, MCP, Obsidian, model, cron, and policy boundaries work live. | `scripts/verify runtime` |
| Product | The research workflows produce reviewable value with telemetry and GUI evidence. | Manual release evidence |
| Release | Fresh-clone candidate, blockers, docs, and release/checkpoint mechanics are ready. | Release issue + release-please or checkpoint close-out |

Run gates in order:

```text
Source -> Package -> Runtime -> Product -> Release
```

## Layout

| Path | Purpose |
| --- | --- |
| [Verification matrix](verification-matrix.md) | One row per required assurance: what proves it, automation level, and evidence home. |
| [Source Gate](plans/source-gate.md) | Deterministic local and CI checks. |
| [Package Gate](plans/package-gate.md) | Disposable vault assembly and offline workflow replay. |
| [Runtime Gate](plans/runtime-gate.md) | Live Hermes/MCP/Obsidian/model/policy checks. |
| [Product Gate](plans/product-gate.md) | Ingest, review, telemetry, quality, and product workflow evidence. |
| [Manual GUI Checks](plans/manual-gui-checks.md) | Obsidian, Zotero, Bases, dashboards, and Agent Client checks. |
| [Failure Recovery Checks](plans/failure-recovery-checks.md) | Deny paths, MCP-down, retry, dry-run, and recovery behavior. |
| [Release Gate](plans/release-gate.md) | Fresh-clone release sequencing and cut checks. |
| [Test plan template](templates/test-plan-template.md) | Use only when a new gate needs a reusable sub-plan. |

## Evidence Rules

- Plans describe reusable procedure, not state.
- A gate is green only when its pass criteria are observed on the candidate under
  test.
- Manual release state is recorded in the release parent issue and sub-issues,
  not in this folder.
- Current command catalogs stay in Reference. Testing docs name only the command
  needed to prove an assurance.

## Adding Coverage

Add a row to [Verification matrix](verification-matrix.md). If an existing gate
can prove it, update that gate. Add a new plan only when the assurance needs a
new reusable procedure.
