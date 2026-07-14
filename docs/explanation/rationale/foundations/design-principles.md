---
title: Design principles
parent: Foundations
grand_parent: Design rationale
nav_order: 1
---

# Design principles

Twelve principles that settle ambiguous decisions. When a tool choice, workflow step, or architectural question is unclear, these are the tiebreakers.

Underneath them runs one master pattern: **the fluent, judging half of any capability stays with the human; the structural, inspectable half goes into the engine.** Truth/grounding, judgment/method, agent-loop/fenced-operation, and knowledge/trust-state are all this one cut — a design fork that resists resolution usually has not been cut along this line yet.

---

**1. The vault is the artifact.**

Not the chat log, not the PDF folder, not a reference-manager library. The
Memoria workspace is what you are building. Everything else serves the workspace.
A useful output that lives only in a chat transcript has not been captured.

**2. Compound, don't just collect.**

Every source ingested should make the whole corpus more useful. A new Work that
connects to existing notes, adds to a hub, and updates a comparative brief is
compounding. An isolated file that sits unlinked is just collection. The design
distinguishes them: synthesis structures (notes and hubs) exist precisely to
force compounding.

**3. Separate capture from synthesis.**

Raw annotations are not synthesis. A catalog Work is not a note. A fleeting
thought is not a finished claim. The architecture preserves this distinction
with catalog state, Concept homes, and separate schemas. Blurring it produces a
vault where everything is "sort of processed" and nothing is reliably citable.

**4. The agent writes narrowly.**

Agents read broadly but write through controlled request, staging, and trusted
writer paths. Worker-owned checks can mark material as checked when declared
warrants pass, but that is not PI approval. The PI owns meaning, curation,
accept/reject dispositions, and direct edits. A vault where agents write freely
is a vault where the human doesn't know what they actually believe.

**5. Provenance everywhere.**

Every claim-bearing note traces back to checked Work evidence through
`work_id`, evidence markers, compact citation payloads, typed `links`, and
event/read-API state. Every agent action traces back to an audit log entry. Untraceable
content is not knowledge — it is a liability that will fail when cited. The
[Policy gate](../../../reference/control-and-policy/policy-mcp.md), trusted writer, per-write SHA-256 hash
pairing, and SQLite journal/read model all enforce this. An evidence marker's
binding to its exact cited text is itself immutable: the hash ledger that
pairs a marker to its source span accepts new rows, never edits to existing
ones, so a citation cannot be silently re-pointed at different text later.

**6. Prefer incremental over full rewrites.**

The agent updates notes, not replaces them. History matters. Dry-run before auto-fix. A note that exists and is imperfect is almost always better than a note that was deleted and recreated. The `superseded_by` field exists precisely so claims can be updated without destroying provenance.

**7. Lint or decay.**

A knowledge base that is never linted slowly becomes unusable. The Linter is not optional maintenance — it is the mechanism that keeps the vault structurally trustworthy. Schema drift, broken links, stale enrichment, and orphaned notes compound silently; the Linter makes them visible.

**8. Code is a research output.**

Code artifacts belong in the vault and are traceable to the literature that motivated them. The false boundary between "notes" and "code" is an organizational failure mode. A figure-generation script with no provenance link to the claim it illustrates is as untrustworthy as an uncited claim.

**9. Simplest stack that solves the real bottleneck.**

Every tool in the stack addresses a specific friction point. Tools that don't address real friction are liabilities — they add maintenance overhead, failure modes, and cognitive load. The required core is deliberately narrow: the standalone CLI/engine plus the vault catalog. Optional adapters earn their place by removing friction, not adding features.

**10. The engine owns the workflow.**

Research, writing, and coding tools may add ergonomic adapters, but Memoria's
required workflow lives in the CLI/engine. Optional editor presence is useful
only when it calls the same request lifecycle, checks, and write boundary.

**11. Grounding, not truth.**

Memoria never reads a claim and asks whether it is true; it asks how the claim is grounded in evidence. No single node is judged true or false — the system asserts only how a change affects knowledge-graph integrity. "Checked" means required checks and warrants passed, never a truth verdict; dispositions record judgment events, they do not adjudicate content.

> **Planned — G4 (alpha.22/B1) and V1 (beta.1):** The complete Toulmin
> warrant graph and its checking model are planned across these milestones. Today,
> `checked` covers shipped checks, not the complete Toulmin warrant graph.

**12. Origin-blind consequences.**

The origin of a change — human, machine, or LLM — does not affect its *epistemic* consequences. When a claim is found wrong, the grounding consequences propagate across the graph identically whoever authored it; flags, demotions, and blast radius are origin-blind. Write and revert *authority*, by contrast, stays origin-gated: human-authored spans are never auto-destroyed, machine material auto-reverts. Origin is provenance, not authorization.

> **Planned — G5 (alpha.22/B1):** Origin-blind epistemic consequence and
> blast-radius propagation are planned for this milestone. Today, write and revert
> authority remains origin-gated as stated above.

---

## Related

- Why these principles led to a review-gated system: [Why the review gate is structural](../boundaries/why-review-gate-is-structural.md)
- Why operation postures rather than one generalist: [Why operation postures](../boundaries/why-operation-postures.md)
- Why not autonomous: [Why Memoria doesn't pursue full autonomy](../boundaries/why-not-autonomous.md)
- What the principles describe: [What Memoria is](what-memoria-is.md)
- Where the principles come from: [Intellectual foundations](intellectual-foundations.md)
