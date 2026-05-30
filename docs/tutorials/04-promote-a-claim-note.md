---
topic: tutorials
---

# Tutorial: Promote a claim note

By the end you will have authored one `claim-note` from a source, grown its `maturity`, and promoted it toward a `reference-note`. This is the human-driven heart of Memoria — it works today (no agent pipeline required).

**Prerequisite:** [Tutorial 02](02-ingest-and-classify-a-batch.md) — at least one classified paper-note (`lifecycle: current`).

## Steps

1. **Discuss the source (optional but recommended).** Open the paper-note, then `Ctrl/Cmd+P → Memoria: ask about this note` to think it through with the Socratic profile (write-denied — the thinking stays yours). See [workflows/upstream/discuss.md](../how-to/workflows/upstream/discuss.md).
2. **Write the claim note.** `Ctrl/Cmd+P → Memoria: write claim note`, or create one in `30-synthesis/01-claims/` from the `claim-note` template. State one durable claim in your own words; it starts at `maturity: seedling`, `lifecycle: current`.
3. **Link it.** Cite the supporting paper-note(s) under `sources:`; record typed links in the `relations:` frontmatter (`supports` / `contradicts`) where they apply. See [vault/linking-patterns.md](../reference/linking-patterns.md).
4. **Grow maturity.** As more sources corroborate the claim and you link it from other notes, advance `seedling → budding → evergreen`. See [workflows/upstream/distill.md](../how-to/workflows/upstream/distill.md).
5. **Promote to reference.** Once `maturity: evergreen`, promote a stable claim into `30-synthesis/02-reference/` as a `reference-note`. This is a **human-gated** move — agents cannot write the synthesis zone (the policy MCP degrades their writes to `dry_run`). See [workflows/upstream/promote.md](../how-to/workflows/upstream/promote.md).

## What to check

- [`weekly-review`](../explanation/dashboards/weekly-review.md) surfaces evergreen claims ready to promote.
- A claim overturned later carries `superseded_by:` (its currency derives from that field) — see [decisions/22-claim-supersession.md](../project/decisions/22-claim-supersession.md).

## Next

- [Tutorial 05 — Add a second profile](05-add-a-second-profile.md) when one lane stops being enough.
