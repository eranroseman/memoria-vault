---
title: Rebuild the search index
parent: Maintain
nav_order: 9
---


# Rebuild the search index

Re-run the `qmd` embedding to restore semantic search when the Writer returns empty results or when a large batch of notes has been added.

## When to rebuild

- The Writer's `/draft` command returns no vault results despite relevant notes existing
- A batch of 20+ notes was ingested and you haven't rebuilt since
- `qmd search "known term"` returns empty or omits notes you know exist

## When a re-embed is (and isn't) the fix

A full `qmd embed` re-embeds *every* note — it's the right tool only for genuine index staleness. Before spending the time, rule out cheaper causes:

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| One new note isn't found | Not yet indexed | Confirm it's saved to disk; a few notes rarely justify a full rebuild — let the scheduled rebuild (step 4) catch it |
| Search misses many notes or returns empty | Stale or missing index | Full `qmd embed` (this guide) |
| Found by keyword but not by meaning | Vectors stale / embedding model changed | Full `qmd embed` — re-embedding is the only fix when the vectors are stale |
| Found in `qmd search` but missing from `/draft` | Not an index problem — a Writer retrieval issue | Check the query, not the index |

A full re-embed is genuinely *required* only when the embedding model or config changed, `.qmd-index/` is corrupt or missing, or a large batch (20+) landed. For a handful of notes, the scheduled rebuild is cheaper than an ad-hoc full pass.

## Steps

**1. Confirm the symptom.**

```bash
qmd search "<term you know exists in a note>" --vault <absolute-vault-path>
```

If this returns empty or fewer results than expected, the index is stale.

**2. Run a full rebuild.**

```bash
cd <absolute-vault-path>
qmd embed
```

This re-embeds every note in the vault. Estimated time:

| Vault size | Time |
| --- | --- |
| Under 500 notes | 1–5 minutes |
| 500–2000 notes | 5–15 minutes |
| 2000+ notes | 15–30 minutes |

The index is written to `.qmd-index/` inside the vault. This folder is gitignored — never commit it.

**3. Verify the rebuild.**

```bash
qmd search "<term>" --vault <absolute-vault-path>
```

Confirm the expected notes now appear. Then test in a Writer session:

```bash
hermes -p memoria-writer chat -s draft
# then, in the session:
/draft "<known topic>" 
```

The response should reference vault notes with citekeys.

**4. Set up automatic rebuilds** (optional).

To rebuild on a schedule, add to the Linter's cron tasks in `vault/.memoria/profiles/memoria-linter/cron/`:

```yaml
- name: rebuild-qmd-index
  schedule: "0 3 * * 0"   # 3 AM every Sunday
  command: "qmd embed"
  working_dir: "{{VAULT_PATH}}"
```

Run `bash scripts/install.sh --profiles-only` (`.\scripts/install.ps1 -ProfilesOnly` on Windows) to register the new cron task.

## Verify

```bash
qmd search "claim note you recently wrote" --vault <vault-path>
```

Returns the note. The Writer's `/draft` command uses vault notes in its response.

## Related

- Stale search index failure mode: [Failure modes](../../reference/failure-modes.md) — "Stale qmd index"
- Writer profile: [The Writer](../../explanation/profiles/writer.md)
