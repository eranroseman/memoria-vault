---
title: System actions
parent: Agents and control
grand_parent: Reference
nav_order: 1
---

# System actions

Every action the system can perform, with its performer. Three performer kinds:
**operations** (CLI/engine work, deterministic or runner-backed), **optional
adapters** (external surfaces that call the same engine), and the **PI** (CLI
commands and review decisions). Where a topic has its own reference page, that
page is authoritative for the details — this catalog is the map.

This page is a guarded mirror, not the source of truth. Action implementation
lives in the referenced Python modules, capability manifests, and linked
reference pages; `docs_doctor.py` `check_reference_rosters` keeps the packaged
operation manifest roster linked.

## Operation manifest roster

Package-owned operation manifests currently ship these operation IDs:

- `acknowledge-attention`, `analyze-claims`, `analyze-gaps`, `analyze-project-argument`, `answer-query`, `capture-bibtex-source`, `capture-pdf-source`, `capture-source`
- `capture-url-source`, `cascade-rollback`, `check-falsifiability`, `check-source-metadata`, `compare-and-contrast`, `compile-source-digest`, `compose-project-draft`, `create-concept`
- `curate-note-candidate`, `curate-note-link`, `enrich-source`, `eval-run`, `export-project`, `extract-claim-stubs`, `frame-paper`, `integrity-citation-survival-check`
- `integrity-claim-quote-check`, `integrity-contradiction-check`, `integrity-evidence-check`, `integrity-link-target-check`, `integrity-prompt-injection-check`, `integrity-provenance-checkpoint`, `integrity-quote-anchor-check`, `mark-checked`
- `observe-pi-edits`, `promote-draft-passage`, `propose-note-candidates`, `rebuild-checked-search-index`, `record-copi-interview`, `red-team-argument`, `regenerate-capability-index`, `regenerate-indexes`
- `regenerate-references-bib`, `regenerate-tracked-projections`, `render-project-argument-canvas`, `resolve-attention`, `run-seeded-error-verdict`, `summarize-for-recall`, `surface-tensions`, `trace-integrity-scan`
- `update-work`, `verify-project-draft`, `write-project-slice`

## Deterministic operations

### Capture pipeline (`memoria_vault.runtime.capture`)

