---
title: Why specialist profiles, not a generalist agent
parent: Design rationale
---

# Why specialist profiles, not a generalist agent

Memoria uses seven specialist profiles instead of one generalist agent. Each specialist has a focused mission, narrow folder permissions, and a clear exit condition. This is not an organizational preference — it is the mechanism that makes quality responsibility traceable and permission enforcement practical.

---

## The problem with a generalist agent

A generalist agent that does everything — discovers sources, synthesizes claims, verifies citations, writes deliverables, lints the vault, and manages code — has several structural problems:

**Unclear responsibility.** When quality fails, it's not possible to say "this was a discovery error" vs "this was a synthesis error" vs "this was a verification failure." The same agent made all three decisions in sequence. Debugging requires re-reading the conversation to reconstruct what happened.

**Ambiguous permissions.** A generalist agent that legitimately needs to write to the inbox (for discovery) also legitimately needs to read synthesis (for drafting). The most permissive permissions required by any task become the baseline for all tasks. The policy MCP can't distinguish "this agent is discovering" from "this agent is synthesizing."

**No separation between optimistic and conservative stances.** Discovery should be optimistic — fetch candidates, classify tentatively, surface possibilities. Verification should be conservative — check every citation, flag duplicates, verify claims against sources. An agent that does both must switch between these stances internally; there is no structural guarantee that it does.

**Single points of failure.** When one agent is responsible for everything, a failure in one task can corrupt the state for downstream tasks. Parallel work becomes difficult because the single agent is a bottleneck.

---

## The seven profiles and their missions

Each profile has a mission that defines what it is *for*, not just what it does:

| Profile | Mission |
|---|---|
| **Librarian** | Find, ingest, enrich, and classify sources. Optimistic and exploratory. |
| **Mapper** | Map the corpus for a project — scope reports, gap analysis, cluster maps. Read-only across the vault. |
| **Socratic** | Sharpen the human's thinking through questions and lens-based reading. Write-denied entirely. |
| **Writer** | Turn evidence into drafts, answer notes, and reference-ready prose. |
| **Verifier** | Trace draft claims to sources; verify citations; flag duplicates. Read-only across the vault, except gap candidate-notes (`10-inbox/03-candidates/`) and verification reports (`40-workbench/*/05-verification/`). |
| **Coder** | Scaffold handoffs to an external coding agent and record provenance. It does not itself write code. |
| **Linter** | Validate structure, metadata, schema, link health. Default dry-run. |

The missions are designed to be in productive tension: Librarian is optimistic, Verifier is conservative. Mapper surveys what's there, Socratic questions the human about it, Writer synthesizes it, Verifier checks the synthesis. Each step's output is the next step's input.

---

## Profiles own outcomes; lanes own claimability

The design distinguishes two things that look similar but are different:

**A profile** is a durable identity with a domain. The Librarian is responsible for the quality of source discovery. The Writer is responsible for the quality of drafts. Each profile's mission is a commitment about what it produces.

**A lane** is a board-level contract about which profile is allowed to claim a card. The lane `memoria-librarian` on a card means only the Librarian profile can move that card forward.

Together: a profile is accountable for its outputs; a lane makes that accountability operational at the dispatch level.

---

## No Orchestrator, no Reviewer

Memoria deliberately omits two roles that comparable multi-agent systems include:

**No Orchestrator profile.** An Orchestrator — a reasoning agent that decides which profile does what — introduces a single point where routing logic lives in the model's reasoning rather than in explicit rules. If the Orchestrator makes a routing mistake, it is hard to audit. Memoria encodes routing in lane-override files and Kanban dispatch rules, not in a reasoning agent. If routing rules can't decide, the card sits in `ready` until a human intervenes. This is slower but auditable.

**No Reviewer profile.** An LLM-based reviewer — an agent that decides whether work is good enough — converts a structural gate into a probabilistic one. An agent reviewer can be confidently wrong. Hallucinated citations are emitted with high fluency and high confidence; a reviewer that assesses confidence would wave through exactly the outputs the gate exists to catch. Human review is the gate; agents (Verifier, Linter) produce recommendations that inform human judgment but never replace it.

The absence of these two profiles is not an oversight — it is a specific design choice with consequences. Routing is deterministic and auditable; review is always human-driven.

---

## The tension pairs

Several profiles are most easily understood by the tensions they represent:

**Librarian ↔ Verifier**: Librarian proposes optimistically; Verifier checks conservatively. The asymmetry is the design — you need both, and they must be separate to work.

**Mapper ↔ Socratic**: Mapper produces structured artifacts over the whole corpus; Socratic converses about one source at a time. Both inform human thinking, through entirely different mechanisms.

**Writer ↔ Verifier**: Writer makes synthesis possible by producing citations and drafts; Verifier makes synthesis trustworthy by checking them. Writer must not pre-empt the verification; Verifier must not synthesize.

**Coder ↔ Linter**: Linter validates structure deterministically; Coder produces artifacts. Linter catches what Coder leaves broken without fixing it silently.

---

## The Socratic special case

Socratic is write-denied entirely. It cannot write anywhere in the vault — `policy.allow.write: []` is enforced at the policy MCP. This is architecturally significant: Socratic's value is in the quality of questions it asks, not in anything it produces. A Socratic session that writes a note has pre-empted the human's own thinking — the human should be the one deciding what to record from a Socratic conversation.

Socratic is also never queue-dispatched. It is only invoked synchronously by the human. A misconfigured cron job can't send work to a write-denied conversational profile.

---

## Related

- How profiles relate to the board and vault: [Architecture](../architecture/README.md)
- Why the board separates concerns: [Why three layers, not one](why-three-layers.md)
- Why the review gate is human-owned: [Why the review gate is structural](why-human-gate.md)
- Permission matrices (lookup): [Profile capabilities](../../reference/profiles.md)
