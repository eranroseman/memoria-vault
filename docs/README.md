---
title: Home
nav_order: 1
permalink: /
topic: overview
---

# Memoria

A local research operating system for one principal investigator: capture
sources, turn them into checked knowledge, and draft from a review-gated
workspace.

The standalone CLI and engine handle capture, enrichment, mapping, verification,
and checked retrieval. The PI keeps judgment: proposed changes and dispositions
are recorded before material enters checked knowledge.

If you want a guided first experience, start with the
[Quickstart](how-to-guides/setup/quickstart.md). If you need to _do_
something, see [How-to guides](how-to-guides/). If you need exact values, field
names, or configuration formats, see [Reference](reference/).

**Status: v0.1 alpha source install** — alpha.21 is the latest closed
checkpoint; the formal package/tag release gate remains open. ·
[GitHub](https://github.com/eranroseman/memoria-vault) ·
[Install](https://github.com/eranroseman/memoria-vault#install) ·
[Issues](https://github.com/eranroseman/memoria-vault/issues)

---

## The model

Memoria is a single-researcher operating system for turning sources into defensible
claims and drafts. It is not an autonomous researcher. The PI owns judgment; Memoria
keeps the work visible, traceable, and review-gated.

### The five terms

| Term | Meaning |
| --- | --- |
| PI | The human principal investigator. The PI decides what enters the vault and what can be cited. |
| Co-PI | The read-only conversational posture behind `memoria ask`. See [The Co-PI](explanation/execution/operation-postures/co-pi.md) for its full mission. |
| Operations | Checked capability-backed units of work such as capture, enrich, digest, ask, verify, and export. |
| Request table | The SQLite control plane. It records operation requests, status, blockers, review, and completion. |
| Workspace | The local folder tree. It holds knowledge bundles, catalog state, attention projections, and system outputs. |

### The working loop

1. Capture or find a source.
2. Capture and enrich it into the catalog.
3. Distill checked Works into notes.
4. Link claims into a project argument.
5. Draft from current claims.
6. Verify the draft and resolve findings.
7. Archive or revise as the project changes.

The loop compounds because each step leaves a typed, linkable artifact in the vault.
Nothing important depends only on chat history.

### The control rule

Operations propose; the PI disposes. CLI commands, observed file changes, and
scheduled jobs can create request rows, attention prompts, and staged outputs
within their manifest scope. Promotion into review-gated knowledge stays
PI-directed and policy-gated.

---

## Where do you want to go?

| I want to…                                  | Go here                                                                                           |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Understand the system model**             | [The model](#the-model)                                                                           |
| **Get set up for the first time**           | [Quickstart — set up your vault](how-to-guides/setup/quickstart.md)                                |
| **Do something specific**                   | [How-to guides](how-to-guides/README.md)                                                          |
| **Look up a field, command, or schema**     | [Reference](reference/README.md)                                                                  |
| **Understand how the system fits together** | [Explanation](explanation/README.md)                                                              |
| **Understand why it is designed this way** | [Design rationale](explanation/rationale/README.md)                                                |
| **Fix something broken**                    | [Failure modes](reference/system/failure-modes.md) · [Troubleshooting](how-to-guides/troubleshooting/README.md) |

---

## New here?

Start with [Quickstart](how-to-guides/setup/quickstart.md), then walk through
the [Tutorials](tutorials/README.md). The tutorials use the standalone
CLI/runtime path and point to task guides when you need more detail.

---

## Reading path

Use this path when you want the system model before doing a full workflow.

1. [What Memoria is](explanation/rationale/foundations/what-memoria-is.md)
2. [Architecture](explanation/architecture/README.md)
3. [The vault](explanation/architecture/vault.md)
4. [The knowledge cycle](explanation/knowledge/knowledge-cycle.md)
5. [The control plane](explanation/execution/control-plane/README.md)
6. [Design rationale](explanation/rationale/README.md)

Then use [Quickstart](how-to-guides/setup/quickstart.md) and
[Tutorials](tutorials/README.md) to learn the current workflow by doing it.

---

## Common tasks

**First session**
[Quickstart](how-to-guides/setup/quickstart.md) · [Set up the vault](how-to-guides/setup/set-up-the-vault.md)

**Daily work — sources**
[Capture and ingest](how-to-guides/library/capture-and-ingest.md) · [Discuss a paper](how-to-guides/library/discuss-a-paper.md)

**Daily work — knowledge and projects**
[Query the vault](how-to-guides/knowledge/query-the-vault.md) · [Build a hub](how-to-guides/knowledge/build-a-hub.md) · [Analyze a project argument](how-to-guides/project/analyze-a-project-argument.md) · [Export a draft](how-to-guides/project/export-a-draft.md)

**Weekly**
[Return to work](how-to-guides/inbox/return-to-work.md) · [Weekly review](how-to-guides/inbox/run-the-weekly-review.md) · [Run the Linter](how-to-guides/operate/run-the-linter.md)

**Troubleshooting**
[Safe mode](how-to-guides/troubleshooting/safe-mode.md) · [Failure modes reference](reference/system/failure-modes.md)

---

## Current status and limitations

Memoria is in the **v0.1 alpha source-install** phase: the installer and CLI
engine are being validated as a standalone local product. What is not working today:

- **Release-candidate validation is still pending** — the offline runtime gate
  replays capture, enrich, digest, ask, project writing/export, recovery, and
  seeded-error evidence (`scripts/verify`), but the RC still needs a live
  provider/package run before release.
- **Mobile capture is not available** — only urgent push (via Telegram) ships today; inbound capture from a phone is planned ([#382](https://github.com/eranroseman/memoria-vault/issues/382)). See [Architecture](explanation/architecture/README.md#interaction-channels).
- **No autonomous code-experiment loop** — provenance-tracked code experiments are future work.
- **Broad writability scoring is not implemented** — the current alpha baseline
  has structural draft verification and project export readiness, but it does not decide
  whether developed claims are ready to become prose.
- **Single-user only** — team and multi-user review are out of scope by design.
- **macOS is not supported** — only Linux (including WSL2) and Windows are tested.
Throughout the docs, unshipped capabilities are marked *planned* or *deferred*;
nothing here implies they work yet.

---

## Browse the docs

[**Tutorials**](tutorials/README.md) — Guided first workflow over the current CLI/runtime.

[**How-to guides**](how-to-guides/README.md) — Task recipes.

[**Reference**](reference/README.md) — Exact fields, commands, schemas, settings, and paths.

[**Explanation**](explanation/README.md) — Architecture, workflows, conceptual model, and design rationale.

---

## Documentation conventions

For contributors editing these docs. Generic Diátaxis craft is a separate,
invoke-only skill; the rules below are the Memoria-specific ones.

- **Routing:** tutorials teach, how-to guides direct, reference informs,
  explanation discusses. Mixed-purpose pages are wrong — split them.
- **Links:** inside `docs/`, use relative links following the target's Pages
  route. Link unpublished targets (root files, `design-history/`) by GitHub blob
  URL. Never relative-link into `src/` (those 404 on the site) — cite a source
  file as an inline-code path.
- **Indexing:** every new page goes in its section README (how-to pages also in
  `how-to-guides/README.md`); set `nav_order` for a logical sequence.
- **Citations:** new works go in `reference/evidence-and-integrations/bibliography.md`
  (ACM author-date, `<a id>` anchor); link in-text mentions to the published anchor.
- **Spelling:** American English (`-ize`/`-or`); `cspell` is the gate. Add a real
  unknown term to `project-words.txt` (lowercase, sorted) — never inline-suppress.
