---
title: System actions
parent: Reference
---

# System actions

Every action the system can perform, with its performer. Three performer kinds: **deterministic engines** (zero-LLM Python, report-only or idempotent), **agents** (LLM lanes acting through gated MCP tools and skills), and the **PI** (palette actions and review decisions). Where a topic has its own reference page, that page is authoritative for the details — this catalog is the map.

## Deterministic engines

### Ingest pipeline (`engines/ingest/`)

| Action | Performer | What it does |
| --- | --- | --- |
| Tier-0 capture | ingest engine (`ingest_paper.py`) | Extracts citekey identity and frontmatter from local BibTeX — no network. |
| Tier-0 routing | ingest engine (`ingest_paper.py`) | Routes the entry type (article / book / software / dataset) to its catalog home and note type ([Ingest routing](ingest.md)). |
| Resolve | ingest engine (`resolve_merge.py`) | Queries Semantic Scholar, OpenAlex, and Crossref to resolve identity, authors, citations, and enrichment metadata. |
| Merge | ingest engine (`resolve_merge.py`) | Merges per-field best-source-wins across the three sources with provenance, and scores identity disagreement. |
| Classify | ingest engine (`classify.py`) | Proposes `research_area` / `methodology` from OpenAlex topics, with a confidence floor and near-tie flagging; audited to `system/logs/classify.jsonl`. |
| Project-hints proposal | ingest engine (`classify.py`) | Scores topic overlap against `.memoria/project-hints.yaml` and proposes `projects` membership for human confirmation (ADR-15). |
| Extract | ingest engine (`extract.py`) | Pulls full text — PMC JATS first, then the local PDF via sandboxed pymupdf4llm — behind a deterministic coherence gate; marks `degraded` otherwise. |
| Link entities | ingest engine (`link.py`) | Plans idempotent find-or-create venue / person / organization entities from merged metadata. |
| Link citations | ingest engine (`link.py`) | Plans cited-by / cites edges by matching the reference union against the vault by DOI / arXiv id. |

### Linter (`engines/linter/`)

The detector table with severities lives in [Linter: detectors and auto-fix](linter.md); every detector is report-only. The sixteen registered detectors: orphan-working-files, stale-fleeting, stale-answer-drafts, extract-path-broken, frontmatter-schema-check, frontmatter-link-check, broken-wikilink, dashboard-field-drift, graph-analyze, fama-exposure, misplaced-note, audit-unpaired-writes, vault-hash-drift, audit-log-size, hub-threshold, skeleton-drift.

| Action | Performer | What it does |
| --- | --- | --- |
| Run detectors | Linter (`detectors.py`, daily cron) | Runs all sixteen structural detectors over the vault; findings surface on the drift dashboards. |
| Pre-commit gate | Linter (`precommit_check.py`, git hook) | Schema-validates staged notes and blocks the commit on a violation — the one gate that prevents rather than reports. |
| Golden stage | Linter (`golden.py stage`) | Snapshots every system file (templates, dashboards, patterns, eval set, scripts, shipped Obsidian config) into a SHA-256 manifest. |
| Golden check | Linter (`golden.py check`, daily cron) | Reports system files that drifted from or went missing against the golden manifest. |
| Golden restore | Linter (`golden.py restore`) | Lists what restoring would change; writes the golden bytes back only with `--apply` (a PI decision). |
| Session digests | Linter (`session_summary.py`, daily cron) | Writes one deterministic per-session digest file under `system/logs/sessions/` from the audit log (ADR-25). |

### Sweeps (`engines/sweeps/`)

