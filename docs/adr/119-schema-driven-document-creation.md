---
topic: decisions
id: 119
title: "Schema-driven documents: the type schema is the complete declarative contract that validates, generates, and is the single source"
nav_exclude: true
status: accepted
date_proposed: 2026-06-23
date_resolved: 2026-06-23
assumes: [47, 49, 52, 116, 117]
supersedes: []
superseded_by: []
---

# ADR-119: The type schema is the complete declarative contract

## Context

Validating *and* creating a typed document touches **eight** concerns: identity & placement,
fields, controlled vocabulary, the state model, the typed-edge graph, cross-field/referential
invariants, generation metadata (labels, defaults, which fields a creation form asks for), and
evolution.

Today the type schema (`types/<t>.yaml`) carries only **fields + enums**. Everything else is
scattered and hand-synced:

| Concern | Where it lives today |
| --- | --- |
| placement / gating | split between `folders.yaml` and the schema's `category`/`gated` |
| state transitions | ADR prose + detector code — *not declared anywhere* |
| graph / edges | `links: map` (untyped); the edge vocabulary ([ADR-52](52-links-vs-relationships.md)) is convention |
| invariants | **hand-coded in the Linter detectors** (`thesis`→`promoted_at`, `claim`→`sources`, …) |
| defaults | in the **templates**, not the schema |
| labels / creation-required | **nowhere** |

So the "schema" is a *fragment* of the contract. The consequences compound: the Linter
hard-codes per-type knowledge it shouldn't have to; the template frontmatter and the Modal Form
**re-encode the field list** (three hand-synced copies — the source form already drifted, adding
`summary` and dropping `links`); and adding a type or a rule means editing **four** places
(the YAML, a detector in code, a template, and `folders.yaml`).

Best practice and Memoria's own single-source-of-truth philosophy converge on the same fix:
stop scattering and duplicating the contract — make the schema **complete and declarative**, and
derive everything else from it.

A per-type audit of all 26 schemas confirms the diagnosis. Alignment is mostly strong — the inbox
honesty-card set (`candidate`/`gap`/`flag`/`alert`/`work-prompt`) and `claim`/`source`/`thesis` are
exemplary — and the *systematic* gaps are exactly this fragment problem: only `project`, `thesis`,
and `code-note` declare their `initial_lifecycle`/promotion gate (the other 23 leave the state
machine implicit); `required_any` is declared in-schema while the conditional and referential rules
(`thesis` `current` → `promoted_at`, `claim.sources` → citekeys, `source.entity` → a Catalog
wikilink) live in the detectors; and `project` is over-required at creation. The audit also surfaced
a handful of concrete per-type fixes, folded into the decision below.

A parallel audit of the four human forms points the same way. They are already ahead of the schema
on validation — every enum is a select, lists are multi-select fields, and `entity`/`sources` use
note-pickers that validate references against real Catalog notes (`fleeting` and `claim` are
exemplary). The telling case is `source_type`: the form renders it as a **required five-value
select** (`paper · dataset · repository · web-page · report`) while the schema declares it an
**optional free `str`** — the controlled vocabulary lives in the *form*, not the *schema*, which is
exactly the inversion this decision removes (once the form is generated, a `str` field loses the
select). The form audit's remaining fixes are folded in below.

## Decision

Promote the type schema from a partial field-list-plus-validator to the **complete declarative
contract** that everything executes or generates from.

### 1. The schema declares the whole contract

One type definition holds all eight concerns:

- **Fields as first-class specs** — `{type, required, default, label, description,
  creation: required|optional, constraints}` — where `creation` may be **conditional on another
  field** (e.g. ask for the provisional thesis only when `output_mode == thesis`), with value
  types richer than `str/list/map`:
  `link(endpoint-type)`, `citekey`, `date`, `enum(ref)`, `list<T>`, and `edges(edge-vocab)` for
  the graph.
- **Placement & gating** — `folder`, `gated` (folding `folders.yaml`'s per-type map in).
- **State machine** — `lifecycle: {states, transitions, gated-transitions}`: the universal chain
  projected to this type's subset, with the review-gated transitions declared (not inferred in
  detectors).
