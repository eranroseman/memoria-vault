---
title: Obsidian plugin settings
parent: Obsidian and Zotero
grand_parent: Reference
---

# Obsidian plugin settings

Load-bearing settings for the Obsidian plugins Memoria ships or relies on. For the plugin inventory and install status, see [Obsidian plugins](obsidian-plugins.md).

## Settings per plugin

Settings with a fixed required value. All others are personal preference. See [explanation/obsidian/](../explanation/obsidian) for rationale.

### obsidian-local-rest-api

| Setting | Required value | Constraint |
| --- | --- | --- |
| HTTPS server | **on**, port `27124` | Serves the plugin's native MCP at `https://127.0.0.1:27124/mcp` — Hermes's vault path ([ADR-31](../adr/31-native-obsidian-mcp.md)). Loopback-only. Each profile's `OBSIDIAN_MCP_PORT` must match; use distinct ports per vault to run a sandbox + production at once. |
| HTTPS certificate | Exported PEM path in `OBSIDIAN_MCP_SSL_VERIFY` | Hermes passes this path to `mcp_servers.obsidian.ssl_verify`, keeping certificate verification enabled for the plugin's self-signed/local cert. |
| HTTP (insecure) server | off unless debugging | Plain HTTP is no longer the shipped Hermes path. Do not use it for normal profile runs. |
| `data.json` | **gitignored** | Contains API key secrets. Ships as `.example`; never commit the real file. |

### obsidian-citation-plugin

| Setting | Required value | Constraint |
| --- | --- | --- |
| BibTeX file (`citationExportPath`) | `references.bib` | Generated tracked projection from checked SQLite catalog rows; the worker regenerates it. |
| Export format (`citationExportFormat`) | `biblatex` | Matches the Better BibTeX export. |
| Literature note folder (`literatureNoteFolder`) | `.memoria/staging/catalog` | The plugin has no disable switch for literature-note creation, so accidental output lands in ignored staging instead of live Concepts. Source capture goes through the worker. |
| Note title (`literatureNoteTitleTemplate`) | `@{{citekey}}` | Filename keys off the stable citekey. |
| Template (`literatureNoteContentTemplate`) | **Inline, in `data.json`** | Scratch notice only. It must not be a valid Concept template. |

### CSS snippets

| Snippet | Required value | Constraint |
| --- | --- | --- |
| `memoria-link-colors.css` | Enabled by default through the installer-maintained `enabledCssSnippets` entry in `appearance.json`; user can toggle after install | Colors wikilinks by folder/type and adds lifecycle accents when Supercharged Links exposes `data-link-*` attributes. |
| `memoria-property-badges.css` | Enabled by default through the installer-maintained `enabledCssSnippets` entry in `appearance.json`; user can toggle after install | Accents scan-critical Properties rows: `lifecycle`, `ingest_status`, `loudness`, and verification status. This is the visual layer for the property display order in [Frontmatter fields](frontmatter.md). |

### obsidian-git

| Setting | Required value | Constraint |
| --- | --- | --- |
| `commitMessage` / `autoCommitMessage` | `"vault: {{date}} {{numFiles}} files"` | `{{numFiles}}` makes abnormally large commits visible. Set both keys so manual commits are stable and timed commits stay recognizable if a user later opts into them. |
| `autoBackupAfterFileChange` | `false` | Produces commits outside the worker-owned write path. |
| `autoSaveInterval` | `0` | Automatic Obsidian Git commits are disabled. Commit manually when the PI wants a vault-history checkpoint. |
| `pullBeforePush` | `true` | Required; prevents conflicts once a remote is configured. |
| `autoPullOnBoot` | `false` | Required default; fresh sandboxes and local-only vaults have no upstream branch, so startup must not emit a git pull error. Users with a remote can enable boot pulls after setting an upstream. |
| `post-commit` hook | enabled | Load-bearing for legacy policy-runtime draft checks. Source lives in `.githooks/`, installer copies it into `.git/hooks/`; it is not a `data.json` setting. Do not disable while that runtime remains shipped. |

The host running Obsidian or the sandboxed test runtime must have a real `git`
binary on `PATH`. Without it, manual Obsidian Git checkpoints, pre-commit schema
validation, verify-on-commit, rollback, and history are degraded; the installer
now fails clearly instead of silently skipping those paths.

> **Note:** obsidian-git has no `pullBeforeCommit` setting (earlier docs listed one in error). Divergence is caught by manual pulls plus `pullBeforePush`; enable `autoPullOnBoot` only after the vault branch has an upstream. Push is governed by `disablePush` and `autoPushInterval` (`0` = no auto-push), not an `autoPush` boolean — the table below maps each deployment onto those two real keys.

**Push behavior by supported deployment** (the two keys that actually exist):

| Deployment | `disablePush` | `autoPushInterval` | Notes |
| --- | --- | --- | --- |
| `local-only` | `false` | `0` | Push manually for offsite-backup checkpoints. |

