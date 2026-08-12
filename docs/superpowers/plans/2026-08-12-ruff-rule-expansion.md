# Ruff Rule Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the ruff rule families that catch real defects this repo can produce, and record why the large families were rejected so the measurement never has to be repeated.

**Architecture:** Two tiers. Five families return **zero findings on the current tree**, so enabling them is free and forward-guarding — admitted on the same test `pyproject.toml` already uses to justify `N` ("enabled while already clean"). Five more rules find 34 sites total and get fixed in the same task that enables them. Everything else is rejected in a comment with its measured finding count.

**Tech Stack:** ruff 0.16.2 (pinned in both `requirements-dev.txt` and `.pre-commit-config.yaml`, held equal by `tests/test_node_tooling.py`), pytest, pre-commit.

## Global Constraints

- Correctness command is `python scripts/verify`. It is the one gate.
- Stage explicit paths in `git add`. Never `git add -A`, `--all`, `-u`, or `.`.
- Ruff owns layout at line length 100. Do not hand-format.
- Do not change the ruff **version** in this plan. Two pins exist and a test holds them equal; a bump is Dependabot's job and a separate PR.
- The `select` list in `pyproject.toml` is an annotated artifact. Every family added carries a comment naming the failure it prevents; every family rejected carries its measured count.
- Every task verifies current state with a command and its expected result before changing anything.

---

### Task 1: Admit the five zero-finding families

**Files:**
- Modify: `pyproject.toml` (`[tool.ruff.lint]` `select`)

**Interfaces:**
- Consumes: nothing.
- Produces: an extended `select` list. Task 2 appends to the same list.

- [ ] **Step 1: Verify each family is at zero**

Run:

```bash
for sel in T10 PLE PGH TID EXE; do
  echo -n "$sel: "
  ruff check --no-cache --select "$sel" src/memoria_vault scripts tests 2>/dev/null | tail -1
done
```

Expected: `All checks passed!` five times. If any family reports findings, the tree has moved since this plan was written — fix the findings first, in their own commit, then continue. Enabling a family with outstanding findings turns the gate red for everyone.

Note the path list above omits `.claude/hooks/`. If the lint-ownership plan has landed, that directory is inside the ruff hook's scope, and `EXE` checks the shebang-versus-executable-bit pairing — `.claude/hooks/block-git-add-all.py` carries `#!/usr/bin/env python3`, so `EXE001` fires if the file is not executable. Step 3 runs the hook rather than a path list and will surface it; fix it with `chmod +x` rather than by dropping `EXE`.

- [ ] **Step 2: Extend `select`**

In `pyproject.toml`, replace the `select` list with:

```toml
select = [
  "F", "E4", "E7", "E9", "W", "B", "I", "UP", "C4", "PIE", "RUF",
  "A", "PT", "DTZ", "FLY", "BLE", "S", "RET", "N",
  # Zero findings on this tree when admitted (2026-08), the same test that
  # earned N its place. Each guards a failure this repo can produce:
  "T10",   # flake8-debugger -- a stray breakpoint()/pdb.set_trace() from an agent session
  "PLE",   # pylint's error tier -- bad str.strip args, misplaced bare raise, invalid % format
  "PGH",   # blanket `# noqa` / `# type: ignore` (RUF100 catches only the *unused* form)
  "TID",   # relative imports creeping into a flat package
  "EXE",   # shebang/executable-bit drift on the scripts the gate invokes by path
]
```

- [ ] **Step 3: Verify the gate is still green**

Run:

```bash
pre-commit run ruff --hook-stage manual --all-files
```

Expected: PASS. No file changes — these families find nothing today.

- [ ] **Step 4: Prove `T10` can actually fail**

A rule admitted at zero is worth nothing if it cannot fire. Run:

```bash
printf 'breakpoint()\n' > tests/_debugger_probe.py
ruff check --no-cache tests/_debugger_probe.py
rm tests/_debugger_probe.py
```

Expected: `T100 Trace found: breakpoint used`. If it passes clean, `T10` is not actually selected — re-read Step 2.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml
git commit -m "feat: admit five ruff families that are already clean

T10, PLE, PGH, TID, EXE all return zero findings on this tree, so they cost
nothing today and guard forward. PGH becomes load-bearing once a type checker
lands."
```

