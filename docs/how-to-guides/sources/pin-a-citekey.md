# How to pin a citekey in Zotero

This guide shows you how to lock a paper's Better BibTeX citekey so it never regenerates when metadata changes.

Do this immediately after adding a paper to Zotero — before running ingest, before the note is created in the vault. An unpinned key can drift if metadata is corrected later, silently breaking vault wikilinks. See [Unpinned citekeys](../../explanation/knowledge/common-pitfalls.md#unpinned-citekeys) for why key stability matters.

## Steps

1. In Zotero, select the item.
2. Right-click → **Better BibTeX** → **Pin BibTeX key**.

The key is now frozen. You will see a lock icon on the key in the Zotero Better BibTeX preferences tab, and the key will no longer regenerate even if you edit the item's metadata.

## Batch-pin a collection

To pin all items in a collection at once:

1. Select all items in the collection (`Ctrl+A` / `Cmd+A`).
2. Right-click → **Better BibTeX** → **Pin BibTeX key**.

## What if you need to change a pinned key

If you discover a citekey is wrong after it has already been used in vault notes:

1. In Zotero, right-click the item → **Better BibTeX** → **Clear pinned BibTeX key**, then re-pin with the correct key.
2. In the vault, use `Cmd+P → Omnisearch` to find all occurrences of the old citekey.
3. Rename the paper-note file to the new citekey.
4. Update all wikilinks pointing to the old filename.
5. Run `hermes -p memoria-linter chat -s graph-analyze` to confirm no broken links remain.

This is why pinning before ingest is the discipline: changes after wikilinks exist cascade across the vault.

## Verify the key format

Memoria expects the BBT key format: `auth.lower + year + shorttitle(1,0)`

This produces `mamykina2010sense`, `chen2021pipeline`, `klasnja2019microrandomized`. Confirm this is your BBT setting under **Edit → Preferences → Better BibTeX → Citation keys → Citation key formula**.

---

## Related

- Pinning is step 2 of ingest: [capture-and-ingest.md](capture-and-ingest.md)
- The unpinned-citekey pitfall this fixes: [common-pitfalls.md](../../explanation/knowledge/common-pitfalls.md)