Second-device or always-on sync topologies are deferred design notes, not supported
install targets. Do not enable automated push/pull behavior for them without a new
deployment decision.

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
| `defaultAgentId` | `memoria-copi` | The Co-PI is the only Agent Client chat partner (`test_agent_client_pane_is_copi_only`). |
| `customAgents[0].displayName` | `Memoria Co-PI` | The pane label uses the product-facing agent name, not the internal profile id. |
| `autoMentionActiveNote` | `true` | Active note is passed as a readable reference; selected text and explicit attachments carry bounded body context. |
| `exportSettings.defaultFolder` | `system/exports` | Session exports are visible PI review material; never point them at hidden `.memoria/` internals. |
| `exportSettings.autoExportOnNewChat` / `autoExportOnCloseChat` | `true` / `true` | Pane sessions export automatically at session start and close. |
| `exportSettings.openFileAfterExport` | `false` | Exporting a session must not steal focus from the Co-PI conversation. |
| `exportSettings.imageCustomFolder` | `system/exports/assets` | Exported images stay beside the visible transcript surface, never in hidden runtime internals. |

### cmdr

| Setting | Required value | Constraint |
| --- | --- | --- |
| `leftRibbon` | `Memoria: capture note`, `Memoria: open Inbox`, `Memoria: resolve inbox card`. | The always-visible ribbon carries the live PI convenience actions; worker jobs live in Memoria Inspector. |
| `pageHeader` | `Memoria: capture note`, `Memoria: record exploration trace`. | Note-local actions sit beside the active note, where their active-note defaults are visible. |
| `showAddCommand` | `false` | The shipped toolbar is curated; ad hoc personal buttons can still be added from Commander settings. |

### modalforms

| Setting | Required value | Constraint |
| --- | --- | --- |
| `formDefinitions[].name` | `memoria-note-capture` | Generated by `scripts/gen-forms.py`; `tests/test_modalforms.py` fails if the committed plugin data drifts. |
| Note fields | `title`, `description`, required `body` | The form creates one unchecked PI-owned `note` Concept. |
| `globalNamespace` | `MF` | Keeps the plugin API available at the default namespace used by Modal Forms examples. |

### portals

Portals persists its shortcuts, hidden items, custom icons, and explorer
replacement settings to a vendored `data.json`. It is adopted as supplemental reach
chrome only; primary navigation stays in spaces and Bases views.

| Setting | Required value | Constraint |
| --- | --- | --- |
| `spaces[]` | Folder-root shortcuts for `inbox`, `catalog/sources`, `catalog/entities`, `knowledge/digests`, `knowledge/notes`, `knowledge/hubs`, `knowledge/projects`, and `capabilities`. | Portals is supplemental reach-only navigation; no tag portals and no space switching. |
| `replaceFileExplorer` | `true` | Portals replaces the visible explorer surface through its own setting while the core `file-explorer` plugin remains enabled as fallback. |
| `hiddenItems` | `{ "system": true, ".memoria": true }` | Runtime and generated infrastructure stay out of the PI-facing navigation pane. |
| `tagNotesFolderPath` | `system/_tag-notes` | Keeps the plugin's tag-note folder out of the user namespace. |
| `splitViewTabs` | `recent`, `bookmarks`, `context-notes`, `trash` | Drops journal/properties modules because Memoria does not use tag/daily-note navigation as primary structure. |

### memoria-inspector

| Setting | Required value | Constraint |
| --- | --- | --- |
| View type | `memoria-inspector-view` | Opens as a right-sidebar pane through the plugin command or ribbon icon. |
| Data sources | `system/logs/board-state.jsonl`, `system/logs/audit.jsonl`, `journal/*.jsonl` failed checks, checked `catalog/`/`knowledge/` Concepts, latest `system/metrics/lint-verdict-*.md`, latest `system/metrics/lane-*.md` | Read-only operational snapshots and checked graph browse data; no network request path or shell path. |
| Worker enqueue | `.memoria/queue/pending/*.json` operation jobs only | The plugin may enqueue `kind: operation` worker jobs for integrity checks, provenance checkpoints, source metadata checks, URL capture, digest compilation, note proposal, project argument analysis/Canvas rendering, projection regeneration, cascade rollback, `acknowledge-attention`, and `resolve-attention`; it never writes Concepts, journal files, projections, or `check_status` directly ([ADR-121](../adr/121-enqueue-only-obsidian-control-panel.md)). |
| Deep links | Board state, audit log, Knowledge graph, Maintenance drift watch, fleet health, and individual checked Concepts. | Uses native Obsidian note links for read navigation. |
| Refresh cadence | Manual refresh plus 60 s refresh while open | Keeps the inspector current without owning worker execution. |

### callout-manager

| Setting | Required value | Constraint |
| --- | --- | --- |
| `callouts.custom` | `["brief", "suggestions", "verification"]` | The three Memoria callout types must be registered as custom callouts. |
| `callouts.settings` | per-callout `color` (RGB triplet) + `icon` (Lucide id) | `brief` = `74, 144, 226` / `lucide-info`; `suggestions` = `123, 74, 226` / `lucide-list-plus`; `verification` = `226, 164, 74` / `lucide-shield-check`. Colors are stored as comma-separated RGB strings (not hex) — that is the format Callout Manager writes to `--callout-color`. |

---

## Related

- Plugin inventory: [Obsidian plugins](obsidian-plugins.md)
- Plugin data-file conventions: [Obsidian plugin data files](obsidian-plugin-data-files.md)