---

### Task 2: Add the five small rules and fix what they find

**Files:**
- Modify: `pyproject.toml` (`select`, `per-file-ignores`)
- Modify: whichever source files the rules report — measured at 19 (`SLF001` in src/scripts), 5 (`PLW2901`), 2 (`PLW1510` in src), 2 (`PLW1508`), 6 (`ERA001`, all in tests)

**Interfaces:**
- Consumes: the `select` list from Task 1.
- Produces: final `select` and `per-file-ignores` blocks.

- [ ] **Step 1: Measure what each rule finds, right now**

Run:

```bash
for sel in SLF001 PLW2901 PLW1510 PLW1508 ERA001; do
  s=$(ruff check --no-cache --select "$sel" --statistics src/memoria_vault scripts 2>/dev/null | head -1 | awk '{print $1}')
  t=$(ruff check --no-cache --select "$sel" --statistics tests 2>/dev/null | head -1 | awk '{print $1}')
  echo "$sel  src+scripts=${s:-0}  tests=${t:-0}"
done
```

Expected, as measured 2026-08:

```
SLF001  src+scripts=19  tests=286
PLW2901 src+scripts=5   tests=0
PLW1510 src+scripts=2   tests=2
PLW1508 src+scripts=2   tests=0
ERA001  src+scripts=0   tests=6
```

Counts will drift as the tree moves. Treat these as the shape, not a contract — what matters is that `SLF001` is small in src and large in tests (which is why tests get an ignore) and that the other four are single-digit.

- [ ] **Step 2: Read every finding before changing a line**

Run:

```bash
ruff check --no-cache --select SLF001,PLW2901,PLW1510,PLW1508 src/memoria_vault scripts
ruff check --no-cache --select ERA001 tests
```

Read each. Three of these are genuine defect classes and one is a judgement call:

- `PLW1510` — `subprocess.run` without `check=`. The failure is a subprocess that fails and is silently treated as success. Fix by adding `check=True` where the call must succeed, or an explicit `check=False` where the return code is inspected. `scripts/verify` already writes `check=False` deliberately; that form satisfies the rule.
- `PLW1508` — a non-string default to `os.environ.get`. Fix the default to a string.
- `PLW2901` — a loop variable overwritten inside its own body. Fix by binding a new name.
- `SLF001` — production code reaching into another module's privates. Fix by promoting the member or routing through a public seam. If a site is genuinely correct, add a targeted `# noqa: SLF001` with a reason — `PGH` from Task 1 rejects a blanket `# noqa`, so the code must be spelled out.
- `ERA001` — commented-out code. Delete it. Src is already clean; the six are in tests.

- [ ] **Step 3: Fix the findings**

Apply the fixes from Step 2. Do not use `--fix` for these — none of the five have safe autofixes, and `SLF001` in particular needs a design decision per site.

- [ ] **Step 4: Verify the tree is clean under the new rules**

Run:

```bash
ruff check --no-cache --select SLF001,PLW2901,PLW1510,PLW1508 src/memoria_vault scripts
ruff check --no-cache --select ERA001 tests
```

Expected: `All checks passed!` twice.

- [ ] **Step 5: Extend `select` and `per-file-ignores`**

In `pyproject.toml`, append to `select`:

```toml
  # Small and real -- 34 sites at admission (2026-08), each a defect class rather
  # than a style position:
  "SLF",       # private-member access -- 19 in src/scripts; tests exempted below
  "ERA",       # commented-out code -- src was already clean
  "PLW1508",   # os.environ.get with a non-string default
  "PLW1510",   # subprocess.run without check= -- a silently ignored failure
  "PLW2901",   # loop variable overwritten inside its own body
```

And extend the tests entry in `per-file-ignores`:

```toml
# Tests legitimately use assert and run trusted subprocesses; bandit there is noise.
# E402: test helpers do sys.path manipulation before imports.
# SLF001: reaching into internals is what a white-box test does -- 286 sites, all intended.
"tests/**" = ["S", "E402", "SLF001"]
```

- [ ] **Step 6: Run the lint gate**

Run:

```bash
pre-commit run ruff --hook-stage manual --all-files
pre-commit run ruff-format --hook-stage manual --all-files
```

Expected: both PASS.

- [ ] **Step 7: Run the test suite**

