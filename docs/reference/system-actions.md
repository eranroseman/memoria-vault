---
title: System actions
parent: Agents and control
grand_parent: Reference
---

# System actions

Every action the system can perform, with its performer. Three performer kinds:
**operations** (CLI/engine work, deterministic or runner-backed), **optional
adapters** (external surfaces that call the same engine), and the **PI** (CLI
commands and review decisions). Where a topic has its own reference page, that
page is authoritative for the details — this catalog is the map.

This page is a guarded mirror, not the source of truth. Action implementation
lives in the referenced Python modules, capability manifests, and linked
reference pages; docs checks keep the mirror linked.

## Deterministic operations

### Capture pipeline (`memoria_vault.runtime.capture`)

| Action | Performer | What it does |
| --- | --- | --- |
| Capture source | worker operation `capture-source` + runtime helpers (`capture_source`, `stage_catalog_source`) | Records a capture run. DOI/ISBN inputs stage an unchecked SQLite catalog row plus durable content/raw blobs under `.memoria/blobs/source-content/` for `enrich-source`; non-enrichment captures write `catalog/sources/<source_id>/{source.md,content.md,raw/}`, promote the `source` and metadata-derived entity Concepts through the trusted writer, update checked SQLite catalog state, and commit Concepts/content/journal plus required `references.bib` together ([Ingest routing](ingest.md)). |
| Enrich staged source | worker operation `enrich-source` + runtime helper (`enrich_source`) | Fetches required DOI payloads from Crossref, OpenAlex, and Unpaywall, stores raw provider payloads under `.memoria/blobs/provider-payloads/`, records external IDs and field provenance in SQLite, blocks provider failures or retracted/contested records with `check-fired` plus an `inbox/` attention projection, then checks passing catalog rows and materializes `references.bib`. |
| Capture BibTeX source | worker operation `capture-bibtex-source` + runtime helper (`bibtex_capture_payload`) | Parses one local BibTeX entry into a DOI/URL-derived `source_id` when available, citekey alias, CSL-JSON-shaped metadata, identifiers, durable raw `.bib` blob, an unchecked SQLite catalog row, and a queued DOI enrichment request when a DOI is present. It does not create source/entity markdown or update `references.bib`. |
| Capture CSL source | `memoria work import --format csl` + runtime helper (`csl_capture_payload`) | Parses one local CSL-JSON item into a stable `source_id`, CSL-JSON-shaped metadata, identifiers, durable raw `.csl.json` blob, an unchecked SQLite catalog row, and a queued DOI enrichment request when a DOI is present. It uses the generic `capture-source` worker operation and does not create source/entity markdown or update `references.bib`. |
| Update Work | worker operation `update-work` | Applies PI-owned Work metadata, standing, and classification changes to the SQLite catalog row, then records the journal event through the worker request queue. |
| Capture URL source | worker operation `capture-url-source` + runtime helper (`capture_url_source`) | Fetches one URL, preserves raw HTML, extracts plain text with stdlib `HTMLParser`, and writes the same checked source Concept path. |
| Capture PDF source | worker operation `capture-pdf-source` + runtime helper (`capture_pdf_source`) | Uses the optional PyMuPDF parser to extract page text from raw PDF bytes and writes the same checked source Concept path. |
| Regenerate bibliography | runtime capture helper (`write_references_bib`) / worker operation `regenerate-references-bib` | Rebuilds `references.bib` from checked SQLite catalog rows, falling back to checked source Concepts only when no catalog rows exist, and can commit the projection plus journal event through the worker. |
| Capture trace | trusted writer + journal | Records `run`, `derived`, and `check-fired` events for the source Concept; raw blobs stay gitignored and are referenced by path + hash. |
| Extract typed edge candidates | trusted writer materialization (`commit_writer_changes`) | Parses explicit argument-class body links such as `[[supports::knowledge/notes/x.md]]` into unchecked `edge-candidate` attention prompts in the same commit; bare `[[wikilink]]` body links do not create `supports`, `contradicts`, or `extends` edges. |
| Create Concept | engine API (`write_new_concept`) + worker operation `create-concept` | Queues PI or CLI-agent `note`/`hub`/`project` creation through the request envelope, validates and commits the Concept through the trusted writer, and leaves it `unchecked` until a later `check` operation passes. |
| Foreign-write quarantine | worker operation `trace-integrity-scan` + trusted writer (`quarantine_untraced_from_status` / `quarantine_untraced`) | Scans git-status or explicit bundle paths, moves untraced bundle files into `.memoria/quarantine/`, and records a failed `trace-integrity` check event. |

