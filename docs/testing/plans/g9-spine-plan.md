---
topic: tests
title: Deterministic-spine test plan (G9)
status: draft
parent: Test plans
grand_parent: Testing
nav_order: 14
---

# Deterministic-spine test plan — v0.1 (G9)

The leanest possible proof that **the agent spine runs end-to-end through the board**: a *dispatched* card runs the Linter operation's `health-report` (zero-LLM, deterministic), writes its report through the live policy gate into an allowed zone, the write is audited, and the card reaches `done` — **with no human-review step required.** Where the [golden-path plan](e2e-golden-path-plan.md) threads all five profiles through the whole lifecycle, this isolates the single question underneath it: *does dispatch → claim → run → gated write → audit → done work live, at all?* Prove this first; it de-risks every richer loop (the ingest value loop is [G10](../../releasing/0.1.0-alpha.1/release-plan-0.1.0-alpha.1.md)).

**Why the Linter operation.** The dispatched lane allows writes only to `system/logs/**`, and that zone is **not** review-gated (the gated zones are `notes/claims/` and `notes/hubs/`). So the write logs a clean `allow_with_log` and the card completes **without** a human approval round — that is the G11 review loop, deliberately out of scope here. The Linter operation is also `invocation: dispatched`, `external_api_policy: blocked`, and zero-LLM ([detectors.py](../../reference/linter.md) is pure-stdlib `run_all()` + `verdict()`), so the same vault state yields the same report every run — the only fully reproducible spine in the system.

**The distinction this plan insists on.** The board is Hermes-native — cards live in `kanban.db`; the **dispatcher** polls every 60 s, claims `ready` cards for the matching lane, and advances them to `running`. `system/board/<task_id>.md` is only the *export mirror* (empty until a card exists and the exporter runs). G9 tests the **dispatch** path — the dispatcher claiming a card — **not** a direct `hermes -p … chat` invocation. Direct invocation proves the skill; dispatch proves the *operability*.

**Where to run.** A live install (the gate candidate): 5 profiles registered, the `memoria-policy-gate` plugin deployed per-lane ([ADR-28](../../adr/28-write-gate-as-plugin.md)), `hermes gateway status` up so the dispatcher runs. A disposable vault is fine and preferred.

**How to read each step.** **Action** → **✓ Pass** → **✗ If it fails**. Each step's output is the next step's input; a step failing **blocks** the rest — record where the chain broke.

> **Exact `hermes kanban`/`cron` flags are marked _(confirm)_** where this draft specifies intent rather than a verified invocation — fill them in on first run and drop the marker.

---

## 0. Preconditions

- [ ] Gate candidate installed; `hermes profile list` shows all 5 at `0.1.0-alpha.10`; policy plugin enabled per-lane.
- [ ] `hermes gateway status` → running (the dispatcher polls only while the gateway is up).
- [ ] Baseline captured: `hermes kanban list --json` _(confirm)_ and a copy of `system/logs/audit.jsonl` (for a clean before/after diff).
- [ ] `cron_mode` defaults to `deny`; for **Variant A** dispatch one card by hand, for **Variant B** enable the Linter-operation lane cron explicitly.

---

## Part A — Dispatch & claim (the spine's entry)

Run **A-min first** (isolates the gate/write/complete spine from the scheduler); run **A-cron** second, once A-min is green.

**A-min. Run the Linter operation directly** with `detectors.py --vault <path>` before testing scheduler plumbing.
- ✓ Pass: the command produces a findings set and verdict without a Hermes chat skill.
- ✗ If it fails: a detector or vault-fixture bug; fix that before testing cron/card plumbing.

**A-cron** (after A-min). Enable the Linter-operation lane cron and let `nightly-lint` fire on its schedule (`cron/scheduled.yaml`: `0 2 * * *` → `creates_card:{state: ready}`), or force a tick _(confirm)_.
- ✓ Pass: the cron entry creates the `ready` card with no human action, then A-min's claim behavior follows.
- ✗ If it fails: cron created nothing → scheduler not running, or `cron_mode` still `deny`. (This is the first live exercise of cron→card creation — expect to debug it here.)