| Action | Performer | What it does |
| --- | --- | --- |
| Capture source | worker operation `capture-source` + runtime helpers (`capture_source`, `stage_catalog_source`) | Records a capture run. All routes write a SQLite catalog row plus durable content/raw blobs under `.memoria/blobs/source-content/`; DOI capture and portable imports stay unchecked until enrichment/checking, while already-supplied full text can become a checked catalog row after worker checks. Portable BibTeX/CSL imports can carry ISBN metadata but do not create a standalone ISBN enrichment route ([Ingest routing](ingest.md)). |
| Enrich staged source | worker operation `enrich-source` + runtime helper (`enrich_source`) | Fetches required DOI payloads from Crossref, OpenAlex, and Unpaywall, stores raw provider payloads under `.memoria/blobs/provider-payloads/`, records external IDs and field provenance in SQLite, blocks provider failures or retracted/contested records with `check-fired` plus an `inbox/` attention projection, then checks passing catalog rows and materializes `bibliography.bib`. |
| Capture BibTeX source | worker operation `capture-bibtex-source` + runtime helper (`bibtex_capture_payload`) | Parses one local BibTeX entry into a DOI/URL-derived `work_id` when available, citekey alias, CSL-JSON-shaped metadata, identifiers, durable raw `.bib` blob, an unchecked SQLite catalog row, and a queued DOI enrichment request when a DOI is present. It does not create source/entity markdown or update `bibliography.bib`. |
| Capture CSL source | `memoria work import --format csl` + runtime helper (`csl_capture_payload`) | Parses one local CSL-JSON item into a stable `work_id`, CSL-JSON-shaped metadata, identifiers, durable raw `.csl.json` blob, an unchecked SQLite catalog row, and a queued DOI enrichment request when a DOI is present. It uses the generic `capture-source` worker operation and does not create source/entity markdown or update `bibliography.bib`. |
| Update Work | worker operation `update-work` | Applies PI-owned Work metadata, standing, and classification changes to the SQLite catalog row, then records the journal event through the worker request queue. |
| Capture URL source | worker operation `capture-url-source` + runtime helper (`capture_url_source`) | Fetches one URL, preserves raw HTML, extracts plain text with stdlib `HTMLParser`, and writes an unchecked catalog row plus source-content blobs. |
| Capture PDF source | worker operation `capture-pdf-source` + runtime helper (`capture_pdf_source`) | Uses the optional PyMuPDF parser to extract page text from raw PDF bytes and writes an unchecked catalog row plus source-content blobs. |
| Regenerate bibliography | runtime capture helper (`write_references_bib`) / worker operation `regenerate-references-bib` | Rebuilds `bibliography.bib` from checked SQLite catalog rows and can commit the projection plus journal event through the worker. |
| Capture trace | trusted writer + journal | Records `run`, `derived`, and `check-fired` events for the catalog Work row; raw blobs stay gitignored and are referenced by path + hash. |
| Extract typed edge candidates | trusted writer materialization (`commit_writer_changes`) | Parses explicit argument-class body links such as `[[supports::notes/x.md]]` into unchecked `edge-candidate` attention prompts in the same commit; bare `[[wikilink]]` body links do not create `supports`, `contradicts`, or `extends` edges. |
| Create Concept | engine API (`write_new_concept`) + worker operation `create-concept` | Queues PI or CLI-agent `note`/`hub`/`project` creation through the request envelope, validates and commits the Concept through the trusted writer, and leaves it `unchecked` until a later `check` operation passes. |
| Foreign-write quarantine | worker operation `trace-integrity-scan` + trusted writer (`quarantine_untraced_from_status` / `quarantine_untraced`) | Scans git-status or explicit bundle paths, moves untraced bundle files into `.memoria/quarantine/`, and records a failed `trace-integrity` check event. |

### Operation runner (`memoria_vault.runtime.operations`)

| Action | Performer | What it does |
| --- | --- | --- |
| Load operation policy | runtime operation helper (`load_operation_policy`) | Loads a package-owned operation manifest and requires the WP5 policy contract: tools, paths, network, `runner.test` plus `runner.live` provider/model branches, prompt version, `io_schema.input`/`io_schema.output`, risk class, checks, and sealed `untrusted_fields` where raw text enters model prompts. |
| Select model pins | `memoria eval select-models` | Runs the seeded-error bar for manifest-declared `runner.test`/`runner.live` pins in a disposable fixture, emits a selection record, and refuses to select a runner whose bar fails. |
| Record Co-PI interview | worker operation `record-copi-interview` + runtime helper (`record_copi_interview_turn`) | Records a PI interview takeaway for a checked Work as a committed `copi-interview` journal event; digest compile can consume it as traced context. |
| Compile source digest | worker operation `compile-source-digest` + runtime helper (`compile_source_digest`) | Reads one checked Work, resolves `--mode test\|live` to a manifest-pinned runner branch, uses deterministic fixture output or an allowed OpenAI-compatible pydantic-ai runner for digest markdown that passes the required section contract and a lexical source-grounding smoke check, records resolved mode/provider/model/params plus prompt hash in `model_call`, embeds compact citation survival payloads, promotes a machine-owned checked digest Work plus brand-new hubs, and stages curated hub suggestions without overwriting curated hubs. |
| Regenerate tracked projections | runtime projection helper (`write_tracked_projections`) / worker operation `regenerate-tracked-projections` | Rebuilds `index.md` and `bibliography.bib` in one worker-owned projection run. |
| Regenerate workspace indexes | runtime projection helper (`write_workspace_indexes`) / worker operation `regenerate-indexes` | Rebuilds the root and bundle `index.md` projections from checked Concept files. |
| Regenerate capability index | runtime capability helper (`write_capability_index`) / worker operation `regenerate-capability-index` | Rebuilds ignored `.memoria/index/capability-index.json` from packaged capability manifests and records product SHA-256 trust hashes. |

