---
topic: plugins
---

# Obsidian plugins — configuration reference

Memoria depends on a small set of Obsidian community plugins. Each plugin's configuration lives in its own `data.json` under `vault/.obsidian/plugins/<plugin-id>/data.json`. The configs are human-edited but version-controlled — the vault ships with reviewed defaults and the human changes them deliberately, not by exploring the plugin's settings UI.

This folder documents which plugins Memoria uses, what their `data.json` should contain, and the **load-bearing settings the human should not change** without understanding the consequences. The human-facing summary lives in `00-meta/04-reference/obsidian-config.md` (vault skeleton note); this folder is the engineering source it points at.

For *why* these plugins, the priority/install-order reasoning, and what the required/recommended/reference distinction means as a concept, see [the plugin model](../../explanation/obsidian-plugins/README.md).

## The plugin tables

The three tables below are the lookup of which plugin does what. The on-disk folders are three — `required/`, `recommended/`, `reference/`.

### Required (8) — Memoria breaks without these

| Plugin | Purpose |
| --- | --- |
| [obsidian-local-rest-api](obsidian-local-rest-api.md) | Exposes the vault to Hermes via HTTPS (port 27124; HTTP is off by default). Required for the [control plane](../../explanation/architecture/control-plane.md). **Its `data.json` contains secrets — gitignore it.** |
| [agent-client](agent-client.md) | Implements ACP (Agent Client Protocol) inside Obsidian. Routes human conversations with Hermes (and optionally Claude Code, Codex, Gemini CLI, Kilocode) through a chat pane attached to the active note. Makes the Socratic profile invocable from a reading session. |
| [dataview](dataview.md) | Powers every dashboard. Without it, the dashboard layer in [obsidian-ui/README.md](../../explanation/obsidian-ui/README.md) is non-functional. |
| [templater-obsidian](templater-obsidian.md) | Runs the safe-and-unambiguous frontmatter scripts the Memoria Linter relies on (see [linter.md](../../explanation/profiles/linter.md#implementing-safe-and-unambiguous-fixes-via-templater)). |
| [quickadd](quickadd.md) | Registers Memoria's command palette entries (see [command-catalog.md](../command-catalog.md)). |
| [obsidian-citation-plugin](obsidian-citation-plugin.md) | Inserts citations from the BibTeX/BibLaTeX file Better BibTeX exports, and creates paper notes from a configured template. Memoria's primary Zotero-to-vault path for note creation today. |
| [callout-manager](callout-manager.md) | Defines the `[!brief]`, `[!suggestions]`, and `[!verification]` callout types used by the [inline agent callouts](../../explanation/obsidian-ui/callouts.md) (a first-class Obsidian-UI component). |
| [obsidian-git](obsidian-git.md) | Drives git commits from inside Obsidian — and git is load-bearing: the `post-commit` hook fires the [Verify](../../how-to/workflows/downstream/verify.md) / [Revise](../../how-to/workflows/downstream/revise.md) workflows, and git is the reversibility, audit, and history layer on every deployment. (Its `autoPush`/backup *settings* are deployment-conditional.) |

### Recommended (11) — install when the friction is felt

The **core eight** — most humans want these early:

| Plugin | Purpose |
| --- | --- |
| [obsidian-homepage](obsidian-homepage.md) | Opens the `Home.md` front door on startup (deterministic landing) + a home command/ribbon. View-only — writes nothing; see [ADR-25](../../project/decisions/25-homepage-front-door.md). |
| [smart-connections](../../explanation/obsidian-plugins/smart-connections.md) (+ `markdb-connect`) | Vector search across notes — **`smart-connections` is the Obsidian plugin**. The paired `markdb-connect` is a *Zotero* add-on (installed in Zotero, not under `.obsidian/plugins/`) that tags Zotero items having vault notes; see the linked file. |
| [smart-lookup](../../explanation/obsidian-plugins/smart-lookup.md) | Question-first semantic search (type a question, get relevant notes). Companion to Smart Connections — shares its index; the two are query-anchored vs. note-anchored. |
| [omnisearch](../../explanation/obsidian-plugins/omnisearch.md) | Fast fuzzy **full-text** search — the keyword counterpart to the semantic Smart\* pair. Memoria doesn't depend on it; settings are workflow-personal. |
| [supercharged-links + obsidian-style-settings](supercharged-links.md) | Color-code internal links by note `type` so a link to a paper-note looks different from a link to a claim-note. |
| [hover-editor](hover-editor.md) | Preview wikilinked notes in a popup without leaving the current note. |
| [tag-wrangler](../../explanation/obsidian-plugins/tag-wrangler.md) | Bulk-rename, merge, and inspect tags across the vault. Useful given Memoria's controlled-vocabulary discipline. |
| [pdf-plus (PDF++)](pdf-plus.md) | Deep-linking from notes to specific PDF passages — passage-level precision for claim-level citation. Citekey-level citation works without it, so it's a high-value add, not a hard dependency. |

The **narrower three** — also `recommended/`, but install only when the specific use case lands:

| Plugin | Purpose |
| --- | --- |
| [cmdr (Commander)](../../explanation/obsidian-plugins/cmdr.md) | Bind frequently-used Memoria commands to physical buttons in the ribbon or status bar. |
| [obsidian-outliner](../../explanation/obsidian-plugins/obsidian-outliner.md) | Outline-aware editing for nested lists. |
| [obsidian-excalidraw](../../explanation/obsidian-plugins/obsidian-excalidraw.md) | Hand-drawn diagrams stored as `.excalidraw` files. |

### Reference (4) — held knowledge, not in the install set

Plugins Memoria documents but does **not** install or recommend for daily use — evaluated alternatives and future-migration targets kept on record so the reasoning isn't lost.

| Plugin | Purpose |
| --- | --- |
| [zotlit](../../project/evaluated-alternatives/zotlit.md) | Reads Zotero's SQLite database directly — faster for bulk imports. **Held as a future migration target, not currently used.** |
| [zotero-integration](../../project/evaluated-alternatives/zotero-integration.md) | Imports Zotero items and annotations via Zotero's local HTTP API (color-coded highlights, Nunjucks templates). **Not in use** — Memoria annotates in Obsidian, not Zotero; held as the alternative if that flips. |
| [obsidian-kanban](../../project/evaluated-alternatives/obsidian-kanban.md) | Renders a markdown Kanban file, but **can't render the Hermes board** (`kanban.db`, shown via Dataview) without an unadopted bridge — evaluated, not wired in. |
| [obsidian-linter](../../project/evaluated-alternatives/obsidian-linter.md) | Frontend Markdown formatter — deterministic, but writes on-save in the GUI, outside the policy MCP audit trail, and would be a second frontmatter authority. The Memoria Linter + markdownlint own this. **HTML-comment-strip footgun.** Demoted from `recommended/`; see [ADR-24](../../project/decisions/24-obsidian-linter-reference-only.md). |

Visual-style discipline — restraint about how the vault *looks*, independent of any specific plugin — lives in [obsidian-ui/ui-discipline.md](../../explanation/obsidian-ui/ui-discipline.md).

## The `data.json` convention

Each plugin's settings live in `.obsidian/plugins/<plugin-id>/data.json`, shipped ready-to-use in the starter vault (or as a `.example` / `.TODO` variant where per-human setup is needed). **The full story — what each suffix means, what ships, and how drift is audited — is owned by [`plugin-configs-lifecycle.md`](../../explanation/obsidian-plugins/plugin-configs-lifecycle.md).** The index-level rules:

- **Commit `data.json` by default** (configuration, not state) — **except any file containing secrets, which must be gitignored.** Today that's exactly one plugin, [obsidian-local-rest-api](obsidian-local-rest-api.md) (it ships a `.example`); audit a new plugin's `data.json` for `apiKey` / `token` / `crypto` / `privateKey` fields before its first commit and gitignore it if any appear.
- **Never edit `data.json` while Obsidian is running** — Obsidian rewrites it on settings change, so external edits race. Quit, edit, restart.

### `.gitignore` snippet for known-secret plugins

```text
# Plugins whose data.json contains secrets — regenerated on first launch
vault/.obsidian/plugins/obsidian-local-rest-api/data.json
```

## Operational notes

- **Disabling a required plugin breaks Memoria.** The control plane, dashboards, and templates all assume their plugin is installed and configured. If a plugin update breaks something, downgrade rather than disable.
- **Plugin updates can change `data.json` schema.** When updating a plugin version, diff the new `data.json` against the committed version before accepting changes. Schema migrations have caused silent setting loss in past Obsidian releases.
- **`.obsidian/plugins/*/main.js` is plugin code, not config.** Don't commit it (it changes on every update and bloats Git history). The `.gitignore` should include `.obsidian/plugins/**/main.js` and `.obsidian/plugins/**/styles.css` while keeping `data.json` and `manifest.json`.

## When this doc is wrong

Plugin behavior changes across versions. If a setting documented here doesn't exist in the installed version, the plugin has either added it (the doc is behind) or removed it (the doc is stale). Update the doc the same session the mismatch is noticed — see the same discipline in [failure-modes.md](../../how-to/operations/failure-modes.md).
