---
title: "Tutorial 02: Bring in your first source"
parent: Tutorials
---

# Tutorial 02: Bring in your first source

**You will end with:** one source of your own in the Catalog, its candidate card judged in the Inbox, and one proposed source note filled in your own words — your first independent Accumulate rep, sitting alongside the sample's worked examples.

**Time:** 30–45 minutes (includes reading the paper or its abstract).

**You will use:** the Obsidian command palette, the Inbox, and the Co-PI pane.

**Prerequisite:** [Tutorial 01: See what you're building](01-orient.md) complete — the sample vault loaded and a project opened over it.

---

Accumulate is a **habit**, and a habit is learned one rep at a time. This is the rep: take something *you* are reading and turn it into a durable, traceable record. The sample vault hands you worked source notes to study, but the move only sticks when you do it on your own material — so this tutorial brings in a source of yours.

The sample vault you loaded in Tutorial 01 brought worked source notes (the PREDIMED note, the Lyon Diet Heart note, and others) — open the **Library** space and they show in the Reading pipeline, already filled. Keep one open in a split pane as you go — they are the *shape* you're aiming at, not something to copy verbatim.

## Step 1 — Capture your source

Pick a paper you actually want to read for your own goal, and copy its URL (the publisher page, or anything that resolves to a DOI). In Obsidian press `Cmd/Ctrl-P` → **Memoria: capture source from URL** → paste the URL. A resolvable DOI ingests immediately; a bare URL asks you for the DOI or citekey. That puts a capture card on the Librarian's `catalog` lane.

> **See also:** if you keep a [Zotero](https://www.zotero.org/) library, **Memoria: capture from Zotero selection** captures the selected item the same way — [Set up Zotero](../how-to-guides/zotero/set-up-zotero.md) is a one-time setup that gives you stable citekeys. If you are unsure what to capture, ask the Co-PI to help shape the request, then use the matching command; both command routes feed the same `catalog` lane.

---

## Step 2 — What the ingest operation creates

Within a couple of minutes the deterministic ingest operation, driven by the Librarian, has:

- Created the **Catalog entity**: `catalog/papers/<citekey>.md` with `type: paper`, merged metadata (title, DOI, authors, year, venue — per-field provenance from Semantic Scholar, OpenAlex, Crossref, and PubMed/NCBI), and a **`relationships`** block with `authored_by`, `published_in`, and `cites` edges into person, venue, and paper entities it finds or creates alongside.
- Created a **proposed source note stub** in `notes/sources/` so the reading queue can see it.

Open the **Library** space, find your new paper in its **Catalog** view (`catalog.base`), and look at the `relationships` block — those are the knowledge graph's *given* edges, built by the operation. Your own links come later, on notes you author. Compare it to a sample paper entity: same shape, real metadata. Full pipeline reference: [Ingest routing](../reference/ingest.md).

---

## Step 3 — Judge the candidate card

Capture doesn't end with a silent import: a **`candidate` card** lands in your Inbox proposing the keep. Open the Inbox space's **Needs me** view.

The card carries an *argument, never a verdict*: an `action`, the case for and against, what tipped it, and a certainty level. Read the `argument_against` field first — it's the information-bearing one. Then decide. Resolve the card from the palette: `Cmd/Ctrl-P` → **Memoria: resolve inbox card**. For this tutorial, keep it (`current` = accepted); a skipped card resolves straight to `archived` and the Catalog entry stays as a record. Why a card argues instead of ruling: [The honesty card](../explanation/kanban-board/card-schema.md).

---

## Step 4 — Read it, then write the source note in your own words

Read the paper, or at minimum its abstract and conclusions, with its Catalog entity open in a split pane (from the **Library** space's **Catalog** view) for the metadata and relationships. Watch for one or two things worth keeping — not a summary of everything.

Then open the proposed source note from the **Library** space's Reading pipeline. The source note is *your* reading record — the literature note, in your words, never the agent's. Under the hood it carries frontmatter like:

```yaml
type: source
lifecycle: proposed
entity: "[[<citekey>]]"
source_type: paper
```

- **`entity`** — the wikilink back to the Catalog entity from Step 2. Every source note is *about* exactly one Catalog entry.
- **`lifecycle: proposed`** — a source note starts proposed and advances as your distillation matures (full chain: [Frontmatter fields](../reference/frontmatter.md)).

Fill the three body sections the template gives you. This is where the sample notes earn their keep — open the **PREDIMED** source note (`estruch2018-predimed`) beside yours and notice *how* it's written, then write yours the same way about your own paper:

1. **In my words** — what the paper claims, on what evidence. Write it fresh; don't paste the abstract. (Look at how the PREDIMED note states the trial, the arms, and the result in plain sentences.)
2. **Worth distilling** — one or two candidate claims you might extract later. Each bullet is a future claim note. Use the **Create linked claim** button when a sentence is ready.
3. **Tensions** — where this paper disagrees with anything your vault already holds. Does your source touch the same causal-vs-confounded tension the sample's cluster holds? Note it.

Save, then set the source note to `lifecycle: provisional`: read, captured in your words, but not yet distilled into claims. Once you distill the claims you need (next tutorial), you'll advance it to `current`.

---

## A note on stray thoughts: fleeting notes

Not every thought arrives attached to a source. When something occurs to you mid-read with no citation behind it — a hunch, a question, a connection — capture it as a **fleeting note** (`Cmd/Ctrl-P` → **Memoria: capture fleeting**): the lightest capture there is, one item per note, no quality bar. It rides the same lifecycle as everything else and surfaces in the Inbox to be distilled into a real note or archived. That's the whole story on fleeting notes — they're a holding pen for un-sourced sparks, not where your knowledge lives. Sourced reading is the spine; keep your attention there.

---

## What you have

- `catalog/papers/<citekey>.md` — your own paper entity, with `relationships` edges into the Catalog
- A judged candidate card — you read an honest argument and resolved it
- `notes/sources/` — one provisional source note of your own, filled in your words, linked to its entity
- The sample's worked source notes still sitting alongside as models

The paper is a vault citizen; the source note is your intellectual claim on it. You've done one rep of the Accumulate habit — the months are just this, repeated.

---

## What's next

[Tutorial 03: Build claims and connect them](03-build-claims-and-connect-them.md) — study a worked claim in the sample, finish its half-built claims and links, then distill a claim from your own source and wire it into the cluster.

---

← [Tutorial 01: See what you're building](01-orient.md) · [Tutorial 03: Build claims and connect them](03-build-claims-and-connect-them.md) →
