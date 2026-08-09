---
title: What checked means
parent: Knowledge
grand_parent: Explanation
nav_order: 2
---

# What checked means

**Checked** is a runtime verdict about whether a Concept or catalog Work may be
consumed by checked-only readers. It is not a verdict that the content is true
or that the PI approves it. The canonical definition is [Check
status](../../reference/data-model/glossary.md#check-status); this page explains
what that definition means at the read boundary.

---

## One closed verdict set

`check_status` has exactly three values: `unchecked`, `checked`, and
`quarantined`. It lives in SQLite and read-API responses, not in Concept
frontmatter. A missing verdict is `unchecked`, so a reader never infers a
checked state from a file's presence or its prose.

- **Unchecked** material exists but is not eligible for checked-only
  consumption.
- **Checked** material is eligible after its applicable declared checks pass.
- **Quarantined** material is held out of ordinary consumption because the
  runtime observed a write or state it cannot accept.

That eligibility is deliberately narrower than a knowledge claim. It does not
establish truth, citation or provenance completeness, a PI disposition or OKF
confirmation, evidence resolution, or export readiness. Those are separate
facts with their own records and gates. A PI-operated `mark-checked` route can
record some of them together for a particular write, but their co-occurrence
does not make them synonyms.

## The checked-file read barrier

Checked-only file readers fail closed. They refuse a file when the verdict is
absent or not `checked`; when its output record is missing, not file-backed, or
not checked; when the output was not materialized; or when the current content
hash does not match the recorded hash. A detected missing record or changed
file can enqueue observation work, but it does not make the file readable in
the meantime.

The same boundary keeps checked retrieval and Ask from silently using stale or
untracked material. See [Search](../../reference/pipelines-and-io/search.md)
for its reader-facing behavior and [Why the review gate is
structural](../rationale/boundaries/why-review-gate-is-structural.md) for the
write-path rationale.

## Checking is not every kind of promotion

**Checking** runs the declared checks. For a staged Concept,
`stage_concept()` records an unchecked output, and the trusted writer's
`promote_checked()` transition makes it readable after the required checks pass;
it does not resolve evidence grounds. `mark_checked(..., judgment=...)` instead re-records a live
Concept's verdict; its explicit `judgment` argument records whether that call
relays a PI acceptance or performs a mechanical rewrite.

This is distinct from project passage promotion. `promote_draft_passage()`
stages and materializes a selected draft passage as a new **unchecked** note
for later review. It does not promote the note to checked knowledge. See
[Promotion and the write boundary](promotion-and-gated-zones.md) for the
broader write-path model.

Catalog Works use the same verdict vocabulary: `set_catalog_check_status()`
keeps the catalog row and the read/retrieval mirrors synchronized. It still
does not turn a Work into a cited claim, resolve evidence in a project, or make
a draft exportable.

## Related

- Canonical term: [Check status](../../reference/data-model/glossary.md#check-status)
- Field boundary: [Frontmatter fields](../../reference/data-model/frontmatter.md#verdict-state-is-not-frontmatter)
- Read behavior: [Search](../../reference/pipelines-and-io/search.md)
- Promotion behavior: [Promotion and the write boundary](promotion-and-gated-zones.md)
