# Verify-Gate Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `scripts/verify` the only living statement of the gate roster — delete the stale prose mirrors, encode docs-only scope as data instead of substring matching, and stop the gitleaks CI job from installing tooling it never uses.

**Architecture:** Three independent, behavior-preserving changes from the 2026-08-03 rethink-audit of the test suite / pre-commit / CI pipeline (migrate steps 1–3). Task 1 deletes roster/marker restatements from `tests/README.md` and `CONTRIBUTING.md` (both currently contradict the code: they say the gate runs `static`/`unit`/`contract` only, while `scripts/verify` runs everything except `live` and `slow`). Task 2 changes `GATES` from `list[list[str]]` to a list of small `Gate` entries carrying a `docs` flag, deleting the `_DOCS_SKIP` substring tuple; `_gates_for_run(docs_only)` keeps its exact signature and output. Task 3 narrows the gitleaks workflow's install line to just the pinned `pre-commit`, keeping `requirements-dev.txt` as the single pin source.

**Tech Stack:** Python 3.12 stdlib (`dataclasses`), pytest (`tests/test_verify_script.py`, marker `static`), pre-commit-managed lint, GitHub Actions YAML.

**Out of scope (decided at audit time):** directory-based test tiers (audit migrate step 4 — close call, standalone PR if ever); any change to CI scope detection, the per-checkout lock, or pytest invocation (audit migrate step 5 — explicitly "no change"). The stale roster mentions inside `design-history/` and old `docs/superpowers/` plans/specs are frozen records — do NOT edit them.

## Global Constraints

- Work in an isolated worktree: from the main checkout run `git worktree add .claude/worktrees/verify-gate-consolidation -b wip/verify-gate-consolidation origin/main`, then `EnterWorktree(path: ".claude/worktrees/verify-gate-consolidation")`. (`main` is protected; the `no-commit-to-branch` hook blocks direct commits to it.)
- Stage explicit paths only — the repo's `PreToolUse` hook rejects `git add -A`/unbounded staging (shared index rule, AGENTS.md).
- The one gate: every task ends with `python scripts/verify` printing `verify: OK`. The first run in a fresh worktree rebuilds `test-vault/` via the e2e smoke, so it is slower than later runs.
- `verify` and `gitleaks` are required checks matched **by name** in branch protection. Never rename the workflow files' `name:`/job ids.
- `tests/README.md` and `CONTRIBUTING.md` are spell-checked by cspell (scope `**/*.md`) but NOT covered by vale/markdownlint (those gate `docs/` only). The replacement prose below uses existing vocabulary only; if you deviate and cspell fails, fix the wording rather than adding words to `project-words.txt`.
- End every commit message with:

  ```
  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  ```

## File Structure

- Modify: `tests/README.md` (levels table + gate prose, lines 3–4 stale cross-ref and lines 18–32)
- Modify: `CONTRIBUTING.md` (Testing and verification section, lines 57–62)
- Modify: `scripts/verify` (roster section: `Gate` dataclass, `GATES`, `_gates_for_run`, delete `_DOCS_SKIP`)
- Modify: `tests/test_verify_script.py` (three joins over `GATES`, one new default-scope test)
- Modify: `.github/workflows/gitleaks.yml` (one `run:` line)

No new files. Nothing else in the repo references `GATES`, `_DOCS_SKIP`, or `_gates_for_run` (verified by repo-wide grep; the only reader outside `scripts/verify` is `tests/test_verify_script.py`, via `runpy`, not import).

---

### Task 1: Delete the stale roster mirrors from tests/README.md and CONTRIBUTING.md

Both files claim the gate runs the `static`/`unit`/`contract` levels and that `package`/`runtime` are "never in the gate". `scripts/verify:42` runs `static or unit or contract or runtime or package or floor` (CHANGELOG.md:124 records the widening). Fix by deletion: docs point at `PYTEST_MARKERS` in `scripts/verify`, they do not restate it.

**Files:**
- Modify: `tests/README.md:3-4` (stale AGENTS.md section reference)
- Modify: `tests/README.md:18-32` (levels table "Runs" column + gate prose)
- Modify: `CONTRIBUTING.md:57-62`

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: nothing later tasks rely on (prose only).

- [ ] **Step 1: Fix the stale cross-reference in tests/README.md**

`tests/README.md` lines 3–4 currently read:

```markdown
Pytest suite for the repo's test levels (see AGENTS.md → *Test before opening a
PR*). Tests live here as standalone files, not inline in shipped modules, so the
```

