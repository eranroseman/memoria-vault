---
topic: roadmap
---

# Autonomy progression

A dependency-ordered roadmap for the 15 patterns that increase Memoria's *within-boundary* autonomy — the agent does more unattended work between human gates without moving the gates themselves — plus the orthogonal Coder-lane exception (C.1), the one place an internal keep/revert loop is admissible.

## Scope

"More autonomous" has two readings:

1. **Same gate, fewer presses.** The human review state remains structurally blocking; the agent does more bookkeeping, drafting, surfacing, and verification per gate press. This document is *only* about reading 1.
2. **Move the gate.** Loosen the autonomy boundary so the agent decides what stays without human approval. That is a redesign of [architecture/why-no-autonomous-synthesis.md](../../explanation/architecture/why-no-autonomous-synthesis.md), not a borrow from the surveyed papers. Not covered here.

This document is the answer to "how do we let the agent do more between gates?" It is not the answer to "should the gate stay where it is?" That question is settled in [vision.md](../../explanation/vision.md) and [architecture/why-no-autonomous-synthesis.md](../../explanation/architecture/why-no-autonomous-synthesis.md).

## Principle

**Same gate, fewer presses.** Every pattern below is admissible because it routes outputs to `10-inbox/` or to a dashboard surface, never to review-gated zones. The policy MCP's review-gated-zone deny rule is the structural guarantee that this stays true regardless of how much unattended activity accumulates.

## The human's task surface