- **Typed edges** — reference the shared edge vocabulary ([ADR-52](52-links-vs-relationships.md)) with
  declared endpoint types, so the graph is typed *in the schema*.
- **Invariants as declarative rules** — conditional requirements
  (`when lifecycle == current, require promoted_at`) and referential rules
  (`sources: each is a citekey resolving to a paper`), replacing the hand-coded detector rules.

### 2. The Linter becomes a generic engine

It **executes the declared** field/enum/invariant/transition/placement rules — no per-type code.
Adding a type or a rule is a *schema edit*, not a detector edit. Declarative beats imperative:
the detector engine runs the contract; it doesn't *contain* it.

### 3. Forms, templates, the folder map, and the reference docs are generated from the schema

- **The Modal Form is generated** — creation-required fields → inputs, enums → selects, defaults
  prefilled, labels/descriptions attached. Validation happens **at submit**; the Linter is the
  backstop, not the primary gate.
- **The template splits** — frontmatter generated from the schema's defaults; the **only
  hand-authored per-type artifact is the body scaffold** (the thinking-shape sections, with
  fading prompts that are easy to delete — hints in comments or `[!hint]` callouts).
- **`folders.yaml` and the reference docs** (`note-types.md`, `frontmatter.md`) are generated,
  not hand-mirrored.

### 4. One creation engine, two input adapters

A single `create(type, inputs)` loads the schema spec, applies defaults, merges inputs, validates
at creation, prepends the generated frontmatter to the body scaffold, and writes to the schema's
folder. **Both the human form and the agent writers (`inbox.py`, ingest) call it** — unifying the
two creation tracks. This also explains why 16 types have a template but no form: they are
agent-created through the *same* engine with a different input adapter.

### 5. Format

Use an **enriched native DSL** — extend the current YAML with field-objects plus
`transitions`/`edges`/`constraints` blocks — structured so the field layer can be **projected to
JSON Schema later** if external tooling (IDE autocomplete, form-generation libraries) ever
justifies it. The decisive wins — completeness and the generic engine — are *format-independent*;
JSON Schema models a document's internal shape, not the vault's placement/graph/referential layer,
so a full migration would buy standard tooling for the easy half while the hard half stayed custom.

### 6. Per-type and per-form cleanups (from the audit)

Concrete fixes the schema and form audits surfaced, folded into the phases below:

- **Drop `index`.** Its schema is title-only — it expresses none of its register purpose — it has
  no creation path, and the register function (a list of hubs) is already the `hubs.base#Hubs index`
  view. It is the one type whose schema simply does not match its purpose; remove the type, the
  template, the schema, and the `notes/indexes/` folder. (This is the only fix *outside* the
  schema-as-contract work — a type-roster decision, recorded here.)
- **Make `source_type` an enum.** A free `str` today but controlled vocabulary in practice
  (paper · dataset · repository · web-page · report); the form *already* renders it as a five-value
  select, so generating the form from a `str` schema would **lose** the constraint — the enum must
  move into the schema. *(Phase 2.)*
- **Carry field `description` in the schema, not just `label`.** The `creation` block should hold a
  per-field description alongside the label, generated into the form as inline help. The `source`
  and `project` forms have none today — and they carry the most jargon (CEBM grades, PICO, FINER),
  where help text matters most. *(Phase 2.)*
- **Declare `initial_lifecycle` and gated transitions uniformly** — three types declare them, 23 do
  not; close the inconsistency as part of the state-machine work. *(Phase 3.)*
- **Document the fine distinctions the schemas already encode** — `flag` vs `alert` (a pointed
  finding with a verdict + target, vs a looser standing warning) and `candidate` vs `gap`
  (accept-this vs fill-this). They are correct in the schemas but undocumented; add the prose (and,
  for `candidate`/`gap`, consider one `proposal` type with a subtype — an ADR-51 question, not a
  schema fault).
