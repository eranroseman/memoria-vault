---
title: Capture and ingest a source
parent: Library
nav_order: 2
---

# Capture and ingest a source

Move a paper from discovery into the vault as a Catalog entity, proposed source note, and judged candidate card. This is the complete intake path: capture from the palette (or Zotero), then the ingest operation and the Librarian do the setup work.

## Prerequisites

- The vault installed with the five profiles and the Hermes gateway running ([Set up Hermes](../setup/set-up-hermes.md))
- Optional but recommended: Zotero + Better BibTeX auto-exporting to `.memoria/memoria.bib` ([Set up Zotero](../zotero/set-up-zotero.md))

## Steps

**1. Capture the source.** Three routes, all landing the same capture card on the Librarian's `catalog` lane:

- **From Zotero:** add the source to Zotero (Better BibTeX pins the citekey automatically), select the item, then in Obsidian press `Cmd/Ctrl-P` → **Memoria: capture from Zotero selection**.
- **From a URL:** `Cmd/Ctrl-P` → **Memoria: capture source from URL** and paste the paper's URL. A URL with a resolvable DOI ingests; a bare or proxied URL asks you for the DOI or citekey.
- **With Co-PI help:** if you are unsure how to frame the capture, open the Agent Client pane and ask; once the request is clear, use the matching palette route or let the Co-PI delegate the same card.

**2. Clean the metadata in Zotero (Zotero route only).**

Check title, authors, and year in Zotero's item panel before capture. These values seed the Tier-0 record, so fix OCR or auto-import errors at the source.

**3. Let the operation run — nothing to invoke.**

The Librarian claims the card and drives the deterministic ingest operation over the ingest MCP ([Ingest routing](../../reference/ingest.md)). Within a couple of minutes it has:

- Created the **Catalog entity** at `catalog/papers/<citekey>.md` — merged metadata with per-field provenance (Semantic Scholar + OpenAlex + Crossref + PubMed/NCBI) and `relationships` edges (`authored_by`, `published_in`, `cites`) into person, venue, and paper entities it finds or creates alongside
- Applied `research_area` (and `methodology` where derivable) automatically when the classification is clear — or left it unset and raised one Inbox `flag` on genuine ambiguity
- Recorded the visible Catalog entity at `catalog/papers/<citekey>.md`; when full text is available, the private operation extract path is reflected in that entity's metadata
- Raised a **`candidate` card** in your Inbox proposing the keep, with the honesty body and the Librarian's `_proposed_classification`
- Created a proposed source-note stub in `notes/sources/<citekey>.md` for your reading record

**4. Judge the candidate card.**

Open the Inbox queue's **Needs me** view of `inbox.base`. Read `argument_against` first — it's the information-bearing field ([Frontmatter fields](../../reference/frontmatter.md)). Then keep it (resolve to `current`, act on it, then `archived`) or skip it (resolve straight to `archived` — the Catalog entry stays as a record). Resolving a card is one palette command: [Work the review queue](../inbox/work-the-review-queue.md).

**5. Write your source note.**

For a kept paper, open the proposed reading record from the Library space's source views — `entity:` wikilinks the Catalog entry, `lifecycle: proposed` until you read it. Fill it in your own words. Once read it advances to `provisional` (read, not yet distilled — the discuss queue picks it up there), then `current` once you've distilled its claims (the lifecycle chain is defined in [Frontmatter fields](../../reference/frontmatter.md)). The full loop is [Tutorial 02: Bring in your first source](../../tutorials/02-bring-in-your-first-source.md).

## Verify

- `catalog/papers/<citekey>.md` exists with `type: paper` and a `relationships` block
- `system/logs/capture-intake.jsonl` has a new line for the capture, and `system/logs/audit.jsonl` shows the gated writes
- A `candidate` card landed in `inbox/` (or you've already resolved it)
- `catalog/papers/<citekey>.md` includes the visible metadata and any extract-path metadata the operation produced
- `notes/sources/<citekey>.md` exists at `lifecycle: proposed`, ready for your reading notes

## Batch capture

Capture each source individually — one palette invocation (or one Zotero selection) per paper; each enqueues its own card and the Librarian processes them one at a time (one `running` card per lane). For a topic-sized batch, skip manual capture entirely and run discovery through **Memoria: delegate task** → `catalog`, or ask the Co-PI to shape the batch if you are still clarifying the request: [Find new sources](find-new-sources.md).

## If a capture stalls

The `memoria-sweeps` cron (every 15 minutes) detects captures that logged an intake line but never landed a note, and enqueues an idempotent re-ingest card — no action needed for a first occurrence. A card stuck beyond that: [Fix a stuck card](../troubleshooting/fix-stuck-card.md).

## Related

- Next step: [Classify a source](classify-a-source.md)
- If the citekey isn't found: [Fix a stale .bib](../zotero/fix-stale-bib.md)
- The pipeline behind the card: [Ingest routing](../../reference/ingest.md)
- The entity and card schemas: [Document types](../../reference/document-types.md)
