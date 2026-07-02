---
topic: decisions
id: 19
title: Agent-proposed hubs (threshold alert and Mapper handoff)
nav_exclude: true
status: superseded
date_proposed: 2026-05-31
date_resolved: 2026-06-01
assumes: []
supersedes: []
superseded_by: [126]
---

# ADR-19: Agent-proposed hubs (threshold alert and Mapper handoff)

> **Status note (0.1.0-alpha.15):** superseded by [ADR-126](126-four-type-knowledge-model.md). Kept for decision history; current architecture is carried by the consolidation ADR.


> **Tier 1 ships (status note, 2026-06-12).** The report-only check is implemented as the Linter's `hub-threshold` detector ([#426](https://github.com/eranroseman/memoria-vault/issues/426)). The chosen rule, where this ADR left the reading open: a "topic" is a term in a claim's `topics` list or a paper's `research_area` list (the paper-side topic facet the classify stage fills — papers carry no `topics` field); the threshold is **15 notes** (papers + claims combined, the lower edge of the ≥15–20 band in [Wikilink and link conventions](../reference/wikilink-and-link-conventions.md#hub-thresholds)); matching is case-insensitive; a topic already covered by a `hub` (or legacy `moc`) note — its `topic` or `title` matches the term — is suppressed. The finding is a LOW advisory ("consider creating a hub"), never auto-creation. **Tier 2 ships (status note, 2026-06-16).** The deterministic `hub_handoff.py` operation reads current `hub-threshold` findings and delegates a `map` lane card to the Librarian. The handoff is ceiling-validated by `tasks_mcp.py`, allows only `notes/fleeting/maps/` and `inbox/`, and explicitly forbids writes under `notes/hubs/`; the PI still creates or promotes the final hub.

> *Terminology note (0.1.0-alpha.12): "MOC" is now the `hub` type
> ([ADR-119](119-schema-driven-document-creation.md)); "the Mapper" is the
> **Librarian's `map` lane** ([ADR-48](48-copi-and-agent-consolidation.md)); the
> old `reference` type is retired. The threshold-alert decision is unchanged.*

## What

The system surfaces when a topic cluster has crossed the hub-creation threshold but has no hub yet, so the human is prompted to create one instead of having to notice the count by hand. Two tiers:

- **Tier 1 — threshold alert (report-only).** A Linter/dashboard signal: "topic `X` has 18 notes (papers + claim notes) and no hub — consider creating one." No agent-written content; it just makes the threshold crossing visible. Mirrors the existing report-only Linter idiom.
- **Tier 2 — Mapper hub proposal.** A `hub_handoff.py` operation reads fired `hub-threshold` findings and raises an idempotent `map` lane card. The Mapper drafts a **bare** hub proposal (schema-shaped frontmatter template + candidate member-note list + threshold evidence) under `notes/fleeting/maps/` and raises one Inbox candidate card for PI review. The stub is a member list only — never annotations or "why these belong" — and `notes/hubs/` remains review-gated.

## Why

There is an asymmetry in how human-owned synthesis types get agent help. A `reference-note` gets an agent-drafted starting point: the Writer's `promote` command proposes a claim→reference promotion the human finalizes ([Obsidian command palette](../reference/obsidian-command-palette.md)). A `hub` formerly got none — it is human-authored start to finish ([Build a Map of Content](../how-to-guides/knowledge/build-a-hub.md)), and the Mapper now receives the request as a `map` lane card rather than as a profile command.

Yet the Mapper already computes the exact signal a hub proposal needs: `cluster-map` finds dense topic clusters, and [Wikilink and link conventions](../reference/wikilink-and-link-conventions.md#hub-thresholds) defines the ≥15–20-note threshold that says "time for a hub." The capability is present; it is simply not wired to a proposal. Today the human must manually track note counts per topic to know when a hub is due — a bookkeeping task the system is otherwise built to absorb.

## Trade-offs

- **Tier 1** is nearly free and nearly risk-free: it reads counts the Linter already has access to and writes a report line. No new content, nothing to rubber-stamp.
- **Tier 2** adds a Mapper handoff, and carries a real hazard: an agent-listed membership *looks* curated but isn't, nudging the human toward rubber-stamping the indiscriminate "hub-as-folder-dump" the design explicitly warns against ([Common pitfalls](../explanation/knowledge/common-pitfalls.md)). The mitigation — stub is a member list + threshold note only, never annotations — must be enforced, because the annotation *is* the curation that defines the type, and that is the human's.



## Dependencies

- Linter running end-to-end (for the Tier 1 alert).
- Mapper `cluster-map` + the hub thresholds in [Wikilink and link conventions](../reference/wikilink-and-link-conventions.md#hub-thresholds) (already defined).
- Tier 2 is implemented by `operations/integrity/linter/hub_handoff.py` delegating through `tasks_mcp.py` to staging paths outside the review-gated zone.
