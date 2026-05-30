---
topic: obsidian-ui
---

# Callouts

Not every agent output belongs in a dashboard. Some context is only useful while looking at a specific note — the comparative read on a paper note matters when the human opens that note to read the source, not in a daily roll-up. Dashboards surface *decisions across notes*; inline callouts surface *context inside one note*.

Memoria uses three callout types, defined via [Callout Manager](../../reference/plugins/callout-manager.md) and rendered consistently across the vault:

| Callout | Where | Producer | Purpose |
| --- | --- | --- | --- |
| `[!brief]` | Top of every paper note in `20-sources/01-papers/` | Mapper (via `comparative-brief`, triggered when a new source enters the queue) | Comparative read — what this source overlaps with, what it may contradict, what new constructs it introduces. Primes attention before reading the PDF. |
| `[!suggestions]` | End of any note Librarian has run link suggestions against | Librarian (after `enrich` or weekly link pass) | Bounded (5 forward + 5 backward, hard cap) candidate links with Approve/Reject affordances. Collapsed by default to avoid rubber-stamping volume. The [fleet-health dashboard](../dashboards/fleet-health.md) tracks accept/reject ratios over time as a drift signal — a sustained accept rate above ~90% means the human is rubber-stamping; below ~20% means the candidate scoring needs tuning (see [the deterministic/LLM split below](#how-the-callout-content-is-produced-deterministic-narrowing--llm-enrichment)). |
| `[!verification]` | Top of any draft in `40-workbench/*/04-drafts/` | Verifier (auto-fired on draft commit) | Per-claim trace back to claim notes, with failed traces and a link to the per-claim verification report. |

Example shape for `[!brief]`:

```markdown
> [!brief] Mapper's comparative read
> Overlaps with: [[mamykina2010sense]], [[veinot2018good]]
> May contradict: [[chen2021pipeline]]
> New construct: "prosodic mimicry safety"
> 5 candidate links queued for review.
```

## Design rules for callouts

- **Producer-owned, human-curated.** The agent writes the callout once; the human accepts/rejects or rewrites. The callout is not edited by the agent on subsequent runs unless explicitly re-requested.
- **Collapsed by default for suggestions, expanded for briefs and verifications.** Volume-prone callouts collapse; one-shot context callouts expand.
- **Never overwrite human content in the same callout.** If a human has edited a `[!brief]`, the next ingest run appends a new `[!brief] (updated YYYY-MM-DD)` callout below it rather than rewriting.

## How the callout content is produced (deterministic narrowing + LLM enrichment)

All three callouts use the **hybrid pattern** described in [architecture/why-computational-methods.md](../architecture/why-computational-methods.md#the-hybrid-pattern): a deterministic step narrows the candidate set, an LLM step composes the prose. This keeps cost bounded, makes the candidate selection auditable, and preserves the qualitative judgment LLMs add to narrative composition.

| Callout | Deterministic step (candidate selection) | LLM step (composition) |
| --- | --- | --- |
| `[!brief]` | Top-5 candidate sources for comparison, ranked by (shared-citation overlap + embedding similarity + topic-tag intersection). | Composes the comparative narrative — "overlaps with," "may contradict," "new construct" — over the 5 candidates. |
| `[!suggestions]` | Top-10 link candidates ranked by weighted scoring: embedding similarity (0.4) + shared citations (0.3) + topic-tag overlap (0.2) + recency boost (0.1). Then truncated to 5 forward + 5 backward per the cap. | Optional one-line explanation per candidate ("suggested because of shared citation to [[veinot2018good]]"). |
| `[!verification]` | Per-claim trace via regex citation extraction + embedding similarity against claim notes. Auto-clean above similarity threshold (~0.75), auto-fail below (~0.4). | LLM judges only the middle ambiguous band (similarity 0.4–0.75) — the claim-source semantic match where deterministic signals are equivocal. |

The audit trail for each callout is the **deterministic step's output** (which candidates ranked where, by what score, against what citations). The LLM's prose is the visible presentation but the candidate selection is what dashboards and the [fleet-health accept/reject ratios](../dashboards/fleet-health.md) measure. This is what makes the rubber-stamping signal (accept rate > 90%) meaningful — if the scoring function is over-suggesting, tune the weights; if under-suggesting, lower the threshold. With pure LLM ranking those ratios would be noise.

Callouts are policy-MCP writes like any other — when Mapper attaches a `[!brief]` to a paper note, the write is gated by the lane policy, logged with SHA-256 hashes, and reversible from the audit log.
