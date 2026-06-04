---
title: Obsidian command palette
parent: Reference
---

# Command palette

The `Memoria:` command-palette surface — the **in-Obsidian UI** for capture, note creation, and (as they ship) agent tasks. Invoked via `Cmd-P → Memoria: …` and registered by QuickAdd. For the per-profile Hermes CLI commands (`ingest`, `draft`, `lint`, board management) see [Hermes CLI](hermes-cli.md); for invocation patterns and hotkey discipline see [Command palette](../how-to-guides/using-obsidian/obsidian-command-palette.md).

> **v0.1 status — read the Status column.** This page is the **designed** palette surface; not all of it is wired yet. Each row is tagged:
>
> - **✓ wired** — registered today (a QuickAdd Template or Macro). These work.
> - **`[deferred]`** — designed, not yet wired. Where the task is conversational, the **agent-client (ACP) pane** is the working path *today* (open *Agent Client: Open chat view*, switch to the named profile — the active note auto-attaches); where it produces a vault artifact, use the **[Hermes CLI](hermes-cli.md)** until the command lands.
>
> Wired today: seven QuickAdd **Templates** (`capture fleeting`, `write claim note`, `write MOC`, `write draft`, `scaffold canvas`, `scaffold code note`, `write project note`) and three **Macros** (`capture from Zotero selection`, `capture source from URL`, `lint this note` — each a QuickAdd UserScript → `hermes kanban create`). **Confirmed live:** `lint this note` runs the Linter end-to-end; `capture source from URL` creates the card but the Librarian **blocks bare/proxied URLs** pending DOI resolution (see its row). The rest land as the system fills in; see [Implementation status](../../project-files/plans/implementation-status.md).

Commander binds the top five to physical ribbon buttons.

---

## Capture

| Status | Command | Output | Implementation |
| --- | --- | --- | --- |
| ✓ | `Memoria: capture fleeting` | New note in `10-inbox/01-fleeting/` with timestamp. | QuickAdd Template (fleeting note) |
| ✓ | `Memoria: capture from Zotero selection` | `intake:source` card on the Librarian lane, citekey pre-populated from the current Zotero selection. | QuickAdd Macro → Better BibTeX CAYW (`?selected=true`) → `hermes kanban create` (WSL on Windows) |
| ✓ macro / ingest `[partial]` | `Memoria: capture source from URL` | `intake:source` card on the Librarian lane with the pasted URL. **The macro is wired**, but the Librarian's pipeline is citekey/`.bib`-driven: a URL **with a resolvable DOI** can be ingested, while a **bare/library-proxied URL, a repo, or a webpage blocks** asking for the DOI or citekey (full URL→metadata resolution is [deferred]). | QuickAdd Macro → prompt for URL → `hermes kanban create` |

## Processing

| Status | Command | Output | Implementation |
| --- | --- | --- | --- |
| `[deferred]` | `Memoria: ask about this note` | Opens the Socratic ACP pane (session-resident). No note writes. **Today:** open *Agent Client: Open chat view*, switch to Socratic — the active note auto-attaches. | QuickAdd → `open-chat-view` (agent: `memoria-socratic`; `autoMentionActiveNote: true`) |
| `[deferred]` | `Memoria: discuss this fleeting note` | `discuss` card + Socratic ACP pane. Fleeting → claim transition path. | QuickAdd composing two commands |
| ✓ | `Memoria: write claim note` | New note from the claim template in `30-synthesis/01-claims/`; `maturity: seedling`. | QuickAdd Template (claim note) |
| ✓ | `Memoria: write MOC` | New Map of Content in `30-synthesis/03-moc/`. | QuickAdd Template (moc) |
| ✓ | `Memoria: write draft` | New draft note in a chosen `40-workbench/<project>/04-drafts/`. | QuickAdd Template (draft) |
| ✓ | `Memoria: scaffold canvas` | New canvas companion note in a chosen `40-workbench/<project>/03-canvas/`. | QuickAdd Template (canvas) |
| ✓ | `Memoria: scaffold code note` | New note from the code-note template in a chosen `40-workbench/<project>/06-code/` folder. | QuickAdd Template (code note) |
| ✓ | `Memoria: write project note` | New project note in a chosen `40-workbench/<project>/`. | QuickAdd Template (project note) |

## Interactive retrieval (transient ACP — no file artifact, no card)

Each is conversational. **Today, use the ACP pane** (open the named profile and ask) — the one-shot palette command is `[deferred]`.

| Status | Command | Profile | Output |
| --- | --- | --- | --- |
| `[deferred]` | `Memoria: find related notes` | Mapper | Top 5–10 related notes by similarity, in chat. No file written. |
| `[deferred]` | `Memoria: counter-outline this section` | Writer (`counter-outline` skill) | 2–3 competing outlines in chat. No file written. |
| `[deferred]` | `Memoria: similarity-check this claim` | Verifier | Top 3 most-similar claim notes, in chat. No audit entry. |

## Project (card-based — produces file artifacts, Kanban-tracked)

`[deferred]` — until wired, dispatch these via the [Hermes CLI](hermes-cli.md) (`hermes -p <profile> chat -s <skill>`).

| Status | Command | Output | Assignee |
| --- | --- | --- | --- |
| `[deferred]` | `Memoria: new project` | `40-workbench/<name>/` + `README.md` (`project-note`); Mapper scope card. | `memoria-mapper` |
| `[deferred]` | `Memoria: scope this project` | `corpus-map.md` in `40-workbench/<project>/01-map/`. | `memoria-mapper` |
| `[deferred]` | `Memoria: frame this section` | Outlines in `40-workbench/<project>/02-framing/`. | `memoria-writer` |
| `[deferred]` | `Memoria: verify this draft` | Verification report in `40-workbench/<project>/05-verification/`. | `memoria-verifier` |

## Maintenance

| Status | Command | Output | Implementation |
| --- | --- | --- | --- |
| `[deferred]` | `Memoria: approve all link suggestions` | Bulk-approves all `review_status: requested` cards. | QuickAdd → POST Hermes API (bulk approve) |
| ✓ | `Memoria: lint this note` | Linter card for the active note (findings reported on the card). | QuickAdd Macro → `hermes kanban create` (assignee: `memoria-linter`) |
| `[deferred]` | `Memoria: show lane status` | Opens the `daily-health.md` (Daily Health) dashboard in right sidebar. | QuickAdd → workspace pane |

## Lens-based reading (Socratic, parameterized)

`[deferred]` — **today, use the Socratic ACP pane** and ask it to read through the named lens. Each lens is designed as one command; adding a lens = adding one QuickAdd entry.

| Status | Command | Lens slug |
| --- | --- | --- |
| `[deferred]` | `Memoria: read through Mamykina lens` | `mamykina-sensemaking` |
| `[deferred]` | `Memoria: read through Veinot equity lens` | `veinot-informational-justice` |
| `[deferred]` | `Memoria: read through Design Justice lens` | `design-justice-costanza-chock` |
| `[deferred]` | `Memoria: read through JITAI lens` | `jitai-receptivity-timing` |

---

## Related

- Hermes CLI commands (per-profile + board management): [Hermes CLI](hermes-cli.md)
- Policy on commands that target review-gated zones: [policy-mcp.md — Review-gated zones](policy-mcp.md)
- Invocation patterns and hotkey discipline: [Command palette](../how-to-guides/using-obsidian/obsidian-command-palette.md)
