---
topic: decisions
id: 106
title: Cost and disposition capture — Hermes session store and the review action
status: accepted
date_proposed: 2026-06-19
date_resolved: 2026-06-19
assumes: [20, 22, 104]
supersedes: []
superseded_by: []
---

# ADR-106: Cost and disposition capture — Hermes session store and the review action

## Context

At the time of this decision, two analytics signals the publication path depends on ([ADR-20](20-publication-path.md)) — per-card **cost/tokens** and reviewer **disposition** (accept / edit / reject) — were empty. The reference doc attributed this to an upstream limitation: that the current Hermes did not surface a cost/token overlay in its serialized card JSON, so the exporter had nothing to read. Verification against the installed Hermes (v0.14.0) showed that explanation was misleading. Hermes **does** compute and persist per-call cost and token usage — in its per-profile session store, not on the card — and the data is reachable from Memoria without modifying Hermes. The exporter was querying the one CLI endpoint (`kanban list --json`) that drops it. These signals cannot be back-filled ([ADR-20](20-publication-path.md)), so every day they stayed empty was permanently lost data; the fix should not wait on an upstream change that is not actually required.

## Decision

Memoria captures both signals at points it controls, per machine ([ADR-104](104-telemetry-three-planes.md)):

- **Cost / tokens — from the Hermes session store.** A Memoria-side exporter (host tooling, not an agent toolset, so unaffected by the MCP-only sandbox) reads, per completed card, the run metadata exposed by `hermes kanban show <id> --json` (`runs[].metadata.worker_session_id`), joins it to the per-profile session store (`~/.hermes/profiles/<lane>/state.db`, `sessions` table), and emits a cost event carrying Hermes's already-priced figures: `input_tokens`, `output_tokens`, cache and reasoning tokens, `estimated_cost_usd`, and the provenance fields (`cost_source`, `billing_provider`, `pricing_version`). Memoria does **not** maintain its own pricing table — it records Hermes's estimate and its provenance. The session store is per-machine and unsynced, so this exporter runs on each machine that dispatches and writes that machine's partitioned cost events.
- **Disposition — at the review action.** The accept / edit / reject outcome is a human decision taken in Obsidian, not an inference event. It is captured where the PI resolves a review (the board/QuickAdd review action), the same Memoria-controlled surface that already emits `attention` and `triage` — never inferred from a card-metadata overlay.

Because this couples to Hermes's internal, undocumented SQLite schema, Memoria pins the
**observed session-store contract** with a **Hermes cost doctor** before any
updater/exporter automation trusts the join. The doctor verifies, against the installed
Hermes runtime under test, that `hermes kanban show <id> --json` exposes
`runs[].metadata.worker_session_id`, that the per-profile `state.db` has the expected
`sessions` table shape, that a fixture or recent completed card can join from card run
to session row, and that missing-session cases fail closed with a counted miss rather
than a fabricated zero. Each Hermes upgrade must follow the same order: upgrade first,
verify the join, then re-enable cost export. A local model-gateway proxy at the profile
`base_url` remains a documented future option if provider-independent or actual (not
estimated) cost is ever required, but is **not adopted** now: it would re-capture data
Hermes already stores and add a process in the inference hot path.

## Consequences

- Both benchmark signals are populated at Memoria-controlled capture points, with no Hermes modification and no inference-path risk.
- The cost figure is Hermes's **estimate** (with the current kilocode provider `actual_cost_usd` is null); the recorded `cost_source` / `pricing_version` make that explicit rather than silently presenting an estimate as actual.
- Coupling to a private Hermes DB schema is brittle across upgrades — the contract doctor plus upgrade-time verification is the standing maintenance cost this accepts.
- Cost capture is per-card via a `kanban show` call per completed card and a session-store lookup; session rotation can occasionally drop an aged session (observed ~1 in 13), so a small miss rate is expected and not treated as an error.
- The misleading "upstream limitation" note in [Telemetry & logs](../reference/telemetry.md) is corrected to describe the real mechanism and its brittleness.
- [ADR-62](62-measurement-and-verification-harnesses.md)'s current implementation mapping records the session-store/review-action capture path.

## When this matters

This matters as soon as the publication benchmark ([ADR-20](20-publication-path.md)) needs real cost or acceptance-quality numbers — i.e. before any run whose cost or disposition is meant to appear in the paper. Until then the capture is wired but the absence is documented, not silently empty.

## Alternatives considered

**Wait for Hermes to surface the card overlay (status quo).** Rejected: it leaves an un-back-fillable signal empty indefinitely, gated on an upstream roadmap, when the data is already reachable today.

**Local model-gateway proxy at the profile `base_url`.** Rejected for now: it couples only to the stable OpenAI wire protocol (a real advantage) but re-captures data Hermes already prices, adds a daemon in the inference hot path, and would need its own pricing table for dollars. Kept on the shelf for provider-independence or actual-cost needs.

**Scrape Hermes logs post-hoc.** Rejected: more brittle than the session store and not guaranteed to contain usage at all.

## Related

- **Related decisions / Depends on:** [ADR-20 (publication path)](20-publication-path.md) (the capture-now mandate these signals serve); [ADR-22 (build on the Hermes runtime)](22-build-on-hermes-runtime.md) (the runtime whose store is read); [ADR-104 (telemetry three planes)](104-telemetry-three-planes.md) (the analytics plane and per-machine partitioning).
- **Files affected:** [`src/.memoria/mcp/board_export.py`](https://github.com/eranroseman/memoria-vault/blob/main/src/.memoria/mcp/board_export.py) (the exporter CLI/orchestrator) and [`src/.memoria/mcp/board_export_cost.py`](https://github.com/eranroseman/memoria-vault/blob/main/src/.memoria/mcp/board_export_cost.py) (the session-store join and cost doctor).
- **Tracking issue:** [#737](https://github.com/eranroseman/memoria-vault/issues/737) — implementation readiness and Hermes cost doctor.
- **Reference:** [Telemetry & logs](../reference/telemetry.md) (cost/disposition schemas and the corrected mechanism note); [Hermes CLI](../reference/hermes-cli.md).
