---
title: Contributing
nav_order: 5
has_children: true
permalink: /contributing/
---

# Contributing

How work moves through this repo, and where each kind of content lives. The
authoritative rules for AI agents are in [AGENTS.md](https://github.com/eranroseman/memoria-vault/blob/main/AGENTS.md); this section is the human-facing complement.

- **[Contributing workflow](process.md)** — branch discipline, the issue/board flow, landing checklists, and divergence recovery.

## Where each kind of content lives

| Content | Location | When to look here |
|---|---|---|
| **Decisions** (ADRs, every status) | [Decisions](../adr/) | Why something is the way it is, or what's been considered |
| **Design notes** | [Design notes](../design/) | The background analysis behind a decision |
| **Release plans + readiness** | [Releasing](../releasing/) | What a release covers, or how to cut one |
| **Test plans** (QA procedures) | [Testing](../testing/) | How to validate or verify the system |
| **Test code** (pytest) | `tests/` at the repo root | The executable unit tests themselves |

Decisions, design notes, and these process docs all live under `docs/` so they render
on the site alongside the explanation pages. Tools and approaches evaluated and **not**
adopted are recorded as *Alternatives considered* in the relevant [ADR](../adr/), not in
a separate folder.
