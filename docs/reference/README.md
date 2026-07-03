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
| [Inbox card fields](inbox-card-fields.md) | Stable target recording that alpha.14 has no durable Inbox-card Concept schemas | Generated |
| [Document types](document-types.md) | Schema-owned document types: folder, template, lifecycle, promotion map | Generated |
| [Vocabulary](vocabulary.md) | Vocabulary-source values for `research_area`, `methodology`, and claim `topics` | Guarded mirror |
| [Wikilink and link conventions](wikilink-and-link-conventions.md) | Wikilink conventions, authored-link vocabulary, hub thresholds | Manual |
| [Kanban board reference](kanban-board.md) | No-Hermes-board contract and current request-control commands | Manual |
| [Glossary](glossary.md) | Term definitions, alphabetical | Manual |

## [Agents and control](agents-and-control.md)

| File | What it covers | Source |
| --- | --- | --- |
| [System actions](system-actions.md) | Every action the system performs — operations, scheduled tasks, optional adapters, and PI actions — with performer and purpose | Guarded mirror |
| [Operations](operations.md) | Deterministic operation entry points, facades, direct callers, and responsibilities | Manual |
| [CLI](cli.md) | Alpha.15 `memoria` command surface | Manual |
| [Project structural impact](project-structural-impact.md) | Project-gate structural-impact command, generated index payload, and write behavior | Manual |
| [Worklists](worklists.md) | Batch worklist report JSON, emitted item notes, and aggregate review prompt contract | Manual |
| [Installed profiles](profile-capabilities.md) | Alpha.14 no-installed-profile contract | Manual |
| [Linter: detectors and auto-fix](linter.md) | Linter structural detectors, auto-fix classes, and severity scale | Manual |
| [Vault eval](vault-eval.md) | The vault-eval gold set, quarterly dispatch, idempotency keys, and diagnostic eval fixtures | Manual |
| [Obsidian command palette](obsidian-command-palette.md) | Obsidian `Memoria:` command-palette entries | Guarded mirror |
| [Hermes CLI](hermes-cli.md) | Alpha.14 boundary for the optional future Hermes adapter | Manual |
| [Policy gate](policy-mcp.md) | Runtime policy hook, optional adapter contract, audit pairing, and fail-closed behavior | Manual |
| [Policy audit log](policy-audit-log.md) | Audit-log fields, JSON example, decision enum, and per-write hash pairing | Manual |
| [Policy auto-fix](policy-auto-fix.md) | Auto-fix classes and dispositions enforced by the policy gate | Manual |
| [Retrieval and analysis methods](retrieval-and-analysis-methods.md) | Deterministic methods: BM25 retrieval, classifiers, clustering, API calls, and graph algorithms | Manual |
| [Calibration](calibration.md) | Drift-bound threshold contracts and shadow-first score calibration | Generated |
| [Dashboards](dashboards.md) | Space dashboards, Inbox, Maintenance, support dashboards, Bases views, verdict bands, and rail badges | Manual |
| [Pattern library](pattern-library.md) | Shipped patterns, pattern-note schema, runner contract, gated-target dry-run, and provenance | Manual |
| [Clustering](clustering.md) | Alpha.14 graph retrieval baseline and non-shipped heavy clustering boundary | Manual |

## [Pipelines and I/O](pipelines-and-io.md)

| File | What it covers | Source |
| --- | --- | --- |
| [Ingest routing](ingest.md) | Type detection dispatch, per-type enrichment, frontmatter written at ingest | Manual |
| [Sweeps](sweeps.md) | Re-ingest and retraction maintenance passes | Manual |
| [Search](search.md) | qmd retrieval surface: checked-only BM25 baseline, consumers, index, and limits | Manual |
| [Export routes and formats](export.md) | Citation states, export routes, editor comparison, deliverable targets | Manual |
| [Memory substrates](memory-substrates.md) | Memory substrate table, audit log schema, retention | Manual |
| [Telemetry & logs](telemetry.md) | Operational log inventory, JSONL conventions, cadence, and join keys | Manual |
| [Telemetry log schemas](telemetry-logs.md) | Exact JSONL schemas for current runtime logs plus historical log boundaries | Manual |
| [Board export](board-export.md) | Alpha.15 no-board-export boundary and replacement request/journal surfaces | Manual |
| [Fleet metrics](fleet-metrics.md) | Alpha.14 no-fleet-runtime boundary and replacement runtime signals | Manual |
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
| [Sample vault](sample-vault.md) | Retired alpha.10 tutorial corpus; not shipped in alpha.11 | Manual |
| [Pattern provenance table](pattern-provenance.md) | Borrow/adapt/reference/ignore judgments for surveyed AI-research-system patterns | Manual |
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
