---
topic: decisions
id: 32
title: Profile capabilities and external access reach the agent only over MCP; deterministic tools are self-hosted
status: accepted
date_proposed: 2026-06-04
date_resolved: 2026-06-04
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 32
---

# ADR-32: External access over MCP

## Context

> *Note (v0.1.0-alpha.2): the profile names below predate [ADR-48](48-copi-and-agent-consolidation.md), which consolidated the seven specialists to five — Mapper → Librarian (`map` lane), Socratic → co-PI, Verifier → Peer-reviewer, Coder → Engineer, Linter → an engine. The MCP-only decision (no direct `web`/`terminal`; deterministic tools self-hosted) is unchanged and applies to the current fleet. The self-hosted retraction MCP described below (`verify_mcp.py` / `retraction_check(doi)`) was never shipped: [ADR-46](46-seven-layer-architecture.md)/D41 delivers retraction as the cron-only sweep engine `engines/sweeps/retraction.py` instead — same three-source design and data provenance, no MCP facade.*

A fleet-wide audit of the seven profiles found the capability surface inconsistent. Some profiles ran deterministic engines as loose scripts via the `terminal` toolset (the Linter's `detectors.py`); some made scholarly-API calls directly via the `web` toolset (the Librarian's `paper-lookup`/`enrich`, the Verifier's retraction lookups); capabilities were a mix of authored skills, K-Dense web-fetch skills, and raw HTTP. This matters because the policy gate ([ADR-28](28-write-gate-as-plugin.md)) and Hermes' determinism guarantees only apply to **MCP tools** (`mcp_<server>_<tool>`): a call made through `web` or `terminal` is neither gated nor audited, and when the *model* constructs an HTTP call or runs a check each turn, the result is no longer deterministic or reproducible in CI. The audit also surfaced a stale claim — that the Librarian wrote back to Zotero — when Memoria uses Zotero's read-only local API, so the "direct API access is required" assumption was partly false.

## Decision

Profile capabilities — both deterministic engines and external service access — reach the agent **only over MCP servers**, registered in each profile's `config.yaml` `mcp_servers` and gated by the policy plugin. The agent's `code_execution` and `web` toolsets are **disabled on every profile**; `terminal` is disabled except for two deliberate exceptions: the **Coder** (delegates to external coding agents that execute code outside the gated runtime) and the **Linter** (runs its own zero-LLM `detectors.py`). Where no suitable off-the-shelf MCP exists, Memoria **self-hosts a thin, pure-stdlib MCP over authoritative open data** rather than granting a raw toolset or vendoring an unproven dependency.

## Consequences

- **Every profile's external access is gated, audited, and deterministic.** Discovery is the `paper_search` MCP (openags/paper-search-mcp); Zotero reads are the read-only `pyzotero` MCP; citation context is the pyzotero MCP's Semantic Scholar tools; vault access is the `obsidian` MCP; the deterministic ingest pipeline is the `ingest` MCP ([ADR-30](30-deterministic-ingest-pipeline.md)); the Linter's detectors are the `structural-detectors` skill's bundled engine.
- **Retraction is self-hosted on authoritative open data.** No mature retraction MCP exists, so `verify_mcp.py` exposes `retraction_check(doi)` over three sources, most-authoritative first: the Retraction Watch dataset (Crossref-owned, CC, refreshed from `gitlab.com/crossref/retraction-watch-data`), CrossRef `update-to`/`is-retracted-by` (real-time delta), and Open Retractions (fallback). Read-only, deterministic, offline-capable, with an offline self-test.
- **Least privilege.** Five of seven profiles (Librarian, Verifier, Mapper, Socratic, Writer) make **no direct API calls and run no code** — their only outward path is gated MCP. The remaining direct-execution surface is the Coder's and Linter's `terminal`, both by design; the Coder's hand-off to external coding agents is the largest trust surface in the fleet and is acknowledged as such.
- **Cost.** More MCP servers to install and keep running. Two require a one-time host install (`pip install paper-search-mcp`, `pip install "pyzotero[mcp]"`); the self-hosted servers (`policy`, `ingest`, `verify`) run from the vault venv. The Retraction Watch CSV needs a periodic cron refresh (`verify_mcp.py --refresh`).
- **Residual.** Loopback HTTP for the obsidian MCP remains unencrypted ([ADR-31](31-native-obsidian-mcp.md)); the Coder's external-agent execution is outside the gate by construction.

## Alternatives considered

- **Keep `web`/`terminal` enabled with `external_api_policy` as the guardrail.** Rejected: those calls bypass the policy gate's audit trail, let the model improvise non-deterministic HTTP/logic, and grant a far larger blast radius than a typed MCP tool — the opposite of the determinism the Linter and ingest pipeline are built on.
- **Vendor `retraction-watch-mcp` (the only purpose-built retraction MCP).** Rejected as the primary: it is a 0-star, single-author repo with a package/name mismatch, and bundles a ~360 MB SQLite snapshot. We instead pull the **same authoritative dataset** straight from Crossref's official distribution into a thin server we control; the vendored RW server remains an upgrade path if its provenance hardens.
- **Adopt a paper-search MCP that downloads full text (openags' `download_*` tools include a Sci-Hub fallback).** Rejected for those tools: the Librarian uses only the `search_*` tools; PDF retrieval and extraction stay with the ingest pipeline (Marker), so the Sci-Hub path is never invoked.

## Related

- **Related decisions / Depends on:** [ADR-27](27-hermes-native-config-and-gate-enforcement.md) (native config + gate enforcement), [ADR-28](28-write-gate-as-plugin.md) (the policy gate this rule rides on), [ADR-30](30-deterministic-ingest-pipeline.md) (the pipeline-as-MCP precedent), [ADR-31](31-native-obsidian-mcp.md) (the obsidian MCP).
- **Files affected:** `vault/.memoria/engines/sweeps/retraction.py` (was planned as `mcp/verify_mcp.py` — see the alpha.2 note above), `vault/.memoria/scripts/refresh-retraction-watch.sh`, every `vault/.memoria/profiles/memoria-*/config.yaml` and `vault/.memoria/lane-overrides/*.yaml`, the Linter's `structural-detectors` skill, the Verifier's `retraction-check` + `claim-checks` skills.
