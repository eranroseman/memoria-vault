---
title: The Librarian
parent: Profiles
nav_order: 2
---

# The Librarian

The Librarian runs Memoria's four processing lanes — **catalog · extract · link · map** — covering everything between "a source exists somewhere" and "the corpus is mapped for a project." Its defining posture is **faithful**: include generously, report state accurately, and let the gate filter. The cost of a missing source is invisible; the cost of an over-inclusive candidate is one human decision. Given that asymmetry, generosity is the right policy for an intake agent — and fidelity to the source material is what keeps the generosity honest.

A research librarian does both intake and literature search, so the old Mapper's corpus work (scope reports, gap analysis, cluster maps) merged into this agent ([ADR-48](../../adr/48-copi-and-agent-consolidation.md)): the **map** lane is the same faithful posture pointed at what the vault already holds.

---

## The four lanes

The table below is an orienting illustration of what each lane does and the signal it raises; [Profile capabilities](../../reference/profiles.md) owns the canonical lane definitions (task-lane ids, write scopes, MCP servers).

| Lane | Work | Inbox signal |
| --- | --- | --- |
| **catalog** | find sources, propose intake, the comparative `[!brief]`, draft classifications | `candidate` |
| **extract** | claim-stubs and distill nudges from kept sources | work prompt |
| **link** | note-link candidates with evidence and stance reasoning | link proposal |
| **map** | corpus-maps, coverage-reports, cluster maps, writability reads, seeded canvases | `gap` |

The lanes are individually triggered, not a pipeline — a human gate (often a long gap) sits between each. Gaps found in *map* raise Inbox `gap`s that re-trigger *catalog*: the loop that compounds.

## Why it's designed this way

**The engine/agent split.** The mechanical half of cataloging — fetch metadata, extract text, build entity `relationships`, create Catalog records — is the **ingest engine**, not the Librarian. The agent fills the two LLM holes: composing the comparative `[!brief]` and proposing the classification. Keeping the mechanics deterministic keeps the high-volume path reproducible, auditable, and cheap; the agent spends LLM judgment only where judgment is needed. Below a confidence floor the engine's fuzzy calls (entity resolution, dedup) emit a `flag` rather than merging silently ([ADR-56](../../adr/56-extraction-uncertainty-flag.md)).

**Faithful, not optimistic-and-loose.** The posture is generous about *inclusion* and strict about *representation*: a brief reports what the paper says, a coverage-report reports what the corpus holds, and neither editorializes. The gate can only filter well if the proposals beneath it are faithful.

**One external surface, fully gated.** The Librarian touches the most external data in the system (OpenAlex, Crossref, Semantic Scholar, …), and every lookup goes through MCP — discovery tools and the ingest facade — never raw web access. Concentrating the external surface in one agent and routing it through the policy boundary makes it auditable by construction.

## What the Librarian is not

**Not a synthesizer.** It curates and maps evidence; the Writer composes arguments and the PI writes claims. It never writes `notes/claims/` or `notes/hubs/`.

**Not its own reviewer.** The agent that gathers and proposes must not also grade the result — that is the [Peer-reviewer](peer-reviewer.md)'s independence, the anti-rubber-stamp principle.

**Not the ingest engine.** You *run* ingest; you *delegate* to the Librarian. The folder is named `catalog/` for its content because both operate on it.

---

## Related

- The mechanical counterpart: [Engines](../engines/README.md)
- The independent checker downstream: [The Peer-reviewer](peer-reviewer.md)
- Why intake is separated from verification: [Why specialist profiles, not a generalist agent](../rationale/why-specialist-profiles.md)
