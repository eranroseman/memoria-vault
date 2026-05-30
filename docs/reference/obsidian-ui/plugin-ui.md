---
topic: obsidian-ui
---

# Other plugin UI

The named components — [dashboards](dashboards.md), [callouts](../../explanation/obsidian-ui/callouts.md), [command palette](../command-catalog.md), [status line](status-line.md), [Home](../../explanation/obsidian-ui/home.md), the [Agent Client pane](../plugins/agent-client.md) — are each *powered by* a specific plugin. This page is the rest: the **additional UI affordances** the required and recommended plugins add to the editor, search, reading, and visual layers that aren't one of those components.

Scope: **required + recommended only.** [`reference/`](../plugins/README.md) plugins (obsidian-kanban, ZotLit, zotero-integration, obsidian-linter) are documented but **not installed**, so they contribute no UI here. One required plugin — `obsidian-local-rest-api` — is **headless** (the vault-access bridge that Hermes reads from, port 27124, HTTPS by default) and renders nothing.

## Plugins that power the named components

These aren't "other" UI — they're the engines under the components documented elsewhere. Listed so the wiring is explicit:

| Component | Powered by | Tier |
| --- | --- | --- |
| [Dashboards](dashboards.md), [Status line](status-line.md), [Home](../../explanation/obsidian-ui/home.md) queries | `dataview` | required |
| [Callouts](../../explanation/obsidian-ui/callouts.md) (`[!brief]` / `[!suggestions]` / `[!verification]`) | `callout-manager` | required |
| [Command palette](../command-catalog.md) (`Memoria:` actions) | `quickadd` | required |
| [Agent Client pane](../plugins/agent-client.md) | `agent-client` | required |
| [Home](../../explanation/obsidian-ui/home.md) auto-open | `obsidian-homepage` | recommended |

## Additional UI affordances

Everything the other plugins add, grouped by the kind of interaction. All recommended-tier entries are quality-of-life — Memoria works without them; install when the friction is felt.

### Navigation & linking

| Plugin | Tier | What it adds |
| --- | --- | --- |
| `supercharged-links` (+ `obsidian-style-settings`) | rec | Colors internal links by note `type`, so a link to a paper-note looks different from one to a claim-note — type becomes visible at a glance in editor and preview. |
| `hover-editor` | rec | A hover popover that previews — and can edit — a wikilinked note without leaving the current one. |
| `cmdr` (Commander) | rec | Binds frequently-used `Memoria:` commands to the ribbon, status bar, or in-editor buttons — extends the command palette's reach to clickable surfaces. |
| `tag-wrangler` | rec | Right-click a tag in the tag pane to rename, merge, or search it vault-wide — bulk tag hygiene, valuable given Memoria's controlled-vocabulary discipline. |

### Search & discovery

| Plugin | Tier | What it adds |
| --- | --- | --- |
| `omnisearch` | rec | A fuzzy **full-text** search modal with ranked results and in-note match highlighting — the keyword counterpart to the semantic pair below. |
| `smart-connections` | rec | A sidebar pane listing notes **semantically related** to the active note (vector search). Note-anchored. |
| `smart-lookup` | rec | **Question-first** semantic search — type a question, get relevant notes. Query-anchored; shares Smart Connections' index. |

### Reading & citation

| Plugin | Tier | What it adds |
| --- | --- | --- |
| `pdf-plus` (PDF++) | rec | An enhanced PDF viewer: deep-link and copy links to a **specific passage**, annotate, and see backlinks from the PDF into notes — passage-level precision for claim-level citation. |
| `obsidian-citation-plugin` | req | An **Insert-Citation** search modal over the Better BibTeX export, and a command to create a paper-note from the configured template — Memoria's primary Zotero-to-vault note path. |

### Editing & authoring

| Plugin | Tier | What it adds |
| --- | --- | --- |
| `obsidian-outliner` | rec | Outline-aware list editing — fold/unfold, move items with shortcuts, zoom into a sub-list, visual indent guides. |
| `obsidian-excalidraw` | rec | A hand-drawn **diagram canvas** (`.excalidraw`) embeddable in notes — for argument sketches that aren't an Obsidian Canvas. |
| `templater-obsidian` | req | Template insertion — the scripts the Linter's safe-and-unambiguous fixes and new-note templates rely on; surfaces as an "Insert template" action. |

### Visual & theme

| Plugin | Tier | What it adds |
| --- | --- | --- |
| `obsidian-style-settings` | rec | A settings panel exposing CSS-snippet / theme variables as toggles and sliders — tune the look (accent color, spacing) without editing CSS. The GUI behind the [design system](../templates/design-system.md). |
| `callout-manager` | req | Beyond defining Memoria's callout types, it provides the UI to style and manage callouts. |

### State & sync

| Plugin | Tier | What it adds |
| --- | --- | --- |
| `obsidian-git` | req | A **Source Control** sidebar (stage / commit / diff) and a **status-bar** sync indicator — the visible surface of the git layer the [Verify](../../how-to/workflows/downstream/verify.md) / [Revise](../../how-to/workflows/downstream/revise.md) hooks ride on. |

## Design notes

- **Affordances, not chrome.** Every entry adds a *capability* (a search, a popover, a colored link), not decoration. That restraint is the [ui-discipline](../../explanation/obsidian-ui/ui-discipline.md) rule applied to plugins: one accent color, hidden chrome, no visual noise.
- **Headless ≠ UI.** `obsidian-local-rest-api` is required but renders nothing — it's the vault-access bridge that Hermes reads from (port 27124, HTTPS by default), not a surface. Don't look for it in the UI.
- **Reference plugins are absent by design.** If you're looking for Kanban-board rendering or ZotLit's import UI, they're [`reference/`](../plugins/README.md) — evaluated, not installed (the Hermes board renders via Dataview, not obsidian-kanban).
- **The catalog of *which plugins exist and how to configure them* lives in [obsidian-plugins/](../plugins/README.md).** This page is the *UI-facing* view of that set; that folder is the *install-and-config* view.
