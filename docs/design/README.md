---
title: Design
nav_order: 15
has_children: true
permalink: /design/
---

# Design

The design pages carry Memoria's maintained arguments: what the system is, which
ideas it borrows from, which alternatives it rejects, and why the architecture is
bounded the way it is.

> **Design vs. design history.** A design page holds the maintained
> argument; [design history](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)
> holds the dated release record. When both cover the same ground, each links to
> the other rather than restating it. Change the reasoning here; record reversals
> in the active release decision ledger before they close into design history.

## Foundations

| Page | The question it answers |
| --- | --- |
| [What Memoria is](what-memoria-is.md) | What the system is, what it is not, and where the autonomy boundary starts |
| [Intellectual foundations](intellectual-foundations.md) | Which ideas Memoria inherits from Karpathy, Luhmann, Bush, and the AI-research-systems survey |
| [Design principles](design-principles.md) | The cross-cutting rules the design returns to |

## Core arguments

| Page | The question it answers |
| --- | --- |
| [Why the architecture is layered](why-layered-architecture.md) | Why requests, workers, and workspace knowledge are kept separate |
| [Why operation postures](why-specialist-postures.md) | Why Memoria has one read-only conversational posture plus scoped operation postures |
| [Why the review gate is structural](why-review-gate-is-structural.md) | Why review is enforced by architecture |
| [Why Memoria doesn't pursue full autonomy](why-not-autonomous.md) | Why synthesis stays human-owned |
| [Why the write half is bounded](why-write-half-is-bounded.md) | Why project writing ships as traceable files, verification, and refusal gates |
| [Why deterministic methods](why-deterministic-methods.md) | Why deterministic methods are preferred where correctness matters |

## Design areas

| Page | The question it answers |
| --- | --- |
| [Lifecycle, not topic — and state, not folders](lifecycle-over-topic.md) | Why folders encode document type while lifecycle and topics live as state and links |
| [Why hubs](hubs-and-navigation.md) | Why human-authored hubs are the vault's navigation layer |
| [Visual discipline](visual-discipline.md) | Why the Obsidian UI uses a small, consistent visual vocabulary |
| [Design system](design-system.md) | Why the cross-context visual and voice spec is portable and restrained |
| [Distribution model](distribution-model.md) | Why Memoria ships as a repo-backed vault plus runtime configuration |
| [Bootstrap installer](bootstrap-installer.md) | Why the installer is a one-command bootstrap with narrow automation boundaries |
| [Always-on VPS design](always-on-vps-design.md) | Why the always-on topology is deferred and what would need validation |

## Evidence base

| Page | What it provides |
| --- | --- |
| [Pattern provenance: borrow, adapt, ignore](why-pattern-provenance.md) | Why Memoria borrows mechanics from autonomous-scientist systems without adopting their autonomy posture |
| [What the literature pushes back on](what-the-literature-pushes-back-on.md) | Where the literature contradicts Memoria's stronger claims |

---

## Related

- The operational explanations these arguments shape: [Explanation](../explanation/README.md)
- Exact contracts and generated references: [Reference](../reference/README.md)
- Pattern lookup table: [Pattern provenance table](../reference/pattern-provenance.md)
- The dated decisions these arguments pair with: [Decision records](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)
