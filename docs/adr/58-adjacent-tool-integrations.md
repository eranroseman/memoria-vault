---
topic: decisions
id: 58
title: Adjacent tool integrations and added surfaces
status: deferred
nav_exclude: true
date_proposed: 2026-06-11
date_resolved:
assumes: [40, 32]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 58
---

# ADR-58: Adjacent tool integrations and added surfaces

## Context

Memoria's operator surfaces — Obsidian, in-vault dashboards, CLI, Telegram, the
REST API — cover the daily path, but several capabilities would connect the vault
to external tools or add narrow new surfaces. Each is shaped and credible on its own
terms yet none clears the bar to adopt now: each adds an external dependency, a
maintenance liability, or a second place to act on content, in exchange for
convenience the existing surfaces already approximate. This ADR records the
forward-looking ones together so the felt need is detectable per release rather
than re-discovered. The read-only Obsidian Inspector idea — a sidebar pane exposing
board counts, WIP depth, recent audit entries, and the Linter verdict band from
inside Obsidian — is recorded under [ADR-40](40-admin-gui-surface.md) as an adjacent
GUI surface and is not duplicated here.

## Decision

Memoria keeps these four integrations **deferred** — shape settled, scheduling parked —
and adopts none until its own trigger fires:

- **Todoist gap-card mirroring.** When the Peer-reviewer creates a gap card in
  `inbox/` (a failed claim-trace for Librarian to fill), mirror it
  as a Todoist task so it surfaces in the human's existing task surface. Adds an
  external dependency and a Todoist API credential in `.env`.
- **Open-design deliverable-rendering agent.** An external rendering agent
  (open-design pattern) takes a Pandoc-exported Markdown deliverable, applies the
  vault's `.memoria/design-system.md`, and produces polished output (slide decks,
  designed PDFs, web pages). The Engineer scaffolds the handoff; the agent renders; the
  human reviews. The handoff contract remains open design.
- **Static-HTML admin reports.** Snapshot reports (board state, Linter verdict
  summary, metrics) rendered to static HTML by the Linter on a weekly schedule and
  stored in `system/reports/`, for retrospective review or sharing a
  health snapshot without opening Obsidian. The leading candidate renderer is
  [Quartz](https://github.com/jackyzha0/quartz) — a static-site generator
  purpose-built for Obsidian/Roam vaults (full-text search, graph, backlinks) — which
  is also the natural downstream renderer for the open-design deliverable flow above
  (publishing `50-deliverables/` or a garden view) rather than a competing system.
  Surfaced by the [#194](https://github.com/eranroseman/memoria-vault/issues/194)
  comparative survey.
- **Literate code-note (weave + tangle).** A `code-note` interleaving prose and
  executable code in one file, with the Linter checking that code and prose
  description haven't drifted — a drift-detected research notebook for computational
  methods.

External access for any of these flows over the policy MCP per
[ADR-32](32-external-access-over-mcp.md); none becomes a new un-gated write surface.

## Consequences

- Recording the set keeps each integration's shape and trigger legible so a cadence
  review can judge readiness rather than re-derive the design.
- Mirroring (Todoist) does not fix a review-capacity problem: if Todoist items go
  unworked, the vault's gap cards stagnate regardless.
- The open-design handoff contract is unspecified; adopting it requires designing the
  Engineer→agent interface, not just wiring an existing one.
- Each adopted integration adds an external dependency, credential, or scheduled job
  to maintain — cost paid only once the trigger justifies it.

## When this matters

Per-release context, not gates:

- **Todoist mirroring:** the human uses Todoist as their primary task surface *and*
  gap cards regularly sit unactioned for more than two weeks.
- **Open-design rendering:** the human needs a deliverable format (presentation,
  designed PDF) plain Pandoc doesn't produce *and* is willing to maintain a
  design-system file.
- **Static-HTML reports:** the human wants to share or archive periodic health
  snapshots, or finds the Dataview dashboards too slow for a quick weekly review.
- **Literate code-note:** the human is writing code-notes for computational methods
  where code and prose description regularly diverge and the divergence is costly to
  catch manually.

## Related

- **Related decisions / Depends on:** [ADR-40 (admin/forensic GUI surface)](40-admin-gui-surface.md) (records the read-only Obsidian Inspector idea), [ADR-32 (external access over MCP)](32-external-access-over-mcp.md) (the gated path any external integration takes)
- **Tracking issue:** [#408](https://github.com/eranroseman/memoria-vault/issues/408) — revisit at each release cadence.