| Action | Performer | What it does |
| --- | --- | --- |
| Reconcile | sweeps engine (`reconcile.py`) | Finds capture-intake anchors with no note on disk and enqueues idempotent re-ingest cards. |
| Retry tier-0 | sweeps engine (`reconcile.py`) | Finds notes stuck at `ingest_status: tier0` and enqueues idempotent re-ingest cards. |
| Stamp chats | sweeps engine (`reconcile.py`) | Prepends fleeting frontmatter to bare ACP chat exports in `notes/fleeting/chats/`. |
| Archive inbox | sweeps engine (`archive_inbox.py`) | Flips resolved inbox cards (`resolved:` stamp older than `inbox.archive_after_days`, default 30) to `lifecycle: archived` so the inbox converges to empty. |
| Eval dispatch | sweeps engine (`eval_dispatch.py`, quarterly cron) | Fans the gold set out as one idempotent kanban card per task, routed to the owning lane ([Vault eval](vault-eval.md)). |
| Eval score | sweeps engine (`eval_score.py`, quarterly cron) | Computes recall@k / support-rate / FAMA-clean from the result blocks reported on eval cards; appends to `system/metrics/eval/runs.jsonl`. |
| Retraction check | sweeps engine (`retraction.py`) | Checks a DOI against the Retraction Watch dataset, Crossref, and Open Retractions (read-only). |
| Retraction sweep | sweeps engine (`retraction.py`) | Scans the catalog's DOIs for retractions and hands findings to the agent to flag. |

## Vault-side MCP servers and hooks (`.memoria/mcp/`)

| Action | Performer | What it does |
| --- | --- | --- |
| Policy decision | [Policy MCP](policy-mcp.md) (`policy_mcp.py`) | Decides allow / allow_with_log / deny / dry_run for every vault action against the lane's ceiling; fail-closed. |
| Pre-tool gate | policy hook (`policy_hook.py`) | Blocks denied or gated writes before the tool runs and stashes the file's `before_hash`. |
| Post-tool pairing | policy hook (`policy_hook.py`) | Computes the `after_hash` and appends the paired reversibility record to `system/logs/audit.jsonl`. |
| Run ingest pipeline | ingest MCP (`ingest_mcp.py`), Librarian-facing | Runs the full deterministic Tier-0/1 ingest for a citekey and returns the draft bundle with its two LLM holes (classification + brief). |
| Persist extract | ingest MCP (`ingest_mcp.py`) | Stores the full-text extract under `.memoria/data/extracts/`, outside the agent write lane. |
| Append intake anchor | ingest MCP (`ingest_mcp.py`) | Appends the durability anchor to `system/logs/capture-intake.jsonl` that the reconcile sweep recovers from. |
| Build cluster graph | cluster MCP (`cluster_mcp.py`), Librarian-facing | Builds the typed knowledge graph from authored links and computes communities and centrality. |
| Emit canvas | cluster MCP (`cluster_mcp.py`) | Renders the claim-debate map as a JSON Canvas with maturity-colored nodes and typed edges. |
| Model topics | cluster MCP (`cluster_mcp.py`) | Runs BERTopic over the corpus to extract topics, the doc-topic map, and outliers. |
| List / run patterns | patterns MCP (`patterns_mcp.py`) | Lists runnable patterns from `system/patterns/` and composes a pattern run (refusing gated-zone output targets), logging provenance. |
| Route task | tasks MCP (`tasks_mcp.py`), co-PI-facing | Validates a delegation against the target lane's ceiling and creates the kanban card. |
| Board export | board export (`board_export.py`, 60 s cron) | Projects kanban cards into `system/board/` and appends the telemetry logs (board state, transitions, dispositions, cost). |
| Metrics aggregate | metrics aggregator (`metrics_aggregate.py`, weekly cron) | Rolls audit + board + lint signals into per-lane trust-score notes under `system/metrics/`. |

## External MCP servers (declared per profile)

| Action | Performer | What it does |
| --- | --- | --- |
| Vault read / gated write | obsidian native MCP (all lanes) | File reads, search, and writes into the vault over the Local REST API plugin's MCP — every write passing the policy gate. |
| Vault search | qmd MCP (Librarian, Writer, co-PI, Peer-reviewer) | Hybrid BM25 + vector + rerank search over the vault corpus, local and read-only. |
| Literature discovery | paper_search MCP (Librarian) | Searches arXiv, PubMed, Semantic Scholar, Google Scholar, and bioRxiv (Unpaywall email for OA lookups). |
| Zotero reads | pyzotero MCP (Librarian, Peer-reviewer) | Read-only citekey resolution, metadata, and citation context from the local Zotero library — no write-back. |

## Scheduled crons (`.memoria/scripts/`)

