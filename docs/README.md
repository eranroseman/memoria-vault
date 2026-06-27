---
title: Home
nav_order: 1
permalink: /
topic: overview
---

# Memoria

A research operating system for a single researcher (the PI) — a Co-PI you converse with and four background agents that read, enrich, map, verify, and write inside your Obsidian vault, under a human-approval gate that audits every proposed change before it lands.

If you want a guided first experience, see [Tutorials](tutorials). If you need
to _do_ something, see [How-to guides](how-to-guides). If you need exact values,
field names, or configuration formats, see [Reference](reference).

**v0.1** — installer validated; not yet run end-to-end on a live Hermes. · [GitHub](https://github.com/eranroseman/memoria-vault) · [Install](https://github.com/eranroseman/memoria-vault#install) · [Issues](https://github.com/eranroseman/memoria-vault/issues)

<!-- SCREENSHOT: Replace this comment with ![Memoria vault](assets/screenshot.png) once the system is running. -->

---

## The model

Memoria is a single-researcher operating system for turning sources into defensible
claims and drafts. It is not an autonomous researcher. The PI owns judgment; Memoria
keeps the work visible, traceable, and review-gated.

### The five terms

| Term | Meaning |
| --- | --- |
| PI | The human principal investigator. The PI decides what enters the vault and what can be cited. |
| Co-PI | The conversational agent in Obsidian. It explains, questions, reads, and delegates. It does not write directly. |
| Lanes | The four background agents: Librarian, Writer, Peer-reviewer, and Engineer. They work through board cards. |
| Board | The Hermes Kanban control plane. It records delegated work, status, blockers, review, and completion. |
| Vault | The Obsidian folder tree. It holds notes, catalog records, inbox cards, spaces, and system projections. |

### The working loop

1. Capture or find a source.
2. Ingest and classify it into the Library.
3. Distill source notes into claim notes.
4. Link claims into a project argument.
5. Draft from current claims.
6. Verify the draft and resolve findings.
7. Archive or revise as the project changes.

The loop compounds because each step leaves a typed, linkable artifact in the vault.
Nothing important depends only on chat history.

### The control rule

Agents propose; the PI disposes. Background lanes can create staged notes, Inbox cards,
or project scratch within their lane scope. Promotion into review-gated knowledge stays
human-owned and policy-gated.

---

## Where do you want to go?

| I want to…                                  | Go here                                                                                           |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Understand the system model**             | [The model](#the-model)                                                                           |
| **Get set up for the first time**           | [Quickstart — set up your vault](how-to-guides/setup/quickstart.md)                                |
| **Do something specific**                   | [How-to guides](how-to-guides/README.md)                                                          |
| **Look up a field, command, or schema**     | [Reference](reference/README.md)                                                                  |
| **Understand how the system fits together** | [Explanation](explanation/README.md)                                                              |
| **Understand why it is designed this way** | [Design Book](design/README.md)                                                                   |
| **Fix something broken**                    | [Failure modes](reference/failure-modes.md) · [Troubleshooting](how-to-guides/troubleshooting/README.md) |

---

## New here? Follow the tutorial sequence

Seven tutorials, each building on the last. Start at 01 and follow the sequence — or jump in at whichever step matches where you are. The full sequence, with what you do and end with at each step, is in [Tutorials](tutorials/README.md).

---

## Prefer to read it straight through?

The sections below are organized by what you're trying to do, not as a syllabus.
If you'd rather understand the system before touching it, read the model above, the
Design Book foundations, then the Explanation pages in this order.

**Understand the system (read in order)**

1. [The model](#the-model) — the shared vocabulary and working loop
2. [What Memoria is](design/what-memoria-is.md) — the central insight, and what it deliberately is not
3. [Intellectual foundations](design/intellectual-foundations.md) — where the design comes from
4. [Design principles](design/design-principles.md) — the rules the framing produces
5. [Architecture](explanation/architecture/README.md) — the layered structure
6. [The vault](explanation/architecture/vault.md) — how knowledge is laid out on disk
7. [Document types and epistemic roles](explanation/knowledge/document-types.md) — the data model
8. [The memory model](explanation/architecture/memory-model.md) — what persists, and why only the Co-PI carries memory
9. [Profiles](explanation/profiles/README.md) — the Co-PI and the four background lanes
10. [Operations](explanation/operations/README.md) — the deterministic layer beneath the agents
11. [The control plane](explanation/kanban-board/README.md) — the board as a state machine
12. [The workflow model](explanation/workflows/README.md) — how work moves, with review as a first-class state
13. [The knowledge cycle](explanation/knowledge/knowledge-cycle.md) — the loop that makes the vault compound
14. [Obsidian — the human surface](explanation/obsidian/README.md) — where you actually work
15. [Design Book](design/README.md) — why each major decision went the way it did

**Then learn it by doing**

16. [Tutorials 01–07](tutorials/README.md) — build one small, well-sourced paragraph end to end
17. [Quickstart](how-to-guides/setup/quickstart.md) — install Memoria when you're ready to use your own corpus

---

## Common tasks

**First session**
[Quickstart](how-to-guides/setup/quickstart.md) · [Set up Hermes](how-to-guides/setup/set-up-hermes.md) · [Vault launch screen](how-to-guides/using-obsidian/use-the-vault-launch-screen.md) · [Use workspaces](how-to-guides/using-obsidian/use-workspaces.md)

**Daily work — sources**
[Find new sources](how-to-guides/library/find-new-sources.md) · [Capture and ingest](how-to-guides/library/capture-and-ingest.md) · [Classify a source](how-to-guides/library/classify-a-source.md) · [Write a claim note](how-to-guides/knowledge/write-a-claim-note.md)

**Daily work — writing**
[Query the vault](how-to-guides/knowledge/query-the-vault.md) · [Assess your corpus](how-to-guides/project/assess-your-corpus.md) · [Draft with Writer](how-to-guides/project/draft-with-writer.md) · [Verify and revise](how-to-guides/project/verify-and-revise.md)

**Weekly**
[Return to work](how-to-guides/inbox/return-to-work.md) · [Weekly review](how-to-guides/inbox/run-the-weekly-review.md) · [Run the Linter](how-to-guides/operate/run-the-linter.md)

**Troubleshooting**
[Safe mode](how-to-guides/troubleshooting/safe-mode.md) · [Failure modes reference](reference/failure-modes.md)

---

## The agents

| Agent             | What it does                                                                  |
| ----------------- | ----------------------------------------------------------------------------- |
| **Co-PI**         | The one agent you converse with — questions, explains, and delegates; read-only |
| **Librarian**     | The four processing lanes (catalog · extract · link · map) — intake to corpus maps |
| **Writer**        | Turns evidence into draft prose — lands in review, never direct to canonical  |
| **Peer-reviewer** | The independent verify gate — traces claims, red-teams arguments; flags, never fixes |
| **Engineer**      | Scaffolds handoffs to external coding agents and owns the commit/revert checkpoint |

Five deterministic **operations** (ingest · search · clustering · sweeps · Linter) do the mechanical work, behind the policy MCP.

→ [Per-agent design rationale](explanation/profiles/README.md) · [Capability and permission table](reference/profiles.md)

---

## Current status and limitations

Memoria is at **v0.1**: the installer is validated, but the system has not yet been run end to end on a live Hermes runtime. What is not working today:

- **No end-to-end run on a live runtime** — continuous, unattended operation through all workflow stages is not yet demonstrated.
- **Mobile capture is not available** — only urgent push (via Telegram) ships today; inbound capture from a phone is planned ([#382](https://github.com/eranroseman/memoria-vault/issues/382)). See [Interaction channels](explanation/architecture/human-channels.md).
- **No autonomous code-experiment loop** — provenance-tracked code experiments are future work.
- **Writability and readiness scoring are not implemented** — `map:score-writability` / `map:score-readiness` are deferred ([Hermes CLI](reference/hermes-cli.md)).
- **Single-user only** — team and multi-user review are out of scope by design.
- **macOS is not supported** — only Linux (including WSL2) and Windows are tested.
- **Some integrations are planned, not shipped** — e.g. expanded reference-manager support.

Throughout the docs, unshipped capabilities are marked *planned* or *deferred*; nothing here implies they work yet.

---

## Browse the docs

[**Tutorials**](tutorials/README.md) — Guided first use.

[**How-to guides**](how-to-guides/README.md) — Task recipes.

[**Reference**](reference/README.md) — Exact fields, commands, schemas, settings, and paths.

[**Explanation**](explanation/README.md) — Architecture, workflows, and conceptual model.

[**Developers**](developers.md) — Design Book and decision records.
