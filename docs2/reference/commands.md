---
topic: reference
---

# Commands

All commands available in Memoria: Obsidian command palette entries (registered by QuickAdd) and Hermes CLI commands per profile. For invocation patterns and hotkey discipline see [how-to-guides/obsidian/command-palette.md](../how-to-guides/obsidian/command-palette.md).

---

## Obsidian command palette (`Memoria:` prefix)

Invoked via `Cmd-P → Memoria: …`. Registered by QuickAdd. Commander binds the top five to physical ribbon buttons.

### Capture

| Command | Output | Implementation |
| --- | --- | --- |
| `Memoria: capture fleeting` | New note in `10-inbox/01-fleeting/` with timestamp. | QuickAdd → Templater (fleeting template) |
| `Memoria: capture source from URL` | `intake:source` card on Librarian lane queue; Librarian picks it up within 60 s. | QuickAdd → POST Hermes API |
| `Memoria: capture from Zotero selection` | `intake:source` card with citekey pre-populated from current Zotero selection. | QuickAdd → Zotero local API → POST Hermes API |

### Processing

| Command | Output | Implementation |
| --- | --- | --- |
| `Memoria: ask about this note` | Opens Socratic ACP pane (session-resident). No note writes. | QuickAdd → `open-chat-view` (agent: `memoria-socratic`; `autoMentionActiveNote: true`) |
| `Memoria: discuss this fleeting note` | `discuss` card + Socratic ACP pane. Fleeting → claim transition path. | QuickAdd composing two commands |
| `Memoria: write claim note` | New note from claim template in `30-synthesis/01-claims/`; `maturity: seedling`. | QuickAdd → Templater (claim template) |

### Interactive retrieval (transient ACP — no file artifact, no card)

| Command | Profile | Output |
| --- | --- | --- |
| `Memoria: find related notes` | Mapper | Top 5–10 related notes by similarity, in chat. No file written. |
| `Memoria: counter-outline this section` | Writer (`counter-outline` skill) | 2–3 competing outlines in chat. No file written. |
| `Memoria: similarity-check this claim` | Verifier | Top 3 most-similar claim notes, in chat. No audit entry. |

### Project (card-based — produces file artifacts, Kanban-tracked)

| Command | Output | Assignee |
| --- | --- | --- |
| `Memoria: new project` | `40-workbench/<name>/` + `brief.md`; Mapper scope card. | `memoria-mapper` |
| `Memoria: scope this project` | `corpus-map.md` in `40-workbench/<project>/01-map/`. | `memoria-mapper` |
| `Memoria: frame this section` | Outlines in `40-workbench/<project>/02-framing/`. | `memoria-writer` |
| `Memoria: verify this draft` | Verification report in `40-workbench/<project>/05-verification/`. | `memoria-verifier` |

### Maintenance

| Command | Output | Implementation |
| --- | --- | --- |
| `Memoria: approve all link suggestions` | Bulk-approves all `review_status: requested` cards. | QuickAdd → POST Hermes API (bulk approve) |
| `Memoria: lint this note` | Linter dry-run report on the active note. | QuickAdd → POST Hermes API (assignee: `memoria-linter`) |
| `Memoria: show lane status` | Opens `index.md` dashboard in right sidebar. | QuickAdd → workspace pane |

### Lens-based reading (Socratic, parameterized)

Each lens is one command. Adding a lens = adding one QuickAdd entry.

| Command | Lens slug |
| --- | --- |
| `Memoria: read through Mamykina lens` | `mamykina-sensemaking` |
| `Memoria: read through Veinot equity lens` | `veinot-informational-justice` |
| `Memoria: read through Design Justice lens` | `design-justice-costanza-chock` |
| `Memoria: read through JITAI lens` | `jitai-receptivity-timing` |

---

## Hermes CLI commands per profile

Run as: `hermes -p memoria-<name> chat -s <command> [args]`

### Librarian