AGENTS.md has no such section (its verify facts live under *Ground truth*). Replace with:

```markdown
Pytest suite for the repo's test levels (see AGENTS.md → *Ground truth*).
Tests live here as standalone files, not inline in shipped modules, so the
```

- [ ] **Step 2: Replace the levels table and gate prose in tests/README.md**

Lines 18–32 currently read:

```markdown
| Level | Purpose | Runs |
| --- | --- | --- |
| `static` | formatting, lint, schema, spell, design history, workflow safety | `scripts/verify`, every PR |
| `unit` | deterministic Python behavior | `scripts/verify`, every PR |
| `contract` | CLI, operations, capability manifests, concept writers, projections | `scripts/verify`, every PR |
| `package` | wheel build/install smoke, e2e smoke, and package-facing helper tests | on demand (built wheel) |
| `runtime` | worker loops, recovery, idempotence, state transitions, long checks | on demand (disposable workspace) |
| `live` | real external services/providers | manual only (live provider) |

`python scripts/verify` runs the `static`/`unit`/`contract` levels (plus lint,
product gates, offline smoke, and syntax checks). Target one level with
`python3 -m pytest tests/ -q -m unit`; use `-m "not slow"` for the fast local
loop. The `package`, `runtime`, and `live` levels run on demand after
`pip install -e .` — e.g. `python3 -m pytest tests/ -q -m package` — never in the
gate.
```

