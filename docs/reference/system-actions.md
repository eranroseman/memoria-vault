---
title: System actions
parent: Agents and control
grand_parent: Reference
---

# System actions

Every action the system can perform, with its performer. Three performer kinds: **deterministic operations** (zero-LLM Python, report-only or idempotent), **agents** (LLM lanes acting through gated MCP tools and skills), and the **PI** (palette actions and review decisions). Where a topic has its own reference page, that page is authoritative for the details — this catalog is the map.

This page is a guarded mirror, not the source of truth. Action implementation lives in the referenced Python modules, QuickAdd scripts, profile skills, and linked reference pages; docs checks keep the mirror linked.

## Deterministic operations

### Capture pipeline (`memoria_vault.runtime.capture`)

| Action | Performer | What it does |
| --- | --- | --- |
| Capture source | worker operation `capture-source` + runtime helper (`capture_source`) | Records a capture run, writes `catalog/sources/<source_id>/{source.md,content.md,raw/}`, promotes the `source` and any metadata-derived entity Concepts through the trusted writer, merges existing source metadata and exact entity source links, and commits Concepts/content/journal together ([Ingest routing](ingest.md)). |
| Capture BibTeX source | worker operation `capture-bibtex-source` + runtime helper (`capture_bibtex_source`) | Parses one local BibTeX entry into a DOI/URL-derived `source_id` when available, citekey alias, CSL-JSON-shaped metadata, identifiers, raw `.bib`, checked source Concept path, and deterministic person/venue Concepts. |
| Capture Zotero source | worker operation `capture-zotero-source` + runtime helpers (`capture_zotero_source`, `capture_zotero_local_source`) | Maps one Zotero Local API item JSON snapshot, or fetches one local desktop API item key first, into stable `source_id`, citekey alias, CSL-JSON-shaped metadata, identifiers, raw `.zotero.json`, checked source Concept path, and deterministic person/venue Concepts. |
| Capture URL source | worker operation `capture-url-source` + runtime helper (`capture_url_source`) | Fetches one URL, preserves raw HTML, extracts plain text with stdlib `HTMLParser`, and writes the same checked source Concept path. |
| Capture PDF source | worker operation `capture-pdf-source` + runtime helper (`capture_pdf_source`) | Uses the optional PyMuPDF parser to extract page text from raw PDF bytes and writes the same checked source Concept path. |
| Regenerate bibliography | runtime capture helper (`write_references_bib`) / worker operation `regenerate-references-bib` | Rebuilds `references.bib` from checked source Concepts with citekeys and can commit the projection plus journal event through the worker. |
| Capture trace | trusted writer + journal | Records `run`, `derived`, and `check-fired` events for the source Concept; raw blobs stay gitignored and are referenced by path + hash. |
| Foreign-write quarantine | worker operation `trace-integrity-scan` + trusted writer (`quarantine_untraced_from_status` / `quarantine_untraced`) | Scans git-status or explicit bundle paths, moves untraced bundle files into `.memoria/quarantine/`, and records a failed `trace-integrity` check event. |

### Operation runner (`memoria_vault.runtime.operations`)

| Action | Performer | What it does |
| --- | --- | --- |
| Load operation policy | runtime operation helper (`load_operation_policy`) | Loads a checked `operation` Concept and requires the WP5 policy contract: tools, paths, network, runner/model, prompt version, `io_schema.input`/`io_schema.output`, risk class, and checks. |
| Record Co-PI interview | worker operation `record-copi-interview` + runtime helper (`record_copi_interview_turn`) | Records a PI interview takeaway for a checked source as a committed `copi-interview` journal event; digest compile can consume it as traced context. |
| Compile source digest | worker operation `compile-source-digest` + runtime helper (`compile_source_digest`) | Reads one checked source, uses deterministic fixture output or an allowed OpenAI-compatible direct-API runner for digest markdown that passes the required section contract and a lexical source-grounding smoke check, records a `model_call`, promotes a machine-owned checked `digest` plus brand-new hubs, and stages curated hub suggestions without overwriting curated hubs. |
| Regenerate tracked projections | runtime projection helper (`write_tracked_projections`) / worker operation `regenerate-tracked-projections` | Rebuilds `index.md`, bundle indexes, `references.bib`, and `capabilities/ai-catalog.json` in one worker-owned projection run. |
| Regenerate workspace indexes | runtime projection helper (`write_workspace_indexes`) / worker operation `regenerate-indexes` | Rebuilds the root and bundle `index.md` projections from checked Concept files. |
| Regenerate capability catalog | runtime capability helper (`write_ai_catalog`) / worker operation `regenerate-ai-catalog` | Rebuilds `capabilities/ai-catalog.json` from capability Concepts and records local SHA-256 trust hashes. |
| Import capability | runtime capability helper (`import_capability`) | Quarantines unsigned imported capability files under `.memoria/quarantine/`, records a failed `capability-import-trust` check, and does not make them executable or catalog-visible. Signed promotion is not implemented in alpha.11. |

