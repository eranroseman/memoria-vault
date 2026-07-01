---
title: Obsidian plugins
parent: Obsidian and Zotero
grand_parent: Reference
---

# Obsidian plugins

Obsidian plugin inventory, install status, and load-bearing configuration for Memoria. For Zotero-side add-ons and the Zotero↔Obsidian connector comparison see [Zotero plugins](zotero-plugins.md). For the plugin model and reasoning see [explanation/obsidian/](../explanation/obsidian).

---

## Required Obsidian plugins (12)

Memoria breaks without these. The starter vault ships all twelve bundled and configured in `.obsidian/plugins/` — eleven third-party plugins plus the Memoria-authored Inspector. First-launch steps live in [Set up Obsidian](../how-to-guides/setup/set-up-obsidian.md).

The provenance lock for the bundled artifacts is
`vault-template/.obsidian/plugin-provenance-lock.json`: it records each required plugin's
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
| dataview | `dataview` | Powers JSONL-backed system dashboards and inline rail counts. Bases own note-frontmatter views. |
| quickadd | `quickadd` | Registers the small alpha.11 `Memoria:` PI-convenience command set. |
| cmdr | `cmdr` | Places the live capture, Inbox, resolve, and exploration-trace commands in the ribbon and page header. |
| modalforms | `modalforms` | Provides the `memoria-note-capture` form from committed plugin data. |
| portals | `portals` | The curated file browser for the left sidebar — replaces the core file explorer with alpha.11 folder homes and hides `system/`/`.memoria/`. The navigation rail and Bases are the primary navigation surface; Portals is for browsing the underlying notes. |
| obsidian-citation-plugin | `obsidian-citation-plugin` | Inserts citations from generated `references.bib`; accidental literature-note output is redirected to ignored staging, not live Concepts. (Zotero-side: see [Zotero plugins](zotero-plugins.md).) |
| memoria-inspector | `memoria-inspector` | Memoria-authored read-only sidebar pane for board counts, checked Concept graph browsing, recent audit entries, integrity flags, and the Linter verdict band ([ADR-122](../adr/122-sqlite-working-state-boundary.md)). |
| callout-manager | `callout-manager` | Defines `[!brief]`, `[!suggestions]`, `[!verification]` callout types. |
| obsidian-git | `obsidian-git` | Manual Git history from inside Obsidian. Automatic commits and pushes are disabled; the worker remains the machine write path. |
| buttons | `buttons` | Supports command-button snippets in note bodies. **Command-type buttons only** — the plugin's `template`/`text`/`calculate` button types write to notes outside the policy gate and are banned. Needs no `data.json` (defaults). |

---

## Recommended Obsidian plugin rows (9)

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
| Workspaces Plus | Evaluated, not shipped | Registers workspace-switching commands, but the navigator rail keeps space switching out of saved workspace layouts. The core Workspaces plugin remains only as a reset layout. |
| templater-obsidian | Evaluated, not shipped | QuickAdd and Modal Forms own Memoria capture flows. Templater's arbitrary template execution is not part of the checked worker-write boundary. |
| obsidian-linter | **Incompatible — do not install** ([ADR-12](../adr/12-obsidian-linter-reference-only.md)) | Frontend formatter; second frontmatter authority that collides with the agent-owned `_proposed_classification` / `_enrichment` namespaces and writes outside the policy MCP audit trail. No config makes it safe. |

---

## Load-bearing settings

The required per-plugin settings live in [Obsidian plugin settings](obsidian-plugin-settings.md).

## `data.json` conventions

Committed, generated, example, and secret-bearing plugin data-file rules live in [Obsidian plugin data files](obsidian-plugin-data-files.md).

## Related

- How a new user enables these plugins: [Quickstart](../how-to-guides/setup/quickstart.md)
