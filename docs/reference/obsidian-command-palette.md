---
title: Obsidian command palette
parent: Agents and control
grand_parent: Reference
---

# Obsidian command palette

The `Memoria:` command-palette surface — the in-Obsidian commands, registered by QuickAdd (`Cmd-P → Memoria: …`). Commander mirrors the highest-frequency entries into the ribbon and page header: capture, delegate, resolve, and note-local claim/source actions. Space switching is handled by the left-pane navigator rail (**Now** / **Places**); the command palette is for actions, not navigation.

Action parity rule: durable actions are reachable from the palette without asking the Co-PI ([ADR-72](../adr/72-command-surfacing.md)). The Co-PI remains the conversational route; durable output still becomes a command result or a delegated board card.

---

## Capture and note-creation commands

| Command | Output | Implementation |
| --- | --- | --- |
| `Memoria: capture fleeting` | Opens the `memoria-fleeting-capture` Modal Forms form, writes one raw item to `notes/fleeting/` (`lifecycle: proposed`, `origin: human`), and leaves processing to the Inbox queue. | QuickAdd Macro → `system/scripts/capture-fleeting.js` |
| `Memoria: archive fleeting note` | The **active** fleeting note (must be under `notes/fleeting/`) flipped in place to `lifecycle: archived` and stamped with `archived:`. | QuickAdd Macro → `system/scripts/archive-active-note.js` (`Type: fleeting`) |
| `Memoria: write claim note` | Opens the `memoria-claim-capture` Modal Forms form, writes a standalone claim in the **review-gated home** (`notes/claims/`), runs the pre-file similarity shadow check, and opens the note. | QuickAdd Macro → `system/scripts/write-claim.js` |
| `Memoria: archive claim note` | The **active** claim note (must be under `notes/claims/`) flipped in place to `lifecycle: archived` and stamped with `archived:`. | QuickAdd Macro → `system/scripts/archive-active-note.js` (`Type: claim`) |
| `Memoria: load sample vault` | Copies the bundled `.memoria/samples/mediterranean-diet/` `catalog/` and `notes/` files into the live vault, skipping existing files so user work is not overwritten. | QuickAdd Macro → `src/system/scripts/load-sample-vault.js` |
| `Memoria: remove sample vault` | Archives live `catalog/` and `notes/` files labeled `sample: true`, leaving the hidden bundle in place. | QuickAdd Macro → `src/system/scripts/remove-sample-vault.js` |
| `Memoria: capture source from URL` | A source candidate lands in **Needs me**; the Librarian ingest task lands in **Activity**. A URL with a resolvable DOI ingests; a bare/proxied URL blocks asking for the DOI or citekey. | QuickAdd Macro → `src/system/scripts/capture-from-url.js` → `hermes kanban create` |
| `Memoria: structured source capture` | Opens the `memoria-source-capture` Modal Forms form, writes a schema-valid `source` note at `lifecycle: proposed` under `notes/sources/`, and raises an Inbox `candidate` pointing at it. | QuickAdd Macro → `src/system/scripts/structured-source-capture.js` (Modal Forms API + Obsidian adapter) |
| `Memoria: start project` | Opens the Project start form, scaffolds `projects/<slug>/` with `project.md`, `thesis.md`, and empty `code/`, `drafts/`, and `exports/` folders. | QuickAdd Macro → `src/system/scripts/start-project.js` (Modal Forms API + Obsidian adapter) |
| `Memoria: capture from Zotero selection` | A Tier-0 Catalog stub plus a source candidate in **Needs me**; the Librarian ingest task lands in **Activity**. | QuickAdd Macro → `src/system/scripts/capture-from-zotero.js` (Better BibTeX JSON-RPC) → `hermes kanban create` |
| `Memoria: resolve inbox card` | The **active** note (must be under `inbox/`) archived in place with `lifecycle: archived` and `resolved:` stamped with today's date. | QuickAdd Macro → `src/system/scripts/resolve-inbox-card.js` (pure Obsidian API — no shelling) |
| `Memoria: dismiss inbox card` | The **active** Inbox card archived in place with no menu, then the pane returns to the Inbox. Generated ticket buttons use this when the only immediate action is to clear the ticket. | QuickAdd Macro → `src/system/scripts/resolve-inbox-card.js` (`Outcome: Dismiss`) |
| `Memoria: open Inbox` | Opens `spaces/inbox.md` in the active pane without changing the active note. Generated tickets use this for a **Back to Inbox** button. | QuickAdd Macro → `src/system/scripts/open-inbox.js` |

