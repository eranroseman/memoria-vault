---
title: 0.1.0-alpha.10 validation log
parent: 0.1.0-alpha.10
grand_parent: Releasing
nav_order: 3
---

# 0.1.0-alpha.10 validation log

Date: 2026-06-23

Candidate commit: `f2cbecda` (`release/execute-alpha10`), clean worktree at
verification time.

## Automated gates

`scripts/verify rc --evidence-dir /tmp/memoria-alpha10-rc-f2cbecda` passed.

- Source Gate: `bash scripts/test.sh all` passed, including `494 passed` for
  `tests/`, ruff, formatting, docs doctor, links, ADR/code doctor, agents doctor,
  GitHub/ruleset/provenance doctors, test-reference checks, Python compile, shell
  checks, and dashboard/design drift checks.
- Package Gate: `bash scripts/e2e-smoke.sh` passed. The disposable vault
  assembled cleanly, golden-copy drift was zero, commit hooks blocked the
  malformed fixture and accepted the valid fixture, offline ingest succeeded,
  workflow replay reached the model-free path, and final integrity was green.
- Runtime Gate: `bash scripts/test-l2.sh` passed with Hermes live dispatch
  through the filesystem-backed Obsidian MCP shim. It asserted
  `projects/l2-smoke/live-dispatch.md` and a policy-gate audit row for task
  `53688d3f-af88-4c68-8cef-ddb768d8b0dc`.

Host evidence in the RC summary:

- Hermes: `Hermes Agent v0.17.0 (2026.6.19)`, upstream `74265c8e`.
- Platform: WSL2 Linux `6.6.87.2-microsoft-standard-WSL2`, Python `3.13.12`.
- Evidence file: `/tmp/memoria-alpha10-rc-f2cbecda/summary.json`.

## Test-vault runtime

`scripts/refresh-test-vault.sh --vault /home/eranr/Memoria-test --profiles always`
passed and redeployed all five profiles from the alpha.10 candidate.

Deployed runtime doctors passed from the test-vault venv:

- `/home/eranr/Memoria-test/.memoria/.venv/bin/python
  /home/eranr/Memoria-test/.memoria/mcp/board_export.py --vault
  /home/eranr/Memoria-test --cost-doctor` passed for `memoria-copi`,
  `memoria-librarian`, and `memoria-writer`.
- `/home/eranr/Memoria-test/.memoria/.venv/bin/python
  /home/eranr/Memoria-test/.memoria/mcp/hermes_contract_doctor.py --vault
  /home/eranr/Memoria-test` passed: all 42 covered direct/egress tools were
  hard-denied. The dead-denylist warning for `code_execution`, `run_command`,
  and `send_message` is informational.

`hermes profile list` still truncates long distribution strings in its table
display. The profile `distribution.yaml` files on disk all carry
`version: 0.1.0-alpha.10`.

## Product surface

Product-surface tests passed:

```bash
env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_workspaces.py tests/test_bases.py tests/test_inbox_cards.py \
  tests/test_modalforms.py tests/test_quickadd.py tests/test_sample_vault.py \
  tests/test_templates.py -q
```

Result: `96 passed`.

Linux Obsidian GUI follow-up was completed on the WSL test vault:

- Linux Obsidian launched with WSLg against `/home/eranr/Memoria-test`; Obsidian's
  own `obsidian.json` recorded that vault path as open.
- The left pane had the Portals/rail view active and expanded.
- Obsidian URI opens landed on `spaces/inbox.md` and `spaces/maintenance.md` as
  Markdown leaves in reading mode.
- `inbox/inbox.base` opened as an Obsidian `bases` leaf on the `Needs me` view.
- `system/board/board.base` opened as an Obsidian `bases` leaf on the `By lane`
  view.
- The running Local REST API plugin returned HTTP 200 for `spaces/maintenance.md`
  over verified HTTPS using the configured `memoria-copi` and `memoria-writer`
  profile environments.

No screenshot/window-capture tool was installed in the WSL image, so this follow-up
records Obsidian workspace and live plugin evidence rather than pixel evidence.

## Release close-out

- `gh issue list --milestone 0.1.0-alpha.10 --state open --limit 100` returned
  no open milestone issues.
- Release parent issue
  [#875](https://github.com/eranroseman/memoria-vault/issues/875) was already
  closed.
- No release-please PR, tag, or GitHub Release was cut. alpha.10 closes as an
  internal checkpoint with `released: false`.
