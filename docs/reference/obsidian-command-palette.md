---
title: Obsidian command palette
parent: Reference
---

# Command palette

The `Memoria:` command-palette surface — the in-Obsidian capture commands, registered by QuickAdd (`Cmd-P → Memoria: …`). In v0.1.1 this surface is deliberately small: **the co-PI conversation is the primary route for agent tasks.** Instead of a palette command per task, you tell the co-PI what you want; it delegates a ceiling-validated card to the right lane via the tasks MCP (see [Kanban board reference](kanban-board.md)). The palette keeps the capture entry points that must fire from inside the editor, plus two thin shims on the delegation model itself (ADR-48): a manual delegate for when you already know the lane, and the inbox resolve action.

---

## Surviving commands

| Command | Output | Implementation |
| --- | --- | --- |
| `Memoria: capture fleeting` | A new fleeting note in `notes/fleeting/` from the fleeting template (`lifecycle: proposed`, `origin: human`). | QuickAdd Template → `system/templates/fleeting.md` |
| `Memoria: write claim note` | A new claim note from the claim template — **review-gated home** (`notes/claims/`): only the PI creates here. | QuickAdd Template → `system/templates/claim.md` |
| `Memoria: capture source from URL` | A capture card on the Librarian lane with the pasted URL. A URL with a resolvable DOI ingests; a bare/proxied URL blocks asking for the DOI or citekey. | QuickAdd Macro → [src/system/scripts/capture-from-url.js](../../src/system/scripts/capture-from-url.js) → `hermes kanban create` |
| `Memoria: capture from Zotero selection` | A capture card on the Librarian lane, citekey pre-populated from the current Zotero selection. | QuickAdd Macro → [src/system/scripts/capture-from-zotero.js](../../src/system/scripts/capture-from-zotero.js) (Better BibTeX CAYW) → `hermes kanban create` |
| `Memoria: delegate a task` | A card on the chosen lane (catalog/extract/link/map → Librarian, draft → Writer, verify → Peer-reviewer, code → Engineer) with the goal you type — the palette twin of asking the co-PI, for when you already know the lane. | QuickAdd Macro → [src/system/scripts/delegate-task.js](../../src/system/scripts/delegate-task.js) → `hermes kanban create` |
| `Memoria: resolve inbox card` | The **active** note (must be under `inbox/`) flipped in place: `lifecycle:` set to your verdict (current = accept, retracted = reject, or archived) and `resolved:` stamped with today's date. | QuickAdd Macro → [src/system/scripts/resolve-inbox-card.js](../../src/system/scripts/resolve-inbox-card.js) (pure Obsidian API — no shelling) |

Template-based note creation (fleeting, claim, hub, …) starts from the templates in `system/templates/` — see [Note types](note-types.md).

---

## Removed and retired commands

| Command | Status | Where the job went |
| --- | --- | --- |
| `Memoria: lint this note` | **Removed** | The Linter is an engine, not an agent — the daily cron and the pre-commit gate cover it; nothing to invoke per note ([Linter: detectors and auto-fix](linter.md)). |
| `Memoria: verify this draft` | Retired | Ask the co-PI to verify; it delegates to the `verify` lane. |
| `Memoria: frame this section` | Retired | Ask the co-PI; it delegates to the `draft` lane. |
| `Memoria: new project` / `Memoria: scope this project` | Retired | Project scaffolding and scoping return with the v0.1.2 Project release; meanwhile the co-PI delegates `map` lane work. |

---

## The co-PI delegation path

For anything that used to be a palette command, the working path is:

1. Open the Agent Client pane (the co-PI; the active note auto-attaches).
2. Say what you want ("verify this draft", "scope a project on X").
3. The co-PI calls `delegate_route_task` — the handoff is validated against the lane's write-scope ceiling, the card lands on the board, and the result resurfaces in the Inbox.

---

## Related

- The delegation mechanics: [Kanban board reference](kanban-board.md)
- The terminal surface: [Hermes CLI](hermes-cli.md)
- The capture pipeline behind both macros: [Ingest routing](ingest.md)
