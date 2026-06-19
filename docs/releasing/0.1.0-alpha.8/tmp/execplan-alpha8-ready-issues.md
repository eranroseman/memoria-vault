# ExecPlan — alpha.8: implement all Ready issues

## 0. Metadata

- **Task:** Implement every issue currently `Readiness: Ready` in the Memoria Issue
  Tracker, as the alpha.8 runtime-foundations & observability checkpoint.
- **Worktree / branch:** one per issue — `~/mv-<slug>` · `feat/<slug>` (small PRs;
  never combine package layout, policy semantics, and domain rewrites in one PR).
- **Related ADRs:** ADR-76 (package spine), ADR-29 (L2 model boundary), ADR-65
  (shadow proposers), ADR-84 (read-only Inspector), ADR-100 (exploration trace),
  ADR-105 (content-light diagnostics), ADR-106 (cost/disposition analytics),
  ADR-38 (pre-file similarity), ADR-80 (containerized test env), ADR-81 (gate
  dashboards), ADR-74 (bundled-plugin provenance).
- **Related issues / milestone:** #726 (umbrella) + #727 #728 #729 #730 #731 #686
  #688 #736 #737 #370 #379 #697 #713 #690 #660 #329 · v0.1.0-alpha.8.
  `#611` was Ready but already **closed** — excluded.
- **Started:** 2026-06-19 · **Last updated:** 2026-06-19

## 1. Purpose / big picture

alpha.8 is a **foundation** checkpoint. Two large coherent blocks dominate: the
ADR-76 incremental technical-debt refactor (a stable `memoria.*` package spine,
shared runtime helpers, and behavior-preserving splits of the security-sensitive
policy MCP and the structural-impact/ingest/installer hotspots), and the
clean-slate observability layer (a content-light diagnostic plane and cost/
disposition analytics, plus shadow-only similarity/calibration telemetry). On top
of those it lands two accepted-ADR feature implementations (read-only Inspector,
exploration-trace capture), day-1 empty-state polish, a Zotero→catalog capture bug
fix, CI provenance + opt-in live-Hermes test hardening, and an Obsidian
project-management research survey.

Observable result: a fresh checkout installs editable through `memoria.*`; the full
pytest + e2e suite stays green through every refactor; redacted diagnostics and
cost rows appear outside the vault; pre-file similarity surfaces report-only
neighbours; the Inspector and exploration-trace surfaces work in a runtime vault;
and an empty fresh vault reads as intentional.

## 2. Context and orientation

- **Memoria** is an Obsidian-vault-plus-Hermes-agent system. Runtime Python lives
  under `src/.memoria/operations/` and `scripts/`; the deployed vault skeleton is
  `src/`. Tests are in `tests/`.
