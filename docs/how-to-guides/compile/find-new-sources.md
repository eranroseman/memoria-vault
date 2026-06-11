---
title: Find new sources
parent: Compile
nav_order: 1
---

# Find new sources

Run a discovery pass — papers that build on what you hold, papers you're missing, or papers matching a research question — and judge the resulting candidate cards in the Inbox. Discovery is a delegated task: you ask, the Librarian searches, candidates come back as honest arguments.

## Prerequisites

- At least a few Catalog entries and source notes, so discovery has something to compare against
- `research-focus.md` reasonably current — the Librarian reads it to aim discovery

## Steps

**1. Ask the co-PI.**

Open the Agent Client pane and name the need as a research question, not keywords:

> "Find sources on just-in-time interventions for physical activity — what am I missing?"

Seed it however helps: "papers that build on `<citekey>`" (forward citations), "the foundational papers `<citekey>` builds on" (backward), "recent work that disagrees with my receptivity claims."

The co-PI delegates a **`catalog`** task to the Librarian via `delegate_route_task`. If you already know the lane, the palette twin is `Cmd/Ctrl-P` → **Memoria: delegate a task** → `catalog`.

**2. Let the Librarian search.**

It searches over the `paper_search` MCP (20+ scholarly databases) and compares hits against your Catalog so papers you already hold aren't resurfaced. Its posture is faithful and generous — include liberally, represent accurately, let your gate filter — with a diversity reserve so the corpus doesn't become an echo chamber ([The Librarian](../../explanation/profiles/librarian.md)).

**3. Judge the candidates as one batch.**

**`candidate` cards** land in the Inbox (`home.md` → **What needs me**), one per proposed source, each carrying the honesty body — `action`, `argument_for`, `argument_against`, `what_tipped_it`, `certainty`, and never a verdict. Read `argument_against` and `certainty` first. Then, in one sitting:

- **Keep:** resolve the card to `current` — the paper enters the Tutorial 03 flow (Catalog entity, reading queue, source note).
- **Skip:** resolve straight to `archived`. Skipping generously offered candidates is the system working, not failing.

`Cmd/Ctrl-P` → **Memoria: resolve inbox card** flips the active card in place. Don't leave candidates undecided — a drip-feed of stale cards trains you to wave things through ([ADR-54](../../adr/54-two-decision-kinds-batch-worklists.md)).

**4. Feed it from gaps.**

Every `gap` card you agree with — from a `map` or `verify` pass — is a pre-written discovery prompt: hand it straight back to the co-PI ("that gap is real — find sources to fill it"). This is the compounding loop: mapping finds holes, discovery fills them, verification keeps the filling honest.

## Verify

- Candidate cards from the run are all resolved — none left at `lifecycle: proposed`
- Kept papers have Catalog entities in `catalog/papers/` and appear in the reading queue (`system/dashboards/sources.base`, once you stub their source notes)

## Related

- After keeping a candidate: [Capture and ingest a source](capture-and-ingest.md)
- The full guided loop: [Tutorial 07: Find new sources](../../tutorials/07-find-new-sources.md)
- Scaling to a topic batch: [Tutorial 04: Build a reading batch](../../tutorials/04-build-a-reading-batch.md)
- The profile behind the search: [The Librarian](../../explanation/profiles/librarian.md)
- A defensible, protocol-driven search instead: [Run a systematic review](run-a-systematic-review.md)
