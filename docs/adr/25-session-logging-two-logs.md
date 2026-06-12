---
topic: decisions
id: 25
title: Two separate session logs — hash-paired audit vs. narrative summaries
status: deferred
nav_exclude: true
date_proposed: 2026-06-01
date_resolved:
assumes: [3, 23]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 25
---

# ADR-25: Two separate session logs — hash-paired audit vs. narrative summaries

> **Status: deferred (partially implemented as of 0.1.0-alpha.1).** Only half of this decision ships: the **audit log** is live, but the **per-session narrative log** has no writer, and audit-log **rotation** is not implemented — so the decision is not fully realized and is marked `deferred` until it is. What ships: the audit log, hash-paired per write and guarded by the Linter's `audit-unpaired-writes` detector. What is deferred: the per-session summaries under `system/logs/sessions/`, weekly rotation, and the `vault-hash-drift` detector named in early drafts of this ADR (never built). The decision below stands as the target design.

## Context

Memoria's review gate ([ADR-03](03-structural-review-gate.md)) is only trustworthy if the record of what happened is tamper-evident. Two different questions need answering from session activity — *"did this write happen and was it authorized?"* (forensic) and *"what did this session accomplish?"* (narrative) — and they have different readers, lifecycles, and integrity requirements. The mechanism that answers both was described in [Session logging](../explanation/architecture/session-logging.md) but never recorded as a decision. Because the audit log is the substrate dashboards and tamper-detection depend on, its design (who writes it, whether it is append-only, how its integrity is guaranteed) deserves a fixed record rather than living only in prose.

## Decision

Memoria keeps **two separate logs in `99-system/logs/`**, written by different components:

- **Policy MCP audit log** (`audit.jsonl`) — written by the **policy MCP**, append-only and **hash-paired per write**: every mutating entry records a `before_hash` / `after_hash` (SHA-256, computed by the MCP) and is matched by a `write_complete` record, so a write can be reversed and an edit made outside the trail is detectable. This is per-write pairing, not a cross-entry chain. It answers the forensic question and feeds the audit-log and fleet-health dashboards. *(Shipped in 0.1.0-alpha.1. The log is currently unbounded; rotation is a deferred convention.)*
- **Per-session summaries** (`sessions/YYYY-MM-DD-HHMM.jsonl`) — *designed*: a **Linter**-written summary of Hermes raw activity, one file per session, never rotated, accumulating indefinitely, answering the narrative question for the researcher reviewing what happened. *(Deferred — no writer exists in 0.1.0-alpha.1; see the status banner above.)*

The two are never combined. The `sessions/` directory is intentionally **not** pre-created in the starter vault (an empty tracked folder would add git noise); the installer creates it on first setup, and the Linter is the sole writer of session memory.

## Consequences

- The audit log stays terse, append-only, and queryable for tamper detection; mixing narrative into it would make it verbose and harder to verify, while mixing per-write events into summaries would make them harder to read.
- Tamper-evidence is structural but **detective, not preventive**: because every write is hash-paired and the log is append-only, modification is *detectable* — the Linter's `audit-unpaired-writes` detector flags a mutating allow with no paired `write_complete`, and the audit-log dashboard flags a path whose recorded `after_hash` no longer matches the file ([ADR-23](23-scoped-memory-substrates.md), audit memory). Enforcement is best-effort, not fail-closed: Hermes fails open on hook errors, so the pairing catches tampering after the fact rather than preventing it.
- Per-session file naming by `YYYY-MM-DD-HHMM` makes the narrative log multi-machine-safe: one researcher's machines each write their own session files and the vault accumulates them without collision (consistent with the single-researcher scope of [ADR-24](24-single-researcher-scope.md)).
- Once the narrative log is built, a missing `sessions/` directory would cause it to silently fail to write, so vault setup must create it — an operational obligation this decision imposes on the installer and the setup guide.
- Capture must start from first run: the audit and session record cannot be reconstructed retroactively, which is also why the publication telemetry of [ADR-20](20-publication-path.md) depends on logging existing early.

## Alternatives considered

**One combined log.** Rejected: the two readers want opposite shapes. A single log is either too verbose to verify (audit polluted with narrative) or too noisy to read (summaries polluted with per-write events). Separation lets each serve its reader.

**Pre-create the `sessions/` directory in the repo.** Rejected: a tracked empty folder accumulates churn in git history as session files land. Creating it at install time keeps the repo clean at the cost of one documented setup step.

## Related

- **Supporting rationale:** [Session logging](../explanation/architecture/session-logging.md) (the two-log table and the not-pre-created rationale).
- **Related decisions:** [ADR-03 structural review gate](03-structural-review-gate.md) (the audit trail makes the gate's writes accountable); [ADR-23 memory substrates](23-scoped-memory-substrates.md) (audit memory is the append-only substrate); [ADR-24 single-researcher scope](24-single-researcher-scope.md) (multi-machine, single-user safety).
- **Profiles affected:** the [Linter](../explanation/engines/README.md) (reads `99-system/logs/`; runs the `audit-unpaired-writes` integrity check; would write the session summaries once that deferred log is built).
- **Reference:** [Policy MCP](../reference/policy-mcp.md) (audit log format and enforcement).
- **Source discussion:** retroactively records the two-log separation already embedded in `session-logging.md`.