### Operation runner (`memoria_vault.runtime.operations`)

| Action | Performer | What it does |
| --- | --- | --- |
| Load operation policy | runtime operation helper (`load_operation_policy`) | Loads a checked packaged operation manifest and requires the WP5 policy contract: tools, paths, network, `runner.test` plus `runner.live` provider/model branches, prompt version, `io_schema.input`/`io_schema.output`, risk class, and checks. |
| Record Co-PI interview | worker operation `record-copi-interview` + runtime helper (`record_copi_interview_turn`) | Records a PI interview takeaway for a checked source as a committed `copi-interview` journal event; digest compile can consume it as traced context. |
| Compile source digest | worker operation `compile-source-digest` + runtime helper (`compile_source_digest`) | Reads one checked source, resolves `--mode test\|live` to a manifest-pinned runner branch, uses deterministic fixture output or an allowed OpenAI-compatible pydantic-ai runner for digest markdown that passes the required section contract and a lexical source-grounding smoke check, records resolved mode/provider/model/params plus prompt hash in `model_call`, embeds compact citation survival payloads, promotes a machine-owned checked `digest` plus brand-new hubs, and stages curated hub suggestions without overwriting curated hubs. |
| Regenerate tracked projections | runtime projection helper (`write_tracked_projections`) / worker operation `regenerate-tracked-projections` | Rebuilds `index.md`, bundle indexes, `knowledge/_views/index.md`, and `references.bib` in one worker-owned projection run. |
| Regenerate workspace indexes | runtime projection helper (`write_workspace_indexes`) / worker operation `regenerate-indexes` | Rebuilds the root and bundle `index.md` projections from checked Concept files. |
| Regenerate capability index | runtime capability helper (`write_capability_index`) / worker operation `regenerate-capability-index` | Rebuilds ignored `.memoria/index/capability-index.json` from packaged capability manifests and records product SHA-256 trust hashes. |
| Import capability | runtime capability helper (`import_capability`) | Quarantines unsigned imported capability files under `.memoria/quarantine/`, records a failed `capability-import-trust` check, and does not make them executable or catalog-visible. Signed promotion is not implemented. |

### Search input and query (`memoria_vault.runtime.search_index`)

| Action | Performer | What it does |
| --- | --- | --- |
| Rebuild checked qmd source | worker operation `rebuild-checked-qmd-source` + runtime helper (`rebuild_checked_qmd_source`) | Rebuilds `.memoria/index/qmd/checked/` from checked retrieval documents: current Concepts plus generated checked Work text and graph neighborhoods. |
| Answer query | worker operation `answer-query` + runtime helper (`answer_query`) | Returns the qmd-backed or deterministic BM25 Ask/Query contract over checked retrieval documents: sources, unknowns, staleness, contradictions, and project context when supplied. |

### Knowledge construction (`memoria_vault.runtime.knowledge`)

| Action | Performer | What it does |
| --- | --- | --- |
| Emit note candidates | worker operation `propose-note-candidates` + runtime helper (`emit_note_candidates`) | Reads one checked digest, records resolved runner provenance in `model_call`, promotes checked `note` Concepts, and records note-candidate state in the journal/SQLite state rather than frontmatter. |
| Curate note candidate | worker operation `curate-note-candidate` + runtime helper (`curate_note_candidate`) | Records a PI accept/reject decision for one checked candidate `note` as a journal `resolved` row without mutating Concept frontmatter. |
| Curate note link | worker operation `curate-note-link` + runtime helper (`curate_note_link`) | Records one PI-authored `supports`, `contradicts`, or `extends` link from a checked note to a checked Concept, updating the note's `links` map and committing it with a journal `resolved` row. |
| Analyze gaps | worker operation `analyze-gaps` + runtime helper (`analyze_gaps`) | Counts checked-current source/digest/accepted-note topic signals and reports `new-topic`, `undigested`, and `under-warranted` gaps with proposed seed actions; when a project path is supplied, it also seeds project scope/facet terms, counts checked linked thesis terms, and includes checked project argument-health gaps. |
| Analyze project argument | worker operation `analyze-project-argument` + runtime helper (`analyze_project_argument`) | Follows checked, non-candidate note links around a checked project's `thesis` note and returns relation counts, stage, saturation, gap/advisory taxonomy, nodes, and edges. |
| Render project argument Canvas | worker operation `render-project-argument-canvas` + runtime helper (`write_project_argument_canvas`) | Renders the checked-note argument graph for one project as a generated `knowledge/projects/<project>/argument.canvas` projection and commits it with a journal row. |
| Run prompt operation | worker operation `<pattern-id>` + runtime helper (`run_prompt_operation`) | Reads checked input refs for checked prompt-operation manifests such as `analyze-claims`, records request/journal provenance, and stages one unchecked report note under `.memoria/staging/knowledge/`. |

