---
release: v0.1.0-alpha.9
status: complete     # draft | candidate | complete | released
released: false      # machine cut-flag; true ONLY for a formal tagged release
title: Release plan -- v0.1.0-alpha.9
parent: Releasing
nav_order: 2
---

# Release plan -- v0.1.0-alpha.9

**Current status: complete internal checkpoint.** alpha.9 is the
**UI/workflow and runtime-gate** checkpoint. It is not a formal release: no
release-please PR, no tag, and no GitHub Release. The checkpoint is complete:
the Obsidian workflow fixes, policy-gate capability boundary, and ADR/code/docs
reconciliation were validated against the running system.

## 1. Scope -- what this release is

alpha.9 delivers the workflow and integrity corrections surfaced by the UI review
and the Hermes/ADR audits. It lands or explicitly dispositions: the Obsidian
capture/triage workflow review in
[#807](https://github.com/eranroseman/memoria-vault/issues/807), the live
capability-boundary hardening in
[#832](https://github.com/eranroseman/memoria-vault/issues/832) /
[#823](https://github.com/eranroseman/memoria-vault/issues/823) /
[#822](https://github.com/eranroseman/memoria-vault/issues/822), the
supersession correctness gap in
[#826](https://github.com/eranroseman/memoria-vault/issues/826), the ADR and docs
truth-alignment batch in
[#827](https://github.com/eranroseman/memoria-vault/issues/827) /
[#833](https://github.com/eranroseman/memoria-vault/issues/833), and the
Hermes-runtime version decision in
[#828](https://github.com/eranroseman/memoria-vault/issues/828). The boundary:
alpha.9 is an internal checkpoint for UI/workflow reliability and runtime
guardrails, not the NLI/MaxSAT contradiction engine, not an autonomous
contradiction linker, and not a formal public release.

## 2. Definition of done -- gates

v0.1.0-alpha.9 ships when **every gate sub-issue under
[Release v0.1.0-alpha.9](https://github.com/eranroseman/memoria-vault/issues/835)
is closed**. Each gate is a yes/no verdict; state and evidence live in the issue,
not in this file.

| Gate | Proves | Verified by | Gate issue |
| --- | --- | --- | --- |
| G1 | **UI/workflow acceptance.** #807 is closed, or every finding has an explicit disposition; Commander/QuickAdd forms, Bases title links, Zotero selection, Inbox links, and claim/fleeting actions match docs and runtime config. | S2 + S5 | [#836](https://github.com/eranroseman/memoria-vault/issues/836) |
| G2 | **Capability-boundary hardening.** #832 lands the interim egress/messaging hard-deny and deploy-freshness check; #823 mitigates the plugin-registration fail-open; #822 has a structural gate decision and test path. | S1 + S4 | [#837](https://github.com/eranroseman/memoria-vault/issues/837) |
| G3 | **Supersession correctness.** #826 resolves the ADR-10 partial: query/write exclude superseded claims by default while explicit historical retrieval remains possible. | S1 + S3 | [#838](https://github.com/eranroseman/memoria-vault/issues/838) |
| G4 | **ADR/docs reconciliation.** #827 lands the stale ADR text/code batch; #833 ships the first ADR-code drift-doctor slice or records an explicit deferral with rationale. | S0 + S1 | [#839](https://github.com/eranroseman/memoria-vault/issues/839) |
| G5 | **Runtime-version decision.** #828 is decided: alpha.9 stays on the installed Hermes v0.14.0 runtime; the contract and cost doctors pass on that path, and 0.17 isolated-source findings remain below on-box truth until a later upgrade checkpoint. | S2 + S4 | [#840](https://github.com/eranroseman/memoria-vault/issues/840) |
| G6 | **Documentation integrity.** Changed behavior is covered in how-to/reference/explanation docs, ADRs, and release docs; every alpha.9 `tmp/` file has a closeout disposition. | S0 + manual docs sweep | [#841](https://github.com/eranroseman/memoria-vault/issues/841) |

## 3. Validation -- stages

The staged test plan that turns `shipped` into `approved`. A release candidate
must re-run **all stages green from a fresh clone** on a clean target box and
record evidence in the stage sub-issues under
[Release v0.1.0-alpha.9](https://github.com/eranroseman/memoria-vault/issues/835).

| Stage | Proves | Stage issue |
| --- | --- | --- |
| S0 | `static-contract`: docs, status, ADR-code mechanism claims, test references, spelling, markdown structure, plugin provenance, and release-plan links are clean. | [#842](https://github.com/eranroseman/memoria-vault/issues/842) |
| S1 | `component`: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests -q` is green, including any new policy, docs, status, or workflow-script tests. | [#843](https://github.com/eranroseman/memoria-vault/issues/843) |
| S2 | `vault-assembly`: `~/Memoria-test` refreshes from `src/`; golden restore and plugin/config provenance checks pass after the alpha.9 changes. | [#844](https://github.com/eranroseman/memoria-vault/issues/844) |
| S3 | `workflow-replay`: model-free replay proves capture, triage, delegated work, policy deny, and artifact assertions for changed alpha.9 paths. | [#845](https://github.com/eranroseman/memoria-vault/issues/845) |
| S4 | `runtime-integration`: live gate-contract checks prove disabled-tool invocation by name is blocked by the gate; gate registration/freshness and deny audit rows are observed. | [#846](https://github.com/eranroseman/memoria-vault/issues/846) |
| S5 | `release-acceptance`: attended Obsidian pass verifies space navigation, Commander/ribbon/page-header commands, capture forms, Zotero capture, Inbox queues, and Bases links. | [#847](https://github.com/eranroseman/memoria-vault/issues/847) |

## 4. Blockers

Not enumerated here as a second state list. By definition the blockers are any
open gate/stage sub-issue under
[Release v0.1.0-alpha.9](https://github.com/eranroseman/memoria-vault/issues/835),
any open issue assigned to the `0.1.0-alpha.9` milestone, and any open
High-priority blocker in the
[Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1).

## 5. Out of scope (later)

- The full NLI/decomposed-gate/MaxSAT contradiction engine is deferred unless
  `current-state-baseline.md` proves contradiction misses are costly enough to
  spend the supervision budget.
- #829 remains a redesign item gated on observed approve/reject data. It does
  not block alpha.9 unless Part 0 of the baseline shows supervision attribution
  is the release-critical bottleneck.
- Bitwarden adoption, auxiliary model routing, and `reasoning_effort` tuning from
  the Hermes utilization audit are optional follow-ups unless #828 chooses a
  runtime path that makes them necessary for alpha.9.
- Cross-vault read-only sharing, native release tags, tarball/signing delivery,
  and projected-canvas work remain outside this checkpoint.

## 6. Known limitations (state in the release notes)

- Limitation: alpha.9 is an **internal checkpoint**, not a tagged release. Impact:
  users should not look for a GitHub Release or release-please changelog entry.
  Workaround: use the merged PRs and this release plan as the checkpoint record.
  Tracking: [#835](https://github.com/eranroseman/memoria-vault/issues/835).
- Limitation: contradiction automation stays **soft/propose-only** unless real
  baseline data changes the priority. Impact: the PI may still see possible
  conflicts as review prompts, not automatic supersession. Workaround: use the
  existing contradictions dashboard and explicit review. Tracking:
  [#826](https://github.com/eranroseman/memoria-vault/issues/826) and
  [#829](https://github.com/eranroseman/memoria-vault/issues/829).
- Limitation: alpha.9 stays on the installed **Hermes v0.14.0** runtime. Impact:
  0.17 isolated-source findings remain below on-box truth and must not be described
  as deployed behavior. Workaround: label claims by evidence rung in docs and ADRs;
  run the upgrade as its own checkpoint with the contract and cost doctors before
  adopting 0.17 behavior. Tracking:
  [#828](https://github.com/eranroseman/memoria-vault/issues/828).

## 7. Documentation integrity

Before the release candidate is approved, complete a fresh documentation sweep:

1. **Coverage:** changed UI/workflow behavior, gate behavior, runtime-version
   direction, supersession behavior, and ADR/docs reconciliation have current
   how-to or reference coverage, with explanation docs updated when the "why"
   changed.
2. **Single source of truth:** release state lives in #835 and its sub-issues;
   this file holds definitions and prose only. Repeated gate/stage details in
   other docs must point back here or to the issue trail.
3. **Diataxis placement and indexing:** release docs stay under
   `docs/releasing/`; user workflow changes update `docs/how-to-guides/` and
   exact command/config changes update `docs/reference/`.
4. **Related links and terminology:** updated pages link to the release issue,
   relevant ADRs, and the owning reference/how-to pages; stale "gate",
   "space", "workflow", "runtime", and "accepted" wording is corrected.
5. **Third-party and runtime claims:** Hermes version claims cite #828 evidence;
   Obsidian plugin and Commander/QuickAdd claims are verified against `src/`.
6. **ADR capture:** durable decisions from the alpha.9 audits land in ADRs or
   existing ADR notes, never only in release `tmp/`.

Record findings in [#841](https://github.com/eranroseman/memoria-vault/issues/841)
or a companion docs PR. Required checker summary: `docs_doctor`,
`status_doctor`, `adr_code_doctor`, `check_test_refs`, cspell, and any manual
full-scope scan.

## 8. Runtime readiness

alpha.9 must record runtime evidence for:

1. **Fresh clone:** S0/S1 pass from a clean checkout.
2. **Installer or sandbox target:** `~/Memoria-test` refreshes after source-owned
   changes; golden restore check is clean.
3. **Policy gate:** the live deployed gate matches source, sees every tool call,
   and blocks known-deny capability invocations by name.
4. **Hermes runtime:** #828 records the stay-on-0.14 decision with rerun
   contract/cost checks; no 0.17 behavior is claimed as deployed in alpha.9.
5. **Obsidian GUI:** changed Commander, QuickAdd, Bases, Inbox, Zotero, fleeting,
   and claim workflows are opened and checked in a runtime or disposable vault.
6. **No production vault mutation:** `memoria-private` remains hands-off; runtime
   acceptance uses `~/Memoria-test` or a disposable vault.

## 9. Release close-out sweep

Before closing this internal checkpoint:

1. Review every tracked file in `docs/releasing/0.1.0-alpha.9/tmp/`.
2. Fold implemented findings into ADRs, reference/how-to/explanation docs, tests,
   or issue comments.
3. Move unfinished scratch forward to the next release `tmp/` or a GitHub issue.
4. Delete only scratch whose durable content has landed elsewhere.
5. Close or roll forward release-critical issues, close #835, and close or roll
   the `0.1.0-alpha.9` milestone.
6. Confirm worktree/branch hygiene: PR merged, remote branch deleted, task
   worktree removed, and the dedicated main checkout fast-forwarded cleanly.

## 10. Cut procedure

This checkpoint follows the untagged internal path:

1. Every gate and stage sub-issue under #835 is closed; required CI is green on
   `main`; no open High-priority blocker remains.
2. Re-run all stages from a fresh clone or clean target and record evidence in
   #842 through #847.
3. Complete the documentation integrity, runtime readiness, and close-out sweeps.
4. Do not cut a tag or GitHub Release. Set this plan to `status: complete`,
   `released: false` after #835 is closed.
5. Close the milestone, rolling unfinished issues to the next checkpoint.

## 11. Roadmap after this release

| Phase | When | Goal |
| --- | --- | --- |
| Structural capability boundary | After #832 interim mitigation | Finish #822 default-deny/per-lane allowlist and keep contract-doctor coverage current. |
| ADR drift prevention | After the first #833 slice | Expand the drift doctor from high-risk accepted ADRs to every accepted ADR with concrete mechanism claims. |
| Measurement-led memory work | After `current-state-baseline.md` is filled | Decide whether contradiction, retrieval, ingest, or supervision attribution is the next real bottleneck. |
| Runtime upgrade path | After #828 | Either graduate 0.17 features to on-box truth or document the 0.14 hardening path. |

## 12. Appendix -- working artifacts

alpha.9 working artifacts were handled at closeout: implemented findings
landed in ADRs, docs, tests, PRs, or issue evidence, and the tracked `tmp/`
files were deleted.
