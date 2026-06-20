---
title: Advance a claim to evergreen
parent: Knowledge
grand_parent: How-to guides
nav_order: 3
---

# Advance a claim to evergreen

Mark a claim as settled knowledge by advancing its `maturity` to `evergreen` — no folder move, no rename; the claim stays in `notes/claims/`.

## Prerequisites

- The claim has accumulated real connections — cross-linked from several distinct sources or claims, and stable across recent reading
- The claim does **not** carry `superseded_by` — a superseded claim represents prior belief and never advances

## Steps

**1. Find candidates.**

`system/dashboards/claims.base` groups claims by maturity; `reading-pipeline.md` shows the same rollup. Long-stable `budding` claims with several inlinks are the candidates. The weekly review is the natural moment.

**2. Re-read the claim as a stranger.**

An evergreen claim will be read months from now without its original context. Tighten the body: the claim in one falsifiable sentence, the evidence with every line tracing to a `sources` citekey, the connections in prose.

**3. Advance the maturity.**

```yaml
maturity: evergreen
```

No move, no rename, no lifecycle change — `lifecycle: current` was already the claim's state from creation.

**4. Give it a navigational home.**

If a hub for the topic exists in `notes/hubs/`, add the claim to its `members` list. If this is the third or fourth settled claim on a topic with no hub, create one: [Build a hub](../knowledge/build-a-moc.md).

**5. Handle supersession separately.**

If this claim *replaces* an older one, set on the **old** note:

```yaml
superseded_by: "[[this-new-claim]]"
lifecycle: archived
```

The Linter's `fama-exposure` detector then flags any downstream note still wikilinking the superseded claim — reuse of obsolete memory.

## Verify

- The claim shows under **evergreen** in `system/dashboards/claims.base`
- A hub lists it as a member (or you've consciously decided the topic doesn't need one)
- No `superseded_by` claim was advanced

## Notes

**Don't advance to clear a queue.** Evergreen is a judgment that this claim is settled in your corpus. If you're uncertain, leave it at `budding` — that is not a penalty state.

## Related

- Where claims are born: [Write a claim note](write-a-claim-note.md)
- The hub the evergreen claim joins: [Build a hub](../knowledge/build-a-moc.md)
- Maturity vs lifecycle, and why `reference` was dropped: [Frontmatter fields](../../reference/frontmatter.md)
- The promotion rules: [Why promotion is gated](../../explanation/knowledge/promotion-model.md)
