---
title: Operations
parent: Agents and control
grand_parent: Reference
---

# Operations

Deterministic mechanisms that agents, scheduled tasks, CI, and the PI can invoke.
Canonical bundle writes route through the worker/trusted-writer path; MCP facades
may request work, but they do not commit Concepts, projections, or journal events
directly.

Shared dependency-light helpers for operation code live under `memoria_vault.runtime`
(`vaultio`, `jsonl`, `time`, and `paths`). MCP modules import those helpers
directly; package code owns the behavior.

| Operation | Primary entry point | MCP facade | Direct callers | What it does |
| --- | --- | --- | --- | --- |
| Capture | `memoria_vault.runtime.capture` | SQLite worker request for `capture-source`, `capture-bibtex-source`, `capture-zotero-source`, `capture-url-source`, `capture-pdf-source`, and `regenerate-references-bib` | worker, tests, debug sessions | Records capture runs, writes immutable raw/content files, imports one local BibTeX entry, Zotero item snapshot, Zotero item key from the local desktop API, URL snapshot, or extracted PDF text through the optional PyMuPDF parser path. DOI/ISBN inputs and portable BibTeX imports are staged unchecked in SQLite plus `.memoria/blobs/source-content/`; DOI BibTeX imports queue `enrich-source`. Non-enrichment captures still create checked `source` and deterministic metadata-derived entity Concepts, update SQLite catalog state, and materialize `references.bib` with bibliography-changing captures. |
| Source enrichment | `memoria_vault.runtime.enrichment` | SQLite worker request for `enrich-source` | worker, tests, debug sessions | Loads `.memoria/config/providers.yaml`, fetches required DOI provider payloads from Crossref, OpenAlex, and Unpaywall through allowed network policy, caches raw payloads under `.memoria/blobs/provider-payloads/`, records field provenance and external IDs in SQLite, writes `inbox/` attention projections for provider failures or contested/retracted records, then marks passing staged sources checked and materializes `references.bib`. |
| Trusted writer | `memoria_vault.runtime.trusted_writer` | SQLite worker request | worker, tests, debug sessions | Stages Concepts unchecked, stores durable materialization payloads in SQLite, enforces supported promotion checks before marking Concepts checked, observes PI edits from git status, quarantines untraced bundle changes from git status or explicit paths, rebuilds trace state, and commits only selected writer paths plus the journal. |
| Worker requests | `memoria_vault.runtime.worker` | CLI / scheduled tasks | scheduled tasks, CLI, tests, debug sessions | Persists the request envelope and job state only in `.memoria/memoria.sqlite`, and executes trusted-write jobs plus operation jobs such as `integrity-evidence-check`, `integrity-quote-anchor-check`, `integrity-claim-quote-check`, `integrity-prompt-injection-check`, `integrity-provenance-checkpoint`, `integrity-citation-survival-check`, `integrity-contradiction-check`, `integrity-link-target-check`, `trace-integrity-scan`, `capture-source`, `enrich-source`, `capture-bibtex-source`, `capture-zotero-source`, `capture-url-source`, `capture-pdf-source`, `record-copi-interview`, `compile-source-digest`, `propose-note-candidates`, `curate-note-candidate`, `curate-note-link`, `analyze-gaps`, `analyze-project-argument`, `export-project`, `render-project-argument-canvas`, `rebuild-checked-qmd-source`, `answer-query`, `check-source-metadata`, `cascade-rollback`, `run-seeded-error-verdict`, `observe-pi-edits`, `regenerate-tracked-projections`, `regenerate-references-bib`, `regenerate-capability-index`, `regenerate-indexes`, `acknowledge-attention`, and `resolve-attention`; `memoria operation run <operation-id> --payload-json '{...}'` queues manual/live smoke jobs, and the scheduled `integrity-sweep` queues the nine integrity checks once per UTC day. |
| Search input and read barrier | `memoria_vault.runtime.search_index`; `vault-template/.memoria/mcp/qmd_filter_mcp.py` | SQLite worker request + qmd MCP wrapper | agents, PI, tests, debug sessions | Rebuilds qmd's checked-current input tree, filters qmd results to current checked Concepts, provides the BM25 eval baseline, and returns the deterministic Ask/Query answer contract. |
| Tracked projections | `memoria_vault.runtime.projections` | SQLite worker request | worker, tests, debug sessions | Regenerates root and bundle `index.md`, `references.bib`, and `capabilities/_generated/capability-index.json`; the drift check regenerates the tracked set into a temp tree and diffs it against the workspace copies. |
| Capability index | `memoria_vault.runtime.capabilities` | SQLite worker request | worker, tests, debug sessions | Renders `capabilities/_generated/capability-index.json` on demand from capability Concepts with local SHA-256 trust hashes, and quarantines unsigned imported capability files outside the live capability bundle. |
| Operation runner | `memoria_vault.runtime.operations` | SQLite worker request | worker, tests, debug sessions | Loads checked operation policy Concepts, records PI Co-PI interview turns in the journal, calls deterministic fixture or allowed OpenAI-compatible pydantic-ai models for digest markdown, enforces the digest section contract and lexical source-grounding smoke check before writing, records `model_call` events, compiles checked sources plus interview takeaways into machine-owned digests and brand-new hubs, and stages curated hub suggestions without overwriting curated hubs. |
| Knowledge construction | `memoria_vault.runtime.knowledge` | SQLite worker request | worker, tests, debug sessions | Emits checked `note` candidates from checked digests, records PI accept/reject and typed-link curation for notes, classifies checked-current source/digest/accepted-note topic gaps (`new-topic`, `undigested`, `under-warranted`), computes the checked-note argument lens for one project thesis, exports checked projects to Markdown/Pandoc formats, and can render that graph as a generated `argument.canvas` projection. |
| Integrity routing and rollback | `memoria_vault.runtime.integrity` | SQLite worker request, later | worker, tests, debug sessions | Checks source metadata, evidence/source resolution, citation-survival payloads, quote anchoring, claim/quote overlap, explicit prompt-injection markers, provenance checkpoints for synthesis over uncorroborated sources, explicit contradiction-link targets, and structural link targets; records shadow-first check verdicts; traces downstream `derived` events; quarantines machine-derived descendants during cascade rollback; and flags PI-derived descendants for human review. |
| Seeded-error verdict | `memoria_vault.runtime.seeded_errors` | SQLite worker request | tests, release gate, debug sessions | Builds the seeded structural/blind-class fixture in a disposable temp workspace, preferring `system/eval/alpha12-seeded-errors.json` and falling back to the alpha.11 bundle, runs integrity checks, rolls back detected machine-owned targets, and reports recall, false positives, check timing, detection timing, rollback completeness, residual error rate, no-checks baseline, residual reduction, and ask-routed checkpoint value. |
| Prompt patterns | `vault-template/.memoria/mcp/patterns_mcp.py` | patterns MCP | agents, PI, tests, debug sessions | Lists checked prompt operations from `capabilities/operations/`, composes prompts, refuses gated output targets, and logs provenance. |
| Integrity retraction | `vault-template/.memoria/operations/integrity/retraction/retraction.py` | None | Cron, CI, PI | Runs retraction lookups, surfacing findings as Inbox cards. |
| Eval telemetry | `vault-template/.memoria/operations/telemetry/eval/*.py` | None | Cron, CI, PI | Dispatches and scores vault-eval runs. |
| Linter | `vault-template/.memoria/operations/integrity/linter/detectors.py`; `hub_handoff.py` | None | Cron, CI, pre-commit, PI | Validates schemas, links, graph health, audit-chain integrity, golden-copy drift, session digests, and opt-in hub-threshold handoffs. |
| Batch worklists | `vault-template/.memoria/operations/lib/worklists.py` | None | Reports, tests, PI | Emits ADR-54 `worklist-item` rows from a report and raises one aggregate Inbox `work-prompt` for the batch. |

## Related

- Why operations are separate from agents: [Operations — the deterministic layer](../explanation/operations.md)
- Ingest command details: [Ingest routing](ingest.md)
- Runtime state boundary: [ADR-122](../adr/122-sqlite-working-state-boundary.md)
- DOI enrichment gate: [ADR-123](../adr/123-doi-catalog-enrichment-gate.md)
- Project-gate cache details: [Project structural impact](project-structural-impact.md)
- Sweep command details: [Sweeps](sweeps.md)
- Batch worklist command details: [Worklists](worklists.md)
- Linter command details: [Linter: detectors and auto-fix](linter.md)
