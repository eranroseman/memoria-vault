# ExecPlan — finish v0.1.0-alpha.4

This is an ExecPlan: a single, self-contained, living document that carries the
remaining v0.1.0-alpha.4 work from its current state to a validated, observable
result. It follows `.agents/templates/exec-plan.md`; see
`.agents/playbooks/exec-plan.md` for how to run and maintain it. This instance is
tracked release scratch — it lives only here, under the alpha.4 `tmp/`, and is
deleted before the alpha.4 checkpoint closes.

## 0. Metadata

- **Task:** complete the v0.1.0-alpha.4 internal checkpoint — close the active
  build/defect/PI-surface issues, land the actionable packaging slice, and park
  the deferred items honestly.
- **Execution model:** each workstream below is its own worktree → branch → PR
  (`AGENTS.md` §1/§2; see §4). Authored on the now-merged `docs/alpha4-execplan`.
- **Milestone:** `0.1.0-alpha.4` (#3) — 25 open issues at authoring; scope
  finalized 2026-06-15 (§2.2 is authoritative for what is in vs out).
- **Related ADRs:** ADR-19 (Mapper MOCs; Tier 2 via #439), ADR-30 (ingest),
  ADR-31 (native Obsidian MCP), ADR-54 (batch worklists), ADR-55 (golden copy /
  upgrade), ADR-57 (engines write, agents judge), ADR-64 (native Windows; via
  #414), ADR-69 (operations naming; rename now), ADR-76 (deferred — wheel; step-1
  tooling only).
- **Design inputs:** [the packaging design note](install-a-real-package.md)
  (ADR-76 / #494 / #521).
- **Started:** 2026-06-15 · **Last updated:** 2026-06-15

## 1. Purpose / big picture

v0.1.0-alpha.4 is an **internal checkpoint** (an alpha checkpoint is a private
milestone, not a tagged public GitHub Release). Finishing it means the milestone
#3 issue set is either **shipped and verifiable from the Obsidian UI** or
**consciously deferred to a cadence-reviewed ADR** — with nothing left in the
ambiguous middle. The observable end state: a fresh install of the alpha.4 vault
lets a researcher capture a real paper, see it enriched and filed, and reach the
shipped assist/linter surfaces directly from Obsidian; everything not delivered
has an open issue or a `status: deferred` ADR explaining why.

## 2. Context and orientation

For a reader new to this repo:

- **Vault / runtime split.** The Python runtime lives in `src/.memoria/` and is
  rsynced into a vault's `.memoria/` by `scripts/install.sh`. Vault data lives in
  the Obsidian vault (`~/Memoria` runtime; `~/Memoria-test` sandbox — never test
  against the real vault).
- **PI** ("Principal Investigator") is this project's internal name for the human
  owner. The **PI direct-access rule:** every feature must be reachable from the
  Obsidian UI directly, not only via CLI.
- **Lanes / engines / gate.** Work runs through MCP servers; the policy-gate
  plugin hard-denies disallowed tool calls (the MCP-only agent sandbox). Agents
  cannot write files — they act only through MCP.
- **ADR-only decision model.** Every decision is an ADR in `docs/adr/` at some
  status; there is no proposals or design-notes folder. **Heads-up for this
  plan:** several issues below still cite retired `docs/design/*.md` paths
  (e.g. `memoria-design-update.md`, `dashboards-design.md`,
  `design-system-and-visual-discipline.md`). Those design docs are retired — the
  source of truth is now the relevant ADR or current `docs/` page. Treat the
  `docs/design/` references as stale pointers to fix, not as live specs.
- **Versioning note.** The canonical scheme is `0.1.0-alpha.N`. Older docs/issues
  used a carry-over labelling (`0.1.0` = alpha.1) where `v0.2`/`v0.1.1` meant
  **alpha.2** and `v0.3`/`v0.1.2` meant **alpha.3**; treat those as alpha labels.
  (#198 "Decide v0.2 scope" is the genuine future 0.2.0 — not a mislabel.)
- **Release housekeeping (already landed).** `project-starter.md` and
  `test-env.md` — not alpha.4 work — were moved to
  `docs/releasing/0.1.0-alpha.5/tmp/` (#530). The packaging note
  (`install-a-real-package.md`) stays here (Workstream E references it) and was
  also **copied** to `0.1.0-alpha.5/tmp/` (#533) where the deferred wheel
  migration will land; the alpha.4 copy is deleted when this checkpoint closes.

### 2.1 Scope — the 25 open alpha.4 issues, grouped

The 2026-06-15 decision (§2.2) is authoritative; the tags below mark the changes
from the original disposition.

**A. Ingest / extraction engine (ADR-30) — in**

| # | Title | One-line scope |
|---|---|---|
| #438 | Unpaywall OA lookup FIRST in extraction | add an Unpaywall tier ahead of PMC + local PDF; OA PDF goes through the same detect path |
| #437 | PubMed/NCBI as a 4th metadata source | add `fetch_pubmed` to resolve/merge cross-check (MeSH, PMID/PMCID, pub types) |

**B. Security / transport — deferred out (2026-06-15)**

| # | Title | One-line scope |
|---|---|---|
| #527 | HTTPS for Obsidian Local REST API + native MCP | **deferred:** keep ADR-31's documented loopback-HTTP residual; revisit later via OS/Python trust-store or mkcert (not a Hermes-only blocker) |

**C. Defects / quality / contradictions**

| # | Title | One-line scope |
|---|---|---|
| #443 | Explanation pages describe unbuilt/retired behavior | five published pages violate zero-contradiction; re-scope to deferred or fix |
| #493 | Refactor tests off dynamic `globals()` imports | explicit module aliases; clears ~hundreds of `F821`; overlaps Workstream E step 1 |
| #472 | Code/test naming cleanup | script kebab→snake + retire `load_script()`; folder pluralization; rides ADR-69 |

**D. Obsidian PI surface + project workspace (PI direct-access)**

| # | Title | One-line scope · note |
|---|---|---|
| #380 | Assist surface (Find/Search/Patterns/Ask/Draft/Explore) | in-Obsidian invocation (palette/pane/selection) → proposals · cites retired design doc |
| #375 | Status-bar ambient indicator | one indicator: Linter verdict + queue depths · cites retired design doc |
| #378 | Design-system enforcement | Linter anti-pattern checks + lifecycle link coloring · cites retired design doc |
| #376 | Callout producers `[!suggestions]` / `[!verification]` | deterministic top-K + LLM line (ADR-57 split) |
| #377 | verify-on-commit trigger | draft commit → verify-lane card |
| #343 | Graded-loudness routing | alert→push, block→hold until ack, quiet/notice pull-only · cites retired design doc |
| #145 | Property reorder / group / color-code | lifecycle stage is buried in frontmatter; define display order + coloring |
| #183 | Obsidian forms for structured capture | modal-form plugin → valid frontmatter into staging |
| #154 | Automate start-a-writing-project | form → script scaffolds `40-workbench/<project>/` + Mapper scope card |
| #336 | Batch worklists (Bases) | ADR-54 worklist surface; per-row lifecycle `decision`; one aggregate prompt |
| #381 | Remaining map skills | **deferred** (with #379/#344): score-* gated on the calibration spec (needs real-data shadow calibration); graph-claims/canvas-hub revisit later |
| #329 | Obsidian project-management research | survey PM plugins/methods → adopt/borrow/reject; feeds the project workspace |

**E. Runtime packaging (the `install-a-real-package.md` workstream)**

| # | Title | One-line scope |
|---|---|---|
| #521 | Deferred ADR-76: runtime as installable wheel | **deferred target** — cadence review, not an alpha.4 gate |
| #493 | (see C) tests off globals | the test side of step 1 below |

Folded-in design note → see §3 Workstream E and §10. Actionable now: the
**tooling-only `pyproject.toml`** step (pytest + ruff config, delete the
`conftest.py` `sys.path` block) — issue work, no ADR. The full wheel/deployment
flip stays deferred (ADR-76) pending the §4.5 policy-gate version-skew decision,
the ADR-69 `engines → operations` rename landing first, and a real distribution
need.

**F. Upgrade path**

| # | Title | One-line scope |
|---|---|---|
| #339 | Golden-copy update path on release upgrade | ADR-55 open question: three-way reconcile (golden-old/new/live) without clobbering PI edits |

**G. Formerly deferred-tracking — split by the 2026-06-15 decision**

| # | Tracks | Disposition |
|---|---|---|
| #414 | ADR-64 native Windows support | **added → in** — build this checkpoint ⇒ accept ADR-64 + supersede the WSL2-only rule (#296). Large roadmap change (see §2.2) |
| #439 | ADR-19 Tier 2 Mapper handoff | **added → in** — build the hub/MOC handoff (review-gated; hubs stay approved) ⇒ update ADR-19 status |
| #412 | ADR-62 measurement/verification harnesses | **deferred** — instrument once more behavior ships |
| #370 | ADR-38 pre-file similarity ratchet | **deferred** — depends on the deferred calibration discipline (#379) |
| #296 | Migrate Windows WSL2 → native | folds into #414's WSL2-rule supersession; track the broader migration here |

**H. Structural — `engines → operations` rename (ADR-69) — added → in**

ADR-69 is accepted; execute the code-tree rename now as a standalone wide PR
(touches `conftest.py`, `install.sh`, tests, docs, every import). It unblocks
#472 and is the prerequisite for the step-1 packaging tooling. Doing it now also
opens the option to do the full ADR-76 wheel migration in the same tree-move pass
— but that stays deferred unless its §4.5 (policy-gate) and §6.7 (schemas)
decisions are made.

### 2.2 Scope decisions (2026-06-15)

**Deferred out of alpha.4:** #527 (HTTPS transport — keep ADR-31's documented
residual); #379 + #381 + #344 (calibration spec, score-* map skills, diversity
reserve — need real-data shadow calibration); #412 (ADR-62 harnesses); #370
(ADR-38 ratchet — depends on the deferred calibration). Their issues stay open.

**Added to alpha.4 (over the original deferred disposition):**

- **ADR-69 rename** — execute `engines → operations` now (Workstream H).
- **#414 native Windows (ADR-64) — major change.** Building it means *accepting
  ADR-64* and *superseding the WSL2-only rule* (the AGENTS.md "work inside WSL2"
  constraint and #296). It collapses the two-OS topology and has wide blast
  radius — the installer, AGENTS.md, the ADR-31 WSL2↔Windows bridge, and the
  analysis-stack wheels. Native Windows was **intended for alpha.3** (ADR-64's
  *When this matters*: "revisit after v0.1.0-alpha.3"); it slipped, so alpha.4
  picks it up as the **overdue carry-over**, not a scope-up. (#296's body carried
  a "v0.3 / v0.2" label — the versioning carry-over where v0.3 = alpha.3 and
  v0.2 = alpha.2; corrected at source.) **Verify Hermes' native-Windows
  support against the primary `~/.hermes` docs first** — it is the load-bearing
  assumption in #296 — and record the supersession as an ADR before the port.
- **#439 Mapper Tier 2 (ADR-19)** — build the hub-threshold → agent-drafted
  hub/MOC handoff (review-gated; `notes/hubs/` stays approved); update ADR-19's
  status from "Tier 2 deferred" to built.
- **#443 contradiction pages** — fix by *building* the in-scope features
  (#375/#376/#377/#343) and *re-scoping* the one genuinely retired page
  (agent-client-picker) to match reality.

**Held to recommendation (flip if you want otherwise):** #339 first (amend
ADR-55 with the reconcile design); packaging **step-1 tooling `pyproject` only**,
full ADR-76 wheel migration **deferred**; #378 bundles supercharged-links under
the current ADR-26/55 baseline (ADR-74 not required).

**ADR actions this scope implies** (ADR edits the plan links to, not recorded
here): accept ADR-64 + supersede the WSL2-only rule (#414); update ADR-19 (#439);
amend ADR-55 with the upgrade reconcile (#339).

## 3. Plan of work

Sequenced so structural and load-bearing changes land before the broad UI
surface; deferred items (§2.2) are not built this checkpoint.

1. **Structural first — `engines → operations` rename (H, ADR-69).** A standalone
   wide PR merged before other branches (AGENTS.md merge discipline); active
   branches rebase the same day. Unblocks #472 and the step-1 packaging tooling.
2. **Engine + integrity (A, F).** #438/#437 are unit-testable against fixture
   papers; #339 resolves ADR-55's upgrade reconcile (amend ADR-55).
3. **Defects / quality (C).** #493 (off `globals()`) + #472 (naming, rides the
   rename); #443 is resolved by building its in-scope producers (step 5) and
   re-scoping the one retired page (agent-client-picker) now.
4. **Packaging step-1 (E).** Tooling-only `pyproject` (pytest + ruff, delete the
   repo-side conftest import bootstrap). Full ADR-76 stays deferred.
5. **PI surface (D), incrementally.** Each verb/indicator independently
   shippable, reachable from Obsidian (PI rule); repoint any retired
   `docs/design/` reference first. Covers #443's producers
   (#375/#376/#377/#343), #336, #380, #145, #183 → #154, #329, and #378 (bundle
   supercharged-links under the current baseline).
6. **Mapper Tier 2 (#439, ADR-19).** Build the hub/MOC handoff; update ADR-19.
7. **Native Windows (#414, ADR-64) — its own track, last.** First land the ADR:
   accept ADR-64 + supersede the WSL2-only rule (verify Hermes native support
   against the `~/.hermes` docs). Then the port (installer, ADR-31 bridge,
   analysis stack). Largest blast radius — isolate it.

## 4. Concrete steps

1. **Isolate each workstream** (`AGENTS.md` §1) — a fresh worktree + branch per
   workstream/issue, off the latest `origin/main`:

   ```bash
   git fetch origin
   git worktree add ~/mv-<slug> -b <type>/<slug> origin/main
   cd ~/mv-<slug>
   ```

2. **Pick the next issue from §2.1 in the §3 order.** Open its own worktree +
   branch per item (one scope → one branch → one PR). Read the issue body and the
   ADR/source it names; if it cites a retired `docs/design/*` path, resolve to
   the current ADR/doc first.

3. **Implement against the source of truth**, then verify per §5 with focused
   tests (`scripts/test.sh`) and an Obsidian-UI check where the PI direct-access
   rule applies.

4. **Update this plan** (§7 Progress, §8 Execution log, §9 Surprises) at every
   stopping point, then open the PR.

   ```text
   (expected: each closed issue maps to a merged PR; each deferred issue maps to
    a status: deferred ADR with a current "When this matters")
   ```

## 5. Validation and acceptance

Per `.agents/playbooks/verify-change.md` — observable claims, lowest-cost
evidence, real transcripts:

- **#438:** Given a capture with no PMCID and a scanned local PDF, when extraction
  runs, then Unpaywall is queried **first** and an OA PDF (if found) is used
  ahead of PMC/local. *Prove with:* a focused extract test on a known-OA DOI.
- **#437:** Given a paper resolvable only via PMID, when resolve/merge runs, then
  `fetch_pubmed` contributes MeSH/PMID/PMCID to the cross-checked record. *Prove
  with:* a resolve_merge unit test.
- **Workstream H (rename):** Given the `engines → operations` rename, when the
  suite runs, then imports resolve, `scripts/test.sh all` stays green, and no
  stale `engines` path remains. *Prove with:* `scripts/test.sh all` + a tree grep.
- **#339:** Given a vault with PI edits, when a release upgrade runs, then changed
  system files refresh and PI customizations survive (three-way reconcile).
  *Prove with:* a disposable-vault upgrade test — never `~/Memoria`.
- **Workstream D items:** Given the feature, when invoked **from the Obsidian
  UI**, then the result lands as a proposal in staging. *Prove with:* an attended
  Obsidian check (note residual risk if runtime-only).
- **Workstream E step 1:** Given the tooling `pyproject.toml`, when tests run
  without the `conftest.py` `sys.path` block, then `python -m pytest` and
  `ruff check .` stay green. *Prove with:* `scripts/test.sh all`.
- **#439 (Mapper Tier 2):** Given a fired `hub-threshold` finding, when handed to
  the Mapper, then a hub/MOC note is drafted as a review-gated proposal and
  `notes/hubs/` stays PI-approved. *Prove with:* a runtime test on a seeded vault.
- **#414 (native Windows):** Given a native-Windows host (no WSL2), when installed,
  then Hermes + the MCP servers run and a capture→file round-trip works. *Prove
  with:* an attended native-Windows install — **gated on** accepting ADR-64 and
  verifying Hermes native support first (§2.2).
- **Deferred (#412, #370):** confirm each ADR is `status: deferred` with a current
  *When this matters*; record the cadence verdict in §8 — do **not** build.

## 6. Idempotence and recovery

- **Safe to re-run:** each issue is its own branch/PR; re-running an unstarted
  issue is a no-op. This plan is regenerable from the milestone #3 issue list.
- **Rollback:** `git worktree remove` a per-issue worktree; revert the PR commit.
  The structural rename (H) is the only wide change — revert it as one squash
  commit before dependent workstreams build on it.

## 7. Progress

- [x] 2026-06-15 — ExecPlan authored; `project-starter.md` + `test-env.md` moved
      to `docs/releasing/0.1.0-alpha.5/tmp/`; 25 issues inventoried + grouped.
- [x] 2026-06-15 — Scope finalized (§2.2): deferred #527/#379/#381/#344/#412/#370;
      added ADR-69 rename, #414, #439, #443.
- [x] 2026-06-15 — Versioning carry-over labels fixed (#532); packaging note
      copied to `0.1.0-alpha.5/tmp/` (#533); plan readiness pass — execution can start.
- [x] 2026-06-15 — H implemented on `refactor/operations-rename`; structural
      PR ready after review/commit. Validation: `scripts/test.sh check`,
      focused pytest, `scripts/test.sh all`, and `bash scripts/e2e-smoke.sh`.
- [x] 2026-06-15 — A ingest #438/#437 implemented on
      `feat/alpha4-ingest-sources`: Unpaywall OA PDF lookup is the first extract
      option, and PubMed/NCBI is the fourth resolve/merge source. Validation:
      focused ingest/classify pytest and `scripts/test.sh all`.
- [x] 2026-06-15 — F golden upgrade #339 implemented on
      `feat/alpha4-golden-restore`: ADR-55 amended; `golden_restore.py upgrade`
      performs old-golden/new-source/live reconcile; installer routes
      golden-covered system files through it. Validation: focused pytest,
      `golden_restore.py --self-test`, `scripts/test.sh all`,
      `bash scripts/e2e-smoke.sh`, installer dry-run, `status-doctor`.
- [x] 2026-06-15 — F follow-through complete: #339 merged via PR #538 and
      issue closed.
- [x] 2026-06-15 — C defects slice #493/#443 implemented on
      `fix/alpha4-defects`: tests no longer use dynamic `globals().update(...)`,
      Ruff/pre-commit/CI now cover `tests/`, and the retired/unbuilt explanation
      pages are re-scoped to shipped vs deferred behavior. Validation:
      `ruff check scripts src/.memoria .github/scripts tests`, `scripts/test.sh all`,
      `status-doctor`, stale-doc audit.
- [x] 2026-06-15 — C follow-through complete: #493/#443 merged via PR #541 and
      both issues closed.
- [x] 2026-06-15 — C structural naming slice for #472 implemented on
      `refactor/alpha4-naming-cleanup`: script kebab-case → snake_case,
      `load_script()` retired, and `notes/source` / `notes/index` pluralized
      across shipped vault paths, schemas, policy, tests, docs, and agent maps.
      Validation: `scripts/test.sh all`, `bash scripts/e2e-smoke.sh`,
      `status-doctor`, stale-reference audit.
- [x] 2026-06-15 — C #472 follow-through implemented on
      `refactor/alpha4-test-splitting`: structural PR #542 merged, and the
      remaining legacy single-function test files were split into granular pytest
      cases. Validation: focused pytest, Ruff, one-test-file inventory, and
      `scripts/test.sh all`. Merge this PR to close #472.
- [x] 2026-06-15 — E step 1 implemented on `chore/alpha4-packaging-tooling`: added
      tooling-only `pyproject.toml` for pytest `pythonpath` and Ruff config,
      removed `tests/conftest.py` import bootstrapping and the standalone Ruff config, and kept
      `requirements-dev.txt` plus runtime bootstraps untouched. Validation:
      `python -m pytest tests/ --co -q`, `python -m pytest tests/ -q`, and
      `ruff check .`. #521 remains open/deferred for the full ADR-76 wheel migration.
- [x] 2026-06-15 — D #375 status-line surface implemented on
      `feat/alpha4-status-bar`: Home now ships the Dataview status line showing
      Linter verdict plus Active/Waiting/Review/Retries queue depths;
      `board_export.py` snapshots retrying depth; status-line docs are no longer
      deferred. Validation: focused pytest, `scripts/test.sh all`, docs-doctor.
- [x] 2026-06-15 — D #376 callout producers implemented on
      `feat/alpha4-callout-producers`: `Memoria: link claim` writes a collapsed
      deterministic `[!suggestions]` top-K callout before delegating, and
      `Memoria: verify draft` writes an expanded `[!verification]` trace callout
      before delegating. Validation: JS syntax checks, focused QuickAdd pytest,
      docs-doctor.
- [ ] (next) D — continue PI surface (#377/#343/#380/#145/#183/#154/#336/#329/#378).
- [ ] (next) #439 Mapper Tier 2 (update ADR-19).
- [ ] (next) #414 native Windows — ADR-64 + WSL2-rule supersession first, then port.

## 8. Execution log

- 2026-06-15 — Scoped alpha.4 from milestone #3 (25 open). Tactical: grouped by
  blast radius (engine/security/integrity before broad UI), kept the deferred
  tracking issues out of the deliverable set. Architectural calls remain in their
  ADRs — e.g. the wheel migration is ADR-76 (deferred), not decided here.
- 2026-06-15 — Decision deferred to ADR, not recorded here: whether to un-defer
  ADR-76 (full wheel migration). Blocked on the §4.5 policy-gate version-skew
  choice and the ADR-69 rename ordering (see the packaging note).
- 2026-06-15 — Scope decision (yours): deferred #527, #379, #381, #344 (plus
  #412, #370) out of alpha.4; added the ADR-69 rename, #414, #439, #443 in.
  Sequencing in §3; architectural consequences routed to ADRs (§2.2), not here:
  accept ADR-64 + supersede the WSL2-only rule (#414), update ADR-19 (#439),
  amend ADR-55 (#339).
- 2026-06-15 — Readiness pass: dropped stale refs (the merged authoring worktree;
  the packaging note now also in alpha.5/tmp), removed the deferred-#527
  validation claim, added acceptance for the rename (H), #439, and #414, and
  corrected the retired-design-doc count. The plan is executable as written.
- 2026-06-15 — H implementation branch prepared: moved
  `src/.memoria/engines/` to `src/.memoria/operations/` by ADR-69 category,
  renamed `pipeline.py` → `runner.py` and `golden.py` → `golden_restore.py`,
  repointed installer/cron/test/CI/docs references, and added installer pruning
  for stale deployed `.memoria/engines/`. Runtime smoke caught and fixed two
  standalone-path misses (`precommit_check.py` schema loader and
  `board_export.py` Inbox writer).
- 2026-06-15 — A ingest branch prepared for #438/#437: `extract.py` now tries
  Unpaywall with the `NCBI_EMAIL` contact before PMC/local PDF and runs OA PDFs
  through the same coherence gate; `resolve_merge.py` now fetches PubMed via
  E-utilities, merges PMID/PMCID/publication types/MeSH terms, and includes
  PubMed in identity-agreement diagnostics. Offline tests cover both paths.
- 2026-06-15 — F golden branch prepared for #339: release refresh now excludes
  golden-covered system files from the bulk deploy and reconciles them via
  `golden_restore.py upgrade --source SRC --apply`. Clean additions/edits/removals
  apply when live still matches old golden; PI-customized conflicts are preserved
  and remain visible as drift against the refreshed golden baseline.
- 2026-06-15 — C defects branch prepared for #493/#443: explicit test bindings
  replace `globals().update(...)` and the Ruff gate now includes `tests/`. The
  five contradiction pages were audited: agent-client/status-line/verify pages
  already carried deferred/current notices; callouts and loudness routing docs
  needed current-vs-deferred wording fixes. `_reports/v011-review-defect-inventory.md`
  is not present in the repo, so there was no report row to mark.
- 2026-06-15 — C structural naming branch prepared for #472: renamed importable
  tooling scripts (`docs_doctor.py`, `check_test_refs.py`, etc.), switched script
  tests to normal imports, removed the `load_script()` helper, and pluralized the
  source/index note homes to `notes/sources/` and `notes/indexes/`. PR #542
  merged; #472 stayed open for the remaining test split.

- 2026-06-15 — C #472 test-splitting branch prepared: converted the remaining
  legacy single-function L1 tests (`check_test_refs`, `docs_doctor`,
  `gen_adr_index`, `ingest_mcp`, `ingest_paper`, `link`, `metrics_aggregate`,
  `runner`, `policy_hook`, `pr_policy`, `status_doctor`, and `retraction`) into
  behavior-scoped pytest cases. The inventory now reports no one-test files.

- 2026-06-15 — E tooling branch prepared: repo-side import roots now live in
  `pyproject.toml` (`tool.pytest.ini_options.pythonpath`) and Ruff reads its lint
  policy from `tool.ruff.lint`. This intentionally does not add `[project]`,
  does not change requirements files, and does not touch deployed runtime
  `__file__` bootstraps; ADR-76 remains deferred via #521.

- 2026-06-15 — D #375 branch prepared: promoted the existing Home status
  glance into the shipped status line by reading latest lint verdict metrics (with
  lint-findings fallback) and board-state queue counts. `board_export.py` now
  includes `retrying` counts for ready cards with retries, so the line can show
  Active/Waiting/Review/Retries without querying Hermes directly.

- 2026-06-15 — D #376 branch prepared: QuickAdd link/verify palette actions
  now produce the inline callout surfaces directly in Obsidian before creating
  their lane cards. Link suggestions are deterministic top-K local overlap
  candidates capped at 5 forward + 5 backward; verification callouts record a
  deterministic claim-link/citekey preflight while the Peer-reviewer card keeps
  the support judgment.

## 9. Surprises & discoveries

- Several alpha.4-milestoned issues began as **deferred-ADR tracking issues**
  (#521, #414, #412, #370, #439). The 2026-06-15 decision pulled **#414** and
  **#439** into scope (accepting ADR-64 + superseding the WSL2-only rule, and
  building ADR-19 Tier 2); #412, #370, and the full ADR-76 stay deferred.
- Four PI-surface issues (#380, #375, #378, #343) cite **retired `docs/design/*`
  paths**. Each needs its reference repointed to the current ADR/doc before build
  — a zero-contradiction fix that travels with the feature.
- #381 is blocked by #379 (calibration threshold spec), which is **not in the
  alpha.4 milestone** — a cross-milestone dependency to surface.

## 10. Interfaces & dependencies

- **Ingest:** `src/.memoria/operations/processing/ingest/extract.py` (ADR-30 tier order; #438)
  and `…/ingest/resolve_merge.py` (`fetch_*`; #437) — these move under
  `operations/` once Workstream H lands, so sequence H first. NCBI/Unpaywall keys
  already provisioned in profile `.env`.
- **Transport:** ADR-31 native Obsidian MCP over loopback. #527 (HTTPS) is
  **deferred** — the residual stays documented; later resolve via OS/Python
  trust-store or mkcert (not a Hermes-only blocker).
- **Rename (ADR-69):** `src/.memoria/engines/` → `operations/` across
  `conftest.py`, `install.sh`, tests, docs, imports — a standalone structural PR
  (Workstream H).
- **Native Windows (#414, ADR-64):** accept ADR-64 + supersede the WSL2-only
  rule; touches the installer, the ADR-31 WSL2↔Windows bridge, and the
  analysis-stack wheels. Verify Hermes native support against `~/.hermes` first.
- **Mapper Tier 2 (#439, ADR-19):** a fired hub-threshold finding → a drafted hub
  note, review-gated; `notes/hubs/` stays approved.
- **Upgrade:** `golden_restore.py` manifest + ADR-55 (#339).
- **Packaging:** full design + the policy-gate version-skew options (i/ii/iii)
  are in [the packaging design note](install-a-real-package.md); the wheel
  carries `assumes: [44, 46, 69, 73]` (not 55 — golden never covered code).
- **PI surface:** ADR-57 (deterministic top-K vs LLM line; #376), ADR-54
  (worklists; #336). Each D item needs an in-Obsidian affordance (PI rule).

## 11. Artifacts & notes

- Release-scratch moves: `project-starter.md` + `test-env.md` renamed into
  `0.1.0-alpha.5/tmp/` (#530); `install-a-real-package.md` copied there (#533).
- Per-issue transcripts to be pasted here as each workstream lands.

## 12. Outcomes & retrospective

- **Shipped:** (fill as workstreams close — each maps to a merged PR.)
- **Still open:** (remaining gaps → keep their GitHub issues open.)
- **Routed to:** decisions → ADRs (e.g. ADR-76 for packaging); readiness/scope →
  milestone #3 issues; this plan holds no durable record of its own.
- **Lessons:** (fill at checkpoint close, before deleting this `tmp/` note.)
