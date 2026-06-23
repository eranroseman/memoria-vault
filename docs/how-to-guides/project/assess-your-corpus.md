---
title: Assess your corpus
parent: Project
nav_order: 2
---

# Assess your corpus

Delegate a **`map`** task to get a corpus map — a structured read of what claims and sources you hold, where coverage is dense, and where the gaps are. The map is the decision point before drafting: write now, or read more first.

## Prerequisites

- At least ~5 claim notes in `notes/claims/` (fewer than that and the map is mostly gaps)
- Obsidian command palette available; the Agent Client pane is optional if you want help shaping the scope

## Steps

**1. Name the question.**

The map lane scopes against what you ask, so bring the deliverable into the question: the topic, the intended output, any framing constraints ("must cover 2020–2025", "needs to foreground equity").

**2. Delegate the map task.**

Use the direct command when the scope is clear: `Cmd/Ctrl-P` → **Memoria: map corpus**. Or, if you want help framing the pass, ask in the Agent Client pane:

> "Map my corpus on `<topic>` — what do I have good coverage on, and where is it thin? I'm aiming at `<deliverable>`."

Both routes create a **`map`** task for the Librarian's map lane, which builds the typed graph and topic clusters over the cluster MCP ([The Librarian](../../explanation/profiles/librarian.md)). The palette command prompts for an optional scope; the Co-PI route delegates the same card after helping shape the request (see [Command palette](../../reference/obsidian-command-palette.md)).

**3. Read the results from the Inbox.**

The coverage read comes back through the Inbox, with **`gap` cards** for the thin areas — each carrying the honesty body, never a verdict. Read by pattern:

- **Dense + recent cluster** — draft from it; the evidence is there and current.
- **Dense + stale cluster** — well-read a while ago; check for newer work before leaning on it.
- **Thin cluster** — mentioned but under-evidenced; read more first.
- **Gap the deliverable requires** — fill it or explicitly scope it out. A gap you neither fill nor acknowledge becomes an unsupported section later.

**4. Decide: write now or read more?**

- **Dense enough** (a hub with several mutually linked claims is the tell): proceed to sketching and drafting.
- **Gaps that matter:** use **Memoria: delegate task** → `catalog` with each accepted gap as context, or ask the Co-PI to shape the discovery request ([Find new sources](../library/find-new-sources.md)). Archive the gaps you don't buy.

**5. Record rejected directions.**

When a map or gap report shows a direction you considered and intentionally rejected, open that report and run `Memoria: record exploration trace` ([Obsidian command palette](../../reference/obsidian-command-palette.md)). Capture the rejected direction, the reason, the evidence you checked, and when it would be worth revisiting.

The trace lands beside the map under `notes/fleeting/maps/`. It is project-local memory for future you, not canonical knowledge: do not turn it into a claim or hub unless you later find positive evidence worth distilling.

Two standing dashboards answer the same questions continuously: `system/dashboards/open-questions.md` (unconnected claims — the synthesis backlog) and `contradictions.md` (open tensions).

## Verify

- The map results and gap cards arrived in the Inbox, and every gap card is resolved — turned into a discovery task or archived
- You've made an explicit "write now / read more" decision — not just noted the map and moved on
- Rejected directions that shaped the decision are captured as exploration traces next to the map/gap report

## Related

- Filling the gaps: [Find new sources](../library/find-new-sources.md)
- Next step when dense: [Use canvas for argument mapping](use-canvas-for-argument-mapping.md)
- The guided walk: [Tutorial 04: Draft a section from your claims](../../tutorials/04-draft-a-section-from-your-claims.md)
- The lane behind the map: [The Librarian](../../explanation/profiles/librarian.md)
