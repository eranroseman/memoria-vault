---
title: Callouts
parent: Obsidian
nav_order: 3
---


# Callouts

Not every agent output belongs on a dashboard. Some context is only useful while looking at a specific note — the comparative read on a paper matters when you open it to read the source, not in a daily roll-up. Dashboards surface *decisions across notes*; callouts surface *context inside one note*.

Memoria defines three callout types via the Callout Manager plugin and renders them consistently across the vault. `[!brief]` is produced during ingest; `[!suggestions]` is produced by the link-claim palette action; `[!verification]` is produced by the verify-draft palette action.

For the exact shipped-vs-deferred contract, see the reference: [Obsidian callouts](../../reference/obsidian-callouts.md). For the rationale, see [Why callouts exist](../../design/why-callouts.md).

## The three callouts and what they represent

**`[!brief]`** is the comparative read the Librarian composes during ingest, before you've read the paper. It tells you: which of your existing notes this paper overlaps with, where it might contradict what you already know, and what new constructs it introduces. The brief primes your attention so you read actively rather than passively.

**`[!suggestions]`** is the Librarian's bounded deterministic set of candidate links, with Approve and Reject affordances. It is designed to start collapsed to prevent rubber-stamping: if you see a wall of suggestions, you tend to approve all of them without reading. The future fleet-health signal should track accept/reject ratios over time, because a too-high acceptance rate means rubber-stamping and a too-low one means the candidate scoring needs tuning.

**`[!verification]`** is the Peer-reviewer's claim-trace scaffold over a draft. It should show the result of tracing every substantive claim in the draft back to a claim note — a check for traced claims, a flag for untraced ones, and a link to the full per-claim report.

The placement, cap values, collapse states, and drift-signal cutoffs are in the [reference](../../reference/obsidian-callouts.md).

## Ownership and updates

Each produced callout is written by the producing agent and then owned by the human. Producers do not overwrite edits on subsequent runs; they append a new `(updated YYYY-MM-DD)` callout below any existing one.

The collapsed/expanded default follows the volume of the callout type. `[!brief]` starts expanded because it provides one-shot context that is always relevant when the note is open. `[!suggestions]` starts collapsed because it contains a list of candidate links; `[!verification]` starts expanded because its trace is a finding surface.

Callout writes pass through the policy MCP like any other vault write — logged, hashed, and reversible from the audit log. This means the callout mechanism cannot be used to bypass the review gate, and the audit trail captures when and by whom each callout was written.

---

## Related

- The hybrid pattern behind callouts: [Why Memoria uses deterministic methods alongside LLMs](../../design/why-computational-methods.md)
- Why callouts exist: [Why callouts exist](../../design/why-callouts.md)
- Callout field reference: [Obsidian callouts](../../reference/obsidian-callouts.md)
