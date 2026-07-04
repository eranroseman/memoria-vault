# ExecPlan -- alpha.10 Hermes upgrade and measurement-led cleanup

## 0. Metadata

- **Task:** Run v0.1.0-alpha.10 from draft planning through candidate validation
  and internal-checkpoint closeout: land the Hermes 0.17 upgrade acceptance,
  fill the #859 baseline, and implement only the cleanup items that the baseline
  and the reconciled 0.17 eval prove pay for themselves.
- **Worktree / branch:** one worktree per slice
  (`git worktree add ~/mv-alpha10-<slice> -b <type>/alpha10-<slice> origin/main`);
  never mutate the primary checkout's branch.
- **Related ADRs:** ADR-22 (lane/MCP-only bet, reaffirmed by the eval), ADR-30
  (deterministic ingest), ADR-31 (native Obsidian MCP), ADR-105 (diagnostic
  plane), ADR-106 (cost capture), plus any ADR touched by a selected cleanup item.
- **Related issues / milestone:** carryover
  [#859](https://github.com/eranroseman/memoria-vault/issues/859); milestone
  `0.1.0-alpha.10`. Release parent and gate/stage sub-issues to be created when
  scope is shaped (none exist yet).
- **Started:** 2026-06-22 · **Last updated:** 2026-06-22.

## 1. Purpose / big picture

alpha.10 turns the in-place Hermes 0.17 upgrade into a validated checkpoint and
uses observed usage to decide which Hermes/memory cleanup is worth doing now. A
person can see it working when: the upgraded runtime passes its full acceptance
(not just the doctors), the #859 baseline records whether memory/retrieval/
contradiction/ingest is actually a bottleneck, and any cleanup that lands is one
the eval confirmed feasible on this install rather than a speculative rewrite.

This plan is a tracked working artifact. It lives under
`docs/releasing/0.1.0-alpha.10/tmp/` while alpha.10 is in progress and must be
deleted or moved after closeout disposition.

## 2. Context and orientation

Release prose lives in `docs/releasing/0.1.0-alpha.10/`. Live readiness state
will live in GitHub once the release parent and gate/stage sub-issues exist.

Scratch inputs carried into this release:

| File | Role | Closeout route |
| --- | --- | --- |
| `tmp/hermes-upgrade.md` | 0.14 -> 0.17 upgrade record and acceptance checklist. | Finish the two un-rerun acceptance lines; fold the durable decision into the release plan / ADR note; delete. |
| `tmp/hermes-017-feature-eval-claude.md` | Reconciled (Codex + source-verified) 0.17 feature eval and ranked recommendations. | Keep ranked recs that #859 selects; route each selected item to an issue/ADR; delete the report at closeout. |
| `tmp/hermes-017-feature-eval-codex.md` | Codex-authored eval copy (operational breadth). | Superseded by the reconciled report; delete at closeout. |
| `tmp/hermes-017-feature-eval.md` | Earlier single-author eval. | Superseded by the reconciled report; delete at closeout. |
| `tmp/hermes-017-recommendations.md` | Kilo / Bitwarden / multiplexing recommendation detail. | Fold selected items into issues; delete at closeout. |
| `tmp/current-state-baseline.md` | The #859 evidence instrument. | Fill from real runs; record the scope decision in #859; delete after the decision lands. |
| `tmp/probe-qwen-compliance.py` | Schema-compliance smoke probe. | Keep until measurement disposition; delete or move at closeout. |
| `tmp/spike-nli-vs-cosine.py` | Contradiction spike. | Keep until baseline disposition; delete or move at closeout. |

Starting state (from `tmp/hermes-upgrade.md`, 2026-06-22):

- `hermes --version` -> v0.17.0, up to date.
- `hermes_contract_doctor.py --json` -> `ok: true` (warning: dead denylist
  names `code_execution`, `run_command`, `send_message`).
- `board_export.py --cost-doctor` -> `ok: true` for copi/librarian/writer.
- **Not yet rerun:** clean profile redeploy to `~/Memoria-test`; one live
  direct-tool deny + one Obsidian/MCP smoke pass.
- `hermes doctor` flags stale default-profile config: unknown provider `ollama`,
  config version `v23 -> v30`.

## 3. Plan of work

First, keep the release planning structure accurate. The release plan and (once
created) parent/gate/stage issues are the only live readiness state. Production
Memoria runs Kilo; the local `provider: custom` / `qwen2.5:7b` render is
test-vault evidence, not the production target — do not infer production
strategy from it. All runtime work uses `~/Memoria-test`, never `~/Memoria`.

Second, finish the upgrade acceptance (G2). The doctors already pass; the open
items are a clean profile redeploy to the test vault and one live deny + one
Obsidian/MCP smoke pass. This gates everything else: no cleanup lands on an
unaccepted runtime.

Third, fill the #859 baseline (G1) before building any memory machinery. If
stale facts / missed contradictions / retrieval misses / extraction errors are
not top issues, the NLI/MaxSAT and warrant-checker work stays deferred and the
baseline says so explicitly. Run the cheap checks the issue names (qmd
rerank-on vs -off over ~20 real queries; sample approve/reject correctness).

Fourth, land only confirmed-feasible Hermes hygiene (G3). The reconciled eval
verified two items on-box, so they are no longer speculative: cost capture via
the `post_llm_call` hook (carries tokens + `cost_details.total`) and the
positive `platform_toolsets` allowlist (`hermes_cli/tools_config.py`). Pair those
with the pure-hygiene config migration (`v23 -> v30`, remove stale `ollama`) and
the config-only auxiliary slots + per-lane `reasoning_effort`.

Fifth, treat the larger items as pilots, not committed scope (G4): Bitwarden for
shared secrets and `gateway.multiplex_profiles` in `Memoria-test`, plus adding
`hermes security audit` to release validation. Pilot in the test vault; promote
nothing without the post-change re-run below. Anything #859 does not select
stays out of scope.

Finally, disposition every `tmp/` artifact at closeout: selected findings move
to ADRs/issues, the reconciled eval's superseded copies are deleted, scripts are
deleted after their result is recorded.

## 4. Concrete steps

1. **Isolate each session** (`AGENTS.md` §4):

   ```bash
   git fetch origin
   git worktree add ~/mv-alpha10-<slice> -b <type>/alpha10-<slice> origin/main
   cd ~/mv-alpha10-<slice>
   ```

   Expected: clean worktree tracking `origin/main`.

2. **Finish G2 upgrade acceptance.**

   ```bash
   # redeploy profiles to the SANDBOX vault only
   <profile redeploy command> --vault /home/eranr/Memoria-test
   python src/.memoria/mcp/hermes_contract_doctor.py --vault /home/eranr/Memoria-test --json
   python src/.memoria/mcp/board_export.py --cost-doctor
   ```

   Then run one live direct-tool deny (invoke a disabled capability by name and
   confirm a deny/audit record) and one Obsidian/MCP smoke pass. Record both in
   `tmp/hermes-upgrade.md` and the G2 stage issue.

3. **Fill G1 baseline.** Complete `tmp/current-state-baseline.md` from observed
   use. Run the qmd rerank-on vs -off comparison over ~20 known-target queries
   and the approve/reject correctness sample. Record the scope decision in #859:
   for each candidate (warrant checker, contradiction machinery, retrieval
   tuning, each Hermes cleanup item) mark **scope alpha.10 / defer / kill**.

4. **Land G3 confirmed hygiene** (only items G1 keeps):
   - Migrate Hermes config to the 0.17 schema; remove stale `ollama` from the
     default profile (`hermes doctor` clean).
   - Switch profile gating to `platform_toolsets`; run the policy deny-path tests
     to confirm new upstream toolsets stay closed by default.
   - Set cheap auxiliary slots (title/compression/MCP-routing/approval/curator)
     and per-lane `reasoning_effort` (low/none deterministic, high only for
     Writer/Peer-reviewer).

5. **Decide G4 cost-capture + pilots** (only items G1 keeps):
   - Spike ADR-106 cost capture in the gate plugin's `post_llm_call` hook;
     decide relocate-vs-keep the `state.db` join and record it on ADR-106.
   - Pilot `gateway.multiplex_profiles: true` and Bitwarden shared secrets in
     `Memoria-test`; verify profile startup. Not a security boundary — kanban
     lane isolation and the policy gate stay unchanged.
   - Add `hermes security audit` to release/runbook validation.

6. **Run validation stages.**

   ```bash
   python scripts/docs_doctor.py docs
   python scripts/status_doctor.py
   python scripts/check_test_refs.py
   node_modules/.bin/cspell lint --no-progress --no-must-find-files --gitignore docs/releasing docs/testing
   git diff --check
   PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests -q
   ```

   Expected: every command exits 0.

7. **Close the checkpoint.** Set `release-plan-0.1.0-alpha.10.md` to
   `status: complete`, `released: false`; disposition all `tmp/` files; close the
   release parent and milestone; merge through PR; delete the remote branch;
   remove the task worktree. Do not cut a tag or GitHub Release.

## 5. Validation and acceptance

- **Claim:** Given the upgraded runtime, when G2 runs, then profiles redeploy
  cleanly to `~/Memoria-test`, the contract and cost doctors pass, and one live
  deny + one Obsidian/MCP smoke pass succeed.
- **Claim:** Given two weeks of observed use, when G1 is filled, then #859 records
  whether memory is the bottleneck and marks every candidate scope/defer/kill.
- **Claim:** Given a disabled capability invoked by name, when `platform_toolsets`
  is active, then the gate blocks it and the deny-path tests confirm new upstream
  toolsets are closed by default — not merely hidden.
- **Claim:** Given a model call completes, when the `post_llm_call` cost spike
  runs, then the hook payload yields tokens + `cost_details.total` matching the
  current session-store figure (so relocation is safe).
- **Claim:** Given a clean checkout, when the S0 stage runs, then docs, status,
  test refs, spelling, and component tests are green.

## 6. Idempotence and recovery

- **Safe to re-run:** docs/status checks, pytest, contract/cost doctors, profile
  redeploy and golden restore against `~/Memoria-test`.
- **Rollback:** revert the PR for repository changes; reopen/reassign issues
  rather than deleting evidence. Stash with `git stash push -u` before removing a
  dirty worktree.
- **No production mutation:** every runtime check uses `~/Memoria-test`, an
  isolated `HERMES_HOME`, or a disposable vault. Never test against `~/Memoria`.
  Bitwarden/multiplex pilots stay in the test vault until a separate decision
  promotes them.

## 7. Progress

- [x] 2026-06-22 -- Hermes upgraded 0.14 -> 0.17; contract doctor and cost doctor
  pass; reconciled 0.17 feature eval recorded.
- [x] 2026-06-22 -- Draft release plan and this ExecPlan authored.
- [ ] G2 -- Upgrade acceptance finished (profile redeploy + live deny + MCP smoke).
- [ ] G1 -- #859 baseline filled and scope decision recorded.
- [ ] G3 -- Confirmed Hermes hygiene landed (config migration, `platform_toolsets`,
  auxiliary slots + `reasoning_effort`) for items G1 keeps.
- [ ] G4 -- Cost-capture decision + Bitwarden/multiplex pilots + security audit
  for items G1 keeps.
- [ ] Closeout -- `tmp/` disposition complete; checkpoint set complete.
