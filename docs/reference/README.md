---
title: Reference
nav_order: 13
has_children: true
permalink: /reference/
---

# Reference

Lookup material for Memoria — fields, values, commands, schemas, folder paths,
and runtime contracts. For design rationale and decision history, see
[Developers](../developers.md); for operational explanations, see
[Explanation](../explanation).

The reference pages are grouped by domain in the site navigation. Generated and
guarded pages name their source so field lists, rosters, and counts do not become
manual mirrors.

## [Vault data model](vault-data-model.md)

| File | What it covers | Source |
| --- | --- | --- |
| [Frontmatter fields](frontmatter.md) | Schema-owned YAML frontmatter fields: type, allowed values, owner, namespace | Generated |
| [Inbox card fields](inbox-card-fields.md) | Schema-owned field contract for candidate, gap, flag, alert, and work-prompt cards | Generated |
| [Document types](document-types.md) | Schema-owned document types: folder, template, lifecycle, promotion map | Generated |
| [Vocabulary](vocabulary.md) | Vocabulary-source values for `research_area`, `methodology`, and claim `topics` | Guarded mirror |
| [Wikilink and link conventions](linking.md) | Wikilink conventions, authored-link vocabulary, hub thresholds | Manual |
| [Kanban board reference](kanban-board.md) | Kanban state machine, card schema, review overlay, WIP limits | Manual |
| [Glossary](glossary.md) | Term definitions, alphabetical | Manual |

## [Agents and control](agents-and-control.md)

| File | What it covers | Source |
| --- | --- | --- |
| [System actions](system-actions.md) | Every action the system performs — operations, MCP servers, crons, skills, PI palette — with performer and purpose | Guarded mirror |
| [Operations](operations.md) | Deterministic operation entry points, facades, direct callers, and responsibilities | Manual |
| [Project structural impact](project-structural-impact.md) | Project-gate structural-impact command, generated index payload, and write behavior | Manual |
| [Worklists](worklists.md) | Batch worklist report JSON, emitted item notes, and aggregate review prompt contract | Manual |
| [Profile capabilities](profiles.md) | Lane identifiers, capability table, invocation levels, folder permissions | Generated |
| [Linter: detectors and auto-fix](linter.md) | Linter structural detectors, auto-fix classes, and severity scale | Manual |
| [Vault eval](vault-eval.md) | The vault-eval gold set, quarterly dispatch, idempotency keys, and eval-task schema | Manual |
| [Obsidian command palette](obsidian-command-palette.md) | Obsidian `Memoria:` command-palette entries | Guarded mirror |
| [Hermes CLI](hermes-cli.md) | All `hermes …` CLI commands for research, board management, profile, skills, and cron admin | Guarded mirror |
| [Policy MCP](policy-mcp.md) | Policy MCP decision values, request/response contract, tools, lane overrides, and enforcement | Manual |
| [Policy audit log](policy-audit-log.md) | Audit-log fields, JSON example, decision enum, and per-write hash pairing | Manual |
| [Policy auto-fix](policy-auto-fix.md) | Auto-fix classes and dispositions enforced by the policy gate | Manual |
| [Retrieval and analysis methods](computational-toolbox.md) | Deterministic and hybrid methods: embeddings, classifiers, clustering, NLI, graph algorithms | Manual |
| [Calibration](calibration.md) | Drift-bound threshold contracts and shadow-first score calibration | Generated |
| [Dashboards](dashboards.md) | Space dashboards, Inbox, Maintenance, support dashboards, Bases views, verdict bands, and rail badges | Manual |
| [Pattern library](patterns.md) | Shipped patterns, pattern-note schema, runner contract, gated-target dry-run, and provenance | Manual |
| [Clustering](clustering.md) | Cluster MCP graph build, claim-debate Canvas, BERTopic topics, parameters, outputs, and opt-in stack | Manual |

## [Pipelines and I/O](pipelines-and-io.md)

| File | What it covers | Source |
| --- | --- | --- |
| [Ingest routing](ingest.md) | Type detection dispatch, per-type enrichment, frontmatter written at ingest | Manual |
| [Sweeps](sweeps.md) | Re-ingest and retraction maintenance passes | Manual |
| [Search](search.md) | qmd retrieval surface: hybrid BM25 + vector + rerank, MCP, consumers, index, and limits | Manual |
| [Export routes and formats](export.md) | Citation states, export routes, editor comparison, deliverable targets | Manual |
| [Memory substrates](memory.md) | Memory substrate table, audit log schema, retention | Manual |
| [Telemetry & logs](telemetry.md) | Operational log inventory, JSONL conventions, cadence, and join keys | Manual |
| [Telemetry log schemas](telemetry-logs.md) | Exact JSONL schemas and derived metric-note contracts | Manual |
| [Board export](board-export.md) | Hermes Kanban projection command, generated board files, event logs, and cost-join failure modes | Manual |
| [Fleet metrics](fleet-metrics.md) | Weekly lane metrics, trust-score formula, inputs, bands, and low-confidence behavior | Manual |
| [Diagnostics](diagnostics.md) | Local diagnostics location, redaction, raw-capture, and support-bundle contract | Manual |

## [System and infrastructure](system-and-infrastructure.md)

| File | What it covers | Source |
| --- | --- | --- |
| [External integrations](integrations.md) | External APIs and tools: enrichment, entity resolution, vault access, execution layer | Manual |
| [Memoria configuration](configuration.md) | Configuration surfaces, source/installed ownership, redeploy triggers, and secret boundaries | Generated |
| [On-disk layout](on-disk-layout.md) | Vault folder tree, `.memoria/` layout, skeleton notes, naming conventions | Manual |
| [System artifacts](system-artifacts.md) | Visible `system/` files, eval fixtures, and shipped Bases views | Manual |
| [Installer (bootstrap)](installer.md) | Bootstrap installer: platform matrix, install flow, component checklist, secrets and skills tables | Manual |
| [Failure modes](failure-modes.md) | Failure modes by severity: symptom, cause, fix | Manual |
| [Sample vault](sample-vault.md) | Bundled tutorial corpus, catalog papers, source notes, and sample labels | Guarded mirror |
| [Bibliography](bibliography.md) | Works cited across the docs in ACM author-date style | Manual |

## [Obsidian and Zotero](obsidian-and-zotero.md)

| File | What it covers | Source |
| --- | --- | --- |
| [Obsidian plugins](obsidian-plugins.md) | Obsidian plugin inventory, install status, and evaluated alternatives | Guarded mirror |
| [Obsidian plugin settings](obsidian-plugin-settings.md) | Load-bearing per-plugin settings | Manual |
| [Obsidian plugin data files](obsidian-plugin-data-files.md) | `data.json`, `.example`, generated, and secret-bearing config conventions | Manual |
| [Zotero plugins](zotero-plugins.md) | Zotero add-ons and the Zotero↔Obsidian connector comparison | Manual |
| [Obsidian callouts](obsidian-callouts.md) | Callout type identifiers, trigger conditions, and field schema | Manual |
| [Obsidian workspaces](obsidian-workspaces.md) | The Memoria reset layout and navigation-rail space-switching model | Manual |
