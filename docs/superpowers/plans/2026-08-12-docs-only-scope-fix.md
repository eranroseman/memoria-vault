# Docs-Only Scope Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop `VERIFY_DOCS_ONLY=1` from firing on pull requests that change runtime-shipped Markdown, which today skips every test that validates it.

**Architecture:** `.github/workflows/verify.yml` classifies a PR as docs-only when every changed file matches `^design-history/` or `\.md$`. Sixty-six tracked Markdown files live under `src/` as package data, so a PR touching only those is misclassified. The fix narrows the Markdown half of the classifier to exclude `^src/`, and a test pins the narrowing so it cannot silently regress.

**Tech Stack:** GitHub Actions, bash, pytest, PyYAML.

## Global Constraints

- Correctness command is `python scripts/verify`. It is the one gate.
- Stage explicit paths in `git add`. Never `git add -A`, `--all`, `-u`, or `.`.
- `verify` is a **required check**. It must report on every PR, so the workflow keeps no `paths:` filter — this plan narrows what docs-only *skips*, never whether the job runs.
- Safe default: if the changed-file list cannot be read, run the full roster. That behaviour must survive this change.
- New tests carry `pytestmark = pytest.mark.static` and import `ROOT` from `tests.paths`.
- No VS Code changes: this plan touches CI classification only, and nothing in it is editor-visible.
- Every task verifies current state with a command and its expected result before changing anything.

---

### Task 1: Prove the hole, then close it

**Files:**
- Modify: `.github/workflows/verify.yml` (the `Detect change scope` step)

**Interfaces:**
- Consumes: nothing.
- Produces: the corrected classifier. Task 2 pins it.

- [ ] **Step 1: Confirm runtime Markdown exists under `src/`**

Run:

```bash
git ls-files 'src/**/*.md' | wc -l
git ls-files 'src/**/*.md' | head -3
grep -n 'operations/\*.md' pyproject.toml
```

Expected: `66`, three paths under `src/memoria_vault/product/capabilities/operations/`, and a `pyproject.toml` line shipping `"*.md"` as package data for `memoria_vault.product.capabilities.operations`. These files are program content, not documentation.

- [ ] **Step 2: Confirm the tests that validate them are dropped under docs-only**

Run:

```bash
grep -rl "capabilities/operations" tests/
for f in tests/test_capabilities.py tests/test_patterns.py tests/test_search_index.py tests/test_cli_workspace_requests.py tests/test_exploration_trace.py; do
  echo -n "$f: "; grep -m1 "pytestmark" "$f"
done
grep -n "PYTEST_MARKERS\|static.*if arg ==" scripts/verify | head -5
```

Expected: five test files listed, each carrying `pytestmark = pytest.mark.contract`, and `scripts/verify` swapping `PYTEST_MARKERS` for the literal `static` under docs-only. `contract` is not `static`, so all five are skipped — along with the wheel gate, the e2e smoke, `compileall`, and `memoria --version`, all marked `docs=False`.

- [ ] **Step 3: Reproduce the misclassification**

Run:

```bash
files="src/memoria_vault/product/capabilities/operations/capture-source.md"
docs_only=false
printf '%s\n' "$files" | grep -qvE '(^design-history/|\.md$)' || docs_only=true
echo "docs_only=$docs_only  <-- should be false; this file is runtime package data"
```

Expected: `docs_only=true`. That is the bug, reproduced with the workflow's exact expression.

- [ ] **Step 4: Replace the classifier**

In `.github/workflows/verify.yml`, in the `Detect change scope` step, replace the `docs_only` block. The full `run:` becomes:

```yaml
        run: |
          files="$(gh pr view "$PR_NUMBER" --json files --jq '.files[].path' || true)"
          printf 'changed files:\n%s\n' "$files"
          # Safe defaults: if the diff can't be read, run everything (full verify).
          ps1=true
          docs_only=false
          if [ -n "$files" ]; then
            printf '%s\n' "$files" | grep -qE '\.ps1$' || ps1=false
            # A file is documentation when it is under design-history/ or is
            # Markdown that is NOT shipped as package data. 66 tracked *.md live
            # under src/ (capabilities/operations/*.md, workspace_seed/) and are
            # program content: the tests that validate them are `contract`, which
            # the docs-only narrowing drops, so a PR editing only those files
            # would skip every check that reads them.
            remaining="$(
              { printf '%s\n' "$files" | grep -vE '^design-history/' | grep -vE '\.md$'
                printf '%s\n' "$files" | grep -E '^src/.*\.md$'
              } | grep -c . || true
            )"
            [ "$remaining" = "0" ] && docs_only=true
          fi
          echo "ps1=$ps1" >> "$GITHUB_OUTPUT"
          echo "docs_only=$docs_only" >> "$GITHUB_OUTPUT"
          echo "scope -> ps1=$ps1 docs_only=$docs_only"
```

