---
topic: architecture
---

# Why Memoria refuses to autonomize synthesis

Karpathy's Autoresearch pattern — an agent that runs autonomously overnight, modifies code, tests against a fixed evaluator, and keeps or reverts — works because three things are simultaneously true for ML experiments:

1. **The metric is monotonic.** Validation loss either improves or it doesn't.
2. **Changes are reversible.** Git reverts the diff; the next experiment starts clean.
3. **Experiments are independent.** Experiment N+1 doesn't depend on the conclusions of experiment N.

Knowledge work satisfies none of these. Memoria adopts the parts of the pattern that *do* fit — see [roadmap/future-directions.md](../../project/roadmap/future-directions.md) for the overnight discovery loop, [workflows/README.md](../../how-to/workflows/README.md) for the research-directions file, [profiles/verifier.md](../profiles/verifier.md) for the point-of-action similarity check — and explicitly refuses the parts that don't.

## Three boundaries

**Memoria is cognition-bound, not compute-bound.** Fixing a wall-clock time budget on ingest or synthesis would be cosmetic — it wouldn't change throughput or quality. The right analog is a fixed *batch size* (e.g., 10 candidates per nightly find run), not a fixed duration. We bound *how much new work the human has to triage tomorrow*, not *how long the agent ran*.

**Autonomous keep / revert is not safe for synthesis.** The agent cannot reliably judge whether a synthesis is novel, correct, or worth keeping; the value of a source is often only knowable in retrospect, when later sources illuminate or contradict it. The discovery loop generates *candidates and proposals*; the morning triage session is the human keep/revert step. The loop prepares the work; it doesn't complete it.

**No single scalar metric.** Every autoresearch system optimizes one number. Academic research resists this. Proxy metrics exist (Scite supporting count, citation count, relevance-to-projects score), and they may inform triage *prioritization*, but they never drive automatic keep/revert decisions. A high-citation paper rises in the discovery queue; the human still decides whether it goes into the vault.

This is an empirical claim about every contemporary autonomous-research system the survey covers, not a normative preference. Each system's keep/revert loop is anchored on a single scalar:

| System | Scalar metric |
| --- | --- |
| AI Scientist v1/v2 (Lu et al. 2024) | Simulated-reviewer score on the generated paper |
| AI-Researcher (Tang et al. 2025) | Scientist-Bench task success rate |
| AiScientist long-horizon engineering (Chen et al. 2026) | MLE-Bench validation AUC; PaperBench score |
| CORAL (Qu et al. 2026) | Domain benchmark score (per task) |
| SciMON (Wang et al. 2024) | Novelty score from iterative comparison to prior literature |
| AI co-scientist (Gottweis et al. 2025) | Tournament Elo from simulated scientific debate |
| Karpathy Autoresearch | Validation loss on the held-out ML eval |

Each metric is plausible *for its target task*. None is plausible for "is this synthesis a faithful, well-cited, non-redundant addition to a research vault." Adopting any of them as Memoria's keep/revert signal would be a category error — optimizing the wrong objective shape. The review gate exists because the right objective is not a scalar; it is human judgment exercised against the vault's existing structure.

## Scope: these boundaries apply to synthesis

The three boundaries above are about *synthesis* — producing claim notes, MOCs, and canonical reference content from the corpus. They are not blanket prohibitions on every agent loop that uses a metric. The Coder lane is the explicit exception:

| Precondition | Synthesis | Coder lane (code against tests) |
| --- | --- | --- |
| Monotonic metric | Fails — synthesis quality is multidimensional | Holds — tests pass / runtime improves / coverage rises |
| Reversible changes | Fails — a wrong claim ripples to downstream cites | Holds — `git reset` |
| Independent experiments | Fails — later sources reinterpret earlier ones | Holds — each branch is independent |

