---
topic: roadmap
---

# Future directions

Things to consider once the core system is running and stable. The doc has two tiers:

- **Substantive proposals** (32 sections) — each carries a *when to implement* trigger, explicit prerequisites, pros / cons, and a *what this is not* boundary. Deferral has a clear off-ramp when conditions are met.
- **Backlog sketches** (5 brief items at the end) — ideas with enough shape to remember but not enough design to ship. See [§"Backlog — sketched ideas"](#backlog--sketched-ideas).

## What's in this document

**Autonomy within the boundary**

- [The discovery loop (proactive)](#the-discovery-loop) — nightly Hermes runs filling `10-inbox/03-candidates/`.
- [Coder lane experiment loop](#coder-lane-experiment-loop) — autonomous iteration on scalar success criteria.
- [Agent-proposed candidate claim notes](#agent-proposed-candidate-claim-notes) — Writer drafts claim candidates from a discussed source; human authors the canonical claim.

**Measurement, quality, and verification**

- [CiteME-style Verifier regression harness](#citeme-style-verifier-regression-harness) — measured attribution accuracy.
- [Chain-of-Evidence claim taxonomy](#chain-of-evidence-claim-taxonomy-for-the-verifier) — typed claims + integrity checks for the Verifier.
- [Fleet observability](#fleet-observability) — per-lane and per-skill cost / success / retry / latency.
- [Skill governance](#skill-governance) — lifecycle state machine and per-skill governance notes (maybe later if needed).
- [Propagation debts](#propagation-debts) — surfaced dependents when a high-traffic note changes.
- [LLM-judge gate for export](#llm-judge-gate-for-export) — informational prose review at the terminal artifact only.
- [Execution-trace reflection on retry](#execution-trace-reflection-on-retry) — packet rewriting from failure traces.

**Schema and retrieval extensions**

- [Scenario-typed retrieval](#scenario-typed-retrieval) — typed wikilinks for `contradicts` / `similar` queries.
- [MASSW-aligned paper-note aspects](#massw-aligned-paper-note-aspects) — three structured aspects per source.
- [Exploration-trace capture](#exploration-trace-capture-ara-style) — preserve rejected directions and dead ends as a Mapper output.

**Classical-method displacements (deterministic / hybrid candidates)**

These are the candidate displacements from [why-computational-methods.md §"Candidate displacements"](../../explanation/architecture/why-computational-methods.md#candidate-displacements-where-the-llm-can-still-recede) — tasks that currently reach for an LLM where a classical method does the job or narrows it to a hybrid.

- [NLI-based contradiction detection](#nli-based-contradiction-detection) — auto-surface candidate `contradicts` pairs for human confirmation.
- [Learning-to-rank for triage](#learning-to-rank-for-triage) — trained ranker as the deterministic alternative to the LLM tournament.
- [Claim-sentence classification](#claim-sentence-classification) — locate claim / aspect sentences before the LLM.
- [Classical prose metrics for the export gate](#classical-prose-metrics-for-the-export-gate) — mechanical checks before the LLM-judge.
- [Keyphrase extraction for tag candidates](#keyphrase-extraction-for-tag-candidates) — KeyBERT / YAKE tags alongside the classifier.
- [Discovery relevance scoring](#discovery-relevance-scoring) — reuse the `[!suggestions]` scorer to rank discovery candidates.
- [Record linkage for entity resolution](#record-linkage-for-entity-resolution) — IDs + string similarity for author / venue dedup.

**Pre-filtering and triage**

- [Semi-autonomous triage](#semi-autonomous-triage) — confidence-split classification queue; batch-approve high-confidence promotions.
- [Agent-consensus pre-filter](#agent-consensus-pre-filter) — second-profile pass to route consensus vs. disagreement.
- [Tournament ranking for triage](#tournament-ranking-for-triage) — pairwise comparison for high-volume candidate lists.

**Adjacent integrations and surfaces**

- [Literate `code-note` (weave + tangle)](#literate-code-note-weave--tangle) — drift-detected prose + executable code.
- [Memoria Inspector Obsidian plugin](#memoria-inspector-obsidian-plugin) — read-only admin views as a sidebar pane.
- [Hermes → Todoist gap-card integration](#hermes--todoist-gap-card-integration) — substantive gaps mirrored to a scheduling surface.
- [Static HTML admin reports](#static-html-admin-reports) — snapshot reports for retrospective review.
- [Open-design integration](#open-design-integration) — external rendering agent for polished deliverables.

**Multi-vault and cross-project**

- [Cross-vault read-only retrieval](#cross-vault-read-only-retrieval) — MCP-mediated foreign-vault search.
- [Cross-project reading as personal AgentRxiv](#cross-project-reading-as-personal-agentrxiv) — within-vault cross-project synthesis surfacing.

**Multi-machine memory**

- [Scripted session-history sync](#scripted-session-history-sync) — `profile export`/`import` snapshots carrying `state.db` chat history between machines (extends the [`memories/` junction](sync-and-coordination.md#syncing-profile-memory-across-machines-the-memories-junction)).
- [Hermes memory server](#hermes-memory-server-shared-memory-provider) — shared cloud / remote memory provider for real-time, concurrency-capable cross-machine recall.

## Autonomy within the boundary

### The discovery loop

Once `research-directions.md` (see [workflows/README.md](../../how-to/workflows/README.md)) is live and stable, the highest-leverage automation is the **discovery loop**: Hermes runs unattended on a schedule, fills `10-inbox/03-candidates/`, and posts a morning summary. This converts the system from *reactive* (you trigger discovery) to *proactive* (discovery happens while you sleep).

The pattern, drawn from Karpathy's Autoresearch by analogy:

```text
nightly (2am):
  1. read 00-meta/research-directions.md
  2. pick top N priorities (default: 3)
  3. for each priority: run `find` (max 10 candidates)
  4. ingest confirmed candidates from the previous day's inbox
  5. enrich any paper notes flagged as stale
  6. commit: "nightly: +N candidates, +M ingested, +K enriched"
  7. post morning summary to Telegram / email / dashboard
```

**Concrete defaults:**

- **Batch size, not duration.** Our bottleneck is human triage capacity, not compute. Cap at ~10 candidates per priority per night, not a wall-clock budget. (Karpathy's 5-minute time budget makes ML experiments comparable; here, it would just mean fewer candidates with no analog payoff.)
- **The loop generates; the morning triages.** The overnight pass only writes to `10-inbox/03-candidates/`. It does not promote to `_proposed_classification`, file synthesis, or close cards. All keep/revert decisions happen during the morning triage session.
- **Fail loud, not silent.** A failed run sends an alert (Telegram, email, or a dashboard flag). Silent cron failure is the dominant operational risk — three days of missing morning summaries should be impossible to overlook.
- **Cost budget.** ~10 ingests + 3 discoveries per night ≈ $1–3/day in API calls ≈ ~$500/year. Set this as an explicit budget; alert if a nightly run exceeds 2× the median.

**Prerequisites:**

- **[the always-on deployment option](deployment-options.md) (Syncthing + VPS)** — sleep-prone WSL2 won't survive the cron schedule.
- `research-directions.md` actively maintained.
- `00-meta/04-reference/screening-protocol.md` or equivalent inclusion criteria — without explicit criteria, the inbox floods with low-quality candidates and the morning triage time explodes.
- Two weeks of tuning before the loop is trustworthy. Expect the first nightly batches to require aggressive pruning.
- **Model routing configured** so embed / classify / quick-summary calls go to a cheap model — see [architecture/capability-stack.md](../../reference/architecture/capability-stack.md#model-routing-synthesis-on-claude-cheap-tasks-elsewhere). Without this the cost budget above blows out 3–5×.

**Cons.** Always-on infrastructure cost; first-month tuning friction; bad criteria flood the inbox; silent cron failures.

**When to implement.** After: (1) MVS is stable, (2) `research-directions.md` has been maintained for ≥ 4 weeks, (3) [the always-on option](deployment-options.md) is deployed, (4) inclusion criteria are written down. Not before.

### Coder lane experiment loop

Today the Coder profile executes one task per dispatch: a script change, a test addition, a fixture build. Iteration — "edit, run tests, keep if better, revert otherwise" — runs at human pace, with the human pressing the loop manually. When a task has a stable scalar success criterion (a passing test suite, a runtime benchmark, a coverage threshold), the human's per-iteration judgment is doing no work the metric isn't already doing. The loop is a candidate for unattended execution.

The pattern, adapted from Chen et al. 2026 (*Toward Autonomous Long-Horizon Engineering for ML Research*) and Karpathy Autoresearch: a lane-bounded skill — `Coder-experiment-loop` — reads a `code-experiment` card (a variant of the existing `code` card with a `success_metric:` field naming the test, benchmark, or measurement), then runs propose → test → keep-if-improved → revert-otherwise for up to N iterations or until a budget cap. Outputs land in `40-workbench/<project>/06-code/experiments/<run-id>/`. When the budget exhausts, the skill posts a single summary card to `done` (`review_status: requested`) containing the best variant, the diff against the starting point, and the metric trajectory. The human reviews the summary and decides whether the best variant promotes into the project's working code.

The autonomy is the inner loop. The gate is the human's review of the summary. The autonomy boundary in [architecture/why-no-autonomous-synthesis.md](../../explanation/architecture/why-no-autonomous-synthesis.md) explicitly admits this pattern in the Coder lane — see [§"Scope: these boundaries apply to synthesis"](../../explanation/architecture/why-no-autonomous-synthesis.md#scope-these-boundaries-apply-to-synthesis) for the precondition table.

**Cons.** Picking the wrong success metric is the dominant failure mode — the loop optimizes the metric, not the underlying goal, so a poorly-specified `success_metric:` produces a winner that game-played the test. Iteration count can balloon API spend if the budget isn't tight (the cost is N model calls × N test runs per card). The summary-card review is genuinely harder than reviewing a single change — the human now has to evaluate a trajectory, which is a different cognitive task.

**When to implement.** When the human notices themselves running the same "edit code → run test → revert if worse" cycle in the Coder lane more than ~10–20 times per project, *and* the cycle has a stable scalar success criterion that existed before the cycle started (a fixture, a test, a benchmark — not a judgment-call disguised as a metric). Below those triggers, ordinary Coder execution with human-in-the-loop is cheaper and the autonomy gain isn't paying for the infrastructure.

**Prerequisites.** A `code-experiment` card type (variant of `code` with `success_metric:`, `budget_iterations:`, `budget_cost_usd:`). A `Coder-experiment-loop` skill bound to the Coder lane, with the policy MCP permitting writes only to `40-workbench/<project>/06-code/experiments/<run-id>/`. A summary-card template (best variant, diff, metric trajectory, iteration log). A cron entry or on-demand trigger; the loop is not strictly overnight-bound, but overnight is the natural cadence.

**What this is not.** Not synthesis autonomy — [architecture/why-no-autonomous-synthesis.md](../../explanation/architecture/why-no-autonomous-synthesis.md) remains unchanged for every lane other than Coder. Not auto-promotion — the best variant goes to `done` for review, not into the project's working code; the human's review state is still the gate. Not metric-design autonomy — the human specifies `success_metric:` on the card, the agent does not propose it mid-run. Not exempt from the review-gated-zone deny rule — the policy MCP continues to block writes outside the experiment-run directory regardless of how many iterations the loop has executed.

### Agent-proposed candidate claim notes

The [distill](../../how-to/workflows/upstream/distill.md) stage is human-authored: after a source is discussed, the human reads it and writes 1–3 atomic claim notes by hand (the Writer assists with prose, but the human decides *what the claim is* and *whether the source yields one* — the [role × stage matrix](../../explanation/workflows/pipeline-design.md#role--stage-matrix)'s "Human authors the claim"). That is correct for the *judgment*, but it also imposes a blank-page cost on the *transcription*: every claim starts from scratch, even when the discussed source's key propositions are already legible.

The pattern: after a `discuss` card closes, the Writer proposes *candidate* claim notes from the discussed source — drafts that land in `10-inbox/03-candidates/` as `type: claim-candidate`, never in `30-synthesis/01-claims/`. Each candidate carries its provenance (the paper note plus the specific passage it derives from, located via [claim-sentence classification](#claim-sentence-classification)). The human edits, accepts (authoring the canonical claim note), or discards. The agent drafts; the human still decides what counts as a claim and how it is phrased.

**Cons.** This is the most judgment-adjacent automation in the roadmap — *what counts as a claim worth extracting* is synthesis judgment, exactly what the [autonomy boundary](../../explanation/architecture/why-no-autonomous-synthesis.md) protects. Two specific risks. (1) **Rubber-stamping** — a fluent candidate invites the human to accept it without the close reading that distillation is meant to force, hollowing out the `discuss → distill` loop. (2) **Framing capture** — the agent's phrasing anchors the human's, narrowing the space of claims they would have written unprompted (the same homogeneity risk as Bisht's hivemind finding). Over-proposing is worse than not proposing: a queue of plausible drafts can substitute for thinking rather than seed it.

**When to implement.** When `discuss` and `distill` are stable workflows *and* the human notices the blank-page cost of transcribing claims — not the reading or thinking — is the actual bottleneck. If comprehension is the bottleneck, this does not help; it accelerates only the writing-down step *after* understanding. Treat it as a *prototype on a handful of sources*, and measure the **accept-unedited rate**: a high rate is a warning (rubber-stamping), not a win.

**Prerequisites.** A stable `discuss` stage — proposing claims from an unread source defeats the purpose, so the candidate fires only after a `discuss` card closes. [Claim-sentence classification](#claim-sentence-classification) to ground each candidate in a specific source passage. A `claim-candidate` card type routing to `10-inbox/03-candidates/`, with the policy MCP denying writes to `30-synthesis/01-claims/`. An accept-unedited-rate metric to detect rubber-stamping.

**What this is not.** Not auto-filing — candidates land in the inbox; the human authors the canonical claim note. Not synthesis autonomy — [why-no-autonomous-synthesis.md](../../explanation/architecture/why-no-autonomous-synthesis.md) is unchanged; the human still owns *what counts as a claim* and *whether the source yields one*. Not a replacement for `discuss` — the candidate is proposed *after* the human has thought the source through, as a transcription aid, not a thinking substitute. Not promotion — an authored candidate is `maturity: seedling` at most; the path to evergreen/reference remains a separate human gate.

## Measurement, quality, and verification

### CiteME-style Verifier regression harness

Today's [Verifier profile](../../explanation/profiles/verifier.md) traces draft claims to claim notes by prompt, with no numeric quality signal. A prompt regression — a model change, a context-length cut, a subtle template edit — degrades attribution accuracy silently until the human notices wrong citations downstream. The Verifier is the gate that protects canonical synthesis from false attribution; running it without a regression harness is the kind of "agent does bookkeeping, but the bookkeeping is unmeasured" risk the design otherwise refuses elsewhere.

The pattern, adapted from Press et al. 2024 (*CiteME: Can Language Models Accurately Cite Scientific Claims?*): construct ~50 (excerpt → target-claim-note) pairs from approved drafts in the human's vault, where each excerpt is a passage from a `40-workbench/*/04-drafts/` note and the target is the specific `30-synthesis/01-claims/` claim note the excerpt is meant to cite. Score the Verifier nightly on the fixture; record accuracy in the [skill-lifecycle dashboard](../../explanation/dashboards/skill-lifecycle.md). The harness is the Verifier's *acceptance criterion* — a Verifier prompt change ships only when fixture accuracy is at or above the running 90th-percentile baseline.

The CiteME paper itself shows frontier LMs scoring 4–18% on the public benchmark and a tooled CiteAgent reaching 35%. Memoria's task is structurally easier (candidate space is bounded by one vault), so the baseline should land much higher — but the *shape* of the test (excerpt → cited artifact) and the *failure mode it protects against* (confident wrong attribution) transfer directly.

**Cons.** Fixture construction is one-time effort (a few hours of human labelling) plus periodic refresh as the vault's claim-note shape evolves. Nightly runs add a small recurring API cost. If the fixture is too small or too easy, the harness gives false confidence; if it is too large or too unrepresentative, the human stops trusting the signal.

**When to implement.** When the Verifier profile has shipped at least one prompt version and is running against real drafts. Implementing earlier — before the Verifier's behavior is settled enough to label its outputs — produces a fixture pinned to whichever prompt happened to be running when the fixture was built.

**Prerequisites.** Verifier profile is live and shipping work. At least one project has produced ≥ 20 approved drafts that cite ≥ 20 approved claim notes. A skill-lifecycle metric for `verifier_attribution_accuracy` with a running-baseline definition (e.g., 30-day 90th-percentile floor). A nightly cron entry on the Linter lane (dry-run posture matches the read-only nature of the harness).

**Companion benchmark (2026).** AutoResearchBench (Xiong et al. 2026) is the discovery-side analogue of this harness. It scores agents on *Deep Research* (find one specific target paper) and *Wide Research* (collect every paper meeting a set of criteria) — the two discovery modes the Librarian already runs. Where the CiteME harness certifies the Verifier's *attribution*, an AutoResearchBench-style fixture built from the vault's own corpus would certify *discovery* recall/precision: did the Librarian find the paper that should have been found, and collect the set it should have collected. Same shape — build the fixture from approved vault material, run it nightly on the Linter lane, gate prompt changes on the running baseline.

**What this is not.** Not a content-quality gate — Verifier still owns the binary "claim traces / doesn't trace" decision per draft; the harness only certifies that the gate itself hasn't drifted. Not a substitute for the human review gate — promotion still requires `review_status: approved`. Not a public-benchmark contribution — the fixture is private to the human because it draws from their vault.

### Chain-of-Evidence claim taxonomy for the Verifier

Today's [Verifier profile](../../explanation/profiles/verifier.md) runs five sub-checks (citation, claim-trace, duplicate, retraction, paper-note completeness) but treats all substantive claims alike — a numerical claim ("X reduces latency 40%") and a citation claim ("Smith 2024 showed Y") go through the same trace check. ScientistOne (Meng et al. 2026) shows that *typing* the claim sharpens what "traces to evidence" means for each kind, and that doing so is what separates 0/337 hallucinated references from baseline rates up to 21%.

The pattern, adapted from ScientistOne's **Chain-of-Evidence**: classify each substantive claim by type and require a type-appropriate evidence chain.

- **`citation`** — a claim attributed to a source. Evidence chain = the resolved `[@citekey]` + the claim note that carries it. (This is the Verifier's existing citation + claim-trace check, now named.)
- **`numerical`** — a reported number. Evidence chain = the specific source passage or table the figure is drawn from. Stricter than a generic claim-trace: the number must appear in the cited artifact, not merely be near it.
- **`methodological`** — a description of how something was done. Evidence chain = the method section / protocol the description summarizes.
- **`conclusion`** — a synthesis the human drew across sources. Evidence chain = the set of claim notes it rests on (the existing claim-trace, applied transitively).

ScientistOne's audit also defines two checks that **do not** map onto knowledge work — **score verification** (numbers reproduce under the benchmark's own evaluator) and **method–code alignment** (the prose matches the implementation). These presuppose executable experiments. They are in scope **only for the Coder lane**, where a `code-note` or `code-experiment` does have runnable code and a measurable score; they are explicitly out of scope for source/claim/draft verification.

**Cons.** Typing every claim adds an extraction step at draft time and a `_claim_type` slot the human (or Writer) must populate; mis-typing degrades the check rather than improving it. The four types do not cleanly partition every claim — a sentence can be both numerical and citation-bearing, forcing a "primary type" convention. As with all schema growth, partial adoption is worse than none: a half-typed corpus makes the type-aware checks unreliable.

**When to implement.** After the [CiteME-style regression harness](#citeme-style-verifier-regression-harness) is live — the harness is what tells you whether typing actually improves attribution accuracy or just adds overhead. Build the harness first, measure the untyped baseline, then adopt typing only if the typed checks measurably reduce false-clean verdicts.

**Prerequisites.** Verifier profile shipping against real drafts. A `_claim_type` convention on claim notes (or inline on draft claims) with a "primary type if ambiguous" rule. Verifier sub-checks extended to branch on type (numerical → passage-level match; the rest → existing trace). The regression harness extended to report accuracy per claim type, so the value of typing is visible.

**What this is not.** Not a truth check — typing sharpens *traceability*, not *correctness*; truth stays the human's domain (per [profiles/verifier.md §"What this profile is not"](../../explanation/profiles/verifier.md#what-this-profile-is-not)). Not the full ScientistOne audit — score verification and method–code alignment stay in the Coder lane. Not agent-assigned on canonical notes — the claim type is set when the claim is written, not inferred retroactively by an agent over approved synthesis.

### Fleet observability

Once the corpus is large enough that the human eye stops noticing slow regressions, stand up the [fleet-health dashboard](../../explanation/dashboards/fleet-health.md). It tracks per-lane and per-skill metrics (cost per task, success rate, retry rate, latency) on a daily / weekly / monthly / quarterly cadence.

**When to implement.** After Phase 6, and only when at least one of these is true:

- More than ~50 tasks per week — eyeballing the board misses regressions.
- Multiple lanes running scheduled work — drift in one lane is hard to spot from another.
- API spend on the order of $50+/month — cost optimization starts paying for the dashboard's overhead.

**Prerequisites.** A scheduled Hermes task that aggregates the audit log and board history into `lane-metric` and `skill-metric` notes under `00-meta/08-metrics/`. Until that aggregator exists, the dashboard is a placeholder.

### Skill governance

The expansion-threshold rule for *skills* — formal lifecycle states (`intake → proposed → scaffolded → testing → needs-review → approved → active → archived`), per-skill markdown registry notes in `00-meta/07-skills/`, the [`skill-lifecycle` dashboard](../../explanation/dashboards/skill-lifecycle.md), and the 7-step onboarding checklist. Today, adding a skill is a runtime operation only: edit `policy.allow.skills` in a lane-override file and drop the `SKILL.md` into the right profile's `skills/` folder. That works fine until the human is regularly graduating passthrough-skills to dedicated ones, retiring stale skills, or coordinating cross-lane permission changes — at which point bookkeeping in someone's head stops being sufficient.

**When to implement.** When at least two of these are true: (a) more than ~15 active skills across the seven profiles; (b) ≥ 2 passthrough-to-dedicated graduations per quarter; (c) recurring confusion about which skills are active in which lane, or whether a specific skill is in review vs. active.

**Prerequisites.** None beyond the runtime mechanism that already exists. The full design (state machine, registry format, onboarding checklist, graduation thresholds) is preserved in [skill-governance.md](skill-governance.md); the dashboard design summary lives in [dashboards/skill-lifecycle.md](../../explanation/dashboards/skill-lifecycle.md). Standing it up is mostly authoring the per-skill notes in `00-meta/07-skills/`, enabling the dashboard, and following the onboarding checklist for new skills from that point forward.

**What this is not.** Not a runtime gate — `policy.allow.skills` remains the runtime mechanism whether or not the governance overlay is active. Not a substitute for `SKILL.md` frontmatter — the authoritative per-skill metadata still lives there. The governance overlay is a *bookkeeping* layer on top of the runtime mechanism, valuable only when the runtime mechanism alone stops giving the human enough situational awareness.

### Propagation debts

When a high-traffic note changes — a `claim-note` promoted to `evergreen`, a `reference-note` updated, a `paper-note` retracted — the change should ripple to anything that depends on it. The implicit answer today is "follow the backlinks in Obsidian." That works at low corpus density. At high density it doesn't, because the human can't tell which dependents are *load-bearing* and which are casual mentions.

The pattern, borrowed from Autonovel's cross-layer change propagation: maintain a small "propagation debt" queue in the Linter's report. When a triggering change happens, enumerate the dependents that need re-evaluation and record them as actionable items, not just backlinks. Example: promoting a claim to `evergreen` queues "review each draft that cites this claim — does the prose still match?"

**When to implement.** When the corpus passes ~500 claim notes *and* the human notices reading a draft and realizing the cited claim has shifted. Below that density, the backlink walk in Obsidian is fine.

**Prerequisites.** A "trigger event" taxonomy (what changes warrant queuing dependents), a Linter check that materializes the queue into a dashboard, and a habit of working the queue down rather than letting it accumulate.

**What this is not.** Not automatic propagation. The agent never rewrites a draft to match a shifted claim. The queue is a *reading prompt*, not an edit pipeline.

### LLM-judge gate for export

The export step (`draft → deliverable`) currently has one quality check: `cite-check` verifies every citekey resolves to a real source. That catches mechanical breakage. It does not catch prose problems — argument gaps, tonal drift between sections, a paragraph that contradicts an earlier one.

A bounded LLM-judge gate would close that gap: at export time only, a `prose-check` command invokes a model to score the manuscript on a small fixed rubric (argument coherence, voice consistency, citation grounding, one-claim-per-paragraph). The result is a report attached to the export card; the human reads it and decides whether to revise or proceed. The gate is **terminal-only** — it never runs against synthesis, never auto-edits, never blocks the export by itself. The human reads the report and decides.

**When to implement.** When a deliverable has been re-exported more than twice because of issues a model could have caught on the first read.

**Prerequisites.** A small, stable rubric (drift-prone if open-ended), a Writer-lane skill that returns structured output, and the habit of reading the report before accepting the export.

**What this is not.** Not editorial control. The model proposes; the human disposes. If the model's report becomes the authority, the gate has failed its design intent.

### Execution-trace reflection on retry

Today's retry pattern (see [kanban-board/README.md](../../explanation/kanban-board/README.md#retry-pattern)) re-dispatches a failed card with the same handoff payload (`metadata`) — same prompt, same context, same expectations. Two retries on a flaky API succeed where one didn't. But two retries on a structurally broken prompt fail identically — the lane burns through retries and the card escalates to `blocked` with three identical failure traces stacked in the comments.

The pattern, borrowed from [NousResearch/hermes-agent-self-evolution](https://github.com/NousResearch/hermes-agent-self-evolution): on a retry, a **reflection skill** (loadable by the lane's primary worker) reads the *failure trace* — what tool was called, what arguments, what error came back, what the agent said next — and synthesizes a *modified* handoff payload for the next attempt. Not a model evaluating the work; a model reading the trace and adjusting the inputs. The next attempt may swap a tool, narrow a search, drop an irrelevant constraint, or escalate immediately if the trace shows the task is infeasible as written.

**When to implement.** When retry-induced API spend becomes visible in the [fleet-health dashboard](../../explanation/dashboards/fleet-health.md) — typically when sustained retry rate > 0.10 across a lane, or when a specific skill's `retry_rate` crosses 0.20. Below that volume the retry-as-identical-redispatch pattern is fine; the cost of building the reflection layer outweighs the savings.

**Prerequisites.** Structured failure traces (the Kanban dispatcher must capture tool calls and errors, not just the agent's final message), a reflection skill bounded to payload rewriting (never to direct execution), and a `reflection_count` field on cards distinct from the retry count (so the human can see when reflection itself is exhausted).

**What this is not.** Not autonomous evolution. The reflection layer never rewrites prompts, skills, or system contracts — it rewrites the *handoff payload* for one card. If the same kind of failure recurs across cards, that's a design issue the human resolves by editing the skill or the prompt; the reflection layer is per-card-scoped specifically to keep it from drifting into the autonomous-keep/revert pattern Memoria [refuses](../../explanation/architecture/why-no-autonomous-synthesis.md).

## Schema and retrieval extensions

### Scenario-typed retrieval

**Update — the base namespace is now adopted.** [ADR-9](../decisions/09-typed-relations-frontmatter.md) adopted a nested `relations:` block on claim-notes with a v1 vocabulary of `supports` and `contradicts` (opt-in, human-set), and [ADR-16](../decisions/16-contradictions-dashboard.md) the contradictions dashboard that reads it. This section now describes the *expansion* beyond that base — a wider vocabulary and richer per-link typing — still gated on density.

Beyond the adopted base, most links stay untyped: a plain `[[wikilink]]` from claim A to claim B does not say *why* A links to B. The human and the agent both have to infer the relation from context. At low corpus density this is fine — the links are few and the human remembers the reasons. At higher density, a useful query like "show me contradictory claims about X" cannot be answered directly from the graph; the human has to walk every backlink and re-derive the relation.

The pattern, adapted from PARNESS (Wang & Luan 2026): a `relation_type:` field on wikilinks (or on claim notes referencing other claim notes), with a small fixed vocabulary. PARNESS uses four values — `similar` / `contradictory` / `cross-domain` / `counter-intuitive` — chosen for ML/science workflows.

For Memoria, the base taxonomy is already live — [ADR-9](../decisions/09-typed-relations-frontmatter.md) adopted `supports` and `contradicts`. The prudent *expansion* is one value at a time: `similar` is the natural next addition (shape resemblance, distinct from evidential `supports`), with `cross-domain` or a fourth value only if the human finds themselves wanting it. The risk in adopting PARNESS's full four-value taxonomy from day one is taxonomy mismatch — `cross-domain` is concrete in ML benchmarks (a method from vision applied to NLP), less concrete in a knowledge-work vault.

**Cons.** Frontmatter schema growth has cost — templates need updating, the Linter needs a check for `relation_type:` values outside the vocabulary, dashboards need to surface the new field. The taxonomy may be wrong-shaped for knowledge work and require iteration. Most damagingly: if the human does not consistently set `relation_type:` on new links, the field becomes noisy (some links typed, most untyped) and queries return incomplete answers, eroding trust in the field.

**When to implement.** When two conditions hold together: (1) the vault contains ≥ 200 claim notes with ≥ 500 inter-claim wikilinks, *and* (2) the human notices themselves wanting to query "find work that contradicts X" or "find work similar in shape to X" and resorting to manual backlink walks. Below that, the cost of adopting and maintaining the field exceeds the value.

**Prerequisites.** Much of the base is already in place via ADR-9/16: the `relations:` block on the claim-note template, the Linter's relations-vocabulary check, and the [contradictions dashboard](../../explanation/dashboards/contradictions.md). The *expansion* adds a richer per-link form (`relation_type:` on a structured `links:` list) if pair-level metadata beyond the block is wanted, the vocabulary check extended to any new values, and a surface for them. A migration plan for existing untyped links — accept that they stay untyped, do not retrofit.

**What this is not.** Not a replacement for wikilinks — typed and untyped wikilinks coexist; typed is opt-in. Not a substitute for MOCs — MOCs provide topic-level grouping; relation-types provide pair-level semantics. Not the full PARNESS taxonomy — Memoria starts with two values and earns more by usage. Not agent-assigned — the human types the link when they make it; the agent does not infer `relation_type:` retroactively (that would re-introduce the agent-judgment-on-canonical surface that the autonomy boundary refuses).

### MASSW-aligned paper-note aspects

Today's paper-note frontmatter captures lifecycle and topical metadata (`topic`, `lifecycle`, `maturity`, `pub_status`, `_proposed_classification`) plus a free-text summary in the note body. The summary captures the human's read of the paper but is hard to query — "find all papers whose *method* is X" or "show me papers whose *outcome* contradicts the established result on Y" requires walking every summary by hand.

The pattern, adapted from MASSW (Zhang et al. 2024, *A New Dataset and Benchmark Tasks for AI-Assisted Scientific Workflows*): five aspects per paper — `context`, `key_idea`, `method`, `outcome`, `projected_impact` — derived from a 152,000-publication corpus and validated by comparing LLM-extracted aspects against human annotations. Memoria's prudent adoption is **three of the five fields**, not all five:

- **`_aspects.key_idea`** — the paper's central claim or contribution. Unambiguous; every paper has one.
- **`_aspects.method`** — the technique or approach used. Unambiguous for empirical papers; theoretical papers' "method" maps to their analytical framework.
- **`_aspects.outcome`** — the result reported. Unambiguous for empirical papers; for surveys / theoretical work it maps to the synthesis or framework produced.

Skipped (intentionally):

- **`context`** — overlaps with the existing `topic:` field and the paper-note's free-text intro. Adding it would duplicate.
- **`projected_impact`** — speculative, easy to hallucinate, hard to verify. Highest noise-to-signal among the five. Defer indefinitely; revisit only if the human finds themselves wanting the field.

The three fields are **optional**. Existing paper notes are not retrofitted. New ones gain the structure incrementally as the Librarian extracts them at ingest.

**Corroboration (2026).** Knows (Yu & Wang 2026) independently validates the core bet: a per-paper YAML sidecar of agent-readable fields raised weak-model comprehension by +29–42pp at lower token cost. That is the same idea as `_aspects.*` — structured per-paper fields beat raw prose for agents — and strengthens the case for adopting the three fields once the felt-need trigger below fires. Knows distributes the spec via a community hub rather than as a vault schema; Memoria's in-vault equivalent is the frontmatter slots described here.

**Cons.** Schema growth has compounding cost — templates, Linter rules, dashboards, frontmatter validators all need updating. Some papers (especially purely theoretical work) will resist clean fits, producing human friction at ingest. Inconsistent human usage degrades the field's retrieval value over time — once `_aspects.*` are partly populated, queries return incomplete answers and trust erodes. **Hardest of the recent design proposals to retire** — once notes carry `_aspects.*` fields, removing them means migrating notes back.

**When to implement.** When the human has felt the absence of structured-aspect retrieval — found themselves wanting to query "papers whose method is X" or "papers whose outcome contradicts Y" and resorted to free-text grep across summaries. Below that signal, the existing `topic:` field plus the free-text summary suffices and three new fields are overhead.

**Prerequisites.** Paper-note template updated with optional `_aspects.key_idea:`, `_aspects.method:`, `_aspects.outcome:` fields. Librarian profile prompt updated to extract these three at ingest with **explicit "leave blank if the paper doesn't fit"** instruction (not "stretch the field" — this is the rule that prevents `projected_impact`-style noise). A Linter check that flags `_aspects.*` values outside expected shapes (extreme length, prose vs. phrase). At least one dashboard or query that *uses* the fields (e.g., "outcome contradicts another paper in the corpus") — without a consumer, the fields accumulate unused.

**What this is not.** Not a replacement for the free-text summary — the body summary stays authoritative; aspects are structured slots, not a substitute. Not the full MASSW taxonomy — Memoria adopts three of five; expansion to `context` and `projected_impact` is a separate decision when usage justifies, and `projected_impact` is the field most likely to never warrant adoption. Not retroactive — existing paper notes stay as-is; only new notes gain the structure. Not agent-inferred for old notes — backfilling aspects from a free-text summary via LLM would re-introduce the kind of agent-judgment-on-canonical surface that Memoria's autonomy boundary refuses.

### Exploration-trace capture (ARA-style)

Memoria's vault keeps *approved* knowledge — the source notes, claim notes, and drafts that survived review. What it discards is the branching process that produced them: the candidates triaged out, the synthesis directions tried and abandoned, the claim that looked promising until a later source contradicted it. ARA / The Last Human-Written Paper (Liu et al. 2026) names this the **Storytelling Tax** — narrative compilation erases failure knowledge — and quantifies its cost for downstream agents (on one benchmark, 90% of total run cost was failed attempts that later agents must rediscover because no record survived). The same tax applies to a single human who, six months later, re-investigates a direction they already ruled out.

The pattern, adapted from ARA's **exploration-graph** layer: capture rejected directions and their *rationale* as a lightweight Mapper output — not raw thrash, but the decision points ("considered X as the organizing frame for this MOC; rejected because it splits the Y literature awkwardly"; "triaged out these 8 candidates because they predate the 2024 method shift"). The artifact is a per-project `exploration-log` note (or a section of the MOC) that records *what was not done and why*, linked from the synthesis it shaped.

**Cons.** The whole value of the vault is curation; preserving every dead end fights that directly — an exploration log that captures raw thrash becomes noise that buries the signal. The practice is capturing *decisions with rationale*, not *every path*, and that judgment is itself human labor at exactly the moment (rejecting a direction) when the human wants to move on. If the log is not maintained consistently it becomes a misleading partial record — worse than no record. Unlike ARA, Memoria has no machine-execution consumer for the trace, so the only beneficiary is the future human, which makes the cost/benefit entirely dependent on whether re-investigation actually recurs.

**When to implement.** When the human notices themselves re-deriving a *negative* conclusion — re-reading candidates they already rejected, or re-attempting a synthesis frame they already abandoned — and wishing they'd recorded why the first time. Below that felt pain, the curated-vault default (keep what survived, discard the rest) is correct and this is overhead.

**Prerequisites.** A lightweight `exploration-log` convention (per-project note or a dedicated MOC section) with a fixed shape (decision / options considered / rejected because / date). A Mapper prompt that proposes log entries at natural decision points (MOC restructure, large triage pass) rather than continuously. A convention — kept by habit, not enforced by the Linter — of recording rationale, not thrash.

**What this is not.** Not an audit log — the [audit log](../../explanation/dashboards/audit-log.md) records *what agents did*; the exploration log records *what the human decided not to pursue and why*. Not the full ARA artifact — Memoria adopts only the exploration-graph idea, not the four-layer machine-executable package (Memoria is single-user and human-curated, not agent fork/diff/merge). Not automatic — the agent proposes entries at decision points; the human decides what is worth preserving, because a rejected direction is a synthesis judgment, not a structural event.

## Classical-method displacements (deterministic / hybrid candidates)

### NLI-based contradiction detection

Memoria's [`contradicts` typed link](#scenario-typed-retrieval) and the [contradictions dashboard (ADR-16)](../decisions/16-contradictions-dashboard.md) both presuppose that someone has *noticed* the contradiction. Today that someone is the human: they read two claims, see the conflict, and type the link. At low claim-note density that works — the human holds the corpus in their head. As claim notes accumulate across projects, contradictions hide in the long tail: two papers years apart, in different MOCs, that the human never reads side by side. A relation can only be typed once it is noticed, and *noticing* does not scale with the corpus.

The pattern, surfaced as a candidate displacement in [why-computational-methods.md](../../explanation/architecture/why-computational-methods.md#candidate-displacements-where-the-llm-can-still-recede): run a **natural-language-inference (NLI)** model over topically-near claim-note pairs to *propose* contradictions for the human to confirm. Pre-filter with the embeddings already computed for `similarity-check` (cosine above a threshold → O(k) candidate pairs, not O(n²)); run a sentence-pair NLI model (`roberta-large-mnli` or a domain-tuned variant) on each pair → entailment / contradiction / neutral + score; route pairs labelled contradiction above a confidence threshold to the contradictions dashboard. The human confirms (types the `contradicts` link) or dismisses. This is the **candidate-generation engine** the dashboard needs — [ADR-16](../decisions/16-contradictions-dashboard.md) supplies the surface and [ADR-9](../decisions/09-typed-relations-frontmatter.md) the link type, but neither answers "which pairs are worth showing." NLI answers it, deterministically and locally.

**Cons.** NLI models are trained on general-domain premise/hypothesis pairs; scientific claims with hedges, scope conditions, and domain terms produce false contradictions ("X improves Y" vs. "X improves Y only under condition Z" can flag as a contradiction when the two are compatible). The pre-filter threshold trades recall against cost — too loose and NLI runs on too many pairs, too tight and cross-domain contradictions are missed. The dominant failure mode is a flood of low-precision candidates that trains the human to ignore the dashboard. And contradiction is sometimes *the point* — a paper refuting an earlier one is a wanted finding, not an error — so the surface must frame candidates as "worth a look," never as defects.

**When to implement.** When two conditions hold together: (1) the corpus has enough claim notes that contradictions plausibly hide unread — the same ~500-claim-note floor that gates [propagation debts](#propagation-debts) and [scenario-typed retrieval](#scenario-typed-retrieval) is a reasonable trigger; and (2) the `contradicts` relation type ([ADR-9](../decisions/09-typed-relations-frontmatter.md)) and the contradictions dashboard ([ADR-16](../decisions/16-contradictions-dashboard.md)) are in active use — both are now adopted (they shipped human-set; this detector is the proposer deliberately deferred out of their v1), so proposed candidates have a place to land and a link to be confirmed into. This graduates the [consistency-checker backlog sketch](#more-agent-roles-and-internal-reviewers) into a designed proposal.

**Prerequisites.** Note embeddings already computed (they are, for `similarity-check`). A claim-extraction step that yields the comparable proposition from each claim note (the claim sentence, not the whole note body) — shares machinery with the claim-sentence detection in [why-computational-methods.md §"Candidate displacements"](../../explanation/architecture/why-computational-methods.md#candidate-displacements-where-the-llm-can-still-recede). A sentence-pair NLI model available locally (`roberta-large-mnli` / `deberta-v3-large-mnli`) with a contradiction threshold tuned on a handful of known vault contradictions. ADR-9 and ADR-16 are adopted (done) — the remaining gate is claim density and felt need. A nightly cron slot on the Linter lane (its read-only posture matches a detector that only writes to a dashboard) running over claim notes added or changed since the last pass.

**What this is not.** Not auto-linking — NLI *proposes*; the human types the confirmed `contradicts` link. This is the same boundary scenario-typed retrieval draws ("the agent does not infer `relation_type:`") read correctly: the agent never writes the relation onto a canonical note, it populates a review queue the human acts from. Not a truth judgment — NLI labels the logical relation between two stated claims, not which one is correct; truth stays the human's call, consistent with the Verifier's [*not a fact-checker*](../../explanation/profiles/verifier.md#what-this-profile-is-not) stance. Not an LLM call — the entire point is a deterministic, local, reproducible detector (see the anti-pattern "ask the LLM whether two claims contradict"). Not a replacement for human-noticed contradictions — it augments the human's own typing by catching the long-tail pairs they will never read side by side.

### Learning-to-rank for triage

The triage queue ([semi-autonomous triage](#semi-autonomous-triage), [tournament ranking](#tournament-ranking-for-triage)) orders candidates so the human reads the best first. Tournament ranking does this with LLM pairwise comparisons — `n log n` LLM calls, non-reproducible, and generic. Once the human has a history of keep/discard decisions, that ordering is *learnable* from features Memoria already computes.

The pattern, surfaced as a candidate displacement in [why-computational-methods.md](../../explanation/architecture/why-computational-methods.md#candidate-displacements-where-the-llm-can-still-recede): a gradient-boosted ranker (LightGBM `LambdaRank` or XGBoost `rank:ndcg`) trained on the human's past keep/discard (and read-order) decisions, scoring candidates from features already on hand — embedding similarity to `research-directions.md`, citation-graph proximity to vault papers, recency, venue, scite supporting count. The result is a reproducible, auditable ranking; the LLM tournament becomes the cold-start fallback only. This mirrors the `_proposed_classification` story exactly: a model trained on the operator's own decisions, sharpening as the override history grows.

**Cons.** Needs ~hundreds of labeled decisions before it beats the existing weighted score. Features must be assembled per candidate (mostly already computed for `[!suggestions]`). Like any trained model it drifts as interests shift — mitigate with the same monthly retraining loop as the classifier.

**When to implement.** When two conditions hold: (1) the triage queue is large enough that ordering matters (~10+ candidates per direction per cycle, the [tournament-ranking](#tournament-ranking-for-triage) threshold), and (2) the human has accumulated enough keep/discard history to train (~hundreds of decisions). Below either, keep the scalar ordering or the LLM tournament.

**Prerequisites.** A per-candidate feature vector (largely shared with the `[!suggestions]` scorer); the human's historical triage decisions as labels; a LightGBM/XGBoost training + inference path; the retraining schedule (reuse the classifier's monthly cadence).

**What this is not.** Not a replacement for the human triage decision — it orders, the human still picks. Not stacked with the LLM tournament — it is the deterministic *alternative* to it; the two are mutually exclusive engines for the same ordering task. Not auto-discard — low-ranked candidates are still shown, just lower.

### Claim-sentence classification

Two tasks need to locate the claim-bearing sentences in a document: the Verifier's claim-trace (which substantive claims in a draft need a supporting claim note?) and the planned [`_aspects.*` extraction](#massw-aligned-paper-note-aspects) (which sentence states the `key_idea` / `method` / `outcome`?). Both are currently unspecified or routed to an LLM that reads the whole text.

The pattern, surfaced as a candidate displacement in [why-computational-methods.md](../../explanation/architecture/why-computational-methods.md#candidate-displacements-where-the-llm-can-still-recede): a sentence classifier that labels each sentence by rhetorical role — background / method / result / conclusion (CoreSC/ART schemes), or, more cheaply, a rule layer (sentences carrying a citation, a hedge, or a numeric assertion are claim-bearing). The classifier or heuristic locates candidate sentences deterministically; an LLM (or extractive selection) only phrases the residual. This demotes both tasks from generative to **hybrid** — the deterministic narrowing the [hybrid pattern](../../explanation/architecture/why-computational-methods.md#the-hybrid-pattern) already applies to `cite-check`.

**Cons.** Zoning classifiers need labeled scientific sentences or a pre-trained model (e.g., on PubMed/ART corpora). Rule-based detection has lower recall on prose that asserts without citing. Domain text varies — a methods-heavy empirical paper and a theoretical one have different rhetorical shapes.

**When to implement.** When the Verifier's claim-trace or the `_aspects` extraction is being built and the cost / latency / reproducibility of an LLM reading the whole document becomes a felt constraint — typically once ingest volume is high enough that per-document LLM passes dominate cost.

**Prerequisites.** A sentence segmenter (spaCy / syntok); a pre-trained rhetorical-zone model or a labeled seed set; integration into both the Verifier claim-trace and the `_aspects` extraction step (they share the machinery).

**What this is not.** Not claim *verification* — that is the Verifier's trace against sources; this only *locates* the claims. Not aspect *phrasing* — the LLM or an extractive step still composes the field value. Not a replacement for reading — it narrows what the LLM reads; it does not replace judgment about what a claim means.

### Classical prose metrics for the export gate

The [LLM-judge gate for export](#llm-judge-gate-for-export) is framed as an LLM scoring the manuscript on a small rubric (argument coherence, voice consistency, citation grounding, one-claim-per-paragraph). Half of that rubric is mechanical and does not need an LLM.

The pattern, surfaced as a candidate displacement in [why-computational-methods.md](../../explanation/architecture/why-computational-methods.md#candidate-displacements-where-the-llm-can-still-recede): a deterministic prose-metrics pass at export — readability (Flesch–Kincaid), passive-voice ratio, citation density (cites per paragraph), n-gram repetition (phrases reused across sections), sentence-length outliers, one-claim-per-paragraph violations. These produce a structured report; the LLM-judge then contracts to the genuinely semantic checks (argument coherence, tonal drift). Demotes the export gate from generative to **hybrid**.

**Cons.** Metrics flag *symptoms*, not substance — a low readability score does not mean the argument is wrong, and a passive sentence may be correct. Thresholds need calibration to the operator's voice (academic prose is denser than the library defaults assume). Over-weighting metrics risks optimizing for the metric rather than the writing.

**When to implement.** When the export gate is being built and the operator notices the LLM-judge spending its attention (and cost) on mechanical issues a script could flag. Pairs naturally with building the LLM-judge gate itself — build the metrics pass first, let the LLM handle only what is left.

**Prerequisites.** A prose-metrics library (`textstat` for readability; spaCy for passive-voice and sentence parsing; simple n-gram counting); a small calibrated threshold set for the operator's domain; integration as the deterministic pre-pass to the export gate.

**What this is not.** Not editorial judgment — metrics inform, the human disposes (the same posture as the LLM-judge). Not a quality gate by themselves — they never block an export alone; they narrow the LLM-judge. Not a style enforcer — the operator owns voice; metrics surface outliers, not rules.

### Keyphrase extraction for tag candidates

At ingest the Librarian proposes topic/tag labels via the `_proposed_classification` classifier (with LLM fallback). Tags drawn from a fixed classifier vocabulary miss emerging or paper-specific terms — the ones that appear as the corpus moves into a new subfield the classifier was not trained on.

The pattern, surfaced as a candidate displacement in [why-computational-methods.md](../../explanation/architecture/why-computational-methods.md#candidate-displacements-where-the-llm-can-still-recede): keyphrase extraction (KeyBERT — embedding-based; or YAKE — statistical) over the paper note to propose candidate tags alongside the classifier's labels. Cheap, local, and it complements rather than replaces the classifier — the classifier knows the operator's established vocabulary, keyphrase extraction catches what is new.

**Cons.** Extracted phrases are surface forms, not controlled-vocabulary terms — they need mapping (a "machine learning" phrase and an "ML" tag must reconcile). Statistical methods (YAKE) over-weight frequent terms; embedding methods (KeyBERT) need the embedding model loaded (it is). Surfaced without a confirm step, they become tag noise.

**When to implement.** When the operator finds the classifier's fixed vocabulary missing paper-specific terms they want as tags — typically as the corpus enters subfields the classifier has not seen.

**Prerequisites.** KeyBERT or YAKE in the ingest path; the existing embedding model (for KeyBERT); a confirm step in `classify` so extracted phrases map onto the controlled vocabulary rather than auto-applying.

**What this is not.** Not auto-tagging — extracted phrases are candidates the operator confirms. Not a replacement for the classifier — it complements it. Not free-text tagging — phrases still reconcile to the controlled vocabulary.

### Discovery relevance scoring

The [discovery loop](#the-discovery-loop) surfaces candidate sources; the discovery-quality harness ([autonomy-progression 1.4](autonomy-progression.md)) measures whether it finds the right ones. Between them sits the question of how candidates are *ranked* for the morning triage — currently reuse-or-LLM.

The pattern, surfaced as a candidate displacement in [why-computational-methods.md](../../explanation/architecture/why-computational-methods.md#candidate-displacements-where-the-llm-can-still-recede): extend the existing `[!suggestions]` weighted scorer (embedding similarity + shared-citation graph + topic-tag overlap) to rank discovery candidates against `research-directions.md`, rather than asking an LLM "is this relevant." It is the same deterministic scorer Memoria already runs for link suggestions, repointed at the discovery inbox.

**Cons.** Cold-start weighting — the weights tuned for link suggestions may not transfer to discovery ranking. A purely similarity-based score favors candidates near what is already in the vault, under-weighting genuinely novel directions (the same homogeneity risk the discovery loop's temperature sampling addresses). Tune against the 1.4 discovery harness.

**When to implement.** When the discovery loop is producing enough candidates that their ordering matters for triage efficiency, and before reaching for an LLM to judge relevance. Essentially free if the `[!suggestions]` scorer already exists.

**Prerequisites.** The `[!suggestions]` weighted scorer; `research-directions.md` as the relevance target; the 1.4 discovery harness to tune weights against.

**What this is not.** Not candidate *generation* — that is `find`'s API/search calls; this only ranks what `find` surfaces. Not auto-triage — it orders the inbox, the human still triages. Not novelty-aware by default — pair it with temperature-sampled generation so similarity ranking does not collapse discovery onto the existing corpus.

### Record linkage for entity resolution

Ingest resolves authors, venues, and organizations to authoritative entity notes. When two papers list "J. Smith" or "Proc. of X," the Librarian must decide whether they are the same entity. Asking an LLM is slow and non-reproducible.

The pattern, surfaced as a candidate displacement in [why-computational-methods.md](../../explanation/architecture/why-computational-methods.md#candidate-displacements-where-the-llm-can-still-recede): record linkage — resolve by stable identifier first (ORCID for authors, OpenAlex / ISSN for venues, ROR for organizations, all available from the enrich APIs), then fall back to string-similarity blocking (normalized name + affiliation / co-author overlap) for entries without IDs. Deterministic, and the IDs make most matches unambiguous.

**Cons.** Missing IDs force the fuzzy path, which carries a false-merge risk — two distinct "J. Smith"s merged is hard to unwind. Name changes and transliteration variants need handling. The blocking threshold trades precision against recall.

**When to implement.** When the entity corpus is large enough that duplicate person/venue notes appear, or when a disambiguation error has already cost the operator (a merged-author note that conflated two people). Below that, the per-ingest API ID lookup is sufficient.

**Prerequisites.** ID fields captured at enrich (ORCID / OpenAlex / ROR); a string-similarity + blocking library (`dedupe`, `recordlinkage`) for the no-ID fallback; an operator-confirm step for low-confidence merges.

**What this is not.** Not auto-merge — low-confidence matches are proposed for operator confirmation (merging two entity notes is a judgment, like the Verifier's duplicate-claim stance). Not a replacement for the API IDs — IDs are the primary key; string similarity is the fallback. Not cross-vault identity — that is the [foreign-vault pattern](#cross-vault-read-only-retrieval)'s concern.

## Pre-filtering and triage

### Semi-autonomous triage

Classification today is one note at a time: the Librarian proposes `_proposed_classification` on each new paper note, and the human promotes the proposed fields to canonical (`topic`, `projects`, etc.) during the morning triage. Most promotions are rubber-stamps — the classifier proposed exactly what the human would have chosen — but the human still opens each note, reads the proposal, and confirms. At low ingest volume that per-note cost is invisible; once the [discovery loop](#the-discovery-loop) is filling `10-inbox/03-candidates/` overnight, confirming each note becomes the dominant triage cost.

The pattern, adapted from LatteReview and ResearchAgent (Baek et al. 2025): attach a confidence score to each `_proposed_classification` and split the triage queue by it. High-confidence proposals (the classifier's own probability above a tuned threshold, corroborated where the field already exists elsewhere in the corpus) surface in a **batch-approval view** — a dashboard listing the proposed promotions with their confidence, which the human approves in one action after a skim. Low-confidence proposals stay in the per-note manual queue. The human's attention shifts from *every* note to *only the uncertain ones*.

**Cons.** A miscalibrated threshold is the dominant failure mode — too high and nothing batches (no saving); too low and wrong classifications slip through a batch-approve the human didn't actually scrutinize. Batch approval invites exactly the rubber-stamping the per-note step guarded against: the human can approve 40 promotions without reading any, and a systematic classifier bias then propagates into canonical `topic` / `projects` fields at scale. The confidence score is only as trustworthy as its calibration against the human's own past overrides, which takes a history to build.

**When to implement.** When two conditions hold together: (1) ingest volume is high enough that per-note classification confirmation is a felt cost — typically once the [discovery loop](#the-discovery-loop) is running and producing tens of candidates per cycle; and (2) the `_proposed_classification` classifier has accumulated enough of the human's accept/override history that its confidence scores are calibrated rather than guessed. Below either, per-note promotion is cheap enough and safer.

**Prerequisites.** A confidence signal on `_proposed_classification` (the classifier's probability, or agreement between the classifier and an existing corpus value). A `triage-approval` dashboard that lists high-confidence promotions for batch action and records the batch decision in the audit log. A tuned threshold with a defined recalibration cadence (reuse the classifier's monthly retraining loop). A per-batch sampling habit — the human spot-reads a few promotions per batch so batch-approve never becomes blind-approve.

**What this is not.** Not auto-promotion — the human still presses approve; the gate is structurally intact, it just moves from per-note to per-batch. Not a replacement for the human's classification judgment — it accelerates *confirmation* of high-confidence proposals, never the decision on the uncertain ones, which stay manual. Not auto-applied to low-confidence proposals — those route to the existing per-note queue. Consistent with the [autonomy boundary](../../explanation/architecture/why-no-autonomous-synthesis.md): the agent proposes and scores; the human disposes, in bulk where the signal is strong.

### Agent-consensus pre-filter

Today the Librarian profile runs a card to completion, completes it to `done` (`review_status: requested`), and the human decides whether to approve. Most cards approve quickly — the agent did exactly what was asked, the frontmatter is correct, the source is well-classified. A few cards require real deliberation. The human pays the same review-attention cost for both, and the easy cards dominate the volume.

The pattern, adapted from Long 2026 (*AI-Supervisor: Autonomous AI Research Supervision via a Persistent Research World Model*): a *consensus pre-filter* between worker output and human review. Instead of routing a Librarian output directly to human review, dispatch the same card to a second profile (a Mapper in read-only mode, or a second Librarian pass with a different prompt). When the two outputs agree on key fields (`_proposed_classification`, suggested wikilinks, frontmatter values), the card reaches review with a `consensus: agreed` flag and the human can batch-approve. When they disagree, the card routes to a distinct review queue with a `consensus: disagreement` flag and the disagreement is the first thing the human sees.

This is a *milder* version of Memoria's blocking-human-review pattern. The human gate remains structurally required — consensus does not bypass review, it filters review. Long 2026's framing treats agent consensus as sufficient for commit; Memoria's adaptation treats it as a pre-filter only.

**Cons.** Doubles API cost per card the pre-filter touches. Two agents with correlated errors may agree on wrong outputs (the AI co-scientist tournament problem at smaller scale) — agreement rate is not the same as accuracy. **This correlated-error risk is now empirically documented:** Bisht et al. 2026's hypothesis-hivemind experiment found that frontier models from independent providers (Anthropic, OpenAI) converge semantically on open-ended generation tasks (inter-model cosine similarity stayed high even when diversity was the goal), so "the effective epistemic sample size is close to one regardless of how many systems are consulted." Consensus between two models — especially two strong models — can therefore manufacture false confidence rather than independent corroboration. This sharpens the prototype's most important measurement (human disagreement with high-confidence consensus) and argues for using *deliberately different* prompts/models, or a contrarian second pass, rather than two runs of the same configuration. Adds another lane, another card flag, and another dashboard surface — design complexity grows. The savings depend on what fraction of cards actually reach consensus, which is unknown today.

**When to implement.** As a *prototype* on one profile (start with Librarian, where the task has the clearest agreement criterion) for ~50 cards. Measure (a) consensus rate, (b) human agreement with consensus outputs, (c) human disagreement with high-confidence consensus (the worrying case — agents agreed but got it wrong). Decide based on data whether to extend to other profiles or abandon.

**Prerequisites.** Librarian profile shipping and producing routine output. Defined "key fields" for agreement (the frontmatter slots that count as agreement vs. divergence). A `consensus:` field on cards (`agreed` / `disagreement` / `not-checked`). A second-profile-pass skill that runs the same task with a different prompt or model, returning comparable output. A budget for ~2× inference cost on cards the pre-filter touches.

**What this is not.** Not a replacement for human review — the review gate (`review_status: approved`) is still structurally required for promotion. Not auto-approval — consensus does not bypass the human; it routes them to a faster queue. Not multi-agent voting — two agents is the prototype scale; expanding to N agents is a separate decision with worse cost characteristics. Not the AI-Supervisor pattern verbatim — Long 2026 commits to the RWM on consensus alone; Memoria pre-filters but does not commit.

### Tournament ranking for triage

When the inbox holds ten or more candidate sources for the same research direction, the human's triage step is "rank these and discard the bottom half." Today the Mapper profile orders candidates by relevance score; the human reads from the top until they stop finding value, then closes the rest. This works at moderate inbox volume but flattens late-tier candidates into a long tail of near-identical scores that the human either over-reads or under-reads.

The pattern, adapted from Gottweis et al. 2025 (AI co-scientist) and Baek et al. 2025 (ResearchAgent): when the candidate set crosses ~10, the Mapper (or a small dedicated triage skill) runs a **pairwise tournament** — each candidate is compared against several others on a small fixed rubric (relevance to the active research direction, methodological novelty, citation context overlap with existing claim notes), and the win-loss record produces a triage-aware ordering distinct from the raw relevance score. The human reads the tournament top-K, not the raw top-K.

**Cons.** Tournament rounds multiply API calls (n^2 in the naïve case, n log n with bracket structure). The rubric is another piece of LLM-judgment surface that drifts and needs review — adding a tournament step is adding another place where the agent's bias can leak into human decisions. Most importantly, it does not change what the human does — they still pick from a top-K — so the value is only in *how good the top-K is*, which is hard to measure without a separate ground-truth.

**When to implement.** When two conditions hold together: (1) the daily inbox exceeds ~10 candidates per research direction often enough to be a recurring friction, *and* (2) the human notices themselves discarding from the middle of the candidate list rather than from the bottom — a signal that scalar ranking is mis-ordering. Below either threshold, the existing Mapper ordering is sufficient.

**Prerequisites.** A stable [research-directions.md](../../how-to/workflows/README.md#research-directions-steering-input) so the tournament rubric has something to score relevance *against*. The discovery loop running long enough to produce the candidate volume that justifies tournament cost. A budget for ~n^2 inference calls per triage session (small per session, recurring across nights).

**What this is not.** Not a quality gate — the tournament reorders, it does not decide. Not autonomous keep/revert — the human still chooses which candidates to ingest; the tournament only changes the order they are read in. Not the same pattern as the full AI co-scientist evolve loop, which scales test-time compute on the *output* (hypothesis quality); here the tournament only orders *inputs* to the human's existing triage decision.

## Adjacent integrations and surfaces

### Literate `code-note` (weave + tangle)

Today's `code-note` (see [vault/note-types.md](../../reference/note-types.md#note-types)) is markdown prose plus a separate code artifact in the same folder. The link between them is convention: humans keep the prose in sync with the source, the Linter doesn't enforce it. Drift between what the code *does* and what the note *says it does* is a real failure mode at corpus scale.

The pattern, borrowed from [tlehman/litprog-skill](https://github.com/tlehman/litprog-skill) (which implements Knuth's 1984 literate-programming model): a `code-note` becomes a single `.lit.md` source from which two artifacts are derived — **weave** (the human-readable narrative-with-code that lives in the vault) and **tangle** (the executable source that lives alongside, runnable as-is). Edit either; the other regenerates. The prose-source drift problem becomes structural: drift is detected the moment the artifacts disagree.

**When to implement.** When prose-vs-source drift starts producing real incidents — a researcher reading a `code-note` to understand a result, finding the code does something different, and having to reconstruct which is correct. Below that pain threshold, the convention-based pattern is fine.

**Prerequisites.** A litprog implementation that handles Python and Jupyter notebooks at minimum (Memoria's two dominant code surfaces), a build hook integrated into the Coder profile's compile step, and a Linter check that flags `.lit.md` files whose weave-hash and tangle-hash disagree (a sibling of `vault-hash-drift`).

**What this is not.** Not a replacement for `code-note` as a type. The litprog file *is* a `code-note`, with `format: literate` distinguishing it from `format: notebook` and `format: script`. Not an enforcement mechanism either — the human still owns whether to use literate format for a given project; small scripts can stay convention-based.

### Memoria Inspector Obsidian plugin

The five existing channels (Obsidian dashboards, command palette, CLI, Telegram, API server — see [architecture/README.md](../../explanation/architecture/README.md#human-channels)) cover daily workflow well but leave a small gap: a *browse-the-Hermes-state* admin channel. CLI is precise but not discoverable; dashboards aggregate rather than drill down per session. The temptation is to adopt a community web UI (e.g., the `hermes-workspace` hackathon project); the architectural problem is that any peer system competes for the same modes the existing channels already cover, ships a chat tab that bypasses the policy MCP, and locks Memoria into someone else's maintenance schedule.

The pattern: build a small Obsidian plugin (~500–1500 lines of TypeScript) exposing read-only Hermes admin views as a sidebar pane — Sessions, Audit, Skills, Memory, all tabs. Connects to the API server on `127.0.0.1:8642`. No chat (that surface belongs to ACP); no editing (skills and memory are write-through the compilation pipeline, not the inspector). The plugin extends Obsidian-as-interface rather than introducing a peer.

**When to implement.** When CLI forensics start dominating the human's time, *and* the desire to browse rather than query becomes recurrent. A rule of thumb: more than ~3 `hermes kanban show` invocations per session means dashboards aren't drilling deep enough and a browse surface is overdue.

**Prerequisites.** The API server reachable on loopback with a stable contract for session/audit/skill/memory queries, an Obsidian plugin scaffold that participates in the vault's mobile-app sync path (so the inspector is reachable on phone via Obsidian mobile rather than requiring a separate PWA), and a policy guarantee that read-only paths in the plugin can never escalate to writes through misuse.

**What this is not.** Not a chat interface — agent conversations stay in ACP panes and Telegram. Not an editing tool — modifying skills, memory, or lane-overrides still goes through the compilation pipeline so the audit log captures every change. Not a substitute for dashboards — the inspector serves drill-down forensics; dashboards serve filtered, decision-oriented views.

### Hermes → Todoist gap-card integration

The downstream gap loop ([workflows/downstream/write.md](../../how-to/workflows/downstream/write.md)) closes through the upstream pipeline today: Verifier's `cite-check` flags an unsupported claim, the gap becomes a card in the upstream queue, the human reads it during the weekly ritual. That works for gaps the human can act on at the desk. It does not work for gaps that need scheduling, deadlines, or external commitment — "ask co-author about IRB scope before next meeting" or "submit amendment to ethics board by 2026-06-15."

The pattern: a thin Hermes skill that mirrors substantive gap cards to Todoist via the Todoist MCP server already in the human's stack. The skill creates a Todoist task tagged `#memoria` and `#research-gap` with a backlink to the verification report, priority P3, into the human's existing project structure. One-way only — Todoist is the scheduling surface; Memoria's gap card remains the canonical artifact in the vault. Closing the Todoist task does not close the gap card; the gap closes when the human pursues the reading, files a new paper note, and the next Verifier pass traces the claim cleanly.

**When to implement.** After the gap loop has run for a corpus of at least one project and the human has noticed gaps slipping because they needed deadline-driven attention rather than weekly-ritual review. Below that, the weekly ritual covers what gaps need covering.

**Prerequisites.** The Todoist MCP server configured in the human profile (typically `mcp__claude_ai_Todoist_MCP__*`), a Todoist project structure stable enough that Memoria-generated tasks land somewhere sensible, and a labelling convention that distinguishes Memoria-originated tasks from human-created ones so the human can filter them out when reviewing their own commitments.

**What this is not.** Not bidirectional. Closing a Todoist task does not modify the vault. Not a replacement for the gap card. Not a general "Memoria notifies via Todoist" channel — only substantive citation gaps qualify; routine link suggestions and triage reminders stay inside Memoria's own surfaces.

### Static HTML admin reports

Most admin tasks are retrospective: weekly audit review, monthly drift analysis, quarterly trust-score retrospectives. Real-time inspection (the [Memoria Inspector plugin](#memoria-inspector-obsidian-plugin) above) is the wrong shape for these — what's needed is a snapshot rendered on a schedule that can be archived, diffed, and read on any device.

The pattern: a Hermes cron skill (`hermes run admin-report`) that renders static HTML pages from the audit log, board history, and trust-score time series. Outputs land in `00-meta/05-reports/<period>/` — version-controllable, archivable, openable in Obsidian directly or served via a simple HTTP server when remote viewing is needed. No runtime infrastructure, no auth surface, no failure mode beyond "stale report" (which the underlying system survives).

**When to implement.** This is the smallest of the three admin-surface entries and the most defensible to build first. A reasonable trigger: the first time the human wants to read the audit log on a phone over a train ride. Until then, dashboards + CLI cover the use case.

**Prerequisites.** A small templating layer (Jinja2 or similar) for the report shape, a cron entry on the Linter profile (whose dry-run posture matches the read-only nature of report generation), and a `00-meta/05-reports/` folder convention that doesn't conflict with the existing `00-meta/01-dashboards/`.

**What this is not.** Not interactive. Not a billing dashboard (cost reconciliation happens in the Hermes config). Not a substitute for the Inspector plugin (live drill-down) or the audit-log dashboard (filterable live view). Pure retrospective snapshots.

### Open-design integration

[Open-design](https://github.com/nexu-io/open-design) is the self-hosted, agent-native rendering tool whose architecture composes cleanly with Memoria's. It uses the SKILL.md convention, supports Hermes as one of its 16 agent CLIs, and operates on portable Markdown design systems. The integration is structured as the **external rendering agent** pattern — a peer of the existing [external coding agent](../../how-to/coder/external-agent-workspace.md#the-pattern-generalizes-external-rendering-agents) — so it absorbs into Memoria's architecture without new control-plane concepts.

**What's already in the design** (ready to use as soon as open-design is installed locally):

- **Render-agent pattern** ([profiles/why-coder-external-agent.md](../../how-to/coder/external-agent-workspace.md#the-pattern-generalizes-external-rendering-agents)). Memoria scaffolds the rendering task in a `deliverable` note; open-design reads the note + vault content + `design-system.md`; the human reviews the rendered artifact in `50-deliverables/`. Same review gate, same audit log, same lane policy as code work — only the artifact type differs.
- **Design-system source** ([obsidian-ui/design-system.md](../../reference/templates/design-system.md)). The authoritative visual-style file lives at `00-meta/04-reference/design-system.md` in open-design's portable DESIGN.md format (9 sections: color, typography, spacing, layout, components, motion, voice, brand, anti-patterns). One vault, one design system, multiple consumers (open-design renders, Pandoc exports, CSS snippets).

**Operationally valuable next steps** (worth doing once open-design is installed and the render-agent pattern has been exercised once or twice):

- **Slide-deck generation from drafts.** A new command — `Memoria: render slide deck from chapter` — that takes a section of a draft and produces a designed PPTX/HTML deck via open-design's 9 deck-mode skills. The deck lands at `50-deliverables/<project>/decks/`. High-leverage because conference/lab-meeting decks are a weekly time-sink that this kind of rendering directly attacks.
- **Selective open-design skill loading.** Open-design ships 132 SKILL.md bundles. A small subset (deck-from-markdown, infographic-template, landing-page, poster-template) are operationally relevant. Add them to the Writer lane's allowed skill list in [profiles/README.md](../../explanation/profiles/README.md) — same SKILL.md convention, same lane-permissions enforcement.

**Deferred — documented but not first-cut work**:

- **`render` card type.** Adding `render` as a first-class card type on the Coder or a new Render lane. Lifecycle: `triage` → `ready` → `running` (open-design generates) → `done` with `review_status: requested` (human inspects) → `approved` → `archived`. The render-agent pattern works without this (the human can invoke open-design directly via the existing Coder pattern); promoting to its own card type makes sense when render volume justifies queue dispatch.
- **Hermes ↔ open-design MCP composition.** Open-design exposes MCP tools (`search_files`, `get_file`, `get_artifact`). Memoria's Writer could call these tools as remote skills during drafting (e.g., embed a previously-rendered figure). Same composition pattern as the existing policy-MCP + rest-passthrough layering. Defer until there's a recurring "I want to reuse an existing artifact mid-draft" pain point.
- **Canvas → designed artifact pipeline.** A Memoria `canvas` note (Obsidian Canvas, spatial argument mapping) can be exported through open-design as a polished figure — methodology diagram for a paper, conceptual map for a grant proposal, mechanism schematic for a thesis. Useful but niche; revisit when the human has more than ~3 canvases per project and is recreating figures manually.

**Cons.** Adds a daemon (Express + SQLite + Next.js) and another agent stack to maintain. Cost overlay if image-generation models are used. The boundary against Pandoc must be enforced (Pandoc for body-text exports, open-design for visual artifacts — don't double-implement). AI-generated visuals must be gated for research outputs; default disabled in Memoria's profile.

**When to implement.** When the human hits a specific high-effort rendering task — a conference poster, a defense-talk deck, a project landing page — and recognizes they'd be hand-templating it without rendering help. Pre-emptively standing up open-design before that pain point is premature.

**Prerequisites.** Open-design installed locally (daemon running on a known port). The vault has a populated `00-meta/04-reference/design-system.md` (either from the [template](../../reference/templates/design-system.md) or imported from one of open-design's 150 built-in systems). A `50-deliverables/<project>/` folder exists for the target project. Workspace settings give open-design read access to the vault and write access to `50-deliverables/`.

**What this is not.** Not a replacement for Pandoc — they cover different artifact types. Not a one-click "make my thesis pretty" tool — open-design renders specific artifacts (decks, posters, landing pages) within an agreed design system, not arbitrary content. Not a content authoring tool — Memoria still owns content; open-design just renders it. Not a visual-AI generator by default — image generation is opt-in per project, with anti-patterns documented in the [design-system template](../../reference/templates/design-system.md).

## Multi-vault and cross-project

### Cross-vault read-only retrieval

Memoria assumes one vault per researcher. If you eventually run multiple vaults — say a personal vault and a project-specific or lab-shared vault — the right pattern is **MCP-mediated, read-only cross-vault retrieval**, not direct vault-to-vault links or sync.

The shape:

- Each vault stays isolated. No profile writes to a vault other than its own.
- Profiles can *read* an external vault through an MCP proxy that:
  - normalizes the external vault's notes into a uniform "research object" schema (`object_id`, `source_type`, `title`, `authors`, `created`, `canonical_url`);
  - exposes only a search/fetch surface — no write tools at all;
  - returns results that are clearly tagged as foreign so the worker can decide whether to create a local stub note in its own vault.
- The local stub captures the reference but never replaces the original. The vault that owns the original stays authoritative for it.

**When to implement.** When at least one of these is true:

- You're collaborating with another researcher who maintains their own Memoria vault.
- You have a project vault separate from your reading vault, and ingest needs to query both.
- A lab or team adopts Memoria and you need a shared corpus alongside personal corpora.

**Prerequisites.** A stable "research object" schema (overlapping but not identical to the paper-note frontmatter), an MCP proxy server, and explicit allowlisting in each vault for which other vaults may read it.

**What this is not.** Not federation — there is no sync, no conflict resolution, no global identity. Each vault is the source of truth for its own notes. Cross-vault is read-only retrieval, not shared state.

### Cross-project reading as personal AgentRxiv

Memoria assumes one vault per human. Within that vault, the human typically runs multiple concurrent projects (a thesis, a side-investigation, a literature scope for a future grant). Today the Librarian in project A does not read the synthesis produced by the Writer in project B unless the human explicitly links across projects — claim notes are searched globally, but project-scoped drafts are read project-locally. Cross-project synthesis happens by the human's hand, not by the agent's discovery.

The pattern, adapted from Schmidgall & Moor 2025 (AgentRxiv): treat the vault's `40-workbench/*/04-drafts/` collection as the human's personal "preprint pool." When a profile in project A runs a discovery or synthesis step, it also queries draft answer notes in projects B and C with a `cross_project: true` flag, and surfaces relevant prior thinking as inspiration context — clearly tagged as foreign so the worker creates a stub or wikilink rather than mistaking the foreign draft for in-project material. The original draft is never modified; the cross-project read is one-way and audit-logged.

**Cons.** Cross-project reads broaden the context any single agent step takes in — more tokens, slower, more places for noise to enter. Project-scoped privacy assumptions (a Project A draft might cite an embargoed source that should not surface in Project C) need to be encoded as policy, not as habit. Without consistent tagging, the same idea can spawn parallel drafts in two projects, which the cross-project loop then re-cross-reads.

**When to implement.** When the human has at least two concurrent projects active for ≥ 8 weeks each *and* notices "I already wrote about this" moments that the agent did not surface. Below that, the absence is not felt — the cost of building the cross-project read pattern outweighs the savings.

**Prerequisites.** The "research object" schema discussed in [cross-vault read-only retrieval](#cross-vault-read-only-retrieval) above — the same normalization that lets a foreign vault be queried also lets a foreign project be queried. An `embargo:` or `confidentiality:` field in project draft frontmatter so cross-project reads can be filtered. A clear UI cue in agent output that flags foreign-project context distinctly from in-project context (matching the foreign-vault pattern).

**What this is not.** Not a global re-merge — projects remain distinct top-level folders. Not bi-directional write — the cross-project loop is read-only, just like the foreign-vault pattern. Not a substitute for explicit cross-project wikilinks — the human still owns canonical cross-project synthesis; the loop only surfaces candidates for that linking.

## Multi-machine memory

### Scripted session-history sync

The [`memories/` junction](sync-and-coordination.md#syncing-profile-memory-across-machines-the-memories-junction) carries learned profile notes (`MEMORY.md` / `USER.md`) between machines but deliberately leaves the [session search database](../../explanation/architecture/memory-tiers.md#the-substrates) (`state.db`) behind — it is a live binary SQLite file that corrupts under raw file-sync and conflicts on merge. So "did we discuss X before?" recall does not follow you across machines. For most non-concurrent use this is fine: the learned conventions are what matter, and the research corpus lives in the vault regardless. This proposal closes the gap for the case where cross-machine chat-history recall is genuinely missed.

The pattern: a `sync-out` / `sync-in` script pair driven by **Windows Task Scheduler** (or `cron` / `launchd`). On leaving a machine, `sync-out` runs `hermes profile export <name>` for each profile — which snapshots that profile's sessions and memory via SQLite's WAL-safe `backup()` API and **excludes credentials** — writes the archive into the git-synced vault (or a dedicated Syncthing channel), and pushes. On arriving at the other machine, `sync-in` pulls and runs `hermes profile import <archive> --name <name>`. Because export is snapshot-based and import overwrites, the rule is strictly non-concurrent: snapshot on leave, restore on arrive.

**Cons.** `hermes profile import` overwrites the *whole* profile, including author-owned files (`SOUL.md`, `config.yaml`, `skills/`) that [`install.ps1` owns](../../explanation/architecture/on-disk-layout.md#how-the-installer-works) — so on a machine driven by `install.ps1`, import and install fight over the profile definition unless ordered deliberately (import first, then re-run `install.ps1` to reassert vault-source definitions). Binary `.tar.gz` snapshots bloat git history if committed to the vault repo — a dedicated Syncthing folder, or a `binary` mark in `.gitattributes`, mitigates. Snapshot granularity means a missed `sync-out` leaves the other machine importing stale history. Task Scheduler logoff / shutdown triggers are unreliable for long pushes, so a periodic timer is needed as a safety net.

**When to implement.** When, with the `memories/` junction already in place, the human repeatedly reaches for "what did the Librarian find about X three sessions ago?" on the *other* machine and the session search returns empty because the history lives on the first machine. Below that felt pain, the junction's `MEMORY.md` sync is sufficient and snapshotting sessions is overhead.

**Prerequisites.** The [`memories/` junction](sync-and-coordination.md#syncing-profile-memory-across-machines-the-memories-junction) in place as the baseline (this complements it, not replaces it). A transport for the archives — the git-synced vault or a Syncthing channel. Task Scheduler entries (`sync-in` at log-on; `sync-out` on workstation-lock plus a periodic timer). One verified round-trip confirming session search works on the second machine before relying on it.

**What this is not.** Not real-time — it is snapshot-on-boundary, so it only works under non-concurrent use. Not a replacement for the junction — the junction handles `MEMORY.md` / `USER.md`, this handles `state.db`; they compose. Not for concurrent machines — two live machines would clobber each other's profiles on import; that case wants the [Hermes memory server](#hermes-memory-server-shared-memory-provider) below.

### Hermes memory server (shared memory provider)

Both the [`memories/` junction](sync-and-coordination.md#syncing-profile-memory-across-machines-the-memories-junction) and [scripted session-history sync](#scripted-session-history-sync) are file-sync patterns: they move bytes between machines and depend on non-concurrent use to avoid conflicts. Hermes also supports a fundamentally different model — **external memory providers** — where the agent's learned memory lives in a backend both machines query in real time, making cross-machine memory machine-independent by construction rather than by sync.

The pattern: configure each machine's profile with the same [Hermes memory provider](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers) and the same memory space (e.g. Hindsight's `bank_id`, Supermemory's `container_tag`). The provider prefetches relevant memories before each turn and syncs conversation turns after each response — **additively** to the native `MEMORY.md` / `state.db`, which keep working unchanged. Cloud providers (Hindsight cloud, Mem0, Honcho, Supermemory, RetainDB) are reachable from any machine with no infrastructure of your own. Self-hostable providers (Hindsight in remote mode, OpenViking) give the same automation but require an always-reachable server — which in practice means [the always-on deployment option](deployment-options.md) (a VPS, or a home server on Tailscale). This is the only option that supports *concurrent* agents on different machines contributing to one shared memory space — e.g. a VPS discovery loop and an interactive desktop session both writing to the same bank.

**Cons.** Cost (a cloud subscription) or always-on infrastructure (to self-host) — neither fits the zero-infra, non-concurrent baseline. An external service or extra server now holds the agent's learned memory: a new dependency, and for cloud providers an off-vault copy of derived research context. Over-broad memory spaces produce noisy recall — keep the bank workflow-specific (`memoria-research`), not a catch-all. Adds a moving part whose value only materializes when real-time or concurrent memory sharing is actually needed.

**When to implement.** When the human graduates to [the always-on deployment option](deployment-options.md) *and* wants the discovery loop's discoveries and the desktop's interactive sessions to share one memory space in real time — the concurrent case the file-sync patterns explicitly do not cover. For a single researcher using one machine at a time, the [`memories/` junction](sync-and-coordination.md#syncing-profile-memory-across-machines-the-memories-junction) plus optional [session-history sync](#scripted-session-history-sync) is sufficient and a memory server is overkill.

**Prerequisites.** A chosen provider with an account (cloud) or a running instance (self-host, which presupposes the always-on deployment). A shared, workflow-specific memory-space identifier configured identically across machines. The provider's API key in each machine's per-profile `.env` (per-machine secret, [never synced](deployment-options.md)). A cost or resource budget, monitored.

**What this is not.** Not a sync layer for the vault — providers hold the agent's small *learned* memory, never the research corpus, which stays in the git-synced vault ([memory tiers](../../explanation/architecture/memory-tiers.md)). Not a replacement for native memory — providers are additive; `MEMORY.md` / `state.db` continue to function. Not needed for non-concurrent use — its distinguishing capability is real-time, concurrent sharing, which the file-sync patterns above intentionally trade away for zero infrastructure.

## Backlog — sketched ideas

Ideas with enough shape to remember but not enough design to ship as full proposals. Each is a candidate to graduate into the substantive list above when usage pressure reveals the design constraints. Listed compactly here; expand in place if any of them earns a full design pass.

### Event-driven and scheduled operations

- Nightly enrichment refresh for paper notes more than 30 days old.
- Weekly orphan-detection scan with a dashboard surface.
- Monthly merge-candidate report.
- On-add hook: when a new citekey appears in `.memoria/library.bib`, auto-trigger ingest.

### Autonomous synthesis (cautious)

- Hermes drafts answer notes from research questions on a schedule.
- All drafts land in `10-inbox/` as `answer-note`, awaiting review.
- Never auto-promoted.

### Gap-seeking planner

- A "gap" agent identifies under-cited claims, contradictory claims, or topics with sparse coverage.
- Proposes discovery queries to fill gaps.
- Surfaces results to the human as a research-planning aid.

### Self-evaluation and benchmarks

- Periodic retrieval-quality checks against held-out questions.
- Note-completeness audits.
- Link-density and orphan-rate trends over time.

### More agent roles and internal reviewers

- A dedicated *claim checker* that verifies every claim note traces to at least one source.
- A *consistency checker* that flags contradictions between claim notes. (Graduated into a full proposal — see [§"NLI-based contradiction detection"](#nli-based-contradiction-detection).)
- An *evidence-strength assessor* that ranks claim notes by how well-supported they are.

These additions all preserve the central rule: agents propose, humans decide.
