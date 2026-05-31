---
status: deferred
created: 2026-05-31
---

# Measurement, quality, and verification

Capabilities that make the Verifier measurable, the claim layer richer, and the system's health visible over time.

---

## 1. CiteME-style Verifier regression harness

**What.** A private fixture of ~50 (excerpt → target-claim-note) pairs built from approved vault drafts. Score the Verifier against this fixture nightly; record accuracy in a metric note. A Verifier prompt change ships only when fixture accuracy is at or above the running 90th-percentile baseline. Prevents silent regression from model updates, context-length changes, or template edits.

**Trade-offs.** One-time fixture construction effort (a few hours of labelling). If the fixture is too small or too easy, it gives false confidence. Needs periodic refresh as the vault's claim-note shape evolves.

**Adoption trigger.** Verifier is live and running against real drafts, *and* at least one project has produced ≥ 20 approved drafts citing ≥ 20 approved claim notes.

**Guard.** Building before the Verifier's behavior is settled produces a fixture pinned to a transient prompt, making the baseline meaningless.

---

## 2. Chain-of-Evidence claim taxonomy

**What.** Type each substantive claim and require a type-appropriate evidence chain: `citation` (resolved citekey + claim note), `numerical` (specific passage containing the figure), `methodological` (protocol summary), `conclusion` (the set of claim notes it rests on). Adapted from ScientistOne (Meng et al. 2026), which reaches 0/337 hallucinated references vs. baselines up to 21%.

**Trade-offs.** Typing every claim adds an extraction step. Types don't cleanly partition every sentence — a "primary type" convention is needed. Partial adoption (some claims typed, most not) is worse than none — makes type-aware checks unreliable.

**Adoption trigger.** The CiteME harness is live and has a measured untyped baseline *and* false-clean verdicts from the Verifier are a recurring issue.

**Guard.** Adopt typing only if the harness shows it measurably reduces false-clean verdicts. The harness is the gate for this capability — build the harness first.

**Note.** Score verification and method–code alignment from ScientistOne are **out of scope** for knowledge work — they presuppose executable experiments and belong only in the Coder lane.

---

## 3. Fleet observability dashboard

**What.** Per-lane and per-skill metrics (cost, success rate, retry rate, latency) on daily/weekly/monthly cadence. Materializes the [fleet-health dashboard](../../docs/explanation/dashboards/fleet-health.md) design.

**Trade-offs.** Requires a scheduled aggregator that reads the audit log and board history. Until the aggregator exists, the dashboard is empty.

**Adoption trigger.** At least one of: > 50 tasks/week (eyeballing the board misses regressions), multiple scheduled lanes running in parallel, API spend ≥ $50/month.

---

## 4. Propagation debts

**What.** When a high-traffic note changes (claim promoted to `evergreen`, reference note updated, paper retracted), enumerate the dependents that need re-evaluation and record them as a readable queue in the Linter's report. The human works the queue; the agent never rewrites dependents.

**Trade-offs.** Needs a trigger-event taxonomy and a habit of working down the queue. A queue that grows forever is noise, not signal.

**Adoption trigger.** Corpus passes ~500 claim notes *and* the human notices reading a draft and realizing a cited claim has shifted.

---

## 5. LLM-judge gate for export

**What.** At export time only, a `prose-check` command scores the manuscript on a small fixed rubric (argument coherence, voice consistency, citation grounding). Result is a report attached to the export card; the human reads it and decides whether to revise. Never auto-edits, never blocks export, never runs against synthesis.

**Adoption trigger.** A deliverable has been re-exported more than twice for issues a model could have caught on the first read.

---

## 6. Execution-trace reflection on retry

**What.** On a retry, a reflection skill reads the failure trace (what tool was called, what arguments, what error) and produces a *modified* handoff payload for the next attempt — not an identical redispatch. Borrowed from Nous Research's hermes-agent-self-evolution pattern.

**Trade-offs.** Requires structured failure traces in the Kanban dispatcher. A reflection_count field on cards (distinct from retry count) so the human can see when reflection itself is exhausted.

**Adoption trigger.** Sustained retry rate > 0.10 across a lane visible in fleet observability, *or* a specific skill's retry rate crosses 0.20.

**Guard.** The reflection layer rewrites the *handoff payload* for one card only. It never rewrites prompts, skills, or system contracts. If the same failure recurs across cards, that is a design issue the human resolves.
