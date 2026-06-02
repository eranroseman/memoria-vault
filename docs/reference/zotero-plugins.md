---
title: Zotero plugins
parent: Reference
---

# Zotero plugins

Plugins that install in **Zotero** (not Obsidian), plus the Zotero↔Obsidian connector comparison. For the Obsidian plugin set (including `obsidian-citation-plugin`, the connector Memoria ships with) see [obsidian-plugins.md](obsidian-plugins.md). For setup steps see [set-up-zotero.md](../how-to-guides/setup/set-up-zotero.md).

---

## Zotero add-ons

Required or recommended alongside the Obsidian plugin set.

| Add-on | Install in | Status | Purpose |
| --- | --- | --- | --- |
| Better BibTeX | Zotero | **Required** | Stable citekeys; auto-export `.bib` to vault; `zotero.lua` Lua filter for live Word export. |
| MarkDB-Connect | Zotero | Recommended | Tags Zotero items that have a vault note; right-click → jump to note. Setup: [set-up-zotero.md](../how-to-guides/setup/set-up-zotero.md). |
| RTF/ODF Scan | Zotero | Optional | Converts Scannable Cite markers in `.odt` exports to live LibreOffice citations. Needed only for the LibreOffice live-citation export route. |

---

## Zotero ↔ Obsidian connector comparison

Four Obsidian plugins connect Zotero to Obsidian. Memoria ships with `obsidian-citation-plugin` (documented in [obsidian-plugins.md](obsidian-plugins.md)); the others are documented here for evaluation.

| Plugin | Connects via | Zotero must run | Annotation import | Bulk import | Stability |
| --- | --- | --- | --- | --- | --- |
| **obsidian-citation-plugin** (hans) | `.bib` / CSL-JSON file | No | No | No | High — Memoria default |
| **zotero-integration** (mgmeyers) | BBT HTTP API | Yes | Yes | No | High — breaks on major updates |
| **zotlit** (PKM-er) | Zotero SQLite DB | No (reads DB) | Yes | Yes | Medium — Zotero 9 issues reported |
| **zotero-bridge + zotero-link** (vanakat) | Zotero Local API | Yes | No | No | Low — ~20 installs/day |

For guidance on choosing between these connectors see [set-up-zotero.md](../how-to-guides/setup/set-up-zotero.md).

### Evaluated, not in the install set

| Plugin | Status | Notes |
| --- | --- | --- |
| zotlit | Future migration target | Reads Zotero SQLite directly — faster for bulk imports. See comparison table above. |
| zotero-integration | Not in use | Imports Zotero items via HTTP API; useful if a PDF-annotation workflow is adopted. |
| Inciteful | Not in use | Citation-network discovery (Zotero plugin + public Inciteful API). Surfaces central related papers not yet in the library — a complement to OpenAlex forward/backward snowballing in the discover stage. Additive to an already-covered capability. |

---

## Related

- Obsidian plugin set and load-bearing settings: [obsidian-plugins.md](obsidian-plugins.md)
- Zotero setup how-to: [set-up-zotero.md](../how-to-guides/setup/set-up-zotero.md)