- [ ] **Step 5: Verify the new classifier on all four cases**

Run:

```bash
classify() {
  files="$1"
  remaining="$(
    { printf '%s\n' "$files" | grep -vE '^design-history/' | grep -vE '\.md$'
      printf '%s\n' "$files" | grep -E '^src/.*\.md$'
    } | grep -c . || true
  )"
  [ "$remaining" = "0" ] && echo "docs_only=true" || echo "docs_only=false"
}
echo -n "published docs only        -> "; classify "docs/how-to-guides/setup/quickstart.md"
echo -n "design-history only        -> "; classify "design-history/2026-08/notes.md"
echo -n "runtime package-data md    -> "; classify "src/memoria_vault/product/capabilities/operations/capture-source.md"
echo -n "docs plus a Python change  -> "; classify "$(printf 'docs/a.md\nsrc/memoria_vault/cli.py\n')"
```

Expected, in order: `true`, `true`, `false`, `false`. The third is the fix.

- [ ] **Step 6: Verify the workflow still parses**

Run:

```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/verify.yml')); print('workflow yaml ok')"
pre-commit run yamllint --hook-stage manual --files .github/workflows/verify.yml
```

Expected: `workflow yaml ok`, then yamllint PASS.

- [ ] **Step 7: Commit**

```bash
git add .github/workflows/verify.yml
git commit -m "fix: stop docs-only narrowing on runtime package-data Markdown

66 tracked *.md ship under src/ as package data. A PR touching only those was
classified docs-only, which drops the wheel gate, the e2e smoke, and the five
contract tests that actually read them."
```

---

### Task 2: Pin the narrowing

**Files:**
- Create: `tests/test_docs_only_scope.py`

**Interfaces:**
- Consumes: the classifier from Task 1.
- Produces: nothing.

The classifier lives in shell inside a workflow, where no test reaches it and a regex that silently over-matches is green. This test executes the workflow's own expression against known inputs, so a future edit that re-widens the match fails loudly instead of quietly skipping gates.

- [ ] **Step 1: Verify no such test exists**

Run:

```bash
grep -rln "docs_only\|VERIFY_DOCS_ONLY" tests/*.py || echo "no test - as expected"
```

Expected: `no test - as expected`.

- [ ] **Step 2: Write the test**

Create `tests/test_docs_only_scope.py`:

