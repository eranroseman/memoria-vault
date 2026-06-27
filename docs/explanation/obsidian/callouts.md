---
title: Callouts
parent: Obsidian
nav_order: 3
---


# Callouts

Not every agent output belongs on a dashboard. Some context is only useful while looking at a specific note — the comparative read on a paper matters when you open it to read the source, not in a daily roll-up. Dashboards surface *decisions across notes*; callouts surface *context inside one note*.

Memoria defines three callout types via the Callout Manager plugin and renders them consistently across the vault. `[!brief]` is produced during ingest; `[!suggestions]` is produced by the link-claim palette action; `[!verification]` is produced by the verify-draft palette action.

For the exact shipped-vs-deferred contract, see the reference: [Obsidian callouts](../../reference/obsidian-callouts.md). This page explains *why* the three callouts exist and why they're shaped the way they are.

## The three callouts and what they represent

**`[!brief]`** is the comparative read the Librarian composes during ingest, before you've read the paper. It tells you: which of your existing notes this paper overlaps with, where it might contradict what you already know, and what new constructs it introduces. The brief primes your attention so you read actively rather than passively.

**`[!suggestions]`** is the Librarian's bounded deterministic set of candidate links, with Approve and Reject affordances. It is designed to start collapsed to prevent rubber-stamping: if you see a wall of suggestions, you tend to approve all of them without reading. The future fleet-health signal should track accept/reject ratios over time, because a too-high acceptance rate means rubber-stamping and a too-low one means the candidate scoring needs tuning.

**`[!verification]`** is the Peer-reviewer's claim-trace scaffold over a draft. It should show the result of tracing every substantive claim in the draft back to a claim note — a check for traced claims, a flag for untraced ones, and a link to the full per-claim report.

The placement, cap values, collapse states, and drift-signal cutoffs are in the [reference](../../reference/obsidian-callouts.md).

## Why callouts rather than dashboards

A dashboard tells you something about the vault as a whole: what's overdue, what's unlinked, what needs review. A callout tells you something about the note you're currently reading. Separating them means you don't have to context-switch to get note-level context, and the dashboard isn't cluttered with per-note detail.

The design rule: if the information is only useful in the context of a specific note, it's a callout. If it requires seeing across multiple notes, it's a dashboard.

## Why content is produced deterministically, then composed

All three callouts follow the same pattern: a deterministic step selects and ranks candidates; an LLM composes the prose over them. This is the [hybrid method pattern](../../design/why-computational-methods.md) applied to a note-level surface, and it is a deliberate choice rather than a convenience.

The reason is auditability under cost control. The *selection* — which sources are comparable, which links are candidates, which claims trace — is the part that must be reproducible and reviewable, so it stays deterministic: the same vault state produces the same candidates, ranked the same way, every run. The *prose* — the comparative narrative, the one-line link explanations — is the part with no deterministic form, so it's where LLM judgment is spent, and only there. Letting the LLM also do the selection would make the callout non-reproducible and the cost unbounded, for no gain the human can verify.

This is why the audit trail for each callout is the deterministic step's output — which candidates ranked where, by what score — not the LLM's wording. The prose is the visible presentation; the scoring is what the dashboards and the fleet-health accept/reject ratios actually measure. (The exact ranking weights and similarity thresholds are in the [reference](../../reference/obsidian-callouts.md#how-content-is-produced-hybrid-pattern).)

## Why callouts are producer-owned and human-curated

Three properties are shared across all three callout types and reflect common design commitments.

Each produced callout is written by the producing agent and then owned by the human. Producers do not overwrite edits on subsequent runs; they append a new `(updated YYYY-MM-DD)` callout below any existing one. This preserves the human's edits while surfacing new agent output, rather than forcing a choice between freshness and persistence.

The collapsed/expanded default follows the volume of the callout type. `[!brief]` starts expanded because it provides one-shot context that is always relevant when the note is open. `[!suggestions]` starts collapsed because it contains a list of candidate links; `[!verification]` starts expanded because its trace is a finding surface.

Callout writes pass through the policy MCP like any other vault write — logged, hashed, and reversible from the audit log. This means the callout mechanism cannot be used to bypass the review gate, and the audit trail captures when and by whom each callout was written.

---

## Related

- The hybrid pattern behind callouts: [Why Memoria uses deterministic methods alongside LLMs](../../design/why-computational-methods.md)
- Callout field reference: [Obsidian callouts](../../reference/obsidian-callouts.md)
