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

An ExecPlan is a **working artifact**, not a new committed deliverable. Memoria
retired standalone proposal and design-doc folders — decisions are ADRs and
state lives in issues — so an ExecPlan must never become a fourth permanent
record.

Put the instance in **`docs/releasing/<version>/tmp/`** under the current
release or checkpoint: tracked so it can be linked and handed off, excluded from
the published site, and deleted before that release/checkpoint closes (see
`AGENTS.md` → "Release plans"). This is the repository's only home for tracked
in-work design scratch — `_notes/` is gitignored and invisible to other agents,
so a plan meant to be resumed or handed off never lives there.

The ExecPlan **orchestrates** the work; it does not replace the records that work
produces. Durable outputs route as usual:

| Output | Goes to |
|---|---|
| An architectural or product decision | an ADR in `docs/adr/` — the plan links it |
| Release readiness / gate / stage state | the "Release <version>" parent issue and its sub-issues |
| A scope cut | a GitHub issue with Readiness `Later`; add or update an ADR only when the cut records a decision or durable rationale |
| A bug, gap, or follow-up | a GitHub issue in the Memoria Issue Tracker |

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
5. **Decisions go to ADRs.** The plan's Execution log records only tactical,
   sequencing choices made while running. Any architectural or product decision
   is written as an ADR in `docs/adr/` and linked — never recorded only here.

## Authoring

1. Copy [`templates/exec-plan.md`](../templates/exec-plan.md) to its home (see
   "Where the plan lives").
2. Research thoroughly first, then fill every section. Read the whole scope —
   no sampling (`AGENTS.md` → "Working principles").
3. Use [Source-of-truth map](../system/source-of-truth-map.md),
   [Change-impact map](../system/change-impact-map.md), and
   [Test selection](../system/test-selection.md) to scope what to read, what to
   inspect together, and which checks to run.
4. Write the "Concrete steps" as exact commands with their expected output, in
   the order they must run. Prose first; the only checklist is Progress.

## Running

1. **Worktree and branch first.** The first concrete step is always the
   `AGENTS.md` §1 setup (`git worktree add … -b … origin/main`); every edit,
   commit, and PR happens from that worktree on that branch.
2. Execute the Concrete steps in order. Do not stop to ask for the next step —
   the plan is the instruction set; proceed autonomously to the next milestone.
3. At every stopping point, update Progress (timestamped), the Execution log,
   and Surprises & discoveries with evidence.
4. Keep steps **idempotent and recoverable**: a re-run from the top must be
   safe, and each step states how to undo it.

## Validating

Validation follows the [verify-change](verify-change.md) playbook:

1. State each acceptance as an observable claim:
   `Given <state>, when <action>, then <result>.`
2. Prove it with the lowest-cost evidence (focused test → CLI repro → smoke
   test → disposable-vault install → runtime), using `scripts/test.sh`.
3. Paste the actual command transcript into Artifacts & notes. "Tests pass" is
   supporting evidence, not the whole report.

## Closing

Fill Outcomes & retrospective: what shipped, what is still open, lessons, and —
critically — where each durable output landed (ADR, issue, milestone). Then
route those outputs, delete or archive the working instance per its home, and
open the PR (`AGENTS.md` → "PR flow").

## Authority

[`AGENTS.md`](../../AGENTS.md) is authoritative for worktrees, branches,
testing, security, documentation, PRs, and routing. When this playbook conflicts
with it, follow `AGENTS.md` and fix the stale text here in the same change.
