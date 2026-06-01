# Command palette

Every Obsidian command-palette entry Memoria registers (the `Memoria:` prefix). These are the **in-Obsidian UI** surface — invoked via `Cmd-P → Memoria: …` and registered by QuickAdd. For the per-profile Hermes CLI commands (`ingest`, `draft`, `lint`, board management, etc.) see [hermes-cli.md](hermes-cli.md). For invocation patterns and hotkey discipline see [how-to-guides/command-palette.md](../how-to-guides/interface/command-palette.md).

> **v0.1 status.** This page is the **designed** palette surface. The shipped QuickAdd config wires **three** so far — `Memoria: capture fleeting`, `Memoria: write claim note`, `Memoria: scaffold code note` (all Templater-backed). The rest (API-POST, ACP-pane, and macro choices) are added as the system fills in; see [implementation-status.md](../../project-files/operations/implementation-status.md).

Invoked via `Cmd-P → Memoria: …`. Registered by QuickAdd. Commander binds the top five to physical ribbon buttons.

---

## Capture

| Command | Output | Implementation |
| --- | --- | --- |
| `Memoria: capture fleeting` | New note in `10-inbox/01-fleeting/` with timestamp. | QuickAdd → Templater (fleeting template) |
| `Memoria: capture source from URL` | `intake:source` card on Librarian lane queue; Librarian picks it up within 60 s. | QuickAdd → POST Hermes API |
| `Memoria: capture from Zotero selection` | `intake:source` card with citekey pre-populated from current Zotero selection. | QuickAdd → Zotero local API → POST Hermes API |

## Processing

| Command | Output | Implementation |
| --- | --- | --- |
| `Memoria: ask about this note` | Opens Socratic ACP pane (session-resident). No note writes. | QuickAdd → `open-chat-view` (agent: `memoria-socratic`; `autoMentionActiveNote: true`) |
| `Memoria: discuss this fleeting note` | `discuss` card + Socratic ACP pane. Fleeting → claim transition path. | QuickAdd composing two commands |
| `Memoria: write claim note` | New note from claim template in `30-synthesis/01-claims/`; `maturity: seedling`. | QuickAdd → Templater (claim template) |
| `Memoria: scaffold code note` | New note from the code-note template in a chosen `40-workbench/<project>/06-code/` folder. | QuickAdd → Templater (code-note template) |

## Interactive retrieval (transient ACP — no file artifact, no card)

| Command | Profile | Output |
| --- | --- | --- |
| `Memoria: find related notes` | Mapper | Top 5–10 related notes by similarity, in chat. No file written. |
| `Memoria: counter-outline this section` | Writer (`counter-outline` skill) | 2–3 competing outlines in chat. No file written. |
| `Memoria: similarity-check this claim` | Verifier | Top 3 most-similar claim notes, in chat. No audit entry. |

## Project (card-based — produces file artifacts, Kanban-tracked)

| Command | Output | Assignee |
| --- | --- | --- |
| `Memoria: new project` | `40-workbench/<name>/` + `brief.md`; Mapper scope card. | `memoria-mapper` |
| `Memoria: scope this project` | `corpus-map.md` in `40-workbench/<project>/01-map/`. | `memoria-mapper` |
| `Memoria: frame this section` | Outlines in `40-workbench/<project>/02-framing/`. | `memoria-writer` |
| `Memoria: verify this draft` | Verification report in `40-workbench/<project>/05-verification/`. | `memoria-verifier` |

## Maintenance

| Command | Output | Implementation |
| --- | --- | --- |
| `Memoria: approve all link suggestions` | Bulk-approves all `review_status: requested` cards. | QuickAdd → POST Hermes API (bulk approve) |
| `Memoria: lint this note` | Linter dry-run report on the active note. | QuickAdd → POST Hermes API (assignee: `memoria-linter`) |
| `Memoria: show lane status` | Opens `index.md` dashboard in right sidebar. | QuickAdd → workspace pane |

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

- Hermes CLI commands (per-profile + board management): [hermes-cli.md](hermes-cli.md)
- Policy on commands that target review-gated zones: [policy-mcp.md — Review-gated zones](policy-mcp.md)
- Invocation patterns and hotkey discipline: [how-to-guides/command-palette.md](../how-to-guides/interface/command-palette.md)
