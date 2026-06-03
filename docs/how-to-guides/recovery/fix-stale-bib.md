---
title: Fix a stale .bib
parent: Recovery
nav_order: 5
---


# Fix a stale .bib

Resolve "citekey not found" errors at ingest caused by Zotero's auto-export not having run or by the Hermes node not having pulled the latest `.bib`.

## Symptom

Running `/obsidian-paper-note --source <citekey>` returns `"citekey not found"` or `"not in memoria.bib"`.

## Detect

Confirm the citekey is missing from the file:

```bash
grep <citekey> vault/.memoria/memoria.bib
```

If this returns nothing, the `.bib` is stale. If it returns the entry, the issue is something else — check the session logs.

## Fix

**Option A — Trigger auto-export from Zotero** (preferred).

In Zotero: File → Export Library → Better BibLaTeX → overwrite `vault/.memoria/memoria.bib`. Or make any change to the Zotero library (add/remove a tag) to trigger the auto-export.

**Option B — Force a git pull on the agent node** (if using a remote/VPS setup).

```bash
git pull --ff-only   # run on the node where Hermes runs
grep <citekey> vault/.memoria/memoria.bib   # confirm entry is now present
```

**Option C — Commit and push manually from Windows** (if auto-export ran but the file wasn't committed).

```bash
git add vault/.memoria/memoria.bib
git commit -m "manual: bib update"
git push
```

Then pull on the agent node (Option B).

## Verify

```bash
grep <citekey> vault/.memoria/memoria.bib        # entry present
git log --oneline vault/.memoria/memoria.bib | head -3   # recent commit timestamp
```

Then retry the ingest:

```bash
hermes -p memoria-librarian chat -s obsidian-paper-note
/obsidian-paper-note --source <citekey> --dry-run
```

`--dry-run` should complete without a "not found" error.

## Prevent recurrence

- Confirm Zotero's auto-export is set to "Automatic (on change)" in Better BibTeX preferences
- Confirm the export path is the absolute path to `vault/.memoria/memoria.bib`
- Pin every citekey immediately after adding to Zotero — unpinned keys can change and create false "not found" errors

## Related

- Zotero setup: [Set up Zotero](../setup/set-up-zotero.md)
- Full failure-modes catalog: [Failure modes](../../reference/failure-modes.md)
