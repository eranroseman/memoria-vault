---
title: Obsidian plugins
parent: Reference
---

# Obsidian plugins

Obsidian plugin inventory, install status, and load-bearing configuration for Memoria. For Zotero-side add-ons and the Zotero↔Obsidian connector comparison see [Zotero plugins](zotero-plugins.md). For the plugin model and reasoning see [explanation/obsidian/](../explanation/obsidian).

---

## Required Obsidian plugins (14)

Memoria breaks without these. The starter vault **ships all fourteen bundled and configured** in `.obsidian/plugins/` — thirteen third-party plugins plus the Memoria-authored Inspector, with no manual install. Enable community plugins (turn off Restricted mode) on first launch; see [Set up Obsidian](../how-to-guides/setup/set-up-obsidian.md).

The provenance lock for the bundled artifacts is
`src/.obsidian/plugin-provenance-lock.json`: it records each required plugin's
upstream repository, pinned local version, artifact SHA-256 digests, license assertion,
and local patch status. `python scripts/plugin_provenance_doctor.py` validates the
lock in the required gate: every enabled plugin is represented once, declared
artifacts exist and match their digests, and no undeclared executable artifact is
bundled. Updater automation remains deferred by
[ADR-74](../adr/74-pinned-obsidian-plugin-supply-chain.md).

| Plugin | ID (`.obsidian/plugins/<id>/`) | Purpose |
| --- | --- | --- |
| obsidian-local-rest-api | `obsidian-local-rest-api` | Exposes the vault to Hermes via its native MCP over verified loopback HTTPS (default port 27124). Required for the control plane. |
| agent-client | `agent-client` | ACP inside Obsidian — routes human conversations with Hermes through a chat pane. |
| dataview | `dataview` | Powers every dashboard. Without it the dashboard layer is non-functional. |
| templater-obsidian | `templater-obsidian` | Runs frontmatter scripts the Linter's safe-fix mode relies on. |
| quickadd | `quickadd` | Registers all `Memoria:` command palette entries. |
| cmdr | `cmdr` | Places the high-frequency `Memoria:` commands in the ribbon and page header so capture, delegation, and resolution do not require a palette round trip. |
| modalforms | `modalforms` | Provides structured in-Obsidian forms for capture and Project flows, including controlled `research_area`, `methodology`, and `scope_topics` fields sourced from `system/vocabulary.md`. |
| portals | `portals` | Replaces the raw left file tree with curated folder portals while retaining the core file explorer as fallback. |
| obsidian-citation-plugin | `obsidian-citation-plugin` | Inserts citations from `.memoria/memoria.bib`; creates paper notes from the configured template. (Zotero-side: see [Zotero plugins](zotero-plugins.md).) |
| memoria-inspector | `memoria-inspector` | Memoria-authored read-only sidebar pane for board counts, WIP depth, recent audit entries, and the Linter verdict band ([ADR-84](../adr/84-read-only-obsidian-inspector.md)). |
| callout-manager | `callout-manager` | Defines `[!brief]`, `[!suggestions]`, `[!verification]` callout types. |
| obsidian-git | `obsidian-git` | Git commits from inside Obsidian; the `post-commit` hook enqueues project-draft verification. |
| homepage | `homepage` | Opens `spaces/inbox` on startup as the deterministic landing surface. |
| buttons | `buttons` | Supports command-button snippets in note bodies. **Command-type buttons only** — the plugin's `template`/`text`/`calculate` button types write to notes outside the policy gate and are banned. Needs no `data.json` (defaults). |

---

## Recommended Obsidian plugins (9)

Install when the friction is felt. Not required for core function.

### Core seven

| Plugin | Purpose |
| --- | --- |
| smart-connections | Vector search across notes. |
| smart-lookup | Question-first semantic search (shares index with smart-connections). |
| omnisearch | Fast fuzzy full-text search (keyword counterpart to smart-*). |
| supercharged-links + style-settings | Tune the shipped CSS snippets for link colors and property state badges. |
| hover-editor | Preview wikilinked notes in a popup. |
| tag-wrangler | Bulk-rename, merge, and inspect tags. |
| pdf-plus | Deep-link from notes to specific PDF passages. |

### Narrower two (install for specific use cases)

| Plugin | When to install |
| --- | --- |
| obsidian-outliner | When nested-list editing becomes friction. |
| obsidian-excalidraw | When hand-drawn diagrams are needed (stored as `.excalidraw`). |

---

## Reference plugins (evaluated, not in the install set)

Documented but not in the install set. Obsidian-side evaluated alternatives. (Zotero-connector alternatives — zotlit, zotero-integration — are in [Zotero plugins](zotero-plugins.md).)