| Command | What it does | Dry-run? |
| --- | --- | --- |
| `find` | Forward/backward citation search or concept-driven search. Writes candidates to `10-inbox/03-candidates/`. | No |
| `ingest` | Create the note for a source in the right folder with enrichment. | No |
| `enrich` | Re-run API enrichment on existing notes. | No |
| `classify` | Re-propose `_proposed_classification` on a note still needing review. | No |
| `obsidian-paper-note` | Full ingest pipeline including PDF extraction via Marker. | No |
| `query` | Deterministic vault search (standalone retrieval). | No |

### Mapper

| Command | What it does | Dry-run? |
| --- | --- | --- |
| `scope-project` | Corpus map for a project. Writes `corpus-map.md` to `<project>/01-map/`. | No |
| `gap-report` | Thin-coverage topics adjacent to a project brief. | No |
| `cluster-map` | Density / recency map for an arbitrary topic. | No |
| `comparative-brief` | Compare a new source against existing claims. Drives `[!brief]` callout. | No |

### Socratic

| Command | What it does | Dry-run? |
| --- | --- | --- |
| `socratic-processing` | Question-only conversation about a note. No writes. | N/A (read-only) |
| `lens-reading` | Read through a named theoretical lens. Parameterized by lens slug. | N/A (read-only) |

### Writer

| Command | What it does | Dry-run? |
| --- | --- | --- |
| `draft` | Search vault and produce an answer note for human review. | No |
| `query` | Pre-draft vault search step. | No |
| `promote` | Propose promotion of a claim → reference note (handoff; human approves). | N/A (handoff) |

### Verifier

| Command | What it does | Dry-run? |
| --- | --- | --- |
| `cite-check` | Verify every citekey in a draft resolves to a real paper note. | Yes (default) |
| `similarity-check` | Top-N most-similar notes; flag at threshold ~0.8; never auto-merge. | Yes |
| `find-duplicates` | Identify semantically similar claim notes for merge review. | Yes; never auto-merges |
| `retraction-check` | Scan paper notes against Zotero retraction alerts and CrossRef. | Yes (default) |

### Coder

| Command | What it does | Dry-run? |
| --- | --- | --- |
| `code` | Scaffold a `code-note` handoff for the external coding agent. | No |
| `commit` | Commit one logical change per call. | No |
| `revert` | Revert a prior Coder commit; scoped small. | No |
| `workspace` | Set up VS Code workspace (vault read-only; code zone writable). | N/A |
| `scaffold` | Generate the `code-note` skeleton from the template. | No |

### Linter

| Command | What it does | Dry-run? |
| --- | --- | --- |
| `lint` | Structural health check across the vault. | Yes (default) |
| `schema-check` | Verify frontmatter against the authoritative schema. | Yes |
| `schema-migrate` | Propose schema changes between versions. Always dry-run first. | Yes (always required first) |
| `graph-analyze` | Knowledge graph health: orphans, hubs, clusters, link density. | Yes |
| `health-report` | Rolls structural findings into the verdict band (PASS / REVIEW / FAIL). | Yes |
| `session-log` | Write per-session log to `00-meta/02-logs/`. | N/A |
| `dry-run` | Run any check in report-only mode. | Yes (by definition) |

---

## Board management commands

| Command | What it does |
| --- | --- |
| `hermes kanban create "<title>" --assignee memoria-<name>` | Create a new card in `triage`. |
| `hermes kanban specify <id>` | Flesh out a `triage` card into a concrete spec → `todo`. |
| `hermes kanban release <id>` | Release a `todo` card to `ready` for dispatch. |
| `hermes kanban dispatch` | Run one dispatcher pass (claims all `ready` cards for matching lanes). |
| `hermes kanban claim <id>` | Manually claim a `ready` card (script/debug use only). |
| `hermes kanban unblock <id>` | Clear a `blocked` card → `ready`. |
| `hermes kanban archive <id>` | Archive a terminal card. |
| `hermes kanban decompose <id>` | Fan out a `triage` card into child task cards. |

See [policy.md — Review-gated zones](policy.md) for the rule on commands that target synthesis or deliverable folders.
