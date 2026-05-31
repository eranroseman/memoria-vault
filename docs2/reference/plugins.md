---
topic: reference
---

# Plugins

Obsidian plugin inventory, install status, and load-bearing configuration for Memoria v0.1. For the plugin model and reasoning see [explanation/obsidian-plugins/](../../docs/explanation/obsidian-plugins/).

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

## Reference plugins (4)

Documented but not in the install set. Evaluated alternatives and future-migration targets.

| Plugin | Status | Notes |
| --- | --- | --- |
| zotlit | Future migration target | Reads Zotero SQLite directly — faster for bulk imports. |
| zotero-integration | Not in use | Imports Zotero items via HTTP API; Memoria annotates in Obsidian, not Zotero. |
| obsidian-kanban | Evaluated, not wired in | Cannot render `kanban.db` without an unadopted bridge. |
| obsidian-linter | Deferred (ADR-24) | Frontend formatter; writes outside the policy MCP audit trail; second frontmatter authority. |

---

## Load-bearing settings per plugin

Settings the human must not change without understanding the consequences. All others are personal preference.

### obsidian-local-rest-api

| Setting | Value | Why |
| --- | --- | --- |
| HTTPS port | `27124` | Hermes hard-coded to this port for vault access. |
| HTTP (insecure) port | off | Off by default; enable only in a fully isolated environment. |
| `data.json` | **gitignored** | Contains API key secrets — never commit. Ship as `.example`. |

### templater-obsidian

| Setting | Value | Why |
| --- | --- | --- |
| `templates_folder` | `00-meta/03-templates` | Must match the vault schema convention. |
| `trigger_on_file_creation` | `false` | Agents create files with their own frontmatter; auto-trigger races with agent writes. |
| `enable_system_commands` | `false` | Not needed by Memoria's Linter scripts; keep the attack surface small. |

### obsidian-citation-plugin

| Setting | Value | Why |
| --- | --- | --- |
| BibTeX file | `.memoria/library.bib` | Better BibTeX auto-exports here; this is the single source of bib data. |
| Literature note folder | `20-sources/01-papers/` | Notes must land in the canonical papers folder. |
| Template | `00-meta/03-templates/paper.md` | Must use the Memoria paper-note template. |

### obsidian-git

| Setting | Notes |
| --- | --- |
| `autoPush` | Deployment-conditional. On for `local-mesh` / `always-on`; off for `local-only`. |
| Commit message template | Keep the default or align with the vault's commit-message convention. |
| `post-commit` hook | Load-bearing — fires Verify/Revise workflows. Do not disable. |

### dataview

| Setting | Value | Why |
| --- | --- | --- |
| Enable JavaScript queries | `true` | Several dashboards use `dataviewjs` blocks. |
| Inline queries | `true` | Used in some reference notes for live field display. |

### agent-client

| Setting | Value | Why |
| --- | --- | --- |
| `defaultAgentId` | `memoria-socratic` | The Socratic profile is the default chat partner for reading sessions. |
| `autoMentionActiveNote` | `true` | The active note is automatically attached as context. |

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

**Never edit `data.json` while Obsidian is running.** Obsidian rewrites it on every settings change; external edits will be overwritten. Quit, edit, restart.

**Do not commit `main.js` or `styles.css`** from plugin folders — they change on every update and bloat git history. `.gitignore` should include `.obsidian/plugins/**/main.js` and `.obsidian/plugins/**/styles.css`.