### Search input and query (`memoria_vault.runtime.search_index`)

| Action | Performer | What it does |
| --- | --- | --- |
| Rebuild checked search source | worker operation `rebuild-checked-search-index` + runtime helper (`rebuild_checked_search_index`) | Rebuilds `.memoria/index/search/checked/` from checked retrieval documents: current Concepts plus generated checked Work text and graph neighborhoods. |
| Answer query | worker operation `answer-query` + runtime helper (`answer_query`) | Returns the deterministic BM25 Ask/Query contract over checked retrieval documents: sources, unknowns, staleness, contradictions, and project context when supplied. |

### Knowledge construction (`memoria_vault.runtime.knowledge`)

| Action | Performer | What it does |
| --- | --- | --- |
| Emit note candidates | worker operation `propose-note-candidates` + runtime helper (`emit_note_candidates`) | Reads one checked digest, records resolved runner provenance in `model_call`, promotes checked `note` Concepts, and records note-candidate state in `.memoria/journal/` and SQLite state rather than frontmatter. |
| Curate note candidate | worker operation `curate-note-candidate` + runtime helper (`curate_note_candidate`) | Records a PI accept/reject decision for one checked candidate `note` as a journal `resolved` row without mutating Concept frontmatter. |
| Curate note link | worker operation `curate-note-link` + runtime helper (`curate_note_link`) | Records one PI-authored `supports`, `contradicts`, or `extends` link from a checked note to a checked Concept, updating the note's `links` map and committing it with a journal `resolved` row. |
| Analyze gaps | worker operation `analyze-gaps` + runtime helper (`analyze_gaps`) | Counts checked Work, checked digest Work, and accepted-note topic signals and reports `new-topic`, `undigested`, and `under-warranted` gaps with proposed seed actions; when a project path is supplied, it also seeds project scope/facet terms, counts checked linked thesis terms, and includes checked project argument-health gaps. Provider-discovered Work candidates surface as unchecked attention with deterministic steering relevance metadata plus a separate exploration channel; repeated off-vocabulary phrases in checked Work text surface as unchecked tag-candidate attention. The operation never captures candidate Works or writes tags directly. |
| Analyze project argument | worker operation `analyze-project-argument` + runtime helper (`analyze_project_argument`) | Follows checked, non-candidate note links around a checked project's `thesis` note and returns relation counts, stage, saturation, gap/advisory taxonomy, nodes, and edges. |
| Render project argument Canvas | worker operation `render-project-argument-canvas` + runtime helper (`write_project_argument_canvas`) | Renders the checked-note argument graph for one project as a generated `projects/<project>/argument.canvas` projection and commits it with a journal row. |
| Run prompt operation | worker operation `<pattern-id>` + runtime helper (`run_prompt_operation`) | Reads checked input refs for package-owned prompt-operation manifests such as `analyze-claims`, records request/journal provenance, and stages one unchecked report note under `.memoria/staging/notes/`. |

### Integrity loop (`memoria_vault.runtime.integrity`)

