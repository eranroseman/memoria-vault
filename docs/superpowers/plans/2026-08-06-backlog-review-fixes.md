# Backlog Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the 2026-08-06 backlog review — 12 mechanical fixes, the tracker mechanism from the rethink design (store-monotonic/derive-volatile: labels `needs-owner`/`needs-triage`/`wontfix`, dependency edges, prefix→category sweep, U3-CANVAS.5), the milestone-policy + issue-conventions doc amendments, and owner-call scaffolding on 11 decision issues — without resolving any owner decision.

**Architecture:** Three independent workstreams. **Part A** is ordinary repo work: one branch in a Claude worktree, `scripts/verify`, one PR. **Part B** is tracker metadata (labels, edges, milestones, project field/board) via `gh` — live writes, no PR. **Part C** rewrites issue bodies one issue at a time, merging each issue's mechanical fix and its owner-call scaffold into a single edit. Parts B and C do not depend on Part A's merge; only Task 22 (close #1748) waits for it.

**Tech Stack:** `gh` CLI (REST + GraphQL), git worktree, pytest, Python.

## Global Constraints

- **Stage explicit paths only. Never `git add -A` / `git add .`** (AGENTS.md shared-index rule; a PreToolUse hook enforces it).
- Repo edits happen in the worktree `.claude/worktrees/backlog-fixes` — every Read/Edit/Write path for Part A MUST begin with that worktree root. Tracker (`gh`) commands run from anywhere.
- `python scripts/verify` must be green before the Part A PR; merge by squash.
- Every `gh issue edit --body-file` REPLACES the whole body: always fetch the current body first, apply the stated edits to that text, and leave all unrelated content byte-identical.
- Tracker writes are live and outward-facing. Each task verifies its target (issue number, label, field id) by a read before the write. No issue is closed except #1748 (Task 22).
- Owner-call scaffolding presents options and evidence — it never picks. Do not add recommendations the review did not make.
- Verify each review claim cited in a task before acting on it (the command is given in the task). If a verification fails, stop that task and report — do not improvise.
- Trust order when sources disagree: schema → tests → code → docs.

**Issue-body editing pattern used throughout Part C** (referenced as "the body pattern"):

```bash
SCRATCH=/tmp/claude-1000/-home-eranr-memoria-vault/7f103617-d0ac-4666-b5ff-1b448012df9d/scratchpad/bodies
mkdir -p "$SCRATCH"
gh issue view <N> --json body -q .body > "$SCRATCH/<N>.md"
# ...edit $SCRATCH/<N>.md exactly as the task states...
gh issue edit <N> --body-file "$SCRATCH/<N>.md"
gh issue view <N> --json body -q .body | grep -c "<anchor from the task>"   # verify
```

---

## Part A — repository changes (one branch, one PR)

### Task 1: Worktree and plan commit

**Files:**
- Create: `.claude/worktrees/backlog-fixes/` (worktree)
- Add: `docs/superpowers/plans/2026-08-06-backlog-review-fixes.md` (this file)

- [ ] **Step 1: Create the worktree from the main checkout**

```bash
cd /home/eranr/memoria-vault
git fetch origin
git worktree add .claude/worktrees/backlog-fixes -b wip/backlog-fixes origin/main
```

- [ ] **Step 2: Copy the plan in and commit it**

```bash
cp docs/superpowers/plans/2026-08-06-backlog-review-fixes.md \
   .claude/worktrees/backlog-fixes/docs/superpowers/plans/
cd .claude/worktrees/backlog-fixes
git add docs/superpowers/plans/2026-08-06-backlog-review-fixes.md
git commit -m "plan: backlog review fixes"
```

### Task 2: #1748 — delete the always-true hasattr guard in test_cockpit.py

**Files:**
- Modify: `.claude/worktrees/backlog-fixes/tests/test_cockpit.py:488`

**Interfaces:**
- Consumes: `cockpit.trace_panel` — unconditionally defined at `src/memoria_vault/runtime/cockpit.py:193`.
- Produces: nothing later tasks use; Task 22 closes the issue after merge.

- [ ] **Step 1: Verify the review's two claims**

```bash
cd /home/eranr/memoria-vault/.claude/worktrees/backlog-fixes
grep -n 'hasattr(cockpit, "trace_panel")' tests/test_cockpit.py
grep -n "trace_panel" src/memoria_vault/runtime/cockpit.py | head -3
```

Expected: one hit in the test near line 488; `trace_panel` defined unconditionally in cockpit.py (near :193, not inside any `if`). If either fails, stop and report.

- [ ] **Step 2: Fetch the blast-radius paragraph from the issue**

```bash
gh issue view 1748 --json body -q .body | grep -n -A4 -i "sweep"
```

Expected: the paragraph warning not to blind-sweep the ~19 other `raising=False` call sites. Keep its text for Step 3.

- [ ] **Step 3: Delete the guard, dedent, add the comment**

In `tests/test_cockpit.py`, remove the `if hasattr(cockpit, "trace_panel"):` line and dedent its block one level. Immediately above the dedented block add a comment carrying the issue's warning, in this shape (adjust the count to the paragraph fetched in Step 2):

```python
    # trace_panel is unconditionally defined (cockpit.py), so no hasattr guard.
    # NOTE: other tests in this suite use raising=False guards deliberately —
    # do not sweep them blind; if a sweep is wanted, it is its own issue (#1748).
```

- [ ] **Step 4: Run the test file**

```bash
python -m pytest tests/test_cockpit.py -q
```

Expected: all pass, same count as before minus zero (the guard was always-true, so no test disappears).

- [ ] **Step 5: Commit**

```bash
git add tests/test_cockpit.py
git commit -m "test: drop always-true trace_panel hasattr guard (closes #1748)"
```

### Task 3: alpha23-usable-loop.md — delete the false JSONL rationale

**Files:**
- Modify: `.claude/worktrees/backlog-fixes/docs/superpowers/plans/2026-07-15-alpha23-usable-loop.md:3121,3213`

- [ ] **Step 1: Verify the rationale is false (code writes the journal)**

```bash
cd /home/eranr/memoria-vault/.claude/worktrees/backlog-fixes
grep -n "_journal_path\|journal/" src/memoria_vault/vault/trusted_writer.py | head -6
sed -n '3115,3130p;3208,3218p' docs/superpowers/plans/2026-07-15-alpha23-usable-loop.md
```

Expected: `trusted_writer.py` builds `vault/.memoria/journal/{machine}.jsonl` (near :1448) and writes it; the plan file near :3121 claims "No such file exists… nothing in `src/` writes a JSONL journal" and near :3213 has a `# Corrected 2026-08-02` comment. If the plan lines have shifted, locate them by those quoted strings.

- [ ] **Step 2: Edit**

Delete the false-rationale sentence(s) at ~:3121 ("**No such file exists**… nothing in `src/` writes a JSONL journal") and the `# Corrected 2026-08-02` comment block at ~:3213. Keep the substituted `sqlite3` command — it is correct (`_append_decorated_event` writes both stores).

- [ ] **Step 3: Verify and commit**

```bash
grep -c "nothing in \`src/\` writes a JSONL journal" docs/superpowers/plans/2026-07-15-alpha23-usable-loop.md
git add docs/superpowers/plans/2026-07-15-alpha23-usable-loop.md
git commit -m "docs: drop false JSONL-journal rationale from alpha23 plan"
```

Expected: grep count 0.

### Task 4: surfaces-bootstrap-and-plugins.md — delete the contradicted reinstall paragraph

**Files:**
- Modify: `.claude/worktrees/backlog-fixes/docs/superpowers/plans/2026-07-22-surfaces-bootstrap-and-plugins.md:13913-13921` (locate by content if drifted; the file is the one containing "must first reinstall the engine")

- [ ] **Step 1: Verify the engine works without reinstall**

```bash
cd /home/eranr/memoria-vault/.claude/worktrees/backlog-fixes
memoria --version
```

Expected: a version prints. If `memoria` is not on PATH or errors, STOP — the paragraph may be right in your shell, and the review flagged exactly this caveat. Report instead of deleting.

- [ ] **Step 2: Locate and delete the paragraph**

```bash
grep -rn "must first reinstall the engine" docs/superpowers/plans/
```

Delete that paragraph (the block asserting a reinstall is required before the step it precedes — it contradicts #1690, which is accurate for this checkout).

- [ ] **Step 3: Verify and commit**

```bash
grep -rc "must first reinstall the engine" docs/superpowers/plans/ | grep -v ":0" || echo CLEAN
git add docs/superpowers/plans/<the file edited in Step 2>
git commit -m "docs: drop reinstall-required paragraph contradicted by #1690"
```

Expected: `CLEAN`.

### Task 5: Milestone-policy doc amendments (roadmap.md, explanation/README.md, AGENTS.md)

**Files:**
- Modify: `.claude/worktrees/backlog-fixes/docs/roadmap.md:9-15,60-61`
- Modify: `.claude/worktrees/backlog-fixes/docs/explanation/README.md:57`
- Modify: `.claude/worktrees/backlog-fixes/AGENTS.md:58`

**Interfaces:**
- Consumes: the review's milestone finding — 21/33 open issues unmilestoned; alpha.11–20 and alpha.22 shipped with `design-history/` chapters and no milestone; beta.1's closed half is 8 `not_planned` + 2 `completed`.
- Produces: the `needs-owner` label's documented home (Task 7 creates the label itself).

- [ ] **Step 1: Read the three current passages**

```bash
cd /home/eranr/memoria-vault/.claude/worktrees/backlog-fixes
sed -n '5,20p;55,65p' docs/roadmap.md
sed -n '50,62p' docs/explanation/README.md
sed -n '55,62p' AGENTS.md
```

- [ ] **Step 2: Amend `docs/roadmap.md`**

Replace the claim at :9-15 that "The canonical record of scope and readiness is GitHub: the milestones … When this page and the milestone disagree, the milestone wins" with:

```markdown
Milestones mark intended-release scope when one is set; not every release
gets one. The per-release record is the frozen `design-history/` chapter.
This page is descriptive, not canonical.
```

At :60-61, replace "per-package readiness lives in the milestone, not here" with:

```markdown
Per-package readiness is tracked on the issues themselves (see the
`needs-owner` label for issues gated on an owner decision, a PI session,
or real-vault data).
```

Adapt surrounding grammar so the section still reads cleanly; change nothing else on the page.

- [ ] **Step 3: Amend `docs/explanation/README.md:57`**

That line repeats the milestones-are-canonical claim. Rewrite it to match Step 2's first block (one sentence: milestones mark intent when set; `design-history/` is the per-release record).

- [ ] **Step 4: Amend `AGENTS.md:58` and add the issue-conventions block**

Current at :58: "Backlog and readiness live in GitHub issues and milestones (a milestone is a release) — no separate status/readiness fields, no release parent-issue ceremony."

Replace with:

```markdown
- Backlog lives in GitHub issues. A milestone marks intended-release scope
  when one is set — not every release gets one; the frozen `design-history/`
  chapter is the per-release record. No separate status/readiness fields
  beyond the labels in "Issue conventions" below, no release parent-issue
  ceremony.
```

Then add a new subsection immediately after the "Where things live" bullet list (design rationale: the tracker is shared state for concurrent, memoryless agents — it stores only facts that cannot rot; everything code-state-dependent is derived at read time):

```markdown
## Issue conventions

The tracker stores only monotonic or owner-gated facts; readiness is always
derived, never stored — a stored "ready" claim about code state goes stale in
hours at this merge rate.

- **Labels.** Category (`bug`, `documentation`, `security`, `tests`) at
  filing, in labels — never as title prefixes. `needs-triage` on every
  agent-filed issue; the owner removes it by ruling. `needs-owner` when only
  an owner act clears the issue (a decision, a PI session, real-vault data).
  `wontfix` at close makes rejections searchable. There is deliberately no
  `ready-for-agent` label.
- **Pull query** — "what can an agent start right now": open, unassigned,
  not `needs-owner`, not `needs-triage`, and no open blocker:
  `gh issue list --state open --search 'no:assignee -label:needs-owner -label:needs-triage'`,
  then drop rows whose `issue_dependencies_summary.blocked_by` is nonzero
  (`gh api repos/{owner}/{repo}/issues/N`).
- **Intake.** Before filing, search open issues and closed `wontfix` issues
  by glossary concept, not just by wording. Bodies cite symbols
  (`file.py::function`) and commit shas — never bare line numbers or plan
  task IDs; both rot.
- **Claim.** An agent working an issue assigns itself as its first write
  (`gh issue edit N --add-assignee @me`); unassigned = unclaimed. Unassign
  on abandonment; a stale assignee with no activity is unclaimed — remove it
  on sight.
- **Ordering.** Native `blocked_by` edges only, issue → issue (they clear
  themselves when the blocker closes). No prose blocker tables.
- **Decisions.** Resolve as a comment, then close. Term-level rulings also
  land in the glossary.
```

- [ ] **Step 5: Verify no dangling claims, run verify, commit**

```bash
grep -rn "milestone wins\|a milestone is a release" docs/ AGENTS.md || echo CLEAN
grep -c "Issue conventions" AGENTS.md
python scripts/verify
git add docs/roadmap.md docs/explanation/README.md AGENTS.md
git commit -m "docs: milestone policy matches practice; issue conventions for the multi-agent tracker"
```

Expected: `CLEAN`, grep count 1, verify OK.

### Task 6: PR for Part A

- [ ] **Step 1: Full verify, push, open PR**

```bash
cd /home/eranr/memoria-vault/.claude/worktrees/backlog-fixes
python scripts/verify
git push -u origin wip/backlog-fixes
gh pr create --title "Backlog review: in-tree fixes (test guard, two stale plan passages, milestone policy docs)" --body "$(cat <<'EOF'
## Summary
In-tree half of the 2026-08-06 backlog review:
- tests: delete the always-true `hasattr(cockpit, "trace_panel")` guard (#1748), keeping its blast-radius warning as a comment.
- alpha23 plan: drop the false "nothing writes a JSONL journal" rationale (trusted_writer.py writes it); keep the sqlite3 command.
- surfaces plan: drop the "must first reinstall the engine" paragraph contradicted by #1690.
- docs: milestone policy now matches practice — milestones mark intent when set, design-history is the per-release record; `needs-owner` label documented in AGENTS.md.

Tracker-side changes (labels, edges, Readiness field, issue rewrites) are separate live `gh` operations, not in this PR.

## Test plan
- [x] `python -m pytest tests/test_cockpit.py -q`
- [x] `python scripts/verify` — OK

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Expected: PR opens; `verify` + `gitleaks` go green. Merge by squash when green (Task 22 depends on the merge).

---

## Part B — tracker metadata (live `gh` writes, no PR)

### Task 7: Labels — create the convention set, delete the three dead ones

- [ ] **Step 1: Verify current label state**

```bash
gh label list --limit 60 | grep -E "needs-owner|needs-triage|wontfix|security|tests|release|autorelease"
```

Expected: `release`, `autorelease: pending`, `autorelease: tagged` exist; none of the five new ones do.

- [ ] **Step 2: Verify the dead labels have no open users**

```bash
for L in "release" "autorelease: pending" "autorelease: tagged"; do
  echo "$L: $(gh issue list --label "$L" --state open --json number -q length) open"
done
```

Expected: `0 open` for all three. If not, stop and report.

- [ ] **Step 3: Create and delete**

```bash
gh label create needs-owner --color B60205 \
  --description "Agent cannot finish alone: owner decision, PI session, or real-vault data"
gh label create needs-triage --color FBCA04 \
  --description "Agent-filed, not yet ratified by the owner"
gh label create wontfix --color FFFFFF \
  --description "Rejected — searched at intake so it is not re-proposed"
gh label create security --color D93F0B \
  --description "Write perimeter, trust seams, secrets"
gh label create tests --color 1D76DB \
  --description "Test hygiene and coverage"
gh label delete "release" --yes
gh label delete "autorelease: pending" --yes
gh label delete "autorelease: tagged" --yes
```

- [ ] **Step 4: Verify**

```bash
gh label list --limit 60 | grep -cE "needs-owner|needs-triage|wontfix|security|tests"
gh label list --limit 60 | grep -c "autorelease\|^release" || echo DEAD-GONE
```

Expected: `5`, then `DEAD-GONE`.

### Task 7b: Prefix→category label sweep on the open set

Category is immutable at birth — this metadata cannot rot, so migrating it is safe (unlike any readiness state). The shadow taxonomy today: `[docs]` ×6, `docs:` ×4, `[test-hygiene]`, `[test-coverage]`, `[security]`, `[P2]`.

**Interfaces:**
- Consumes: Task 7's labels; the existing `documentation` label.
- Note: run before the Part C retitles or after — independent; Part C's new titles carry no prefixes.

- [ ] **Step 1: Apply category labels**

```bash
for N in 1572 1647 1648 1649 1650 1651 1652 1653 1753 1754; do
  gh issue edit "$N" --add-label documentation
done
gh issue edit 1727 --add-label security
gh issue edit 1529 --add-label security
gh issue edit 1747 --add-label tests
gh issue edit 1748 --add-label tests
```

- [ ] **Step 2: Strip the prefixes from titles**

```bash
for N in 1572 1647 1648 1649 1650 1651 1652 1653 1753 1754 1727 1747 1748 1529; do
  T=$(gh issue view "$N" --json title -q .title)
  NT=$(printf '%s' "$T" | sed -E 's/^\[(docs|test-hygiene|test-coverage|security|P2)\] //; s/^docs: //')
  [ "$T" != "$NT" ] && gh issue edit "$N" --title "$NT" && echo "$N: $NT"
done
```

Expected: 14 retitles echo. `[P2]` is dropped without replacement — no priority vocabulary is adopted; `security` + `needs-owner` carry what P2 was signalling on #1529.

- [ ] **Step 3: Verify the shadow taxonomy is gone**

```bash
gh issue list --state open --limit 50 --json title -q '.[].title' | grep -E "^\[|^docs:" || echo PREFIXES-GONE
```

Expected: `PREFIXES-GONE`.

### Task 8: Apply `needs-owner` to the 17 gated issues

**Interfaces:**
- Consumes: Task 7's label. The 17 (review §1.3): 447, 560, 562, 829, 902, 1348, 1473, 1474, 1520, 1526, 1529, 1572, 1652, 1653, 1690, 1702, 1760.

- [ ] **Step 1: Apply**

```bash
for N in 447 560 562 829 902 1348 1473 1474 1520 1526 1529 1572 1652 1653 1690 1702 1760; do
  gh issue edit "$N" --add-label needs-owner
done
```

- [ ] **Step 2: Verify count**

```bash
gh issue list --label needs-owner --state open --json number -q length
```

Expected: `17`.

### Task 9: Wire the two native blocking edges

**Interfaces:**
- Consumes: GitHub's issue-dependencies REST endpoint. `issue_id` must be the numeric **database id** (`--jq .id`), not the `#number`, not the `node_id`.
- Edges: #1702 blocked_by #1505 (#1505 body: journey suite "lands before LOOP.13"); #1526 blocked_by #1348 (K2 option B kills #1526's option 1). The two ↔ pairs (#1727/#1731, #1653/#1753) get body cross-references in Part C, not edges — neither strictly precedes the other.

- [ ] **Step 1: Wire and verify**

```bash
R=repos/eranroseman/memoria-vault
B1505=$(gh api $R/issues/1505 --jq .id)
B1348=$(gh api $R/issues/1348 --jq .id)
gh api --method POST $R/issues/1702/dependencies/blocked_by -F issue_id=$B1505
gh api --method POST $R/issues/1526/dependencies/blocked_by -F issue_id=$B1348
gh api $R/issues/1702 --jq .issue_dependencies_summary
gh api $R/issues/1526 --jq .issue_dependencies_summary
```

Expected: both show `"blocked_by":1`.

### Task 10: Milestone the four release-relevant issues

**Assumption (stated, cheap to reverse):** target milestone `0.1.0-beta.1` — #1691 (the bug), #1727 (security), #1731 and #1760 (trust seams) plainly precede a release.

- [ ] **Step 1: Assign and verify**

```bash
for N in 1691 1727 1731 1760; do
  gh issue edit "$N" --milestone "0.1.0-beta.1"
done
gh issue list --milestone "0.1.0-beta.1" --state open --json number -q length
```

Expected: `14` (10 prior + 4).

### Task 11: Delete the Readiness field from Project #1

- [ ] **Step 1: Confirm nothing reads it and fetch its id**

```bash
ls /home/eranr/memoria-vault/.github/workflows/   # expect only gitleaks.yml verify.yml
grep -rn "Readiness" /home/eranr/memoria-vault/src /home/eranr/memoria-vault/tests /home/eranr/memoria-vault/scripts 2>/dev/null || echo NO-READERS
FID=$(gh project field-list 1 --owner eranroseman --format json \
  | jq -r '.fields[] | select(.name=="Readiness") | .id')
echo "$FID"
```

Expected: `NO-READERS`; a `PVTSSF_…` id prints.

- [ ] **Step 2: Delete via GraphQL**

```bash
gh api graphql -f query='mutation($id: ID!) {
  deleteProjectV2Field(input: {fieldId: $id}) {
    projectV2Field { ... on ProjectV2SingleSelectField { name } }
  }
}' -f id="$FID"
```

Expected: response names `Readiness`. If the mutation is rejected, fall back to the UI: project → Settings → Fields → Readiness → Delete, and note that in the report.

- [ ] **Step 3: Verify**

```bash
gh project field-list 1 --owner eranroseman --format json | jq -r '.fields[].name' | grep -c Readiness || echo GONE
```

Expected: `GONE`.

### Task 12: Board — drop PR #1514; archive-on-close (HITL)

- [ ] **Step 1: Remove the lone PR item**

```bash
IID=$(gh project item-list 1 --owner eranroseman --limit 200 --format json \
  | jq -r '.items[] | select(.content.number==1514 and .content.type=="PullRequest") | .id')
gh project item-delete 1 --owner eranroseman --id "$IID"
```

Expected: succeeds; re-listing shows no PullRequest items.

- [ ] **Step 2: Archive-on-close — hand to the owner (no API exists)**

ProjectV2 built-in workflows have no CLI/API mutation. Present this checklist and mark the step done when the owner confirms:

> Open https://github.com/users/eranroseman/projects/1 → ⋯ menu → **Workflows** → **Auto-archive items** → enable, with the filter `is:closed`. This makes the Done column self-empty; the 65 current Done items can be bulk-archived from the board (select column → Archive all).

### Task 13: File the U3-CANVAS.5 issue

**Interfaces:**
- Consumes: the retirement plan names three human-gated items keeping six plan files alive; two have issues (#1702, #1690), U3-CANVAS.5 has none (`gh issue list --state all --search "U3-CANVAS"` is empty).

- [ ] **Step 1: Extract the remaining steps verbatim**

```bash
cd /home/eranr/memoria-vault
grep -rn "U3-CANVAS" docs/superpowers/plans/ design-history/ | head
sed -n '30,45p' docs/superpowers/plans/2026-08-02-retire-alpha21-alpha23-working-records.md
```

From the owning plan file, copy U3-CANVAS.5's remaining two unchecked steps exactly as written.

- [ ] **Step 2: Create the issue**

```bash
gh issue create --label needs-owner \
  --title "U3-CANVAS.5: <one-line summary of the two remaining steps> (PI session)" \
  --body "$(cat <<'EOF'
## What this tracks

The last release-gating working-record item without a tracker endpoint. The
retirement plan (docs/superpowers/plans/2026-08-02-retire-alpha21-alpha23-working-records.md)
names three human-gated items keeping six plan files alive and alpha.23
unfrozen: LOOP.13 (#1702), U3-PLUG.11 (#1690), and this one.

## Remaining steps (verbatim from the owning plan)

<the two steps copied in Step 1, with the plan file cited by name — not by line number>

## Gate

PI session — requires a human driving the canvas surface. Not agent-executable.
EOF
)"
```

Fill both `<…>` slots from Step 1 before running. Expected: issue created with `needs-owner`.

---

## Part C — issue-body rewrites (one edit per issue; use the body pattern)

Every task here: fetch current body → verify the quoted anchor exists → apply the edits → push the body back → verify. If an anchor is missing, stop that task and report.

### Task 14: #1761 — one-character reference fix

- [ ] **Step 1: Verify and fix**

Anchor: the Problem 2 section cites `#1761` where it means the operation-dispatch PR `#1762`.

```bash
gh issue view 1761 --json body -q .body | grep -n "#1761"
```

Apply the body pattern: change that self-reference to `#1762`. Everything else in the issue verified to the character — touch nothing else.

### Task 15: #1727 — refresh citations, cross-reference #1731, scaffold the flag-convention decision

- [ ] **Step 1: Verify current line positions**

```bash
cd /home/eranr/memoria-vault
grep -n "machine_authored" src/memoria_vault/engine/api.py | head -3
grep -n "machine_authored" src/memoria_vault/runtime/worker.py | head -3
sed -n '1365,1375p' src/memoria_vault/vault/trusted_writer.py
```

Expected: api.py hit near :932; worker.py near :2099; trusted_writer.py:1369-1372 documents why the two fields differ.

- [ ] **Step 2: Edit the body (body pattern)**

1. Replace the stale citations `api.py:764` → `api.py::run_operation` (symbol form; note current line :932 in parentheses) and `worker.py:1663` → `worker.py::<enclosing symbol>` (note: the cited line never resolved on `main`; the flag sits near :2099 today).
2. Append:

```markdown
## Related decision (owner)

#1731 flags the same defect class — a trust boolean defaulting to trusted
beside a sibling deliberately made mandatory — at the adjacent seam, with the
opposite prescription (derive-and-delete vs make-required here).

One convention should win:

- **Keyword-required everywhere** — every authorship/composition flag must be
  passed explicitly. Pro: no silent trusted default anywhere. Con: noisier
  call sites; `trusted_writer.py:1369-1372` documents why the two fields
  differ, which may make the divergence principled.
- **Derive where derivable** — compute `machine_composed` (per #1731), keep
  explicit flags only where derivation is impossible. Pro: deletes a
  parameter; can't be passed wrongly. Con: derivation logic is a new seam.

Deciding here settles #1731's direction too.
```

### Task 16: #1731 — cross-reference back

- [ ] **Step 1: Edit (body pattern)**

Append one section:

```markdown
## Related

#1727 flags the same defect class at the adjacent seam with the opposite
prescription (make-required). The convention decision is scaffolded on #1727 —
resolve it there; this issue then follows the chosen convention.
```

### Task 17: #1691 — strike the shipped first move, retitle to the real scope

- [ ] **Step 1: Verify the first move shipped**

```bash
cd /home/eranr/memoria-vault
git log --oneline --all | grep -c 25f33afa || git show 25f33afa --stat | head -5
grep -n "_golden_diff" tests/floor_lib.py | head -2
```

Expected: `25f33afa` exists (PR #1722); `_golden_diff` near floor_lib.py:311.

- [ ] **Step 2: Edit (body pattern) and retitle**

1. Strike the "Suggested first move" block (its `floor_lib.py:328` change shipped in #1722; say so in one line with the sha).
2. Add one line naming the live front: the tmpfs-vs-real-filesystem control experiment.
3. Retitle — the comments record three drifted operations, the title names one:

```bash
gh issue edit 1691 --title "Floor goldens drift in CI (create-concept, capture-bibtex-source, red-team-argument): isolate the tmpfs variable"
```

Keep the issue open.

### Task 18: #1702 — strike the false precondition table, retitle to the PI-run item

- [ ] **Step 1: Verify the in-tree record supersedes the body**

```bash
sed -n '3089,3110p' /home/eranr/memoria-vault/docs/superpowers/plans/2026-07-15-alpha23-usable-loop.md
```

Expected: the 13-row precondition table with file:line + sha per row (the record that was corrected in-tree within four hours while the issue body rotted).

- [ ] **Step 2: Edit (body pattern) and retitle**

1. Strike the `## Blocked` precondition table ("Missing: O2 W.2 …") and the embedded defect section (its JSONL claim is false — `trusted_writer.py` writes the journal; Part A Task 3 removes the same claim in-tree).
2. Replace with:

```markdown
## Status

The six upstream preconditions this issue was filed against all landed by
2026-08-02 (`b4b62063`, `44ca3411`, `649c7e22`, `9645a1da`, `c3712748`; O2 A.2
shipped earlier). The current, corrected precondition record is the 13-row
table in `docs/superpowers/plans/2026-07-15-alpha23-usable-loop.md` (§ LOOP.13)
— trust it over any snapshot here.

What remains is the LOOP.13 run itself: PI-executed by construction.
```

3. Retitle:

```bash
gh issue edit 1702 --title "LOOP.13: run the usable-loop evaluation (PI session)"
```

### Task 19: #902 — replace the cleared U4 gate

- [ ] **Step 1: Verify U4 shipped and the residual gate**

```bash
cd /home/eranr/memoria-vault
git log --oneline a1d815c9 2fe8c9ca 8688a0e5 --max-count=3 2>/dev/null | head -3
sed -n '23p' src/memoria_vault/runtime/copi_skill/__init__.py
sed -n '138,145p' docs/superpowers/specs/2026-07-16-o1-onboarding-seed-design.md
```

Expected: the three shas exist; `copi_skill` in the roster; the spec's :141 names the single-script mechanism as the remaining precondition.

- [ ] **Step 2: Edit (body pattern)**

Replace the "revisit when the U4 bundle ships" paragraph with:

```markdown
## Status

The U4 co-PI bundle shipped 2026-08-02 (`a1d815c9`, `2fe8c9ca`, `8688a0e5`);
`copi_skill` is in the agent roster. The remaining gate is the single-script
mechanism named in `docs/superpowers/specs/2026-07-16-o1-onboarding-seed-design.md`
(§ mechanism) — an owner design decision, not landed code.
```

### Task 20: #1473 and #1474 — replace cleared preconditions, scaffold the shared kill-or-keep decision

- [ ] **Step 1: Verify the I1 gate cleared**

```bash
cd /home/eranr/memoria-vault
grep -n "telemetry_events" src/memoria_vault/vault/schema.sql | head -2
git log --oneline -3 b93e93dc 2>/dev/null | head -3
```

Expected: `telemetry_events` near schema.sql:437; `b93e93dc` deleted the i1-skeleton spec as fully folded.

- [ ] **Step 2: Edit #1473 (body pattern)**

Replace the paragraph gating on I1 instrumentation ("currently pre-plan per `2026-07-14-i1-skeleton-design.md`") with:

```markdown
## Status

I1 instrumentation shipped: `telemetry_events` is live in `schema.sql`, and
the i1-skeleton spec was deleted 2026-08-02 (`b93e93dc`) as fully folded — the
dead citation in the previous body text was the tell. The remaining gates are
(a) real-vault usage volume and (b) the decision below.

## Decision (owner) — shared with #1474

Is the ADR-62-era concept still wanted? One ruling closes both issues:

- **Keep** — the prose-check gate (here) and retry-reflection harness (#1474)
  proceed once usage data exists. Con: both were specified against a design
  three generations back.
- **Kill** — close both; if the need reappears it gets respecified against the
  current engine. Pro: deletes two of the oldest tracked rows.

Also: both sit in beta.1 while beta.2's description is literally
"data/security-gated units" — if kept, they likely move.
```

- [ ] **Step 3: Edit #1474 (body pattern)**

Same Status replacement, then:

```markdown
## Decision (owner)

Shared with #1473 — the kill-or-keep ruling is scaffolded there and closes
both. Three of this issue's four sections are near-verbatim copies of #1473's.
```

### Task 21: #1293 — retitle, fold comment 5's slice list into the body

- [ ] **Step 1: Verify the spec and the landed slices**

```bash
cd /home/eranr/memoria-vault
ls docs/superpowers/specs/2026-07-14-evidence-set-grounds-contract-design.md
grep -n "" src/memoria_vault/engine/evidence_review.py | sed -n '506p' | cut -c1-60
sed -n '2730p' src/memoria_vault/engine/knowledge.py | cut -c1-60
sed -n '304p' src/memoria_vault/vault/trusted_writer.py | cut -c1-60
gh issue view 1293 --json comments -q '.comments[4].body' | head -30
```

Expected: spec exists (merged `d3c61c0f`, #1481); the three cited lines hold slice implementations; comment 5 carries the §12 slice list.

- [ ] **Step 2: Edit (body pattern) and retitle**

1. Replace the "AC: a concrete schema/state table exists" framing with a status line: the contract spec exists (`2026-07-14-evidence-set-grounds-contract-design.md`, #1481); what remains is landing its §12 slices.
2. Paste comment 5's §12 slice list into the body as checkboxes; check the ones verified on `main` (the three lines from Step 1), leave the rest unchecked — slices 1 and 4 are unverified; do NOT close the issue.
3. Retitle:

```bash
gh issue edit 1293 --title "Land the remaining evidence-set / warrant contract slices (spec: 2026-07-14, #1481)"
```

### Task 22: Close #1748 (after Part A merges)

- [ ] **Step 1: Confirm the merge, then close with the receipt**

```bash
gh pr view --repo eranroseman/memoria-vault wip/backlog-fixes --json state,mergeCommit -q '.state+" "+.mergeCommit.oid' 2>/dev/null \
  || gh pr list --state merged --head wip/backlog-fixes --json number,mergeCommit
gh issue close 1748 --comment "Fixed in <merge sha>: guard deleted, blast-radius warning moved into tests/test_cockpit.py as a comment."
```

Expected: only runs once the PR state is MERGED. Fill `<merge sha>`.

### Task 23: #1504 — strike the landed row, delegate to #1753

- [ ] **Step 1: Verify the row landed**

```bash
git -C /home/eranr/memoria-vault log --oneline -1 a605e0ab
```

Expected: `a605e0ab` (PR #1707) — the `memoria review` reference row.

- [ ] **Step 2: Edit (body pattern)**

In the bolded "**Additive pages**" enumeration: mark the `memoria review` reference row landed (`a605e0ab`, #1707) and strike it from the outstanding set; replace the "how-tos for evidence review" bullet with a delegation line: "owned by #1753 (filed 2026-08-03 from the Diátaxis audit; same scope, more current)." Add a cross-reference line to #1651's relationship (it owns the migration-map rows that #1647/#1648/#1649 write).

### Task 24: #1529 — record the fired trigger, scaffold the remedy decision

This is the review's top finding: the issue's own escalation condition fired 2026-08-01 and the body still reads as a watch item.

- [ ] **Step 1: Verify every element of the claim**

```bash
cd /home/eranr/memoria-vault
git merge-base --is-ancestor 2a05a37b HEAD && echo BOOT-C2-ON-MAIN
grep -n "hooks.json" src/memoria_vault/runtime/bundles.py
grep -n "include_agent_bundle" src/memoria_vault/cli.py | head -3
python -c "import json,glob; p=glob.glob('src/**/.codex/hooks.json',recursive=True)+glob.glob('src/**/hooks.json',recursive=True); print(p); d=json.load(open(p[0])); print('PreToolUse' in str(d))"
```

Expected: `BOOT-C2-ON-MAIN`; `.codex/hooks.json` in `BUNDLE_FILES["agent"]`; the template has no `PreToolUse` handler (prints `False`). If any check fails, STOP — do not write a security claim you did not verify.

- [ ] **Step 2: Edit (body pattern)**

Prepend a status section (keep the whole existing body below it):

```markdown
## Trigger fired — 2026-08-01

The escalation condition below is no longer hypothetical. BOOT-C.2 landed as
`2a05a37b` (ancestor of `main`): `.codex/hooks.json` is in
`bundles.py::BUNDLE_FILES["agent"]`, which `cli.py` (under
`include_agent_bundle`) writes on **every fresh `memoria init`**, including
`--no-obsidian`. The materialized file is still the schema-1 deny **list** with
no `PreToolUse` handler, while the Claude side of the same roster ships an
executable `write_perimeter.py` that exits 2 unconditionally. Per this issue's
own terms, that is the reportable medium / P2 write-perimeter asymmetry: every
new vault ships a Codex write perimeter that does not enforce.

## Decision (owner)

- **Implement a real project-local Codex `PreToolUse` guard** — pick a schema
  Codex actually executes and ship it in the bundle. Pro: parity with the
  Claude side; the deny list stops being decorative. Con: requires choosing
  and testing a Codex hook mechanism that has no current in-repo precedent.
- **Delete the preventive-enforcement claim** — keep the deny list as
  documentation, and say so where the bundle is described. Pro: honest
  immediately, no new mechanism. Con: accepts permanent asymmetry in the
  write perimeter (AGENTS.md "Cross-tool parity" would need a matching edit).
```

Also update the pinned comment ("no supported fresh-init materializes it yet") with a one-line correction pointing at the new status section:

```bash
gh issue comment 1529 --body "Correction: the fresh-init trigger fired 2026-08-01 (\`2a05a37b\`) — see the '## Trigger fired' section now at the top of the body."
```

### Task 25: #1348 and #1526 — surface the K2 ruling home, scaffold both decisions

- [ ] **Step 1: Verify the ruling home and the glossary line**

```bash
cd /home/eranr/memoria-vault
grep -n "Fulltext storage (K2)" docs/superpowers/specs/2026-07-12-beta.1-consolidation.md
grep -n "^### Concept$" docs/reference/data-model/glossary.md
sed -n "$(grep -n '^### Concept$' docs/reference/data-model/glossary.md | cut -d: -f1),+6p" docs/reference/data-model/glossary.md
```

Expected: consolidation §6 near :291 holds "**Fulltext storage (K2) — OPEN**" with options A/B; the glossary's `### Concept` section holds the six-type umbrella and names `fulltext` as one of the six, with a folder home. (Locate the section by heading, never by line number — it moved from :155 to :299 in the 2026-08-06 glossary restructure, #1764, which is exactly the rot this plan's citation rule exists to prevent.)

- [ ] **Step 2: Edit #1348 (body pattern)**

Append:

```markdown
## Decision home

This restates K2, whose canonical open ruling lives in
`docs/superpowers/specs/2026-07-12-beta.1-consolidation.md` §6 ("Fulltext
storage (K2) — OPEN", options A/B, "→ Decide B + where the PDF/artifact
lives"). Resolve it there and record the outcome here. #1526's option 1
("add `fulltext` to browse/list") dies if the answer is B — the native
blocking edge on #1526 encodes that.
```

- [ ] **Step 3: Edit #1526 (body pattern)**

Append:

```markdown
## Prior art the options must answer to

`docs/reference/data-model/glossary.md` (§ Concept, the six-type umbrella,
landed `d85d8799` 2026-07-15 — fifteen days before this issue) may already bind
this decision: AGENTS.md makes that file canonical and none of the three
options above cites it. If it binds, this issue narrows to a conformance
sweep and becomes agent-executable. Blocked by #1348 (K2): option B there
kills option 1 here and forces option 3.
```

### Task 26: #447 — decision format or close

- [ ] **Step 1: Edit (body pattern)**

The body is 299 bytes with two identical URLs and two owner comments (2026-07-07, 2026-07-14) independently concluding "underspecified." Replace the body with:

```markdown
## Decision (owner)

Open since 2026-06-12; triaged twice (2026-07-07, 2026-07-14), both times
reaching "underspecified." Third touch should be a ruling, not a re-read:

- **CLI flag** (`memoria open --editor vscode`) — explicit, no magic. Con: one
  more flag to remember.
- **Auto-detect** (use `code` if on PATH) — zero config. Con: silent behavior
  change on machines that happen to have VS Code.
- **Config key** (vault settings) — set once. Con: the settings surface grows
  for an optional adapter.
- **Close** — no third editor adapter until a real session needs one. (Obsidian
  is seeded; Zotero/MCP are the named optional adapters.)

Milestone is beta.2 ("data/security-gated units") — if any build option is
picked it stays; if Close, close.
```

### Task 27: #1760 — cite the evidence, confirm decision shape

- [ ] **Step 1: Verify the cited surfaces**

```bash
cd /home/eranr/memoria-vault
sed -n '378p;425p' src/memoria_vault/engine/api.py | cut -c1-70
sed -n '261,271p' tests/test_surface_contract.py | head -4
```

Expected: the two evidence-review verbs at api.py:378 and :425; the transport exemption at test_surface_contract.py:261-271.

- [ ] **Step 2: Edit (body pattern)**

The body already carries "## Decision required" with three options and no recommendation — the right shape; leave the options untouched. Append only an evidence block:

```markdown
## Current surfaces

The two verbs: `engine/api.py::evidence_review_item` (:378) and
`engine/api.py::resolve_evidence` (:425). The standing transport exemption:
`tests/test_surface_contract.py:261-271`. Whichever option wins, that
exemption block is where the test-side change lands.
```

### Task 28: #1652 and #1653 — cross-reference, scaffold the shared repair-flow question

- [ ] **Step 1: Edit #1652 (body pattern)**

Append:

```markdown
## Decision (owner) — shared with #1653

Both how-tos are blocked on the same unconfirmed flow: what re-satisfies a
mint-once binding after the claim block changed. Confirm the repair flow
first; both docs then write themselves. #1753 (review-queue how-to)
references the same machinery — keep the three consistent.
```

- [ ] **Step 2: Edit #1653 (body pattern)**

Append the mirror:

```markdown
## Decision (owner) — shared with #1652

Same gate: the repair flow ("what re-satisfies a mint-once binding after the
claim block changed") is unconfirmed. Scaffolded on #1652; resolve once,
unblock both. Cross-cutting with #1753.
```

### Task 29: #1520 — scaffold the AC1 amendment

- [ ] **Step 1: Verify the contradiction**

```bash
cd /home/eranr/memoria-vault
grep -n "_record_token_usage" src/memoria_vault/engine/operations.py | head -3
sed -n '1265,1270p' src/memoria_vault/engine/operations.py
```

Expected: `_record_token_usage(result, settings)` near :1267, documented as "the tranche's single point of contact with the SDK's `result.usage()`".

- [ ] **Step 2: Edit (body pattern)**

Replace the stale status paragraph ("main still has the pre-COST LOOP.3 shape" — false since `3a3754da`, ~17h after filing) with:

```markdown
## Status

The canonical COST dict shipped in `3a3754da`:
`operations.py::run_llm_operation` returns `{"text","usage","cost_usd",
"elapsed_s"}`, and the charge (:1317) precedes the text read (:1318). AC2,
AC3, AC5 verified met on `main`.

## Decision (owner) — AC1

AC1 as written forbids what the shipped design requires:
`_record_token_usage(result, settings)` is documented as "the tranche's single
point of contact with the SDK's `result.usage()`" (operations.py:1267). Amend
AC1 to name that one permitted call site, then close this issue — or state why
the single-point-of-contact design itself should change.
```

### Task 30: #1572 — scaffold the wording decision

- [ ] **Step 1: Verify the triplication**

```bash
cd /home/eranr/memoria-vault
grep -rn "MANUAL_OPEN_FALLBACK" src/ docs/ | head -6
```

Expected: the wording near `onboarding.py:202`, plus the spec (:240) and plan (:7182/:7264) copies.

- [ ] **Step 2: Edit (body pattern)**

Append:

```markdown
## Decision (owner)

The `MANUAL_OPEN_FALLBACK` wording lives in three places (onboarding.py:202,
the O1 spec :240, the surfaces plan :7182/:7264). Whatever wording wins — with
or without the vault-switcher step — pick it once and update all three, or the
fixed copy re-drifts. The code copy is the one users see.
```

---

## Explicitly out of scope (stated, not silently dropped)

- **Resolving any of the 11 owner-calls** — scaffolding only; every ruling is the owner's.
- **The #1529 remedy implementation** — whichever option wins is its own security-reviewed branch.
- **Milestone backfill** of the 21 unmilestoned issues and the ten dead alpha milestones — rejected by the review as ceremony (two prior sweeps didn't stick).
- **Retroactive `needs-triage` sweep** — the intake convention applies to issues filed from now on; the existing 33 are ratified by this plan's own review.
- **`.out-of-scope/` KB** — rejected by the rethink design: a curated store dies of neglect here (measured: Readiness, `documentation`); closed + `wontfix` is the same fact with zero new mechanism, searched at intake.
- **`setup-matt-pocock-skills` / `to-tickets` / `triage` adoption** — rejected; principles adopted instead (edges, claims, intake, decision scaffolds), stored-state machine declined.
- **The "tracking unit" owner-call** (package issues vs per-deliverable issues) — has no issue to scaffold; noted in the #1504 edit's cross-reference line, otherwise left for the owner.
- **#1293 closure** — slices 1 and 4 unverified; the issue stays open by design.

## Execution notes for SDD

- Parts B and C need no worktree — they are `gh` writes. Only Tasks 1–6 touch the repo; keep every path inside `.claude/worktrees/backlog-fixes`.
- Part C tasks are mutually independent and parallelizable, EXCEPT: Task 15 before Task 16 (the decision block Task 16 points at must exist), Task 25's Step 2 before Step 3 (same reason), Task 28's two steps in order.
- Task 9 (edges) after Task 8 (labels) is cosmetic ordering only; Tasks 7b, 8, and 13 after Task 7 (they need its labels).
- Task 7b's retitles and Part C's retitles (Tasks 17, 18, 21) touch disjoint prefixes — Part C sets complete new titles with no prefixes, so order between them does not matter.
- Task 22 is the only merge-gated task.
