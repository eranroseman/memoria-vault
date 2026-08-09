---
title: Overview
nav_order: 2
permalink: /overview/
topic: overview
---

# Overview

Memoria is a single-researcher operating system for turning sources into
defensible claims and drafts. The engine proposes; the PI disposes. This is a
compact orientation, not a second glossary or workflow manual: use the linked
owners for exact terms and detailed behavior.

## The five terms

| Term | Orientation |
| --- | --- |
| [PI](reference/data-model/glossary.md#pi) | The human principal investigator, who owns judgment, curation, dispositions, and citation decisions. |
| [Co-PI](reference/data-model/glossary.md#co-pi) | The read-only research-partner role behind `memoria ask`; see [The Co-PI](explanation/execution/operation-postures/co-pi.md) for its full mission. |
| [Operations](reference/data-model/glossary.md#operation) | Capability-backed units of work such as capture, enrich, digest, ask, verify, and export. |
| [Request table](reference/data-model/glossary.md#task-request) | The SQLite control plane that records operation requests, status, blockers, review, and completion. |
| [Workspace](reference/data-model/glossary.md#workspace) | The local folder tree holding Knowledge Bundles, catalog state, attention projections, and system outputs. |

The [Glossary](reference/data-model/glossary.md) owns the canonical definitions.

## The working loop

1. Find a source.
2. Capture and enrich it into the catalog.
3. Distill checked Works into notes.
4. Link claims into a project argument.
5. Draft from current claims.
6. Verify the draft and resolve findings.
7. Archive or revise as the project changes.

The loop compounds because each step leaves a typed, linkable artifact in the
vault. Nothing important depends only on chat history. [The knowledge
cycle](explanation/knowledge/knowledge-cycle.md) develops the workflow, its
gates, and its feedback loop.

## The control rule

Operations propose; the PI disposes. CLI commands, observed file changes, and
scheduled jobs can create request rows, attention prompts, and staged outputs
within their manifest scope. Admission to checked readers is policy-gated; it
means the applicable checks and grounds passed, not that the PI judged content
true or complete. PI-directed routes remain responsible for judgment,
curation, and disposition.

For the mechanical boundary, see [Promotion and the write
boundary](explanation/knowledge/promotion-and-gated-zones.md). For the PI's
separate judgment gate, see [Why the review gate is
structural](explanation/rationale/boundaries/why-review-gate-is-structural.md).
