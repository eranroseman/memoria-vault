---
topic: decisions
id: 25
title: Two separate session logs — hash-chained audit vs. narrative summaries
status: accepted
date_proposed: 2026-06-01
date_resolved: 2026-06-01
supersedes: []
superseded_by: []
---

# ADR-25: Two separate session logs — hash-chained audit vs. narrative summaries

## Context

Memoria's review gate ([ADR-03](03-structural-review-gate.md)) is only trustworthy if the record of what happened is tamper-evident. Two different questions need answering from session activity — *"did this write happen and was it authorized?"* (forensic) and *"what did this session accomplish?"* (narrative) — and they have different readers, lifecycles, and integrity requirements. The mechanism that answers both was described in [session-logging.md](../../docs/explanation/architecture/session-logging.md) but never recorded as a decision. Because the audit log is the substrate dashboards and tamper-detection depend on, its design (who writes it, whether it is append-only, whether it is hash-chained) deserves a fixed record rather than living only in prose.

## Decision

Memoria keeps **two separate logs in `99-system/logs/`**, written by different components:

- **Policy MCP audit log** (`audit.jsonl`) — written by the **policy MCP**, append-only and **SHA-256 hash-chained** (each entry records `sha256_before` / `sha256_after`, computed by the MCP, and the chain must stay unbroken across the whole log) so modification is detectable; rotated weekly by the Linter. It answers the forensic question and feeds the audit-log and fleet-health dashboards.
- **Per-session summaries** (`sessions/YYYY-MM-DD-HHMM.jsonl`) — written by the **Linter** (summarizing Hermes raw activity), one file per session, never rotated, accumulating indefinitely. They answer the narrative question for the human reviewing what happened.

The two are never combined. The `sessions/` directory is intentionally **not** pre-created in the starter vault (an empty tracked folder would add git noise); the installer creates it on first setup, and the Linter is the sole writer of session memory.

## Consequences

- The audit log stays terse, append-only, and queryable for tamper detection; mixing narrative into it would make it verbose and harder to verify, while mixing per-write events into summaries would make them harder to read.
- Tamper-evidence is structural but **detective, not preventive**: because the audit log is SHA-256 hash-chained and append-only, modification is *detectable* — the Linter's `vault-hash-drift` detector fires when a `before`/`after` link fails ([ADR-23](23-six-memory-substrates.md), vault audit memory). Enforcement is best-effort, not fail-closed: Hermes fails open on hook errors, so the chain catches tampering after the fact rather than preventing it.
- Per-session file naming by `YYYY-MM-DD-HHMM` makes the narrative log multi-machine-safe: one researcher's machines each write their own session files and the vault accumulates them without collision (consistent with the single-researcher scope of [ADR-24](24-single-researcher-scope.md)).
- A missing `sessions/` directory causes session logging to silently fail, so vault setup must create it — an operational obligation this decision imposes on the installer and the setup guide.
- Capture must start from first run: the audit and session record cannot be reconstructed retroactively, which is also why the publication telemetry of [ADR-20](20-publication-path.md) depends on logging existing early.

## Alternatives considered

**One combined log.** Rejected: the two readers want opposite shapes. A single log is either too verbose to verify (audit polluted with narrative) or too noisy to read (summaries polluted with per-write events). Separation lets each serve its reader.

**Pre-create the `sessions/` directory in the repo.** Rejected: a tracked empty folder accumulates churn in git history as session files land. Creating it at install time keeps the repo clean at the cost of one documented setup step.

## Related

- **Supporting rationale:** [session-logging.md](../../docs/explanation/architecture/session-logging.md) (the two-log table and the not-pre-created rationale).
- **Related decisions:** [ADR-03 structural review gate](03-structural-review-gate.md) (the audit trail makes the gate's writes accountable); [ADR-23 memory substrates](23-six-memory-substrates.md) (vault audit memory is the append-only substrate); [ADR-24 single-researcher scope](24-single-researcher-scope.md) (multi-machine, single-user safety).
- **Profiles affected:** the [Linter](../../docs/explanation/profiles/linter.md) (owns `99-system/logs/`, writes session summaries, rotates the audit log, runs `vault-hash-drift`).
- **Reference:** [reference/policy-mcp.md](../../docs/reference/policy-mcp.md) (audit log format and enforcement).
- **Source discussion:** retroactively records the two-log separation already embedded in `session-logging.md`.
