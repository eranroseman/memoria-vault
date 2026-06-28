---
title: Callouts
parent: Obsidian
grand_parent: Explanation
nav_order: 3
---


# Callouts

Not every agent output belongs on a dashboard. Some context is only useful while looking at a specific note — the comparative read on a paper matters when you open it to read the source, not in a daily roll-up. Dashboards surface *decisions across notes*; callouts surface *context inside one note*.

Memoria defines three callout types via the Callout Manager plugin and renders them consistently across the vault. They follow the hybrid pattern: deterministic selection first, LLM composition second.

For the exact shipped-vs-deferred contract, see the reference: [Obsidian callouts](../../reference/obsidian-callouts.md).

## The three callouts and what they represent

| Callout | Producer | Purpose | Default |
| --- | --- | --- | --- |
| `[!brief]` | Ingest / Librarian | Comparative read before you read the source: overlaps, possible contradictions, new constructs. | Expanded |
| `[!suggestions]` | Link-claim action / Librarian | Bounded candidate links with approve/reject affordances. | Collapsed |
| `[!verification]` | Verify-draft action / Peer-reviewer | Claim-trace scaffold over a draft, with gaps surfaced separately. | Expanded |

The placement, cap values, collapse states, and drift-signal cutoffs are in the [reference](../../reference/obsidian-callouts.md).

## Ownership and updates

- The producing agent writes the callout; the human owns it after that.
- Producers append a dated update rather than overwriting human edits.
- Writes pass through the policy MCP, so callouts cannot bypass the review gate.

---

## Related

- The hybrid pattern behind callouts: [Why Memoria uses deterministic methods alongside LLMs](../../design/why-computational-methods.md)
- Callout field reference: [Obsidian callouts](../../reference/obsidian-callouts.md)
