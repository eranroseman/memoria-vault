# Plugins

Obsidian plugin inventory, install status, and load-bearing configuration for Memoria v0.1. For the plugin model and reasoning see [explanation/obsidian-plugins/](../../docs/explanation/obsidian/).

---

## Required plugins (8)

Memoria breaks without these. Install before first use.

| Plugin | ID (`.obsidian/plugins/<id>/`) | Purpose |
| --- | --- | --- |
| obsidian-local-rest-api | `obsidian-local-rest-api` | Exposes the vault to Hermes via HTTPS (port 27124). Required for the control plane. |
| agent-client | `agent-client` | ACP inside Obsidian — routes human conversations with Hermes through a chat pane. |
| dataview | `dataview` | Powers every dashboard. Without it the dashboard layer is non-functional. |
| templater-obsidian | `templater-obsidian` | Runs frontmatter scripts the Linter's safe-fix mode relies on. |
| quickadd | `quickadd` | Registers all `Memoria:` command palette entries. |
| obsidian-citation-plugin | `obsidian-citation-plugin` | Inserts citations from `.memoria/library.bib`; creates paper notes from the configured template. |
| callout-manager | `callout-manager` | Defines `[!brief]`, `[!suggestions]`, `[!verification]` callout types. |
| obsidian-git | `obsidian-git` | Git commits from inside Obsidian; `post-commit` hook fires Verify/Revise workflows. |

---

## Recommended plugins (11)

Install when the friction is felt. Not required for core function.

### Core eight

| Plugin | Purpose |
| --- | --- |
| obsidian-homepage | Opens `Home.md` on startup (deterministic landing). |
| smart-connections | Vector search across notes. |
| smart-lookup | Question-first semantic search (shares index with smart-connections). |
| omnisearch | Fast fuzzy full-text search (keyword counterpart to smart-*). |
| supercharged-links + style-settings | Color-code links by note `type`. |
| hover-editor | Preview wikilinked notes in a popup. |
| tag-wrangler | Bulk-rename, merge, and inspect tags. |
| pdf-plus | Deep-link from notes to specific PDF passages. |

### Narrower three (install for specific use cases)

| Plugin | When to install |
| --- | --- |
| cmdr (Commander) | When binding Memoria commands to ribbon buttons becomes worthwhile. |
| obsidian-outliner | When nested-list editing becomes friction. |
| obsidian-excalidraw | When hand-drawn diagrams are needed (stored as `.excalidraw`). |

---

## Zotero-side add-ons

Plugins that install in Zotero (not Obsidian). Required or recommended alongside the Obsidian plugin set.

| Add-on | Install in | Status | Purpose |
| --- | --- | --- | --- |
| Better BibTeX | Zotero | **Required** | Stable citekeys; auto-export `.bib` to vault; `zotero.lua` Lua filter for live Word export. |
| MarkDB-Connect | Zotero | Recommended | Tags Zotero items that have a vault note; right-click → jump to note. Setup: [set-up-zotero.md](../how-to-guides/setup/set-up-zotero.md). |
| RTF/ODF Scan | Zotero | Optional | Converts Scannable Cite markers in `.odt` exports to live LibreOffice citations. Needed only for the LibreOffice live-citation export route. |

### Zotero ↔ Obsidian plugin comparison

Four Obsidian plugins connect Zotero to Obsidian. Memoria ships with `obsidian-citation-plugin`; the others are documented for evaluation.

| Plugin | Connects via | Zotero must run | Annotation import | Bulk import | Stability |
| --- | --- | --- | --- | --- | --- |
| **obsidian-citation-plugin** (hans) | `.bib` / CSL-JSON file | No | No | No | High — Memoria default |
| **zotero-integration** (mgmeyers) | BBT HTTP API | Yes | Yes | No | High — breaks on major updates |
| **zotlit** (PKM-er) | Zotero SQLite DB | No (reads DB) | Yes | Yes | Medium — Zotero 9 issues reported |
| **zotero-bridge + zotero-link** (vanakat) | Zotero Local API | Yes | No | No | Low — ~20 installs/day |

For guidance on choosing between these plugins see [how-to/setup/set-up-zotero.md](../how-to-guides/setup/set-up-zotero.md).

---

## Reference plugins (4)

Documented but not in the install set. Evaluated alternatives and future-migration targets.

