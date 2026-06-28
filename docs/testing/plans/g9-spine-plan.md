---
topic: tests
title: Dispatched-card spine test plan (G9)
status: draft
parent: Test plans
grand_parent: Testing
nav_order: 14
---

# Dispatched-card spine test plan — v0.1 (G9)

The leanest live proof that the shipped agent spine works: create one card on an existing
lane, let the Hermes dispatcher claim it, make the worker write only inside that lane's
allowed scope through the policy gate, verify the audit row, and confirm the card reaches
`done`.

This plan does **not** use the Linter as a board lane. The Linter is a deterministic
operation wired through direct CLI/cron wrappers, not a dispatched profile. Run it as a
preflight if you need a cheap vault-health check; G9 itself tests the shipped board path.

**Where to run.** A live install candidate: all five profiles registered, gateway running,
policy plugin deployed for dispatched lanes, and a disposable test vault preferred.

**How to read each step.** **Action** → **✓ Pass** → **✗ If it fails**. A failing step
blocks the rest.

---

## 0. Preconditions

- [ ] `hermes profile list` shows all five `memoria-*` profiles.
- [ ] `hermes gateway status` reports running so the dispatcher can claim ready cards.
- [ ] Baseline captured: `hermes kanban list --json` and `system/logs/audit.jsonl`.
- [ ] Optional preflight: `python src/.memoria/operations/integrity/linter/detectors.py --vault <vault>` returns without a CRITICAL finding.

---

## Part A — Create and Claim

Create one minimal card on a shipped lane. The smallest current target is the
Peer-reviewer `verify` lane because its write scope is only `inbox/`.

```bash
hermes kanban create "G9 verify spine smoke" \
  --assignee memoria-peer-reviewer \
  --created-by memoria-copi \
  --body "Create one test gap or flag card in inbox/ proving the verify lane can write through the gate, then kanban_complete."
```

- ✓ Pass: the card appears ready, then the dispatcher moves it to running.
- ✗ If it fails: profile registration, gateway, or Kanban creation is broken before the worker logic starts.

---

## Part B — Gated Write and Audit

Let the worker create exactly one Inbox card under `inbox/`.

- ✓ Pass: the new file exists under `inbox/`, the policy decision is `allow` or
  `allow_with_log`, and the paired `write_complete` row's `after_hash` matches the file.
- ✗ If it fails: a deny means the worker targeted a path outside the lane ceiling; no audit
  row means the write bypassed the gate.

---

## Part C — Complete

Confirm the card reaches `done`.

- ✓ Pass: `hermes kanban list --json` shows the card `done`; `board-transitions.jsonl`
  records the transition after board export ticks.
- ✗ If it fails: stuck `running` means the worker did not call `kanban_complete`; a review
  request is acceptable only if the card explicitly produced PI-facing follow-up.

---

## Invariants

| # | Check | ✓ Pass |
| --- | --- | --- |
| G9.1 | Dispatch, not direct chat | the dispatcher moved the card `ready → running` |
| G9.2 | Lane ceiling held | every write stayed under the selected lane's `write_scope` |
| G9.3 | Gate held | the write produced policy audit rows and no fail-open behavior |
| G9.4 | Completion held | the card reached `done` without manual state editing |

Record the result in the G9 sub-issue under the current release parent issue. Keep only the
command, date, environment, card id, touched file, and audit-row hash; anything more is noise.
