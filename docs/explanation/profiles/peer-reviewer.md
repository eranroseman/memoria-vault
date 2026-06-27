---
title: The Peer-reviewer
parent: Profiles
grand_parent: Explanation
nav_order: 4
---

# The Peer-reviewer

The Peer-reviewer runs the **verify** lane — the formal, independent review gate before anything ships, the academic peer-review pass. Its posture is **skeptical, and deliberately independent**: flag, don't fix. It runs the *judgment* checks — citekey resolution, claim→source tracing, near-duplicate adjudication — and the conceptual red-team, reading a draft *for soundness, not just facts*. Its findings land as Inbox `gap` and `flag` cards; it writes nowhere else. It receives work from deliberate verify requests and from the project-draft post-commit trigger.

The Peer-reviewer owns judgment checks; deterministic verification work — retraction lookups, duplicate and broken-citation sweeps — lives in verification-sweep operations, scheduled on cron, no posture, no lane ([Operations](../operations/README.md)). ADR-48 records the consolidation decision.

---

## What the Peer-reviewer is not

**Not a truth oracle.** It judges whether a claim *traces* and whether an argument *holds*, and says so with calibrated certainty. Truth stays the PI's domain.

**Not the Co-PI's sparring.** The Peer-reviewer is the formal, independent pass over a finished artifact — it certifies work, where [The Co-PI](co-pi.md)'s continuous in-conversation questioning sharpens thinking.

**Not the sweeps.** If a check is reproducible without judgment, it belongs to an operation, and findings reach the PI the same way — as Inbox cards.

---

## Related

- The deterministic half of verification: [Operations](../operations/README.md)
- The proposer it stays independent of: [The Librarian](librarian.md)
- Why the profile boundaries are strict: [Why profile boundaries exist](../../design/why-profile-boundaries.md)
- Why review is human-driven: [Why the review gate is structural](../../design/why-human-gate.md)
