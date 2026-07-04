# Pre-alpha.1 "Old Skeleton" — captured from Google Drive (2026-05-29 snapshot)

> Supporting source for the **Origins prologue** of the Memoria design-history doc.
> Location: Google Drive → `memoria-docs/` (folder `1R5Tw9Gt5GHhsWU7-3GU9iHKBFXNz7__r`),
> created 2026-05-29 — **before alpha.1** (alpha.1 cut ~2026-06-03…06-14).
> The `memoria-docs/` folder contains `.git/`, `.obsidian/`, **`Old Skeleton/`**, **`New Skeleton/`**
> — so this design **has its own git backup inside the Drive snapshot** (not at-risk like the
> gitignored `_notes/`). Full file list + IDs recorded below; the two anchor docs (vision, README)
> are distilled here. Pull the full tree into the repo on request.

## What the Old Skeleton design was (pre-alpha.1)

**Identity.** "A research operating system that turns sources into durable knowledge through
explicit states, specialized Hermes profiles, and a Kanban board that preserves review, retries,
and handoffs." Single-user; the human owns judgment.

**Intellectual synthesis (the genesis stack)** — from `vision.md`:
- **Karpathy's LLM-Wiki** — the agent is a *compiler*, not a retriever; a persistent interlinked
  markdown wiki that grows with use (vs RAG-from-scratch per query).
- **Luhmann's Zettelkasten** — atomicity, explicit linking, type distinction (fleeting / literature
  / permanent → renamed `paper-note`, `claim-note` "for clarity in a software context").
- **Bush's Memex** — associations as first-class objects; preserve trails of inquiry.
- **Contemporary AI-research systems** (survey of 37) — adopted: stage-gated pipelines, thin control
  over thick state, explicit agent roles, structured handoff outputs, persistent knowledge graphs,
  reviewable organization artifacts. Nearest twin = PARNESS (near-identical, but PARNESS is fully
  autonomous; Memoria has a structurally blocking human gate).

**Autonomy position.** Targets **L3 with a structurally enforced ceiling** (Chen 2026 taxonomy):
profiles execute multi-step unattended within a card, human sets strategy + review gates promotion.
Deliberately NOT L4/L5 — "synthesis correctness is not scalar and synthesis changes are not
reversible." Framed as "vibe researching made durable (the vault) and gated (blocking review)."
The one exception: the Coder lane (where scalar+reversible+independent preconditions hold).

**Three-layer model** (`architecture/`): **board (Kanban) = control plane** · **workers (Hermes
profiles) = execution layer** · **vault (Obsidian folders) = durable store**. "Thin control over
thick state" — orchestrator/workers carry minimal context; durable knowledge lives in files.