### Integrity loop (`memoria_vault.runtime.integrity`)

| Action | Performer | What it does |
| --- | --- | --- |
| Check evidence integrity | runtime integrity helper (`check_evidence_integrity`) | Scans checked `digest` and `note` Concepts and flags unresolved `source_id` or `evidence_set` references. |
| Check source metadata | runtime integrity helper (`check_source_metadata`) | Flags checked `source` Concepts that lack citekey, CSL-JSON basics, issued year, an external resource/identifier, or carry conflicting DOI metadata. |
| Check quote anchors | runtime integrity helper (`check_quote_anchor_support`) | Flags checked notes whose quoted span is absent from checked source text declared by `source_id` or `evidence_set`. |
| Record integrity check | runtime integrity helper (`record_integrity_check`) | Appends a `check-fired` event with shadow-first `drop` routing by default; active failures route `ask`, and explicit auto-revert checks route `act`. |
| Check claim quote support | runtime integrity helper (`check_claim_quote_support`) | Flags checked notes whose claim and cited quote share no substantive terms; this is a high-precision first pass for unwarranted-claim seeded errors, not a full NLI replacement. |
| Check prompt-injection markers | runtime integrity helper (`check_prompt_injection_markers`) | Flags checked sources, digests, or notes containing explicit prompt-injection marker text; this is a high-precision marker check, not semantic injection detection. |
| Check provenance checkpoint | runtime integrity helper (`check_provenance_checkpoint`) | Flags checked notes or digests that depend on checked sources whose provider coverage is still partial or degraded; this routes fresh uncorroborated source use to PI attention without claiming semantic detection. |
| Check citation survival | runtime integrity helper (`check_citation_survival`) | Flags checked notes, digests, or hubs that reference catalog sources without compact citation payloads sufficient to read the keep-set without SQLite. |
| Surface tensions | worker operation `surface-tensions` + runtime helper (`surface_tensions`) | Runs the Tier-1 HANS-gated contradiction candidate pass over checked notes and works; if Tier-1 is degraded, lexical candidates route to PI attention, and no `contradicts` link is written. |
| Check contradiction links | runtime integrity helper (`check_contradiction_links`) | Flags checked digests whose explicit `contradictions` targets are missing, unchecked, or stale; this is structural link integrity, not semantic contradiction discovery. |
| Check link targets | runtime integrity helper (`check_link_targets`) | Flags checked Concepts whose explicit path-like `links` targets are missing, unchecked, or stale; this is structural link-target integrity, not semantic false-link detection. |
| Trace downstream | runtime integrity helper (`trace_downstream`) | Rebuilds the downstream graph from journal `derived.inputs` without reading unchecked Concepts. |
| Cascade rollback | runtime integrity helper (`cascade_rollback`) | Moves machine-derived downstream Concepts to `.memoria/quarantine/`, appends `resolved` plus inverse `derived` events, and leaves PI-derived downstream Concepts live while flagging them with route `ask`. |
| Run seeded-error verdict | worker operation `run-seeded-error-verdict` + runtime helper (`run_seeded_error_verdict`) | Builds the seeded structural fixture from `system/eval/alpha15-seeded-errors.json` (falling back to alpha.12/alpha.11) in a disposable temp workspace, measures recall, false positives, check timing, detection timing, rollback completeness, residual error, no-checks residual baseline, residual reduction, and ask-routed checkpoint value, then returns a pass/fail verdict and live-only non-sandbox license flag for that bundle. |

### Linter (`memoria_vault.runtime.subsystems.integrity.linter`)

