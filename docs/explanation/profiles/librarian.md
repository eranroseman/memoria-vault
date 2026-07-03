---
title: The Librarian
parent: Operation postures
grand_parent: Explanation
nav_order: 2
---

# The Librarian

The Librarian is the posture behind intake, extraction, linking, and mapping
operations. Together those operations cover the span from "a source exists
somewhere" to "the corpus is mapped for a project."

Its posture is **faithful**: include generously, report state accurately, and let the review gate filter. A missing source is invisible; an over-inclusive candidate costs one human decision. That asymmetry makes generosity the right intake policy, and fidelity keeps it honest.

A research librarian does both intake and literature search, so corpus work
(scope reports, gap analysis, cluster maps) belongs with the same faithful
posture ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)). Alpha.15
implements that posture through checked operation manifests and request rows, not
installed profile packages.

---

## The operation family

The table below is an orienting illustration of what each operation family does
and the attention signal it can raise. [Operations](../../reference/operations.md)
owns the concrete command and manifest surface; [Installed profiles](../../reference/profile-capabilities.md)
owns the no-installed-profile boundary.

| Operation family | Work | Attention signal |
| --- | --- | --- |
| **catalog** | find sources, propose intake, the comparative `[!brief]`, draft classifications | `candidate` |
| **extract** | claim-stubs and distill nudges from kept sources | work prompt |
| **link** | note-link candidates with evidence and stance reasoning | link proposal |
| **map** | corpus maps, coverage reports, cluster maps, graph/canvas proposals, gap analysis | `gap` |

The operations are individually triggered, not a pipeline. A human gate, often a
long gap, sits between each. Gaps found by mapping raise attention that can lead
to new catalog work: the loop that compounds.

## What the Librarian is not

**Not the owner of synthesis judgment.** It maps evidence and suggests links,
notes, and hub updates. Digests are machine-owned checked records; note
acceptance and hub curation stay with the PI.

**Not its own reviewer.** The operation posture that gathers and proposes must
not also grade the result - that is the [Peer-reviewer](peer-reviewer.md)'s
independence, the anti-rubber-stamp principle.

**Not the ingest operation.** You *run* ingest; you *delegate* to the Librarian. The folder is named `catalog/` for its content because both operate on it.

---

## Related

- The mechanical counterpart: [Operations](../operations.md)
- The independent checker downstream: [The Peer-reviewer](peer-reviewer.md)
- Why the posture boundaries are strict: [Why specialist profiles, not a generalist agent](../../design/why-specialist-profiles.md)
- Why intake is separated from verification: [Why specialist profiles, not a generalist agent](../../design/why-specialist-profiles.md)
