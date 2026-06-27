---
title: Rebuild the search index
parent: Operate
grand_parent: How-to guides
nav_order: 5
---


# Rebuild the search index

Re-run the `qmd` embedding to restore semantic search. `qmd` (hybrid BM25 + vector search) is the shared similarity index behind the Co-PI's vault search, the Librarian's comparative pulls, and the Peer-reviewer's verify checks ([External integrations](../../reference/integrations.md)).

## When to rebuild

- The Co-PI's vault answers miss notes you know exist ([Query the vault](../knowledge/query-the-vault.md))
- New papers stop showing up in `[!brief]` comparisons or similarity checks
- A batch of 20+ notes was ingested and you haven't rebuilt since
- `qmd search "known term"` returns empty or omits notes you know exist

## When a re-embed is (and isn't) the fix

A full `qmd embed` re-embeds *every* note. Before spending the time, rule out cheaper causes:

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| One new note isn't found | Not yet indexed | Confirm it's saved to disk; a few notes rarely justify a full rebuild — let the scheduled rebuild (step 4) catch it |
| Search misses many notes or returns empty | Stale or missing index | Full `qmd embed` (this guide) |
| Found by keyword but not by meaning | Vectors stale / embedding model changed | Full `qmd embed` — re-embedding is the only fix when the vectors are stale |
| Found by `qmd search` but the Co-PI doesn't cite it | Not an index problem — a retrieval/prompt issue | Push the Co-PI ("which note says that?"), not the index |

## Steps

**1. Confirm the symptom.**

```bash
cd <vault>
qmd search "<term you know exists in a note>"
```

If this returns empty or fewer results than expected, the index is stale.

**2. Run a full rebuild.**

```bash
cd <vault>
qmd embed
```

This re-embeds every note in the vault. Estimated time:

| Vault size | Time |
| --- | --- |
| Under 500 notes | 1–5 minutes |
| 500–2000 notes | 5–15 minutes |
| 2000+ notes | 15–30 minutes |

The index lives inside the vault and is gitignored — never commit it.

**3. Verify the rebuild.**

```bash
qmd search "<term>"
```

Confirm the expected notes now appear. Then test the consumer you actually noticed the staleness in — ask the Co-PI a question whose answer lives in a recently added note and check it cites that note.

**4. Set up automatic rebuilds** (optional).

The installer wires no qmd cron — embedding is incremental in normal operation. If your ingest volume makes weekly full rebuilds worthwhile, drop a one-line wrapper in `~/.hermes/scripts/` and register it the same way the installer registers its deterministic crons:

```bash
printf '#!/usr/bin/env bash\ncd <vault> && qmd embed\n' > ~/.hermes/scripts/memoria-qmd-embed.sh
chmod +x ~/.hermes/scripts/memoria-qmd-embed.sh
hermes cron create '0 3 * * 0' --script memoria-qmd-embed.sh --no-agent \
  --name memoria-qmd-embed --deliver local
```

`hermes cron list` should then show `memoria-qmd-embed` with a next-run time.

## Verify

```bash
qmd search "claim note you recently wrote"
```

Returns the note, and the Co-PI's vault answers cite recently added notes again.

## Related

- Stale-index failure mode: [Failure modes](../../reference/failure-modes.md) — "qmd search index stale"
- The search consumer you'll notice first: [Query the vault](../knowledge/query-the-vault.md)
- Where qmd sits in the toolchain: [External integrations](../../reference/integrations.md)