**The seven Hermes profiles** (`profiles/`): co-pi/socratic, librarian, mapper, writer, coder,
verifier, + (per Drive files: cmdr). Each has narrow permissions + a clear exit condition ("avoids
one-model-does-everything"). Profiles claim cards within their lane.

**The board** (`board/`): Hermes native Kanban. `states.md` = state machine + lanes + review gate;
`card-schema.md` = Hermes built-in card fields (task_id, title, body, assignee=lane key, status
enum `triage·todo·ready·running·blocked·done·archived`, priority, workspace, …) + Memoria overlay
in free-form `metadata` JSON (review_status, provenance). **Review is a structural gate**: a card
cannot promote until the human sets `review_status: approved` (not advisory).

**The vault** (`vault/`): **folders encode lifecycle stage, not subject** — numbered folders like
`20-sources/01-papers/`, `30-synthesis/01-claims/`. **15 note types** (`templates.md`) with
lifecycles; `frontmatter-schema.md` = frontmatter + controlled vocab; wikilinks + MOCs + entity
links. Canonical synthesis is human-owned; paper notes never overwritten by structure/code agents.

**Surfaces** (`surfaces/`): four types — persistent, modal, inline, ambient — + command-palette +
design-system. **11 dashboards** (`dashboards/`). **Plugins** (`plugins/`): required(8)/
recommended(5)/optional(6) incl. agent-client (ACP pane), citation, linter, dataview, templater.

**Decisions**: **21 ADRs** in `decisions/` (18 with files, 3 index-only). Diátaxis-by-frontmatter
(`mode`/`audience`/`topic` in each file, not folder path).

**Design goals** (`vision.md`): capture/synthesis/promotion are distinct operations; human judgment
in the loop for classification/synthesis-quality/canonization; agent for mechanical work; Kanban as
shared state machine; durable knowledge in the vault not chat; explicit over implicit ("review is a
state not a comment; ownership is a field not a convention; promotion is a move not a tag").

**Naming**: *Memoria* = curated memory that compounds; *Hermes* = the messenger that moves work
between states/profiles/human↔vault.

## How this maps forward (for the design-history doc)
This is the direct ancestor of the **alpha.1 baseline** (which kept the seven profiles, Hermes
runtime, Kanban, numbered lifecycle folders, blocking gate, MCP sandbox). The researcher's own
notes ([../notes/... via researcher-notes.md](../../researcher-notes.md)) describe adopting this
stack (Hermes/Obsidian/Zotero/ZK) "without evaluating fit" — the tension that later forces the
clean-slate reset (2026-06-26) and the alpha.11 pivot ("direction not authorship / traceability not
approval"). The seven-layer architecture in the researcher's notes is a later elaboration of this
three-layer model.

## Full Drive inventory (Old Skeleton) — pullable on request
Folder `Old Skeleton/` = `10dRmJPVaJui9gHuLl8YAN6Q8Jix9FTGZ`. Subfolders: architecture, board,
profiles, vault, workflows, surfaces, roadmap, operations, decisions, dashboards, plugins,
tutorials. Root files: `vision.md`, `README.md`, `glossary.md`, `Notes.md`.
Key design files (id): vision (13yZIrF79aT9WEs571f7u_XWI1Fx62Ph5), README
(177aFcMrJkrqypNXNrP-u6fSerL4r6U9w), glossary (1-MR2Way-P1eS2-JOHPytcFAYkwX7Ir-f),
architecture/README (1dnvSJJSsMeqOFdbiNtmTcNFyCcfIJ7QT), control-plane (11RLs0emCp8Hnj9JqTnwOBGbDVPr3jfSy),
capability-stack (1-jxBOkUFYZZhGJ0DUt3YOL_WHc7q7P3-), on-disk-layout (1hHTAVx0OaeCt6w6Z5z43vGlN1WrTAEWQ),
why-no-autonomous-synthesis (1RjWJVq17PjbecMVgYRJpq0B8p43BOy_H),
why-pattern-provenance (1_FJArg1EMsk7W0bnsWlyW_4SAdygEzAh),
why-computational-methods (1v005WaUCt2qPZ7Kalm_BjA9THBETLZHi),
board/README (1A4hWJHzmfYR8CBImg-5DFmLpAWrcmenY), board/states (12jT5oELnJVD7s0qbtn9IVl5kPvGn2xEz),
board/card-schema (1jYqX3VnwgPCCcHBlabgXai9anDgr0TvN),
vault/README (12TinBnSvJ4k0HHyiFUuvs4zAu8_R0vn2), vault/frontmatter-schema (1LTMyTzJBO_hzTEi7EIH9R5xwhJHs_vfT),
vault/templates (1qSRuxoBs8zYy4egmjdTyhVBNaevQI5Pf),
profiles/README (1sPaN_0ZuG8fGaLGQzNUf7TwoEnfmQZ6Y) + coder/writer/socratic/mapper/librarian/verifier md,
roadmap/README (1V9MpYZW3wtP2e5rM7Jtu7UdHGgnLmS6w) + deployment-options/future-directions/timeline/
design-tensions/success-metrics/sync-and-coordination/profile-compilation.
`New Skeleton/` = `1_EpiRJJGOjqgFOMS09I7fzW79qJqjR_g` (Diátaxis reorg: 10 Setup, 20 Using the Vault,
25 Using Hermes, 30 Architecture, 40 References, 50 Changelog, 60 Roadmap, Index.md, 70 About.md).