The seventeen registered detectors (slugs, severities, and what each catches) live in [Linter: detectors and auto-fix](linter.md#the-detectors); every detector is report-only.

| Action | Performer | What it does |
| --- | --- | --- |
| Run detectors | Linter (`detectors.py`, daily cron) | Runs all seventeen structural detectors over the vault; findings surface on the drift dashboards. |
| Pre-commit hook | Linter (`precommit_check.py`, git hook) | Schema-validates staged notes and blocks the commit on a violation — the one check that prevents rather than reports. |
| Golden stage | Linter (`golden_restore.py stage`) | Snapshots every shipped system file (templates, dashboards, patterns, eval set, and root guidance files) into a SHA-256 manifest. |
| Golden check | Linter (`golden_restore.py check`, daily cron) | Reports system files that drifted from or went missing against the golden manifest. |
| Golden restore | Linter (`golden_restore.py restore`) | Lists what restoring would change; writes the golden bytes back only with `--apply` (a PI decision). |
| Session digests | Linter (`session_summary.py`, daily cron) | Writes one deterministic per-session digest file under `system/logs/sessions/` from the audit log ([ADR-25](../adr/25-session-logging-two-logs.md)). |
| Hub proposal handoff | Linter (`hub_handoff.py`, PI-run) | Converts current `hub-threshold` findings into idempotent local handoff payloads for map work; curated `knowledge/hubs/` stays PI-approved. |

### Sweeps (`memoria_vault.runtime.subsystems`)

| Action | Performer | What it does |
| --- | --- | --- |
| Eval dispatch | sweeps operation (`eval_dispatch.py`, scheduled task or `memoria eval run`) | Fans the gold set out as one idempotent local eval task per current task ([Vault eval](vault-eval.md)). |
| Eval score | sweeps operation (`eval_score.py`, scheduled task) | Computes recall@k / support-rate / FAMA-clean from local result blocks; appends to `system/metrics/eval/runs.jsonl`. |
| Retraction check | sweeps operation (`retraction.py`) | Checks a DOI against the Retraction Watch dataset, Crossref, and Open Retractions (read-only). |
| Retraction sweep | sweeps operation (`retraction.py`) | Scans the catalog's DOIs for retractions and hands findings to the agent to flag. |
| Emit worklist | shared operation helper (`worklists.py`) | Converts a scan/search report into file-backed worklist projections and one aggregate `work-prompt` attention projection. |

## Runtime policy and helper modules

| Action | Performer | What it does |
| --- | --- | --- |
| Policy decision | [Policy gate](policy-mcp.md) (`memoria_vault.runtime.policy`) | Decides allow / allow_with_log / deny / dry_run for optional adapter writes and runtime checks; fail-closed. |
| Pre-tool gate | runtime policy hook (`memoria_vault.runtime.policy.hook`) | Optional adapters call it before a tool runs; denied, dry-run, direct-file, terminal, browser, and unaudited egress tools are blocked. |
| Post-tool pairing | runtime policy hook (`memoria_vault.runtime.policy.hook`) | Computes the `after_hash` and appends the paired reversibility record to `system/logs/audit.jsonl`. |
| Build graph neighborhoods | runtime search/knowledge helpers | Builds checked retrieval documents and first-order graph-neighborhood text for qmd-backed ask and gap analysis. |
| Render argument canvas | worker operation `render-project-argument-canvas` | Renders the project argument map as a JSON Canvas artifact from checked project graph state. |
| List / run prompt operations | runtime prompt helper (`memoria_vault.runtime.patterns`) and `memoria operation run` | Lists checked packaged prompt operations, composes prompt runs, refuses gated-zone output targets, and logs provenance. |
| Loudness routing | shared operation helper (`memoria_vault.runtime.subsystems.lib.loudness`) | Sends/logs alert/block push attempts, keeps quiet/notice pull-only, and exposes open block cards to delegation and policy gates. |

## CLI requests

| Action | Performer | What it does |
| --- | --- | --- |
| Run integrity check | `memoria operation run <operation-id>` | Inserts one SQLite request and runs worker-owned integrity operations such as `integrity-evidence-check`, `integrity-quote-anchor-check`, `integrity-claim-quote-check`, `integrity-link-target-check`, and `check-source-metadata`; the worker owns journal rows and routing. |
| Capture or enrich source | `memoria work add`, `memoria work import`, `memoria work enrich` | Creates the request envelope in `.memoria/memoria.sqlite`, runs capture/enrichment, writes provider/raw payloads, and materializes checked source/catalog outputs through the worker boundary. |
| Compile digest or record interview | `memoria work digest`, `memoria work interview` | Queues and runs source synthesis jobs, recording Co-PI interview takeaways and digest materialization through the same request/journal path. |
| Ask query | `memoria ask --question ...` / `memoria project ask <project-id> --question ...` | Runs `answer-query` and returns the Ask/Query response contract over checked retrieval documents; project Ask includes checked project context when available. |
| Author and curate Concepts | `memoria new note`, `memoria check`, `memoria link` | Authors PI or CLI-agent Concepts through the engine request envelope, promotes checked Concepts through the request boundary, and records typed-link curation through worker-owned requests and journal rows. |
| Analyze project | `memoria project gaps <project-path>`, `trace`, `frame-paper`, `export` | Runs checked graph, project-scope, linked-thesis, project-argument, and paper-readiness gap analysis; records PI-supplied paper framing; runs argument tracing; and performs deterministic Markdown/Pandoc project export from the CLI control plane. New Project Concepts are authored through `memoria new project`, queued as `create-concept`, and remain unchecked until review/check promotion. |
| Refresh projections and search | `memoria workspace rebuild` | Regenerates tracked projections, bibliography, workspace indexes, and checked-only qmd inputs from worker-readable state. |
| Trace rollback | `memoria workspace rollback` | Runs `cascade-rollback` against a target id; the worker owns quarantine, commit, and journal rows. |
| Observe PI edits | Worker / file-watch trigger | Runs `observe-pi-edits`, scanning bundle-root git status and committing direct PI Concept edits with backfilled `derived` events. |
| Resolve attention | `memoria attention resolve (--apply\|--reject\|--defer)` | Runs the attention-disposition request, records routing class plus PI resolution outcome, and closes or defers the attention projection in the committed journal row. |
| Inspect requests | `memoria status`, `memoria request list`, `memoria doctor bundle` | Reads SQLite request state and diagnostic bundles; no file queue mirror exists. |

## Optional external adapters

| Action | Performer | What it does |
| --- | --- | --- |
| Vault read / gated write | optional editor or BYO-agent adapter | Reads may inspect workspace files; writes must call the runtime policy hook and then enter the same checked request/journal boundary as CLI work. |
| Vault search | `memoria ask` / qmd debug commands | Uses the checked-only qmd tree and runtime read barrier; no required external operation API ships. |
| Literature discovery | provider-backed runtime operations | Uses configured provider allowlists and replay fixtures for tests; no live Zotero or required external agent server is authoritative. |
| Portable bibliography import | `memoria work import --format bibtex` or `--format csl` | Reads local BibTeX or CSL JSON files as input data only; no live reference-manager DB/API is a baseline dependency. |

## Scheduled tasks (`.memoria/scripts/`)

The deterministic scheduled jobs are optional operator wiring around the CLI and
runtime package. The shipped wrappers call `.memoria/scripts/cron-runner.sh`,
which dispatches `sweeps`, `worker`, `lint`, `eval`, and
`retraction-refresh`. No scheduler is required for a one-shot CLI workflow; a
systemd timer, cron entry, launchd job, or another local scheduler can call the
same wrappers when always-on maintenance is desired.

## Skills and prompts

Alpha.14 does not ship installed profile skill bundles or per-lane task routing.
Reusable prompt behavior lives as checked packaged operation manifests and runs
through `memoria operation run`. Optional
adapters may expose their own skills later, but those adapters are not current
product authority.

## PI actions

### Review decisions

| Action | What it does |
| --- | --- |
| Worker promotion | Machine writes promote from `.memoria/staging/` only after worker checks set DB/read API `check_status = checked`; operation-owned promotions enforce their `required_checks` (`memoria-runtime`) before the state transition and record durable materialization payloads in SQLite. PI edits are direct, then the worker observes git-status changes and backfills `{Concept + journal}`. |
| Inbox triage | Resolve or act on attention projections; dispositions are logged for trust and attention metrics. |
| Golden restore `--apply` | The PI (not the cron) decides to write golden bytes back over drifted system files. |
