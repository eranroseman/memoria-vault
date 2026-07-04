---
title: 0.1.0-alpha.8 validation log
parent: 0.1.0-alpha.8
grand_parent: Releasing
---

# 0.1.0-alpha.8 validation log

alpha.8 closed as an internal untagged checkpoint on June 20, 2026. Evidence lives
primarily in the gate/stage sub-issues under
[Release 0.1.0-alpha.8](https://github.com/eranroseman/memoria-vault/issues/740);
this file preserves the curated closeout summary.

## Automated and Headless Stages

- S0 static-contract: `docs_doctor`, `status_doctor`, `agents_doctor`,
  `check_test_refs`, ADR index check, plugin provenance doctor, cspell, and editable
  install metadata all passed from a clean validation worktree.
- S1 component: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/` passed
  with 436 tests.
- S2 vault-assembly: `bash scripts/e2e-smoke.sh` passed.
- S3 workflow-replay: model-free replay evidence was recorded on the stage issue.
- S4 runtime-integration: `bash scripts/test-l2.sh` passed outside the restricted
  sandbox. The smoke endpoint, live Hermes dispatch, filesystem-backed Obsidian MCP
  shim, written artifact, and policy-gate audit rows were all asserted.

## Fresh-Vault Acceptance

S5 used a disposable vault at `/tmp/memoria-alpha8-s5-vault` and an isolated
`HERMES_HOME=/tmp/memoria-alpha8-s5-hermes`.

- The installer completed with `MEMORIA_ENV=test bash scripts/install.sh --yes
  --no-apps --vault /tmp/memoria-alpha8-s5-vault`.
- The disposable vault was initialized as a Git repository, committed, and given a
  local upstream at `/tmp/memoria-alpha8-s5-remote.git` so Obsidian Git could sync
  without the "No upstream-branch is set" failure.
- Five temp Hermes profiles installed under the isolated Hermes home.
- The Inspector plugin, Zotero capture script, exploration-trace script, QuickAdd
  command bindings, and four space empty states were present in the fresh vault.
- S5 was operator-accepted after the disposable vault's Obsidian Git upstream was
  fixed. The preserved machine evidence covers the installer, profile, plugin,
  script, QuickAdd, and empty-state surfaces; no separate checklist-level GUI run
  sheet was preserved beyond the S5 issue comments.

## Closeout

- All G1-G9 gate issues and S0-S5 stage issues closed.
- The release parent checklist was updated so only completed items are checked.
- The alpha.8 milestone had no remaining open issues.
- The tracked `tmp/` ExecPlan was deleted after durable content was routed to ADRs,
  docs, and issues.
- This checkpoint did not cut a tag or GitHub Release; `released: false` remains
  intentional.
