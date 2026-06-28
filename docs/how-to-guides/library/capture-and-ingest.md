---
title: Capture and ingest a source
parent: Library
grand_parent: How-to guides
nav_order: 2
---

# Capture and ingest a source

Goal: bring a paper into the vault. You capture it once; Memoria then builds the records and proposes that you keep it.

This is the full intake path. You capture the paper from the command palette (or from Zotero). After that, a background worker called the **Librarian** does the setup. The Librarian is the lane (a background worker) that owns the **catalog** — Memoria's set of records about papers.

By the end you have three things: a **catalog entity** (Memoria's record of the paper, at `catalog/papers/<citekey>.md`), a draft **source note** (your reading record, in `notes/sources/`), and a **candidate card** in your Inbox proposing that you keep the paper.

## Prerequisites

- The vault installed with the five profiles, and the Hermes gateway running ([Set up Hermes](../setup/set-up-hermes.md))
- Optional but recommended: Zotero with Better BibTeX, auto-exporting to `.memoria/memoria.bib` ([Set up Zotero](../zotero/set-up-zotero.md))

## Steps

**1. Capture the source.** Pick one of three routes. Each hands the same capture card to the Librarian.

- **From Zotero:** Add the source to Zotero. Better BibTeX pins the citekey for you. Select the item. Then, in Obsidian, press `Cmd/Ctrl-P` and run **Memoria: capture from Zotero selection**.
- **From a URL:** Press `Cmd/Ctrl-P`, run **Memoria: capture source from URL**, and paste the paper's URL. A URL with a resolvable DOI ingests on its own; a bare or proxied URL prompts for the DOI or citekey.
- **With Co-PI help:** The Co-PI is the one agent you talk to, in the Agent Client pane. If you are unsure how to frame the capture, open that pane and ask. Once the request is clear, use the matching palette route, or let the Co-PI hand off the same card for you.

**2. Clean the metadata in Zotero (Zotero route only).**

Check the title, authors, and year in Zotero's item panel before you capture. Memoria seeds its first record from these values, so fix any OCR or auto-import errors here, at the source.

**3. Let the ingest run — nothing to invoke.**

The Librarian claims the card and runs the ingest for you ([Ingest routing](../../reference/ingest.md)). Within a couple of minutes it produces the following.

- **The catalog entity**, at `catalog/papers/<citekey>.md`. This is Memoria's record of the paper. The Librarian fills it by merging metadata from four sources: Semantic Scholar, OpenAlex, Crossref, and PubMed/NCBI. Each field notes which source it came from (its provenance). If full text is available, the Librarian also extracts from it, and that shows up in the entity's metadata.
- **Links to related entities.** The catalog entity gets a `relationships` block — the edges to other records. Three kinds: `authored_by`, `published_in`, and `cites`. These point to person, venue, and paper entities, which the Librarian finds or creates alongside this one.
- **A classification, when it's clear.** The Librarian sets `research_area` (and `methodology` where it can tell). When the call is genuinely ambiguous, it leaves these unset and raises one `flag` in your Inbox instead.
- **A `candidate` card** in your Inbox. This proposes that you keep the paper. Its body is an honest argument for and against, not a verdict — you decide. The card also carries the Librarian's `_proposed_classification`.
- **A draft source note**, at `notes/sources/<citekey>.md`. This is the start of your reading record.

**4. Judge the candidate card.**

Your Inbox is a queue. Open its **Needs me** view, in `inbox.base`. Read `argument_against` first — it carries the most information ([Frontmatter fields](../../reference/frontmatter.md)).

Then decide. To keep the paper, resolve the card to `current`, act on it, then mark it `archived`. To skip it, resolve straight to `archived`; the catalog entity stays as a record either way. Resolving a card is one palette command ([Work the review queue](../inbox/work-the-review-queue.md)).

**5. Write your source note.**

For a kept paper, open the draft reading record from the Library space's source views. Its `entity:` field wikilinks back to the catalog entity. Its `lifecycle` is `proposed` until you read the paper. Fill the note in your own words.

The note's `lifecycle` then advances as you work. It moves to `provisional` once you've read the paper but not yet distilled it (the discuss queue picks it up at that point). It moves to `current` once you've distilled its claims. The full chain is defined in [Frontmatter fields](../../reference/frontmatter.md). For the end-to-end walkthrough, see [Tutorial 02: Bring in your first source](../../tutorials/02-bring-in-your-first-source.md).

## Verify

- `catalog/papers/<citekey>.md` exists, with `type: paper`, a `relationships` block, the merged metadata, and any metadata the full-text extract produced
- `system/logs/capture-intake.jsonl` has a new line for the capture, and `system/logs/audit.jsonl` shows the writes the gate let through
- A `candidate` card landed in `inbox/` (or you've already resolved it)
- `notes/sources/<citekey>.md` exists at `lifecycle: proposed`, ready for your reading notes

## Batch capture

Capture papers one at a time. Run one palette command (or make one Zotero selection) per paper. Each enqueues its own card, and the Librarian works through them one at a time (one `running` card per lane).

For a topic-sized batch, skip manual capture. Run discovery instead, with **Memoria: delegate task** targeting `catalog`. If you are still clarifying what you want, ask the Co-PI to shape the batch first. See [Find new sources](find-new-sources.md).

## If a capture stalls

A scheduled sweep, `memoria-sweeps`, runs every 15 minutes. It looks for captures that logged an intake line but never produced a note, and re-enqueues an ingest card for them. The re-ingest is safe to repeat, so a first stall needs no action from you. For a card stuck beyond that, see [Fix a stuck card](../troubleshooting/fix-stuck-card.md).

## Related

- Next step: [Classify a source](classify-a-source.md)
- If the citekey isn't found: [Fix a stale .bib](../zotero/fix-stale-bib.md)
- The pipeline behind the card: [Ingest routing](../../reference/ingest.md)
- The entity and card schemas: [Document types](../../reference/document-types.md)