| Action | Performer | What it does |
| --- | --- | --- |
| Check evidence integrity | runtime integrity helper (`check_evidence_integrity`) | Scans checked `digest` and `note` Concepts and flags unresolved `work_id`, legacy evidence-set, or body evidence-marker references. |
| Check source metadata | runtime integrity helper (`check_source_metadata`) | Flags checked catalog Work rows that lack citekey, CSL-JSON basics, issued year, an external resource/identifier, carry conflicting DOI metadata, share an exact source external ID with another catalog row, hit the deterministic title/year/first-author duplicate block, or expose duplicate person ORCID/OpenAlex IDs or entity-name blocks; active record-linkage findings also emit stable `inbox/` work prompts for PI review without merging records. |
| Check quote anchors | runtime integrity helper (`check_quote_anchor_support`) | Flags checked notes whose quoted span is absent from checked Work text declared by `work_id` or evidence markers. |
| Record integrity check | runtime integrity helper (`record_integrity_check`) | Appends a `check-fired` event with shadow-first `drop` routing by default; active failures route `ask`, and explicit auto-revert checks route `act`. |
| Check claim quote support | runtime integrity helper (`check_claim_quote_support`) | Flags checked notes whose claim and cited quote share no substantive terms; this is a high-precision first pass for unwarranted-claim seeded errors, not a full NLI replacement. |
| Check prompt-injection markers | runtime integrity helper (`check_prompt_injection_markers`) | Flags checked Works, digest Work, or notes containing explicit prompt-injection marker text; this is a high-precision marker check, not semantic injection detection. |
| Check provenance checkpoint | runtime integrity helper (`check_provenance_checkpoint`) | Flags checked notes or digest Work that depend on checked catalog Works whose provider coverage is still partial or degraded; this routes fresh uncorroborated source use to PI attention without claiming semantic detection. |
| Check citation survival | runtime integrity helper (`check_citation_survival`) | Flags checked notes, digests, or hubs that reference catalog Works without compact citation payloads sufficient to read the keep-set without SQLite. |
| Surface tensions | worker operation `surface-tensions` + runtime helper (`surface_tensions`) | Runs the Tier-1 HANS-gated contradiction pass and the Tier-2 judge for Tier-1 abstain/degraded hard cases; Tier-2 must quote both checked texts or abstain, and no `contradicts` link is written. |
| Check contradiction links | runtime integrity helper (`check_contradiction_links`) | Flags checked digests whose explicit `contradictions` targets are missing, unchecked, or stale; this is structural link integrity, not semantic contradiction discovery. |
| Check link targets | runtime integrity helper (`check_link_targets`) | Flags checked Concepts whose explicit path-like `links` targets are missing, unchecked, or stale; this is structural link-target integrity, not semantic false-link detection. |
| Trace downstream | runtime integrity helper (`trace_downstream`) | Rebuilds the downstream graph from journal `derived.inputs` without reading unchecked Concepts. |
| Cascade rollback | runtime integrity helper (`cascade_rollback`) | Moves machine-derived downstream Concepts to `.memoria/quarantine/`, appends `resolved` plus inverse `derived` events, and leaves PI-derived downstream Concepts live while flagging them with route `ask`. |
| Run seeded-error verdict | worker operation `run-seeded-error-verdict` + runtime helper (`run_seeded_error_verdict`) | Builds the seeded structural fixture from `.memoria/eval/alpha15-seeded-errors.json` in a disposable temp workspace, measures recall, false positives, check timing, detection timing, rollback completeness, residual error, no-checks residual baseline, residual reduction, and ask-routed checkpoint value, then returns a pass/fail verdict, a contained probe review batch, and live-only non-sandbox license flag for that bundle. |

### Linter (`memoria_vault.runtime.subsystems.integrity.linter`)

