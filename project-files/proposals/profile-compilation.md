---
status: deferred
created: 2026-05-31
---

# Profile compilation

**Status: deferred.** The seven SOUL.md files are hand-authored and hand-maintained. This proposal describes a build step that would generate the shared sections from a common base, reducing inter-profile drift.

---

## What

A compile step that generates each profile's SOUL.md by combining:
- A shared base (common audit-log behavior, common policy invariants, common MCP connections)
- A per-profile override block (unique mission, commands, permissions)

The compiler outputs the seven SOUL.md files into the starter vault; no hand-authoring of shared sections.

## Why

The current approach copies shared content (e.g., the audit-log behavior specification) into seven separate SOUL.md files that must be kept in lockstep by hand. When shared behavior changes, seven files need updating — and the Linter's `profile-install-drift` check catches only the *deployment* copy drifting from the *source* copy, not the seven *sources* drifting from each other.

## Trade-offs

A compiler adds a build step and a source-to-output relationship that must be maintained. Debugging requires understanding which sections are compiled vs. hand-authored. The gains are proportional to how much content is actually shared across profiles — if profiles diverge significantly, the compiler buys little.

## Adoption trigger

Inter-profile drift (the seven SOUL.md files disagreeing on shared behavior) becomes a recurring maintenance problem — not a theoretical one. The trigger is at least two instances of a shared-behavior change being applied to some profiles but not others, causing a real bug.

## Guard

Do not adopt as a preparatory measure. Seven hand-authored files are simpler than a compiler until drift causes a real problem. The complexity cost of the compiler is paid up front; the benefit only materializes if drift is actually painful.