Run:

```bash
python3 -m pytest tests/ -q -m "unit or contract"
```

Expected: PASS. `SLF001` and `PLW1510` fixes change real behaviour — a promoted seam or an added `check=True` can surface a failure that was previously swallowed. That is the rule doing its job; fix the underlying problem rather than reverting.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml src/memoria_vault scripts tests
git commit -m "feat: enable five ruff rules for real defect classes

SLF, ERA, PLW1508, PLW1510, PLW2901 -- 34 sites, fixed. PLW1510 in particular
caught subprocess calls whose failures were silently treated as success."
```

Stage only the paths you actually changed; if no file under `scripts/` was touched, drop it from the `git add` line.

---

### Task 3: Record the rejections

**Files:**
- Modify: `pyproject.toml` (the comment block above `select`)

**Interfaces:**
- Consumes: nothing.
- Produces: nothing.

The existing "Deliberately OFF" comment reads as an exhaustive account of what was weighed, but `PL`, `TRY`, `EM`, `ARG`, `SLF`, `ERA`, `T10`, `PGH`, `TID`, and `EXE` appear nowhere in it — they were never considered, not rejected. Without the counts written down, the next reader re-runs a `--select ALL` sweep to learn what this one already learned.

- [ ] **Step 1: Reproduce the measurement**

Run:

```bash
ruff check --no-cache --select ALL --statistics src/memoria_vault scripts tests 2>/dev/null | head -25
```

Expected, top entries: `D103` 2567, `COM812` 2252, `TRY003` 878, `ANN001` 792, `PLR2004` 499, `ANN201` 467, `EM101` 446, `EM102` 437, `PLC0415` 417, `SLF001` 305 (0 after Task 2), `CPY001` 285.

Note: `--select ALL` on the command line overrides the config's `ignore`, so already-ignored rules (`S603`, `S607`, `S310`, `DTZ011`, `PT011`, `PT018`, `E731`) appear in these totals. They are not candidates.

- [ ] **Step 2: Extend the rejection comment**

In `pyproject.toml`, replace the paragraph beginning `# Deliberately OFF:` with:

```toml
# Deliberately OFF: E1/E2/E3, E501, COM, ISC, Q -- the formatter owns
# layout (COM/ISC actively conflict with it). T20 (print is intentional in CLI),
# LOG/G (no logging), PTH (pathlib everywhere except the atomic-replace and chmod
# paths in backup/rendezvous/secrets/vaultio, where the os call is the clearer
# primitive), ANN/D (docstring presence is a judgement call, not a lint gate -- see AGENTS.md §Python style),
# SIM/PERF/FURB (opinionated terseness-over-clarity refactors).
#
# Measured and rejected 2026-08, with the finding count that decided it. These
# are the families a `--select ALL` sweep surfaces; the counts are here so the
# next reader does not have to re-run it:
#   TRY003 878 + EM101/EM102 883 -- 1,761 findings, zero bugs. Exception-message style.
#   PLC0415 417 -- import-outside-top-level. The lazy imports are deliberate
#                  (e.g. `import fcntl` inside scripts/verify's lock helper).
#   PLR2004 499 -- magic-value comparison; noise in a test suite this size.
#   CPY001 285 -- copyright headers. No.
#   INP001 175 -- implicit namespace package. The `namespaces = false` guard in
#                 [tool.setuptools.packages.find] covers the real risk.
#   TC003 144 -- typing-only imports; a micro-optimisation under
#                `from __future__ import annotations`.
#   ARG001 108 (src) -- unused arguments, mostly callback/interface conformance.
#                Needs a read per site, not a blanket enable.
#   TRY004 59 (src) -- raising ValueError where TypeError belongs. A real defect
#                class at real volume; worth its own pass, not a drive-by enable.
#   Complexity thresholds -- PLR0913 116, C901 60, PLR0912/PLR0915 31/31,
#                PLR0911 27, PLR0917 18. Threshold opinions, not defects.
#   FBT 60 across three rules -- boolean-trap is a real design smell, but that
#                volume for a style position buys a bikeshed.
```

- [ ] **Step 3: Verify the file still parses and the gate is green**

Run:

```bash
python3 -c "import tomllib; tomllib.load(open('pyproject.toml','rb')); print('pyproject ok')"
python scripts/verify
```

