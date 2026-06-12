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
| `[!brief]` | Top of every source note in `notes/source/` | Librarian (composed during ingest by `obsidian-paper-note`) | Comparative read — what this source overlaps with, what it may contradict, what new constructs it introduces |
| `[!suggestions]` | End of any note Librarian has run link suggestions against | Librarian (after `enrich` or weekly link pass) | Bounded candidate links (5 forward + 5 backward, hard cap) with Approve / Reject affordances |
| `[!verification]` | Top of any draft in `projects/<project>/composition/` | Peer-reviewer (auto-fired on draft `git commit`) | Per-claim trace back to claim notes; failed traces flagged with a link to the verification report |

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

## Behavior

| Property | Value |
| --- | --- |
| Default collapse state | `[!suggestions]` collapsed; `[!brief]` and `[!verification]` expanded |
| Re-run on edited callout | Appends a new `(updated YYYY-MM-DD)` block below the existing one; never rewrites it |
| Write path | Policy-MCP gated — logged with SHA-256 hashes, reversible from the audit log |

For why each behaves this way, see [Callouts](../explanation/obsidian/callouts.md).

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

| Accept rate | Indicates |
| --- | --- |
| > ~90% | Rubber-stamping — candidate scoring is too permissive |
| < ~20% | Candidates not relevant enough — scoring needs tuning |

How to read and respond to these signals is covered in [Callouts](../explanation/obsidian/callouts.md).

---

## Related

- Callout Manager plugin: [Obsidian plugins](obsidian-plugins.md)
- Computational toolbox (scoring functions): [Retrieval and analysis methods](computational-toolbox.md)
- Fleet-health dashboard: [explanation/dashboards/](../explanation/dashboards)
- The callout explanation page: [Callouts](../explanation/obsidian/callouts.md)
