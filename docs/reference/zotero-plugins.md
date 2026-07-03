---
title: Zotero plugins
parent: Obsidian and Zotero
grand_parent: Reference
---

# Zotero plugins

Optional plugins that install in **Zotero** (not Obsidian), plus a historical
Zotero↔Obsidian connector comparison. Alpha.15 has no Obsidian adapter plugin
set. For setup steps see
[Set up Zotero](../how-to-guides/setup/set-up-zotero.md).

---

## Zotero add-ons

Optional add-ons for users who keep references in Zotero.

| Add-on | Install in | Status | Purpose |
| --- | --- | --- | --- |
| Better BibTeX | Zotero | Optional, recommended for Zotero users | Stable citekeys; local BibTeX snapshots when needed; `zotero.lua` Lua filter for live Word export. |
| MarkDB-Connect | Zotero | Deferred | Legacy flat-note sync does not match alpha.15 nested source Concepts. |
| RTF/ODF Scan | Zotero | Optional | Converts Scannable Cite markers in `.odt` exports to live LibreOffice citations. Needed only for the LibreOffice live-citation export route. |

---

## Zotero ↔ Obsidian connector comparison

Four Obsidian plugins connect Zotero to Obsidian. The standalone CLI/runtime
does not require any of them; this comparison is retained only for optional
adapter evaluation.

| Plugin | Connects via | Zotero must run | Annotation import | Bulk import | Stability |
| --- | --- | --- | --- | --- | --- |
| **obsidian-citation-plugin** (hans) | `.bib` / CSL-JSON file | No | No | No | High — historical comparison only |
| **zotero-integration** (mgmeyers) | BBT HTTP API | Yes | Yes | No | High — breaks on major updates |
| **zotlit** (PKM-er) | Zotero SQLite DB | No (reads DB) | Yes | Yes | Medium — Zotero 9 issues reported |
| **zotero-bridge + zotero-link** (vanakat) | Zotero Local API | Yes | No | No | Low — ~20 installs/day |

For guidance on choosing between these connectors see [Set up Zotero](../how-to-guides/setup/set-up-zotero.md).

### Evaluated, not in the install set

| Plugin | Status | Notes |
| --- | --- | --- |
| zotlit | Not in use | Reads Zotero SQLite directly — faster for bulk imports, but not part of the standalone import path. |
| zotero-integration | Not in use | Imports Zotero items via HTTP API; useful if a PDF-annotation workflow is adopted. |
| Inciteful | Not in use | Citation-network discovery (Zotero plugin + public Inciteful API). Surfaces central related papers not yet in the library — a complement to OpenAlex forward/backward snowballing in the discover stage. Additive to an already-covered capability. |

---

## Related

- Obsidian no-plugin baseline: [Obsidian plugins](obsidian-plugins.md)
- Obsidian plugin-settings boundary: [Obsidian plugin settings](obsidian-plugin-settings.md)
- Zotero setup how-to: [Set up Zotero](../how-to-guides/setup/set-up-zotero.md)