- **`project` form fixes.** Derive `slug`, default `question_version`, and defer PICO/FINER to
  shaping. Make **`scope_topics` `creation: optional`** — required before the *project gate* runs,
  not at the first form: a project's scope sharpens while reading, so blocking on it fights
  start-then-shape (keep it mandatory only under a strict "no unbounded projects" rule). **Restore
  the full five-criterion FINER** — the form drops Interesting and Ethical, so projects never
  capture the full answerability lens. And add a **conditional creation field**: in **thesis** mode
  the form asks for the one-sentence **provisional thesis**; in **survey** mode it does not — keyed
  on `output_mode`, which *is* the thesis/survey distinction (thesis starts with a provisional
  answer, survey starts open). This also **matches the tutorial** (`tutorials/01-see-what-you-are-building.md`), which
  already describes the thesis prompt the form currently omits — so it is the *form* that catches up,
  not the tutorial that changes. *(Phase 5.)*

## Consequences

- **Single source, no drift** — the contract is declared once; the Linter executes it, and the
  forms, templates, folder map, and docs are generated from it.
- **Declarative validation** — adding a type or invariant is a schema edit; the detector engine is
  generic.
- **Field minimization + progressive enrichment** (`creation`), **validate-at-input** (enum
  selects, required checks), **fading scaffolding**, and **labels/descriptions** all fall out for
  free.
- **Phasing** (sequencing lives in the milestone/issues):
  1. **Move invariants into the schema; make the detector engine generic** — replace hand-coded
     per-type rules with declared `constraints` the engine runs. *(Biggest correctness win.)*
  2. **Fold defaults + labels + `creation` in** — removes the template-frontmatter duplication.
  3. **Declare the state machine + typed edges** — remove implicit lifecycle/graph knowledge from
     detectors.
  4. **Fold `folders.yaml`'s per-type map into the type definitions.**
  5. **Generate the forms and template frontmatter; reduce templates to body scaffolds; route the
     human form and agent writers through one `create()`** — the creation pipeline. Trim the
     project form (derive `slug`, default `question_version`, defer non-essential PICO/FINER).
  6. **(Optional) project the field layer to JSON Schema** — only if external tooling pays.
  - A cheap floor for Phase 5: a **drift test** asserting each form's creation-required fields and
    enums equal the schema's — catches divergence immediately, no architecture change.
- Migration touches: the schema files (enriched), the Linter (generic engine), `folders.yaml`
  (folded/generated), the Modal Forms config (generated), the templates (split to body scaffolds),
  the agent writers (routed through the engine), `note-types.md`/`frontmatter.md` (generated), and
  the test suite.

## Alternatives considered

- **Keep fields-only schemas + per-type detector code + hand-synced templates/forms (status quo).**
  Rejected: the contract stays scattered across four places and the creation layer keeps drifting.
- **Adopt full JSON Schema as the format.** Standard and well-tooled, but it models a document's
  internal shape, not the vault's placement/graph/referential layer — so a custom layer survives
  regardless — and it is verbose. Better deferred to a *projection* of the field slice (Phase 6).
- **Model + projections** (author types in a rich internal model, emit JSON Schema / forms / docs).
  The strongest single-source, but the most upfront engineering; the enriched DSL reaches most of
  the benefit at lower cost, and can grow into this.
- **Put the body scaffold in the YAML schema.** Rejected: a markdown body shape is best authored
  as markdown — keep it a separate body-scaffold file the engine combines with generated
  frontmatter.

## Related

- **Refines:** [ADR-116](116-obsidian-surface-architecture.md) (the single-definition principle —
  applied here to document validation *and* creation), [ADR-117](117-type-naming-scheme.md) (the
  document-type vocabulary).
- **Depends on:** [ADR-47](47-type-first-category-folders.md) (the type→folder map),
  [ADR-49](49-catalog-in-bases-linter-monitor.md) (the schema as the authoritative contract the
  Linter and Bases read), [ADR-52](52-links-vs-relationships.md) (the typed-edge vocabulary the graph
  declares against).
- **Source discussion:** the alpha.8 schemas, templates, and form-creation clean-slate review.
