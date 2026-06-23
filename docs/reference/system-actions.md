---
title: System actions
parent: Reference
---

# System actions

Every action the system can perform, with its performer. Three performer kinds: **deterministic operations** (zero-LLM Python, report-only or idempotent), **agents** (LLM lanes acting through gated MCP tools and skills), and the **PI** (palette actions and review decisions). Where a topic has its own reference page, that page is authoritative for the details — this catalog is the map.

## Deterministic operations

### Ingest pipeline (`operations/processing/ingest/`)

| Action | Performer | What it does |
| --- | --- | --- |
| Tier-0 capture | ingest operation (`ingest_paper.py`) | Extracts citekey identity and frontmatter from local BibTeX — no network. |
| Tier-0 routing | ingest operation (`ingest_paper.py`) | Routes the entry type (article / book / software / dataset) to its catalog home and document type ([Ingest routing](ingest.md)). |
| Resolve | ingest operation (`resolve_merge.py`) | Queries Semantic Scholar, OpenAlex, Crossref, and PubMed/NCBI to resolve identity, authors, citations, biomedical identifiers, and enrichment metadata. |
| Merge | ingest operation (`resolve_merge.py`) | Merges per-field best-source-wins across the four sources with provenance, and scores identity disagreement. |
| Classify | ingest operation (`classify.py`) | Proposes `research_area` / `methodology` from OpenAlex topics, with a confidence floor and near-tie flagging; audited to `system/logs/classify.jsonl`. |
| Project-hints proposal | ingest operation (`classify.py`) | Scores topic overlap against `.memoria/project-hints.yaml` and proposes `projects` membership for human confirmation ([ADR-15](../adr/15-project-membership-from-topic-hint.md)). |
| Extract | ingest operation (`extract.py`) | Pulls full text — Unpaywall OA PDF first, then PMC JATS, then the local PDF via sandboxed pymupdf4llm — behind a deterministic coherence gate; marks `degraded` otherwise. |
| Link entities | ingest operation (`link.py`) | Plans idempotent find-or-create venue / person / organization entities from merged metadata. |
| Link citations | ingest operation (`link.py`) | Plans cited-by / cites edges by matching the reference union against the vault by DOI / arXiv id. |

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
| Hub proposal handoff | Linter (`hub_handoff.py`, PI-run) | Converts current `hub-threshold` findings into idempotent Librarian `map` cards that stage proposals under `notes/fleeting/maps/` and `inbox/`; `notes/hubs/` stays PI-approved. |

### Sweeps (`operations/`)

| Action | Performer | What it does |
| --- | --- | --- |
| Reconcile | sweeps operation (`reconcile.py`) | Finds capture-intake anchors with no note on disk and enqueues idempotent re-ingest cards. |
| Retry tier-0 | sweeps operation (`reconcile.py`) | Finds notes stuck at `ingest_status: tier0` and enqueues idempotent re-ingest cards. |
| Archive inbox | sweeps operation (`archive_inbox.py`) | Flips accepted inbox cards (`lifecycle: current` with a `resolved:` stamp older than `inbox.archive_after_days`, default 30) to `lifecycle: archived` so the inbox converges to empty. |
| Eval dispatch | sweeps operation (`eval_dispatch.py`, quarterly cron) | Fans the gold set out as one idempotent kanban card per task, routed to the owning lane ([Vault eval](vault-eval.md)). |
| Eval score | sweeps operation (`eval_score.py`, quarterly cron) | Computes recall@k / support-rate / FAMA-clean from the result blocks reported on eval cards; appends to `system/metrics/eval/runs.jsonl`. |
| Retraction check | sweeps operation (`retraction.py`) | Checks a DOI against the Retraction Watch dataset, Crossref, and Open Retractions (read-only). |
| Retraction sweep | sweeps operation (`retraction.py`) | Scans the catalog's DOIs for retractions and hands findings to the agent to flag. |
| Emit worklist | shared operation helper (`worklists.py`) | Converts a scan/search report into file-backed `worklist-item` rows and one aggregate Inbox `work-prompt`. |

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
| Route task | tasks MCP (`tasks_mcp.py`), Co-PI-facing | Validates a delegation against the target lane's ceiling, refuses dispatch while an open `loudness: block` card exists, and creates the kanban card. |
| Loudness routing | shared operation helper (`operations/lib/loudness.py`) | Sends/logs alert/block push attempts, keeps quiet/notice pull-only, and exposes open block cards to delegation and policy gates. |
| Board export | board export (`board_export.py`, 60 s cron) | Projects kanban cards into `system/board/` and appends board-state, transition, cost, and blind-review telemetry; review disposition is emitted by QuickAdd when the human resolves a work prompt. |
| Metrics aggregate | metrics aggregator (`metrics_aggregate.py`, weekly cron) | Rolls audit + board + lint signals into per-lane trust-score notes under `system/metrics/`. |

## External MCP servers (declared per profile)

