# ExecPlan

An ExecPlan is a single, self-contained, **living** document that carries one
complex or multi-hour task from research through design, implementation, and
validation. It is written so that a stateless agent — or a human novice with no
prior knowledge of this repository — can read it top to bottom and produce a
working, observable result without asking for the next step.

Use installed planning/execution skills for generic plan quality. This playbook
only maps that method onto Memoria's worktree, scratch-branch, decision, and
verification rules. The skeleton to copy is
[`templates/exec-plan.md`](../templates/exec-plan.md).

## When to use one

Reach for an ExecPlan when the work is large enough that it will not fit one
short session, must survive context loss or a handoff, or needs to run
unattended across several milestones:

- A complex feature or significant refactor.
- A multi-step migration (schema, folder, profile, or installer changes).
- Any task where "what was I doing and what is left" must be reconstructable
  from a file rather than from chat history.

Do **not** write one for a small, single-sitting change. Use
[`templates/handoff.md`](../templates/handoff.md) for a bounded handoff, or just
do the change.

## Where the plan lives (Memoria routing)

`AGENTS.md` owns the path rules. In short: live plan instances are working
artifacts on the `scratch` branch under `releases/<version>/`; delete them
before the release/checkpoint closes and route durable outputs through
`AGENTS.md` "Scratch branch flow", "Decision records", and "Work routing".

## Authoring

1. Copy [`templates/exec-plan.md`](../templates/exec-plan.md) to its scratch
   home.
2. Research thoroughly first, then fill every section. Read the whole scope —
   no sampling (`AGENTS.md` → "Working principles").
3. Use [Source-of-truth map](../system/source-of-truth-map.md),
   [Change-impact map](../system/change-impact-map.md), and
   [Test selection](../system/test-selection.md) to scope what to read, what to
   inspect together, and which checks to run.
4. Write the "Concrete steps" as exact commands with their expected output, in
   the order they must run. Prose first; the only checklist is Progress.
5. Size tasks with the installed planning skill when available. The deliverable
   still lands in this template, never a new `docs/superpowers/plans/` file.

## Running

1. **Worktree and branch first.** The first concrete step is always the
   `AGENTS.md` §1 setup. For the ExecPlan file itself, use `AGENTS.md` →
   "Scratch branch flow".
2. Execute the Concrete steps in order. Do not stop to ask for the next step —
   the plan is the instruction set; proceed autonomously to the next milestone.
3. At every stopping point, update Progress (timestamped), the Execution log,
   and Surprises & discoveries with evidence.
4. Keep steps **idempotent and recoverable**: a re-run from the top must be
   safe, and each step states how to undo it.

## Reusing installed execution skills

An ExecPlan's Concrete steps may be executed via
`superpowers:subagent-driven-development` (per-task implementer + two-stage
reviewer) or `superpowers:executing-plans` (separate-session handoff). This
file's own Validation, Progress, Execution log, and Surprises sections remain
authoritative — neither technique's plan-file or recovery ledger substitutes for
this file's record.

## Validating

Validation follows [Verify a change](verify-change.md) and
[Test selection](../system/test-selection.md). Paste the actual command
transcript into Artifacts & notes. "Tests pass" is supporting evidence, not the
whole report.

## Closing

Fill Outcomes & retrospective: what shipped, what is still open, lessons, and —
critically — where each durable output landed (decision ledger/design history,
issue, milestone). Then route those outputs, delete or archive the working
instance per its home, and open the PR (`AGENTS.md` → "PR flow").

## Authority

[`AGENTS.md`](../../AGENTS.md) is authoritative for worktrees, branches,
testing, security, documentation, PRs, and routing. When this playbook conflicts
with it, follow `AGENTS.md` and fix the stale text here in the same change.