Before the patterns, the full picture: everything the human does in Memoria today, re-sorted by whether an agent should take it. The [role × stage matrix](../../explanation/workflows/pipeline-design.md#role--stage-matrix) is the authoritative who-does-what; this is that surface sorted by *transferability*. The layers below are the mechanization of buckets A and B. Bucket C is the residue the [autonomy boundary](../../explanation/architecture/why-no-autonomous-synthesis.md) protects — the patterns never touch it.

> **Reading the tables.** Entries tagged `(shipped)` are **already implemented** — listed for context, not roadmap work. The roadmap value is the numbered patterns (`1.1`, `4.4`, …) that are *not* yet built; see [implementation-status.md](../implementation-status.md) for what ships today.

**Bucket A — the agent should own it, and is genuinely *better*** (recall, consistency, tirelessness). The human's role shrinks to spot-checking.

| Human task today | Pattern that relieves it |
| --- | --- |
| Skim for discovery candidates | 1.1 discovery loop (1.4 to trust it) |
| Run — or skip — cite-checks; verify claims trace | 3.3 CoE pre-gate verification (1.3 guards drift) |
| Notice duplicate claims | `find-duplicates` (shipped) |
| Notice contradictions across the corpus | 4.4 contradiction detection |
| Remember cross-links | `[!suggestions]` callout (shipped) |
| Check retractions / orphans / broken links / drift | Verifier `retraction-check` + Linter (shipped); 4.2 propagation debts |
| Fetch / normalize metadata | Librarian `enrich` (shipped) |

These are *recall/consistency* tasks where human performance is not just slower but worse — humans skip, forget, and cannot scan the whole corpus. The agent is genuinely better, which is why most are already agent-owned; the remaining win is making them **proactive** (1.1) rather than human-triggered.

**Bucket B — the agent proposes, the human disposes.** The agent does the heavy lift; the decision stays human, but the human's effort drops to a confirmation.

| Human task today | Pattern that relieves it |
| --- | --- |
| Classify (promote `_proposed_classification`) | 3.1 semi-autonomous triage (batch-approve high-confidence) |
| Assess corpus readiness | Mapper `scope-project` produces the map; human judges "enough" |
| Order / triage the inbox | 3.2 tournament ranking (or its learning-to-rank engine) |
| Generate framings / outlines | 2.2 inspiration retrieval; Writer `counter-outline` |
| Disposition Verifier flags | 3.3 pre-clears the mechanical part; human softens / pursues / accepts |
| Transcribe a discussed source into claim drafts | [Agent-proposed candidate claim notes](future-directions.md#agent-proposed-candidate-claim-notes) — the boundary-adjacent one |

These are the "same gate, fewer presses" core. The win is *pre-gate* work that makes each human decision cheaper, never the decision itself.

**Bucket C — deliberately human; the residue the patterns never touch.** An agent *could* attempt some of these; the design refuses, and the 2026 evidence backs the refusal.

| Human task | Why it stays human |
| --- | --- |
| The approve gate (`review_status: approved`) | The structural differentiator; agent-approval is the failure mode (Zhang 2026: agents pass surface review, fail artifact-aware review). |
| What counts as a claim / synthesis faithfulness | Not scalar — the distill judgment. |
| Merge / split of claim notes | Collapsing two claims is a *meaning* decision, not a structural one. |
| Framing choice, prose voice, argument | Taste; agents converge to generic (Bisht's hivemind finding). |
| Steering priorities (`research-directions.md`) | Problem selection resists formalization (Bisht's McNamara fallacy). |
| Promotion to canonical; archive | The durability commitment. |

**The throughline.** The 15 patterns below are exactly the mechanization of buckets A and B. When they all ship, the human's day collapses to bucket C: *steer (priorities), decide (approve / reject / merge), and write (taste).* That residue is the autonomy boundary working as designed — not a gap to close. This also gives a reusable test for any *future* pattern: if it moves a bucket-C task to the agent, it is no longer "same gate, fewer presses" — it is "move the gate," which this document does not cover (see [Scope](#scope)).

## The layers

Five layers, in strict dependency order. A pattern in layer N depends on at least one pattern in layer < N to function or to pay off meaningfully. Within a layer, patterns are independent of each other.

### Layer 0 — Reliability foundation

Preconditions, not autonomy gains in themselves. Without these, every layer above is unreliable; with them, retries become a manageable cost.

| # | Pattern | Source | Status |
| --- | --- | --- | --- |
| 0.1 | Structured-output handoffs at profile boundaries | MetaGPT (Hong 2024) | Already specified in [vault/frontmatter-schema.md](../../reference/frontmatter-schema.md); recently named as a borrow in [why-pattern-provenance.md](../../explanation/architecture/why-pattern-provenance.md) |
| 0.2 | Reflection on retry | NousResearch hermes-agent-self-evolution | [future-directions.md §"Execution-trace reflection on retry"](future-directions.md#execution-trace-reflection-on-retry) |

**Why first.** Layer 1+ run unattended; an unattended pipeline that fails on the third retry blocks until the human wakes up. Structured handoffs prevent silent format drift between profiles; reflective retry prevents identical re-dispatch on structurally broken inputs. Together they raise the unattended success rate to the point where nightly autonomy is worth attempting.

### Layer 1 — Unattended cycles (the gateway)

The single largest autonomy gain in the roadmap. Everything above this layer compounds with it.

| # | Pattern | Source | Status |
| --- | --- | --- | --- |
| 1.1 | Discovery loop | Karpathy Autoresearch | [future-directions.md §"The discovery loop"](future-directions.md#the-discovery-loop) |
| 1.2 | Hypothesis sampling at higher temperature | Qi 2023 | Tuning choice within 1.1; cited inline |
| 1.3 | CiteME-style Verifier nightly harness | Press 2024 (CiteME) | [future-directions.md §"CiteME-style Verifier regression harness"](future-directions.md#citeme-style-verifier-regression-harness) |
| 1.4 | Discovery-quality harness | AutoResearchBench (Xiong et al. 2026) | [future-directions.md §"CiteME-style Verifier regression harness"](future-directions.md#citeme-style-verifier-regression-harness) (the "Companion benchmark" note) |

**Sequencing within the layer.** 1.1 is the headline pattern. 1.2 is a tuning bullet within 1.1 (sample candidates at higher temperature, evaluate them at lower temperature). 1.3 and 1.4 are *parallel* — neither depends on 1.1 and each provides a different kind of unattended quality tracking: 1.3 certifies the Verifier's attribution (does a cited claim trace?), 1.4 certifies the Librarian's discovery (was the paper that should have been found actually found, and the set that should have been collected actually collected?). 1.4 is what lets you *trust* 1.1 before scaling it — a nightly discovery loop is only worth running unattended if its recall/precision is measured rather than assumed. All four share the structural property "agent runs on a cron, writes only to inbox or dashboard, human reads in the morning." How 1.1's candidates are *ranked* for the morning triage is a deterministic enhancement, not a separate pattern — reuse the `[!suggestions]` weighted scorer rather than an LLM relevance judge; see [future-directions.md §"Discovery relevance scoring"](future-directions.md#discovery-relevance-scoring).

**Why this layer is the gateway.** Layers 2–4 amplify or refine the inbox produced by 1.1. Without unattended discovery cycles producing volume, the patterns above this layer have nothing to operate on at a scale that justifies their cost.

### Layer 2 — Amplifying nightly volume

Patterns that improve *what flows through* the discovery loop without human hand-feeding.

| # | Pattern | Source | Status |
| --- | --- | --- | --- |
| 2.1 | Gap-seeking planner | AI-Researcher, ResearchAgent | [future-directions.md §"Gap-seeking planner"](future-directions.md#gap-seeking-planner) |
| 2.2 | Inspiration retrieval before drafting | SciMON (Wang 2024) | Adopted as Adapt in [why-pattern-provenance.md](../../explanation/architecture/why-pattern-provenance.md); Writer-profile change |

**Why after layer 1.** Both work without the discovery loop (you can run the gap-planner on demand; inspiration retrieval helps any Writer invocation). But 2.1 produces *discovery queries* whose natural consumer is 1.1's nightly run, and 2.2 pays off most when there's enough vault content for retrieval to find non-trivial matches — which the discovery loop accelerates accumulating.

### Layer 3 — Reduce per-batch human decisions

The discovery loop fills the inbox; this layer reduces human time per inbox item.

| # | Pattern | Source | Status |
| --- | --- | --- | --- |
| 3.1 | Semi-autonomous triage | LatteReview, ResearchAgent | [future-directions.md §"Semi-autonomous triage"](future-directions.md#semi-autonomous-triage) |
| 3.2 | Tournament ranking for triage | AI co-scientist (Gottweis 2025) | [future-directions.md §"Tournament ranking for triage"](future-directions.md#tournament-ranking-for-triage) |
| 3.3 | Chain-of-Evidence pre-gate verification | ScientistOne (Meng et al. 2026) | [future-directions.md §"Chain-of-Evidence claim taxonomy for the Verifier"](future-directions.md#chain-of-evidence-claim-taxonomy-for-the-verifier) |

**Why after layer 1.** 3.1 and 3.2 presuppose a triage queue with enough volume that batching and ranking matter. Below ~10 candidates per research direction per cycle (the threshold named in 3.2's implementation gate), the existing per-card Mapper ordering and per-card human decision are sufficient and cheaper. 3.3 presupposes the Verifier is live and shipping (its prerequisite), and it pairs with 1.3 — where 1.3 *measures* Verifier drift, 3.3 *deepens* what the Verifier checks (typed claim→evidence chains), so the human reviews pre-cleared claims and re-checks fewer citations per card.

**Order within the layer.** 3.1 first — it removes human decisions from high-confidence candidates entirely (batch-approve). 3.2 second — it reorders the remaining lower-confidence candidates so the human reads from a tournament top-K rather than from a flat list. 3.2 without 3.1 reorders the full list; 3.1 without 3.2 leaves the residual list flat-ordered. Together they handle both ends. 3.3 is independent of 3.1/3.2 — it reduces per-card *verification* effort rather than per-card *triage* effort — and can land whenever the Verifier is mature enough to label its outputs. 3.2's *deterministic alternative* is learning-to-rank — a ranker trained on the operator's keep/discard history — see [future-directions.md §"Learning-to-rank for triage"](future-directions.md#learning-to-rank-for-triage); the two are mutually exclusive engines for the same ordering, not stacked, so this is an engine swap inside 3.2 rather than a new pattern.

### Layer 4 — Corpus-density gated

Patterns whose value is dominated by *vault size*, not by *nightly volume*. They become meaningful only once the corpus has accumulated to a critical density.

| # | Pattern | Source | Status |
| --- | --- | --- | --- |
| 4.1 | Reviewer agents on draft synthesis | ResearchAgent (Baek 2025), AI co-scientist Reflection | Partial coverage in [future-directions.md §"More agent roles"](future-directions.md#more-agent-roles-and-internal-reviewers) and §"LLM-judge gate for export" |
| 4.2 | Propagation debts queue | Autonovel cross-layer change propagation | [future-directions.md §"Propagation debts"](future-directions.md#propagation-debts) |
| 4.3 | Cross-project reading as personal AgentRxiv | Schmidgall & Moor 2025 (AgentRxiv) | [future-directions.md §"Cross-project reading as personal AgentRxiv"](future-directions.md#cross-project-reading-as-personal-agentrxiv) |
| 4.4 | NLI-based contradiction detection | NLI literature; surfaces the contradictions dashboard (ADR-16) | [future-directions.md §"NLI-based contradiction detection"](future-directions.md#nli-based-contradiction-detection) |

**Why last.** Each has a corpus-density precondition:

- 4.1 needs enough drafts that a pre-review pass catches more structural issues than it falsely flags. Below ~20 drafts per project, the human's own review is fast and the LLM pre-review is noise.
- 4.2 needs ~500 claim notes before the cost of materializing a dependents queue exceeds the cost of an Obsidian backlink walk.
- 4.3 needs ≥ 2 projects with ≥ 8 weeks of activity each. Single-project vaults give cross-project reading nothing to surface.
- 4.4 needs ~500 claim notes (the same floor as 4.2) before enough claims exist for cross-project, cross-MOC contradictions to hide unread. The `contradicts` relation ([ADR-9](../decisions/09-typed-relations-frontmatter.md)) and contradictions dashboard ([ADR-16](../decisions/16-contradictions-dashboard.md)) are **already adopted** as the confirm-surface, so 4.4 adds only the NLI candidate-proposer on top — deterministic (NLI, not an LLM), proposing only; the human confirms each `contradicts` link.

These three are also relatively independent — none requires another within the layer. They can ship in any order as their preconditions land.

## The Coder-lane exception (orthogonal to the layers)

The five layers above are about the **synthesis pipeline** — discovery → triage → review of claim notes, MOCs, and reference content. Every pattern there routes outputs to `10-inbox/` or a dashboard, never deciding what stays. The **Coder lane** is the one place where an *internal* autonomous keep/revert loop is admissible, because the Coder lane has the three preconditions synthesis lacks: a monotonic metric (tests pass / runtime / coverage), reversible changes (`git reset`), and independent iterations. See [why-no-autonomous-synthesis.md §"Scope: these boundaries apply to synthesis"](../../explanation/architecture/why-no-autonomous-synthesis.md#scope-these-boundaries-apply-to-synthesis).

| # | Pattern | Source | Status |
| --- | --- | --- | --- |
| C.1 | Coder-lane experiment loop | Chen et al. 2026 (long-horizon engineering), Karpathy Autoresearch | [future-directions.md §"Coder lane experiment loop"](future-directions.md#coder-lane-experiment-loop) |

**Why it is not in the layers.** C.1 is not "same gate, fewer presses" on the synthesis pipeline — it is a different lane with its own scalar success criterion that exists *before* the loop runs. It still respects the promotion gate: the loop keeps/reverts code variants internally against the metric, then routes the best variant to `done` for review, and the human promotes it into the project's working code. The keep/revert autonomy is bounded to `40-workbench/<project>/06-code/experiments/<run-id>/`; the policy MCP's review-gated-zone deny rule is untouched. It depends only on Layer 0 (reliable unattended runs); it shares nothing else with the synthesis layers, which is why it sits outside the dependency graph.

## Dependency graph

```text
Layer 0 ──────────────────────────────────────────────────────────────
                                                                       
  0.1 structured-output handoffs ──┐                                   
                                   ├──► reliable unattended runs       
  0.2 reflection on retry ─────────┘                                   
                                                                       
Layer 1 ──────────────────────────────────────────────────────────────
                                                                       
  1.1 discovery loop ──────────────────┐                               
        │                              │                               
        └─ 1.2 temperature sampling    │                               
                                       │                               
  1.3 CiteME harness ──── (parallel) ──┤
  1.4 discovery harness ─ (parallel) ──┤                               
                                       ▼                               
Layer 2 ─────────────────────── nightly inbox volume ─────────────────
                                                                       
  2.1 gap-seeking planner ──► feeds discovery queries to 1.1           
  2.2 inspiration retrieval ──► improves Writer outputs                
                                       │                               
                                       ▼                               
Layer 3 ────── human reviews larger / better-ordered batches ──────
                                                                       
  3.1 semi-autonomous triage ──► batch-approve high-confidence         
  3.2 tournament ranking ──► reorder residual candidates
  3.3 CoE pre-gate verification ──► fewer per-card citation checks               
                                       │                               
                                       ▼                               
Layer 4 ─────────── once corpus density justifies cost ───────────────
                                                                       
  4.1 reviewer agents on synthesis                                     
  4.2 propagation debts queue                                          
  4.3 cross-project reading
  4.4 contradiction detection ──► proposes contradictory pairs to confirm                                            

Coder lane (orthogonal — depends on Layer 0 only) ─────────────────────

  C.1 coder-lane experiment loop ──► best variant to done (review)
        (internal keep/revert on code vs. tests; promotion still gated)
```

## What each layer feels like at steady state

- **Pre-progression (today).** Every candidate is human-discovered, human-classified, human-reviewed. Retries fail loudly. The vault grows by direct human action.
- **After layer 0.** Same human workload; fewer interruptions for retry failures and format mismatches. The agent's nightly runs (when added) won't break on the third retry.
- **After layer 1.** Mornings start with a curated inbox produced overnight. The human's discovery effort drops sharply; the per-candidate triage effort stays the same. Verifier drift is caught by a metric instead of by surprise.
- **After layer 2.** The inbox is not only larger but better-aimed (gap-planner) and Writer drafts come with relevant prior thinking pre-loaded (inspiration retrieval). The vault starts feeling self-suggesting.
- **After layer 3.** Triage is bulk-approve plus a short tournament-ranked residual. Per-card human decisions drop to a small fraction of the inbox volume.
- **After layer 4.** Reviewer agents catch structural issues before the human's review. Propagation queue surfaces what to re-read when a claim shifts. Cross-project reading surfaces "I wrote about this two projects ago" connections the human no longer has to remember. Contradiction detection surfaces "these two claims conflict" pairs the human would never have read side by side — proposed, never auto-linked.

The cumulative shift: from "review every candidate, approve every triage, manually link across projects, hand-feed context to the Writer, watch the Verifier" to "review the morning's curated batch, approve in bulk, follow surfaced gaps." Same gate. Far fewer presses.

## What this is not

- **Not the autonomy boundary.** The 15 patterns above keep [architecture/why-no-autonomous-synthesis.md](../../explanation/architecture/why-no-autonomous-synthesis.md) unchanged. Autonomous keep/revert *for synthesis*, auto-promotion to canonical, scalar-metric optimization, and conversation-as-substrate remain refused. The lone admitted keep/revert loop is the Coder-lane exception (C.1), which operates on code against a pre-existing scalar and still routes its best variant through the human promotion gate — never on synthesis.
- **Not a substitute for the human review gate.** Every pattern routes outputs to `10-inbox/` or to a dashboard, never to review-gated zones. The policy MCP enforces this regardless of how much unattended activity accumulates.
- **Not a strict implementation order across layers.** Layers are dependency-ordered; *within* a layer (and between layers, where the preconditions are independent) the human can sequence by available time, budget, or felt friction.
- **Not a commitment.** This is a roadmap, not a contract. Any of the 15 (or the Coder-lane C.1) may be deferred indefinitely if the human finds they aren't experiencing the friction they relieve. See each pattern's "When to implement" and "Why not earlier" in [future-directions.md](future-directions.md) for the per-pattern triggers.

## Related

- The autonomy boundary that this progression respects: [architecture/why-no-autonomous-synthesis.md](../../explanation/architecture/why-no-autonomous-synthesis.md).
- The pattern-by-pattern borrow / adapt / ignore mapping: [architecture/why-pattern-provenance.md](../../explanation/architecture/why-pattern-provenance.md).
- The per-entry "when / why not earlier / prerequisites" detail: [future-directions.md](future-directions.md).
- The MVS implementation phases (a different axis — *building* the system, not *expanding agent autonomy*): [timeline.md](timeline.md).
