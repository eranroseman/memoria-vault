---
title: System action operations
parent: Commands and transports
nav_order: 2
grand_parent: Reference
---

# System action operations

Deterministic operations and runtime helpers behind the system action roster.
For the guarded operation ID list, see [System actions](system-actions.md).

## Request authority and retries

Every request carries one validated actor. The worker enforces the operation
authority matrix before payload validation or domain mutation; the reserved-
actor roster is published once, in the
[Actor Authority Guard](../control-and-policy/control-plane.md#actor-authority-guard).

Idempotency-key identity:

| Rule | Behavior |
| --- | --- |
| Key binding | A key binds the normalized request/job kind and the complete request envelope. |
| Exact retry | The same kind and envelope returns the existing request. |
| Key reuse | Rejected when any of kind, operation, arguments, references, output intent, target, preconditions, causal references, actor, provenance, or schedule differs — including concurrent submissions. |
| Identity comparison | Canonical JSON: object key order does not matter, Python tuple and list inputs normalize to the same JSON array, and JSON booleans remain distinct from numbers. |

Lifecycle transitions:

| Transition | Rule |
| --- | --- |
| Answer / amend | Creates one unscheduled PI successor with a fresh key, binding the source in provenance and causal references without altering the source envelope. An exact successor replay coalesces; a fork conflicts. |
| Cancel | Accepts only pending work. |
| Retry | Accepts failed or explicitly cancelled, non-superseded work. |
| Resume | Accepts only pending work. |
| Claim vs. supersession | Competing atomic state transitions; at most one wins. |
| Interrupted lifecycle append | An exact repeat repairs the one missing event; it does not duplicate a successor or reopen work. |

## Content neutralization boundary

Code-owned Markdown insertions neutralize model- and provider-derived prose
before apply:

| Construct | Neutralization |
| --- | --- |
| Markdown images and Obsidian embeds | Made inert. |
| Raw HTML | Escaped. |
| External URLs | Become code spans. |
| Vault wikilinks; ordinary literal code spans; top-level fences | Unchanged. |
| Container-nested code | Handled conservatively. |
| Pandoc attribute lists, including raw-format attributes | Made literal. |
| Top-level fence attributes | Stripped. |
| Ambiguous container-nested fence headers | Made literal. |
| Malformed or unclosed code candidates | Treated as prose. |

This applies to prompt reports, digest and hub suggestions, note candidates,
generated outlines and drafts, promoted draft passages, provider attention
prompts, worklists, and extracted-edge prompts.

`stage_concept` and the shared Inbox writers remain byte-preserving
mixed-author seams. They cannot infer which substring a human authored. Their
code-owned callers neutralize fields whose provenance is known. Structural IDs
and paths remain unchanged state; display prose derived from them is inert or
rendered as code.

## Change witness

`observe-pi-edits` seeds and reconciles baselines from file-byte snapshots for
eligible bundle Concepts under the configured bundle roots.

| Observation | Result |
| --- | --- |
| Direct PI edit | Gets a baseline only after its observed snapshot survives staging and commit; a later edit remains dirty for the next sweep. |
| Later mismatch with no matching journaled current hash | Returns a `route: ask` `foreign-edit` finding. |
| Tracked restriction key removed — a `superseded` or `local-only` frontmatter boolean recorded `true` in the baseline | Returns `restriction-key-removed`. |
| Journal-backed current hash | Reconciles the baseline. |
| Generic writer commit with no journal record for the disk edit | Does not bless the edit. |

These structured operation findings do not block the file or create an
attention projection. `local-only: true` is recognized only as a
change-detection key in this release. It does not enforce privacy, retrieval,
export, or egress policy.

## Capture pipeline (`memoria_vault.runtime.capture`)

| Action | Performer | What it does |
| --- | --- | --- |
| Capture source | worker operation `capture-source` + runtime helpers (`capture_source`, `stage_catalog_source`) | Records a capture run, writes catalog state plus durable source blobs, and keeps DOI/portable imports unchecked until enrichment or worker checks pass ([Ingest routing](../pipelines-and-io/ingest.md)). |
| Enrich staged source | worker operation `enrich-source` + runtime helper (`enrich_source`) | Resolves required DOI providers, records provenance, blocks failed or contested records with attention, neutralizes provider prose in generated attention/candidate Markdown, then checks passing rows and refreshes `bibliography.bib`. |
| Capture BibTeX source | worker operation `capture-bibtex-source` + runtime helper (`bibtex_capture_payload`) | Parses one BibTeX entry into unchecked catalog metadata, a raw `.bib` blob, and a DOI enrichment request when a DOI is present. |
| Capture CSL source | `memoria work import --format csl` + runtime helper (`csl_capture_payload`) | Parses each CSL-JSON item into unchecked catalog metadata and a raw `.csl.json` blob; `--enrich` also queues a DOI enrichment request for each newly admitted item when a DOI is present. |
| Update Work | worker operation `update-work` | Applies PI-owned Work metadata, standing, and classification changes to the SQLite catalog row, then records the journal event through the worker request queue. |
| Capture URL source | worker operation `capture-url-source` + runtime helper (`stage_url_source`) | Fetches one URL, preserves raw HTML, extracts plain text with stdlib `HTMLParser`, and writes an unchecked catalog row plus source-content blobs. |
| Capture PDF source | worker operation `capture-pdf-source` + runtime helper (`stage_pdf_source`) | Uses the optional PyMuPDF parser to extract page text from raw PDF bytes, rejecting more than 1,000 pages or 8 MiB of extracted UTF-8 text before it writes an unchecked catalog row plus source-content blobs. |
| Capture remote PDF source | PI-only worker operation `capture-remote-pdf-source` + `resolve_fetch` / `stage_pdf_source` | Validates an imported fetch descriptor and metadata separately, authorizes every resolver URL against the seven-prefix PMC/Frontiers/ACL/Sociologica/arXiv policy, then stages the resolved PDF. It accepts no caller-supplied PDF bytes and is not a new CLI command. |
| Regenerate bibliography | runtime capture helper (`write_references_bib`) / worker operation `regenerate-references-bib` | Rebuilds `bibliography.bib` from checked SQLite catalog rows and can commit the projection plus journal event through the worker. |
| Capture trace | trusted writer + journal | Records `run`, `derived`, and `check-fired` events for the catalog Work row; raw blobs stay gitignored and are referenced by path + hash. |
| Extract typed edge candidates | trusted writer materialization (`commit_writer_changes`) | Parses explicit argument-class body links such as `[[supports::notes/x.md]]` into unchecked `edge-candidate` attention prompts in the same commit, neutralizing copied title/target prose; bare `[[wikilink]]` body links create no typed edge candidate at all. |
| Create Concept | engine API (`write_new_concept`) + worker operation `create-concept` | Queues PI or CLI-agent `note`/`hub`/`project` creation through the request envelope, validates and commits the Concept through the trusted writer, and leaves it `unchecked` until a later `check` operation passes. |
| Foreign-write quarantine | worker operation `trace-integrity-scan` + trusted writer (`quarantine_untraced_from_status` / `quarantine_untraced`) | Scans git-status or explicit bundle paths, moves untraced bundle files into `.memoria/quarantine/`, and records a failed `trace-integrity` check event. |

## Operation runner (`memoria_vault.runtime.operations`)

| Action | Performer | What it does |
| --- | --- | --- |
| Load operation policy | runtime operation helper (`load_operation_policy`) | Loads a package-owned operation manifest and requires the operation-manifest policy contract: tools, paths, network, `runner.test` plus `runner.live` provider/model branches, prompt version, `io_schema.input`/`io_schema.output`, risk class, checks, and sealed `untrusted_fields` where raw text enters model prompts. |
| Select model pins | `memoria eval select-models` | Runs the seeded-error bar for manifest-declared `runner.test`/`runner.live` pins in a disposable fixture, emits a selection record, and refuses to select a runner whose bar fails. |
| Record empirical event | worker operation `empirical-event-record` + runtime helper (`record_empirical_event`) | Validates one strict [`empirical_event.v1`](../control-and-policy/empirical-events.md) payload, requires `idempotency_key=empirical-event:<event_id>`, rejects raw text/path-like fields, and stores one analytics-only `telemetry_events` row, returning its `telemetry_id`. Nothing is appended to the journal and no commit is made. |
| Record Co-PI interview | worker operation `record-copi-interview` + runtime helper (`record_copi_interview_turn`) | Records a PI interview takeaway for a checked Work as a committed `copi-interview` journal event; digest compile can consume it as traced context. |
| Compile source digest | worker operation `compile-source-digest` + runtime helper (`compile_source_digest`) | Builds a checked digest from one checked Work using the manifest-pinned runner, records the raw model-output hash, neutralizes source/model/topic prose before apply, embeds citation-survival payloads, and writes the machine Candidates block on existing hubs (wholesale replace; the curated body above the block is never touched). |
| Digest related works | worker operation `digest-related-works` + runtime helper (`digest_related_works`) | Deterministically ranks co-cited catalog Works (shared `references` targets in `work_graph_edges`) against one hub's works and replaces the hub's terminal machine Candidates block wholesale; the curated body above the block is never touched. |
| Regenerate tracked projections | runtime projection helper (`write_tracked_projections`) / worker operation `regenerate-tracked-projections` | Rebuilds `index.md`, `bibliography.bib`, `AGENTS.md`, and owned `projects/<project>/argument.canvas` files in one worker-owned projection run. An orphan Canvas has no project owner, so scan quarantines it without regeneration. |
| Regenerate workspace indexes | runtime projection helper (`write_workspace_indexes`) / worker operation `regenerate-indexes` | Rebuilds the root and bundle `index.md` projections from checked Concept files. |
| Regenerate capability index | runtime capability helper (`write_capability_index`) / worker operation `regenerate-capability-index` | Rebuilds ignored `.memoria/index/capability-index.json` from packaged capability manifests and records product SHA-256 trust hashes. |
| Apply decision-rule notices | PI-only worker operation `apply-decision-rule-notices` + runtime helper (`apply_decision_rule_notices`) | Recomputes the dashboard panels and the decision-rule assessment from the workspace, then records each crossing as one deduped `notice` card and one `armed`-to-`fired` flip in `.memoria/config/decision-rules.yaml`. The only path that applies a rule; assembling the dashboard never does. A paused `decision-rules` producer suppresses the card but never the status flip. |

## Search input and query (`memoria_vault.runtime.search_index`)

| Action | Performer | What it does |
| --- | --- | --- |
| Rebuild checked search source | worker operation `rebuild-checked-search-index` + runtime helper (`rebuild_checked_search_index`) | Rebuilds `.memoria/index/search/checked/` from checked retrieval documents: current Concepts plus generated checked Work text and graph neighborhoods. |
| Answer query | worker operation `answer-query` + runtime helper (`answer_query`) | Returns the deterministic BM25 Ask/Query contract over checked retrieval documents: sources, unknowns, staleness, contradictions, and project context when supplied. |

## Knowledge construction (`memoria_vault.runtime.knowledge`)

| Action | Performer | What it does |
| --- | --- | --- |
| Emit note candidates | worker operation `propose-note-candidates` + runtime helper (`emit_note_candidates`) | Reads one checked digest, records resolved runner provenance in `model_call`, neutralizes model-derived prose fields before apply, promotes checked `note` Concepts, and records note-candidate state in SQLite's authoritative event log rather than frontmatter. |
| Curate note candidate | worker operation `curate-note-candidate` + runtime helper (`curate_note_candidate`) | Records a PI accept/reject decision for one checked candidate `note` as a journal `resolved` row without mutating Concept frontmatter, and the matching [`disposition` row](../control-and-policy/empirical-events.md#disposition-call-sites). |
| Curate note link | worker operation `curate-note-link` + runtime helper (`curate_note_link`) | Records one PI-authored link — `supports`, `contradicts`, `extends`, `warrant`, `qualifier`, `rebuttal` — from a checked note to a checked Concept, updating the note's `links` map and committing it with a journal `resolved` row. An optional `proposal_ref` payload field names the machine-proposed edge the link adopts, which is what [gates its `disposition` row](../control-and-policy/empirical-events.md#disposition-call-sites). |
| Move concept | worker operation `move-concept` + runtime helper (`move_concept`) | Renames a note, hub, or project file, rewriting inbound `links:` entries and the concept's DB `path` attribute in one trusted-writer commit; identity is the frontmatter `id`, so verdicts and edges stay attached. A refused move restores the files, the DB row, and git, then appends a `move-reverted` event naming the old path, the new path, and the linkers it rolled back — the append-only journal cannot drop the rows the attempt already wrote, so it retracts them instead; the refusal text itself stays out of that row and reaches the PI through the raised error and the request's `error` field. |
| Analyze gaps | worker operation `analyze-gaps` + runtime helper (`analyze_gaps`) | Reports topic, digest, grounds, and project argument gaps from checked state; provider candidates and tag candidates surface as unchecked attention, never direct writes. |
| Analyze project argument | worker operation `analyze-project-argument` + runtime helper (`analyze_project_argument`) | Follows checked, non-candidate note links around a checked project's `thesis` note and returns relation counts, stage, saturation, gap/advisory taxonomy, nodes, and edges. |
| Render project argument Canvas | worker operation `render-project-argument-canvas` + runtime helper (`write_project_argument_canvas`) | Renders the checked-note argument graph for one project as a generated `projects/<project>/argument.canvas` projection and commits it with a journal row. |
| Fork project Canvas | worker operation `fork-project-canvas` + runtime helper (`fork_project_canvas`) | Copies a rendered `argument.canvas` to an editable `projects/<project>/scratch-<name>.canvas` with the generated banner stripped. The scratch canvas is not a tracked projection and is never regenerated, so the PI's hand edits are never overwritten; `project.canvas.forks` diffs it against the live render and hand-drawn edges graduate through `curate-note-link`. |
| Run prompt operation | worker operation `<pattern-id>` + runtime helper (`run_prompt_operation`) | Reads checked input refs for package-owned prompt-operation manifests such as `analyze-claims`, records request/journal provenance and the raw model-output hash, neutralizes the rendered model output, and stages one unchecked report note under `.memoria/staging/notes/`. |

## Integrity loop (`memoria_vault.runtime.grounding`)

| Action | Performer | What it does |
| --- | --- | --- |
| Check evidence integrity | runtime integrity helper (`check_evidence_integrity`) | Scans checked `digest` and `note` Concepts and flags unresolved `work_id`, legacy evidence-set, or body evidence-marker references. |
| Check source metadata | runtime integrity helper (`check_source_metadata`) | Flags missing catalog basics, conflicting DOI metadata, exact duplicate source IDs, deterministic duplicate Work candidates, and duplicate person/entity identifiers for PI review. |
| Check quote anchors | runtime integrity helper (`check_quote_anchor_support`) | Flags checked notes whose quoted span is absent from checked Work text declared by `work_id` or evidence markers. |
| Record integrity check | runtime integrity helper (`record_integrity_check`) | Appends a `check-fired` event with shadow-first `drop` routing by default; active failures route `ask`, and explicit auto-revert checks route `act`. |
| Check claim quote support | runtime integrity helper (`check_claim_quote_support`) | Flags checked notes whose claim and cited quote share no substantive terms; this is a high-precision first pass for unwarranted-claim seeded errors, not a full NLI replacement. |
| Check prompt-injection markers | runtime integrity helper (`check_prompt_injection_markers`) | Flags checked Works, digest Work, or notes containing explicit prompt-injection marker text; this is a high-precision marker check, not semantic injection detection. |
| Check provenance checkpoint | runtime integrity helper (`check_provenance_checkpoint`) | Flags checked notes or digest Work that depend on checked catalog Works whose provider coverage is still partial or degraded; this routes fresh uncorroborated source use to PI attention without claiming semantic detection. |
| Check citation survival | runtime integrity helper (`check_citation_survival`) | Flags a missing or stale generated `bibliography.bib` projection for checked catalog sources; this is the vault-level bibliography staleness check, not a per-Concept citation-payload scan. |
| Surface tensions | worker operation `surface-tensions` + runtime helper (`surface_tensions`) | Runs the Tier-1 HANS-gated contradiction pass and the Tier-2 judge for Tier-1 abstain/degraded hard cases; Tier-2 must quote both checked texts or abstain, and no `contradicts` link is written. |
| Check contradiction links | runtime integrity helper (`check_contradiction_links`) | Flags checked digests whose explicit `links.contradicts` targets are missing, unchecked, or stale; this is structural link integrity, not semantic contradiction discovery. |
| Check link targets | runtime integrity helper (`check_link_targets`) | Flags checked Concepts whose explicit path-like `links` targets are missing, unchecked, or stale; this is structural link-target integrity, not semantic false-link detection. |
| Trace downstream | runtime integrity helper (`trace_downstream`) | Rebuilds the downstream graph from journal `derived.inputs` without reading unchecked Concepts. |
| Cascade rollback | runtime integrity helper (`cascade_rollback`) | Moves machine-derived downstream Concepts to `.memoria/quarantine/`, appends `resolved` plus inverse `derived` events, and leaves PI-derived downstream Concepts live while flagging them with route `ask`. |
| Run seeded-error verdict | worker operation `run-seeded-error-verdict` + runtime helper (`run_seeded_error_verdict`) | Runs the seeded structural fixture in a disposable workspace and returns the verdict metrics, probe review batch, and live-only license flag. |

## Linter (`memoria_vault.runtime.sweeps.linter`)

The registered detectors (slugs, severities, and what each catches) live in [Linter: detectors and auto-fix](../analysis-and-surfaces/linter.md#the-detectors); every detector is report-only.

| Action | Performer | What it does |
| --- | --- | --- |
| Run detectors | Linter (`detectors.py`, manual or scheduled run) | Runs all registered structural detectors over the vault; severity-ranked findings return in command output. The linter does not write attention; separately invoked integrity operations may do so. |
| Pre-commit hook | Linter (`precommit_check.py`, git hook) | Schema-validates staged notes and blocks the commit on a violation - the one check that prevents rather than reports. |
| Session digests | Linter (`session_summary.py`, manual or scheduled run) | Writes one deterministic per-session digest file under `system/logs/sessions/` from the audit log ([the quarantine-and-verify with durable, audit-logged crash recovery decision](https://github.com/eranroseman/memoria-vault/blob/main/design-history/arcs.md)). |
| Hub proposal handoff | Linter (`hub_handoff.py`, PI-run) | Converts current `hub-threshold` findings into idempotent local handoff payloads for map work; `hubs/` stays PI-curated. |

## Sweeps and scheduled operations

| Action | Performer | What it does |
| --- | --- | --- |
| Eval dispatch | telemetry operation (`eval_dispatch.py`, operator-managed scheduled task or `memoria eval run`) | Fans workspace-authored gold tasks out as one idempotent local eval task per current task ([Vault eval](../analysis-and-surfaces/vault-eval.md)). |
| Eval score | telemetry operation (`eval_score.py`, operator-managed scheduled task) | Computes recall@k / support-rate / FAMA-clean from local result blocks; appends to `system/metrics/eval/runs.jsonl`. |
| Retraction check | retraction operation (`retraction.py`) | Checks a DOI against the Retraction Watch dataset, Crossref, and Open Retractions (read-only). |
| Retraction sweep | retraction operation (`retraction.py`) | Scans the catalog's DOIs for retractions and writes an Inbox `alert` projection for each retracted Work. |
| Emit worklist | shared operation helper (`worklists.py`) | Converts a scan/search report into file-backed worklist projections and one aggregate `work-prompt` attention projection; report-derived display prose is neutralized while structural row references remain unchanged. |

## Runtime policy and helper modules

| Action | Performer | What it does |
| --- | --- | --- |
| Policy decision | [Policy gate](../control-and-policy/policy-mcp.md) (`memoria_vault.runtime.policy`) | Decides allow / allow_with_log / deny / dry_run for optional adapter writes and runtime checks; fail-closed. |
| Pre-tool gate | runtime policy hook (`memoria_vault.runtime.policy.hook`) | Optional adapters call it before a tool runs; denied, dry-run, direct-file, terminal, browser, and unaudited egress tools are blocked. |
| Post-tool pairing | runtime policy hook (`memoria_vault.runtime.policy.hook`) | Computes the `after_hash` and appends the paired reversibility record to `system/logs/audit.jsonl`. |
| Build graph neighborhoods | runtime search/knowledge helpers | Builds checked retrieval documents and first-order graph-neighborhood text for BM25 ask and gap analysis. |
| Render argument canvas | worker operation `render-project-argument-canvas` | Renders the project argument map as a JSON Canvas artifact from checked project graph state. |
| Run prompt operations | `memoria operation run` / `engine_api.run_operation` | Runs package-owned prompt operations through the same request, runner, staging, and journal boundary as other worker operations. |
| Loudness routing and blockers | shared operation helper (`memoria_vault.runtime.attention.loudness`) | Interprets loudness metadata on pull-only Inbox attention projections and exposes open block attention items to delegation and policy gates. |
