---
topic: decisions
id: 02
title: Seven specialist profiles over one generalist agent
nav_exclude: true
status: superseded
date_proposed: 2026-05-01
date_resolved: 2026-05-01
assumes: []
supersedes: []
superseded_by: [48]
---

# ADR-02: Seven specialist profiles over one generalist agent

## Context

The worker layer needs to be structured. The choice is between one generalist agent that does everything and several specialist agents, each with a narrow mission. A generalist is simpler to configure but creates permission ambiguity, unclear quality responsibility, and no structural separation between optimistic (discovery) and conservative (verification) stances.

## Decision

Memoria uses seven specialist profiles — Librarian, Mapper, Socratic, Writer, Verifier, Coder, Linter — each with a focused mission, narrow folder permissions, the skills it actually needs, and a clear exit condition. There is no Orchestrator profile and no Reviewer profile. Routing is static (encoded in lane-override files); review is always human-driven.

## Why

**Quality responsibility is traceable.** When a paper note has an error, it's a Librarian problem. When a citation doesn't trace, it's a Verifier problem. With one agent, debugging requires replaying the conversation to reconstruct which decision caused what.

**Permission enforcement is practical.** A specialist profile's write scope is narrow and checkable by the policy MCP. A generalist profile's write scope is the superset of all tasks — the MCP can't distinguish "this agent is in discovery mode" from "this agent is in synthesis mode."

**Optimistic and conservative stances must be structurally separated.** Librarian proposes optimistically (include candidates, classify tentatively). Verifier checks conservatively (trace every citation, flag every near-duplicate). An agent that does both must switch internally; there is no structural guarantee it does, and no way to audit whether it did.

No Orchestrator because routing encoded in rules is auditable; routing decided by a reasoning agent is not. No Reviewer profile because LLM-based reviewers are confidently wrong on exactly the outputs the gate needs to catch — hallucinated citations are emitted with high fluency and high confidence.

## Consequences

- Each profile's permissions are declared in a lane-override YAML file that the policy MCP reads at startup.
- Routing is deterministic: a card's `assignee` field determines which profile can claim it; no reasoning agent makes routing decisions.
- The review gate is a human action on `review_status`; agents recommend via `agent_recommendation` but never approve.
- Profile count is fixed at seven for Memoria 0.1.0. Adding an eighth profile requires a new lane-override file, SOUL.md, and policy MCP registration.

## Alternatives considered

**One generalist agent** — ambiguous permissions, no quality traceability, no structural separation between discovery and verification.

**Orchestrator profile for routing** — routing becomes a reasoning step that's hard to audit; if the orchestrator makes a wrong assignment, the failure is invisible until the wrong profile runs.

**LLM-as-Reviewer** — confidently wrong on hallucinated citations; converts a structural gate into a probabilistic one that fails on exactly the inputs it needs to catch.
