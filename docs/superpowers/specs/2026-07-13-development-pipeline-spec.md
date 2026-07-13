# Memoria development pipeline — governing spec

Date: 2026-07-13. Status: **governing once merged** — merging this PR is the
gate-1 (spec-approval) act for the pipeline itself. Names *what must be true*
of the path from an approved spec to the production vault; implementation
plans derive from it. It implements the pipeline half of
[0.1.0-beta.1-requirements.md](./0.1.0-beta.1-requirements.md) §4–§5 (runtime
mode/profile split, eval gating, migration drills) for a multi-agent-authored
codebase. Prior-art claims cite
[2026-07-13-pipeline-research.md](./2026-07-13-pipeline-research.md)
(verified sources). Design lineage: the 2026-07-10/13 pipeline sessions,
folded from the workflow-audit dossier (`docs/superpowers/plans/`).

## 1. Trust model

- **One human owns all judgment; the code authors are multiple, parallel,
  untrusted AI agents.** Agent output is treated as untrusted input to a
  strong deterministic pipeline (DORA 2025 framing). Documented agent failure
  modes this spec defends against: plausible-but-wrong code, reward-hacking
  visible test suites (the visible-vs-holdout pass gap grows with task
  complexity), and error compounding under rubber-stamp review.
- **Exactly two human gates.** Gate 1: spec approval (ITIL "standard change"
  pre-authorization — approve the change model once, instances flow through
  automated gates). Gate 2: pre-production go/no-go (NASA Flight Readiness
  Review — pre-declared, non-waivable checklist at the irreversible commit).
  Everything between is machine. Per-PR human code review is deliberately
  absent: at agent volume it degrades to rubber-stamping, which launders
  errors and manufactures false precedent; DORA finds end-of-pipe human
  approval uncorrelated with change-failure rate.
- **A standing observatory, not a third gate:** error analysis — reading
  transcripts, calibrating any LLM judge against human labels, monitoring
  drift — is a recurring PI activity (Husain/Shankar, Anthropic evals
  doctrine). In Memoria this *is* the empirical plan's diary/disposition
  practice; it blocks nothing and is scheduled, not gated.
- **The admission rule is actor-relative.** "Prefer rule over checker"
  assumes a rule-following author. For agent authors, rules are
  probabilistic; the deterministic checker's cost is repaid by its
  reliability. Corollary: prefer auto-fixing tools (formatters) over
  fail-and-fix, and deterministic gates over advisory ones.
- **Judgment placement:** front-loaded into specs (gate 1) and exercised on
  behavior/quality (gate 2 and the observatory). Code review is the
  exception path, entered only when spec→behavior breaks. Rulings are
  recorded with grounds, never as bare verdicts; an ungrounded ruling does
  not bind (the past is a teacher, not a prison).

## 2. Pipeline shape

```
[HUMAN gate 1: approve spec]
  → agents implement (worktree per session, explicit-path staging)
  → deterministic CI gates (verify + gitleaks; self-merge on green, squash)
  → test-vault floor (ephemeral; mechanism correctness — THE promotion gate)
  → middle ring (pre-prod: restored copy of the production vault)
[HUMAN gate 2: go/no-go — irreversibility checklist]
  → promotion (exact validated artifact; checkpointed migration)
  → production vault (permanent; live LLM; the real corpus)
  → standing observatory (empirical plan: dispositions, diary, baseline)
```

Three environments: the **ephemeral test-vault** (cattle: disposable,
reconstructible from seed), the **middle ring** (a restored copy of
production — parity + restore drill), and the **production vault** (pet:
permanent, recoverable but **not** reconstructible — it holds the researcher's
irreplaceable knowledge and, at beta.1, the ~1,200-paper corpus).

## 3. Stage requirements

### 3.1 Gate 1 — spec approval

- Work enters as a spec/plan under `docs/superpowers/`; PI approval of that
  artifact is the authorization for unattended implementation.
- Spec quality is load-bearing: vague specs push failures into the exception
  path until code review becomes routine again. Named practice: spec-driven
  agent development (GitHub Spec Kit, AWS Kiro, "specs are the new code").

### 3.2 Agent execution

- Worktree per session; stage explicit paths, never `git add -A`; squash
  merge, one feature per PR (cheap `git revert` is the first undo lever).
- Agents self-merge on green (`gh pr merge --auto --squash`) — **coupled**:
  self-merge authority exists only because the deterministic gate is strong;
  weakening the gate revokes the coupling.
