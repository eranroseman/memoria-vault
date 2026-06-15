---
title: The Peer-reviewer
parent: Profiles
nav_order: 4
---

# The Peer-reviewer

The Peer-reviewer runs the **verify** lane — the formal, independent review gate before anything ships, the academic peer-review pass. Its posture is **skeptical, and deliberately independent**: flag, don't fix. It runs the *judgment* checks — citekey resolution, claim→source tracing, near-duplicate adjudication — and the conceptual red-team, reading a draft *for soundness, not just facts*. Its findings land as Inbox `gap` and `flag` cards; it writes nowhere else. It ships fully with the deferred Project workflow.

It replaces the old Verifier, split by determinism ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)): the *judgment* half became this agent; the *deterministic* half — retraction lookups, duplicate and broken-citation sweeps — became the verification-sweep operations, scheduled on cron, no posture, no lane ([Operations](../operations/README.md)).

---

## Why it's designed this way

**Independence is the design, not a staffing detail.** The agent that synthesizes must not also grade its own work — separation of duties, the anti-rubber-stamp principle. That is why the Peer-reviewer was never merged into the Librarian, however much tooling they share: a checker that inherits the proposer's stance waves through exactly what the gate exists to catch.

**Judgment checks vs engine sweeps.** A retraction lookup gives the same answer on every run — that's an engine. "Does this prose claim actually follow from this source?" requires reading — that's this agent. Splitting by determinism keeps the reproducible checks cheap and auditable while spending LLM judgment only where a verdict requires it.

**Flag, don't fix.** The entity that checks the work must not correct it. A failed trace becomes a `gap` card the Librarian picks up; a soundness problem becomes a `flag` for the PI. The draft is untouched — closing the loop without blurring the duty.

**Verification cards lead with the finding.** Unlike proposal cards (where the verdict is a given and is therefore omitted), a verification item carries its `agent_recommendation` — `clean` / `issues-found` / `inconclusive` — up front, with the evidence ([ADR-51](../../adr/51-inbox-category-and-honesty-card.md)). A recommendation is a soft signal, never a gate: `clean` does not substitute for the PI's approval.

## What the Peer-reviewer is not

**Not a truth oracle.** It judges whether a claim *traces* and whether an argument *holds*, and says so with calibrated certainty. Truth stays the PI's domain.

**Not the Co-PI's sparring.** The Co-PI questions continuously and informally, inside the conversation; the Peer-reviewer is the formal, independent pass over a finished artifact. The first sharpens thinking; the second certifies work.

**Not the sweeps.** If a check is reproducible without judgment, it belongs to an engine, and findings reach the PI the same way — as Inbox cards.

---

## Related

- The deterministic half of verification: [Operations](../operations/README.md)
- The proposer it stays independent of: [The Librarian](librarian.md)
- Why review is human-driven: [Why the review gate is structural](../rationale/why-human-gate.md)
