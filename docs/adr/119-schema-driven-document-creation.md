---
topic: decisions
id: 119
title: "Schema-driven document creation: the schema generates the form and the template, not just validates them"
status: accepted
date_proposed: 2026-06-23
date_resolved: 2026-06-23
assumes: [47, 49, 116, 117]
supersedes: []
superseded_by: []
---

# ADR-119: Schema-driven document creation

## Context

Creating a typed document has **three concerns**: the **contract** (type, required fields,
enums, defaults, folder, lifecycle — owned by the schema), the **input** (the values a human
or an agent supplies), and the **shape** (the body structure that encodes how to think about
the note kind — the template body).

Today a type's field list is defined in **three** hand-synced places: the schema
(`types/<t>.yaml`), the template's frontmatter (`system/templates/<t>.md`), and the Modal Form
(`memoria-<t>-capture`). The schema is "authoritative" only for *validation* — the template
and the form **re-encode** it. This is the one corner that breaks Memoria's single-source-of-truth
rule (the linter, installer, policy MCP, and Bases all *read* the schema; only the form and
template *duplicate* it), and the drift is already visible — the source form adds a `summary`
field and drops `links` relative to `source.yaml`.

Best practice and Memoria's own philosophy converge on the same fix: stop hand-syncing three
copies; **derive the form and the template from the schema.**

## Decision

Promote the schema from a passive validator to the **generator** everything is derived from.

1. **The schema is the single source for the contract — and gains creation metadata.** Per
   field, beyond type/enum/default, it declares `creation: required | optional` (the creation
   form asks only for creation-required fields; the rest are filled later during shaping) and a
   `label` + `description` (for the generated form, especially the jargon fields — CEBM evidence
   levels, FINER, PICO).
2. **The form is generated from the schema, not authored.** A build step emits the Modal Form
   definition from the type schema: creation-required fields → inputs, enums → selects, defaults
   prefilled, labels/descriptions attached. The form cannot drift because it is compiled.
   Validation happens **at submit** against the schema; the Linter becomes the backstop, not the
   primary gate.
3. **The template splits — frontmatter generated, body authored.** The frontmatter block is
   generated from the schema's defaults; the **only hand-authored per-type artifact is the body
   scaffold** — the thinking-shape sections, with **fading prompts that are easy to delete**
   (hints in comments or `[!hint]` callouts, removed as the section is filled). The full template =
   generated frontmatter + authored body scaffold.
4. **One creation engine, two input adapters.** A single `create(type, inputs)` loads the schema
   spec, applies defaults, merges inputs, validates at creation, prepends the generated
   frontmatter to the body scaffold, and writes to the schema's folder. **Both the human form and
   the agent writers (`inbox.py`, ingest) call it** — unifying the two creation tracks. This also
   explains why 16 types have a template but no form: they are agent-created through the *same*
   engine with a different input adapter.

## Consequences

- **No form/frontmatter drift** — both are generated from the schema. **Field minimization +
  progressive enrichment** via `creation: required`. **Validate-at-input** (enum selects, required
  checks); the Linter is the backstop. **Fading scaffolding** in the body. **Labels/descriptions**
  carried in the schema.
- Phasing (so it is not a big-bang):
  1. **Drift test (now).** Assert each form's creation-required fields equal the schema's, and
     form enum fields equal the schema's enums. Catches drift immediately; no architecture change.
  2. **Generate the artifacts.** Add the `creation`/`label` annotations; generate the Modal Form
     definitions and the template frontmatter from the schema (a generator like `gen_adr_index`);
     reduce each template to its authored body scaffold.
  3. **Unify the engine.** Route the human form and the agent writers through one
     `create(type, inputs)`; trim the project form (derive `slug`, default `question_version`,
     defer non-essential PICO/FINER fields to shaping).
- Migration touches: the schema files (annotations), a new generator, the Modal Forms config
  (becomes generated, not hand-edited), the templates (split into body scaffolds), the agent
  writers (`inbox.py` / ingest, routed through the engine), and the test suite.

## Alternatives considered

- **Keep three hand-synced copies (status quo).** Rejected: guarantees the drift this decision
  removes.
- **Drift test only, no generation.** This is the pragmatic Phase 1, but it merely *detects*
  divergence; it does not reach single-source. Generation is the target.
- **Put the body scaffold in the YAML schema.** Rejected: a markdown body shape is best authored
  as markdown — keep it a separate body-scaffold file the engine combines with generated
  frontmatter.
- **Adopt an external schema-form library.** Rejected: out-of-Obsidian and overkill; Modal Forms
  plus a small in-repo generator is sufficient and native.

## Related

- **Refines:** [ADR-116](116-obsidian-surface-architecture.md) (the single-definition principle —
  applied here to document *creation*, not just views), [ADR-117](117-type-naming-scheme.md) (the
  document-type vocabulary).
- **Depends on:** [ADR-47](47-type-first-category-folders.md) (the type→folder schema map),
  [ADR-49](49-catalog-in-bases-linter-monitor.md) (the schema as the authoritative contract the
  Linter and Bases read).
- **Source discussion:** the alpha.8 templates and form-creation clean-slate review.
