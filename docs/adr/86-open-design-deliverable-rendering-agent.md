---
topic: decisions
id: 86
title: Open-design deliverable-rendering agent
nav_exclude: true
status: proposed
date_proposed: 2026-06-19
date_resolved:
assumes: [32]
supersedes: []
superseded_by: []
---

# ADR-86: Open-design deliverable-rendering agent

## Context

Pandoc-style exports cover plain scholarly deliverables, but some outputs need
polished presentation, designed PDF, or web rendering. A rendering agent could
apply Memoria's design system, but that creates a new handoff contract outside the
core vault workflow.

## Proposal

Memoria may add an open-design deliverable-rendering handoff: the Engineer
scaffolds an external rendering request from a Pandoc-exported Markdown
deliverable and `.memoria/design-system.md`; the external agent renders; the human
reviews the final artifact.

## Consequences

- Enables polished formats that plain Pandoc does not produce.
- Requires a maintained design-system file and a clear Engineer-to-renderer
  contract.
- Must keep human review as the acceptance step; generated design output is not
  automatically published.

## When this matters

The human needs a deliverable format such as a presentation or designed PDF that
plain Pandoc cannot produce, and is willing to maintain the design-system file.

## Alternatives considered

**Use Pandoc only.** Lower operational cost, but does not cover designed outputs.

**Build native rendering into Memoria.** Rejected for now because design rendering
is not core research OS behavior and carries a large maintenance surface.

## Related

- **Related decisions / Depends on:** [ADR-32](32-external-access-over-mcp.md).
- **Tracking issue:** [#699](https://github.com/eranroseman/memoria-vault/issues/699).
