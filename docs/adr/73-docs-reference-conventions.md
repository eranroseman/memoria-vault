---
topic: decisions
id: 73
title: Documentation references — source links, ADR links, and per-operation Diátaxis split
status: accepted
date_proposed: 2026-06-14
date_resolved: 2026-06-14
assumes: [46]
supersedes: []
superseded_by: []
---

# ADR-73: Documentation references — source links, ADR links, and per-operation Diátaxis split

## Context

The docs site is Jekyll + just-the-docs on GitHub Pages, organized by Diátaxis. Three
recurring defects: relative links from docs into `src/` break on the published site
(`src/` is outside the Jekyll source root, so they 404 at any path depth); stale
`(D41)`-style references point at deleted design docs; and complex subsystems mix
procedural reference with rationale on one page (and even document more than one
subject).

## Decision

1. **Never link into `src/` from a published page.** Reference a source file as an
   **inline-code path** (`` `src/.memoria/…` ``) by default; use an **absolute,
   tag-pinned** `https://github.com/eranroseman/memoria-vault/blob/<tag>/…` URL only
   when a click genuinely adds value. `docs-doctor` blocks published→`src/` relative
   links via `check_site_local_links`.
2. **ADR references stay out of tutorial / how-to / reference body text and
   subheadings.** They are allowed inline within **explanation** pages and in an
   optional per-page footer **"Decisions"** section, always as **title-text links** —
   never bare `(ADR-NN)` codes. `docs-doctor` enforces the bare `(ADR-NN)` ban;
   the Diátaxis placement rule remains a manual documentation convention.
   Bare `(D##)` references are purged from published user-facing prose, but may
   remain in ADR history where they are part of the decision record.
3. **Complex operations get a procedural reference page and a separate rationale
   explanation page** (Diátaxis "work vs study"), cross-linked with Django's
   "link, don't repeat" discipline so each fact has one home. Simple operations may keep
   a one-paragraph "Why" inline.

## Consequences

- Source references survive the engines→operations rename ([ADR-69](69-operations-layer-naming.md)),
  because inline-code paths and tag-pinned URLs don't depend on the live relative tree.
- Cleaner prose; ADR traceability preserved without clutter.
- Builds on [ADR-12](12-obsidian-linter-reference-only.md) (docs tooling is advisory);
  the new structural rule is enforced by docs-doctor, not obsidian-linter.

## When this matters

alpha.3 (docs hygiene), sequenced **before** the engines→operations code rename so links
aren't pinned to paths about to move.

## Alternatives considered

- **`blob/main` links.** Always current but silently break on rename/delete and drift on
  line anchors; reserved only for "browse this directory" links.
- **Keep relative `src/` links.** They resolve on disk and on github.com but are dead on
  the published site — the defect this ADR removes.

## Related

- **Related decisions / Depends on:** [ADR-46](46-seven-layer-architecture.md),
  [ADR-12](12-obsidian-linter-reference-only.md), [ADR-69](69-operations-layer-naming.md)
- **Implementing issues:** #464 (docs hygiene sweep), #443 (explanation pages describe
  unbuilt behavior)
- **Source discussion:** the alpha.3 research notes (`open-issues-research` Issue 3,
  `naming-and-diataxis-audit` Part 2)