- **Readiness** is a field in the [Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1)
  (Projects v2 #1): `Ready | Needs shaping | Blocked | Later`. "Ready" means the
  shaping gate is cleared and the issue can be implemented now.
- **Gate** = the approval gate (policy MCP enforced). "Space"/"dashboard" =
  navigation surfaces. Do not call the user "PI".
- **ExecPlan home:** this file lives in `docs/releasing/0.1.0-alpha.8/tmp/` and is
  deleted before the checkpoint closes; durable outputs route to ADRs and issues.
- **State lives in issues, not this plan.** Gate/stage readiness state belongs to
  the "Release v0.1.0-alpha.8" parent issue and its sub-issues (see §4 step 0).
- **Project Projects-v2 CLI/GraphQL calls must be prefixed `env -u GITHUB_TOKEN`**
  (the repo-scoped `GITHUB_TOKEN` shadows the project-scoped token).

## 3. Plan of work

The work is a **dependency-ordered sequence of small PRs**, one per issue. The hard
ordering constraint comes from the #726 umbrella: the package spine (#727) must land
first; shared helpers (#728) next; then the splits and everything else can proceed,
largely in parallel, against the new import root. The structural/ingest/installer
hotspot split (#730) goes last in the refactor block. The observability, telemetry,
feature-ADR, UX, bug, CI, and research issues do not depend on the refactor and can
be scheduled around it, but PRs that touch refactored modules should rebase onto the
landed spine to avoid churn.

Cross-cutting constraints (from #726): required CI check names stay unchanged;
public/user-facing commands stay callable (compatibility wrappers where needed);
every refactor PR preserves behavior — semantic changes need a separate issue/ADR;
docs/reference + docs/testing + ADR-76 are updated whenever a child changes the
documented architecture.

**Sequencing tiers:**

1. **Tier 0 — bootstrap.** Create the "Release v0.1.0-alpha.8" parent issue + gate
   sub-issues (G1–G9), and the `0.1.0-alpha.8` milestone; backfill the `{{ #NN }}`
   placeholders in the release plan.
2. **Tier 1 — spine (blocks the rest of the refactor).** #727.
3. **Tier 2 — helpers.** #728 (prefer before #729/#730).
4. **Tier 3 — parallel after foundation.** #729, #731, #686, #688, #736, #737,
   #370, #379, #697, #713, #690, #660, #329.
5. **Tier 4 — last refactor split.** #730 (after #727; prefer after #728).
6. **Tier 5 — close.** #726 umbrella closes when all children close.

## 4. Concrete steps

Each issue is its own worktree/branch/PR. Step 0 is bootstrap; steps map to the
sequencing tiers. Per AGENTS.md §1, **always** start a fresh worktree+branch before
any change (a shared checkout sweeps concurrent staged files into your commit).

0. **Bootstrap the release** (do once):

   ```bash
   env -u GITHUB_TOKEN gh api repos/eranroseman/memoria-vault/milestones \
     -f title='0.1.0-alpha.8' -f state=open
   # create the "Release v0.1.0-alpha.8" parent issue with one sub-issue per gate G1-G9,
   # then edit release-plan-0.1.0-alpha.8.md §2/§4 to replace {{ #NN }} with the parent number.
   ```

1. **Per-issue session** (template — repeat for each issue, `<slug>`/`<n>` filled):

   ```bash
   git fetch origin
   git worktree add ~/mv-<slug> -b feat/<slug> origin/main
   cd ~/mv-<slug>
   # ... implement the issue's acceptance criteria ...
   PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/
   bash scripts/e2e-smoke.sh
   ```

   Expected: pytest and e2e-smoke green before opening the PR. Open one PR per issue;
   link it to the issue and the gate sub-issue.

### Per-issue scope & acceptance (the instruction set)

**#727 — Package spine & editable import root (G1, Tier 1).** Add a `memoria.*`
package root; keep `src/` as the deployed vault skeleton; add `[project]` metadata so
`pip install -e .` works and tests import through the package root; convert one
low-risk shared import path first; keep installer/MCP/profile entrypoints working via
wrappers or updated config templates. Done when: fresh-checkout editable install runs;
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/` passes; `check_test_refs.py`
passes; `e2e-smoke.sh` passes; a bare-import smoke imports the core package without the
MCP SDK; the PR lists every retained `sys.path.insert` with rationale.

**#728 — Shared runtime helpers (G2, Tier 2).** Create dependency-light
`memoria.runtime.{vaultio,jsonl,time,paths}` helpers (frontmatter parse, safe read,
markdown traversal with directory pruning during walk, tolerant JSONL iterate/append,
`now_iso()` UTC-Z). Migrate ≥3 of: `detectors.py`, `structural_impact.py`,
`loudness.py`, `test_env_harness.py`, MCP modules using `_shared.py`. Done when: unit
tests cover malformed frontmatter / nested YAML / no-frontmatter / bad+missing JSONL /
append parent creation / skip-dir traversal; duplicates removed from ≥3 modules;
dependency-light modules still import without the MCP SDK.

**#729 — Split policy MCP (G3, Tier 3).** Split `policy_mcp.py` into
model/paths/decision/lanes/audit/engine + `mcp.policy_server`. **All security
invariants must hold unchanged** (invalid action denies; traversal denies+audits raw
path; missing `task_id` denies; lane-load error denies; hash-read error denies
mutating allows; review-gated writes degrade to `dry_run`; open `loudness: block`
denies promotion until acked; skill policy can only narrow; `complete_write` validates
`before_hash`; pure decision importable without MCP SDK). Add characterization tests
for any untested invariant first. Thin compatibility wrapper at old entrypoint if
config still points there. **No policy semantic changes** in this PR.

**#730 — Split structural-impact / ingest / installer hotspots (G3, Tier 4).**
Umbrella for three behavior-preserving splits in order: structural impact
(graph/analysis/survey/gap-taxonomy/render/CLI), ingest (source clients / partial
model / merge-provenance / diagnostics / runner stages), installer (prereqs / source
resolution / Obsidian config / Hermes-profiles / runtime tools). One PR per hotspot;
create child issues if a PR would touch more than one. Each keeps existing tests green,
adds ≥1 focused test for an extracted pure function, names moved symbols + compat
strategy, no unrelated formatting churn.

**#731 — e2e smoke importable helpers (G4, Tier 3).** Keep `scripts/e2e-smoke.sh` as
the entrypoint; move assertions into `scripts/e2e_smoke.py` (or package equivalent)
exposing `vault-assembly`/`commit-gate`/`offline-ingest`/`workflow-replay`/
`final-integrity`. Shell orchestrates, Python owns assertions. Done when: e2e-smoke
passes; `pytest tests/test_test_env_harness.py` + new harness tests pass; embedded
Python substantially reduced; same stage names in order; no live/GUI/Docker checks
added to PR CI.

**#686 — CI provenance doctor for bundled plugin lock (G4, Tier 3).** Add a doctor in
the required validation path that validates `src/.obsidian/plugin-provenance-lock.json`:
each enabled plugin represented once, each declared artifact exists and matches SHA-256,
no undeclared executable entered `src/.obsidian/plugins/`, install stays
network-independent. Existing `test_plugin_provenance.py` calls the doctor or shares its
core. Updater automation stays out of scope. Keep ADR-74 consistent.

**#688 — Opt-in live Hermes test-l2 smoke (G4, Tier 3).** Add `scripts/test-l2.sh`,
non-PR: preflight Hermes/vault/local-model; use a filesystem `obsidian` MCP shim (no
GUI); drive 1–2 `hermes -z`/`hermes chat -q` dispatches; assert artifact shape + a live
policy-gate audit row; clear skip status when prereqs missing. Done when: `--help`
documents prereqs + non-PR status; a local run proves ≥1 live dispatch + gate decision +
artifact assertion; ADR-29 and the coverage matrix link to it.

**#736 — ADR-105 content-light diagnostic plane (G5, Tier 3).** Structured error/warn
logging for Memoria-owned Python MCP servers + Operations, written to an OS state dir
**outside vault and Git**, with rotation + bounded retention; user-triggered redacted
bundle generation; a redaction self-test with known-sensitive strings. Done when:
diagnostics default to errors/warnings + typed codes + hashes/lengths (not raw
payloads); raw capture is ephemeral/self-disarming; nothing written under vault/commit
path; redaction + retention boundary tests pass; reference docs explain location +
bundle sharing.

**#737 — ADR-106 cost & disposition analytics (G5, Tier 3).** Add a Hermes cost doctor
(fail-closed on schema/CLI drift) before any updater/exporter; verify
`hermes kanban show <id> --json` exposes `runs[].metadata.worker_session_id` and the
pinned `state.db` sessions schema; join completed cards to session rows emitting
cost/tokens with provenance; capture disposition at the human review action (not
inferred). Done when: drift fails closed; a joined-cost fixture test passes; missing
session rows counted/reported without corruption; disposition emitted by the review
surface; `cost.jsonl`/`disposition.jsonl` docs describe the real mechanism + limits.
Update ADR-62 + telemetry docs.

**#370 — Pre-file similarity ratchet shadow mode (G6, Tier 3).** Before a claim/
reference note is filed, run a qmd top-3 neighbour check scoped to synthesis/claim
neighbours and surface **report-only** for human confirm/merge/override; warn or
trigger incremental index on stale index; record shadow telemetry for #562.
**No hard block, no auto-merge, no calibrated threshold claim.**

**#379 — Calibration threshold spec for hybrid scores (G6, Tier 3).** Write a threshold
spec — grounded in real data, error-budgeted, drift-bound, shadow-first — covering
candidate-rank, outline-score, and clustering; extend `calibration.yaml` with the new
score thresholds; scores ship only once their thresholds are filled. This is the
gating analysis for #381/#344 (out of scope here).

**#697 — ADR-84 read-only Obsidian Inspector (G7, Tier 3).** Implement per accepted
`docs/adr/84-read-only-obsidian-inspector.md`. Read-only surface; verify in a runtime
vault.

**#713 — ADR-100 exploration-trace capture (G7, Tier 3).** Implement per accepted
`docs/adr/100-exploration-trace-capture.md`.

**#690 — Finish day-1 empty states & starter guidance (G8, Tier 3).** Audit the four
gate dashboards (Inbox/Library/Knowledge/Project) + first-run docs so each explains what
to do when its primary Bases are empty; prefer lightweight callouts over seeded content;
any starter artifact stays schema-valid and covered by golden-copy/drift checks. Done
when: fresh `src/` vault has clear first actions for all four gates; docs + shipped gate
notes agree; new starter artifacts covered by tests.

**#660 — Zotero capture doesn't add to catalog (G8, Tier 3, `bug`).** Reproduce
`capture zotero`, fix so capture writes to the catalog, add a regression test.

**#329 — Obsidian project-management research (G9, Tier 3).** Survey Obsidian PM
plugins + methodologies; for each, short description + adopt/borrow/reject + rationale;
note conflicts with the gate/lifecycle model; summarize concrete Project-space
candidates. Route findings to issues/ADR (not left in `tmp/`).

**#726 — Umbrella (Tier 5).** Stays open until all children close; final acceptance
runs `docs_doctor`, `status_doctor`, `agents_doctor`, `check_test_refs`, `e2e-smoke`,
`pytest tests/` green, and ADR-76 + docs/reference describe the final import/deploy
shape.

## 5. Validation and acceptance

Per the verify-change playbook. Lowest-cost evidence first; paste transcripts into §11.

- **Claim:** Given a fresh checkout, when `pip install -e .` then
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/`, then both succeed and a
  bare import of the core package works without the MCP SDK. *(G1/#727)*
- **Claim:** Given the policy split, when the policy/gate/loudness test suites run, then
  every security invariant in §4/#729 still holds (deny paths, audit, narrowing, hash
  validation). *(G3/#729)*
- **Claim:** Given the diagnostic plane, when an error is logged, then a redacted,
  rotated file appears in the OS state dir and **no** file appears under the vault or a
  committed path; the redaction self-test passes on known-sensitive strings. *(G5/#736)*
- **Claim:** Given pre-file similarity, when a claim note is filed near existing
  neighbours, then top-3 neighbours are surfaced report-only and nothing is auto-merged
  or blocked. *(G6/#370)*
- **Claim:** Given a fresh vault, when each of the four gate dashboards is opened empty,
  then each reads as intentional with a clear first action. *(G8/#690)*
- **Claim:** Given `capture zotero`, when run, then the catalog gains the captured
  entry (regression test green). *(G8/#660)*
- **Prove with:** `scripts/test.sh` selections, `bash scripts/e2e-smoke.sh`,
  `scripts/test-l2.sh` (opt-in), and a fresh-vault GUI pass.

## 6. Idempotence and recovery

- **Safe to re-run:** each issue is an isolated worktree/branch; re-running a session
  from the top re-creates the worktree (`git worktree add` is the only stateful step —
  remove the worktree first if it exists). Refactor PRs preserve behavior, so rebasing
  onto a landed earlier tier is safe.
- **Rollback:** `git worktree remove ~/mv-<slug>` and delete the branch; revert the
  merged PR if a split changed behavior. Compatibility wrappers mean old entrypoints
  keep working if a later tier is reverted.

## 7. Progress

- [x] 2026-06-19 — Release plan + this ExecPlan authored; scope = 17 Ready issues
      (#611 already closed).
- [x] 2026-06-19 — Tier 0 done: milestone `0.1.0-alpha.8` (#9), parent #740, gate
      sub-issues G1 #741 · G2 #742 · G3 #743 · G4 #744 · G5 #745 · G6 #746 · G7 #747 ·
      G8 #748 · G9 #749 (natively linked under #740, on the board as `Ready`); 17 work
      issues assigned to the milestone; release-plan placeholder backfilled.
- [ ] Tier 1 — #727 package spine merged.
- [ ] Tier 2 — #728 shared helpers merged.
- [ ] Tier 3 — #729 #731 #686 #688 #736 #737 #370 #379 #697 #713 #690 #660 #329 merged.
- [ ] Tier 4 — #730 hotspot splits merged.
- [ ] Tier 5 — #726 umbrella closed; close-out sweep done; checkpoint set `complete`.

## 8. Execution log

- 2026-06-19 — Sequenced the refactor strictly behind #727 per the #726 umbrella;
  scheduled observability/feature/UX/CI/research issues in parallel Tier 3 since they
  do not depend on the import-root move. (Architectural decisions remain in their ADRs.)
- 2026-06-19 — Excluded #611 from implementation: it was `Readiness: Ready` on the board
  but already closed on GitHub (2026-06-19); its work folds into the G6 telemetry baseline.

## 9. Surprises & discoveries

- #611 appears `Ready`/`In review` on the project board but is **closed** on GitHub —
  the board Status field and issue open/closed state diverged. Verified via
  `gh issue view 611 --json state`.

## 10. Interfaces & dependencies

- **Import root:** `memoria.*` (introduced by #727) — every later module move imports
  through it. `pyproject.toml` `[project]` metadata + editable install.
- **Shared helpers:** `memoria.runtime.{vaultio,jsonl,time,paths}` (#728) — consumed by
  the #729/#730 splits and diagnostics/cost code.
- **Required CI check names** (`python-selftest`, e2e stage names) — must not change.
- **External:** qmd (retrieval, #370), Hermes CLI `kanban show --json` + pinned
  `state.db` sessions schema (#737), Obsidian bundled-plugin lock (#686), local LLM
  endpoint (#688, qwen2.5:7b default).

## 11. Artifacts & notes

_(Fill with command transcripts + key diffs as each tier lands.)_

## 12. Outcomes & retrospective

_(Filled at close: what shipped, what stayed open → issues, where decisions landed →
ADRs, lessons.)_
