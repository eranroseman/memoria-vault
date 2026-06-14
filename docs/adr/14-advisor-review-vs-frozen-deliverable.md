---
topic: decisions
id: 14
title: Advisor-review exports are live-citation artifacts, outside the frozen-deliverable contract
status: accepted
date_proposed: 2026-05-30
date_resolved: 2026-05-30
assumes: []
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 14
---

# ADR-14: advisor-review exports are live-citation artifacts, outside the frozen-deliverable contract

## Context

Memoria models a `deliverable` (`50-deliverables/`) as **terminal and frozen** — produced by
re-running Pandoc, never edited in place; if it needs changes you supersede it with a new
draft → export cycle ([Export routes and formats](../reference/export.md),
[Note types](../reference/note-types.md)). The current export path emits one thing: a
static citeproc `.docx` whose citations are frozen text.

This is correct for **final journal submission**. It has no answer for the **advisor-feedback
loop** that dominates the months *before* submission: a PhD student sends drafts to an advisor
who comments and tracks changes in Word/LibreOffice, and that round needs **live, editable
citation fields** (so the advisor can move, add, or restyle references) — exactly what a
frozen static export cannot provide. The predecessor (v1.5) design documented three live-citation
routes (`zotero.lua` Word fields, LibreOffice ODF Scan, Google Docs) and the hybrid
"draft in Obsidian, finish in Word." Memoria carried the static route and dropped the live one,
leaving the frozen-deliverable model implicitly responsible for a job it cannot do.

## Decision

A **deliverable is frozen and is produced by static Pandoc citeproc at submission time only.**
An **advisor-review export** — a live-citation `.docx`/`.odt` carrying editable Zotero fields —
is a **separate, explicitly non-deliverable working artifact.** It does **not** live in
`50-deliverables/`, is not subject to the "never edit in place" rule, and is regenerated from
the same draft whenever a new round is needed. The routes and their failure modes are
documented in [export a draft](../how-to-guides/compose/export-a-draft.md); the
human chooses the target editor **before drafting**.

## Consequences

- The frozen-deliverable invariant is preserved by construction — live, hand-edited Word files
  never masquerade as deliverables, so `50-deliverables/` stays a clean record of what shipped.
- The real PhD workflow (advisor track-changes rounds) is supported instead of silently
  unsupported.
- One more documented export route to maintain (`zotero.lua` / ODF Scan) with real,
  named failure modes (`lpeg` on Windows; first-open `.docx` corruption) — mitigated by the
  "test on a single-citation doc first" guidance in export-targets.
- The human carries a new up-front decision — pick the final editor before drafting — because
  switching Obsidian → Google Docs late forces manual re-insertion of every citation.

## Alternatives considered

**Stretch the frozen-deliverable model to allow in-place edits for advisor rounds.** Rejected:
it destroys the invariant that `50-deliverables/` is terminal and auditable, and conflates a
mutable working file with a shipped artifact.

**Only ever ship static citeproc; tell advisors to comment on frozen text.** Rejected: frozen
citations can't be restyled or moved, and it fights the advisor's native Word/Zotero workflow —
the friction the live route exists to remove.

**Build a Memoria-native live-citation exporter.** Rejected as over-engineering: Zotero +
Better BibTeX + Pandoc already provide the routes; Memoria's job is to document and run them,
not reimplement citation-field injection.

## Related

- **Workflows affected:** [export a draft](../how-to-guides/compose/export-a-draft.md) (companion how-to, added with this ADR), [Export routes and formats](../reference/export.md) (the existing static path)
- **Files affected:** the `deliverable` note type — [Note types](../reference/note-types.md)
- **Profiles:** [Coder](../explanation/profiles/engineer.md) runs the Pandoc mechanics
