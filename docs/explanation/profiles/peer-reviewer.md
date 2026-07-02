---
title: The Peer-reviewer
parent: Operation postures
grand_parent: Explanation
nav_order: 4
---

# The Peer-reviewer

The Peer-reviewer is the formal, independent verification posture before
anything ships: the academic peer-review pass. Its posture is **skeptical, and
deliberately independent**: flag, don't fix. Verification operations run
judgment checks - citekey resolution, claim-to-source tracing, near-duplicate
adjudication - and conceptual red-team checks, reading a draft *for soundness,
not just facts*. Findings land as attention; they do not become automatic fixes.

The Peer-reviewer owns judgment checks. Deterministic verification work -
retraction lookups, duplicate and broken-citation sweeps - lives in
verification-sweep operations that can be run manually or by an operator-managed
schedule, with no installed profile and no lane ([Operations](../operations.md)).
ADR-48 records the consolidation decision.

---

## What the Peer-reviewer is not

**Not a truth oracle.** It judges whether a claim *traces* and whether an argument *holds*, and says so with calibrated certainty. Truth stays the PI's domain.

**Not the Co-PI's sparring.** The Peer-reviewer is the formal, independent pass over a finished artifact — it certifies work, where [The Co-PI](co-pi.md)'s continuous in-conversation questioning sharpens thinking.

**Not the sweeps.** If a check is reproducible without judgment, it belongs to
an operation, and findings reach the PI the same way - as attention.

---

## Related

- The deterministic half of verification: [Operations](../operations.md)
- The proposer it stays independent of: [The Librarian](librarian.md)
- Why the posture boundaries are strict: [Why specialist profiles, not a generalist agent](../../design/why-specialist-profiles.md)
- Why review is human-driven: [Why the review gate is structural](../../design/why-review-gate-is-structural.md)
