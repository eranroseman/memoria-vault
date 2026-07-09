# ExecPlan — {{ task title }}

<!-- Copy this template, fill every {{ placeholder }}, and delete guidance
     comments. See ../playbooks/exec-plan.md for the routing, mandates, and
     formatting rules. -->

## 0. Metadata

<!-- The minimum a stateless reader needs to orient. -->

- **Task:** {{ one line }}
- **Worktree / branch:** `~/memoria-vault/worktrees/<name>` · `feat/<name>` for implementation;
  `~/memoria-vault/scratch/releases/<version>/<name>.md` on the shared
  `scratch` branch for this plan file
- **Related decisions:** {{ release decision entry / design-history link, or — }}
- **Related issues / milestone:** {{ #NN + intended disposition:
  refs/closes/folded into #NN/no tracker change; 0.1.0 or — }}
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
<!-- See ../playbooks/exec-plan.md → "Authoring" item 5 and "Reusing superpowers
     execution techniques" for optional sizing/execution engines. -->

1. **Isolate the session** (`AGENTS.md` §1):

   ```bash
   git -C ~/memoria-vault/main fetch origin
   git -C ~/memoria-vault/main worktree add ~/memoria-vault/worktrees/{{ name }} -b feat/{{ name }} origin/main
   cd ~/memoria-vault/worktrees/{{ name }}
   ```

2. {{ next exact command }}

   ```text
   {{ expected output transcript }}
   ```

## 5. Validation and acceptance

<!-- Per the verify-change playbook. State each acceptance as an observable
     claim, then the command that proves it. Validation is NOT optional. -->

- **Claim:** Given {{ state }}, when {{ action }}, then {{ observable result }}.
  - **Prove with:** `{{ python3 scripts/verify … or CLI repro }}`
- {{ add one claim per requested outcome, plus key failure behavior }}

## 6. Idempotence and recovery

<!-- A re-run from the top must be safe. State how to undo each risky step. -->

- **Safe to re-run:** {{ what makes the steps repeatable }}
- **Rollback:** {{ how to undo — e.g. `git worktree remove`, revert commit }}

## 7. Progress

<!-- The ONE checklist. Timestamp each entry; split tasks that grew. Keep it
     honest — this is how a fresh agent resumes. -->

- [ ] {{ YYYY-MM-DD HH:MM }} — {{ milestone }}
- [ ] {{ release/checkpoint close only }} — `design-history/<NN>-<release>.md`,
      `design-history/arcs.md`, and `design-history/README.md` latest-checkpoint
      marker updated, or explicitly N/A for non-release work

## 8. Execution log

<!-- Tactical and sequencing decisions made WHILE running, with rationale.
     Architectural / product decisions are NOT recorded here — write them in
     releases/<version>/decisions.md and link them. -->

- {{ YYYY-MM-DD }} — {{ tactical choice and why }} (architectural decision → {{ link the release decision entry }})

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
- **Routed to:** {{ decision ledger/design-history, issue(s), milestone — where decisions/state landed }}
- **Lessons:** {{ what to do differently next time }}
