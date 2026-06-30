---
topic: decisions
id: 03
title: Review gate is structural, enforced by the policy MCP
nav_exclude: true
status: accepted
date_proposed: 2026-05-01
date_resolved: 2026-05-01
assumes: []
supersedes: []
superseded_by: []
---

# ADR-03: Review gate is structural, enforced by the policy MCP

## Context

Canonical zones (*0.1.0-alpha.12: checked `knowledge/notes/` and `knowledge/hubs/`,
per [ADR-119](119-schema-driven-document-creation.md); Project gate thesis promotion
adds a project-scoped review path; the deliverable zone remains later work. Originally
`30-synthesis/01-claims/`, `30-synthesis/02-reference/`, `30-synthesis/03-moc/`,
`50-deliverables/`*) must only receive content that a human has reviewed and approved.
The question is whether this guarantee lives in prompt instructions, agent conventions,
or infrastructure.

## Decision

The review gate is enforced by the **policy MCP** at the filesystem level. Any write targeting a review-gated zone is degraded to `dry_run` — the write does not reach disk — regardless of which profile requests it and regardless of what the profile's prompt says. The human's `review_status: approved` on the board card is the only path to canonical.

This is not a naming convention or a prompt instruction. A profile that "decides" to canonize directly cannot, because the file-system call returns before content reaches disk.

## Why

Prompt-based rules have a mean time to failure: they degrade at long context, can be overridden by later instructions, and don't survive session restarts. Structural enforcement doesn't degrade.

The specific failure mode that matters: hallucinated citations and fabricated claims are emitted with high fluency and high confidence. An advisory gate that fires on low-confidence outputs would wave through exactly the outputs the gate exists to catch. The gate must be unconditional — it cannot be confidence-routed.

The cost is that the human is a bottleneck. This is the point: the human must stay in contact with what the system produces. A system that can autonomously populate the synthesis zone without human attention has removed the epistemic guarantee that makes the vault trustworthy.

## Consequences

- Review-gated zones are hardcoded in the policy MCP configuration; they cannot be bypassed by profile prompt or lane-override.
- Every write to the vault is intercepted, logged with a SHA-256 hash, and auditable.
- The board's `review_status` field is the authoritative state of human approval — not comments, tags, or conversations.
- A WIP cap on done-awaiting-review cards creates back-pressure: when the human's review queue is full, the dispatcher slows new card creation on that lane.

## Promotion within synthesis is also manual

The same principle governs promotion, not just writes: read-state changes that make a
Concept trusted are human-gated. Earlier drafts described this as a claim `maturity`
promotion into a `reference` layer; the current schema uses `check_status` and retired
that separate layer. The human-only rule is unchanged: no automatic maturity threshold
or link-density heuristic can promote content. (Inlink count signals "well-cited," not
"stable enough"; contested claims accumulate inlinks too.) *Folded in from an earlier
renumbered draft on auto-promotion, which was only ever `proposed`.*

## Alternatives considered

**Prompt-based rule ("always wait for review")** — degrades at long context; overrideable; doesn't survive session restart.

**Advisory LLM reviewer** — confidently wrong on exactly the inputs the gate needs to catch. Converts a structural guarantee into a probabilistic one.

**Confidence-routed gate (SmartPause)** — routes to human only when agent confidence is low. Fails because hallucinated citations are emitted with high confidence. See [Why Memoria doesn't pursue full autonomy](../design/why-not-autonomous.md).
