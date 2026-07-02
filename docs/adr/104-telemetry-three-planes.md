---
topic: decisions
id: 104
title: Telemetry as three planes — audit, analytics, diagnostic
nav_exclude: true
status: superseded
date_proposed: 2026-06-19
date_resolved: 2026-06-19
assumes: [20, 24, 25]
supersedes: []
superseded_by: [127]
---

# ADR-104: Telemetry as three planes — audit, analytics, diagnostic

> **Status note (0.1.0-alpha.15):** superseded by [ADR-127](127-quarantine-and-verify-integrity.md). Kept for decision history; current architecture is carried by the consolidation ADR.

## Context

Memoria's logging grew signal-by-signal: an append-only audit trail ([ADR-25](25-session-logging-two-logs.md)), the publication-benchmark capture ([ADR-20](20-publication-path.md)), and a dozen purpose-named JSONL streams documented in [Telemetry & logs](../reference/telemetry.md). The pieces work, but the *posture* was never decided as a whole, and one need is missing entirely: when Memoria's own deterministic code (an MCP server, an ingest run, a cron) fails, the only trace is a stderr print — there is no persisted, queryable diagnostic record. At the same time the existing signals conflate concerns with opposite requirements: forensic permanence, content-free analytics, and (the missing) content-bearing debugging all want different integrity, retention, and privacy rules. Treating them as one substrate forces the strictest rule onto everything and still leaves debugging unserved. This decision settles the overall shape; the diagnostic plane's privacy contract ([ADR-105](105-diagnostic-plane.md)) and the cost/disposition capture points ([ADR-106](106-cost-and-disposition-capture.md)) are decided separately. Where this ADR changes audit storage layout for future multi-machine operation, it amends [ADR-25](25-session-logging-two-logs.md) without changing ADR-25's audit semantics: append-only, hash-paired, full-history-readable audit evidence remains the invariant.

## Decision

Memoria's telemetry is **three planes, separated by their intrinsic requirements**, not one log family:

- **Audit plane** — forensic: *"what writes hit the vault, and were they authorized?"* This is `audit.jsonl` today, plus its deterministic per-session digest projection ([ADR-25](25-session-logging-two-logs.md)). Content-free, append-only, with per-write SHA-256 before/after hashes. **Its tamper-evidence and sync substrate is Git, not in-file cryptography.** The vault is already a Git repository; commit history is a Merkle chain, a remote the researcher does not solely control is a genuine second trust domain, and signed commits (optional) add authorship. Memoria therefore does **not** add a per-entry `prev_hash` chain: a linear chain would add complexity without a guarantee Git does not already give. Per-write pairing stays (it pins vault content state at finer grain than a commit); external cryptographic anchoring (OpenTimestamps / RFC-3161) is **deferred** until a second party or compliance driver makes it more than theater under single-researcher scope ([ADR-24](24-single-researcher-scope.md)).
- **Analytics plane** — operational and publication signals: board state, transitions, disposition, cost, attention, triage, linkage, lint findings. **Content-free** (hashes, IDs, counts, enums, durations — never note content), retained, and Git-synced. Derived metrics (lane notes, trust-score, eval trends) are **pure, reproducible projections** over these events — never a second source of truth, so a formula change re-runs over history rather than going dark. The plane is a small set of streams grouped by writer and cadence, not one merged stream and not a file per metric.
- **Diagnostic plane** — operability: *"why did Memoria's own code break?"* Structured records from Memoria's **own Python MCP servers and Operations only** — never agent cognition, which lives inside the external, unmodified Hermes runtime ([ADR-22](22-build-on-hermes-runtime.md)) and is unreachable. This plane lives **outside the vault and outside Git**, is rotated and disposable, defaults to errors/warnings, and is content-light by default. Its full privacy and lifecycle contract is [ADR-105](105-diagnostic-plane.md).

