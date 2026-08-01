## alpha.22 - Substrate identity, the evidence-set contract, and cost telemetry

**Theme:** alpha.22 lays the substrate a real corpus stands on. alpha.21 made
the delivered machinery *true*; alpha.22 makes it *keyed* — bringing the dead
`concept_edges` join point to life, implementing the full evidence-set/grounds
contract so grounding is derived rather than asserted, and instrumenting what
each model call actually costs. It is a schema-and-contract checkpoint: none of
it is user-visible feature work, and all of it must land before bulk import,
because every reshape here is expensive to unwind once a vault holds real
sources.

### 1. G2S1 · the graph substrate becomes live (schema v13-v15)

- **What:** `concept_edges` stopped being a dead join point. The table gained
  `edge_id` and `attributes_json`, a unique index on `edge_id`, and reverse
  traversal indexes (`idx_concept_edges_target`, `idx_work_graph_edges_target`);
  `state.concept_edge_id(source, relation, target)` became the canonical digest,
  and the indexer began filling and persisting edges across reindex.
  **Why:** every later graph package — traversal, propagation, consequence
  routing — reads this join. Leaving it inert meant the argument graph existed
  in the schema and nowhere else.

- **Fresh-install ruling (binding).** There are no existing Memoria
  installations to upgrade, so the plan's numbered-migration machinery was
  **retired rather than executed**: no `MIGRATIONS` registry, no version-to-
  version fixtures, no compatibility writers. `state._init` creates a version-0
  database from the current `schema.sql` and fails closed on any other nonzero
  `user_version` *before* mutating anything. Each schema task edits the current
  DDL, its trailing `PRAGMA user_version`, `SCHEMA_VERSION`, and the fresh-schema
  assertions in one commit. A version bump declares incompatibility; it does not
  authorize an upgrade path.

### 2. S12/S35/S68 · the #1293 evidence-set and grounds contract

- **What (rename sweep, S12):** the Toulmin role `warrant` became `grounds`
  wherever it named *evidence supporting a claim* — including
  `code_artifacts.purpose`'s CHECK constraint and default. The genuine Toulmin
  six-role uses (`unstated-warrant`, the NLI-judge field, "Warrant lost"
  consequences) were deliberately left alone; the manifest's DO-NOT-TOUCH audit
  is what separates the two.

- **What (unified derivation, S35):** evidence-set membership became derived
  through one R1-R4 path with transitive completeness and fail-closed cycles,
  retiring `_derived_evidence_type`, `_draft_evidence_type`,
  `_evidence_items_resolve` and `_disposed_evidence_ids`.
  `state.evidence_item_closure` exposes (item, path) pairs for non-set items
  reachable through nested sets — cycle-safe, unknown refs yield nothing.

- **What (journal-backed bindings, S68):** first binding now journals an
  `evidence-minted` event, and `state.rebuild_evidence_bindings_from_journal`
  makes the bindings ledger reconstructible by replaying authoritative events
  rather than trusting a cached table.
  **Why:** a bindings table that cannot be rebuilt from the journal is a second
  source of truth, and the whole trust argument rests on there being one.

### 3. COST · model-call usage and cost telemetry

- **What:** `_pydantic_ai_chat` stopped returning a bare `str` and now returns
  the canonical `{text, usage, cost_usd, elapsed_s}`, threaded through
  `_run_prompt_model`, `_run_digest_model` and their three callers. The three
  `model_call` journal literals carry those fields; the reference page documents
  them. `usage` is the five-field dict harvested from the SDK **exactly once**
  per call; `cost_usd` is a nullable best-effort estimate (null for unpriced
  models and always null on the deterministic-fixture path) and is **never** an
  input to the token breaker; no prompt or completion text is captured.
  **Why:** you cannot reason about what a research loop costs without measuring
  it, and retrofitting per-call cost onto a journal after a corpus exists means
  the history is unmeasured.

