---
title: Reference
nav_order: 4
has_children: true
permalink: /reference/
---

# Reference

Lookup material for Memoria — fields, values, commands, schemas, folder paths. For design rationale and conceptual explanations, see [Explanation](../explanation).

The files are grouped below by domain for scanning; the folder itself is flat.

## Vault data model

| File | What it covers |
| --- | --- |
| [Frontmatter fields](frontmatter.md) | Every YAML frontmatter field: type, allowed values, owner, namespace |
| [Inbox card fields](inbox-card-fields.md) | Field-level contract for candidate, gap, flag, alert, and work-prompt cards |
| [Note types](note-types.md) | The 21 note types: folder, template, lifecycle, promotion map |
| [Vocabulary](vocabulary.md) | Controlled values for `research_area`, `methodology`, and claim `topics` |
| [Wikilink and link conventions](linking.md) | Wikilink conventions, authored-link vocabulary, hub thresholds |
| [Kanban board reference](kanban-board.md) | Kanban state machine, card schema, review overlay, WIP limits |
| [Glossary](glossary.md) | Term definitions, alphabetical |

## Agents and control

| File | What it covers |
| --- | --- |
| [System actions](system-actions.md) | Every action the system performs — operations, MCP servers, crons, the 25 skills, PI palette — with performer and purpose |
| [Operations](operations.md) | Deterministic operation entry points, facades, direct callers, and responsibilities |
| [Profile capabilities](profiles.md) | Lane identifiers, capability table, invocation levels, folder permissions |
| [Linter: detectors and auto-fix](linter.md) | Linter structural detectors, auto-fix classes, and severity scale |
| [Vault eval](vault-eval.md) | The vault-eval gold set, the quarterly dispatch, idempotency keys, and the eval-task schema |
| [Obsidian command palette](obsidian-command-palette.md) | Obsidian `Memoria:` command-palette entries (the in-Obsidian UI surface) |
| [Hermes CLI](hermes-cli.md) | All `hermes …` CLI commands: per-profile research, board management, profile/skills/cron admin |
| [Policy MCP](policy-mcp.md) | Policy MCP: decision values, request/response contract, audit log format, auto-fix classes |
| [Retrieval and analysis methods](computational-toolbox.md) | Deterministic and hybrid methods: embeddings, classifiers, clustering, NLI, graph algorithms |
| [Dashboards](dashboards.md) | The twelve dashboards: source file, sort order, verdict band, trust score, eval metrics, queue counters |

## Pipelines and I/O

| File | What it covers |
| --- | --- |
| [Ingest routing](ingest.md) | Type detection dispatch, per-type enrichment, frontmatter written at ingest |
| [Sweeps](sweeps.md) | Re-ingest and retraction maintenance passes |
| [Export routes and formats](export.md) | Citation states, export routes, editor comparison, deliverable targets |
| [Memory substrates](memory.md) | Memory substrate table, audit log schema, retention (append-only forever) |
| [Telemetry & logs](telemetry.md) | Every operational log under `system/logs/`: exact JSONL schema, cadence, join keys |

## System and infrastructure

| File | What it covers |
| --- | --- |
| [External integrations](integrations.md) | External APIs and tools: enrichment, entity resolution, vault access, execution layer |
| [On-disk layout](on-disk-layout.md) | Vault folder tree, `.memoria/` layout, skeleton notes, naming conventions |
| [System artifacts](system-artifacts.md) | Visible `system/` files, eval fixtures, and shipped Bases views |
| [Installer (bootstrap)](installer.md) | Bootstrap installer: platform matrix, install flow, component checklist, secrets and skills tables |
| [Failure modes](failure-modes.md) | All failure modes by severity: symptom, cause, fix |
| [Bibliography](bibliography.md) | Works cited across the docs, in ACM author-date style; in-text citations link here |

## Obsidian

| File | What it covers |
| --- | --- |
| [Obsidian plugins](obsidian-plugins.md) | Obsidian plugin inventory and load-bearing configuration settings |
| [Zotero plugins](zotero-plugins.md) | Zotero add-ons and the Zotero↔Obsidian connector comparison |
| [Obsidian callouts](obsidian-callouts.md) | Callout type identifiers, trigger conditions, and field schema |
| [Obsidian status line](obsidian-status-line.md) | Status-line format, field definitions, and update cadence |
| [Obsidian workspaces](obsidian-workspaces.md) | Workspace names, layout rules, and switching conventions |
