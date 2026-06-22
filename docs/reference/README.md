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
| [Note types](note-types.md) | The 24 note types: folder, template, lifecycle, promotion map |
| [Vocabulary](vocabulary.md) | Controlled values for `research_area`, `methodology`, and claim `topics` |
| [Wikilink and link conventions](linking.md) | Wikilink conventions, authored-link vocabulary, hub thresholds |
| [Kanban board reference](kanban-board.md) | Kanban state machine, card schema, review overlay, WIP limits |
| [Glossary](glossary.md) | Term definitions, alphabetical |

## Agents and control

| File | What it covers |
| --- | --- |
| [System actions](system-actions.md) | Every action the system performs — operations, MCP servers, crons, the 27 skills, PI palette — with performer and purpose |
| [Operations](operations.md) | Deterministic operation entry points, facades, direct callers, and responsibilities |
| [Project structural impact](project-structural-impact.md) | Project-gate structural-impact command, generated index payload, and write behavior |
| [Worklists](worklists.md) | Batch worklist report JSON, emitted item notes, and aggregate review prompt contract |
| [Profile capabilities](profiles.md) | Lane identifiers, capability table, invocation levels, folder permissions |
| [Linter: detectors and auto-fix](linter.md) | Linter structural detectors, auto-fix classes, and severity scale |
| [Vault eval](vault-eval.md) | The vault-eval gold set, the quarterly dispatch, idempotency keys, and the eval-task schema |
| [Obsidian command palette](obsidian-command-palette.md) | Obsidian `Memoria:` command-palette entries (the in-Obsidian UI surface) |
| [Hermes CLI](hermes-cli.md) | All `hermes …` CLI commands: per-profile research, board management, profile/skills/cron admin |
| [Policy MCP](policy-mcp.md) | Policy MCP: decision values, request/response contract, tools, lane overrides, and enforcement |
| [Policy audit log](policy-audit-log.md) | Audit-log fields, JSON example, decision enum, and per-write hash pairing |
| [Policy auto-fix](policy-auto-fix.md) | Auto-fix classes and dispositions enforced by the policy gate |
| [Retrieval and analysis methods](computational-toolbox.md) | Deterministic and hybrid methods: embeddings, classifiers, clustering, NLI, graph algorithms |
| [Calibration](calibration.md) | Drift-bound threshold contracts and shadow-first score calibration |
| [Dashboards](dashboards.md) | The four space dashboards, thirteen support dashboards, and Bases views: source file, sort order, verdict band, trust score, eval metrics, queue counters |
| [Pattern library](patterns.md) | The shipped patterns, the pattern-note schema, the `patterns_list`/`patterns_run` contract, gated-target dry-run, and provenance |
| [Clustering](clustering.md) | The cluster MCP: graph build, claim-debate Canvas, BERTopic topics — parameters, outputs, and the opt-in stack |

## Pipelines and I/O

| File | What it covers |
| --- | --- |
| [Ingest routing](ingest.md) | Type detection dispatch, per-type enrichment, frontmatter written at ingest |
| [Sweeps](sweeps.md) | Re-ingest and retraction maintenance passes |
| [Search](search.md) | The qmd retrieval surface: hybrid BM25 + vector + rerank, the MCP, consumers, the index, and limits |
| [Export routes and formats](export.md) | Citation states, export routes, editor comparison, deliverable targets |
| [Memory substrates](memory.md) | Memory substrate table, audit log schema, retention (append-only forever) |
| [Telemetry & logs](telemetry.md) | Operational log inventory, JSONL conventions, cadence, and join keys |
| [Telemetry log schemas](telemetry-logs.md) | Exact JSONL schemas and derived metric-note contracts |
| [Board export](board-export.md) | Hermes Kanban projection command, generated board files, event logs, and cost-join failure modes |
| [Fleet metrics](fleet-metrics.md) | Weekly lane metrics, trust-score formula, inputs, bands, and low-confidence behavior |
| [Diagnostics](diagnostics.md) | Local diagnostics location, redaction, raw-capture, and support-bundle contract |

## System and infrastructure

| File | What it covers |
| --- | --- |
| [External integrations](integrations.md) | External APIs and tools: enrichment, entity resolution, vault access, execution layer |
| [Memoria configuration](configuration.md) | Configuration surfaces, source/installed ownership, redeploy triggers, and secret boundaries |
| [On-disk layout](on-disk-layout.md) | Vault folder tree, `.memoria/` layout, skeleton notes, naming conventions |
| [System artifacts](system-artifacts.md) | Visible `system/` files, eval fixtures, and shipped Bases views |
| [Installer (bootstrap)](installer.md) | Bootstrap installer: platform matrix, install flow, component checklist, secrets and skills tables |
| [Failure modes](failure-modes.md) | All failure modes by severity: symptom, cause, fix |
| [Bibliography](bibliography.md) | Works cited across the docs, in ACM author-date style; in-text citations link here |

## Obsidian

| File | What it covers |
| --- | --- |
| [Obsidian plugins](obsidian-plugins.md) | Obsidian plugin inventory, install status, and evaluated alternatives |
| [Obsidian plugin settings](obsidian-plugin-settings.md) | Load-bearing per-plugin settings |
| [Obsidian plugin data files](obsidian-plugin-data-files.md) | `data.json`, `.example`, generated, and secret-bearing config conventions |
| [Zotero plugins](zotero-plugins.md) | Zotero add-ons and the Zotero↔Obsidian connector comparison |
| [Obsidian callouts](obsidian-callouts.md) | Callout type identifiers, trigger conditions, and field schema |
| [Obsidian workspaces](obsidian-workspaces.md) | The Memoria reset layout and the persistent space-dashboard navigation model |
