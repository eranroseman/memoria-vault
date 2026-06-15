# ExecPlan — {{ task title }}

<!-- ===========================================================================
  THIS IS A TEMPLATE. Copy it, then fill every {{ placeholder }} and delete the
  guidance comments. See ../playbooks/exec-plan.md for when and how to use it.

  ── Where this instance lives ───────────────────────────────────────────────
  docs/releasing/<version>/tmp/  — under the current release/checkpoint; tracked
  for linking and handoff, deleted before that release closes. (_notes/ is
  gitignored, so a plan meant to be resumed or handed off never lives there.)
  Never keep an ExecPlan as a permanent record; it is a working artifact.

  ── The mandates this file must satisfy ─────────────────────────────────────
  1. Self-contained — embed every needed fact; full repo-relative paths; no
     pointers to chat history or external blogs.
  2. Living — update Progress / Execution log / Surprises at every stop.
  3. Novice-executable — define every term the first time it appears.
  4. Demonstrably working — validation is observable behavior with transcripts.
  5. Decisions go to ADRs — link them; the Execution log holds only tactics.

  ── Formatting ──────────────────────────────────────────────────────────────
  Prose first; the ONLY checklist is Progress (§7). If you paste this whole plan
  inside one fenced code block in a prompt, indent inner code instead of nesting
  fences.
============================================================================ -->

## 0. Metadata

<!-- The minimum a stateless reader needs to orient. -->

- **Task:** {{ one line }}
- **Worktree / branch:** `~/mv-<name>` · `feat/<name>`
- **Related ADRs:** {{ ADR-NN — link to `docs/adr/<NN>-*.md`, or — }}
- **Related issues / milestone:** {{ #NN, vX.Y or — }}
- **Started:** {{ YYYY-MM-DD }} · **Last updated:** {{ YYYY-MM-DD }}

## 1. Purpose / big picture

<!-- Why this work exists, in user-visible terms. What becomes observable that
     was not before? One or two paragraphs. -->

{{ What this delivers and how a person can see it working. }}

## 2. Context and orientation

<!-- Assume the reader has never seen this repo. Where do the relevant pieces
     live (full repo-relative paths)? What is the current state? Define every
     specialized term in plain language the first time you use it. -->

{{ Repository state, the files in play, and the vocabulary needed to proceed. }}

## 3. Plan of work

<!-- Prose narrative of the edits and changes, in the order they make sense.
     Not a checklist — explain the shape of the change and why. -->

{{ The approach, described as connected prose. }}

## 4. Concrete steps

<!-- Exact commands in execution order, each with its EXPECTED output. Step 1 is
     always the AGENTS.md §1 worktree/branch setup. Keep each step idempotent. -->

1. **Isolate the session** (`AGENTS.md` §1):

   ```bash
   git fetch origin
   git worktree add ~/mv-{{ name }} -b feat/{{ name }} origin/main
   cd ~/mv-{{ name }}
   ```

2. {{ next exact command }}

   ```text
   {{ expected output transcript }}
   ```

## 5. Validation and acceptance

<!-- Per the verify-change playbook. State each acceptance as an observable
     claim, then the command that proves it. Validation is NOT optional. -->

- **Claim:** Given {{ state }}, when {{ action }}, then {{ observable result }}.
  - **Prove with:** `{{ scripts/test.sh … or CLI repro }}`
- {{ add one claim per requested outcome, plus key failure behavior }}

## 6. Idempotence and recovery

<!-- A re-run from the top must be safe. State how to undo each risky step. -->

- **Safe to re-run:** {{ what makes the steps repeatable }}
- **Rollback:** {{ how to undo — e.g. `git worktree remove`, revert commit }}

## 7. Progress

<!-- The ONE checklist. Timestamp each entry; split tasks that grew. Keep it
     honest — this is how a fresh agent resumes. -->

- [ ] {{ YYYY-MM-DD HH:MM }} — {{ milestone }}

## 8. Execution log

<!-- Tactical and sequencing decisions made WHILE running, with rationale.
     Architectural / product decisions are NOT recorded here — write them as an
     ADR in docs/adr/ and link it. -->

- {{ YYYY-MM-DD }} — {{ tactical choice and why }} (architectural decision → {{ link the ADR at `docs/adr/<NN>-*.md` }})

## 9. Surprises & discoveries

<!-- Unexpected behavior, with the evidence that revealed it. -->

- {{ what surprised you, and the command/output that showed it }}

## 10. Interfaces & dependencies

<!-- Prescriptive: the exact libraries, modules, schemas, or contracts this work
     depends on or introduces. Name versions and source-of-truth files. -->

{{ The interfaces and dependencies, named precisely. }}

## 11. Artifacts & notes

<!-- Concise transcripts and diffs that prove the steps ran. Keep them short —
     paste the lines that matter, not whole logs. -->

{{ Command transcripts, key diffs, generated-file excerpts. }}

## 12. Outcomes & retrospective

<!-- Filled at close. What shipped, what is still open, lessons learned, and
     where each durable output landed. -->

- **Shipped:** {{ what now works }}
- **Still open:** {{ remaining gaps → GitHub issues }}
- **Routed to:** {{ ADR(s), issue(s), milestone — where decisions/state landed }}
- **Lessons:** {{ what to do differently next time }}