The Coder lane works on code, fixtures, and tooling whose success can be defined by a scalar that exists *before* the loop runs — a test suite, a runtime benchmark, a coverage threshold. When that scalar is present, the autonomous keep / revert pattern that Chen et al. 2026 (AiScientist long-horizon engineering) and Karpathy Autoresearch describe is admissible. It is captured concretely as [roadmap/future-directions.md §"Coder lane experiment loop"](../../project/roadmap/future-directions.md#coder-lane-experiment-loop).

The exemption is narrow by design. It applies only when **all** of the following hold:

- The work is in the Coder lane — not Librarian, Writer, Verifier, Mapper, Socratic, or Linter.
- The success criterion is a verifiable scalar that exists *before* the loop starts. A fixture, a test, a benchmark. Not a metric the agent proposes mid-run; not an LLM-judge score.
- Outputs land in `40-workbench/<project>/06-code/experiments/<run-id>/` and require human review to promote into the project's working code. **The keep/revert decision is internal to the loop; the promotion decision still routes through the human review state.**

The structural enforcement is unchanged. The policy MCP's review-gated-zone deny rule still blocks writes to `30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, and `50-deliverables/`. The Coder lane's autonomy operates inside zones it has always been permitted to write to; the synthesis gate remains structurally untouched. The exemption is a clarification of where the boundary already was, not a relaxation of where it is.

## Why not confidence-routed gating

AutoResearchClaw (Liu et al. 2026) offers a tempting refinement called **SmartPause**: route a decision to the human *only* when the agent's self-assessed confidence is low, and let high-confidence outputs through automatically. Its human-in-the-loop ablation reports that this targeted gating beat both full autonomy and dense step-by-step oversight. Memoria **declines** to make its blocking review confidence-routed, for two reasons.

First, it would convert a *structural* gate into a *probabilistic* one. The whole point of the blocking review (see [vision.md §"What Memoria is"](../vision.md#what-memoria-is)) is that promotion cannot happen without the human, regardless of how the agent feels about its output. Confidence-routing makes the gate fire on a signal the agent produces — and a **confidently-wrong** agent is precisely the failure mode that matters here: hallucinated citations and fabricated numbers are emitted with high fluency and high confidence, not with visible hesitation. Routing the gate on self-assessed confidence would wave through exactly the outputs the gate exists to catch. This is the same gameable-metric hazard as the [co-trained reviewer](why-pattern-provenance.md#ignore) — the gate signal becomes the optimization target.

Second, the ablation's result was measured on a throughput-optimizing autonomous system, where the cost of a wrong "high-confidence" output is a wasted run that the next run replaces. Memoria's cost model is inverted: the vault is **durable**, so a wrongly-promoted claim persists and compounds into everything that later cites it. The asymmetry means the burden-reduction that confidence-routing buys is not worth the structural guarantee it spends.

The real insight in the ablation — that gating everything and gating nothing are both worse than gating *well* — is one Memoria keeps, but it spends it on the other side of the gate: **make each review cheaper rather than skip reviews.** Strengthening the pre-gate Verifier (typed claim checks, evidence-chain verification — see [roadmap/future-directions.md §"Chain-of-Evidence claim taxonomy"](../../project/roadmap/future-directions.md#chain-of-evidence-claim-taxonomy-for-the-verifier)) lets the human review pre-verified material faster without removing the human from the loop. The [agent-consensus pre-filter](../../project/roadmap/future-directions.md#agent-consensus-pre-filter) is the one adjacent move Memoria *does* prototype — but note it routes review, it never bypasses it, and it carries its own correlated-error caution.

## What this implies

- The review gate (see [kanban-board/README.md](../kanban-board/README.md)) is structural, not optional. Every autonomy upgrade has to route through it.
- The agent's job is to *surface*, *propose*, and *prepare* — never to canonize.
- Scheduled / overnight operations write to `10-inbox/` only. Promotion is always synchronous with human attention.
- Cost discipline ("$1–3/day API call budget for the nightly loop") matters because there's no scalar payoff to optimize against — discipline has to come from the budget, not from the metric.

The refusal is enforced by infrastructure, not by prompt discipline. The policy MCP's review-gated-zone rule degrades every write to `30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`, and `50-deliverables/` to `dry_run` regardless of which profile requests it; the [`socratic-processing`](../profiles/README.md#skills-with-restrictive-policy) skill goes further by denying *any* vault write during the processing-step conversation. Both gates exist at the [policy MCP layer](../../reference/architecture/policy-mcp.md) — an agent that "decides" to canonize cannot, because the file-system call returns `deny` before any content reaches disk.

## Related

- Overnight discovery loop (the autonomy that *is* adopted): [roadmap/future-directions.md](../../project/roadmap/future-directions.md)
- Review gate mechanics: [kanban-board/README.md](../kanban-board/README.md)
- Policy MCP review-gated-zone rule: [architecture/policy-mcp.md](../../reference/architecture/policy-mcp.md)
- Pattern provenance (the full borrow/adapt/ignore table): [architecture/why-pattern-provenance.md](why-pattern-provenance.md)