| Action | Performer | What it does |
| --- | --- | --- |
| Vault read / gated write | obsidian native MCP (all lanes) | File reads, search, and writes into the vault over the Local REST API plugin's MCP — every write passing the policy gate. |
| Vault search | filtered qmd MCP (Librarian, Writer, Co-PI, Peer-reviewer) | Hybrid BM25 + vector + rerank search over the vault corpus, local and read-only; superseded claim notes are hidden unless historical lookup is explicit. |
| Literature discovery | paper_search MCP (Librarian) | Searches arXiv, PubMed, Semantic Scholar, Google Scholar, and bioRxiv (Unpaywall email for OA lookups). |
| Zotero reads | pyzotero MCP (Librarian, Peer-reviewer) | Read-only citekey resolution, metadata, and citation context from the local Zotero library — no write-back. |

## Scheduled crons (`.memoria/scripts/`)

The deterministic cron jobs (board export, sweeps, lint, metrics, retraction refresh, eval) and their schedules are owned by [Installer (bootstrap)](installer.md#the-crons-it-wires). They run from the repo source wrappers under `.memoria/scripts/`: the installer copies each `<job>-cron.sh` to `~/.hermes/scripts/` renamed **`memoria-<job>.sh`** — that `memoria-*` form is the cron-job name `hermes cron list` shows.

## Agent skills (per lane)

### Librarian (14)

| Skill | What it does |
| --- | --- |
| catalog-find-source | Searches the literature via paper_search, screens against the vault, raises honesty-bodied candidate cards. |
| catalog-rank-candidate | Ranks candidate sources by relevance / novelty / venue into a batch worklist. |
| catalog-classify-source | Proposes `research_area` / `methodology` from the vocabulary for human promotion at triage. |
| catalog-enrich-record | Runs the ingest pipeline MCP, fills the classification and `[!brief]` holes, applies the gated writes. |
| extract-flag-distill | Flags kept sources worth reading and raises a distill work-prompt. |
| extract-stub-claim | Proposes one-sentence, citekey-bound claim stubs in a source's "Worth distilling" section. |
| link-suggest-claim | Proposes typed links (supports / contradicts / extends) as one candidate card with quoted evidence. |
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
| verify-card-gap | Converts missing-evidence findings into gap cards in `inbox/`. |
| verify-propose-fix | Proposes the obvious remedy for a finding as a candidate card — flag, don't fix. |

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
| Capture fleeting | Creates a proposed fleeting note in `notes/fleeting/` from the bundled template. |
| Capture from Zotero | Reads the current Zotero selection (Better BibTeX JSON-RPC), writes the intake anchor, materializes a Tier-0 `catalog/papers/<citekey>.md` stub, and creates an `intake:source` card. |
| Capture source from URL | Prompts for a URL and creates an `intake:source` card on the Librarian lane. |
| Structured source capture | Opens the guided Modal Forms capture; writes a proposed `notes/sources/` note plus an Inbox candidate, with pre-file similarity reported but never blocking. |
| Write claim note | Creates a human-authored claim note in `notes/claims/` from the bundled claim template. |
| Create linked claim note | Starts from the active source note, creates a claim note with the source citekey prefilled, links it back under **Worth distilling**, and opens it for editing. |
| Catalog a source | Prompts for a citekey / URL and creates a catalog-lane card. |
| Extract claims | Sends the active (or chosen) source to the extract lane. |
| Link a claim | Sends the active (or chosen) claim to the link lane. |
| Map the corpus | Prompts for an optional scope and creates a map-lane card. |
| Record exploration trace | Captures a rejected direction/dead end beside a map or gap report under `notes/fleeting/maps/`; it stays project-local and is never canonical knowledge. |
| Draft a section | Prompts for a goal and creates a draft-lane card. |
| Verify a draft | Sends the active (or chosen) draft to the verify lane. |
| Delegate a task | Prompts for a lane and goal — the palette twin of the Co-PI's routing skill. |
| Assist commands | `assist find/search/patterns/ask/draft/explore` start the same task or conversation shape with active-note and selection context attached. |
| Run a pattern | Suggester over runnable patterns; creates the card that invokes the patterns MCP. |
| Resolve inbox card | Flips the active inbox card's `lifecycle` to a schema-valid outcome (`current` or `archived`) and stamps `resolved:`. |
| Start project | Scaffolds `projects/<slug>/`, creates the initial active thesis, and opens the project gate index for triage. |
| Refresh project gate | Rebuilds the project gate index from current thesis, links, saturation signals, and open risks. |
| Supersede thesis | Creates a replacement thesis, marks the old one superseded, updates the project `active_thesis`, and raises an Inbox alert for re-confirmation. |
| Open a space | Opens `spaces/inbox.md`, `spaces/library.md`, `spaces/knowledge.md`, or `spaces/project.md` from the left-pane navigator rail (**Now** / **Places**). |

### Review decisions

| Action | What it does |
| --- | --- |
| Review-gated approval | Every write to `notes/claims/` and `notes/hubs/` is a proposal until the PI approves it — the agents cannot land it alone. |
| Inbox triage | Accept / edit / reject candidate and flag cards; dispositions are logged for the trust metrics. |
| Golden restore `--apply` | The PI (not the cron) decides to write golden bytes back over drifted system files. |