### Search input and query (`memoria_vault.runtime.search_index`)

| Action | Performer | What it does |
| --- | --- | --- |
| Rebuild checked qmd source | worker operation `rebuild-checked-qmd-source` + runtime helper (`rebuild_checked_qmd_source`) | Rebuilds `.memoria/index/qmd/checked/` from checked, current Concepts only and writes the disposable qmd manifest. |
| Answer query | worker operation `answer-query` + runtime helper (`answer_query`) | Returns the deterministic BM25 Ask/Query contract over checked current Concepts: sources, unknowns, staleness, and contradictions. |

### Knowledge construction (`memoria_vault.runtime.knowledge`)

| Action | Performer | What it does |
| --- | --- | --- |
| Emit note candidates | worker operation `propose-note-candidates` + runtime helper (`emit_note_candidates`) | Reads one checked digest, records a `model_call`, promotes checked `note` Concepts with `status: candidate`, and commits notes plus journal together. |
| Curate note candidate | worker operation `curate-note-candidate` + runtime helper (`curate_note_candidate`) | Records a PI accept/reject decision for one checked candidate `note`, updates `status`, and commits the note plus a journal `resolved` row together. |
| Curate note link | worker operation `curate-note-link` + runtime helper (`curate_note_link`) | Records one PI-authored `supports`, `contradicts`, or `extends` link from a checked note to a checked Concept, updating the note's `links` map and committing it with a journal `resolved` row. |
| Analyze gaps | worker operation `analyze-gaps` + runtime helper (`analyze_gaps`) | Counts checked-current source/digest/accepted-note topic signals and reports `new-topic`, `undigested`, and `under-warranted` gaps with proposed seed actions. |
| Analyze project argument | worker operation `analyze-project-argument` + runtime helper (`analyze_project_argument`) | Follows checked, non-candidate note links around a checked project's `thesis` note and returns relation counts, stage, saturation, gap/advisory taxonomy, nodes, and edges. |
| Render project argument Canvas | worker operation `render-project-argument-canvas` + runtime helper (`write_project_argument_canvas`) | Renders the checked-note argument graph for one project as a generated `knowledge/projects/<project>/argument.canvas` projection and commits it with a journal row. |

### Integrity loop (`memoria_vault.runtime.integrity`)