The supported runtime is local-only with one active dispatcher per vault ([ADR-24](24-single-researcher-scope.md)). If a future second-device or sync topology is adopted, it must decide its own conflict-free audit/analytics partitioning before more than one machine can write. Until then, the current single-machine audit and analytics files remain valid current behavior.

## Consequences

- A future multi-device write topology must not append to one shared `audit.jsonl` from multiple machines. That topology is outside the current design and needs its own ADR before support.
- Integrity ties to Git: the guarantee is only as strong as "an out-of-your-sole-control remote plus you do not force-push history." A self-hosted vs. hosted remote is the lever for how much activity-cadence metadata leaves the machine — content-free, but a timestamped trail reveals *when* the researcher works.
- The diagnostic plane fills the operability gap but is honestly scoped: it cannot see prompts, agent retries, or tool-selection inside Hermes. Whole-system diagnosis is not on offer; Memoria-side failure diagnosis is.
- Three planes mean three retention rules (audit: forever; analytics: retained, content-free; diagnostic: rotated, disposable) and three privacy rules. This is more written policy than one log family, but each rule is simpler because it serves one reader.
- Reproducibility is preserved: wall-clock timestamps remain event facts, but no vault content or nondeterministic derived state enters the audit/analytics planes that digests and the benchmark read. Derived metrics stay pure projections over retained events. The diagnostic plane is explicitly non-canonical, so its timing-dependence and lossiness pollute nothing reproducible.
- No heavyweight "spine": there is a shared event envelope and a small emit helper per language, not a correlation-ID propagated through Hermes (impossible across an unmodified runtime) nor a taxonomy registry. `task_id` remains the join key where a card exists.

## When this matters

The diagnostic plane becomes worth building the first time a Memoria MCP/Operations failure is diagnosed by guesswork because stderr was gone — most concretely during unattended cron or worker operation, where no human watches the terminal. Until that is real, the existing single-machine audit + analytics streams are adequate.

## Alternatives considered

**Keep one log family, add levels/rotation to it.** Rejected: forces forensic-permanence rules onto disposable diagnostics and content-free rules onto the one plane that needs content, while still not separating the readers. The planes have opposite requirements; one substrate serves none well.

**Collapse the analytics streams into a single event stream.** Rejected as dogma: for a single-user local tool it is a wash — one envelope and metrics-as-projection are the real wins, and those hold with a few cadence-grouped streams without making every reader filter one firehose or making a corrupt line poison everything.

**Per-entry hash-chaining of the audit log (with later external anchoring).** Rejected on merits, not authority: Git already provides a Merkle chain plus remote anchoring and merges without forking, whereas a linear in-file chain forks across machines and is recomputable by the file owner — speculative generality for a future the single-researcher scope does not have.

**A correlation/trace ID propagated across all processes.** Rejected: it cannot be threaded through the external unmodified Hermes runtime, and at n=1 local there is no service mesh to reconstruct. `task_id` already correlates everything card-scoped.

## Related

- **Related decisions / Depends on:** [ADR-25 (two session logs)](25-session-logging-two-logs.md) (the audit plane); [ADR-20 (publication path)](20-publication-path.md) (the analytics plane's capture-now mandate); [ADR-24 (single-researcher scope)](24-single-researcher-scope.md) (the integrity threat model and one-dispatcher boundary); [ADR-22 (build on the Hermes runtime)](22-build-on-hermes-runtime.md) (why agent cognition is unreachable).
- **Decided separately:** [ADR-105 (diagnostic plane)](105-diagnostic-plane.md); [ADR-106 (cost and disposition capture)](106-cost-and-disposition-capture.md).
- **Tracking issue:** [#735](https://github.com/eranroseman/memoria-vault/issues/735) — implementation readiness and ADR-25 mapping.
- **Design rationale:** [Telemetry architecture](../explanation/architecture/telemetry-architecture.md).
- **Reference:** [Telemetry & logs](../reference/telemetry.md); [Policy MCP](../reference/policy-mcp.md).
