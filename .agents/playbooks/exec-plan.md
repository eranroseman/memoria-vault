# ExecPlan

An ExecPlan is a single, self-contained, **living** document that carries one
complex or multi-hour task from research through design, implementation, and
validation. It is written so that a stateless agent — or a human novice with no
prior knowledge of this repository — can read it top to bottom and produce a
working, observable result without asking for the next step.

Adapted for Memoria from the OpenAI Codex "ExecPlans" approach. The skeleton to
copy is [`templates/exec-plan.md`](../templates/exec-plan.md).

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

An ExecPlan is a **working artifact**, not a permanent record. Put live plan
instances on the `scratch` branch under `releases/<version>/`, delete them
before the release/checkpoint closes, and route durable outputs per `AGENTS.md`
"Scratch branch flow", "Decision records", and "Work routing".

## Five mandates (non-negotiable)

1. **Self-contained.** Embed every fact the executor needs. Do not point to
   external blogs or chat history; if knowledge is required, write it into the
   plan. Name every file by its full repository-relative path.
2. **Living.** Update Progress, the Execution log, and Surprises at every
   stopping point — honestly, splitting tasks that turned out larger than
   planned. A plan that drifts from reality is a defect, like any stale doc.
3. **Novice-executable.** Assume the reader knows nothing about this repo.
   Define every specialized term in plain language the first time it appears.
4. **Demonstrably working.** Validation is not optional. Acceptance is phrased
   as observable behavior, with the exact commands, inputs, and expected output
   transcripts — not "the code compiles."
5. **Decisions go to release ledgers.** The plan's Execution log records only
   tactical, sequencing choices made while running. Any architectural or product
   decision is written in the active release decision ledger and linked — never
   recorded only here.

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
5. Size tasks using `superpowers:writing-plans`' right-sizing rule (each task
   independently testable and revertable) — but the deliverable still lands in
   this file's own template, never a new `docs/superpowers/plans/` file.

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

## Reusing superpowers execution techniques

An ExecPlan's Concrete steps may be executed via
`superpowers:subagent-driven-development` (per-task implementer + two-stage
reviewer) or `superpowers:executing-plans` (separate-session handoff). This
file's own Validation, Progress, Execution log, and Surprises sections remain
authoritative — neither technique's plan-file or recovery ledger substitutes for
this file's record.

## Validating

Validation follows the [verify-change](verify-change.md) playbook:

1. State each acceptance as an observable claim:
   `Given <state>, when <action>, then <result>.`
2. Prove it with the lowest-cost evidence (focused test → CLI repro → smoke
   test → disposable-vault install → runtime), using `python3 scripts/verify`.
3. Paste the actual command transcript into Artifacts & notes. "Tests pass" is
   supporting evidence, not the whole report.

## Closing

Fill Outcomes & retrospective: what shipped, what is still open, lessons, and —
critically — where each durable output landed (decision ledger/design history,
issue, milestone). Then route those outputs, delete or archive the working
instance per its home, and open the PR (`AGENTS.md` → "PR flow").

## Authority

[`AGENTS.md`](../../AGENTS.md) is authoritative for worktrees, branches,
testing, security, documentation, PRs, and routing. When this playbook conflicts
with it, follow `AGENTS.md` and fix the stale text here in the same change.
