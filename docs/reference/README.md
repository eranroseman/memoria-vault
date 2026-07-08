---
title: Reference
nav_order: 4
has_children: true
permalink: /reference/
---

# Reference

Lookup material for Memoria — fields, values, commands, schemas, folder paths,
and runtime contracts. For design rationale and decision history, see
[Design](../explanation/rationale/README.md); for operational explanations, see
[Explanation](../explanation/).

The site navigation and this index group reference pages by domain. Pages that
summarize schema-owned contracts name the owning source rather than mirroring
every field and count.

## Vault data model

| File | What it covers | Source |
| --- | --- | --- |
| [Frontmatter fields](data-model/frontmatter.md) | Schema-owned YAML frontmatter field grammar and ownership | Source-owned |
| [Document types](data-model/document-types.md) | Schema-owned document types, owning files, and retired Inbox-card Concept status | Source-owned |
| [Vocabulary](data-model/vocabulary.md) | Vocabulary-source values for Work `research_area`/`methodology` metadata and claim-bearing note `topics` | Guarded mirror |
| [Wikilink and link conventions](data-model/wikilink-and-link-conventions.md) | Wikilink conventions, authored-link vocabulary, hub thresholds | Manual |
| [Glossary](data-model/glossary.md) | Term definitions, alphabetical | Manual |

## Commands and transports

| File | What it covers | Source |
| --- | --- | --- |
| [System actions](commands-and-transports/system-actions.md) | Guarded operation manifest roster and map of action catalogs | Guarded mirror |
| [System action operations](commands-and-transports/system-actions-operations.md) | Deterministic operations, runtime policy helpers, and subsystem helpers | Manual |
| [System action CLI and PI flows](commands-and-transports/system-actions-cli-and-pi.md) | CLI requests plus PI review and recovery decisions | Manual |
| [System action adapters](commands-and-transports/system-actions-adapters.md) | Optional external adapters and reusable prompt surfaces | Manual |
| [System action scheduled tasks](commands-and-transports/system-actions-scheduled.md) | Optional local scheduler wiring around the CLI/runtime package | Manual |
| [Operations](commands-and-transports/operations.md) | Deterministic operation entry points, facades, direct callers, and responsibilities | Manual |
| [CLI](commands-and-transports/cli.md) | Alpha.20 `memoria` command surface | Guarded mirror |
| [Engine read API](commands-and-transports/read-api.md) | Host-neutral read/write API functions and project WRITE views | Manual |
| [Local HTTP transport](commands-and-transports/local-http-transport.md) | REST-like loopback adapter surface, auth, endpoints, scope, write payload, and limits | Manual |
| [MCP transport](commands-and-transports/mcp-transport.md) | Optional FastMCP stdio agent surface, required read scope, tool roster, and write provenance | Manual |
| [Prompt operations](commands-and-transports/prompt-operations.md) | Shipped prompt operations, manifest schema, and runner contract | Manual |

## Request, review, and policy contracts

| File | What it covers | Source |
| --- | --- | --- |
| [Control plane reference](control-and-policy/control-plane.md) | Request-control commands and state | Manual |
| [Empirical events](control-and-policy/empirical-events.md) | Alpha.20 empirical-use event schema, enums, required fields, and privacy boundary | Guarded mirror |
| [Evidence sets](control-and-policy/evidence-sets.md) | Draft evidence marker and derived-store contract | Manual |
| [Project structural impact](control-and-policy/project-structural-impact.md) | Project-gate structural-impact command, generated index payload, and write behavior | Manual |
| [Worklists](control-and-policy/worklists.md) | Batch worklist report JSON, emitted item notes, and aggregate review prompt contract | Manual |
| [Policy gate](control-and-policy/policy-mcp.md) | Runtime policy hook, optional adapter contract, auto-fix classes, audit pairing, and fail-closed behavior | Manual |
| [Policy audit log](control-and-policy/policy-audit-log.md) | Audit-log fields, JSON example, decision enum, and per-write hash pairing | Manual |

## Analysis, diagnostics, and surfaces

| File | What it covers | Source |
| --- | --- | --- |
| [Linter: detectors and auto-fix](analysis-and-surfaces/linter.md) | Linter structural detectors, auto-fix classes, and severity scale | Manual |
| [Vault eval](analysis-and-surfaces/vault-eval.md) | The vault-eval gold set, quarterly dispatch, idempotency keys, and diagnostic eval fixtures | Manual |
| [Retrieval and analysis methods](analysis-and-surfaces/retrieval-and-analysis-methods.md) | Deterministic methods: BM25 retrieval, API calls, and graph algorithms | Manual |
| [Calibration](analysis-and-surfaces/calibration.md) | Drift-bound threshold contracts and shadow-first score calibration | Source-owned |
| [Dashboards](analysis-and-surfaces/dashboards.md) | Space dashboards, Inbox, Maintenance, support dashboards, Bases views, verdict bands, and rail badges | Manual |

## Pipelines and I/O

| File | What it covers | Source |
| --- | --- | --- |
| [Ingest routing](pipelines-and-io/ingest.md) | Type detection dispatch, per-type enrichment, frontmatter written at ingest | Manual |
| [Sweeps](pipelines-and-io/sweeps.md) | Retraction maintenance passes | Manual |
| [Search](pipelines-and-io/search.md) | search retrieval surface: checked-only BM25 baseline, consumers, index, and limits | Manual |
| [Export routes and formats](pipelines-and-io/export.md) | Citation states, export routes, editor comparison, deliverable targets | Manual |
| [Memory substrates](pipelines-and-io/memory-substrates.md) | Memory substrate table, audit log schema, retention | Manual |
| [Telemetry & logs](pipelines-and-io/telemetry.md) | Operational log inventory, exact JSONL schemas, conventions, cadence, and join keys | Manual |
| [Diagnostics](pipelines-and-io/diagnostics.md) | Local diagnostics location, redaction, raw-capture, and support-bundle contract | Manual |

## System and infrastructure

| File | What it covers | Source |
| --- | --- | --- |
| [Memoria configuration](system/configuration.md) | Configuration surfaces, source/installed ownership, redeploy triggers, and secret boundaries | Manual |
| [On-disk layout](system/on-disk-layout.md) | Vault folder tree, `.memoria/` layout, skeleton notes, naming conventions | Manual |
| [System artifacts](system/system-artifacts.md) | Visible `system/` files, eval fixtures, and shipped Bases views | Manual |
| [Installer (bootstrap)](system/installer.md) | Bootstrap installer: platform matrix, install flow, component checklist, secrets and skills tables | Manual |
| [Failure modes](system/failure-modes.md) | Failure modes by severity: symptom, cause, fix | Manual |

## Evidence and integrations

| File | What it covers | Source |
| --- | --- | --- |
| [External integrations](evidence-and-integrations/integrations.md) | External APIs and tools: enrichment, entity resolution, vault access, execution layer | Manual |
| [Pattern provenance table](evidence-and-integrations/pattern-provenance.md) | Borrow/adapt/reference/ignore judgments for surveyed AI-research-system patterns | Manual |
| [Bibliography](evidence-and-integrations/bibliography.md) | Works cited across the docs in ACM author-date style | Manual |
| [Zotero plugins](evidence-and-integrations/zotero-plugins.md) | Zotero add-ons and the Zotero↔Obsidian connector comparison | Manual |
