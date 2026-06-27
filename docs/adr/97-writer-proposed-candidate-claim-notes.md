---
topic: decisions
id: 97
title: Writer-proposed candidate claim notes
nav_exclude: true
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [21, 51]
supersedes: [61]
superseded_by: []
---

# ADR-97: Writer-proposed candidate claim notes

## Context

After discussion or distillation, the Writer may be able to propose candidate
claim notes. This is judgment-adjacent: fluent proposals can anchor the human or
encourage rubber-stamping, so proposals must not become canonical claims without
PI authorship.

## Proposal

Memoria may let the Writer propose candidate claim notes as Inbox cards, each with
source provenance and passage evidence. The policy MCP continues to deny agent
writes to `notes/claims/`; the human edits, authors, or discards.

## Consequences

- Reduces transcription effort when claim comprehension is already done.
- Increases rubber-stamping and framing-capture risk.
- Requires measurement of accept-unedited rate as a warning signal, not a success
  metric.

## When this matters

`discuss` and `distill` are stable, and the felt bottleneck is transcribing claims
rather than comprehending them.

## Alternatives considered

**Let Writer write canonical claims.** Rejected because ADR-21 and the review gate
reserve canonical claim authorship for the PI.

**Never propose claims.** Safer, but leaves repetitive transcription work entirely
manual even when provenance is clear.

## Related

- **Supersedes:** [ADR-61](61-nightly-discovery-loop.md).
- **Related decisions / Depends on:** [ADR-21](21-l3-autonomy-ceiling.md), [ADR-51](51-inbox-category-and-honesty-card.md).
- **Tracking issue:** [#710](https://github.com/eranroseman/memoria-vault/issues/710).