- PR size/scope caps force decomposition (Intercom's risk-tiered agent-PR
  system is the precedent: refuse outsized agent PRs, keep revert ready).
- A merge queue becomes mandatory once agents land concurrently (both the
  agentic and promotion research threads; GitHub required-checks +
  merge-queue is the mechanism).

### 3.3 Deterministic CI gates (the machine seam)

Exists: `scripts/verify` (one flat roster: lint, product gates,
static|unit|contract tests, offline e2e smoke, syntax) + `gitleaks` as the
two required checks; ruleset: PR-required, squash-only, zero approvals, no
bypass actors.

Must be added (each names the failure it prevents; all are prerequisites for
trusting self-merge):

- **Python type checking** over the ~25k agent-authored lines (ramp: enable
  `ANN` ruff rules → adopt a checker in strict-where-annotated mode). Sole
  static coverage of unexercised code paths no human reads.
- **Runtime-tier tests into CI.** The LLM-free `runtime` tier (25 files of
  engine behavior) currently runs on no trigger; route it into CI. LLM-bound
  tests follow the tiering in §4.
- **JS/TS static floor**: `tsc --noEmit` + a formatter for the Obsidian
  plugin (agent-authored; currently execution-checked only).
- **Dependency lockfile** (uv or pip-tools, hash-verified): the runtime deps
  are the only unpinned supply-chain surface; tested resolution must equal
  shipped resolution. Freshness becomes a monthly reviewed upgrade PR,
  same cadence as the existing Dependabot surfaces.
- **Single Python version, single source**: `.python-version` is
  authoritative; CI derives via `python-version-file`; `requires-python`
  pins to the same minor; a verify check fail-closes on drift.
- **Fail-closed in CI**: a required tool absent on a CI runner fails the
  gate (local runs may skip with a printed notice). Silent skip at the
  authoritative gate is silent coverage loss.
- **Mutation testing (diff-scoped)** over agent-authored tests — the
  standard defense against tests that pass but assert nothing (Google
  diff-scoped mutation, Meta ACH).