| Action | Performer | What it does |
| --- | --- | --- |
| Check evidence integrity | runtime integrity helper (`check_evidence_integrity`) | Scans checked `digest` and `note` Concepts and flags unresolved `source_id` or `evidence_set` references. |
| Check source metadata | runtime integrity helper (`check_source_metadata`) | Flags checked `source` Concepts that lack citekey, CSL-JSON basics, issued year, an external resource/identifier, or carry conflicting DOI metadata. |
| Check quote anchors | runtime integrity helper (`check_quote_anchor_support`) | Flags checked notes whose quoted span is absent from checked source text declared by `source_id` or `evidence_set`. |
| Record integrity check | runtime integrity helper (`record_integrity_check`) | Appends a `check-fired` event with shadow-first `drop` routing by default; active failures route `ask`, and explicit auto-revert checks route `act`. |
| Check claim quote support | runtime integrity helper (`check_claim_quote_support`) | Flags checked notes whose claim and cited quote share no substantive terms; this is a high-precision first pass for unwarranted-claim seeded errors, not a full NLI replacement. |
| Check prompt-injection markers | runtime integrity helper (`check_prompt_injection_markers`) | Flags checked sources, digests, or notes containing explicit prompt-injection marker text; this is a high-precision marker check, not semantic injection detection. |
| Check provenance checkpoint | runtime integrity helper (`check_provenance_checkpoint`) | Flags checked notes or digests that depend on checked sources whose metadata is still partial, unverified, or not indexed; this routes fresh uncorroborated source use to PI attention without claiming semantic detection. |
| Check contradiction links | runtime integrity helper (`check_contradiction_links`) | Flags checked digests whose explicit `contradictions` targets are missing, unchecked, or stale; this is structural link integrity, not semantic contradiction discovery. |
| Check link targets | runtime integrity helper (`check_link_targets`) | Flags checked Concepts whose explicit path-like `links` targets are missing, unchecked, or stale; this is structural link-target integrity, not semantic false-link detection. |
| Trace downstream | runtime integrity helper (`trace_downstream`) | Rebuilds the downstream graph from journal `derived.inputs` without reading unchecked Concepts. |
| Cascade rollback | runtime integrity helper (`cascade_rollback`) | Moves machine-derived downstream Concepts to `.memoria/quarantine/`, appends `resolved` plus inverse `derived` events, and leaves PI-derived downstream Concepts live while flagging them with route `ask`. |
| Run seeded-error verdict | worker operation `run-seeded-error-verdict` + runtime helper (`run_seeded_error_verdict`) | Builds the frozen alpha.11 structural fixture from `system/eval/alpha11-seeded-errors.json` in a disposable temp workspace, measures recall, false positives, check timing, detection timing, rollback completeness, residual error, no-checks residual baseline, residual reduction, and ask-routed checkpoint value, then returns a pass/fail verdict for that bundle. |

### Linter (`operations/integrity/linter/`)