Template-based document creation starts from the templates in `system/templates/` — see [Document types](document-types.md). Claim and fleeting capture use Modal Forms wrappers that render their templates, so the form prompts, note body, and note-local command buttons stay aligned.

---

## Per-task lane commands

One command per non-code lane task, each prompting only for what that task needs and creating a card addressed to the lane's agent and skill (`hermes kanban create --assignee … --skill …`). These commands show status in **Inbox → Activity**; **Needs me** changes only if the result requires PI action. Code and unusual work use the generic delegate command.

| Command | Lane → agent (skill) | Prompts for | Implementation |
| --- | --- | --- | --- |
| `Memoria: catalog source` | catalog → Librarian (`catalog-enrich-record`) | Citekey or URL, optional goal. | QuickAdd Macro → `src/system/scripts/catalog-source.js` |
| `Memoria: extract claims` | extract → Librarian (`extract-stub-claim`) | The source note — defaults to the active note when it's under `catalog/papers/` or `notes/sources/`, otherwise prompts for a path or citekey. | QuickAdd Macro → `src/system/scripts/extract-claims.js` |
| `Memoria: link claim` | link → Librarian (`link-suggest-claim`) | The claim note — defaults to the active note when it's under `notes/claims/`. | QuickAdd Macro → `src/system/scripts/link-claim.js` |
| `Memoria: map corpus` | map → Librarian (`map-cluster-corpus`) | Scope (folder or hub note) — optional; Enter maps the whole corpus. | QuickAdd Macro → `src/system/scripts/map-corpus.js` |
| `Memoria: retry map corpus and dismiss` | map → Librarian (`map-cluster-corpus`) | Scope (folder or hub note) — optional; Enter maps the whole corpus. Generated map-blocker tickets use it to queue the retry, archive the ticket, and return to the Inbox. | QuickAdd Macro → `src/system/scripts/retry-map-corpus-and-dismiss.js` |
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
| `Memoria: assist ask` | Co-PI `ask-question-source` / `ask-read-lens` | Stages a Co-PI question card when the answer should be reviewable or persistent. | Ask directly in the Agent Client pane; the active note is passed as a readable reference. |
| `Memoria: assist draft` | Writer `draft-write-section` | Prompts for a section/outline goal and stages a draft request with selected text as source context. | Ask the Co-PI to shape the draft, then delegate the durable drafting step. |
| `Memoria: assist explore` | Co-PI `explore-framings` | Stages an exploration card with the active note/selection attached. | Explore directly in the pane while the output is still human understanding. |

## Note utility commands

These commands write notes directly from local templates or the active note; they do
not create board cards.

| Command | Use | Implementation |
| --- | --- | --- |
| `Memoria: create linked claim note` | From an active source note, create a claim in `notes/claims/`, add the source citekey to `sources`, link it under **Worth distilling**, and open the claim. | QuickAdd Macro → `src/system/scripts/create-linked-claim.js` |
| `Memoria: refresh project gate` | From an active project file, runs the deterministic Project structural-impact operation and refreshes `project-gate-index.md`. | QuickAdd Macro → `src/system/scripts/refresh-project-gate.js` |
| `Memoria: supersede thesis` | From an active thesis note, creates a proposed replacement, marks `superseded_by` on the old thesis, updates the project `active_thesis`, and raises a re-confirmation alert. | QuickAdd Macro → `src/system/scripts/supersede-thesis.js` |
| `Memoria: record exploration trace` | Capture a rejected direction/dead end beside an active or selected map/gap report under `notes/fleeting/maps/`. | QuickAdd Macro → `src/system/scripts/record-exploration-trace.js` |

---
## The Co-PI delegation path

For work where the lane is unknown or spans several tasks, use the Agent Client pane:

1. The PI asks the Co-PI in free form; the active note is available as a readable reference.
2. The Co-PI calls `delegate_route_task`.
3. The handoff is validated against the lane's write-scope ceiling.
4. A board card is created.
5. Status appears in **Inbox → Activity**.
6. **Needs me** changes only when the result needs PI action.

The mechanics are in [Kanban board reference](kanban-board.md).

---

## Related

- The delegation mechanics: [Kanban board reference](kanban-board.md)
- The terminal surface: [Hermes CLI](hermes-cli.md)
- The capture pipeline behind both macros: [Ingest routing](ingest.md)
