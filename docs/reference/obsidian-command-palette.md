---
title: Obsidian command palette
parent: Reference
---

# Command palette

Every Obsidian command-palette entry Memoria registers (the `Memoria:` prefix). These are the **in-Obsidian UI** surface — invoked via `Cmd-P → Memoria: …` and registered by QuickAdd. For the per-profile Hermes CLI commands (`ingest`, `draft`, `lint`, board management, etc.) see [Hermes CLI](hermes-cli.md). For invocation patterns and hotkey discipline see [Command palette](../how-to-guides/using-obsidian/obsidian-command-palette.md).

> **v0.1 status.** This page is the **designed** palette surface. The shipped QuickAdd config wires **seven note-creation commands** — `Memoria: capture fleeting`, `write claim note`, `write MOC`, `write draft`, `scaffold canvas`, `scaffold code note`, `write project note` (each a QuickAdd **Template** choice that instantiates a raw-note template from `99-system/templates/`) — plus the `Memoria: capture from Zotero selection` **Macro** (a UserScript at `99-system/scripts/capture-from-zotero.js`: Better BibTeX CAYW → `hermes kanban create`). The remaining commands below (API-POST and ACP-pane choices) are added as the system fills in; see [Implementation status](../../project-files/plans/implementation-status.md).

Invoked via `Cmd-P → Memoria: …`. Registered by QuickAdd. Commander binds the top five to physical ribbon buttons.

---

## Capture

| Command | Output | Implementation |
| --- | --- | --- |
| `Memoria: capture fleeting` | New note in `10-inbox/01-fleeting/` with timestamp. | QuickAdd Template (fleeting note) |
| `Memoria: capture source from URL` | `intake:source` card on Librarian lane queue; Librarian picks it up within 60 s. | QuickAdd → POST Hermes API |
| `Memoria: capture from Zotero selection` | `intake:source` card on the Librarian lane, citekey pre-populated from the current Zotero selection. | QuickAdd Macro → Better BibTeX CAYW (`?selected=true`) → `hermes kanban create` (WSL on Windows) |

## Processing

| Command | Output | Implementation |
| --- | --- | --- |
| `Memoria: ask about this note` | Opens Socratic ACP pane (session-resident). No note writes. | QuickAdd → `open-chat-view` (agent: `memoria-socratic`; `autoMentionActiveNote: true`) |
| `Memoria: discuss this fleeting note` | `discuss` card + Socratic ACP pane. Fleeting → claim transition path. | QuickAdd composing two commands |
| `Memoria: write claim note` | New note from the claim template in `30-synthesis/01-claims/`; `maturity: seedling`. | QuickAdd Template (claim note) |
| `Memoria: write MOC` | New Map of Content in `30-synthesis/03-moc/`. | QuickAdd Template (moc) |
| `Memoria: write draft` | New draft note in a chosen `40-workbench/<project>/04-drafts/`. | QuickAdd Template (draft) |
| `Memoria: scaffold canvas` | New canvas companion note in a chosen `40-workbench/<project>/03-canvas/`. | QuickAdd Template (canvas) |
| `Memoria: scaffold code note` | New note from the code-note template in a chosen `40-workbench/<project>/06-code/` folder. | QuickAdd Template (code note) |
| `Memoria: write project note` | New project note in a chosen `40-workbench/<project>/`. | QuickAdd Template (project note) |

## Interactive retrieval (transient ACP — no file artifact, no card)

| Command | Profile | Output |
| --- | --- | --- |
| `Memoria: find related notes` | Mapper | Top 5–10 related notes by similarity, in chat. No file written. |
| `Memoria: counter-outline this section` | Writer (`counter-outline` skill) | 2–3 competing outlines in chat. No file written. |
| `Memoria: similarity-check this claim` | Verifier | Top 3 most-similar claim notes, in chat. No audit entry. |

## Project (card-based — produces file artifacts, Kanban-tracked)

| Command | Output | Assignee |
| --- | --- | --- |
| `Memoria: new project` | `40-workbench/<name>/` + `README.md` (`project-note`); Mapper scope card. | `memoria-mapper` |
| `Memoria: scope this project` | `corpus-map.md` in `40-workbench/<project>/01-map/`. | `memoria-mapper` |
| `Memoria: frame this section` | Outlines in `40-workbench/<project>/02-framing/`. | `memoria-writer` |
| `Memoria: verify this draft` | Verification report in `40-workbench/<project>/05-verification/`. | `memoria-verifier` |

## Maintenance

| Command | Output | Implementation |
| --- | --- | --- |
| `Memoria: approve all link suggestions` | Bulk-approves all `review_status: requested` cards. | QuickAdd → POST Hermes API (bulk approve) |
| `Memoria: lint this note` | Linter dry-run report on the active note. | QuickAdd → POST Hermes API (assignee: `memoria-linter`) |
| `Memoria: show lane status` | Opens the `daily-health.md` (Daily Health) dashboard in right sidebar. | QuickAdd → workspace pane |

## Lens-based reading (Socratic, parameterized)

Each lens is one command. Adding a lens = adding one QuickAdd entry.

| Command | Lens slug |
| --- | --- |
| `Memoria: read through Mamykina lens` | `mamykina-sensemaking` |
| `Memoria: read through Veinot equity lens` | `veinot-informational-justice` |
| `Memoria: read through Design Justice lens` | `design-justice-costanza-chock` |
| `Memoria: read through JITAI lens` | `jitai-receptivity-timing` |

---

## Related

- Hermes CLI commands (per-profile + board management): [Hermes CLI](hermes-cli.md)
- Policy on commands that target review-gated zones: [policy-mcp.md — Review-gated zones](policy-mcp.md)
- Invocation patterns and hotkey discipline: [Command palette](../how-to-guides/using-obsidian/obsidian-command-palette.md)
