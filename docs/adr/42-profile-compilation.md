---
topic: decisions
id: 42
title: Profile compilation from a shared base
nav_exclude: true
status: superseded
superseded_by: [48]  # the shared AGENTS.md layer + unique SOUL/skills/config (D46) removes the drift problem the compiler addressed
assumes: []
date_proposed: 2026-05-31
date_resolved: 2026-06-10
supersedes: []
---

# ADR-42: Profile compilation from a shared base

The seven SOUL.md files are hand-authored and hand-maintained. This proposal describes a build step that would generate the shared sections from a common base, reducing inter-profile drift.

## What

A compile step that generates each profile's SOUL.md by combining:
- A shared base (common audit-log behavior, common policy invariants, common MCP connections)
- A per-profile override block (unique mission, commands, permissions)

The compiler outputs the seven SOUL.md files into the starter vault; no hand-authoring of shared sections.

## Why

The current approach copies shared content (e.g., the audit-log behavior specification) into seven separate SOUL.md files that must be kept in lockstep by hand. When shared behavior changes, seven files need updating — and the retired `profile-install-drift` idea ([ADR-67](67-drift-procedures-keep-or-retire.md)) only ever addressed the *deployment* copy drifting from the *source* copy, not the seven *sources* drifting from each other.

## Trade-offs

A compiler adds a build step and a source-to-output relationship that must be maintained. Debugging requires understanding which sections are compiled vs. hand-authored. The gains are proportional to how much content is actually shared across profiles — if profiles diverge significantly, the compiler buys little.

## When this matters

Inter-profile drift (the seven SOUL.md files disagreeing on shared behavior) becomes a recurring maintenance problem — not a theoretical one. The trigger is at least two instances of a shared-behavior change being applied to some profiles but not others, causing a real bug.


## Alternatives considered

**Keep hand-authoring (the current state).** The standing answer: at seven-profile scale the shared content is small enough to keep in lockstep by hand, and the idempotent installer re-run keeps the source→deployment copy synchronized (the `profile-install-drift` check is retired, [ADR-67](67-drift-procedures-keep-or-retire.md)). Held until inter-profile drift is a felt, recurring bug.

**A lighter include/partial mechanism instead of a full compiler.** A possible middle path (shared blocks pulled in by reference rather than generated). Defer the build-step-vs-include choice until a concrete first drift incident shows which shape the shared content actually wants.

## Related

- **Decision:** [ADR-26 repo-as-install-unit](26-repo-as-install-unit.md) — records hand-authored profiles as the current state and this proposal as the deferred compiler.
- **Linter detector:** `profile-install-drift` — retired ([ADR-67](67-drift-procedures-keep-or-retire.md)); the idempotent installer re-run owns source-vs-deployed sync (and never addressed source-vs-source).
- **Files:** the seven `.memoria/profiles/memoria-<name>/SOUL.md`.
