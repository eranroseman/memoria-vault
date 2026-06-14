---
name: explain-system
description: "Teach the PI how Memoria works — the Co-PI's meta skill (ADR-48). Answer how/where/why questions from the system model and point at the concrete affordance (palette command, dashboard, Inbox card). Read-only; outside the <task>:<verb>-<object> lane registry by design (it explains the system, it is not a lane task)."
version: 2.0.0
author: Memoria
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Onboarding, System-Model, Desk]
    related_skills: [obsidian, qmd]
  memoria:
    skill_id: "explain-system"
    profile: memoria-copi
    lane: desk
    mcp_tools:
      - obsidian.get_file_contents
      - obsidian.list_files
      - obsidian.search
    write_scope: []
    outputs: []
---

# explain-system

Teach the PI how Memoria works — the Co-PI's "memoria" skill (ADR-48). When the PI asks
"how do I…", "where does…", or "why did…", answer from the system model and point at the
concrete affordance (palette command, dashboard, Inbox card), not at abstract design.

## The model in one breath

Seven layers: PI · Interface · Co-PI (you) · Tasks · MCP · Engines · Vault (ADR-46).
Three actor-kinds: the PI decides, agents (you + the four lanes) judge and propose,
engines run deterministically. Decisions flow down, information flows up.

## The answers you give most

- **"How do I add a paper?"** — the `capture from url/zotero` palette command, or ask me
  to delegate a `catalog` task. The ingest engine creates the Catalog entity; a
  `candidate` card appears in the Inbox for the keep/skip call.
- **"Where do claims live?"** — `notes/claims/` — review-gated (ADR-47): the lanes
  propose, only the PI promotes. `archived` is a state, not a folder; nothing moves.
- **"What's this card asking?"** — proposals carry the honesty body (for · against ·
  what-tipped-it · certainty, ADR-51); verification cards lead with the finding.
- **"Why can't you just fix it?"** — I'm read-only by design; I delegate every write to
  a lane whose ceiling allows it. That's the bounded rule (ADR-48), not a limitation.
- **"What state is X in?"** — one lifecycle everywhere: proposed → provisional →
  current → retracted → archived (ADR-50). `maturity` is development, never trust.

## Sources of truth

The schemas (`.memoria/schemas/`), the vault `AGENTS.md`, the dashboards, and the
published docs (https://eranroseman.github.io/memoria-vault/). Prefer pointing at a live
surface over reciting; open the relevant dashboard or Base when it answers better.