- No new dependency (`genai-prices` ships transitively with the pinned
  `pydantic-ai-slim`, reading a **bundled** snapshot with no network I/O) and no
  `SCHEMA_VERSION` bump — the payload change is additive and no JSON schema
  constrains `model_call` fields.

### 4. Defects found and repaired during execution

Three defects were introduced by the plan's own prescribed code and caught in
review before they shipped. They are recorded because each is a *class* of
mistake this codebase keeps making, not a one-off:

- **A double usage-harvest** that contradicted the same task's own
  `usage_calls == 1` assertion. Resolved by folding the harvest into
  `_record_token_usage`, which now charges the ledger and returns the telemetry
  from one SDK call.
- **A completed, billed model call reported as a failure with a zero ledger
  charge.** The usage-field read had slipped outside its guard, so a raising
  usage *property* escaped to the outer catch — contradicting the code's own
  retained comment, "completed calls must still be charged."
- **A `cost_usd` extraction narrow enough that a pricing hiccup could fail a
  completed operation**, against a spec that calls cost "never a breaker input."

A fourth was a test-quality defect: recalibrating the token-ceiling constants
collapsed the strictly-over-budget scenario into a duplicate of the
exact-boundary test, so a mutant refusing only on `spent == ceiling` survived
both. Mutation testing caught it; the two tests now kill mutants the other
misses.

### 5. Plan-record reconciliation

Ten tasks in the working plan read as open over work that was either already
landed or explicitly retired — 39 checkboxes across G1.1-G1.3 (retired
migration machinery), G2S1.2/.3, S12.2, S12.4, S35.2, S68.3 and S68.4. Each was
reconciled with an execution receipt citing the file:line proving the
deliverable exists, or the amendment retiring it.

The drift had one cause worth recording: **the plan cites pre-squash commit
SHAs**, which are not ancestors of `main` even when their content is. Verifying
by SHA reports landed work as missing. Verification must be by content.

### 6. Verification gate

- `python scripts/verify` is the one gate: lint, product gates, tests, offline
  smoke, syntax. `main` requires a PR plus `verify` and `gitleaks`.
- `scripts/test_vault/e2e_smoke.py` was repaired during this checkpoint: it
  resolved its disposable vault from a hardcoded `~/memoria-vault/test-vault`
  regardless of which checkout ran it, and `_reset_test_vault` wipes every child
  of that directory including the vault's own nested `.git`. Any gate run from a
  git worktree therefore wiped the main checkout's vault, and concurrent gates
  destroyed each other's — making results untrustworthy in both directions. The
  default now derives from the running checkout; `MEMORIA_TEST_ROOT` still
  overrides.

### 7. Deferred scope

- **The graph package beyond G2S1** — node identity (NID), edge-relation
  promotion (ERP), propagation and consequence routing — is alpha.23 scope and
  carries its own schema ladder.
- **Beta.1 blockers** stay deferred behind their empirical or design blockers,
  unchanged from alpha.21.
- **Remote API** — remote bind, CORS, OAuth, cookies, SSE, WebSockets, and
  multi-user service behavior — remains out of scope.

### Release management

- Alpha checkpoints carry no release process: the chapter freezes when the
  checkpoint's plan reaches zero open checkboxes, which
  `2026-07-15-alpha22-substrate-trust.md` did at
  [#1577](https://github.com/eranroseman/memoria-vault/pull/1577).
- No formal tag or GitHub Release is cut; release-please remains
  `workflow_dispatch`-only.
- The alpha.22 working plan under `docs/superpowers/plans/` is retired as active
  scratch now that its accepted decisions are folded into this chapter; it
  remains tracked design evidence, not a frozen history chapter.
- One decision remains open at chapter close:
  [#1561](https://github.com/eranroseman/memoria-vault/issues/1561) — the cost-
  telemetry spec's six design decisions were marked "confirm at review" and were
  ratified by the execution directive rather than by a separate PI review.
