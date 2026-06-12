---
title: Safe mode
parent: Troubleshooting
nav_order: 1
---

# Safe mode

**Symptom:** Hermes, ACP, or some optional tool is down, and you still need to ingest, triage, or export.

**Diagnosis:** the integration layer is unreachable, but the underlying operations don't depend on it — every core workflow has a terminal-level fallback.

**Fix:** for each of the three workflows below — the command that must work, the named fallbacks, and the one thing never to run automatically.

## Ingest a source

**Must work:** enqueue the capture card from the terminal — the same card the palette commands create:

```bash
hermes kanban create "Ingest <citekey>" --assignee memoria-librarian
```

**If the ACP pane is unresponsive** — the terminal is always the fallback: the pane and the palette macros shell out to the same `hermes kanban create`. A direct lane chat (`hermes -p memoria-librarian chat`) also works as a debugging posture.

**If enrichment APIs are unreachable** — ingest still creates the Catalog entity from the `.bib` metadata; the per-field provenance records what's missing. The enrichment fills in on a later re-ingest once connectivity is restored — a thin entity is better than a deferred ingest.

**If `.bib` is not synced** — push it manually first, then ingest: [Fix a stale .bib](../zotero/fix-stale-bib.md).

**Never run automatically:** a schema migration. Schema changes require human review of every proposed field change ([Run a schema migration](../operate/run-a-schema-migration.md)).

---

## Review and triage

**Must work:** open `system/dashboards/weekly-review.md` in Obsidian. The Dataview queries surface the triage queue without any Hermes involvement.

**If Hermes is unreachable** — triage is a human-only action anyway. Classify by hand:

1. Open the paper entity in `catalog/papers/`
2. Copy the fields you accept from the `_proposed_classification` block into the main frontmatter
3. Delete the `_proposed_classification:` block
4. Set `lifecycle: current` ([Classify a source](../compile/classify-a-source.md))

**If Dataview is not rendering** — search manually in Obsidian for `lifecycle: proposed` to find unclassified notes.

**Never run automatically:** accept Inbox cards in bulk. Every `proposed` card requires human review — agent output is unverified until you confirm the citekeys and claims.

---

## Export a draft

**Must work:**

```bash
pandoc projects/<slug>/<draft>.md \
  --citeproc \
  --bibliography .memoria/memoria.bib \
  --csl .memoria/csl/<style>.csl \
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

- Return-to-work checklist: [Return to work](../curate/return-to-work.md)
- Fix stale .bib: [Fix a stale .bib](../zotero/fix-stale-bib.md)
- Fix stuck card: [Fix a stuck card](fix-stuck-card.md)
- Rebuild search index: [Rebuild the search index](../operate/rebuild-the-search-index.md)
