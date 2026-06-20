---
title: Write a claim note
parent: Knowledge
grand_parent: How-to guides
nav_order: 1
---

# Write a claim note

Distill a source into a single, durable claim in `notes/claims/`. One claim per note; no more than 2–3 claims per source. Claims live in a **review-gated zone** — agents can only propose writes there; you author claims directly, because they're yours.

## Prerequisites

- A read source whose **Worth distilling** section names the candidate ([Discuss a paper](../library/discuss-a-paper.md) sharpens it first)

## Steps

**1. Check for a near-duplicate first.**

Ask the Co-PI: "Do I already hold a claim like *\<one-sentence statement\>*?" — it searches the vault read-only and answers in the pane. For a systematic pass over a whole folder, delegate a `verify` task instead (the Peer-reviewer's duplicate hunt returns flag cards). If a close match exists, extend that note rather than creating a twin.

**2. Create the note.**

From a source note, click **Create linked claim** under **Worth distilling**. It creates a new note in `notes/claims/`, adds the source citekey to `sources`, links the claim back into the source note, and opens the claim for editing.

If you prefer the palette, open the source note and run `Memoria: create linked claim note` ([Obsidian command palette](../../reference/obsidian-command-palette.md)). The command asks for the claim sentence, then performs the same linked-source write. Before filing, it runs the qmd pre-file similarity shadow check and writes neighbours to a `[!similarity]` callout/log when available; that report is advisory and never blocks note creation.

For a standalone claim, use `Cmd/Ctrl-P` → **Memoria: write claim note** — a new note in `notes/claims/` from `system/templates/claim.md`, with the frontmatter pre-populated:

```yaml
type: claim
lifecycle: current
maturity: seedling
sources: []
topics: []
links:
  supports: []
  contradicts: []
```

**3. Name the file with the claim as the title.**

The filename *is* the claim: `receptivity-decreases-under-high-cognitive-load.md`, not `receptivity.md` or `mamykina-claim.md`. One falsifiable sentence, in your words. A topic stub is not a claim note.

**4. Write the body.**

- **Claim** — the assertion, standing alone; a reader with no access to the source should understand it.
- **Evidence** — why this seems true; **every line traces to a citekey in `sources`** (the provenance guardrail).
- **Connections** — the conceptual neighbors, in prose.

Do not quote the paper directly — distillation, not transcription.

**5. Check `sources`.**

The linked-claim button fills the active source's citekey for you. For standalone claim notes, list the citekey(s) of the supporting paper(s):

```yaml
sources: ["mamykina2010sense"]
```

**6. Leave maturity at `seedling`.**

Maturity (`seedling → budding → evergreen`) tracks development, never trust — a seedling isn't a doubted claim, it's a young one. It advances as connections accumulate: [Advance a claim to evergreen](promote-a-claim.md).

**7. Add typed links if applicable.**

If the claim supports or contradicts an existing claim, say so in `links:` — the contradictions are the valuable ones ([Link related claims](link-related-claims.md)). If it *replaces* an existing claim, that is supersession, not a link: set `superseded_by` on the **old** note instead ([Advance a claim to evergreen](promote-a-claim.md)).

**8. Close the loop on the source.**

Advance the source note past `provisional` and, if a candidate card is still open for this paper, resolve it — its job is done.

## Verify

- The file exists at `notes/claims/<claim-as-a-sentence>.md` with `maturity: seedling`, `lifecycle: current`
- At least one citekey in `sources`, and every Evidence line traces to one
- The claim appears in `system/dashboards/claims.base` under seedling

## Related

**How-to**

- Previous step: [Discuss a paper](../library/discuss-a-paper.md)
- When the claim settles: [Advance a claim to evergreen](promote-a-claim.md)
- Relating it to its neighbors: [Link related claims](link-related-claims.md)

**Reference**

- The claim schema: [Note types](../../reference/note-types.md)
- Field semantics: [Frontmatter fields](../../reference/frontmatter.md)

**Explanation**

- Why each section functions as knowledge: [Note body structure](../../explanation/knowledge/note-body-structure.md)
- The summary-without-synthesis pitfall: [Common pitfalls](../../explanation/knowledge/common-pitfalls.md)