| Cadence | Script | What it runs |
| --- | --- | --- |
| Every 60 s | `board-export-cron.sh` | Board export + telemetry append. |
| Every 15 min | `sweeps-cron.sh` | Reconcile, retry, stamp-chats, and inbox-archival sweeps. |
| Daily 06:00 | `lint-cron.sh` | Detectors, golden check, session digests. |
| Weekly | `metrics-cron.sh` | Per-lane metrics aggregation. |
| Weekly | `refresh-retraction-watch.sh` | Refreshes the Retraction Watch CSV under `.memoria/data/`. |
| Quarterly | `eval-cron.sh` | Scores the previous quarter's eval run, then dispatches the new one. |

## Agent skills (per lane)

### Librarian (12)

| Skill | What it does |
| --- | --- |
| catalog-find-source | Searches the literature via paper_search, screens against the vault, raises honesty-bodied candidate cards. |
| catalog-rank-candidate | Ranks candidate sources by relevance / novelty / venue into a worklist card. |
| catalog-classify-source | Proposes `research_area` / `methodology` from the vocabulary for human promotion at triage. |
| catalog-enrich-record | Runs the ingest pipeline MCP, fills the classification and `[!brief]` holes, applies the gated writes. |
| extract-flag-distill | Flags kept sources worth reading and raises a distill work-prompt. |
| extract-stub-claim | Proposes one-sentence, citekey-bound claim stubs in a source's "Worth distilling" section. |
| link-suggest-claim | Proposes typed links (supports / contradicts / extends) as one candidate card with quoted evidence. |
| link-surface-tension | Surfaces claim-pair contradictions with both sides quoted and reconciliation options. |
| map-cluster-corpus | Clusters topics via the cluster MCP and emits a map note plus a report card. |
| map-report-coverage | Topic-models the corpus and composes a gap report of thin topics. |
| map-scope-project | Corpus-maps a project into a narrative map with thin spots named. |
| map-seed-canvas | Seeds a JSON Canvas from the cluster graph (communities, edges, layout). |

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
| verify-card-gap | Converts missing-evidence findings into gap cards in `inbox/`. |
| verify-propose-fix | Proposes the obvious remedy for a finding as a candidate card — flag, don't fix. |

### Co-PI (5)

| Skill | What it does |
| --- | --- |
| ask-question-source | Answers questions about a source from vault holdings, read-only. |
| ask-read-lens | Re-reads a source through a named lens (frame / checklist / hypothesis), read-only. |
| explore-branch-framings | Branches a question into rival framings — the sparring partner. |
| delegate-route-task | Routes work to the right lane via the tasks MCP with a composed handoff payload. |
| explain-the-system | Teaches how Memoria works, pointing at concrete affordances. |

## PI actions

### Palette (QuickAdd scripts, `system/scripts/`)

| Action | What it does |
| --- | --- |
| Capture from Zotero | Reads the current Zotero selection (CAYW), writes the intake anchor, creates an `intake:source` card. |
| Capture source from URL | Prompts for a URL and creates an `intake:source` card on the Librarian lane. |
| Catalog a source | Prompts for a citekey / URL and creates a catalog-lane card. |
| Extract claims | Sends the active (or chosen) source to the extract lane. |
| Link a claim | Sends the active (or chosen) claim to the link lane. |
| Map the corpus | Prompts for an optional scope and creates a map-lane card. |
| Draft a section | Prompts for a goal and creates a draft-lane card. |
| Verify a draft | Sends the active (or chosen) draft to the verify lane. |
| Delegate a task | Prompts for a lane and goal — the palette twin of the co-PI's routing skill. |
| Run a pattern | Suggester over runnable patterns; creates the card that invokes the patterns MCP. |
| Resolve inbox card | Flips the active inbox card's `lifecycle` to the chosen verdict and stamps `resolved:`. |

### Review decisions

| Action | What it does |
| --- | --- |
| Review-gated approval | Every write to `notes/claims/` and `notes/hubs/` is a proposal until the PI approves it — the agents cannot land it alone. |
| Inbox triage | Accept / edit / reject candidate and flag cards; dispositions are logged for the trust metrics. |
| Golden restore `--apply` | The PI (not the cron) decides to write golden bytes back over drifted system files. |
