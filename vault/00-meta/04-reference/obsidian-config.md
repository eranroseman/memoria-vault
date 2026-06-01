# Obsidian configuration

Which Obsidian community plugins Memoria uses and the load-bearing settings you shouldn't change. Companion to [Obsidian plugins reference](https://eranroseman.github.io/memoria-vault/reference/obsidian-plugins/).

## Required plugins

| Plugin | Purpose | Load-bearing setting |
| --- | --- | --- |
| **Templater** | Note templates | `templates_folder: "00-meta/03-templates"` |
| **Dataview** | Dashboard queries | `enableJs: true` (required for dataviewjs blocks) |
| **QuickAdd** | Command-palette actions | Custom QuickAdd entries register each `Memoria: <verb>` command |
| **agent-client** | ACP integration with Hermes | `defaultAgentId: "memoria-socratic"`; `autoAllowPermissions: false` |
| **Local REST API** | Webhook entry point for Hermes | Token in `data.json`; tightly scoped |
| **PDF++** | Paper-note deep linking to PDF pages | Used in the paper-note workflow |
| **Citation plugin** | Reads `library.bib` | `citationExportPath: ".memoria/library.bib"` |
| **callout-manager** | Inline-surface callouts (`[!brief]`, `[!suggestions]`, `[!verification]`) | Memoria's three custom callouts |

## Recommended plugins

| Plugin | Purpose |
| --- | --- |
| **Tag Wrangler** | Bulk-rename / merge controlled vocabularies |
| **Smart Connections** | Human-side, in-Obsidian semantic search ("what notes do I have on X?"). *Not* wired into the Mapper — the agent's retrieval substrate is `qmd`; the two run separately. |
| **Obsidian Linter** | Note formatting consistency |
| **Hover Editor** | Preview wikilinks without opening |
| **Supercharged Links** | Visual cues on link colors by note type |

## Optional plugins

| Plugin | When to add |
| --- | --- |
| **Commander** | When you want top palette commands on physical buttons |
| **Obsidian Kanban** | When you want a board view of in-flight cards (Memoria runs the actual board state in JSONL) |
| **Obsidian Excalidraw** | When you want diagrams in canvas notes |
| **Obsidian Git** | If you prefer in-Obsidian Git operations over CLI |
| **zotlit** | Alternative Zotero integration; complements the citation plugin |

## What not to change

- **Don't change the template path** — Templater hard-references `00-meta/03-templates`
- **Don't enable `autoAllowPermissions: true`** in agent-client — bypasses policy MCP review at the ACP layer
- **Don't unhide `.memoria/` or `.obsidian/`** — both are intentionally dot-prefixed
- **Don't disable Dataview's `enableJs`** — many dashboards depend on dataviewjs

## Workspace conventions

- **One mode per workspace.** Human (`Cmd-1`), Reading & Processing (`Cmd-2`), Drafting (`Cmd-3`)
- **Three workspaces is the working set.** Resist proliferation
- **Pin [[../index]]** in the file explorer

## Hotkey conventions (Memoria-specific)

- `Ctrl+Shift+1/2/3/4` — profile-switching for the ACP chat (Socratic / Mapper / Writer / Verifier)
- `Cmd-P → "M"` — filter palette to Memoria commands only

---

**For depth:** [Obsidian plugins reference](https://eranroseman.github.io/memoria-vault/reference/obsidian-plugins/) — per-plugin design rationale and full configuration.
