
# How to rebuild the search index

Re-run the `qmd` embedding to restore semantic search when the Writer returns empty results or when a large batch of notes has been added.

## When to rebuild

- The Writer's `/draft` command returns no vault results despite relevant notes existing
- A batch of 20+ notes was ingested and you haven't rebuilt since
- `qmd search "known term"` returns empty or omits notes you know exist

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

Run `./install.ps1` to register the new cron task.

## Verify

```bash
qmd search "claim note you recently wrote" --vault <vault-path>
```

Returns the note. The Writer's `/draft` command uses vault notes in its response.

## Related

- Writer profile: [explanation/profiles/writer.md](../../explanation/profiles/writer.md)
- Stale search index failure mode: [how-to/operations/failure-modes.md](../../how-to-guides/recovery/) — "Stale qmd index"
