---
title: Home
nav_order: 1
permalink: /
---

# Memoria

A research operating system for a single researcher (the PI) — a Co-PI you converse with and four background agents that read, enrich, map, verify, and write inside your Obsidian vault, under a human-approval gate that audits every proposed change before it lands.

**[Read about what Memoria is](explanation/overview/what-memoria-is.md)**, what it's not, and why it exists. Everything else builds on this.
If you want a guided first experience, see [Tutorials](tutorials).
If you need to _do_ something, see [how-to guides](how-to-guides).
If you need exact values, field names, or configuration formats, see [Reference](reference).

**v0.1** — installer validated; not yet run end-to-end on a live Hermes. · [GitHub](https://github.com/eranroseman/memoria-vault) · [Install](https://github.com/eranroseman/memoria-vault#install) · [Issues](https://github.com/eranroseman/memoria-vault/issues)

<!-- SCREENSHOT: Replace this comment with ![Memoria vault](assets/screenshot.png) once the system is running. -->

---

## Where do you want to go?

| I want to…                                  | Go here                                                                                           |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Get set up for the first time**           | [Quickstart — set up your vault](how-to-guides/setup/quickstart.md)                                |
| **Do something specific**                   | [How-to guides](how-to-guides/README.md)                                                          |
| **Look up a field, command, or schema**     | [Reference](reference/README.md)                                                                  |
| **Understand why something works this way** | [Explanation](explanation/README.md)                                                              |
| **Fix something broken**                    | [Failure modes](reference/failure-modes.md) · [Troubleshooting](how-to-guides/troubleshooting/README.md) |

---

## New here? Follow the tutorial sequence

Seven tutorials, each building on the last. Start at 01 and follow the sequence — or jump in at whichever step matches where you are. The full sequence, with what you do and end with at each step, is in [Tutorials](tutorials/README.md).

---

## Common tasks

**First session**
[Quickstart](how-to-guides/setup/quickstart.md) · [Set up Hermes](how-to-guides/setup/set-up-hermes.md) · [Set up the vault homepage](how-to-guides/using-obsidian/use-the-vault-homepage.md) · [Use workspaces](how-to-guides/using-obsidian/use-workspaces.md)

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
| **Engineer**      | Scaffolds handoffs to external coding agents and owns the commit/revert gate  |

Five deterministic **operations** (ingest · search · clustering · sweeps · Linter) do the mechanical work, behind the policy MCP.

→ [Per-agent design rationale](explanation/profiles/README.md) · [Capability and permission table](reference/profiles.md)

---

## Browse the docs

[**Tutorials**](tutorials/README.md) — Guided first experiences, work through in order.

[**How-to guides**](how-to-guides/README.md) — Task-oriented recipes. Setup · Using Obsidian · Using Hermes Agent · Sources · Writing · Maintenance · Recovery.

[**Explanation**](explanation/README.md) — Why Memoria is built the way it is. Architecture · Knowledge model · Profiles · Workflows · Obsidian surfaces.

[**Reference**](reference/README.md) — Exact values, schemas, commands. Frontmatter · Note types · Profiles · Hermes CLI · Policy MCP · Failure modes · Glossary.
