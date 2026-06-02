---
title: "Safe mode: minimal working path"
parent: Recovery
---

# Safe mode: minimal working path

When optional tooling is unavailable, these three workflows must still function. For each: the command that must work, the named fallbacks, and the one thing never to run automatically.

## Ingest a source

**Must work:**

```bash
hermes -p memoria-librarian chat -s obsidian-paper-note
# in session:
/obsidian-paper-note --source <citekey>
```

**If the ACP pane is unresponsive** — the terminal is always the fallback. ACP is a convenience layer over the same Hermes operations.

**If enrichment APIs are unreachable** — ingest still creates the note with Zotero metadata. Run enrichment separately once connectivity is restored:

```bash
hermes -p memoria-librarian chat -s obsidian-paper-note
/obsidian-paper-note --source <citekey> --skip-enrichment
```

A note without enrichment is better than a deferred ingest.

**If `.bib` is not synced** — push it manually first:

```bash
git add vault/.memoria/memoria.bib
git commit -m "manual: bib update"
git push
```

Then ingest.

**Never run automatically:** `schema-migrate`. Schema changes require human review of every proposed field change.

---

## Review and triage

**Must work:** open `00-meta/01-dashboards/weekly-review.md` in Obsidian. The Dataview queries surface the triage queue without any Hermes involvement.

**If Hermes is unreachable** — triage is a human-only action. Classify by hand:

1. Open the paper note in `20-sources/01-papers/`
2. Copy fields from the `_proposed_classification` comment block into main frontmatter
3. Delete the comment block
4. Set `lifecycle: current` (the "classified" marker; triage completion is a board state, not a note field)

**If Dataview is not rendering** — search manually in Obsidian for `lifecycle: proposed` to find unclassified notes.

**Never run automatically:** promote claim notes from `10-inbox/` to `30-synthesis/`. Every inbox note requires human review — agent synthesis is unverified until a human confirms the citekeys and claims.

---

## Export a draft

**Must work:**

```bash
pandoc 40-workbench/<project>/04-drafts/<draft>.md \
  --citeproc \
  --bibliography vault/.memoria/memoria.bib \
  --csl vault/.memoria/csl/<style>.csl \
  -o /tmp/<output>.docx
```

**If an Obsidian export plugin fails** — run Pandoc directly from the terminal; it is the authoritative export route (any plugin is just a UI wrapper over the same command). See [Export routes and formats](../../reference/export.md).

**If `zotero.lua` live citations are broken** — fall back to static `--citeproc`. Do not debug `zotero.lua` mid-draft. Finish the draft with static citations, then investigate using the failure-modes guide.

**Never run automatically:** auto-export on file save. Drafts change constantly; automatic export creates Git noise and can overwrite a clean export with a mid-sentence state.

---

## Quick system check

Run before assuming something is broken:

```bash
echo $KILOCODE_API_KEY $OPENALEX_API_KEY   # env vars loaded?
hermes --version                           # Hermes reachable?
hermes profile list                        # profiles registered?
cd <vault-path> && git status              # vault synced?
```

All four must return expected values before blaming a tool.

## Related

- Return-to-work checklist: [How to return to work after a break](../maintenance/return-to-work.md)
- Fix stale .bib: [How to fix a stale .bib](fix-stale-bib.md)
- Fix stuck card: [How to fix a stuck card](fix-stuck-card.md)
- Rebuild search index: [How to rebuild the search index](../maintenance/rebuild-the-search-index.md)
