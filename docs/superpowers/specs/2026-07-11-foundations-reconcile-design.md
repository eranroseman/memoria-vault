# Foundations reconcile — design (2026-07-11)

## Context

The canonical product doctrine (`docs/superpowers/product-statement.md`, composed
2026-07-09) is an unpublished working record. Most of it is already published —
and better shaped for readers — across three pages under
`docs/explanation/rationale/foundations/`: `what-memoria-is.md`,
`intellectual-foundations.md`, and `design-principles.md`. So the goal is **not**
a new page (that would duplicate `what-memoria-is.md`, which the repo's no-mirror
principle forbids). The goal is to fold the product statement's genuine *deltas*
into those existing pages, then retire the working record.

The deltas that are canonical but unpublished: the **four pillars** framing with
**Toulmin** (logic) and **autoresearch** (self-improvement); the **Open Knowledge
Format** bundle constitution; and two design **axioms** (grounding-not-truth,
origin-blind consequences) plus the master pattern.

## Changes

### 1. `intellectual-foundations.md` — name the four pillars; fill two gaps
- Reframe the load-bearing structure as **four pillars**: LLM-Wiki (inflow),
  Zettelkasten (topology), **Toulmin** (logic), **autoresearch** (self-improvement).
- **Fold Memex into the LLM-Wiki section** as its intellectual antecedent (Bush's
  1945 private, curated, associative-trail store; the maintenance problem he
  couldn't solve, which the LLM now handles). Remove the standalone "Bush's Memex"
  section; keep the associative-trails idea where it belongs (the link graph).
- **Add Toulmin**: the six components (Claim, Grounds, Warrant, Backing, Qualifier,
  Rebuttal) as the *basis of the knowledge graph* — the roles make consequence
  propagation typed.
- **Add autoresearch**: Karpathy's fixed-harness / one-metric / keep-discard /
  overnight loop, applied to Memoria's *own instruments*, never the knowledge they
  assess.
- Update the "synthesis" section and the opener to reflect the four pillars.

### 2. `what-memoria-is.md` — add the OKF bundle constitution
- One section: the vault (excluding `.memoria/`) is one self-contained **Open
  Knowledge Format** Knowledge Bundle — readable by anything (`cat` works); each
  project is a nested, detachable bundle; `.memoria/` is engine-space (trust state,
  never the knowledge). Grounds the existing "three spaces" in the bundle model.

### 3. `design-principles.md` — add two axioms + the master pattern
- **11. Grounding, not truth** — no node is judged true/false; the system asserts
  only how a change affects graph integrity; "checked" = checks passed, never a
  truth verdict.
- **12. Origin-blind consequences** — a change's origin (human/machine/LLM) does
  not affect its *epistemic* consequences (flags, demotions, blast radius); write
  and revert *authority* stays origin-gated.
- Name the **master pattern** in the intro: the fluent/judging half of any
  capability stays with the human; the structural/inspectable half goes to the
  engine. Retitle "Ten principles" → "Twelve principles".

### 4. `product-statement.md` — retire in place
- Prepend a "Superseded" note pointing to the three foundations pages; keep it as
  the dated 2026-07-09 working record. Route the **warrant-ontology open question**
  to issue [#1353](https://github.com/eranroseman/memoria-vault/issues/1353) — a
  link, not doctrine.

### 5. Glossary + spelling
- Add new terms to `docs/reference/data-model/glossary.md`: Open Knowledge Format
  (OKF), Knowledge Bundle, the Toulmin six (Grounds, Warrant, Backing, Qualifier,
  Rebuttal — Claim already covered), autoresearch.
- Add jargon to `project-words.txt` as `cspell` requires (e.g. `okf`, `toulmin`,
  `autoresearch`, `rebuttal`, `qualifier`).
- Update each touched page's *Related* section for the new/removed sections.

## Non-goals
- No new explanation page (avoids duplicating `what-memoria-is.md`).
- No change to the doctrine itself — only publishing deltas already ratified in
  the product statement.
- No `design-history/` edits (frozen record).

## Success criteria
- `python scripts/verify` green (cspell + markdownlint over the changed docs).
- The four pillars, OKF, both axioms, and the master pattern are published in the
  foundations pages; Memex reads as the LLM-Wiki antecedent, not a separate root.
- `product-statement.md` marked superseded; warrant question links #1353.
- No duplicated content between the foundations pages and the retired statement.
