---
title: Obsidian callouts
parent: Reference
---

# Obsidian callouts

Three inline callout types written by agent profiles into vault notes. Defined via the [Callout Manager](obsidian-plugins.md) plugin.

---

## The three callout types

| Callout | Location | Producer | Purpose |
| --- | --- | --- | --- |
| `[!brief]` | Top of every paper note in `20-sources/01-papers/` | Librarian (composed during ingest by `obsidian-paper-note`) | Comparative read — what this source overlaps with, what it may contradict, what new constructs it introduces |
| `[!suggestions]` | End of any note Librarian has run link suggestions against | Librarian (after `enrich` or weekly link pass) | Bounded candidate links (5 forward + 5 backward, hard cap) with Approve / Reject affordances |
| `[!verification]` | Top of any draft in `40-workbench/*/04-drafts/` | Verifier (auto-fired on draft `git commit`) | Per-claim trace back to claim notes; failed traces flagged with a link to the verification report |

---

## Example shape

```markdown
> [!brief] Comparative read
> Overlaps with: [[mamykina2010sense]], [[veinot2018good]]
> May contradict: [[chen2021pipeline]]
> New construct: "prosodic mimicry safety"
> 5 candidate links queued for review.
```

---

## Design rules

- **`[!suggestions]` collapsed by default; `[!brief]` and `[!verification]` expanded.** Volume-prone callouts collapse; one-shot context callouts expand.
- **Never overwrite human edits.** If a human has edited a `[!brief]`, the next ingest run appends a new `[!brief] (updated YYYY-MM-DD)` block below it — it does not rewrite the existing one.
- **All callout writes are policy-MCP gated.** When the Librarian attaches a `[!brief]` during ingest, the write is logged with SHA-256 hashes and is reversible from the audit log.

---

## How content is produced (hybrid pattern)

All three callouts use a deterministic candidate-selection step followed by an LLM composition step.

| Callout | Deterministic step | LLM step |
| --- | --- | --- |
| `[!brief]` | Top-5 candidates ranked by: shared-citation overlap + embedding similarity + topic-tag intersection | Composes the "overlaps with / may contradict / new construct" narrative over the 5 candidates |
| `[!suggestions]` | Top-10 candidates ranked by: embedding similarity (0.4) + shared citations (0.3) + topic-tag overlap (0.2) + recency boost (0.1); truncated to 5 forward + 5 backward | Optional one-line explanation per candidate |
| `[!verification]` | Per-claim trace via regex citation extraction + embedding similarity; auto-clean above ~0.75, auto-fail below ~0.4 | Judges only the middle ambiguous band (0.4–0.75 similarity) |

The audit trail for each callout is the deterministic step's output (which candidates ranked where, by what score). The LLM's prose is the visible presentation but the scoring is what the fleet-health accept/reject ratios measure.

---

## Drift signals

The fleet-health dashboard tracks `[!suggestions]` accept/reject ratios over time:

- **Accept rate > ~90%** → the human is rubber-stamping; candidate scoring is too permissive — tune down the similarity threshold or the weighting.
- **Accept rate < ~20%** → the candidate scoring needs tuning; candidates are not relevant enough.

---

## Related

- Callout Manager plugin: [Obsidian plugins](obsidian-plugins.md)
- Computational toolbox (scoring functions): [Retrieval and analysis methods](computational-toolbox.md)
- Fleet-health dashboard: [explanation/dashboards/](../explanation/dashboards/)
- The callout explanation page: [Callouts](../explanation/obsidian/callouts.md)
