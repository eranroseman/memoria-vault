# Memoria — Design History: alpha.1 → alpha.15

*Author: Eran Roseman · Assembled 2026-07-04 · Scope: the complete alpha.1 design and every design-bearing change through alpha.15 (does not cover beta.1).*

## About this document

This is a design-history reconstruction: **the full alpha.1 design in detail, then an exhaustive per-version changelog of everything that changed through alpha.15**, with the **reasoning** for each change, not just the change itself.

**Method.** Each version's design state was reconstructed from its release-boundary commit on `main` (there are no git tags; the boundary commits are listed per section), and every version-to-version delta was produced by diffing that boundary against the prior across `docs/`, `vault-template/`, and `src/`, cross-read against that version's own release/design/exec-plan documents. The *why* behind each change was mined from the version's design docs, the `docs/design/why-*.md` essays, ADR Context/Decision sections, full commit-message bodies, and the 401-paper literature review that drove many bets. **ADRs were used as reference, never as authority** — the shipped design docs, the `vault-template`/`src` substrate, and the researcher's own notes are the sources of truth.

**Sources** (all consolidated under [sources/](sources/)): the recovered `docs/releasing/0.1.0-alpha.{1..11}` release docs (`sources/versions/`); the `scratch/releases/0.1.0-alpha.{11..15}` design docs; the retired `docs/design/` essays (`sources/prealpha-docs-design/`); the gitignored `_notes/` reasoning layer (`sources/notes/`); the pre-alpha.1 Drive "Old Skeleton" snapshot (`sources/old-skeleton/`); and the researcher's own round-by-round notes ([researcher-notes.md](researcher-notes.md)).

> **Caveat — the reasoning layer is unbacked.** The `_notes/` directory (which holds the two documents that explain *why* the alpha.11 reset happened — `REVIEW-REFUTATIONS.md` and the clean-slate designs — plus the alpha.11 SSOT design) is **gitignored** and exists nowhere in version control. This document is intended to be the durable capture of that reasoning; where a decision's rationale lives only in an unbacked note, this history quotes it rather than merely pointing at it.

---

# Part I — Origins (pre-alpha.1)

*This prologue is context, not a version entry: it is the design Memoria inherited on day one of alpha.1. Sources: the researcher's origin notes ([researcher-notes.md](researcher-notes.md)); the pre-alpha.1 Drive "Old Skeleton" snapshot dated 2026-05-29 ([sources/old-skeleton/](sources/old-skeleton/)); and the alpha.11 design's own genesis account.*

## The goal it started from

Memoria began with one aim: **integrate rigorous research practices into a Karpathy-style "LLM wiki."** Its genesis is the crossing of two ideas the design docs name explicitly — **Andrej Karpathy's LLM-Wiki pattern** (an agent that *compiles* raw sources into a persistent, interlinked markdown wiki that grows with use, instead of retrieving from scratch each query) and **Elena Razlogova's *Doing History with Zotero and Obsidian*** (a working research methodology). The alpha.11 design later crystallized the distinction: *"Karpathy's LLM wiki is an LLM-driven knowledge **base**; Memoria is an LLM-driven knowledge **production methodology** — Razlogova's."*

The pre-alpha.1 "Old Skeleton" `vision.md` states the founding thesis that survives, in some form, to this day:

> **Maintaining a knowledge base is a bookkeeping problem, not an intelligence problem.** Humans are excellent at recognizing valuable sources and forming original arguments; they are poor at consistently updating summaries, patching links, filing answers, and running structural health checks. Make the agent narrower and more reliable, and let the human do the irreducibly judgment-laden work.

The intellectual stack was a four-way synthesis: **Karpathy** (agent-as-compiler), **Luhmann's Zettelkasten** (atomicity, explicit linking, note-type distinction — fleeting / literature / permanent), **Bush's Memex** (associations as first-class objects), and a survey of ~37 contemporary AI-research systems (from which it borrowed stage-gated pipelines, thin-control-over-thick-state, explicit agent roles, structured handoffs, and persistent knowledge graphs).

## The three tool bets — and the admission that they were unexamined

Three tools were adopted at the outset, each for a specific reason:

