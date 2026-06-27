---
title: Fix a stale .bib
parent: Zotero
grand_parent: How-to guides
nav_order: 5
---


# Fix a stale .bib

**Symptom:** a capture card fails at ingest with `"citekey not found"` or `"not in memoria.bib"` — the candidate never lands, and the failure surfaces on the card or in the Librarian's session log.

**Diagnosis:** the citekey is missing from `memoria.bib` — either Zotero's auto-export hasn't run, or the Hermes node hasn't pulled the latest `.bib`. Confirm with a `grep` before reaching for a fix.

**Fix:** re-export from Zotero, pull on the agent node, or commit and push the file — whichever step is missing.

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

Then retry the ingest — re-run the capture (`Cmd/Ctrl-P` → **Memoria: capture from Zotero selection** with the item selected), or enqueue the card from the terminal:

```bash
hermes kanban create "Ingest <citekey>" --assignee memoria-librarian
```

The Librarian's run should now complete without a "not found" error and raise the candidate card in `inbox/`.

## Prevent recurrence

- Confirm Zotero's auto-export is set to "Automatic (on change)" in Better BibTeX preferences
- Confirm the export path is the absolute path to `vault/.memoria/memoria.bib`
- Pin every citekey immediately after adding to Zotero — unpinned keys can change and create false "not found" errors

## Related

- Zotero setup: [Set up Zotero](set-up-zotero.md)
- Full failure-modes catalog: [Failure modes](../../reference/failure-modes.md)
