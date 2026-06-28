---
topic: decisions
id: 25
title: Two separate session logs — hash-paired audit vs. per-session digests
nav_exclude: true
status: accepted
date_proposed: 2026-06-01
date_resolved: 2026-06-12
assumes: [3, 23]
supersedes: []
superseded_by: []
---

# ADR-25: Two separate session logs — hash-paired audit vs. per-session digests

> **Status: accepted — fully implemented (2026-06-12).** Both halves now ship: the **audit log** (hash-paired per write, guarded by the Linter's `audit-unpaired-writes` and `vault-hash-drift` detectors) and the **per-session digests** under `system/logs/sessions/`, written by the Linter's `session_summary` engine on the daily cron ([#391](https://github.com/eranroseman/memoria-vault/issues/391), [#392](https://github.com/eranroseman/memoria-vault/issues/392)). Two amendments from the original draft: the audit log is **append-only forever — never rotated** (the "weekly rotation" of early drafts is rejected, [#393](https://github.com/eranroseman/memoria-vault/issues/393); growth is surfaced by the Linter's `audit-log-size` advisory at 50 MB), and the second log is a **deterministic digest, not an LLM narrative** — the Linter is zero-LLM, so "narrative" below reads as "per-session digest."

## Context

Memoria's review gate ([ADR-03](03-structural-review-gate.md)) is only trustworthy if the record of what happened is tamper-evident. Two different questions need answering from session activity — *"did this write happen and was it authorized?"* (forensic) and *"what did this session accomplish?"* (narrative) — and they have different readers, lifecycles, and integrity requirements. The mechanism that answers both was described in [Session logging](../explanation/architecture/session-logging.md) but never recorded as a decision. Because the audit log is the substrate dashboards and tamper-detection depend on, its design (who writes it, whether it is append-only, how its integrity is guaranteed) deserves a fixed record rather than living only in prose.

## Decision

Memoria keeps **two separate logs in `99-system/logs/`**, written by different components:

- **Policy MCP audit log** (`audit.jsonl`) — written by the **policy MCP**, **append-only forever** and **hash-paired per write**: every mutating entry records a `before_hash` / `after_hash` (SHA-256, computed by the MCP) and is matched by a `write_complete` record, so a write can be reversed and an edit made outside the trail is detectable. This is per-write pairing, not a cross-entry chain. It answers the forensic question and feeds the audit-log and fleet-health dashboards. The log is **never rotated**: at single-researcher write volume ([ADR-24](24-single-researcher-scope.md)) rotation would complicate every consumer that walks the full history — the pairing reads, the `vault-hash-drift` verifier, the session digests — for no benefit, and it would match neither the session files' accumulate-indefinitely posture. Unbounded growth is surfaced, not silent: the Linter's `audit-log-size` detector raises a LOW advisory once the log exceeds **50 MB**.
- **Per-session summaries** (`sessions/YYYY-MM-DD-HHMM.jsonl`) — a **Linter**-written *deterministic digest* of the audit trail (the Linter is zero-LLM, so this is a digest, not an LLM narrative): one file per session (`task_id`), named from the session's first timestamp (a deterministic `-2` suffix disambiguates a shared start minute), carrying a header record (task, profiles, start/end, counts by action and decision) and one record per touched path (actions, final decision, final `after_hash`). Files are never rotated and accumulate indefinitely, answering the what-happened question for the researcher. The writer (`operations/integrity/linter/session_summary.py`) runs on the daily lint cron, is idempotent (an already-digested `task_id` is never rewritten), and only digests sessions quiet for **24 h**, so an in-flight session is never summarized early.

The two are never combined. The `sessions/` directory is intentionally **not** pre-created in the starter vault (an empty tracked folder would add git noise); the installer creates it on first setup, and the Linter is the sole writer of session memory.

## Consequences

- The audit log stays terse, append-only, and queryable for tamper detection; mixing narrative into it would make it verbose and harder to verify, while mixing per-write events into summaries would make them harder to read.
- Tamper-evidence is structural but **detective, not preventive**: because every write is hash-paired and the log is append-only, modification is *detectable* — the Linter's `audit-unpaired-writes` detector flags a mutating allow with no paired `write_complete`, and its `vault-hash-drift` detector flags (CRITICAL) any path whose latest recorded `after_hash` no longer matches the on-disk file ([ADR-23](23-scoped-memory-substrates.md), audit memory) — a legitimate human edit in Obsidian surfaces there too, by design: the finding means the trail no longer pins that file's state, not that the edit was malicious. Enforcement is best-effort, not fail-closed: Hermes fails open on hook errors, so the pairing catches tampering after the fact rather than preventing it.
- Per-session file naming by `YYYY-MM-DD-HHMM` makes the narrative log multi-machine-safe: one researcher's machines each write their own session files and the vault accumulates them without collision (consistent with the single-researcher scope of [ADR-24](24-single-researcher-scope.md)).
- A missing `sessions/` directory would cause the digest writer to silently fail, so vault setup must create it — the installer's folder skeleton includes `system/logs/sessions/` (declared in `.memoria/schemas/folders.yaml` and guarded by the Linter's `skeleton-drift` detector), and the writer itself creates the directory on demand as a backstop.
- Capture must start from first run: the audit and session record cannot be reconstructed retroactively, which is also why the publication telemetry of [ADR-20](20-publication-path.md) depends on logging existing early.

## Alternatives considered

**Weekly rotation of `audit.jsonl`.** Rejected ([#393](https://github.com/eranroseman/memoria-vault/issues/393)): rotation would force every full-history consumer — the `write_complete` pairing reads, the `vault-hash-drift` walk, the session digests — to stitch across rotated files, for no benefit at single-researcher write volume. Append-only forever keeps one walk = the whole history; the `audit-log-size` advisory keeps growth visible.

**An LLM-written narrative summary.** Rejected: the Linter is a zero-LLM engine ([ADR-49](49-catalog-in-bases-linter-monitor.md)), and a digest derived deterministically from the audit trail is reproducible, auditable, and free — the narrative reading stays with the researcher.

**One combined log.** Rejected: the two readers want opposite shapes. A single log is either too verbose to verify (audit polluted with narrative) or too noisy to read (summaries polluted with per-write events). Separation lets each serve its reader.

**Pre-create the `sessions/` directory in the repo.** Rejected: a tracked empty folder accumulates churn in git history as session files land. Creating it at install time keeps the repo clean at the cost of one documented setup step.

## Related

- **Tracking issues (resolved):** [#391](https://github.com/eranroseman/memoria-vault/issues/391) (per-session digests), [#392](https://github.com/eranroseman/memoria-vault/issues/392) (`vault-hash-drift`), [#393](https://github.com/eranroseman/memoria-vault/issues/393) (append-only-forever).
- **Supporting rationale:** [Session logging](../explanation/architecture/session-logging.md) (the two-log table and the not-pre-created rationale).
- **Related decisions:** [ADR-03 structural review gate](03-structural-review-gate.md) (the audit trail makes the gate's writes accountable); [ADR-23 memory substrates](23-scoped-memory-substrates.md) (audit memory is the append-only substrate); [ADR-24 single-researcher scope](24-single-researcher-scope.md) (multi-machine, single-user safety).
- **Profiles affected:** the [Linter](../explanation/operations.md) (reads `99-system/logs/`; runs the `audit-unpaired-writes`, `vault-hash-drift`, and `audit-log-size` integrity checks; writes the per-session digests).
- **Reference:** [Policy MCP](../reference/policy-mcp.md) (audit log format and enforcement).
- **Source discussion:** retroactively records the two-log separation already embedded in `session-logging.md`.
