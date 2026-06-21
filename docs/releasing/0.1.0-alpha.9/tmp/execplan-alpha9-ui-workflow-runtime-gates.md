# ExecPlan -- alpha.9 UI/workflow and runtime-gate checkpoint

## 0. Metadata

- **Task:** Run v0.1.0-alpha.9 from draft planning through candidate validation
  and internal-checkpoint closeout.
- **Worktree / branch:** `~/mv-alpha9-release-plan` · `docs/alpha9-release-plan`
  for the planning artifact; implementation slices use one worktree per branch.
- **Related ADRs:** ADR-10, ADR-28, ADR-30, ADR-41, ADR-55, ADR-73, ADR-76,
  ADR-83, ADR-104, ADR-105, ADR-106, and any ADR updated by #827.
- **Related issues / milestone:** Release parent
  [#835](https://github.com/eranroseman/memoria-vault/issues/835);
  gate/stage issues #836-#847; milestone `0.1.0-alpha.9`; work issues #807,
  #822, #823, #824, #826, #827, #828, #832, #833. Design-gated: #829.
- **Started:** 2026-06-21 · **Last updated:** 2026-06-21.

## 1. Purpose / big picture

alpha.9 is the checkpoint that turns the recent UI/workflow work and Hermes/ADR
audits into a validated release unit. A person can see it working when the
Obsidian capture and triage flows behave as documented, the runtime policy gate
blocks capability escapes by mechanism rather than by hidden schemas, accepted
ADRs no longer overclaim what code does, and the release readiness state is
visible in GitHub rather than chat history.

This plan is a tracked working artifact. It lives under
`docs/releasing/0.1.0-alpha.9/tmp/` while alpha.9 is in progress and must be
deleted or moved after closeout disposition.

## 2. Context and orientation

The release prose lives in `docs/releasing/0.1.0-alpha.9/`. Live state lives in
GitHub: parent issue #835 and gate/stage sub-issues #836-#847. The milestone
`0.1.0-alpha.9` owns the release-critical work.

The current alpha.9 scratch inputs are:

| File | Role | Closeout route |
| --- | --- | --- |
| `tmp/hermes-clean-slate-design.md` | Synthesis and change ledger for Hermes usage and gate findings. | Land durable findings in ADRs/docs/issues; delete after U1-U4 are filed or moved. |
| `tmp/hermes-014-utilization-audit.md` | On-box Hermes v0.14 audit. | Route B1-B5 to #822/#823/#824/#832; route A1-A4 to follow-up issues unless #828 pulls them in. |
| `tmp/adr-enforcement-audit.md` | ADR enforcement-mechanism audit. | Fold corrections into #827 and relevant ADR notes. |
| `tmp/adr-implementation-gap-audit.md` | Accepted-ADR implementation audit. | Fold #826/#827/#833 and any ADR text updates into durable docs/issues. |
| `tmp/design-update-recommendations.md` | Measurement-led memory design recommendations. | Keep only decisions backed by baseline data; defer NLI/MaxSAT unless Part 0 justifies it. |
| `tmp/current-state-baseline.md` | Instrument for observed alpha.9 behavior. | Fill from real runs or record that observability is insufficient. |
| `tmp/probe-qwen-compliance.py` | Temporary schema-compliance probe. | Keep only until #828 / measurement disposition; move or delete at closeout. |
| `tmp/spike-nli-vs-cosine.py` | Temporary contradiction spike. | Keep only until baseline disposition; move or delete at closeout. |

Recent merged work that forms the starting state:

- #819 refined Obsidian capture workflows, claim/fleeting forms, Bases title
  links, Zotero citekey selection, cspell dev dependency, and the test-vault
  refresh helper.
- #820 corrected enforcement-attribution prose and "enforcement is a mechanism"
  guidance.
- #821 folded 0.14 utilization and 0.17 probe findings into the clean-slate
  design.
- #825 completed the direct-capability denylist `process` fix and contract
  doctor slice.
- #830 folded ADR-83/30/55 implementation-gap notes into design docs.
- #831 rewrote the Hermes-usage audit as a readable record and ledger.
- #834 folded the adversarial critique round into the audit and ledger.

## 3. Plan of work

First, keep the release planning structure accurate: parent issue #835, gate and
stage sub-issues #836-#847, and the `0.1.0-alpha.9` milestone remain the only
live readiness state. Update the release plan when definitions change, not when
state changes.

Second, implement the release gates in dependency order. Close the live P0
interim first (#832), because #822's structural default-deny rewrite is larger
and must not block the immediate egress/messaging hard-deny. Pair it with #823
so a missing policy plugin cannot silently turn the gate into a label. Then
resolve #826 because superseded-claim reuse is a correctness gap in the
query/write path. After those, land #827/#833 so accepted ADRs and docs are
truthful and drift detection starts with the highest-risk claims. Decide #828
before candidate validation so release docs do not mix 0.14 on-box truth with
0.17 isolated-source claims.

Third, validate the user-facing Obsidian workflows end to end. #807 stays open
until every original UI finding is either fixed, already resolved by a merged PR,
or explicitly deferred with a reason. Refresh `~/Memoria-test`, run golden
restore, and open the changed Obsidian surfaces for S5.

Finally, disposition every alpha.9 `tmp/` artifact before closeout. Implemented
findings move into ADRs/docs/tests/issue evidence; unfinished findings move to
the next release `tmp/` or a GitHub issue; temporary scripts are deleted after
their result is recorded.

## 4. Concrete steps

1. **Isolate each implementation session** (`AGENTS.md`):

   ```bash
   git fetch origin
   git worktree add ~/mv-alpha9-<slice> -b <type>/alpha9-<slice> origin/main
   cd ~/mv-alpha9-<slice>
   ```

   Expected output: a clean worktree on a branch that tracks `origin/main`.

2. **Confirm release state anchors.**

   ```bash
   gh issue view 835 --json state,milestone,title
   gh api repos/eranroseman/memoria-vault/issues/835/sub_issues --jq '.[].number'
   gh issue list --milestone 0.1.0-alpha.9 --state open --json number,title
   ```

   Expected output: #835 is open with milestone `0.1.0-alpha.9`; sub-issues list
   #836-#847; release-critical work issues are on the milestone.

3. **Implement G2 before broader structural work.**

   Resolve #832 first: hard-deny egress/messaging/browser/web/image/computer-use
   tool families in the policy gate, update contract-doctor expectations, redeploy
   to `~/Memoria-test`, and add a deploy-freshness check. Then resolve #823 with a
   startup or runtime assertion that a lane refuses work when the gate plugin is
   absent. Record S4 evidence in #846.

4. **Implement G3 supersession correctness.**

   Resolve #826 by filtering superseded claims out of query/write defaults while
   preserving explicit historical retrieval. Add component tests and replay the
   relevant workflow. Record evidence in #838 and #845.

5. **Implement G4 ADR/docs truth alignment.**

   Resolve #827 by updating stale ADR prose to match code, not the other way
   around, unless the issue explicitly calls for code. Start #833 with the
   smallest useful drift-doctor slice: accepted ADRs that name a concrete command,
   file, check, or path. Record evidence in #839.

6. **Decide G5 runtime version.**

   Resolve #828 by either testing Hermes 0.17 under an isolated `HERMES_HOME` and
   recording the checks, or documenting the stay-on-0.14 decision. Rerun contract
   and cost checks for the chosen path.

7. **Close G1 UI/workflow acceptance.**

   Review every numbered item in #807 against current source and `~/Memoria-test`.
   Close the issue only after each item is fixed, linked to a merged PR, or
   explicitly deferred.

8. **Run validation stages.**

   ```bash
   python scripts/docs_doctor.py docs
   python scripts/status_doctor.py
   python scripts/check_test_refs.py
   node_modules/.bin/cspell lint --no-progress --no-must-find-files --gitignore docs/releasing docs/testing
   git diff --check
   PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests -q
   ```

   Expected output: every command exits 0. Add S2-S5 runtime transcripts to
   #844-#847.

9. **Close the checkpoint.**

   Update `release-plan-0.1.0-alpha.9.md` to `status: complete`,
   `released: false`; disposition all `tmp/` files; close #835 and the milestone;
   merge through PR; delete the remote branch; remove the task worktree; fast-forward
   `/home/eranr/memoria-vault`.

## 5. Validation and acceptance

- **Claim:** Given a clean checkout, when S0 and S1 commands run, then docs,
  release status, test references, spelling, and component tests are green.
- **Claim:** Given `~/Memoria-test` refreshed from `src/`, when S2 runs, then
  golden restore reports zero drift and changed plugin/workflow config matches
  source.
- **Claim:** Given a disabled capability tool is invoked by name, when S4 runs,
  then the policy gate blocks it and writes a deny/audit record; the result does
  not depend on `agent.disabled_toolsets` hiding the schema.
- **Claim:** Given a superseded claim exists, when normal query/write paths run,
  then the superseded claim is excluded by default and included only under an
  explicit historical request.
- **Claim:** Given Obsidian opens the test vault, when S5 runs, then the UI
  surfaces from #807 behave as documented.

## 6. Idempotence and recovery

- **Safe to re-run:** docs checks, pytest, contract doctors, `refresh-test-vault`
  against `~/Memoria-test`, and golden restore checks are repeatable.
- **Rollback:** revert the PR for repository changes; for GitHub state, reopen or
  reassign issues rather than deleting evidence. If a task worktree becomes dirty
  or wrong, preserve changes with `git stash push -u -m wip` before removal.
- **No production mutation:** all runtime checks use `~/Memoria-test`, an isolated
  `HERMES_HOME`, or a disposable vault. Never test against `~/Memoria`.

## 7. Progress

- [x] 2026-06-21 -- Release parent #835, gate issues #836-#841, stage issues
  #842-#847, and milestone assignments created.
- [x] 2026-06-21 -- Draft release README, release plan, and ExecPlan authored.
- [ ] G2 -- Capability-boundary hardening implemented and verified.
- [ ] G3 -- Supersession correctness implemented and verified.
- [ ] G4 -- ADR/docs reconciliation implemented and verified.
- [ ] G5 -- Runtime-version decision recorded and verified.
- [ ] G1/G6 -- UI workflow and docs integrity accepted.
- [ ] Closeout -- tmp disposition complete; release parent and milestone closed.

## 8. Execution log

- 2026-06-21 -- Treat #832 and #823 as release-blocking because the audits describe
  a live capability-boundary P0 and fail-open path. #822 remains the structural
  follow-through and must not delay the interim mitigation.
- 2026-06-21 -- #832 closed via PR #849: egress/messaging/browser/computer-use/media
  tools are hard-denied in the policy gate; the contract doctor now checks covered
  egress tools and deployed `policy_hook.py` freshness; `~/Memoria-test` was
  refreshed and the deployed writer gate blocked `mcp_x__web_search` by name.
- 2026-06-21 -- #823 closed via PR #850: profile deployment refuses a missing policy
  plugin source, shipped profile configs are test-pinned to enable
  `memoria-policy-gate`, and a broken `policy_hook` import blocks failed-closed.
- 2026-06-21 -- G3 implementation path chosen for #826: wrap the qmd MCP with a
  Memoria-owned `qmd_filter_mcp.py` that preserves the existing qmd tool surface
  while filtering claim notes whose frontmatter has `superseded_by`, unless the
  caller passes `include_superseded=True` for historical lookup.
- 2026-06-21 -- Keep #829 out of the milestone unless Part 0 baseline shows
  supervision attribution is the release-critical bottleneck.
- 2026-06-21 -- Use GitHub sub-issues for gate/stage readiness and keep this file
  as prose plus execution guidance, not a state table.

## 9. Surprises & discoveries

- 2026-06-21 -- The alpha.9 milestone existed but only #807 was assigned before
  release planning; #822-#833 were open and unmilesoned.
- 2026-06-21 -- `gh issue` has no sub-issue helper, but the REST
  `/issues/{issue_number}/sub_issues` endpoint accepts numeric `sub_issue_id`, so
  #836-#847 were attached to #835 through `gh api`.

## 10. Interfaces & dependencies

- **Release state:** GitHub milestone `0.1.0-alpha.9`; parent issue #835; gate/stage
  sub-issues #836-#847.
- **Release docs:** `docs/releasing/0.1.0-alpha.9/README.md` and
  `docs/releasing/0.1.0-alpha.9/release-plan-0.1.0-alpha.9.md`.
- **Policy gate:** `src/.memoria/plugins/memoria-policy-gate/` and
  `src/.memoria/mcp/policy_hook.py`; runtime contract checked by the Hermes
  contract doctor and live S4 evidence.
- **Runtime vault:** `~/Memoria-test` only; production vault stays untouched.
- **Validation commands:** docs doctor, status doctor, check-test-refs, cspell,
  pytest, golden restore, and attended GUI checks.

## 11. Artifacts & notes

- Release parent:
  `https://github.com/eranroseman/memoria-vault/issues/835`.
- Gates: #836, #837, #838, #839, #840, #841.
- Stages: #842, #843, #844, #845, #846, #847.
- Release-critical work issues now on the milestone: #807, #822, #823, #824,
  #826, #827, #828, #832, #833.

## 12. Outcomes & retrospective

- **Shipped:** fill at checkpoint closeout.
- **Still open:** fill with rolled-forward issues at checkpoint closeout.
- **Routed to:** ADRs, docs, issue comments, and validation evidence under #835.
- **Lessons:** fill after S5 and tmp disposition.