Replace with (the "Runs" column and the per-level run claims are the drift source — delete, don't correct):

```markdown
| Level | Purpose |
| --- | --- |
| `static` | formatting, lint, schema, spell, design history, workflow safety |
| `unit` | deterministic Python behavior |
| `contract` | CLI, operations, capability manifests, concept writers, projections |
| `package` | wheel build/install smoke, e2e smoke, and package-facing helper tests |
| `runtime` | worker loops, recovery, idempotence, state transitions, long checks |
| `live` | real external services/providers |

Which levels the gate runs is owned by `PYTEST_MARKERS` in `scripts/verify` —
read it there rather than restating it here. Target one level with
`python3 -m pytest tests/ -q -m unit`; use `-m "not slow"` for the fast local
loop; run a level the gate excludes the same way on demand (e.g. `-m live`).
```

- [ ] **Step 3: Replace the marker restatement in CONTRIBUTING.md**

Lines 57–62 currently read:

```markdown
`python scripts/verify` is the one gate. It runs lint, the product-integrity
checks, the `static`/`unit`/`contract` test suite, an offline end-to-end smoke,
and syntax checks; CI requires it plus `gitleaks`. Target a subset while
iterating with `python3 -m pytest tests/ -q -m unit` (or `contract`, `static`).
The `package`, `runtime`, and `live` test markers need a built wheel, a
disposable workspace, or a live provider and are run on demand, not in the gate.
```

Replace with (the coarse category summary — lint, product gates, tests, smoke, syntax — stays; it matches AGENTS.md and survives roster edits. The marker list goes):

```markdown
`python scripts/verify` is the one gate. It runs lint, the product-integrity
checks, the test suite, an offline end-to-end smoke, and syntax checks; CI
requires it plus `gitleaks`. Which pytest levels the gate runs is owned by
`PYTEST_MARKERS` in `scripts/verify`. Target a subset while iterating with
`python3 -m pytest tests/ -q -m unit` (or `contract`, `static`); levels the
gate excludes run the same way on demand.
```

- [ ] **Step 4: Run the gate**

Run: `python scripts/verify`
Expected: `verify: OK` (cspell and removed_surface_gate both cover these files; the replacement prose uses existing vocabulary).

- [ ] **Step 5: Commit**

```bash
git add tests/README.md CONTRIBUTING.md
git commit -m "docs: point level-selection prose at PYTEST_MARKERS instead of restating it

tests/README.md and CONTRIBUTING.md still described the pre-alpha.21 gate
(static/unit/contract only, package/runtime 'never in the gate');
scripts/verify has run everything except live and slow since the widening.
Delete the restatements rather than correct them — the roster's one
legitimate mirror is tests/test_verify_script.py.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Roster entries carry docs-only scope as data; delete `_DOCS_SKIP`

`_DOCS_SKIP` selects gates to drop under `VERIFY_DOCS_ONLY=1` by substring-matching fragments (`"bash -n"`, `"wheel_gate.py"`) against the joined command. Encode the same fact on each roster entry instead. `_gates_for_run(docs_only: bool) -> list[list[str]]` keeps its exact signature and output — `tests/test_verify_script.py::test_docs_only_scope_narrows_the_roster` already pins the narrowed roster and proves behavior is unchanged.

**Files:**
- Test: `tests/test_verify_script.py` (edit first — TDD)
- Modify: `scripts/verify:55-144` (roster section)

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: `Gate` dataclass in `scripts/verify` with fields `cmd: list[str]` and `docs: bool = True`; `GATES: list[Gate]`; `_gates_for_run(docs_only: bool) -> list[list[str]]` unchanged. The mirror test reads these via `runpy` (`_verify_namespace()`).

- [ ] **Step 1: Update the mirror test to the new roster shape (failing first)**

In `tests/test_verify_script.py`, make exactly these changes.

Line 22 (in `test_roster_covers_lint_tests_and_product_gates`):

```python
    flat = [" ".join(gate.cmd) for gate in _verify_namespace()["GATES"]]
```

Line 46 (in `test_retired_doctors_are_absent_from_the_roster`):

```python
    flat = " ".join(" ".join(gate.cmd) for gate in _verify_namespace()["GATES"])
```

Line 73 (in `test_docs_only_scope_narrows_the_roster`):

```python
    assert full == [" ".join(gate.cmd) for gate in namespace["GATES"]]
```

Then add this test after `test_docs_only_scope_narrows_the_roster` (pins the fail-safe direction: an entry that forgets to declare scope runs under docs-only; skipping is the explicit exception):

```python
def test_gate_entries_run_under_docs_scope_unless_opted_out() -> None:
    # Fail-safe default: a new roster entry that never considered docs-only
    # scope still runs there; docs=False is the explicit "provably cannot be
    # affected by a docs diff" claim.
    gate_type = _verify_namespace()["Gate"]

    assert gate_type(["echo", "ok"]).docs is True
```

- [ ] **Step 2: Run the mirror test to verify it fails**

Run: `env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_verify_script.py -q`
Expected: FAIL — `AttributeError: 'list' object has no attribute 'cmd'` in the three edited tests, `KeyError: 'Gate'` in the new one.

- [ ] **Step 3: Rewrite the roster section of scripts/verify**

Add to the imports block (after `from __future__ import annotations`, alphabetical among stdlib imports):

```python
from dataclasses import dataclass
```

Replace the `GATES` definition (`scripts/verify:50-115`, from the `# Source of truth…` comment through the closing `]`) with — every existing comment stays:

```python
@dataclass(frozen=True)
class Gate:
    """One verify step.

    `docs` is True unless a docs-only diff (`*.md` / `design-history/`) provably
    cannot affect the step; False is the explicit opt-out that drops it under
    `VERIFY_DOCS_ONLY=1`, so a new entry that never considered docs scope still
    runs there.
    """

    cmd: list[str]
    docs: bool = True


# Source of truth for what "verified" means; tests/test_verify_script.py mirrors
# this roster. Lint runs the manual-stage pre-commit hooks (ruff, ruff-format,
# yamllint, shellcheck, cspell, markdownlint); the commit-stage hooks
# (gitleaks, no-commit-to-branch) are pinned out of the manual stage so this
# never trips no-commit-to-branch on the post-merge main run.
GATES: list[Gate] = [
    Gate(["pre-commit", "run", "--hook-stage", "manual", "--all-files"]),
    Gate(["python3", "scripts/checks/schema_doc_drift.py"]),
    Gate(["python3", "scripts/checks/removed_surface_gate.py"]),
    Gate(["python3", "scripts/checks/checked_terminology_gate.py"]),
    Gate(["python3", "scripts/checks/plugin_provenance_doctor.py"]),
    Gate(["python3", "scripts/checks/doc_claims_gate.py"]),
    Gate(["python3", "scripts/checks/control_plane_actor_gate.py"]),
    # a docs-only diff provably cannot change packaging, so the wheel gate is skipped
    Gate(["python3", "scripts/checks/wheel_gate.py"], docs=False),
    Gate(
        [
            "env",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
            "python3",
            "-m",
            "pytest",
            "tests/",
            "-q",
            # Parallelize across cores (pytest-xdist); `-p xdist` because plugin
            # autoload is disabled above. The vault-mutating tests are I/O-bound and
            # per-test isolated (tmp_path), so this cuts the suite ~3x. `-m` stays
            # last so the docs-only narrowing can swap the marker for `static`.
            "-n",
            "auto",
            "-p",
            "xdist",
            # 1733: the default `--dist load` scatters a module's tests across
            # workers, so module-scoped fixtures (the ~30s seed_vault builds in
            # test_floor_sweep_reads / test_read_api_scope_walk) are rebuilt once
            # per worker. loadgroup pins only the xdist_group-marked modules to a
            # single worker each (one fixture build per file) while everything
            # else — notably test_floor_sweep_operations' 60 expensive tests —
            # keeps free load balancing; a blanket loadfile would serialize them.
            "--dist",
            "loadgroup",
            "-m",
            PYTEST_MARKERS,
        ]
    ),
    Gate(["python3", "scripts/test_vault/e2e_smoke.py"], docs=False),
    Gate(
        [
            "python3",
            "-m",
            "compileall",
            "-q",
            "src/memoria_vault",
            "scripts/checks",
            "scripts/test_vault",
            "scripts/verify",
        ],
        docs=False,
    ),
    Gate(
        [
            "bash",
            "-n",
            "scripts/install.sh",
            "scripts/test_vault/refresh-test-vault.sh",
            "scripts/test_vault/install-test-vault-local-llm.sh",
        ],
        docs=False,
    ),
    # 1689: the installed console script is the one surface no other gate
    # exercises through PATH — pytest resolves src/ via path config, so a
    # stale editable install (e.g. pointing at a deleted worktree) keeps
    # every gate green while `memoria` is dead for every CLI-consuming task.
    Gate(["memoria", "--version"], docs=False),
]
```

Then delete the `_DOCS_SKIP` tuple and its comment (`scripts/verify:128-129`):

```python
# Gates a docs-only diff cannot affect: they exercise code, not documentation.
_DOCS_SKIP = ("e2e_smoke.py", "-m compileall", "bash -n", "memoria --version", "wheel_gate.py")
```

and replace `_gates_for_run` (`scripts/verify:132-144`) with:

```python
def _gates_for_run(docs_only: bool) -> list[list[str]]:
    """The full roster, or its docs-relevant subset when docs_only is set."""
    if not docs_only:
        return [gate.cmd for gate in GATES]
    reduced: list[list[str]] = []
    for gate in GATES:
        if not gate.docs:
            continue
        # Exact-argument swap; only the pytest gate carries PYTEST_MARKERS, so
        # every other command passes through unchanged.
        reduced.append(["static" if arg == PYTEST_MARKERS else arg for arg in gate.cmd])
    return reduced
```

Nothing else in the file changes — `main()`'s `for command in _gates_for_run(DOCS_ONLY)` loop, `run()`, the lock, and the JSON/PowerShell steps are untouched.

- [ ] **Step 4: Run the mirror test to verify it passes**

Run: `env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_verify_script.py -q`
Expected: PASS (all tests, including `test_docs_only_scope_narrows_the_roster` — the behavioral proof the narrowed roster is unchanged — and the new default-scope test).

- [ ] **Step 5: Run the gate**

Run: `python scripts/verify`
Expected: `verify: OK` (ruff/ruff-format cover the extensionless `scripts/verify` via the directory-scoped hooks; compileall re-checks it).

- [ ] **Step 6: Commit**

```bash
git add scripts/verify tests/test_verify_script.py
git commit -m "verify: roster entries carry docs-only scope as data

_DOCS_SKIP selected gates by substring-matching fragments of the joined
command ('bash -n', 'wheel_gate.py'); a future gate whose argv happens to
contain a fragment would be silently dropped from docs-only runs. Each
Gate now declares docs=False explicitly, defaulting to running under docs
scope. _gates_for_run keeps its signature and output — the mirror test's
docs-narrowing assertions prove behavior is unchanged.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: gitleaks CI job installs only the pinned pre-commit

`.github/workflows/gitleaks.yml` installs all of `requirements-dev.txt` (pytest, pytest-cov, pytest-xdist, setuptools…) to run one pre-commit hook. Install just the `pre-commit` pin, read from `requirements-dev.txt` so there is still exactly one place to bump it. (Audit note, honest framing: the dev requirements are light — this buys seconds and pin hygiene, not minutes. The heavier alternative — dropping pre-commit for a pinned gitleaks binary or the official action — was rejected: it would split the version pin from the local hook's `.pre-commit-config.yaml` rev and change scan invocation semantics. The separate always-on `gitleaks` required check itself is deliberate and stays: it must survive edits to verify's roster.)

**Files:**
- Modify: `.github/workflows/gitleaks.yml:25-26`

**Interfaces:**
- Consumes: `pre-commit==4.6.1` pin line in `requirements-dev.txt` (matched by `^pre-commit==`; the neighboring `pre-commit-hooks==6.0.0` line does not match because `-hooks` follows before `==` — verified by the grep in Step 2).
- Produces: nothing later tasks rely on.

- [ ] **Step 1: Narrow the install line**

`.github/workflows/gitleaks.yml` lines 25–26 currently read:

```yaml
      - name: Install pre-commit
        run: python -m pip install --quiet -r requirements-dev.txt
```

Replace with:

```yaml
      - name: Install pre-commit
        run: python -m pip install --quiet "$(grep -E '^pre-commit==' requirements-dev.txt)"
```

Do not touch anything else in the file — the workflow `name:`, job id, and step order are matched by branch protection and the pre-commit cache key.

- [ ] **Step 2: Verify the grep resolves to exactly one requirement**

Run: `grep -E '^pre-commit==' requirements-dev.txt`
Expected output, exactly one line:

```
pre-commit==4.6.1
```

(`pre-commit-hooks==6.0.0` must NOT appear — the `==` anchor excludes it. If two lines ever match, the pip call gets one malformed argument and CI fails loudly, not silently.)

- [ ] **Step 3: Lint the workflow**

Run: `pre-commit run yamllint --hook-stage manual --all-files`
Expected: `yamllint.............Passed` (yamllint is the only local gate that parses workflow YAML — there is no actionlint — so also re-read the diff once: the real Actions-semantics check is the PR's own gitleaks run in Step 5).

- [ ] **Step 4: Run the gate and commit**

Run: `python scripts/verify`
Expected: `verify: OK`

```bash
git add .github/workflows/gitleaks.yml
git commit -m "ci: gitleaks job installs only the pinned pre-commit

The job installed all of requirements-dev.txt (pytest, coverage, xdist,
setuptools) to run one hook. Grep the pre-commit pin out of
requirements-dev.txt so the version is still bumped in exactly one place.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

- [ ] **Step 5: Open the PR and watch the edited workflow validate itself**

```bash
git push -u origin wip/verify-gate-consolidation
gh pr create --title "Verify-gate consolidation: one living roster, scope as data, slim gitleaks job" --body "$(cat <<'EOF'
Rethink-audit (2026-08-03) migrate steps 1-3.

- docs: tests/README.md + CONTRIBUTING.md pointed at the pre-alpha.21 roster
  (static/unit/contract, package/runtime "never in the gate") while
  scripts/verify runs everything except live and slow. Restatements deleted;
  prose now points at PYTEST_MARKERS.
- verify: GATES entries carry docs-only scope as a Gate.docs field; the
  _DOCS_SKIP substring tuple is gone. _gates_for_run signature and output
  unchanged (pinned by test_docs_only_scope_narrows_the_roster).
- ci: the gitleaks job installs only the pinned pre-commit instead of all of
  requirements-dev.txt; requirements-dev.txt stays the single pin source.

Out of scope, decided at audit time: directory-based test tiers (close call,
standalone PR if ever); scope detection, lock, and pytest invocation
(explicitly unchanged).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Then confirm on the PR that **both** required checks report: `verify` green, and `gitleaks` green *running the edited workflow* — that run is the only real validation of the Task 3 change (no local gate executes Actions semantics). If `gitleaks` never reports, the workflow edit broke check-name matching: stop and re-inspect `.github/workflows/gitleaks.yml` against the Step 1 diff before anything merges.

## Self-review record

- Spec coverage: audit migrate step 1 → Task 1 (grown to include CONTRIBUTING.md per evidence sweep); step 2 → Task 2; step 3 → Task 3 (shrunk to install-line narrowing per evidence — dev deps are light, binary swap rejected); steps 4–5 explicitly out of scope in the header.
- Behavior pins: Task 2's narrowed-roster equality is asserted by the existing `test_docs_only_scope_narrows_the_roster` (docs roster: lint + six check scripts + `-m static` pytest; e2e/compileall/`bash -n`/`memoria --version`/wheel gate dropped) — old `_DOCS_SKIP` set and new `docs=False` set are identical, checked entry-by-entry.
- Type consistency: `Gate.cmd`/`Gate.docs` names match across the verify rewrite, the three mirror-test joins, and the new default-scope test; `_gates_for_run` returns `list[list[str]]` in both branches.
