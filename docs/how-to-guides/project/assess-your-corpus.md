---
title: Assess your corpus
parent: Project
nav_order: 2
---

# Assess your corpus

Delegate a **`map`** task to get a corpus map — a structured read of what claims and sources you hold, where coverage is dense, and where the gaps are. The map is the decision point before drafting: write now, or read more first.

## Prerequisites

- At least ~5 claim notes in `notes/claims/` (fewer than that and the map is mostly gaps)
- The Agent Client pane connected

## Steps

**1. Name the question.**

The map lane scopes against what you ask, so bring the deliverable into the question: the topic, the intended output, any framing constraints ("must cover 2020–2025", "needs to foreground equity").

**2. Delegate the map task.**

In the Co-PI pane:

> "Map my corpus on `<topic>` — what do I have good coverage on, and where is it thin? I'm aiming at `<deliverable>`."

The Co-PI delegates a **`map`** task to the Librarian's map lane, which builds the typed graph and topic clusters over the cluster MCP ([The Librarian](../../explanation/profiles/librarian.md)). (Palette twin: **Memoria: map corpus** — prompts for an optional scope; see [Command palette](../../reference/obsidian-command-palette.md).)

**3. Read the results from the Inbox.**

The coverage read comes back through the Inbox, with **`gap` cards** for the thin areas — each carrying the honesty body, never a verdict. Read by pattern:

- **Dense + recent cluster** — draft from it; the evidence is there and current.
- **Dense + stale cluster** — well-read a while ago; check for newer work before leaning on it.
- **Thin cluster** — mentioned but under-evidenced; read more first.
- **Gap the deliverable requires** — fill it or explicitly scope it out. A gap you neither fill nor acknowledge becomes an unsupported section later.

**4. Decide: write now or read more?**

- **Dense enough** (a hub with several mutually linked claims is the tell): proceed to sketching and drafting.
- **Gaps that matter:** hand each gap card you agree with straight back — "that gap is real, find sources to fill it" ([Find new sources](../library/find-new-sources.md)). Archive the gaps you don't buy.

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
- The guided walk: [Tutorial 05: Synthesize toward a writing project](../../tutorials/05-synthesize-toward-a-writing-project.md)
- The lane behind the map: [The Librarian](../../explanation/profiles/librarian.md)