The registered detectors (slugs, severities, and what each catches) live in [Linter: detectors and auto-fix](linter.md#the-detectors); every detector is report-only.

| Action | Performer | What it does |
| --- | --- | --- |
| Run detectors | Linter (`detectors.py`, manual or scheduled run) | Runs all registered structural detectors over the vault; findings surface on the drift dashboards. |
| Pre-commit hook | Linter (`precommit_check.py`, git hook) | Schema-validates staged notes and blocks the commit on a violation — the one check that prevents rather than reports. |
| Session digests | Linter (`session_summary.py`, manual or scheduled run) | Writes one deterministic per-session digest file under `system/logs/sessions/` from the audit log ([the quarantine-and-verify with durable, audit-logged crash recovery decision](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)). |
| Hub proposal handoff | Linter (`hub_handoff.py`, PI-run) | Converts current `hub-threshold` findings into idempotent local handoff payloads for map work; `hubs/` stays PI-curated. |

### Sweeps (`memoria_vault.runtime.subsystems`)

| Action | Performer | What it does |
| --- | --- | --- |
| Eval dispatch | telemetry operation (`eval_dispatch.py`, scheduled task or `memoria eval run`) | Fans the gold set out as one idempotent local eval task per current task ([Vault eval](vault-eval.md)). |
| Eval score | telemetry operation (`eval_score.py`, scheduled task) | Computes recall@k / support-rate / FAMA-clean from local result blocks; appends to `system/metrics/eval/runs.jsonl`. |
| Retraction check | retraction operation (`retraction.py`) | Checks a DOI against the Retraction Watch dataset, Crossref, and Open Retractions (read-only). |
| Retraction sweep | retraction operation (`retraction.py`) | Scans the catalog's DOIs for retractions and hands findings to the agent to flag. |
| Emit worklist | shared operation helper (`worklists.py`) | Converts a scan/search report into file-backed worklist projections and one aggregate `work-prompt` attention projection. |

## Runtime policy and helper modules

| Action | Performer | What it does |
| --- | --- | --- |
| Policy decision | [Policy gate](policy-mcp.md) (`memoria_vault.runtime.policy`) | Decides allow / allow_with_log / deny / dry_run for optional adapter writes and runtime checks; fail-closed. |
| Pre-tool gate | runtime policy hook (`memoria_vault.runtime.policy.hook`) | Optional adapters call it before a tool runs; denied, dry-run, direct-file, terminal, browser, and unaudited egress tools are blocked. |
| Post-tool pairing | runtime policy hook (`memoria_vault.runtime.policy.hook`) | Computes the `after_hash` and appends the paired reversibility record to `system/logs/audit.jsonl`. |
| Build graph neighborhoods | runtime search/knowledge helpers | Builds checked retrieval documents and first-order graph-neighborhood text for BM25 ask and gap analysis. |
| Render argument canvas | worker operation `render-project-argument-canvas` | Renders the project argument map as a JSON Canvas artifact from checked project graph state. |
| Run prompt operations | `memoria operation run` / `engine_api.run_operation` | Runs package-owned prompt operations through the same request, runner, staging, and journal boundary as other worker operations. |
| Loudness routing | shared operation helper (`memoria_vault.runtime.subsystems.lib.loudness`) | Sends/logs alert/block push attempts, keeps quiet/notice pull-only, and exposes open block attention items to delegation and policy gates. |

## CLI requests

| Action | Performer | What it does |
| --- | --- | --- |
| Run integrity check | `memoria operation run <operation-id>` | Inserts one SQLite request and runs worker-owned integrity operations such as `integrity-evidence-check`, `integrity-quote-anchor-check`, `integrity-claim-quote-check`, `integrity-link-target-check`, and `check-source-metadata`; the worker owns journal rows and routing. |
| Capture or enrich source | `memoria work add`, `memoria work import`, `memoria work enrich` | Creates the request envelope in `.memoria/memoria.sqlite`, runs capture/enrichment, writes provider/raw payloads, and materializes catalog outputs through the worker boundary. |
| Compile digest or record interview | `memoria work digest`, `memoria work interview` | Queues and runs source synthesis jobs, recording Co-PI interview takeaways and digest materialization through the same request/journal path. |
| Ask query | `memoria ask --question ...` / `memoria project ask <project-id> --question ...` | Runs `answer-query` and returns the Ask/Query response contract over checked retrieval documents; project Ask includes checked project context when available. |
| Author and curate Concepts | `memoria new note`, `memoria check`, `memoria link` | Authors PI or CLI-agent Concepts through the engine request envelope, promotes checked Concepts through the request boundary, and records typed-link curation through worker-owned requests and journal rows. |
| Analyze and write project | `memoria project gaps <project-path>`, `trace`, `frame-paper`, `slice`, `compose`, `verify`, `promote`, `explore`, `export` | Runs checked graph, project-scope, linked-thesis, project-argument, paper-readiness, and exploration analysis; records PI-supplied paper framing; proposes `outline.md` with BM25; composes and verifies `draft.md`; promotes selected draft passages into unchecked notes; records code-artifact/code-run provenance for computed warrants; and performs deterministic Markdown/Pandoc project or draft export from the CLI control plane. New Project Concepts are authored through `memoria new project`, queued as `create-concept`, and remain unchecked until review/check promotion. |
| Refresh projections and search | `memoria workspace rebuild` | Regenerates tracked projections, bibliography, workspace indexes, and checked-only search inputs from worker-readable state. |
| Trace rollback | `memoria workspace rollback` | Runs `cascade-rollback` against a target id; the worker owns quarantine, commit, and journal rows. |
| Observe PI edits | `memoria workspace scan` / `memoria serve --watch` | Runs `observe-pi-edits`, scanning bundle-root git status and committing direct PI Concept edits with backfilled `derived` events. `serve --watch` is only a stdlib polling trigger; the scan worker remains the correctness boundary. |
| Resolve attention | `memoria attention resolve (--apply\|--reject\|--defer)` | Runs the attention-disposition request, records routing class plus PI resolution outcome, and closes or defers the attention projection in the committed journal row. |
| Inspect requests | `memoria status`, `memoria request list`, `memoria doctor bundle` | Reads SQLite request state and diagnostic bundles; no file queue mirror exists. |
| Serve local HTTP | `memoria serve --http` | Starts the [local HTTP transport](local-http-transport.md) with bearer-token auth; handlers only marshal selected `engine/api` reads and request-envelope writes. Remote/OAuth transport is not implemented. |
| Serve MCP stdio | `memoria mcp --workspace <path> --read-scope <path>` | Starts the optional [MCP transport](mcp-transport.md). It requires a non-root read scope, exposes only engine read tools plus request-envelope writes, and records MCP provenance. |

## Optional external adapters

| Action | Performer | What it does |
| --- | --- | --- |
| Vault read / gated write | optional editor or BYO-agent adapter | Reads may inspect workspace files; writes must call the runtime policy hook and then enter the same checked request/journal boundary as CLI work. |
| Vault search | `memoria ask` / search debug commands | Uses the checked-only search tree and runtime read barrier; no required external operation API ships. |
| Literature discovery | provider-backed runtime operations | Uses configured provider allowlists and replay fixtures for tests; no live Zotero or required external agent server is authoritative. |
| Portable bibliography import | `memoria work import --format bibtex` or `--format csl` | Reads local BibTeX or CSL JSON files as input data only; no live reference-manager DB/API is a baseline dependency. |

## Scheduled tasks (`.memoria/scripts/`)

The deterministic scheduled jobs are optional operator wiring around the CLI and
runtime package. `.memoria/scripts/cron-runner.sh` dispatches `worker`, `lint`,
`eval`, and `retraction-refresh`. No scheduler is required for a one-shot
CLI workflow; a systemd timer, cron entry, launchd job, or another local
scheduler can call the runner when always-on maintenance is desired.

## Skills and prompts

The standalone runtime does not ship installed profile skill bundles or per-lane task routing.
Reusable prompt behavior lives as package-owned operation manifests and runs
through `memoria operation run`.

## PI actions

### Review decisions

| Action | What it does |
| --- | --- |
| Worker promotion | Machine writes promote from `.memoria/staging/` only after worker checks set DB/read API `check_status = checked`; operation-owned promotions enforce their `required_checks` (`memoria-runtime`) before the state transition and record durable materialization payloads in SQLite. PI edits are direct, then the worker observes git-status changes and backfills `{Concept + journal}`. |
| Inbox triage | Resolve or act on attention projections; dispositions are logged for trust and attention metrics. |
| Workspace recover | `memoria workspace recover` marks interrupted running requests failed for explicit retry and replays pending materialization payloads; `--fixture crash-before-materialization` is a test-only recovery harness. |