| Plugin | Status | Notes |
| --- | --- | --- |
| zotlit | Future migration target | Reads Zotero SQLite directly — faster for bulk imports. See comparison table above. |
| zotero-integration | Not in use | Imports Zotero items via HTTP API; useful if PDF annotation workflow is adopted. |
| obsidian-kanban | Evaluated, not wired in | Cannot render `kanban.db` without an unadopted bridge. |
| obsidian-linter | Deferred (ADR-24) | Frontend formatter; writes outside the policy MCP audit trail; second frontmatter authority. |

---

## Load-bearing settings per plugin

Settings with a fixed required value. All others are personal preference. See [explanation/obsidian-plugins/](../../docs/explanation/obsidian/) for rationale.

### obsidian-local-rest-api

| Setting | Required value | Constraint |
| --- | --- | --- |
| HTTPS port | `27124` | Hermes hard-codes this port; changing it breaks vault access. |
| HTTP (insecure) port | off | Enable only in a fully isolated environment. |
| `data.json` | **gitignored** | Contains API key secrets. Ships as `.example`; never commit the real file. |

### templater-obsidian

| Setting | Required value | Constraint |
| --- | --- | --- |
| `templates_folder` | `00-meta/03-templates` | Must match vault schema convention. |
| `trigger_on_file_creation` | `false` | Auto-trigger races with agent writes. |
| `enable_system_commands` | `false` | Not required by Memoria; increases attack surface. |

### obsidian-citation-plugin

| Setting | Required value | Constraint |
| --- | --- | --- |
| BibTeX file | `.memoria/library.bib` | Single source of bib data; Better BibTeX auto-exports here. |
| Literature note folder | `20-sources/01-papers/` | Notes must land in the canonical papers folder. |
| Template | `00-meta/03-templates/paper.md` | Must use the Memoria paper-note template. |

### obsidian-git

| Setting | Required value | Constraint |
| --- | --- | --- |
| `commitMessage` | `"vault: {{date}} {{numFiles}} files"` | `{{numFiles}}` makes abnormally large auto-commits visible. |
| `autoBackupAfterFileChange` | `false` | Produces hundreds of commits per session when Hermes is writing; use scheduled commits (`autoSaveInterval: 30` min). |
| `pullBeforeCommit` | `true` | Required to catch divergence before the local commit. |
| `pullBeforePush` | `true` | Required; prevents conflicts on multi-machine setups. |
| `autoPullOnBoot` | `true` | Required; catches stale vaults when switching machines. |
| `post-commit` hook | enabled | Load-bearing — fires Verify workflow. Do not disable. |

**`autoPush` by deployment:**

| Deployment | `autoPush` | Notes |
| --- | --- | --- |
| `local-only` | `false` | Push manually for offsite-backup checkpoints. |
| `local-mesh` | `false` | Syncthing handles sync; Git is history only. |
| `obsidian-sync` | `false` | Obsidian Sync handles sync; Git is history only. |
| `always-on` (desktop) | `true` | Desktop auto-pushes as backup; Syncthing handles sync. |
| `always-on` (VPS) | — | Set `disablePush: true`; VPS must only pull. |

### dataview

| Setting | Required value | Constraint |
| --- | --- | --- |
| Enable JavaScript queries | `true` | Required; several dashboards use `dataviewjs` blocks. |
| Inline queries | `true` | Required; used in some reference notes for live field display. |
| `refreshEnabled` | `true` | Required; queries must update as notes change. |
| `refreshInterval` | `2500` (ms) | Default; lower values degrade performance on large vaults. |

### agent-client

| Setting | Required value | Constraint |
| --- | --- | --- |
| `defaultAgentId` | `memoria-socratic` | Default chat partner for reading sessions. |
| `autoMentionActiveNote` | `true` | Active note is automatically attached as context. |

### callout-manager

| Setting | Status |
| --- | --- |
| `data.json` | Ships as `data.json.TODO` — callout styling requires manual configuration after clone. |

---

## `data.json` conventions

| Suffix | Meaning |
| --- | --- |
| `data.json` | Committed, ready to use. |
| `data.json.example` | Committed stub; rename to `data.json` and fill in per-human values (e.g., API keys). |
| `data.json.TODO` | Committed; manual configuration required before the plugin is functional. |
| (gitignored) | Contains secrets; generated on first launch with defaults. |

| Constraint | Rule |
| --- | --- |
| `data.json` edits | Only edit while Obsidian is not running; Obsidian overwrites it on every settings change. |
| `main.js` / `styles.css` | Do not commit; add `.obsidian/plugins/**/main.js` and `.obsidian/plugins/**/styles.css` to `.gitignore`. |
