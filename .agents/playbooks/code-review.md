# Code review

Use this playbook for a branch, commit, pull request, or working-tree diff. A
review identifies problems; it does not silently rewrite the patch unless the
user also asks for fixes.

## 1. Establish scope

1. Read [`AGENTS.md`](../../AGENTS.md).
2. Resolve the exact base and head or local patch being reviewed.
3. Check `git status --short --branch` and list changed files.
4. Read each changed file in full, plus only the supporting code needed to trace
   affected behavior.
5. Treat commit messages and PR descriptions as context, not proof.

## 2. Review behavior

For every changed behavior, trace:

- Inputs and callers
- State transitions and side effects
- Error and retry paths
- Output and compatibility contracts
- Permissions and trust boundaries
- Existing tests and untested edges

Prioritize:

1. Data loss, security regressions, and broken invariants
2. Incorrect behavior and silent failure
3. Compatibility and operational regressions
4. Missing tests for plausible failures
5. Complexity that obscures correctness

Do not report personal style preferences unless they create a concrete
maintenance or correctness risk. Confirm that apparent problems are reachable
before presenting them as findings.

## 3. Run checks

Run the narrowest relevant tests first. Use the repository gate when the change
has broad or shared impact:

```bash
python3 scripts/verify pr
```

Also run language- or component-specific checks required by `AGENTS.md`. Record
commands that could not be run and why.

## 4. Report

Use [the review report template](../templates/review-report.md).

- Findings come first, ordered Critical, High, Medium, Low.
- Every finding names an exact file and line, user-visible impact, and evidence.
- Separate confirmed findings from open questions.
- If there are no findings, say so explicitly and state remaining test gaps or
  environmental limitations.
