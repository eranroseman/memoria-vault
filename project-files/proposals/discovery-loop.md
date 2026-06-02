---
topic: proposals
title: Discovery loop and autonomy within the boundary
status: deferred
created: 2026-05-31
---

# Discovery loop and autonomy within the boundary

Three related capabilities that extend what the agent does *between* human gates, without moving the gates themselves.

---

## 1. Proactive discovery loop

**What.** Hermes runs unattended on a nightly schedule, fills `10-inbox/03-candidates/`, and posts a morning summary. Converts the system from reactive (you trigger discovery) to proactive (discovery happens while you sleep).

**Nightly pattern:**
```text
1. Read 00-meta/research-directions.md
2. Pick top N priorities (default 3)
3. For each priority: run `find` (max 10 candidates)
4. Ingest confirmed candidates from the previous day's inbox
5. Enrich any paper notes flagged as stale
6. Commit and post morning summary
```

**Trade-offs.** Requires always-on infrastructure (a sleep-prone machine misses the cron). Bad inclusion criteria flood the inbox and make morning triage unsustainable. Silent cron failure is the dominant operational risk — fail loud, not silent.

**Adoption trigger.** All four must hold: (1) Memoria v0.1 stable, (2) `research-directions.md` maintained for ≥ 4 weeks, (3) always-on deployment active (Syncthing + VPS), (4) `screening-protocol.md` written down. Not before.

**Guard.** Adopting before inclusion criteria are written down produces an inbox that floods with low-relevance candidates and makes morning triage the slowest part of the day — the opposite of the intent.

---

## 2. Coder lane experiment loop

**What.** A lane-bounded skill (`Coder-experiment-loop`) runs propose → test → keep-if-improved → revert-otherwise for up to N iterations against a pre-defined scalar success criterion (a test suite, a benchmark, a coverage threshold). Output lands in `40-workbench/<project>/06-code/experiments/<run-id>/`. When the budget exhausts, a summary card goes to `done` (`review_status: requested`) with the best variant, its diff, and the metric trajectory. The human reviews and decides whether the best variant promotes.

**Trade-offs.** Picking the wrong success metric is the dominant failure mode — the loop optimizes the metric, not the underlying goal. A poorly-specified `success_metric:` produces a winner that game-played the test. Iteration count can balloon API spend if the budget isn't tight.

**Adoption trigger.** The human notices running the same "edit → test → revert if worse" cycle more than ~10–20 times per project, *and* the cycle has a scalar success criterion that existed *before* the cycle started.

**Guard.** Do not apply to synthesis work. The three preconditions (monotonic metric, reversible changes, independent experiments) hold for code and fail for knowledge work. This is explicitly scoped to the Coder lane.

**Dependencies.** A `code-experiment` card type with `success_metric:`, `budget_iterations:`, `budget_cost_usd:` fields. Policy MCP permitting writes only to `40-workbench/<project>/06-code/experiments/<run-id>/`.

**Related.** [PROP-01 code-artifact autopilot](PROP-01-code-artifact-autopilot.md) is the *scheduled-script* variant of Coder-lane autonomy; this is the *keep/revert experiment* variant. Both are bounded by [ADR-21](../decisions/21-l3-autonomy-ceiling.md).

---

## 3. Agent-proposed candidate claim notes

**What.** After a `discuss` card closes, the Writer proposes *candidate* claim notes from the discussed source — drafts that land in `10-inbox/03-candidates/` as `type: candidate-note`, never in `30-synthesis/01-claims/`. Each carries its provenance (the paper note and the specific passage). The human edits, authors the canonical claim note, or discards.

**Trade-offs.** Most judgment-adjacent automation in the roadmap. Two specific risks: (1) **rubber-stamping** — a fluent candidate invites acceptance without the close reading distillation is meant to force; (2) **framing capture** — the agent's phrasing anchors the human's, narrowing the claims they would have written unprompted. Over-proposing is worse than not proposing.

**Adoption trigger.** `discuss` and `distill` are stable workflows *and* the human notices the blank-page cost of *transcribing* claims (not comprehending them) is the actual bottleneck. Prototype on a handful of sources first; measure the accept-unedited rate. A high rate is a warning, not a win.

**Guard.** If comprehension is the bottleneck, this does not help. The candidate fires only *after* a `discuss` card closes — proposing from an unread source defeats the purpose.

**Dependencies.** Claim-sentence classification (to ground candidates in specific source passages). A `candidate-note` card type (shared candidate schema, ADR-17) routing to `10-inbox/03-candidates/` with policy MCP denying writes to `30-synthesis/01-claims/`.