- **Obsidian** as the vault/UI — chosen for its popularity and its markdown-plus-frontmatter substrate.
- **Hermes** (Nous Research's self-improving agent, with a built-in learning loop) as the LLM runtime — *"Memoria is what you keep; Hermes is who moves things."*
- **Zotero** (with Better BibTeX) as the bibliographic backbone.

The researcher's own notes are unusually candid that these were **defaults adopted without evaluating fit** — the tension that this entire history is, in effect, the story of confronting:

> *"Hermes offered the necessary infrastructure, but we adopted it without evaluating whether it was the best fit."* Unasked: is the Hermes **Kanban board** suitable (it enforces a rigid predefined structure, but Memoria needs multiple workflows and actors)? Are Hermes **profiles** the right LLM-control mechanism (should all librarian tasks use the same model)? Later: *"Obsidian… does not appear to be the best option for a structured knowledge graph,"* and *"we did not conceptualize Memoria as an application or implement an appropriate agentic application stack."*

Two external frameworks that would later shape the design were noted as *not* adopted at this stage: the **ARD spec** and Google Cloud's **OKF (Open Knowledge Format) spec**.

## The Old Skeleton design (what alpha.1 inherited)

The 2026-05-29 snapshot documents a mature design already in place before the first tagged release:

- **A three-layer model:** the **board (Hermes Kanban) = control plane**, the **workers (Hermes profiles) = execution layer**, and the **vault (Obsidian folders) = durable store** — bound by "thin control over thick state" (orchestrator and workers carry minimal context; durable knowledge lives in files).
- **Seven specialist Hermes profiles**, each with narrow permissions and a clear exit condition (explicitly avoiding "one model does everything"). *The exact roster evolved* — the Old Skeleton names coder/writer/socratic/mapper/librarian/verifier/cmdr; by alpha.1 it was co-pi/engineer/librarian/peer-reviewer/writer/retriever-scout and one more.
- **A structurally blocking human review gate:** a card cannot promote until the human sets `review_status: approved` — positioned deliberately against the surveyed autonomous-research systems, whose LLM reviewers only advise.
- **An L3-with-a-ceiling autonomy posture** (Chen 2026's taxonomy): profiles execute multi-step unattended *within a card*, but the human sets strategy and gates promotion; L4/L5 are refused structurally because "synthesis correctness is not scalar and synthesis changes are not reversible." Framed as *"vibe researching made durable (the vault) and gated (blocking review)."*
- **Folders encode lifecycle stage, not subject** — the original scheme used *numbered lifecycle folders* (`20-sources/01-papers/`, `30-synthesis/01-claims/`, `10-inbox/02-answers/`); topics live in frontmatter and links, never in folder paths (a Zettelkasten inheritance — "Luhmann's slip-box had no subject folders").
- **~15 typed notes** with lifecycles, a controlled-vocabulary frontmatter schema, wikilinks + MOCs, and **21 ADRs** (Diátaxis mode declared per-file in frontmatter).

The researcher's notes then describe elaborating this into a **seven-layer architecture** — L1 the human/PI, L2 the Obsidian workspace, L3 the co-PI (the permanent ACP-pane agent with the full Hermes learning loop), L4 the tasks layer (ephemeral profiles + Kanban + cards), L5 the MCP server(s) (the sandbox boundary), L6 the engines (deterministic bookkeeping/maintenance), L7 the vault — *"decisions flow top-down, information flows bottom-up."*

## The unresolved tension that drives everything after

The origin notes name the flaw that the alpha line spends its whole length working out:

> *"Layer 7, the vault, evolved into a mix of the original notes and additional data repositories, leading to a lack of clarity. This approach prevented us from selecting optimal solutions for specific problems."*

That is the through-line of this history: an inherited, tool-shaped skeleton (Hermes-Kanban + Obsidian-vault + per-item human gate + a vault that fused store-of-record, authoring view, and safety boundary) is progressively examined, measured against a 401-paper literature base, and re-derived from first principles — culminating in the **alpha.11 clean-slate reset** ("direction not authorship / traceability not approval") and the **alpha.15 standalone-engine + four-type + quarantine-and-verify cut**. The rest of this document traces that arc, version by version.

---

# Part II — The full alpha.1 design (baseline)

*Reconstructed from the tree at the alpha.1 release commit `0e9ed9dd` ("split 0.1.0 → 0.1.0-alpha.1", 2026-06-14). Four facets: the vault & knowledge model; profiles, SOUL & the Hermes runtime; the write gate, policy engine & provenance; and the pipeline, discovery, evaluation, distribution & ADR landscape.*
