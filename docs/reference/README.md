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

The reference pages are grouped by domain in the site navigation. Pages that
summarize schema-owned contracts name the owning source rather than mirroring
every field and count.

## [Vault data model](vault-data-model.md)

| File | What it covers | Source |
| --- | --- | --- |
| [Frontmatter fields](frontmatter.md) | Schema-owned YAML frontmatter field grammar and ownership | Source-owned |
| [Inbox card fields](inbox-card-fields.md) | Stable target recording that alpha.15 has no durable Inbox-card Concept schemas | Manual |
| [Document types](document-types.md) | Schema-owned document types and owning files | Source-owned |
| [Vocabulary](vocabulary.md) | Vocabulary-source values for Work `research_area`/`methodology` metadata and claim-bearing note `topics` | Guarded mirror |
| [Wikilink and link conventions](wikilink-and-link-conventions.md) | Wikilink conventions, authored-link vocabulary, hub thresholds | Manual |
| [Control plane reference](control-plane.md) | Request-control commands and state | Manual |
| [Glossary](glossary.md) | Term definitions, alphabetical | Manual |

## [Agents and control](agents-and-control.md)

| File | What it covers | Source |
| --- | --- | --- |
| [System actions](system-actions.md) | Every action the system performs — operations, scheduled tasks, optional adapters, and PI actions — with performer and purpose | Guarded mirror |
| [Operations](operations.md) | Deterministic operation entry points, facades, direct callers, and responsibilities | Manual |
| [CLI](cli.md) | Alpha.15 `memoria` command surface | Manual |
| [Project structural impact](project-structural-impact.md) | Project-gate structural-impact command, generated index payload, and write behavior | Manual |
| [Worklists](worklists.md) | Batch worklist report JSON, emitted item notes, and aggregate review prompt contract | Manual |
| [Linter: detectors and auto-fix](linter.md) | Linter structural detectors, auto-fix classes, and severity scale | Manual |
| [Vault eval](vault-eval.md) | The vault-eval gold set, quarterly dispatch, idempotency keys, and diagnostic eval fixtures | Manual |
| [Policy gate](policy-mcp.md) | Runtime policy hook, optional adapter contract, audit pairing, and fail-closed behavior | Manual |
| [Policy audit log](policy-audit-log.md) | Audit-log fields, JSON example, decision enum, and per-write hash pairing | Manual |
| [Policy auto-fix](policy-auto-fix.md) | Auto-fix classes and dispositions enforced by the policy gate | Manual |
| [Retrieval and analysis methods](retrieval-and-analysis-methods.md) | Deterministic methods: BM25 retrieval, API calls, and graph algorithms | Manual |
| [Calibration](calibration.md) | Drift-bound threshold contracts and shadow-first score calibration | Source-owned |
| [Dashboards](dashboards.md) | Space dashboards, Inbox, Maintenance, support dashboards, Bases views, verdict bands, and rail badges | Manual |
| [Prompt operations](prompt-operations.md) | Shipped prompt operations, manifest schema, and runner contract | Manual |
| [Clustering](clustering.md) | Alpha.15 graph retrieval baseline and non-shipped heavy clustering boundary | Manual |

## [Pipelines and I/O](pipelines-and-io.md)

| File | What it covers | Source |
| --- | --- | --- |
| [Ingest routing](ingest.md) | Type detection dispatch, per-type enrichment, frontmatter written at ingest | Manual |
| [Sweeps](sweeps.md) | Retraction maintenance passes | Manual |
| [Search](search.md) | search retrieval surface: checked-only BM25 baseline, consumers, index, and limits | Manual |
| [Export routes and formats](export.md) | Citation states, export routes, editor comparison, deliverable targets | Manual |
| [Memory substrates](memory-substrates.md) | Memory substrate table, audit log schema, retention | Manual |
| [Telemetry & logs](telemetry.md) | Operational log inventory, JSONL conventions, cadence, and join keys | Manual |
| [Telemetry log schemas](telemetry-logs.md) | Exact JSONL schemas for current runtime logs | Manual |
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
| [Pattern provenance table](pattern-provenance.md) | Borrow/adapt/reference/ignore judgments for surveyed AI-research-system patterns | Manual |
| [Bibliography](bibliography.md) | Works cited across the docs in ACM author-date style | Manual |

## [Obsidian and Zotero](obsidian-and-zotero.md)

| File | What it covers | Source |
| --- | --- | --- |
| [Zotero plugins](zotero-plugins.md) | Zotero add-ons and the Zotero↔Obsidian connector comparison | Manual |