| Plugin | Status | Notes |
| --- | --- | --- |
| obsidian-kanban | Evaluated, not wired in | Cannot render `kanban.db` without an unadopted bridge. |
| Workspaces Plus | Evaluated, not shipped | Registers workspace-switching commands, but [ADR-81](../adr/81-persistent-gate-dashboards.md) keeps space switching in dashboard notes rather than saved workspace layouts. The core Workspaces plugin remains only as a reset layout. |
| obsidian-linter | **Incompatible — do not install** ([ADR-12](../adr/12-obsidian-linter-reference-only.md)) | Frontend formatter; second frontmatter authority that collides with the agent-owned `_proposed_classification` / `_enrichment` namespaces and writes outside the policy MCP audit trail. No config makes it safe. |

---

## Load-bearing settings per plugin

Settings with a fixed required value. All others are personal preference. See [explanation/obsidian/](../explanation/obsidian) for rationale.

### obsidian-local-rest-api

| Setting | Required value | Constraint |
| --- | --- | --- |
| HTTPS server | **on**, port `27124` | Serves the plugin's native MCP at `https://127.0.0.1:27124/mcp` — Hermes's vault path ([ADR-31](../adr/31-native-obsidian-mcp.md)). Loopback-only. Each profile's `OBSIDIAN_MCP_PORT` must match; use distinct ports per vault to run a sandbox + production at once. |
| HTTPS certificate | Exported PEM path in `OBSIDIAN_MCP_SSL_VERIFY` | Hermes passes this path to `mcp_servers.obsidian.ssl_verify`, keeping certificate verification enabled for the plugin's self-signed/local cert. |
| HTTP (insecure) server | off unless debugging | Plain HTTP is no longer the shipped Hermes path. Do not use it for normal profile runs. |
| `data.json` | **gitignored** | Contains API key secrets. Ships as `.example`; never commit the real file. |

### templater-obsidian

| Setting | Required value | Constraint |
| --- | --- | --- |
| `templates_folder` | `system/templates` | Must match vault schema convention. |
| `trigger_on_file_creation` | `false` | Auto-trigger races with agent writes. |
| `enable_system_commands` | `false` | Not required by Memoria; increases attack surface. |

### obsidian-citation-plugin

| Setting | Required value | Constraint |
| --- | --- | --- |
| BibTeX file (`citationExportPath`) | `.memoria/memoria.bib` | Single source of bib data; Better BibTeX auto-exports here. |
| Export format (`citationExportFormat`) | `biblatex` | Matches the Better BibTeX export. |
| Literature note folder (`literatureNoteFolder`) | `catalog/papers` | Notes must land in the canonical papers home ([ADR-47](../adr/47-type-first-category-folders.md)). |
| Note title (`literatureNoteTitleTemplate`) | `@{{citekey}}` | Filename keys off the stable citekey. |
| Template (`literatureNoteContentTemplate`) | **Inline, in `data.json`** | This plugin has no external-template-file setting — the full paper-note body is stored inline in `literatureNoteContentTemplate`. Kept **structurally aligned** with `system/templates/paper.md` (the human-facing copy): both follow the `paper` schema in `.memoria/schemas/types/paper.yaml`. They are not identical field-for-field (the citation copy carries Zotero `{{vars}}`); edit both together when the shared structure changes. |

### CSS snippets

| Snippet | Required value | Constraint |
| --- | --- | --- |
| `memoria-link-colors.css` | Enabled by default through the installer-maintained `enabledCssSnippets` entry in `appearance.json`; user can toggle after install | Colors wikilinks by folder/type and adds lifecycle accents when Supercharged Links exposes `data-link-*` attributes. |
| `memoria-property-badges.css` | Enabled by default through the installer-maintained `enabledCssSnippets` entry in `appearance.json`; user can toggle after install | Accents scan-critical Properties rows: `lifecycle`, `ingest_status`, `loudness`, and verification status. This is the visual layer for the property display order in [Frontmatter fields](frontmatter.md). |

### obsidian-git

| Setting | Required value | Constraint |
| --- | --- | --- |
| `commitMessage` / `autoCommitMessage` | `"vault: {{date}} {{numFiles}} files"` | `{{numFiles}}` makes abnormally large auto-commits visible. Set both keys so timed and manual commits match. |
| `autoBackupAfterFileChange` | `false` | Produces hundreds of commits per session when Hermes is writing; use scheduled commits instead. |
| `autoSaveInterval` | `30` | Scheduled commit every 30 min (the replacement for per-change backup). `0` disables it. |
| `pullBeforePush` | `true` | Required; prevents conflicts on multi-machine setups. |
| `autoPullOnBoot` | `true` | Required; catches stale vaults when switching machines. |
| `post-commit` hook | enabled | Load-bearing — enqueues Peer-reviewer verification for committed `projects/**/*.md` drafts. Source lives in `.githooks/`, installer copies it into `.git/hooks/`; it is not a `data.json` setting. Do not disable. |

