---
title: Obsidian command palette
parent: Reference
---

# Command palette

The `Memoria:` command-palette surface — the in-Obsidian commands, registered by QuickAdd (`Cmd-P → Memoria: …`). The co-PI conversation remains the primary route for agent tasks — you tell the co-PI what you want and it delegates a ceiling-validated card to the right lane via the tasks MCP (see [Kanban board reference](kanban-board.md)) — but **every lane task is also directly reachable from the palette** ([#203](https://github.com/eranroseman/memoria-vault/issues/203)): one command per task, each creating a correctly-addressed card on the matching lane, plus the generic delegate fallback, a pattern runner, the capture entry points that must fire from inside the editor, and the inbox resolve action.

---

## Capture and note-creation commands

| Command | Output | Implementation |
| --- | --- | --- |
| `Memoria: capture fleeting` | A new fleeting note in `notes/fleeting/` from the fleeting template (`lifecycle: proposed`, `origin: human`). | QuickAdd Template → `system/templates/fleeting.md` |
| `Memoria: write claim note` | A new claim note from the claim template — **review-gated home** (`notes/claims/`): only the PI creates here. | QuickAdd Template → `system/templates/claim.md` |
| `Memoria: capture source from URL` | A capture card on the Librarian lane with the pasted URL. A URL with a resolvable DOI ingests; a bare/proxied URL blocks asking for the DOI or citekey. | QuickAdd Macro → [src/system/scripts/capture-from-url.js](../../src/system/scripts/capture-from-url.js) → `hermes kanban create` |
| `Memoria: capture from Zotero selection` | A capture card on the Librarian lane, citekey pre-populated from the current Zotero selection. | QuickAdd Macro → [src/system/scripts/capture-from-zotero.js](../../src/system/scripts/capture-from-zotero.js) (Better BibTeX CAYW) → `hermes kanban create` |
| `Memoria: resolve inbox card` | The **active** note (must be under `inbox/`) flipped in place: `lifecycle:` set to your verdict (current = accept, retracted = reject, or archived) and `resolved:` stamped with today's date. | QuickAdd Macro → [src/system/scripts/resolve-inbox-card.js](../../src/system/scripts/resolve-inbox-card.js) (pure Obsidian API — no shelling) |

Template-based note creation (fleeting, claim, hub, …) starts from the templates in `system/templates/` — see [Note types](note-types.md).

---

## Per-task lane commands

One command per lane task, each prompting only for what that task needs and creating a card addressed to the lane's agent and skill (`hermes kanban create --assignee … --skill …`). All six lane tasks are reachable here without the co-PI.

| Command | Lane → agent (skill) | Prompts for | Implementation |
| --- | --- | --- | --- |
| `Memoria: catalog a source` | catalog → Librarian (`catalog-enrich-record`) | Citekey or URL, optional goal. | QuickAdd Macro → [src/system/scripts/catalog-source.js](../../src/system/scripts/catalog-source.js) |
| `Memoria: extract claims` | extract → Librarian (`extract-stub-claim`) | The source note — defaults to the active note when it's under `catalog/papers/` or `notes/source/`, otherwise prompts for a path or citekey. | QuickAdd Macro → [src/system/scripts/extract-claims.js](../../src/system/scripts/extract-claims.js) |
| `Memoria: link a claim` | link → Librarian (`link-suggest-claim`) | The claim note — defaults to the active note when it's under `notes/claims/`. | QuickAdd Macro → [src/system/scripts/link-claim.js](../../src/system/scripts/link-claim.js) |
| `Memoria: map the corpus` | map → Librarian (`map-cluster-corpus`) | Scope (folder or hub note) — optional; Enter maps the whole corpus. | QuickAdd Macro → [src/system/scripts/map-corpus.js](../../src/system/scripts/map-corpus.js) |
| `Memoria: draft a section` | draft → Writer (`draft-write-section`) | The goal or outline ref. | QuickAdd Macro → [src/system/scripts/draft-section.js](../../src/system/scripts/draft-section.js) |
| `Memoria: verify a draft` | verify → Peer-reviewer (`verify-check-citation`) | The draft — defaults to the active note when it's under `projects/`. | QuickAdd Macro → [src/system/scripts/verify-draft.js](../../src/system/scripts/verify-draft.js) |
| `Memoria: delegate a task` | Any lane (you pick from a suggester; no skill pinned) | Lane + free-form goal — the generic fallback for work that doesn't fit a single-task command. | QuickAdd Macro → [src/system/scripts/delegate-task.js](../../src/system/scripts/delegate-task.js) |
| `Memoria: run a pattern` | Librarian card invoking `patterns_run` (ADR-53) | A pattern, from a suggester over the runnable (`lifecycle: current`) patterns in `system/patterns/`; the active note rides along as `input_ref`. | QuickAdd Macro → [src/system/scripts/run-pattern.js](../../src/system/scripts/run-pattern.js) |

The lane → agent mapping mirrors `LANE_PROFILE` in `.memoria/mcp/tasks_mcp.py` (the `code` lane has no single-task command — use `Memoria: delegate a task`).

---

## Removed and retired commands

| Command | Status | Where the job went |
| --- | --- | --- |
| `Memoria: lint this note` | **Removed** | The Linter is an engine, not an agent — the daily cron and the pre-commit gate cover it; nothing to invoke per note ([Linter: detectors and auto-fix](linter.md)). |
| `Memoria: verify this draft` | Replaced | `Memoria: verify a draft` (above), or ask the co-PI. |
| `Memoria: frame this section` | Replaced | `Memoria: draft a section` (above), or ask the co-PI. |
| `Memoria: new project` / `Memoria: scope this project` | Retired | Project scaffolding and scoping return with the v0.1.0-alpha.3 Project release; meanwhile `Memoria: map the corpus` or the co-PI covers `map` lane work. |

---

## The co-PI delegation path

When you don't already know the lane — or the work spans several tasks — the conversational path is:

1. Open the Agent Client pane (the co-PI; the active note auto-attaches).
2. Say what you want ("verify this draft", "scope a project on X").
3. The co-PI calls `delegate_route_task` — the handoff is validated against the lane's write-scope ceiling, the card lands on the board, and the result resurfaces in the Inbox.

---

## Related

- The delegation mechanics: [Kanban board reference](kanban-board.md)
- The terminal surface: [Hermes CLI](hermes-cli.md)
- The capture pipeline behind both macros: [Ingest routing](ingest.md)