Expected: `pyproject ok`, then `verify: OK`.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "docs: record the ruff families measured and rejected

The OFF list read as exhaustive but never mentioned PL, TRY, EM, ARG, or the
complexity family. Counts included so the sweep is not re-run."
```

---

### Task 4: Match the editor to the gate

**Files:**
- Modify: `.vscode/settings.json`

**Interfaces:**
- Consumes: nothing.
- Produces: nothing.

`.vscode/settings.json` sets `[python]` to format on save with `charliermarsh.ruff`, and `ruff.importStrategy` is `fromEnvironment` so the editor uses the pinned ruff from `requirements-dev.txt`. But **format ≠ lint-fix**: `ruff format` does not sort imports. `I` (isort) is in `select`, so the gate demands sorted imports the editor never applies. Every contributor and agent session hits that as a gate failure on a file that looked clean on save.

- [ ] **Step 1: Verify the skew**

Run:

```bash
printf 'import sys\nimport os\n\nprint(os, sys)\n' > tests/_import_probe.py
ruff format tests/_import_probe.py && cat tests/_import_probe.py
ruff check --no-cache --select I tests/_import_probe.py
rm tests/_import_probe.py
```

Expected: `ruff format` leaves the import order untouched (`sys` then `os`), and `ruff check --select I` then reports `I001 Import block is un-sorted or un-formatted`. That is exactly what save-then-commit produces today.

- [ ] **Step 2: Apply ruff's fixes on save**

In `.vscode/settings.json`, replace the `[python]` block:

```json
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports.ruff": "explicit",
      "source.fixAll.ruff": "explicit"
    }
  },
```

`source.organizeImports.ruff` applies `I`; `source.fixAll.ruff` applies the safe autofixes for the rest of `select`, which is what the gate checks. `"explicit"` means it runs on save (matching the `[markdown]` block's existing `source.fixAll.markdownlint` setting) rather than on every keystroke.

- [ ] **Step 3: Verify the setting file still parses**

Run:

```bash
python3 -c "
import json, re
raw = re.sub(r'^\s*//.*$', '', open('.vscode/settings.json').read(), flags=re.M)
s = json.loads(raw)
assert s['[python]']['editor.codeActionsOnSave']['source.organizeImports.ruff'] == 'explicit'
print('vscode python block ok')
"
```

Expected: `vscode python block ok`.

- [ ] **Step 4: Confirm the pin that makes this work still holds**

Run:

```bash
python3 -m pytest tests/test_node_tooling.py::test_precommit_hooks_use_pinned_tool_environments -q
```

Expected: PASS. This is the assertion that keeps `requirements-dev.txt`'s ruff equal to the hook's rev — without it, the editor would apply a different ruff's fixes than the gate checks, which is the failure this task exists to prevent.

- [ ] **Step 5: Commit**

```bash
git add .vscode/settings.json
git commit -m "fix: apply ruff's import sort and autofixes on save

`ruff format` does not sort imports, but I is in select, so the gate demanded
sorted imports the editor never applied."
```

---

## Self-Review

**Spec coverage.** Zero-cost families (Task 1), small real rules with their fixes (Task 2), rejection record with measured counts (Task 3), editor parity (Task 4). The middle tier from the session — `TRY004` at 59 and `ARG001` at 108 — is deliberately *not* a task; both are recorded in Task 3's comment as needing their own pass. Turning either into a drive-by enable would bundle a 60-to-100-site refactor into a config change.

**Placeholder scan.** No TBDs. Every rule name, count, and comment body is literal. Step 2 of Task 2 is the one step that cannot show final code, because the fixes depend on what the sites look like — it compensates by naming the correct fix shape per rule.

**Type consistency.** Rule codes are spelled identically throughout: `T10`, `PLE`, `PGH`, `TID`, `EXE`, `SLF`/`SLF001`, `ERA`/`ERA001`, `PLW1508`, `PLW1510`, `PLW2901`. Where a family is selected (`SLF`, `ERA`) the per-file-ignore uses the specific code (`SLF001`), which is how ruff resolves them.

**Ordering note.** Task 1 must land before Task 2 because Task 2 appends to the `select` list Task 1 rewrites. Tasks 3 and 4 are independent of both and of each other.