---

## Part B — Run (deterministic health-report)

**B1.** The Linter-operation run produces the report — `detectors.py --vault <path>` → `run_all()` + `verdict()`.
- ✓ Pass: a findings set + a single verdict band (`PASS`/`REVIEW`/`FAIL`) is produced; running it twice on unchanged vault state yields a byte-identical report (determinism).
- ✗ If it fails: a stack trace or a non-deterministic diff → a detector bug, not a spine problem (run `python3 -m pytest tests/test_detectors.py` to bisect).

---

## Part C — Gated write + audit (the load-bearing step)

`detectors.py` **prints to stdout** — it does not write a file. The agent must capture that output and save the report; that save is the gated write. This seam is the thing most likely to be assumed-not-built — test it explicitly.

**C1.** The Linter operation's report is written to `system/logs/` (e.g. `system/logs/health-report-<date>.md`). The write crosses `policy_hook` → `policy_mcp`.
- ✓ Pass: file on disk under `system/logs/`; the gate logs `allow_with_log` (in-zone, non-gated); **no** `dry_run`/`deny`.
- ✗ If it fails: `deny` → the write targeted a path outside `system/logs/` (a SOUL-procedure path bug). No write at all → the stdout→save step isn't in the procedure (the seam was assumed).

**C2.** The policy MCP appends one line to `system/logs/audit.jsonl`.
- ✓ Pass: exactly one audit row for the write, `after_hash` matches the saved file's SHA-256; `before_hash` empty (new file).
- ✗ If it fails: no audit row → the write bypassed the gate (a fail-open the whole gate exists to prevent — a release blocker).

---

## Part D — Complete (card → done, no review)

**D1.** The card advances `running → done`. *(The per-session digest in `system/logs/sessions/` lands later — the Linter's daily cron digests a session after a 24 h quiet window; see [ADR-25](../../adr/25-session-logging-two-logs.md).)*
- ✓ Pass: `hermes kanban list --json` shows the card `done`; **no** review step was required (logs zone is not review-gated); `board-transitions.jsonl` records the `running → done` move once `board_export` ticks.
- ✗ If it fails: card stuck `running` → the agent didn't signal completion (orchestration gap). Card asks for review → a mis-scoped write zone leaked into a gated path.

---

## Part E — Invariants held

| # | Cross-cutting check | ✓ Pass |
| --- | --- | --- |
| E1 | **Dispatch, not invocation** | the card moved `ready → running` via the dispatcher, not a manual `chat` call |
| E2 | **Determinism** | a second run on unchanged state produces a byte-identical report (zero-LLM holds) |
| E3 | **Audit pairing intact** | the write's `audit.jsonl` row has an `after_hash` matching the file; `lint`'s `audit-unpaired-writes` is clean afterward |
| E4 | **Gate held, no fail-open** | the only decision logged is `allow_with_log`; a simulated policy outage during the write would `deny` (fail-closed) |
| E5 | **No human in the loop** | the card reached `done` with no review step — the spine completes autonomously for a non-gated zone |

---

## Results

| Step | Test | Pass / Fail | Notes |
| --- | --- | --- | --- |
| A-min | hand-dispatched card claimed → running | | |
| A-cron | cron creates the ready card | | |
| B | deterministic health-report produced | | |
| C | gated write `allow_with_log` + audit row | | |
| D | card → done, no review needed | | |
| E | dispatch / determinism / audit / gate / autonomy | | |

**G9 green** when one card traverses A-min → D with the gate logging `allow_with_log`, an `audit.jsonl` row whose `after_hash` matches the saved report, and the card ending `done` — and all E invariants hold. A-cron green adds the scheduler + cron→card proof. Record the result in the G9 sub-issue under the current release parent issue; preserve run details in that release folder's `validation-log.md` only when a curated summary is worth keeping.
