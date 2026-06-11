---
topic: decisions
id: 19
title: Agent-proposed MOCs (threshold alert; Mapper stub deferred)
status: accepted
date_proposed: 2026-05-31
date_resolved: 2026-06-01
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 19
---

# ADR-19: Agent-proposed MOCs (threshold alert; Mapper stub deferred)

> **Tier 1 accepted / implemented in v0.1 (2026-06-01).** The report-only "MOC threshold crossed" check ships in the Linter's lint-checks table — surfaces "consider a MOC for topic X" in the weekly dashboard, never auto-creates. **Tier 2 (Mapper stub) remains deferred** per the Guard below.

## What

The system surfaces when a topic cluster has crossed the MOC-creation threshold but has no MOC yet, so the human is prompted to create one instead of having to notice the count by hand. Two tiers:

- **Tier 1 — threshold alert (report-only).** A Linter/dashboard signal: "topic `X` has 18 notes (papers + claim notes) and no MOC — consider creating one." No agent-written content; it just makes the threshold crossing visible. Mirrors the existing report-only Linter idiom.
- **Tier 2 — Mapper stub proposal (optional, later).** A `propose-moc` handoff: when `cluster-map` detects a past-threshold cluster, the Mapper drafts a **bare** MOC stub (title + member-note list + a Dataview block) into `10-inbox/` (or a `_proposed` namespace) for the human to curate and promote into `30-synthesis/03-moc/`. The stub is a member list only — never annotations or "why these belong."

## Why

There is an asymmetry in how the two human-owned synthesis types get agent help. A `reference-note` gets an agent-drafted starting point: the Writer's `promote` command proposes a claim→reference promotion the human finalizes ([Obsidian command palette](../reference/obsidian-command-palette.md)). A `moc` gets none — it is human-authored start to finish ([Build a Map of Content](../how-to-guides/curate/build-a-moc.md): "You author and curate the MOC"), and the Mapper's `SOUL.md` has no MOC verb at all.

Yet the Mapper already computes the exact signal a MOC proposal needs: `cluster-map` finds dense topic clusters, and [Wikilink and link conventions](../reference/linking.md#hub-thresholds) defines the ≥15–20-note threshold that says "time for a MOC." The capability is present; it is simply not wired to a proposal. Today the human must manually track note counts per topic to know when a MOC is due — a bookkeeping task the system is otherwise built to absorb.

## Trade-offs

- **Tier 1** is nearly free and nearly risk-free: it reads counts the Linter already has access to and writes a report line. No new content, nothing to rubber-stamp.
- **Tier 2** adds a Mapper command + handoff, and carries a real hazard: an agent-listed membership *looks* curated but isn't, nudging the human toward rubber-stamping the indiscriminate "MOC-as-folder-dump" the design explicitly warns against ([Common pitfalls](../explanation/knowledge/common-pitfalls.md)). The mitigation — stub is a member list + threshold note only, never annotations — must be enforced, because the annotation *is* the curation that defines the type, and that is the human's.



## Dependencies

- Linter running end-to-end (for the Tier 1 alert).
- Mapper `cluster-map` + the MOC thresholds in [Wikilink and link conventions](../reference/linking.md#hub-thresholds) (already defined).
- Tier 2 additionally needs a `propose-moc` Mapper command and a handoff target outside the review-gated zone.
