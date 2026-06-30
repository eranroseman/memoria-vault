---
title: The Librarian
parent: Profiles
grand_parent: Explanation
nav_order: 2
---

# The Librarian

The Librarian runs four background lanes: **catalog · extract · link · map**. Together they cover the span from "a source exists somewhere" to "the corpus is mapped for a project."

Its posture is **faithful**: include generously, report state accurately, and let the review gate filter. A missing source is invisible; an over-inclusive candidate costs one human decision. That asymmetry makes generosity the right intake policy, and fidelity keeps it honest.

A research librarian does both intake and literature search, so corpus work (scope reports, gap analysis, cluster maps) belongs in this agent ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)): the **map** lane is the same faithful posture pointed at what the vault already holds.

---

## The four lanes

The table below is an orienting illustration of what each lane does and the Inbox signal (a proposal card in your queue — see [Glossary](../../reference/glossary.md)) it raises; [Profile capabilities](../../reference/profile-capabilities.md) owns the canonical lane definitions (task-lane ids, write scopes, MCP servers).

| Lane | Work | Inbox signal |
| --- | --- | --- |
| **catalog** | find sources, propose intake, the comparative `[!brief]`, draft classifications | `candidate` |
| **extract** | claim-stubs and distill nudges from kept sources | work prompt |
| **link** | note-link candidates with evidence and stance reasoning | link proposal |
| **map** | corpus maps, coverage reports, cluster maps, graph/canvas proposals, gap analysis | `gap` |

The lanes are individually triggered, not a pipeline — a human gate (often a long gap) sits between each. Gaps found in *map* raise Inbox `gap`s (one of the card types — `candidate` / `flag` / `gap` — see [Glossary](../../reference/glossary.md)) that re-trigger *catalog*: the loop that compounds.

## What the Librarian is not

**Not the owner of synthesis judgment.** It maps evidence and suggests links,
notes, and hub updates. Digests are machine-owned checked records; note
acceptance and hub curation stay with the PI.

**Not its own reviewer.** The agent that gathers and proposes must not also grade the result — that is the [Peer-reviewer](peer-reviewer.md)'s independence, the anti-rubber-stamp principle.

**Not the ingest operation.** You *run* ingest; you *delegate* to the Librarian. The folder is named `catalog/` for its content because both operate on it.

---

## Related

- The mechanical counterpart: [Operations](../operations.md)
- The independent checker downstream: [The Peer-reviewer](peer-reviewer.md)
- Why the profile boundaries are strict: [Why specialist profiles, not a generalist agent](../../design/why-specialist-profiles.md)
- Why intake is separated from verification: [Why specialist profiles, not a generalist agent](../../design/why-specialist-profiles.md)
