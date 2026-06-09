---
title: Obsidian plugins
parent: Reference
---

# Obsidian plugins

Obsidian plugin inventory, install status, and load-bearing configuration for Memoria v0.1. For Zotero-side add-ons and the Zotero↔Obsidian connector comparison see [Zotero plugins](zotero-plugins.md). For the plugin model and reasoning see [explanation/obsidian/](../explanation/obsidian).

---

## Required Obsidian plugins (8)

Memoria breaks without these. The starter vault **ships all eight bundled and configured** in `.obsidian/plugins/` — no manual install. Enable community plugins (turn off Restricted mode) on first launch; see [Set up Obsidian](../how-to-guides/setup/set-up-obsidian.md).

| Plugin | ID (`.obsidian/plugins/<id>/`) | Purpose |
| --- | --- | --- |
| obsidian-local-rest-api | `obsidian-local-rest-api` | Exposes the vault to Hermes via its native MCP over loopback HTTP (port 27123). Required for the control plane. |
| agent-client | `agent-client` | ACP inside Obsidian — routes human conversations with Hermes through a chat pane. |
| dataview | `dataview` | Powers every dashboard. Without it the dashboard layer is non-functional. |
| templater-obsidian | `templater-obsidian` | Runs frontmatter scripts the Linter's safe-fix mode relies on. |
| quickadd | `quickadd` | Registers all `Memoria:` command palette entries. |
| obsidian-citation-plugin | `obsidian-citation-plugin` | Inserts citations from `.memoria/memoria.bib`; creates paper notes from the configured template. (Zotero-side: see [Zotero plugins](zotero-plugins.md).) |
| callout-manager | `callout-manager` | Defines `[!brief]`, `[!suggestions]`, `[!verification]` callout types. |
| obsidian-git | `obsidian-git` | Git commits from inside Obsidian; `post-commit` hook fires Verify/Revise workflows. |

---

## Recommended Obsidian plugins (11)

Install when the friction is felt. Not required for core function.

### Core eight

| Plugin | Purpose |
| --- | --- |
| obsidian-homepage | Opens `home.md` on startup (deterministic landing). |
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

## Reference plugins (evaluated, not in the install set)

Documented but not in the install set. Obsidian-side evaluated alternatives. (Zotero-connector alternatives — zotlit, zotero-integration — are in [Zotero plugins](zotero-plugins.md).)

| Plugin | Status | Notes |
| --- | --- | --- |
| obsidian-kanban | Evaluated, not wired in | Cannot render `kanban.db` without an unadopted bridge. |
| obsidian-linter | **Incompatible — do not install** (ADR-12) | Frontend formatter; second frontmatter authority that collides with the agent-owned `_proposed_classification` / `_enrichment` namespaces and writes outside the policy MCP audit trail. No config makes it safe. |

---

## Load-bearing settings per plugin

Settings with a fixed required value. All others are personal preference. See [explanation/obsidian/](../explanation/obsidian) for rationale.

### obsidian-local-rest-api

| Setting | Required value | Constraint |
| --- | --- | --- |
| HTTP (insecure) server | **on**, port `27123` | Serves the plugin's native MCP at `http://127.0.0.1:27123/mcp` — Hermes's vault path ([ADR-31](../adr/31-native-obsidian-mcp.md)). Loopback-only. Each profile's `OBSIDIAN_MCP_PORT` must match; use distinct ports per vault to run a sandbox + production at once. |
| HTTPS port | `27124` | The plugin's HTTPS REST endpoint. **Not** the Hermes vault path — Hermes can't verify the self-signed cert, so it uses the HTTP MCP above. |
| `data.json` | **gitignored** | Contains API key secrets. Ships as `.example`; never commit the real file. |

### templater-obsidian

| Setting | Required value | Constraint |
| --- | --- | --- |
| `templates_folder` | `99-system/templates` | Must match vault schema convention. |
| `trigger_on_file_creation` | `false` | Auto-trigger races with agent writes. |
| `enable_system_commands` | `false` | Not required by Memoria; increases attack surface. |

### obsidian-citation-plugin