```python
"""The docs-only narrowing must not fire on runtime-shipped Markdown.

`.github/workflows/verify.yml` sets VERIFY_DOCS_ONLY=1 when a PR's whole diff is
documentation, which drops the wheel gate, the offline smoke, `memoria
--version`, and narrows pytest from six markers to `static`. Sixty-six tracked
*.md files ship under src/ as package data (capabilities/operations/*.md and
workspace_seed/), and every test that reads them is `contract` — so
misclassifying them skips exactly the checks that would catch a break.

This extracts the classifier from the workflow and runs it, rather than
asserting on the regex text: a test that only greps for a pattern passes on a
pattern that is present and wrong.
"""

from __future__ import annotations

import re
import subprocess

import pytest
import yaml

from tests.paths import ROOT

pytestmark = pytest.mark.static

WORKFLOW = ROOT / ".github/workflows/verify.yml"


def _scope_script() -> str:
    """The `Detect change scope` step's shell body, lifted from the workflow."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    # The gate runs in the `shards` matrix job (#1824); `verify` is the fan-in
    # that owns the required-check name and has no scope step.
    steps = workflow["jobs"]["shards"]["steps"]
    step = next(s for s in steps if s.get("id") == "scope")
    return step["run"]


def _classify(paths: list[str]) -> bool:
    """Run the workflow's own classifier over `paths`, return its docs_only verdict."""
    body = _scope_script()
    # Drop the two lines that reach GitHub; feed the file list in directly.
    body = re.sub(r'^\s*files=.*$', 'files="$FILES"', body, count=1, flags=re.M)
    body = re.sub(r'^\s*printf .changed files.*$', "", body, count=1, flags=re.M)
    body = re.sub(r'^\s*echo "\w+=.*>> "\$GITHUB_OUTPUT"\s*$', "", body, flags=re.M)
    # The trailing `echo "scope -> ..."` is a human progress line, not output we
    # parse. Left in, it lands on stdout ahead of the verdict and every True case
    # silently reads as False.
    body = re.sub(r'^\s*echo "scope ->.*$', "", body, flags=re.M)
    result = subprocess.run(
        ["bash", "-c", body + '\nprintf "%s" "$docs_only"'],
        env={"FILES": "\n".join(paths), "PATH": "/usr/bin:/bin"},
        text=True,
        capture_output=True,
        check=True,
    )
    # Last line only, so a stray echo left in the step cannot silently invert a verdict.
    lines = result.stdout.strip().splitlines()
    assert lines, f"classifier produced no verdict; stderr: {result.stderr}"
    return lines[-1].strip() == "true"


@pytest.mark.parametrize(
    ("paths", "expected", "why"),
    [
        (["docs/how-to-guides/setup/quickstart.md"], True, "published docs are documentation"),
        (["design-history/2026-08/chapter.md"], True, "the frozen record is documentation"),
        (["README.md"], True, "root Markdown is documentation"),
        (
            ["src/memoria_vault/product/capabilities/operations/capture-source.md"],
            False,
            "package data read by contract tests, not documentation",
        ),
        (
            ["src/memoria_vault/product/workspace_seed/CLAUDE.md"],
            False,
            "seeded into every vault; package data",
        ),
        (["docs/a.md", "src/memoria_vault/cli.py"], False, "a code change is in the diff"),
        (["scripts/verify"], False, "the gate itself is not documentation"),
    ],
)
def test_classifier_verdicts(paths: list[str], expected: bool, why: str):
    assert _classify(paths) is expected, f"{paths}: expected docs_only={expected} because {why}"


def test_runtime_markdown_actually_exists_under_src():
    """If this ever returns nothing, the parametrised cases above stop testing anything."""
    listing = subprocess.run(
        ["git", "ls-files", "src/**/*.md"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    shipped = listing.stdout.split()
    assert len(shipped) > 50, (
        f"expected the package-data Markdown corpus, found {len(shipped)} files; "
        "if it genuinely moved, update this test and the workflow comment together"
    )
```

- [ ] **Step 3: Run the test**

Run:

```bash
python3 -m pytest tests/test_docs_only_scope.py -q
```

Expected: PASS, 8 tests. If `_classify` raises, print the transformed body with `python3 -c "import tests.test_docs_only_scope as t; print(t._scope_script())"` and check the three `re.sub` calls still match the workflow's current text — they strip the `gh pr view` call and the `$GITHUB_OUTPUT` writes, which do not exist outside Actions.

- [ ] **Step 4: Prove the test catches the old bug**

Run:

```bash
git stash push .github/workflows/verify.yml
python3 -m pytest tests/test_docs_only_scope.py -q
git stash pop
python3 -m pytest tests/test_docs_only_scope.py -q
```

Expected: FAIL on the two `src/` cases with the pre-fix workflow, then PASS after restoring. If Task 1 was already committed, revert the workflow locally instead of stashing.

**Read the failure, do not just count it.** The pre-fix run must fail on *exactly* the two `src/` cases and pass the other five. If every case fails, `_classify` itself is broken — most likely the `re.sub` calls no longer match the step's text — and both the pre-fix and post-fix runs would fail, which reads like a working regression test and is not.

- [ ] **Step 5: Run the full gate**

Run:

```bash
python scripts/verify
```

Expected: `verify: OK`.

- [ ] **Step 6: Commit**

```bash
git add tests/test_docs_only_scope.py
git commit -m "test: pin the docs-only classifier against runtime Markdown

Executes the workflow's own shell rather than grepping its regex: a test that
matches on pattern text passes on a pattern that is present and wrong."
```

---

## Self-Review

**Spec coverage.** The session flagged this as an aside outside formatter scope; it is a correctness fix in CI classification and gets both halves — the fix (Task 1) and a regression test that runs the real classifier (Task 2).

**Placeholder scan.** No TBDs. Every shell block is literal and runnable at a prompt, including the `classify()` helper in Task 1 Step 5 that lets the fix be verified before it is committed.

**Type consistency.** `docs_only` is the shell variable name in the workflow and the string compared in `_classify`. `_scope_script()` and `_classify()` keep their signatures. The step is located by `id: scope`, which is what the workflow already sets.

**Risk worth naming.** `_classify` transforms the workflow's shell with three regexes. If the step's text changes shape — say the `gh pr view` line is reformatted across two lines — the substitutions stop matching and the test fails loudly with a bash error rather than silently passing. That is the correct failure direction, but the next person to edit that step will need to update the regexes; the test docstring says why they exist.