The host running Obsidian or the sandboxed test runtime must have a real `git`
binary on `PATH`. Without it, obsidian-git, pre-commit schema validation,
verify-on-commit, rollback, and history are degraded; the installer now fails
clearly instead of silently skipping those paths.

> **Note:** obsidian-git has no `pullBeforeCommit` setting (earlier docs listed one in error). Divergence is caught by `autoPullOnBoot` + `pullBeforePush`. Push is governed by `disablePush` and `autoPushInterval` (`0` = no auto-push), not an `autoPush` boolean — the table below maps each deployment onto those two real keys.

**Push behavior by deployment** (the two keys that actually exist):

| Deployment | `disablePush` | `autoPushInterval` | Notes |
| --- | --- | --- | --- |
| `local-only` | `false` | `0` | Push manually for offsite-backup checkpoints. |
| `local-mesh` | `false` | `0` | Syncthing handles sync; Git is history only. |
| `obsidian-sync` | `false` | `0` | Obsidian Sync handles sync; Git is history only. |
| `always-on` (desktop) | `false` | `> 0` (e.g. `10`) | Desktop auto-pushes as backup; Syncthing handles sync. |
| `always-on` (VPS) | `true` | `0` | VPS must only pull, never push. |

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
| `defaultAgentId` | `memoria-copi` | The Co-PI is the only ACP chat partner (`test_acp_pane_is_copi_only`). |
| `customAgents[0].displayName` | `Memoria Co-PI` | The pane label uses the product-facing agent name, not the internal profile id. |
| `autoMentionActiveNote` | `true` | Active note is automatically attached as context. |
| `exportSettings.defaultFolder` | `system/exports` | Session exports are visible PI review material; never point them at hidden `.memoria/` internals. |
| `exportSettings.autoExportOnNewChat` / `autoExportOnCloseChat` | `true` / `true` | Pane sessions export automatically at session start and close. |
| `exportSettings.openFileAfterExport` | `false` | Exporting a session must not steal focus from the Co-PI conversation. |
| `exportSettings.imageCustomFolder` | `system/exports/assets` | Exported images stay beside the visible transcript surface, never in hidden runtime internals. |

### cmdr

| Setting | Required value | Constraint |
| --- | --- | --- |
| `leftRibbon` | Capture fleeting, capture from Zotero selection, capture source from URL, delegate task, resolve inbox card. | The always-visible ribbon carries the commands needed for the capture → triage loop; space switching lives in dashboard nav rows. |
| `pageHeader` | Create linked claim note, write claim note, extract claims, link claim. | Note-local actions sit beside the active note, where their active-note defaults are visible. |
| `showAddCommand` | `false` | The shipped toolbar is curated; ad hoc personal buttons can still be added from Commander settings. |

### modalforms

| Setting | Required value | Constraint |
| --- | --- | --- |
| `formDefinitions[].name` | `memoria-source-capture`, `memoria-project-start` | Structured source capture and the Project start on-ramp are active PI-facing Modal Forms flows. |
| `research_area` / `methodology` / `scope_topics` fields | Fixed multiselect options matching `system/vocabulary.md`. | `system/vocabulary.md` is the source of truth; `tests/test_modalforms.py` fails if the committed form options drift. |
| `globalNamespace` | `MF` | Keeps the plugin API available at the default namespace used by Modal Forms examples. |

### portals

Portals persists its folder spaces, hidden items, custom icons, and file-explorer
replacement settings to a vendored `data.json`. It is adopted as navigation chrome
only, not as a query layer or space switcher.

| Setting | Required value | Constraint |
| --- | --- | --- |
| `spaces[]` | Folder portals for `inbox`, `catalog`, `notes/sources`, `notes/claims`, `notes/hubs`, and `projects`. | Portals is reach-only folder navigation; no tag portals and no space switching. |
| `replaceFileExplorer` | `true` | Portals replaces the visible explorer surface through its own setting while the core `file-explorer` plugin remains enabled as fallback. |
| `hiddenItems` | `{ "system": true, ".memoria": true }` | Runtime and generated infrastructure stay out of the PI-facing navigation pane. |
| `tagNotesFolderPath` | `system/_tag-notes` | Keeps the plugin's tag-note folder out of the user namespace. |
| `splitViewTabs` | `recent`, `bookmarks`, `context-notes`, `trash` | Drops journal/properties modules because Memoria does not use tag/daily-note navigation as primary structure. |

### memoria-inspector

| Setting | Required value | Constraint |
| --- | --- | --- |
| View type | `memoria-inspector-view` | Opens as a right-sidebar pane through the plugin command or ribbon icon. |
| Data sources | `system/logs/board-state.jsonl`, `system/logs/audit.jsonl`, latest `system/metrics/lint-verdict-*.md` | Read-only operational snapshot only; the plugin has no vault write path, network request path, or shell path. |
| Refresh cadence | Manual refresh plus 60 s refresh while open | Keeps the inspector current without becoming an action surface. |

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
