---
title: Home
nav_order: 1
permalink: /
---

# Memoria

A research operating system for a single researcher — seven AI agents that read, enrich, map, verify, and write inside your Obsidian vault, under a human-approval gate that audits every proposed change before it lands.

**[Read about what Memoria is](explanation/overview/what-memoria-is.md)**, what it's not, and why it exists. Everything else builds on this.
If you want a guided first experience, see [Tutorials](tutorials/).
If you need to _do_ something, see [how-to guides](how-to-guides/).
If you need exact values, field names, or configuration formats, see [Reference](reference/).

**v0.1** — installer validated; not yet run end-to-end on a live Hermes. · [GitHub](https://github.com/eranroseman/memoria-vault) · [Install](https://github.com/eranroseman/memoria-vault#install) · [Issues](https://github.com/eranroseman/memoria-vault/issues)

<!-- SCREENSHOT: Replace this comment with ![Memoria vault](assets/screenshot.png) once the system is running. -->

---

## Where do you want to go?

| I want to…                                  | Go here                                                                                           |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Get set up for the first time**           | [Tutorial 01 — Set up from zero](tutorials/01-set-up-from-zero.md)                                |
| **Do something specific**                   | [How-to guides](how-to-guides/README.md)                                                          |
| **Look up a field, command, or schema**     | [Reference](reference/README.md)                                                                  |
| **Understand why something works this way** | [Explanation](explanation/README.md)                                                              |
| **Fix something broken**                    | [Failure modes](reference/failure-modes.md) · [Recovery guides](how-to-guides/recovery/README.md) |

---

## New here? Follow the tutorial sequence

Seven tutorials, each building on the last. Start at 01 and follow the sequence — or jump in at whichever step matches where you are.

| Tutorial                                                                 | What you'll do                                           | You'll end with                                     |
| ------------------------------------------------------------------------ | -------------------------------------------------------- | --------------------------------------------------- |
| [01 — Set up from zero](tutorials/01-set-up-from-zero.md)                | Clone the vault, run the installer, wire Zotero          | A working vault, all plugins, all seven profiles    |
| [02 — Your first note](tutorials/02-your-first-note.md)                  | Capture a thought, discuss it, write a claim note        | One permanent claim note in your own words          |
| [03 — Bring in a paper](tutorials/03-bring-in-a-paper.md)                | Ingest one Zotero paper, classify it, distill one claim  | One paper-note and one linked claim-note            |
| [04 — Build a reading batch](tutorials/04-build-a-reading-batch.md)      | Ingest five papers, write three linked claim notes       | Your first connected knowledge cluster              |
| [05 — Start a writing project](tutorials/05-start-a-writing-project.md)  | Read the corpus map, commit a framing                    | A project folder with map and chosen outline        |
| [06 — Verify and address a gap](tutorials/06-verify-and-address-gaps.md) | Write a draft paragraph, run verification, close the gap | A verified draft with a complete citation trail     |
| [07 — Find new sources](tutorials/07-find-new-sources.md)                | Run forward-citation search, triage candidates           | A populated candidates queue and one new paper-note |

---

## Common tasks

**First session**
[Quickstart](how-to-guides/setup/quickstart.md) · [Set up Hermes](how-to-guides/setup/set-up-hermes.md) · [Set up the vault homepage](how-to-guides/using-obsidian/use-the-vault-homepage.md) · [Use workspaces](how-to-guides/using-obsidian/use-workspaces.md)

**Daily work — sources**
[Find new sources](how-to-guides/compile/find-new-sources.md) · [Capture and ingest](how-to-guides/compile/capture-and-ingest.md) · [Classify a source](how-to-guides/compile/classify-a-source.md) · [Write a claim note](how-to-guides/compile/write-a-claim-note.md)

**Daily work — writing**
[Query the vault](how-to-guides/compose/query-the-vault.md) · [Assess your corpus](how-to-guides/compose/assess-your-corpus.md) · [Draft with Writer](how-to-guides/compose/draft-with-writer.md) · [Verify and revise](how-to-guides/compose/verify-and-revise.md)

**Weekly**
[Return to work](how-to-guides/maintain/return-to-work.md) · [Weekly review](how-to-guides/maintain/run-the-weekly-review.md) · [Run the Linter](how-to-guides/maintain/run-the-linter.md)

**Recovery**
[Safe mode](how-to-guides/recovery/safe-mode.md) · [Failure modes reference](reference/failure-modes.md)

---

## The seven agents

| Agent         | What it does                                                                 |
| ------------- | ---------------------------------------------------------------------------- |
| **Librarian** | Fetches sources, enriches metadata, proposes classifications — intake layer  |
| **Mapper**    | Produces corpus maps, gap reports, and cluster maps — read-only              |
| **Socratic**  | Asks questions to sharpen your thinking — architecturally write-denied       |
| **Writer**    | Turns evidence into draft prose — lands in review, never direct to canonical |
| **Verifier**  | Traces claims to sources, flags retractions, catches near-duplicates         |
| **Coder**     | Scaffolds handoffs to external coding agents (Claude Code, Aider)            |
| **Linter**    | Zero-LLM structural validator — frontmatter, links, schema, audit logs       |

→ [Per-agent design rationale](explanation/profiles/README.md) · [Capability and permission table](reference/profiles.md)

---

## Browse the docs

[**Tutorials**](tutorials/README.md) — Guided first experiences, work through in order.

[**How-to guides**](how-to-guides/README.md) — Task-oriented recipes. Setup · Using Obsidian · Using Hermes Agent · Sources · Writing · Maintenance · Recovery.

[**Explanation**](explanation/README.md) — Why Memoria is built the way it is. Architecture · Knowledge model · Profiles · Workflows · Obsidian surfaces.

[**Reference**](reference/README.md) — Exact values, schemas, commands. Frontmatter · Note types · Profiles · Hermes CLI · Policy MCP · Failure modes · Glossary.