- **Fresh-context adversarial agent review** as a machine gate: a reviewer
  agent with no shared context with the author (Anthropic harness pattern;
  DORA's CAB-replacement guidance). Advisory LLM findings feed the agent's
  fix loop; the LLM layer never hard-blocks (non-deterministic gates train
  everyone to ignore red).
- **Pinning doctrine**: Actions by SHA, tools by `==`, plugins by release,
  **model IDs never aliases** — an alias is a silent instrument change.

### 3.4 The test-vault floor (the promotion gate)

**The floor (minimum promotable):** from a rich seed baseline, run **every
command × every API** (CLI, HTTP, MCP, and the Obsidian plugin's client
against the real engine), and after each command assert the **expected vault
state and integrity** — catalog-driven for completeness, versioned for
upgradeability, error-seeded for detection. Clearing the floor is what
"promotable" means; its absence is what stranded the production vault.

Floor construction rules (research-adjusted):

- **Catalog-driven, pairwise-sampled.** The command/API dimension is
  enumerated exhaustively from the operation catalog (complete by
  construction — op #55 is auto-covered; git t0450 / Schemathesis
  precedent). Option/state combinations are sampled pairwise (NIST
  interaction testing) — the full cross-product is waste.
- **Invariants over goldens as the default assertion.** Prefer universal
  properties — `PRAGMA integrity_check` **plus `foreign_key_check`** (the
  former does not check FKs), files↔index reconciliation, journal appended,
  reads never modify vault bytes — over exact expected values. Invariants
  resist reward hacking (no target to special-case toward) and are SQLite's
  own model for protecting irreplaceable state.
- **Exact-state scope limit.** Byte-exact goldens only where output is
  deterministic mechanics; wherever LLM-generated content lands, assert
  properties/outcomes (schema-valid, grounded, anchored), never bytes
  (Anthropic: grade outcomes, not steps).
- **The LLM seam is pinned by record/replay.** Mechanism tests run against
  recorded cassettes: deterministic, free, CI-runnable. The cheap/local LLM's
  job is refreshing cassettes on a schedule and ad-hoc agent testing. Live
  models never appear inside exact-state assertions.
- **Golden discipline**: machine writes snapshots, the human reviews diffs —
  CI refuses auto-updated snapshots; PRs touching golden/fixture paths are
  flagged; all golden-state diffs surface in the gate-2 packet.
- **Holdout (decided 2026-07-13, hybrid):** the generated bulk of the floor
  is agent-visible (gaming it requires corrupting the small generator, which
  adversarial review reads); a **small curated set of end-to-end acceptance
  scenarios is held out** — stored where authoring agents cannot read it,
  run at gate 2 and nightly, reporting pass/fail plus a PI-readable report.
  Baseline anti-gaming controls apply regardless: mutation testing,
  adversarial review, golden path-protection.
- **Seed discipline**: the seed is an immutable baseline cloned fresh per
  test (avoids shared-fixture rot); rich enough to satisfy every command's
  preconditions; doubles as the version-N upgrade fixture.

**Above the floor** (required before gate 2 can pass, beyond mechanism):

- **User-error resilience.** Doctrine: *total for display, strict for
  derivation* — surfaces render broken files with a warning; every
  derivation boundary parses-don't-validates and fails closed **per file**
  into quarantine with a reason (never crash the sweep, never silently
  skip — Jekyll's log-and-skip is the named anti-pattern). Test layers: a
  hand-enumerated, schema-driven fault corpus (delete required field, break
  YAML, dangling/malformed links, wrong enum, self-asserted verdict…) as the
  executable spec and permanent regression set, plus property-based
  structure-aware mutation of realistic seeds (Hypothesis) with the generic
  oracle *"structured error or correct parse; never crash; vault bytes never
  modified by a read."* Repair follows git-fsck: a report-only `doctor`
  sweep, lost-found quarantine, explicit opt-in repairs, vault-git as undo,
  **never auto-rewrite user files** (Dendron/Logseq failures are the
  precedent); the rebuild path itself gets fault-injection coverage.
- **Durability.** Deliberate `synchronous` choice for the vault DB (WAL +
  NORMAL can silently lose the most recent commits on power loss — likely
  wrong for expensive LLM-output writes); kill-9-during-write recovery
  tests; backups via `VACUUM INTO`/backup API, never file-copying a live
  DB; atomic write discipline (write-temp, fsync, rename) wherever the
  engine rewrites notes; consider continuous replication (Litestream-style)
  for the production vault.
- **Upgradeability.** Migration machinery is a hard prerequisite for a
  permanent vault (today `user_version` mismatch hard-fails — correct for
  ephemeral, fatal for permanent). Pattern: **frozen fixture per shipped
  version + an upgrade test per version** (Firefox Places), forward-only
  migrations, automatic pre-migration backup, `user_version` stamp, refuse
  downgrade (Firefox/Anki/Zotero consensus). Seed-file reconciliation on
  upgrade follows the lifecycle classes: regenerate release-owned data
  projections; never touch PI-owned view preferences and authored content.

### 3.5 The middle ring (pre-prod)

Runs on every gate-2 candidate; produces the gate-2 packet. **Decided
2026-07-13: budget-bounded sampled evals with conditional narrowing.**

- **Restore the latest production-vault backup into an isolated
  environment.** This *is* the restore drill (SRE: "no one wants backups;
  people want restores") — recoverable stays a verified property, not a
  hope.
- **Rehearse the migration on the restored real copy** (GitLab
  thin-clone / Lightroom pattern).
- **Run the deterministic sweep against the restored corpus — always.**
  Free (cassette-pinned) and covers the data-shape parity gap: the real
  corpus exercises scale and edge content no seed will.
- **Live-LLM portion, conditionally narrowed** (the same scope-narrowing
  pattern `verify` uses for docs-only diffs): if the diff touches any
  LLM-relevant surface (prompts, models, call sites, retrieval policy), run
  the frozen call-site eval suites against a stratified sample of real-corpus
  items at the production model tier; otherwise a fixed minimal smoke
  (digest, interrogation, draft slice, verify) suffices. Hard per-release
  budget cap; sample size set by observed cost telemetry.
- **Packet out:** golden-state diffs, holdout results, eval deltas vs
  baseline, migration + restore results, budget spent — the evidence gate 2
  actually reviews.

### 3.6 Gate 2 — go/no-go

An **irreversibility-management ritual, not a defect filter** (DORA: end-of-
pipe approval does not reduce change-failure; expecting it to catch bad code
is the CAB fallacy). Pre-declared, non-waivable checklist: floor green;
holdout green; backup taken and restore verified; migration rehearsed;
golden diffs reviewed; eval deltas within registered thresholds; budget
within cap. The human decision is *whether to touch the unrebuildable vault
now* — nothing else.

### 3.7 Promotion and production

- **Promote the exact artifact the middle ring validated** — no rebuild
  between gate 2 and production.
- Expand/contract migrations + the pre-promotion backup make the
  "irreversible" step a checkpointed transition.
- The production vault runs the promoted LLM profile (`production` runtime
  mode per beta.1 §5); the ephemeral tiers run `test` mode with isolated
  workspaces and budget-capped profiles.
- The 1,200-paper import is the **last** rung: instrumentation and the
  seeded-error license gate precede ingestion (telemetry is
  non-backfillable), per the empirical plan. Item 19 ("live in it") and the
  quality baseline run here — this vault is where the promise is answered.

## 4. LLM tiering doctrine

Fidelity follows **what the check assesses**, bounded by budget — the tier is
a budget decision, not a vault boundary:

| Tier | Use | Where |
| --- | --- | --- |
| Recorded cassettes | mechanism / exact-state / CI | floor, CI — deterministic and free |
| Cheap model (local or budget-capped cloud) | cassette refresh; ad-hoc agent behavior checks | scheduled job; agent loops |
| Production-tier live model | frozen eval suites; quality judgment; smoke | middle ring (sampled), production, observatory |

Ordering is cheap-first: functionality failures must never burn quality
budget. Judges: binary pass/fail over Likert; judge model ≠ generating
model; calibrated against PI labels and monitored (the observatory); an LLM
judge is never the sole authority for promotion. Eval tooling is portable
OSS in the existing pytest harness (hosted eval platforms are a deprecation
risk). Model selection rides the autoresearch harness: per-manifest choice,
pinned IDs, shadow-first promotion, `model_id` + `prompt_version` in the
experiment unit (roadmap items 16–17).

## 5. Explicitly not adopted (with the failure each avoidance prevents)

- **Per-PR required human review / CODEOWNERS-as-review** — rubber-stamps at
  agent volume; launders errors into human-approved precedent.
- **LLM gates that hard-block** — non-deterministic red trains everyone to
  ignore or re-run; LLM findings are advisory into the fix loop.
- **Full command × option × state cross-product** — interaction-testing
  evidence says pairwise; exhaustive only on the catalog dimension.
- **Full-fidelity middle ring** (whole corpus, live) — cost scales with the
  corpus for marginal signal over stratified samples; violates cheap-first.
- **A live model inside exact-state assertions** — nondeterministic flake
  that carries zero production-quality signal.
- **Down-migrations for the vault DB** — forward-only + pre-migration
  backup + refuse-downgrade is the embedded-SQLite consensus.
- **dm-flakey/CrashMonkey-grade filesystem fault rigs** — SQLite's own VFS
  testing covers it; the app's obligations are the misuse list + kill-9
  recovery + restore drills.

## 6. Build order (the trust track)

1. **The floor harness**: seed vault, catalog-driven sweep, invariant
   assertions, cassette layer, golden discipline. (The linchpin — nothing
   promotes without it.)
2. **Deterministic gate additions** (§3.3), coupled with granting agent
   self-merge.
3. **Above-floor layers**: fault corpus + doctor, durability tests,
   fixture-per-version upgrade tests (with roadmap item 6's migration
   machinery).
4. **Backup/restore machinery + the middle ring**, and the gate-2 checklist.
5. **The promotion step** (exact-artifact deploy to the Windows production
   vault) — the easier half, built once the floor is green.
6. **Merge queue** when agent concurrency demands it.

Feature readiness (beta.1's usefulness track) proceeds in parallel; both
tracks converge on the production vault's live evaluation.

## 7. Relationship to other documents

- [0.1.0-beta.1-requirements.md](./0.1.0-beta.1-requirements.md) §4–§5 — the
  governing *what*; this spec is the pipeline *how*.
- [0.1.0-beta.1-empirical-use-action-plan.md](./0.1.0-beta.1-empirical-use-action-plan.md)
  — the standing observatory and the production vault's evaluation protocol.
- `docs/superpowers/plans/roadmap.md` — items 6 (migrations), 10 (manifest
  dispatch), 12 (reactive substrate), 16–17 (autoresearch/model selection),
  19 (live in it) carry the implementation weight this spec references.
- `docs/superpowers/plans/okf-note.md` — placement doctrine and seeded-file
  lifecycle classes (the upgrade-reconciliation contract).
- [2026-07-13-pipeline-research.md](./2026-07-13-pipeline-research.md) — the
  verified prior-art record behind every named pattern above.
