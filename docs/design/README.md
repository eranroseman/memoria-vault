---
title: Design Book
parent: Developers
nav_order: 1
has_children: true
permalink: /design/
---

# Design Book

The Design Book carries Memoria's maintained arguments: what the system is, which
ideas it borrows from, which alternatives it rejects, and why the architecture is
bounded the way it is.

> **Design Book vs. ADRs.** A Design Book page holds the maintained argument; an
> [ADR](../adr) holds the dated decision. When both cover the same ground, each
> links to the other rather than restating it. Change the reasoning here; reverse
> the decision in a superseding ADR.

## Foundations

| Page | The question it answers |
| --- | --- |
| [What Memoria is](what-memoria-is.md) | What the system is, what it is not, and where the autonomy boundary starts |
| [Intellectual foundations](intellectual-foundations.md) | Which ideas Memoria inherits from Karpathy, Luhmann, Bush, and the AI-research-systems survey |
| [Design principles](design-principles.md) | The cross-cutting rules the design returns to |

## Core arguments

| Page | The question it answers |
| --- | --- |
| [Why the architecture is layered](why-layered-architecture.md) | Why board, workers, and vault are kept separate |
| [Why specialist profiles](why-specialist-profiles.md) | Why Memoria has one conversational Co-PI plus specialist background profiles |
| [Why the review gate is structural](why-review-gate-is-structural.md) | Why the human approval gate is enforced by architecture |
| [Why Memoria doesn't pursue full autonomy](why-not-autonomous.md) | Why synthesis stays human-owned |
| [Why Hermes](why-hermes.md) | Why Hermes is the execution layer |
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
- The dated decisions these arguments pair with: [Decision records](../adr)