The seventeen registered detectors (slugs, severities, and what each catches) live in [Linter: detectors and auto-fix](linter.md#the-detectors); every detector is report-only.

| Action | Performer | What it does |
| --- | --- | --- |
| Run detectors | Linter (`detectors.py`, daily cron) | Runs all seventeen structural detectors over the vault; findings surface on the drift dashboards. |
| Pre-commit hook | Linter (`precommit_check.py`, git hook) | Schema-validates staged notes and blocks the commit on a violation — the one check that prevents rather than reports. |
| Golden stage | Linter (`golden_restore.py stage`) | Snapshots every system file (templates, dashboards, patterns, eval set, scripts, shipped Obsidian config) into a SHA-256 manifest. |
| Golden check | Linter (`golden_restore.py check`, daily cron) | Reports system files that drifted from or went missing against the golden manifest. |
| Golden restore | Linter (`golden_restore.py restore`) | Lists what restoring would change; writes the golden bytes back only with `--apply` (a PI decision). |
| Session digests | Linter (`session_summary.py`, daily cron) | Writes one deterministic per-session digest file under `system/logs/sessions/` from the audit log ([ADR-25](../adr/25-session-logging-two-logs.md)). |
| Hub proposal handoff | Linter (`hub_handoff.py`, PI-run) | Converts current `hub-threshold` findings into idempotent Librarian `map` cards that stage proposals under `knowledge/notes/maps/`; curated `knowledge/hubs/` stays PI-approved. |

### Sweeps (`operations/`)

| Action | Performer | What it does |
| --- | --- | --- |
| Eval dispatch | sweeps operation (`eval_dispatch.py`, quarterly cron) | Fans the gold set out as one idempotent kanban card per task, routed to the owning lane ([Vault eval](vault-eval.md)). |
| Eval score | sweeps operation (`eval_score.py`, quarterly cron) | Computes recall@k / support-rate / FAMA-clean from the result blocks reported on eval cards; appends to `system/metrics/eval/runs.jsonl`. |
| Retraction check | sweeps operation (`retraction.py`) | Checks a DOI against the Retraction Watch dataset, Crossref, and Open Retractions (read-only). |
| Retraction sweep | sweeps operation (`retraction.py`) | Scans the catalog's DOIs for retractions and hands findings to the agent to flag. |
| Emit worklist | shared operation helper (`worklists.py`) | Converts a scan/search report into file-backed worklist projections and one aggregate `work-prompt` attention projection. |

## Vault-side MCP servers and hooks (`.memoria/mcp/`)

| Action | Performer | What it does |
| --- | --- | --- |
| Policy decision | [Policy MCP](policy-mcp.md) (`policy_mcp.py`) | Decides allow / allow_with_log / deny / dry_run for every vault action against the lane's ceiling; fail-closed. |
| Pre-tool gate | policy hook (`policy_hook.py`) | Blocks denied or gated writes before the tool runs and stashes the file's `before_hash`. |
| Post-tool pairing | policy hook (`policy_hook.py`) | Computes the `after_hash` and appends the paired reversibility record to `system/logs/audit.jsonl`. |
| Build cluster graph | cluster MCP (`cluster_mcp.py`), Librarian-facing | Builds the typed knowledge graph from authored links and computes communities and centrality. |
| Emit canvas | cluster MCP (`cluster_mcp.py`) | Renders the note-debate map as a JSON Canvas under `knowledge/notes/maps/`, with status-colored nodes and typed edges. |
| Model topics | cluster MCP (`cluster_mcp.py`) | Runs BERTopic over the corpus to extract topics, the doc-topic map, and outliers. |
| List / run patterns | patterns MCP (`patterns_mcp.py`) | Lists checked prompt operations from `capabilities/operations/` and composes a pattern run, refusing gated-zone output targets and logging provenance. |
| Route task | tasks MCP (`tasks_mcp.py`), Co-PI-facing | Validates a delegation against the target lane's ceiling, refuses dispatch while an open `loudness: block` card exists, and creates the kanban card. |
| Loudness routing | shared operation helper (`operations/lib/loudness.py`) | Sends/logs alert/block push attempts, keeps quiet/notice pull-only, and exposes open block cards to delegation and policy gates. |
| Board export | board export (`board_export.py`, 60 s cron) | Projects kanban cards into `system/board/` and appends board-state, transition, cost, and blind-review telemetry; review disposition is emitted by QuickAdd when the human resolves a work prompt. |
| Metrics aggregate | metrics aggregator (`metrics_aggregate.py`, weekly cron) | Rolls audit + board + lint signals into per-lane trust-score notes under `system/metrics/`. |

## Obsidian control panel

| Action | Performer | What it does |
| --- | --- | --- |
| Enqueue integrity evidence check | Memoria Inspector (`memoria-inspector`) | Writes one `kind: operation` job to `.memoria/queue/pending/` for the worker to run `integrity-evidence-check`; the plugin does not write Concepts, journal rows, projections, or `check_status` directly. |
| Enqueue quote anchor check | Memoria Inspector (`memoria-inspector`) | Writes one `kind: operation` job to `.memoria/queue/pending/` for the worker to run `integrity-quote-anchor-check`; the worker owns journal rows and routing. |
| Enqueue claim quote check | Memoria Inspector (`memoria-inspector`) | Writes one `kind: operation` job to `.memoria/queue/pending/` for the worker to run `integrity-claim-quote-check`; the worker owns journal rows and routing. |
| Enqueue link target check | Memoria Inspector (`memoria-inspector`) | Writes one `kind: operation` job to `.memoria/queue/pending/` for the worker to run `integrity-link-target-check`; the worker owns journal rows and routing. |
| Enqueue source metadata check | Memoria Inspector (`memoria-inspector`) | Writes one `kind: operation` job to `.memoria/queue/pending/` for the worker to run `check-source-metadata`; the worker owns journal rows and routing. |
| Enqueue projection refresh | Memoria Inspector (`memoria-inspector`) | Writes one `regenerate-tracked-projections` job to `.memoria/queue/pending/`; the worker owns generated projection writes. |
| Enqueue search rebuild | Memoria Inspector (`memoria-inspector`) | Writes one `rebuild-checked-qmd-source` job to `.memoria/queue/pending/`; the worker rebuilds the disposable checked-only qmd input tree. |
| Enqueue Ask query | Memoria Inspector (`memoria-inspector`) | Writes one `answer-query` job with the PI-entered query to `.memoria/queue/pending/`; the worker returns the deterministic BM25 Ask/Query contract. |
| Enqueue Co-PI interview record | Memoria Inspector (`memoria-inspector`) | Writes one `record-copi-interview` job with the PI-entered source id and takeaway; the worker records the interview turn in the journal for later source synthesis. |
| Enqueue note candidate curation | Memoria Inspector (`memoria-inspector`) | Writes one `curate-note-candidate` job with the PI-entered note path and accept/reject decision; the worker owns the note status update and journal row. |
| Enqueue note link curation | Memoria Inspector (`memoria-inspector`) | Writes one `curate-note-link` job with PI-entered source note, target Concept, and relation type; the worker owns the `links` map update and journal row. |
| Enqueue gap analysis | Memoria Inspector (`memoria-inspector`) | Writes one `analyze-gaps` job to `.memoria/queue/pending/`; the worker returns deterministic gap rows over checked-current Concepts. |
| Enqueue project argument analysis | Memoria Inspector (`memoria-inspector`) | Writes one `analyze-project-argument` job with the PI-entered project path; the worker returns the checked-note argument-health payload. |
| Enqueue project argument Canvas | Memoria Inspector (`memoria-inspector`) | Writes one `render-project-argument-canvas` job with the PI-entered project path; the worker owns the generated Canvas projection and journal row. |
| Enqueue trace rollback | Memoria Inspector (`memoria-inspector`) | Writes one `kind: operation` job to `.memoria/queue/pending/` for the worker to run `cascade-rollback` against a PI-entered trace target; the worker owns the rollback commit and journal rows. |
| Observe PI edits | Worker / file-watch trigger | Runs `observe-pi-edits`, scanning bundle-root git status and committing direct PI Concept edits with backfilled `derived` events. |
| Enqueue attention disposition | Memoria Inspector (`memoria-inspector`) | Writes `acknowledge-attention` or `resolve-attention` jobs to `.memoria/queue/pending/`; the worker records the PI disposition as a committed journal `resolved` row. |
| Inspect worker queue | Memoria Inspector (`memoria-inspector`) | Reads `.memoria/queue/{pending,running,failed}/` job files and shows queue counts plus recent failed jobs; it does not modify queue state. |
| Browse checked graph | Memoria Inspector (`memoria-inspector`) | Reads checked `catalog/` and `knowledge/` Concepts plus their declared references, previews recent nodes and edges, then opens existing Concept notes, normalized edge targets, or `knowledge/views/knowledge.base`; it does not write graph state. |

## External MCP servers (declared per profile)

| Action | Performer | What it does |
| --- | --- | --- |
| Vault read / gated write | obsidian native MCP (all lanes) | File reads, search, and writes into the vault over the Local REST API plugin's MCP — every write passing the policy gate. |
| Vault search | filtered qmd MCP (Librarian, Writer, Co-PI, Peer-reviewer) | Checked-only qmd search over the Concept corpus, local and read-only; unchecked and quarantined Concepts are hidden by the read barrier, and BM25 is the current eval baseline. |
| Literature discovery | paper_search MCP (Librarian) | Searches arXiv, PubMed, Semantic Scholar, Google Scholar, and bioRxiv (Unpaywall email for OA lookups). |
| Zotero reads | pyzotero MCP (Librarian, Peer-reviewer) | Read-only citekey resolution, metadata, and citation context from the local Zotero library — no write-back. |

## Scheduled crons (`.memoria/scripts/`)

The deterministic cron jobs (board export, sweeps, lint, metrics, retraction refresh, eval) and their schedules are owned by [Installer (bootstrap)](installer.md#the-crons-it-wires). They run from the repo source wrappers under `.memoria/scripts/`: the installer copies each `<job>-cron.sh` to `~/.hermes/scripts/` renamed **`memoria-<job>.sh`** — that `memoria-*` form is the cron-job name `hermes cron list` shows.

## Agent skills (per lane)

### Librarian (14)

| Skill | What it does |
| --- | --- |
| catalog-find-source | Searches the literature via paper_search, screens against the workspace, and raises honesty-bodied attention projections. |
| catalog-rank-candidate | Ranks candidate sources by relevance / novelty / venue into a batch worklist. |
| catalog-classify-source | Proposes `research_area` / `methodology` from the vocabulary for human promotion at triage. |
| catalog-enrich-record | Runs the ingest pipeline MCP, fills the classification and `[!brief]` holes, applies the gated writes. |
| extract-flag-distill | Flags kept sources worth reading and raises a distill work prompt. |
| extract-stub-claim | Proposes one-sentence, citekey-bound claim stubs in a source's "Worth distilling" section. |
| link-suggest-claim | Proposes typed links (supports / contradicts / extends) as attention with quoted evidence. |
| link-surface-tension | Surfaces claim-pair contradictions with both sides quoted and reconciliation options. |
| map-cluster-corpus | Clusters topics via the cluster MCP and emits a map note plus a report card. |
| map-report-coverage | Topic-models the corpus and composes a gap report of thin topics; records rejected directions/dead ends as a companion exploration-trace note when present. |
| map-scope-project | Corpus-maps a project into a narrative map with thin spots named; records rejected directions/dead ends as a companion exploration-trace note when present. |
| map-seed-canvas | Seeds a JSON Canvas from the cluster graph (communities, edges, layout). |
| map-graph-claims | Emits a propose-class claim-debate JSON Canvas from authored `supports` / `contradicts` / `extends` links, with pruning disclosed in a companion note. |
| map-canvas-hub | Assembles existing maps, claim graphs, project gates, and dashboards into a propose-class JSON Canvas hub for navigation. |

### Writer (4)

| Skill | What it does |
| --- | --- |
| draft-outline-argument | Produces 2–3 outline options for an argument, each with a counter-outline. |
| draft-score-outline | Scores an outline against coverage / maturity / contradictions / holes (advisory). |
| draft-write-section | Drafts a prose section with every fact bound to a citekey, marking holes. |
| draft-bind-citation | Binds every factual sentence to a citekey and normalizes citations against the bibliography. |

### Peer-reviewer (4)

| Skill | What it does |
| --- | --- |
| verify-trace-claim | Traces a draft's factual claims to supporting notes (link → citekey → similarity) and flags failures. |
| verify-check-citation | Checks every `[@citekey]` resolves and that the source supports the claim. |
| verify-card-gap | Converts missing-evidence findings into gap attention in `inbox/`. |
| verify-propose-fix | Proposes the obvious remedy for a finding as attention — flag, don't fix. |

### Co-PI (5)

| Skill | What it does |
| --- | --- |
| ask-question-source | Answers questions about a source from vault holdings, read-only. |
| ask-read-lens | Re-reads a source through a named lens (frame / checklist / hypothesis), read-only. |
| explore-framings | Branches a question into rival framings — the sparring partner. |
| route-task | Routes work to the right lane via the tasks MCP with a composed handoff payload. |
| explain-system | Teaches how Memoria works, pointing at concrete affordances. |

## PI actions

### Palette (QuickAdd scripts, `system/scripts/`)

| Action | What it does |
| --- | --- |
| Capture note | Creates an unchecked `note` Concept in `knowledge/notes/` from the bundled note template. |
| Open Inbox | Opens the Inbox projection at `spaces/inbox.md` without mutating the active note. |
| Record exploration trace | Captures a rejected direction/dead end beside a map or gap report under `knowledge/notes/maps/`; it stays project-local and unchecked until reviewed. |
| Resolve inbox card | Resolves the active attention projection by setting `attention_status: resolved` and appending attention/triage telemetry. |

### Review decisions

| Action | What it does |
| --- | --- |
| Worker promotion | Machine writes promote from `.memoria/staging/` only after worker checks set `check_status: checked`; operation-owned promotions enforce their `required_checks` (`memoria-profile` in alpha.11) before the state transition. PI edits are direct, then the worker observes git-status changes and backfills `{Concept + journal}`. |
| Inbox triage | Resolve or act on attention projections; dispositions are logged for trust and attention metrics. |
| Golden restore `--apply` | The PI (not the cron) decides to write golden bytes back over drifted system files. |
