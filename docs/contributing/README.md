---
title: Contributing
nav_order: 6
has_children: true
permalink: /contributing/
---

# Contributing

How work moves through this repo, and where each kind of content lives. The
authoritative rules for AI agents are in [AGENTS.md](https://github.com/eranroseman/memoria-vault/blob/main/AGENTS.md); this section is the human-facing complement.

- **[Contributing workflow](process.md)** — branch discipline, landing checklists, and divergence recovery.
- **[Issue tracking](issue-tracking.md)** — the GitHub Project / milestone / sub-issue / label model for live work state.

## Where each kind of content lives

| Content | Location | When to look here |
|---|---|---|
| **Decisions** (ADRs, every status) | [Decisions](../adr/) | Why something is the way it is, what's been considered, and the background analysis behind a decision |
| **Live work state** | [Issue tracking](issue-tracking.md) + [Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1) | What is planned, active, deferred, or complete |
| **Release prose** | [Releasing](../releasing/) | What a release covers, how to cut one, and where live readiness lives |
| **Test plans** (QA procedures) | [Testing](../testing/) | How to validate or verify the system |
| **Test code** (pytest) | `tests/` at the repo root | The executable unit tests themselves |

Decisions and these process docs all live under `docs/` so they render
on the site alongside the explanation pages. Tools and approaches evaluated and **not**
adopted are recorded as *Alternatives considered* in the relevant [ADR](../adr/), not in
a separate folder.
