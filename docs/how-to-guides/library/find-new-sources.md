---
title: Find new sources
parent: Library
nav_order: 1
---

# Find new sources

Run a discovery pass — papers that build on what you hold, papers you're missing, or papers matching a research question — and judge the resulting candidate cards in the Inbox. Discovery is a delegated task: use the palette directly or ask the Co-PI to route it; either way, the Librarian searches and candidates come back as honest arguments.

## Prerequisites

- At least a few Catalog entries and source notes, so discovery has something to compare against
- `research-focus.md` reasonably current — the Librarian reads it to aim discovery

## Steps

**1. Delegate discovery.**

Use the direct command when you know this is a catalog/discovery job: `Cmd/Ctrl-P` → **Memoria: delegate task** → `catalog`. Or open the Agent Client pane and name the need as a research question, not keywords:

> "Find sources on just-in-time interventions for physical activity — what am I missing?"

Seed it however helps: "papers that build on `<citekey>`" (forward citations), "the foundational papers `<citekey>` builds on" (backward), "recent work that disagrees with my receptivity claims."

Both routes create a **`catalog`** task for the Librarian. The Co-PI route uses `delegate_route_task`; the palette route is the direct action path and should be the default when the lane is already clear.

**2. Let the Librarian search.**

It searches over the `paper_search` MCP (20+ scholarly databases) and compares hits against your Catalog so papers you already hold aren't resurfaced. Its posture is faithful and generous — include liberally, represent accurately, let your review gate filter — with a diversity reserve so the corpus doesn't become an echo chamber ([The Librarian](../../explanation/profiles/librarian.md)).

**3. Judge the candidates as one batch.**

**`candidate` cards** land in the Inbox (the **Needs me** view of `inbox/inbox.base`, shown on the Inbox space), one per proposed source, each carrying the honesty body and never a verdict ([Frontmatter fields](../../reference/frontmatter.md)). Judge each one the same way as any captured candidate — read `argument_against` first, then keep (`current`) or skip (`archived`) ([Capture and ingest a source](capture-and-ingest.md)). Work them in one sitting:

- **Keep:** the paper enters the Tutorial 03 flow (Catalog entity, reading queue, proposed source note).
- **Skip:** skipping generously offered candidates is the system working, not failing.

Resolving a card flips it in place ([Work the review queue](../inbox/work-the-review-queue.md)). Don't leave candidates undecided — a drip-feed of stale cards trains you to wave things through ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)).

**4. Feed it from gaps.**

Every `gap` card you agree with — from a `map` or `verify` pass — is a pre-written discovery prompt: use **Memoria: delegate task** → `catalog` with the gap as context, or ask the Co-PI ("that gap is real — find sources to fill it") if you want help shaping the request. This is the compounding loop: mapping finds holes, discovery fills them, verification keeps the filling honest.

## Verify

- Candidate cards from the run are all resolved — none left at `lifecycle: proposed`
- Kept papers have Catalog entities in `catalog/papers/` and appear in the reading queue (`system/dashboards/sources.base`) through their proposed source-note stubs

## Related

- After keeping a candidate: [Capture and ingest a source](capture-and-ingest.md)
- The full guided loop: [Tutorial 05: Close the loop](../../tutorials/05-close-the-loop.md)
- The profile behind the search: [The Librarian](../../explanation/profiles/librarian.md)
- A defensible, protocol-driven search instead: [Run a systematic review](run-a-systematic-review.md)