| Setting | Required value | Constraint |
| --- | --- | --- |
| BibTeX file (`citationExportPath`) | `.memoria/memoria.bib` | Single source of bib data; Better BibTeX auto-exports here. |
| Export format (`citationExportFormat`) | `biblatex` | Matches the Better BibTeX export. |
| Literature note folder (`literatureNoteFolder`) | `20-sources/01-papers` | Notes must land in the canonical papers folder. |
| Note title (`literatureNoteTitleTemplate`) | `@{{citekey}}` | Filename keys off the stable citekey. |
| Template (`literatureNoteContentTemplate`) | **Inline, in `data.json`** | This plugin has no external-template-file setting — the full paper-note body is stored inline in `literatureNoteContentTemplate`. Kept **structurally aligned** with `99-system/templates/paper-note.md` (the human-facing copy): both use `created`/`updated` timestamps and store `_proposed_classification`/`_enrichment` as **YAML frontmatter namespaces** (not HTML comments). They are not identical field-for-field (the citation copy carries Zotero `{{vars}}` and a few extra ingest fields); edit both together when the shared structure changes. |

### obsidian-git

| Setting | Required value | Constraint |
| --- | --- | --- |
| `commitMessage` / `autoCommitMessage` | `"vault: {{date}} {{numFiles}} files"` | `{{numFiles}}` makes abnormally large auto-commits visible. Set both keys so timed and manual commits match. |
| `autoBackupAfterFileChange` | `false` | Produces hundreds of commits per session when Hermes is writing; use scheduled commits instead. |
| `autoSaveInterval` | `30` | Scheduled commit every 30 min (the replacement for per-change backup). `0` disables it. |
| `pullBeforePush` | `true` | Required; prevents conflicts on multi-machine setups. |
| `autoPullOnBoot` | `true` | Required; catches stale vaults when switching machines. |
| `post-commit` hook | enabled | Load-bearing — fires Verify workflow. Lives in `.githooks/`, not `data.json`. Do not disable. |

> **Note:** obsidian-git has no `pullBeforeCommit` setting (earlier docs listed one in error). Divergence is caught by `autoPullOnBoot` + `pullBeforePush`. Push is governed by `disablePush` and `autoPushInterval` (`0` = no auto-push), not an `autoPush` boolean — the table below maps deployments onto those keys.

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

| Setting | Required value | Constraint |
| --- | --- | --- |
| `callouts.custom` | `["brief", "suggestions", "verification"]` | The three Memoria callout types must be registered as custom callouts. |
| `callouts.settings` | per-callout `color` (RGB triplet) + `icon` (Lucide id) | `brief` = `74, 144, 226` / `lucide-info`; `suggestions` = `123, 74, 226` / `lucide-list-plus`; `verification` = `226, 164, 74` / `lucide-shield-check`. Colors are stored as comma-separated RGB strings (not hex) — that is the format Callout Manager writes to `--callout-color`. |

---

## `data.json` conventions

| Suffix | Meaning |
| --- | --- |
| `data.json` | Committed, ready to use. |
| `data.json.example` | Committed stub; rename to `data.json` and fill in per-human values (e.g., API keys). |
| `data.json.TODO` | Committed; manual configuration required before the plugin is functional. |
| (gitignored) | Contains secrets; generated on first launch with defaults. |

**Example-file casing.** Memoria-authored example files use lowercase `.example` (the industry-standard convention; `.env.example`, `.sample`, etc.). The only uppercase exception is Hermes's `.env.EXAMPLE`, which is **generated by `hermes profile install`** ([upstream schema](https://hermes-agent.nousresearch.com/docs/user-guide/profile-distributions)) and reused verbatim — its casing is not Memoria's to change. Rule of thumb: *Memoria-authored = `.example`; Hermes-generated = `.EXAMPLE`*.

| Constraint | Rule |
| --- | --- |
| `data.json` edits | Only edit while Obsidian is not running; Obsidian overwrites it on every settings change. |
| `main.js` / `styles.css` / `manifest.json` | **Committed.** The starter vault ships every required plugin pre-installed, so the plugin build files are part of the distribution and are tracked in git. Do not add them to `.gitignore`. |
| Private `data.json` | Any plugin `data.json` that holds secrets or per-machine data is **gitignored and ships as `data.json.example`**. Two qualify: `obsidian-local-rest-api/data.json` (apiKey + TLS cert + RSA private key, regenerated on first launch) and `agent-client/data.json` (per-machine agent command paths + any provider apiKeys). Every other plugin's `data.json` carries no private data and is committed, configured to spec. Rule: a new secret-bearing config gets **both** a `.gitignore` line and a `.example` sibling. |

---

## Related

- How a new user enables these plugins: [Quickstart](../how-to-guides/setup/quickstart.md)
