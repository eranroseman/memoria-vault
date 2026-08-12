# Lint Ownership Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make "every tracked authored file is claimed by a gate" a mechanism instead of a prose comment, then fix the five files that escape today.

**Architecture:** One new static test reads the existing tool configs (`.pre-commit-config.yaml` hook scopes, `scripts/verify`'s roster) and asserts two properties: every tracked file extension has a declared policy, and every file of a claimed type falls inside its owner's scope or appears in an `UNCLAIMED` map with a reason. The test restates nothing — it reads config and asserts a property, the same species as `tests/test_node_tooling.py` and `tests/test_cspell_scope.py`. Two gate entries that hardcode file lists are then deleted or de-hardcoded.

**Tech Stack:** Python 3.12, pytest, PyYAML, pre-commit, ruff, shellcheck, PSScriptAnalyzer.

## Global Constraints

- Correctness command is `python scripts/verify`. It is the one gate.
- Stage explicit paths in `git add`. Never `git add -A`, `--all`, `-u`, or `.` — a checked-in `PreToolUse` hook rejects those forms.
- New tests carry `pytestmark = pytest.mark.static` and import `ROOT` from `tests.paths`.
- Ruff owns layout at line length 100. Run `ruff format` before committing, or let the commit-stage hook do it.
- Trust order when layers disagree: schema → tests → code → docs.
- Do not reformat `design-history/` — it is a frozen record.
- Every task verifies current state with a command and its expected result **before** the step that changes anything.

---

### Task 1: The coverage test

**Files:**
- Create: `tests/test_lint_coverage.py`
- Read only: `.pre-commit-config.yaml`, `scripts/verify`

**Interfaces:**
- Consumes: `tests.paths.ROOT` (a `pathlib.Path` to the repo root, already used by every static test).
- Produces: `KNOWN_EXTENSIONS: dict[str, str]` and `UNCLAIMED: dict[str, str]` in `tests/test_lint_coverage.py`. Task 2 adds entries to `UNCLAIMED`; Task 4 changes what the ruff matcher accepts.

This task lands the test **red**, documenting the five escapes. Task 2 turns it green. That ordering is deliberate: a coverage test seeded to pass proves nothing about whether it can fail.

- [ ] **Step 1: Verify the current escapes exist**

Run:

```bash
git ls-files '*.py' | grep -vE '^(src/memoria_vault|scripts|tests)/'
git ls-files '*.sh' | grep -vE '^scripts/'
git ls-files 'src/memoria_vault/product/workspace_seed/.githooks/*'
```

Expected: first prints `.claude/hooks/block-git-add-all.py`; second prints nothing; third prints `src/memoria_vault/product/workspace_seed/.githooks/pre-commit`. The third is a bash script (`head -1` shows `#!/usr/bin/env bash`) that no shell gate claims, because shellcheck's hook is scoped `^scripts/`.

- [ ] **Step 2: Write the failing test**

Create `tests/test_lint_coverage.py`:

```python
"""Every tracked authored file is claimed by a gate, or declared unclaimed with a reason.

Scope has escaped four times on record and once more when this test was written:
`scripts/verify` was the one Python file exempt from both ruff hooks;
`scripts/dev/setup.sh` was covered by no gate at all; an alternation in the
shellcheck hook named `scripts/install/`, deleted in #1322, so it matched
nothing and stayed green; `.claude/hooks/block-git-add-all.py` sits outside
every scope; and the seeded `.githooks/pre-commit` is a bash script shipped to
every vault that shellcheck's `^scripts/` scope does not reach.

Each was fixed on its own and memorialised as a comment. None of those comments
can fail. This test computes the claimed set instead, in the spirit of
`test_policy_gate_completeness.py`: a boundary test must prove the boundary is
complete, not that one known case is handled.

It reads the tool configs rather than restating them. The per-type mapping below
does re-encode "what counts as Python", which the hook comments say was
abandoned for `files:` regexes — the difference is failure mode. A stale filter
fails silent (green hook, nothing linted); a stale test fails loud, naming the
file.
"""

from __future__ import annotations

import re
import subprocess

import pytest
import yaml

from tests.paths import ROOT

pytestmark = pytest.mark.static

PRECOMMIT = ROOT / ".pre-commit-config.yaml"

# Every extension tracked in this repo, mapped to the gate that claims it.
# A new extension fails `test_every_tracked_extension_has_a_policy` until it is
# added here, which is the point: a new language must be a decision, not a drift.
KNOWN_EXTENSIONS: dict[str, str] = {
    ".py": "ruff",
    ".sh": "shellcheck",
    ".ps1": "psscriptanalyzer",
    ".js": "oxlint",
    ".mjs": "oxlint",
    ".yaml": "yamllint",
    ".yml": "yamllint",
    ".json": "check_json",
    ".md": "cspell",
    # Claimed by no linter, on purpose. The reason is the value.
    ".toml": "unclaimed: 2 files; pyproject is parsed by every pip and build invocation",
    ".css": "unclaimed: 2 files, one a generated bundle; three CSS files is not a mechanism",
    ".scss": "unclaimed: 1 Jekyll theme override",
    ".base": "unclaimed: Obsidian Bases config, shipped as package data",
    ".sql": "unclaimed: runtime package data, exercised by the migration tests",
    ".bib": "unclaimed: generated bibliography artifact",
    ".txt": "unclaimed: word lists and vocabularies",
    ".cff": "unclaimed: citation metadata",
    ".ini": "unclaimed: .vale.ini, read by the vale hook itself",
    ".psd1": "unclaimed: PSScriptAnalyzer settings, read by the analyzer itself",
    ".ico": "unclaimed: binary",
    ".gitignore": "unclaimed: git metadata",
    ".gitattributes": "unclaimed: git metadata",
    # Basename contains a dot, so the extension derivation below sees the whole
    # tail as the extension. It belongs here rather than in EXTENSIONLESS.
    ".git-blame-ignore-revs": "unclaimed: git metadata",
    ".yamllint": "unclaimed: yamllint's own config, read by the hook",
}

# Files of a claimed type that no gate reaches, each with the reason it is exempt.
# An entry here is a decision on the record, not an oversight.
UNCLAIMED: dict[str, str] = {
    "src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/main.js": (
        "generated esbuild bundle; `npm run check --prefix packages/memoria-obsidian` "
        "compares it byte-for-byte against a fresh build, so formatting it fails that check"
    ),
}

# Tracked files with no extension at all, and what claims each.
EXTENSIONLESS: dict[str, str] = {
    "scripts/verify": "ruff",
    "src/memoria_vault/product/workspace_seed/.githooks/pre-commit": "shellcheck",
    "LICENSE": "unclaimed: license text",
}


def _tracked() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.splitlines()


def _hook(hook_id: str) -> dict:
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    hooks = [h for repo in config["repos"] for h in repo["hooks"] if h["id"] == hook_id]
    assert len(hooks) == 1, f"expected exactly one {hook_id} hook, got {len(hooks)}"
    return hooks[0]


def _claims(hook_id: str, path: str) -> bool:
    """True when the hook's own `files`/`exclude` scope reaches `path`."""
    hook = _hook(hook_id)
    if not re.search(hook["files"], path):
        return False
    exclude = hook.get("exclude")
    return not (exclude and re.search(exclude, path))


# Which hook id enforces each claimed extension. `.json` and `.ps1` are claimed
# by native gates in `scripts/verify`, not by a pre-commit hook, so they are
# handled separately below.
HOOK_FOR_OWNER = {
    "ruff": "ruff",
    "shellcheck": "shellcheck",
    "oxlint": "oxlint",
    "yamllint": "yamllint",
    "cspell": "cspell",
}


def test_every_tracked_extension_has_a_policy():
    """A new file type must be a decision. Add it to KNOWN_EXTENSIONS."""
    seen = {"." + name.rsplit(".", 1)[1] for name in _tracked() if "." in name.rsplit("/", 1)[-1]}
    undeclared = sorted(seen - set(KNOWN_EXTENSIONS))
    assert undeclared == [], (
        f"tracked extensions with no declared owner: {undeclared}. "
        "Add each to KNOWN_EXTENSIONS with an owner or an 'unclaimed: <reason>' string."
    )


def test_every_extensionless_tracked_file_has_a_policy():
    undeclared = sorted(
        name
        for name in _tracked()
        if "." not in name.rsplit("/", 1)[-1] and name not in EXTENSIONLESS
    )
    assert undeclared == [], (
        f"tracked files with no extension and no declared owner: {undeclared}. "
        "Add each to EXTENSIONLESS."
    )


@pytest.mark.parametrize("owner", sorted(HOOK_FOR_OWNER))
def test_claimed_files_fall_inside_their_owner_scope(owner: str):
    extensions = [ext for ext, who in KNOWN_EXTENSIONS.items() if who == owner]
    paths = [
        name
        for name in _tracked()
        if any(name.endswith(ext) for ext in extensions) and name not in UNCLAIMED
    ]
    paths += [name for name, who in EXTENSIONLESS.items() if who == owner]
    escaped = sorted(path for path in paths if not _claims(HOOK_FOR_OWNER[owner], path))
    assert escaped == [], (
        f"tracked files the {owner} hook's `files` scope does not reach: {escaped}. "
        "Either widen the hook scope in .pre-commit-config.yaml or add the file to "
        "UNCLAIMED with the reason it is exempt."
    )


def test_json_and_powershell_are_claimed_by_the_verify_roster():
    """These two types are gated by native steps in `scripts/verify`, not by a hook.

    `check_json()` parses every tracked `*.json`; the PowerShell step runs
    PSScriptAnalyzer. This asserts both still enumerate from `git ls-files`
    rather than a hardcoded path, so a new file of either type is covered the
    day it lands.
    """
    source = (ROOT / "scripts/verify").read_text(encoding="utf-8")
    assert '["git", "ls-files", "*.json"]' in source, (
        "check_json must enumerate tracked JSON from git, not a hardcoded list"
    )
    assert "ls-files" in source and "*.ps1" in source, (
        "the PowerShell step must enumerate tracked .ps1 from git, not a hardcoded path"
    )
```

- [ ] **Step 3: Run the test to verify it fails, and on the right things**

Run:

```bash
python3 -m pytest tests/test_lint_coverage.py -q
```

Expected: FAIL. Three specific failures:

1. `test_claimed_files_fall_inside_their_owner_scope[ruff]` — escaped: `['.claude/hooks/block-git-add-all.py']`
2. `test_claimed_files_fall_inside_their_owner_scope[shellcheck]` — escaped: `['src/memoria_vault/product/workspace_seed/.githooks/pre-commit']`
3. `test_json_and_powershell_are_claimed_by_the_verify_roster` — `*.ps1` not found in `scripts/verify` (it hardcodes `scripts/install.ps1`)

If a failure names a file not in that list, stop and add it to `KNOWN_EXTENSIONS` or `UNCLAIMED` with a reason before continuing — an unexpected escape is a finding, not noise.

- [ ] **Step 4: Commit the red test**

```bash
git add tests/test_lint_coverage.py
git commit -m "test: assert every tracked file is claimed by a lint gate

Lands red on the five files that escape today. Task 2 closes them."
```

---

### Task 2: Close the escaped scopes

**Files:**
- Modify: `.pre-commit-config.yaml` (ruff hook `files`, ruff-format hook `files`, shellcheck hook `files`)
- Modify: `scripts/verify` (the `PSSA_COMMAND` constant's literal path)

**Interfaces:**
- Consumes: `tests/test_lint_coverage.py` from Task 1.
- Produces: nothing new. This task only widens existing scopes.

- [ ] **Step 1: Verify the scopes as they stand**

Run:

```bash
grep -n 'files: \^' .pre-commit-config.yaml
```

Expected: `^(src/memoria_vault|scripts|tests)/` twice (ruff, ruff-format) and `^scripts/` once (shellcheck).

- [ ] **Step 2: Widen the two ruff hooks**

In `.pre-commit-config.yaml`, change **both** the `ruff` and `ruff-format` hooks:

```yaml
        files: ^(src/memoria_vault|scripts|tests|\.claude/hooks)/
```

Add to the comment block already above the `ruff` hook:

```yaml
      # `.claude/hooks/` holds the checked-in PreToolUse gate that enforces the
      # shared-index rule. Tracked, load-bearing, and outside every scope until
      # tests/test_lint_coverage.py computed the claimed set.
```

- [ ] **Step 3: Widen the shellcheck hook**

```yaml
        files: ^(scripts|src/memoria_vault/product/workspace_seed/\.githooks)/
```

Add to the comment already above that hook:

```yaml
      # The seeded `.githooks/pre-commit` is a bash script installed into every
      # user's vault. `^scripts/` never reached it.
```

- [ ] **Step 4: De-hardcode the PowerShell step**

In `scripts/verify`, replace the `PSSA_COMMAND` constant:

Also update the step's printed label in `check_powershell()`, which names the literal path:

```python
    print("== PSScriptAnalyzer (tracked *.ps1)")
```

```python
# Self-skips when the analyzer module is absent (exit 2), so a machine with pwsh
# but no PSScriptAnalyzer does not hard-fail the gate. Enumerates from git rather
# than naming a path: the shellcheck hook shipped an exact-path form that lint-ed
# one of four scripts, and a literal here is the same failure waiting for a
# second .ps1.
PSSA_COMMAND = (
    "if (-not (Get-Module -ListAvailable -Name PSScriptAnalyzer)) "
    "{ Write-Host 'PSScriptAnalyzer module not installed'; exit 2 }; "
    "$files = git ls-files '*.ps1'; "
    "if (-not $files) { exit 0 }; "
    "$r = Invoke-ScriptAnalyzer -Path $files -Severity Warning,Error "
    "-Settings ./scripts/PSScriptAnalyzerSettings.psd1; "
    "if ($r) { $r | Format-Table -AutoSize; exit 1 }"
)
```

- [ ] **Step 5: Run the coverage test to verify it passes**

Run:

```bash
python3 -m pytest tests/test_lint_coverage.py -q
```

Expected: PASS, all parametrisations.

- [ ] **Step 6: Run the newly-covered files through their gates**

Run:

```bash
pre-commit run ruff --hook-stage manual --all-files
pre-commit run ruff-format --hook-stage manual --all-files
pre-commit run shellcheck --hook-stage manual --all-files
```

Expected: each passes, or reports findings in the two newly-covered files. If ruff reports findings in `.claude/hooks/block-git-add-all.py`, fix them — they are real, the file has never been linted. If `ruff-format` rewrites either file, that rewrite is the deliverable; stage it.

- [ ] **Step 7: Verify the PowerShell step still runs**

Run:

```bash
python3 -c "
import runpy
ns = runpy.run_path('scripts/verify', run_name='_probe')
print(ns['check_powershell']())
"
```

Expected: prints `== PSScriptAnalyzer (tracked *.ps1)` then `0` — the analyzer ran clean, or skipped because `pwsh` or the module is absent. Any nonzero means the analyzer found something in `scripts/install.ps1` — fix it.

- [ ] **Step 8: Commit**

```bash
git add .pre-commit-config.yaml scripts/verify tests/test_lint_coverage.py .claude/hooks/block-git-add-all.py src/memoria_vault/product/workspace_seed/.githooks/pre-commit
git commit -m "fix: bring the five escaped files inside a lint scope

.claude/hooks and the seeded .githooks/pre-commit were tracked and gated by
nothing. PSScriptAnalyzer now enumerates .ps1 from git instead of naming one."
```

If Step 6 changed neither newly-covered file, drop those two paths from the `git add` line rather than staging unmodified files.

---

### Task 3: Delete the `bash -n` gate

**Files:**
- Modify: `scripts/verify` (remove the `Gate` entry whose `cmd` starts `bash -n`)
- Modify: `tests/test_verify_script.py` (remove the assertion pinning it)

**Interfaces:**
- Consumes: nothing.
- Produces: nothing. Pure deletion.

`bash -n` parse-checks 3 of the 5 tracked shell scripts. shellcheck, scoped `^scripts/` (and after Task 2, the seeded githook too), parse-fails on syntax errors across all of them. The gate guards nothing shellcheck does not already guard, and its hardcoded list is the same restatement failure this plan exists to remove.

- [ ] **Step 1: Verify shellcheck actually rejects a syntax error**

Run:

```bash
printf 'if true; then\n  echo hi\n' > scripts/_syntax_probe.sh
pre-commit run shellcheck --hook-stage manual --files scripts/_syntax_probe.sh
```

Expected: FAIL, with shellcheck reporting an unterminated `if` (`SC1046`/`SC1073` or similar). This is the evidence that deleting `bash -n` loses no coverage.

Then remove the probe:

```bash
rm scripts/_syntax_probe.sh
```

- [ ] **Step 2: Verify the mirror test currently pins the gate**

Run:

```bash
grep -n 'bash -n' tests/test_verify_script.py scripts/verify
```

Expected: one hit in `tests/test_verify_script.py` (`assert any(f.startswith("bash -n scripts/install.sh") for f in flat)`) and one in `scripts/verify` (the roster entry). Both must go, in the same commit — deleting only the roster entry ships a red gate.

- [ ] **Step 3: Delete the roster entry**

In `scripts/verify`, remove this whole `Gate(...)` block:

```python
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
```

- [ ] **Step 4: Delete the mirror assertion**

In `tests/test_verify_script.py`, remove:

```python
    assert any(f.startswith("bash -n scripts/install.sh") for f in flat)
```

- [ ] **Step 5: Run the mirror test**

Run:

```bash
python3 -m pytest tests/test_verify_script.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/verify tests/test_verify_script.py
git commit -m "refactor: drop the bash -n gate, subsumed by shellcheck

It parse-checked 3 of 5 tracked shell scripts from a hardcoded list.
shellcheck at ^scripts/ parse-fails on the same input across all of them."
```

---

### Task 4: Fix the drifted tool-config scopes

**Files:**
- Modify: `.oxfmtrc.json`
- Modify: `.oxlintrc.json`
- Modify: `cspell.json:23`
- Modify: `pyproject.toml` (the ruff `select` comment block)

**Interfaces:**
- Consumes: nothing.
- Produces: nothing.

Four config statements that are false today. Each is editor-facing or comment-facing only — the pre-commit hooks are unaffected — so none of these can fail the gate. That is exactly why they drifted.

- [ ] **Step 1: Verify each claim**

Run:

```bash
git ls-files '*.scss'
git ls-files scratchpad | head -1; echo "(scratchpad tracked files above, if any)"
ls node_modules 2>&1 | head -1
printf 'x = 1   \n' > tests/_ws_probe.py && ruff check --no-cache tests/_ws_probe.py; rm tests/_ws_probe.py
```

Expected, in order: `docs/_sass/custom/custom.scss` (so `.oxfmtrc.json`'s `**/*.css` deny does not cover it); nothing (so `cspell.json`'s `scratch/**` matches no tracked path, and the real directory is `scratchpad/`); `ls: cannot access 'node_modules'` (so both `$schema` paths are dangling); and `W291 Trailing whitespace` (so the pyproject comment claiming W291/293 are off is false — `select = ["W"]` enables them and `ignore` does not exclude them).

- [ ] **Step 2: Fix `.oxfmtrc.json`**

Repoint `$schema` at the only `node_modules` that exists, and add the missing extensions:

```json
{
  "$schema": "./packages/memoria-obsidian/node_modules/oxfmt/configuration_schema.json",
  "ignorePatterns": [
    "src/memoria_vault/product/workspace_seed/**",
    "packages/memoria-obsidian/styles.css",
    "test-vault/**",
    ".kilo/**",
    "**/*.md",
    "**/*.json",
    "**/*.jsonc",
    "**/*.json5",
    "**/*.yml",
    "**/*.yaml",
    "**/*.toml",
    "**/*.css",
    "**/*.scss",
    "**/*.less",
    "**/*.graphql",
    "**/*.mdx"
  ]
}
```

The pre-commit hook's `types_or` already keeps oxfmt off all of these. This list guards a bare `oxfmt .` run from an editor, the way `.yamllint`'s `ignore` guards a bare `yamllint .`.

- [ ] **Step 3: Fix `.oxlintrc.json`**

Repoint `$schema` the same way, and drop the two plugins for languages this repo does not contain — every tracked JS file is plain CommonJS `.js`/`.mjs`:

```json
{
  "$schema": "./packages/memoria-obsidian/node_modules/oxlint/configuration_schema.json",
  "plugins": ["eslint", "unicorn", "promise"],
  "rules": {
    "promise/catch-or-return": "error",
    "promise/always-return": "error"
  },
  "ignorePatterns": [
    "src/memoria_vault/product/workspace_seed/.obsidian/plugins/**",
    "test-vault/**",
    ".kilo/**"
  ]
}
```

- [ ] **Step 4: Fix the cspell ignore path**

In `cspell.json`, change `"scratch/**"` to `"scratchpad/**"`.

- [ ] **Step 5: Fix the false pyproject comment**

In `pyproject.toml`, in the `[tool.ruff.lint]` comment block, change:

```
# Deliberately OFF: E1/E2/E3, W291/293, E501, COM, ISC, Q -- the formatter owns
```

to:

```
# Deliberately OFF: E1/E2/E3, E501, COM, ISC, Q -- the formatter owns
```

W291/W293 are **on** (via `select = ["W"]`) and always have been. The formatter strips trailing whitespace before they can fire, which is why nobody noticed the comment was wrong.

- [ ] **Step 6: Verify the JSON still parses and oxlint still runs**

Run:

```bash
python3 -c "import json; [json.loads(open(f).read()) for f in ('.oxfmtrc.json', '.oxlintrc.json', 'cspell.json')]; print('json ok')"
pre-commit run oxlint --hook-stage manual --all-files
pre-commit run oxfmt --hook-stage manual --all-files
pre-commit run cspell --hook-stage manual --all-files
```

Expected: `json ok`, then three passing hooks. Dropping the `react` and `typescript` plugins must not change oxlint's verdict — if it does, a rule from one of them was firing and you need to know which before proceeding.

- [ ] **Step 7: Commit**

```bash
git add .oxfmtrc.json .oxlintrc.json cspell.json pyproject.toml
git commit -m "fix: correct four config statements that were false

Dangling $schema paths (no root node_modules), an oxfmt deny-list missing
.scss while docs/_sass/custom/custom.scss is tracked, a cspell ignore for
scratch/ against a directory named scratchpad/, and a ruff comment claiming
W291/293 are off when select=[\"W\"] enables them."
```

---

### Task 5: Full gate and documentation

**Files:**
- Modify: `AGENTS.md` (add the coverage test to "Where things live" — the engineering skills' configuration list)

**Interfaces:**
- Consumes: everything above.
- Produces: nothing.

- [ ] **Step 1: Run the full gate**

Run:

```bash
python scripts/verify
```

Expected: `verify: OK`. If the pytest step fails, read which test — a `static` failure is most likely `test_verify_script.py` (Task 3's mirror edit) or `test_lint_coverage.py` (a file added since Task 1).

- [ ] **Step 2: Record where the invariant now lives**

In `AGENTS.md`, under "Where things live", append to the bullet listing what the engineering skills read:

```markdown
- Which gate claims which file is computed, not asserted in prose:
  `tests/test_lint_coverage.py` fails when a tracked file falls outside every
  tool scope without an `UNCLAIMED` entry giving the reason. Adding a language
  or a top-level directory means adding a line there.
```

- [ ] **Step 3: Verify the docs gates accept the edit**

Run:

```bash
pre-commit run cspell --hook-stage manual --files AGENTS.md
pre-commit run markdownlint-structural --hook-stage manual --files AGENTS.md
```

Expected: both pass. `markdownlint-structural` is scoped to `^docs/.*\.md$` and will report "no files to check" for `AGENTS.md` — that is a pass, not a skip to worry about.

- [ ] **Step 4: Commit**

```bash
git add AGENTS.md
git commit -m "docs: record that lint ownership is computed by a test"
```

---

### Task 6: Match the editor to the corrected scopes

**Files:**
- Modify: `.vscode/settings.json`
- Modify: `.vscode/extensions.json`

**Interfaces:**
- Consumes: the corrected `.oxfmtrc.json` and `.oxlintrc.json` from Task 4.
- Produces: nothing.

Task 4's deny-list guards a bare `oxfmt .`, but VS Code is the likelier way a stray formatter reaches a file no gate formats. Today `.vscode/settings.json` sets `editor.formatOnSave` for `[javascript]` and `[python]` and explicitly disables it for `[markdown]` and `[plaintext]` — JSON, YAML, TOML, and CSS are unstated, so whichever extension claims them formats on save with settings no gate agrees with. That is invariant I1 (editor output equals gate output) failing by omission.

- [ ] **Step 1: Verify what the editor formats today**

Run:

```bash
python3 -c "
import json, re
raw = open('.vscode/settings.json').read()
raw = re.sub(r'^\s*//.*$', '', raw, flags=re.M)
s = json.loads(raw)
print('language blocks:', sorted(k for k in s if k.startswith('[')))
print('global formatOnSave:', s.get('editor.formatOnSave', '<unset>'))
"
```

Expected: `language blocks: ['[javascript]', '[markdown]', '[plaintext]', '[python]']` and `global formatOnSave: <unset>`. So JSON, YAML, TOML, and CSS inherit whatever the user's global setting is — parity with the gate is left to chance.

- [ ] **Step 2: State the unstated languages**

In `.vscode/settings.json`, add these blocks next to the existing `[markdown]` and `[plaintext]` ones:

```json
  "[json]": {
    "editor.formatOnSave": false
  },
  "[jsonc]": {
    "editor.formatOnSave": false
  },
  "[yaml]": {
    "editor.formatOnSave": false
  },
  "[toml]": {
    "editor.formatOnSave": false
  },
  "[scss]": {
    "editor.formatOnSave": false
  },
  "[css]": {
    "editor.formatOnSave": false
  },
  "[shellscript]": {
    "editor.formatOnSave": false
  },
```

Every one of these types is claimed by no formatter in the gate — JSON gets a syntax check only, YAML gets yamllint (which never rewrites), TOML and CSS and SCSS are declared unclaimed in Task 1's `KNOWN_EXTENSIONS`, and shell gets shellcheck (also never rewrites). An editor that rewrites them produces diffs no gate asked for and no gate can verify.

- [ ] **Step 3: Make the yamllint editor integration read the repo config**

The `fnando.linter` extension is already enabled for yamllint in `.vscode/settings.json`, but it invokes yamllint without pointing at `.yamllint`, so the editor lints with yamllint's *default* rules while the gate uses `extends: relaxed` with `line-length` and `colons` disabled. That is a live skew: the editor flags long lines and column-aligned values the gate accepts. Replace the existing `linter.linters` block:

```json
  "linter.linters": {
    "yamllint": {
      "enabled": true,
      "args": ["-c", "${workspaceFolder}/.yamllint"]
    }
  },
```

Confirm the key name before committing: `fnando.linter` spells per-linter arguments as `args` in current releases, but check the extension's contributed settings in VS Code (Extensions → Linter → Settings, or the extension README) and use whatever it actually reads. A silently-ignored key leaves the skew in place while looking fixed — the exact failure mode this task exists to close.

- [ ] **Step 4: Drop the actionlint recommendation**

`rhysd.actionlint` is in `.vscode/extensions.json`, but actionlint runs in no gate — workflows get yamllint only, which checks indentation and duplicate keys, not workflow schema. Recommending an editor-only linter means contributors see findings CI will never enforce, which is the mirror image of the skew this task closes.

Remove this line from `.vscode/extensions.json`:

```json
    "rhysd.actionlint",
```

If you would rather keep actionlint, that is a defensible call — but then it belongs in the gate, which is its own change and not part of this plan. File an issue rather than leaving the recommendation dangling.

- [ ] **Step 5: Verify both files still parse and the pins still hold**

Run:

```bash
python3 -m pytest tests/test_node_tooling.py -q
python3 -c "
import json, re
for f in ('.vscode/settings.json', '.vscode/extensions.json'):
    raw = re.sub(r'^\s*//.*$', '', open(f).read(), flags=re.M)
    json.loads(raw)
print('vscode config ok')
"
```

Expected: pytest PASS and `vscode config ok`. `test_node_tooling.py` asserts `oxc.oxc-vscode` is still in `extensions.json` — removing the wrong line breaks it, which is the guard working.

- [ ] **Step 6: Commit**

```bash
git add .vscode/settings.json .vscode/extensions.json
git commit -m "fix: state editor formatting for the languages no gate formats

JSON, YAML, TOML, CSS, SCSS, and shell inherited an unstated formatOnSave, so
an editor could rewrite files the gate never formats. Also points the yamllint
integration at .yamllint, which the gate uses and the editor was ignoring, and
drops the actionlint recommendation for a linter that runs in no gate."
```

---

## Self-Review

**Spec coverage.** Every structural item from the audit's `migrate:` section maps to a task: coverage test (1), escaped scopes (2), `bash -n` deletion including the mirror test (3), PSScriptAnalyzer path (2, Step 4), `.scss` and `scratch/` drift (4). The `$schema` paths, the `react` plugin, and the W291 comment were review findings rather than audit findings; they are cheap and adjacent, so they ride in Task 4.

**Placeholder scan.** No TBDs. Every code step carries the literal content. Every verification step names a command and its expected output.

**Type consistency.** `KNOWN_EXTENSIONS`, `UNCLAIMED`, `EXTENSIONLESS`, and `HOOK_FOR_OWNER` are defined once in Task 1 and referenced by those exact names in Tasks 2 and 5. `_claims(hook_id, path)` and `_hook(hook_id)` keep their signatures throughout.

**One known risk.** Task 1 Step 3 expects exactly three failures. If the tree has changed since this plan was written, a fourth escape will surface. That is the test working, not the plan breaking — add the file to `UNCLAIMED` with a reason, or widen the scope that should have claimed it.
