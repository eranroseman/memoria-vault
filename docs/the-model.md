---
title: The model
nav_order: 2
permalink: /the-model/
topic: overview
---

# The model

Memoria is a single-researcher operating system for turning sources into defensible
claims and drafts. It is not an autonomous researcher. The PI owns judgment; Memoria
keeps the work visible, traceable, and review-gated.

## The five terms

| Term | Meaning |
| --- | --- |
| PI | The human principal investigator. The PI decides what enters the vault and what can be cited. |
| Co-PI | The conversational agent in Obsidian. It explains, questions, reads, and delegates. It does not write directly. |
| Lanes | The four background agents: Librarian, Writer, Peer-reviewer, and Engineer. They work through board cards. |
| Board | The Hermes Kanban control plane. It records delegated work, status, blockers, review, and completion. |
| Vault | The Obsidian folder tree. It holds notes, catalog records, inbox cards, spaces, and system projections. |

## The working loop

1. Capture or find a source.
2. Ingest and classify it into the Library.
3. Distill source notes into claim notes.
4. Link claims into a project argument.
5. Draft from current claims.
6. Verify the draft and resolve findings.
7. Archive or revise as the project changes.

The loop compounds because each step leaves a typed, linkable artifact in the vault.
Nothing important depends only on chat history.

## The control rule

Agents propose; the PI disposes. Background lanes can create staged notes, Inbox cards,
or project scratch within their lane scope. Promotion into review-gated knowledge stays
human-owned and policy-gated.

## Documentation map

| Section | Use it for |
| --- | --- |
| [Tutorials](tutorials/README.md) | Learn Memoria through a guided first project. |
| [How-to guides](how-to-guides/README.md) | Complete a specific task. |
| [Reference](reference/README.md) | Look up exact fields, commands, schemas, settings, and paths. |
| [Explanation](explanation/README.md) | Understand architecture, workflows, and concepts. |
| [Developers](developers.md) | Inspect runtime contracts, design rationale, and ADRs. |

## Where details live

- Exact fields, schemas, commands, and configuration live in [Reference](reference/README.md).
- Explanations live in [Explanation](explanation/README.md).
- Design Book pages and dated decisions live in [Developers](developers.md).
- Agent working rules live in
  [AGENTS.md](https://github.com/eranroseman/memoria-vault/blob/main/AGENTS.md).
