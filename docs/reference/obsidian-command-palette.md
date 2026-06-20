---
title: Obsidian command palette
parent: Reference
---

# Command palette

The `Memoria:` command-palette surface — the in-Obsidian commands, registered by QuickAdd (`Cmd-P → Memoria: …`). Commander mirrors the highest-frequency entries into the ribbon and page header: capture, delegate, resolve, and note-local claim/source actions. Space switching is now the nav row in the four dashboard notes ([ADR-81](../adr/81-persistent-gate-dashboards.md)), not a QuickAdd workspace command. The Co-PI conversation remains the primary route for agent tasks — you tell the Co-PI what you want and it delegates a ceiling-validated card to the right lane via the tasks MCP (see [Kanban board reference](kanban-board.md)) — but **every lane task is also directly reachable from the palette** ([#203](https://github.com/eranroseman/memoria-vault/issues/203)): one command per task, each creating a correctly-addressed card on the matching lane, plus the generic delegate fallback, a pattern runner, the capture entry points that must fire from inside the editor, the inbox resolve action, and verb-shaped assist commands for Find/Search/Patterns/Ask/Draft/Explore.

---

## Capture and note-creation commands

| Command | Output | Implementation |
| --- | --- | --- |
| `Memoria: capture fleeting` | A new fleeting note in `notes/fleeting/` from the fleeting template (`lifecycle: proposed`, `origin: human`). | QuickAdd Template → `system/templates/fleeting.md` |
| `Memoria: write claim note` | A new claim note from the claim template — **review-gated home** (`notes/claims/`): only the PI creates here. | QuickAdd Template → `system/templates/claim.md` |
| `Memoria: capture source from URL` | A capture card on the Librarian lane with the pasted URL. A URL with a resolvable DOI ingests; a bare/proxied URL blocks asking for the DOI or citekey. | QuickAdd Macro → `src/system/scripts/capture-from-url.js` → `hermes kanban create` |
| `Memoria: structured source capture` | Opens the `memoria-source-capture` Modal Forms form, writes a schema-valid `source` note at `lifecycle: proposed` under `notes/sources/`, and raises an Inbox `candidate` pointing at it. | QuickAdd Macro → `src/system/scripts/structured-source-capture.js` (Modal Forms API + Obsidian adapter) |
| `Memoria: start project` | Opens the Project start form, scaffolds `projects/<slug>/` with `project.md`, `thesis.md`, and empty `code/`, `drafts/`, and `exports/` folders. | QuickAdd Macro → `src/system/scripts/start-project.js` (Modal Forms API + Obsidian adapter) |
| `Memoria: capture from Zotero selection` | A Tier-0 Catalog stub plus a capture card on the Librarian lane, citekey pre-populated from the current Zotero selection. | QuickAdd Macro → `src/system/scripts/capture-from-zotero.js` (Better BibTeX JSON-RPC) → `hermes kanban create` |
| `Memoria: resolve inbox card` | The **active** note (must be under `inbox/`) flipped in place: `lifecycle:` set to your outcome (`current` = accept, `archived` = reject / done) and `resolved:` stamped with today's date. | QuickAdd Macro → `src/system/scripts/resolve-inbox-card.js` (pure Obsidian API — no shelling) |

Template-based note creation (fleeting, claim, hub, …) starts from the templates in `system/templates/` — see [Note types](note-types.md).

---

## Per-task lane commands

One command per lane task, each prompting only for what that task needs and creating a card addressed to the lane's agent and skill (`hermes kanban create --assignee … --skill …`). All six lane tasks are reachable here without the Co-PI.

| Command | Lane → agent (skill) | Prompts for | Implementation |
| --- | --- | --- | --- |
| `Memoria: catalog source` | catalog → Librarian (`catalog-enrich-record`) | Citekey or URL, optional goal. | QuickAdd Macro → `src/system/scripts/catalog-source.js` |
| `Memoria: extract claims` | extract → Librarian (`extract-stub-claim`) | The source note — defaults to the active note when it's under `catalog/papers/` or `notes/sources/`, otherwise prompts for a path or citekey. | QuickAdd Macro → `src/system/scripts/extract-claims.js` |
| `Memoria: link claim` | link → Librarian (`link-suggest-claim`) | The claim note — defaults to the active note when it's under `notes/claims/`. | QuickAdd Macro → `src/system/scripts/link-claim.js` |
| `Memoria: map corpus` | map → Librarian (`map-cluster-corpus`) | Scope (folder or hub note) — optional; Enter maps the whole corpus. | QuickAdd Macro → `src/system/scripts/map-corpus.js` |
| `Memoria: draft section` | draft → Writer (`draft-write-section`) | The goal or outline ref. | QuickAdd Macro → `src/system/scripts/draft-section.js` |
| `Memoria: verify draft` | verify → Peer-reviewer (`verify-check-citation`) | The draft — defaults to the active note when it's under `projects/`. | QuickAdd Macro → `src/system/scripts/verify-draft.js` |
| `Memoria: delegate task` | Any lane (you pick from a suggester; no skill pinned) | Lane + free-form goal — the generic fallback for work that doesn't fit a single-task command. | QuickAdd Macro → `src/system/scripts/delegate-task.js` |
| `Memoria: run pattern` | Librarian card invoking `patterns_run` ([ADR-53](../adr/53-pattern-library.md)) | A pattern, from a suggester over the runnable (`lifecycle: current`) patterns in `system/patterns/`; the active note rides along as `input_ref`. | QuickAdd Macro → `src/system/scripts/run-pattern.js` |

The lane → agent mapping mirrors `LANE_PROFILE` in `.memoria/mcp/tasks_mcp.py` (the `code` lane has no single-task command — use `Memoria: delegate task`).

---


## Assist commands

Assist commands are verb-shaped entry points for work that starts in the current surface. Invoke them from the palette, from a selected span in the editor, or by asking the Co-PI in the Agent Client pane. Palette/selection invocations create staged cards or proposal artifacts; pane invocations stay conversational until you ask the Co-PI to delegate. None of these commands writes directly to canonical notes.

| Command | Existing skill / operation | Palette and selection behavior | Pane behavior |
| --- | --- | --- | --- |
| `Memoria: assist find` | Librarian `catalog-find-source` | Prompts for a source, topic, DOI, URL, or clue; selected text and the active note ride on the card. | Ask the Co-PI to find a source; it delegates if the result should persist. |
| `Memoria: assist search` | Librarian `map-report-coverage` | Prompts for a search lens or coverage question and stages a coverage/gap report request. | Ask the Co-PI what the corpus already holds for the lens. |
| `Memoria: assist patterns` | Librarian card invoking `patterns_run` | Picks a runnable pattern from `system/patterns/`; selected text/active note become input context, and output goes only to the returned target. | Ask the Co-PI which pattern to run, then delegate or use this command. |
| `Memoria: assist ask` | Co-PI `ask-question-source` / `ask-read-lens` | Stages a Co-PI question card when the answer should be reviewable or persistent. | Ask directly in the Agent Client pane; the active note is auto-attached. |
| `Memoria: assist draft` | Writer `draft-write-section` | Prompts for a section/outline goal and stages a draft request with selected text as source context. | Ask the Co-PI to shape the draft, then delegate the durable drafting step. |
| `Memoria: assist explore` | Co-PI `explore-framings` | Stages an exploration card with the active note/selection attached. | Explore directly in the pane while the output is still human understanding. |

## Note utility commands

These commands write notes directly from local templates or the active note; they do
not create board cards.

| Command | Use | Implementation |
| --- | --- | --- |
| `Memoria: write claim note` | Create a standalone claim note from `system/templates/claim.md`. | QuickAdd Template |
| `Memoria: create linked claim note` | From an active source note, create a claim in `notes/claims/`, add the source citekey to `sources`, link it under **Worth distilling**, and open the claim. | QuickAdd Macro → `src/system/scripts/create-linked-claim.js` |
| `Memoria: refresh project gate` | From an active project file, runs the deterministic Project structural-impact operation and refreshes `project-gate-index.md`. | QuickAdd Macro → `src/system/scripts/refresh-project-gate.js` |
| `Memoria: supersede thesis` | From an active thesis note, creates a proposed replacement, marks `superseded_by` on the old thesis, updates the project `active_thesis`, and raises a re-confirmation alert. | QuickAdd Macro → `src/system/scripts/supersede-thesis.js` |
| `Memoria: record exploration trace` | Capture a rejected direction/dead end beside an active or selected map/gap report under `notes/fleeting/maps/`. | QuickAdd Macro → `src/system/scripts/record-exploration-trace.js` |

---

## Removed and retired commands

| Command | Status | Where the job went |
| --- | --- | --- |
| `Memoria: lint this note` | **Removed** | The Linter is an operation, not an agent — the daily cron and the pre-commit hook cover it; nothing to invoke per note ([Linter: detectors and auto-fix](linter.md)). |
| `Memoria: verify this draft` | Replaced | `Memoria: verify draft` (above), or ask the Co-PI. |
| `Memoria: frame this section` | Replaced | `Memoria: draft section` (above), or ask the Co-PI. |
| `Memoria: new project` / `Memoria: scope this project` | Replaced | `Memoria: start project` opens the Project space on-ramp; `Memoria: refresh project gate` recomputes the deterministic cache. |
| `Memoria: open Desk/Library/Studio workspace` | Retired | Space switching is the nav row in `spaces/inbox.md`, `spaces/library.md`, `spaces/knowledge.md`, and `spaces/project.md`. |
| `Memoria: open Project gate` | Retired | Open `spaces/project.md` from any space nav row. |

---

## The Co-PI delegation path

For work where the lane is unknown or spans several tasks, the conversational path runs through the Agent Client pane (the Co-PI, with the active note auto-attached): a free-form request triggers a `delegate_route_task` call, the handoff is validated against the lane's write-scope ceiling, the card lands on the board, and the result resurfaces in the Inbox. The mechanics are in [Kanban board reference](kanban-board.md).

---

## Related

- The delegation mechanics: [Kanban board reference](kanban-board.md)
- The terminal surface: [Hermes CLI](hermes-cli.md)
- The capture pipeline behind both macros: [Ingest routing](ingest.md)
