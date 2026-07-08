---
title: Why the write half is bounded
parent: Boundaries
grand_parent: Design
nav_order: 5
---

# Why the write half is bounded

Memoria writes plain files first: `outline.md`, `draft.md`, and unchecked notes.
That boundary keeps synthesis useful without making the engine a truth oracle.
The alpha.17 write loop deliberately shipped as text output only: project slice,
outline, draft, verification, export, and selected passage back into the
knowledge graph.

## Why files first

The write half has to help the PI move from checked knowledge to a deliverable
without hiding the argument. Plain files are the smallest surface that does that:
the PI can read the outline, edit draft order, inspect evidence markers, diff the
change, and keep the result if Memoria disappears.

A hidden agent workspace would be faster to demo and worse to trust. The
artifact that matters is the one the PI can open, review, cite, and export.

## What the engine may do

The engine can propose a slice, compose draft text, verify evidence markers,
and refuse unsafe export. It does not decide that a claim is true, promote a
draft passage to checked knowledge, run analysis code, or hide uncertainty
behind a score.

That is the important boundary: the engine may make work visible and repeatable,
but the PI still decides what belongs in the argument and what can become
checked knowledge. Exact file names and command contracts live in the project
how-to guides and reference pages.

## Failure modes this prevents

**Draft prose becoming canon.** A polished paragraph can sound more settled
than the evidence warrants. Promotion therefore creates an unchecked note
proposal; checked knowledge still passes through the normal write boundary.

**Evidence-free export.** Export is useful only when internal markers resolve to
source-backed citations. If verification finds missing or review-required
evidence, the export refuses with reasons.

**Code output masquerading as analysis.** Computed warrants can prove that an
output came from a recorded run, but they do not make the research claim true.
Code execution stays behind its own fail-closed gate.

**A score replacing review.** Broad writability scoring is out of scope. The
shipped signals are concrete file state, evidence findings, and explicit
refusal.

## What this means for the user

You get help turning checked notes into a draft, but the handoff stays visible:
`outline.md` shows what the draft uses, `draft.md` shows the prose and evidence
markers, verification names what blocks export, and promoted passages re-enter
the vault as unchecked notes. The system helps write; it does not decide what
you believe.

---

## Related

- The cycle this completes: [The knowledge cycle](../../explanation/knowledge/knowledge-cycle.md)
- The project slice file: [Project slice](../../explanation/knowledge/project-slice.md)
- The draft posture: [The Writer](../../explanation/execution/operation-postures/writer.md)
- Export behavior: [Export routes and formats](../../reference/export.md)
- The checkpoint that shipped the loop: [alpha.17 WRITE half](https://github.com/eranroseman/memoria-vault/blob/main/design-history/17-alpha.17.md)
