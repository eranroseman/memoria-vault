# Vale Curated Rules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the already-installed Vale gate earn its place by enabling eleven curated rules from three upstream packages, instead of enforcing casing on five proper nouns.

**Architecture:** Vendor three Vale packages (Microsoft, alex, write-good) into `.vale/styles/` so the gate stays offline and pinned, then enable individual rules by name rather than turning on a package wholesale. Nine rules are clean and their 35 findings get fixed. Two rules are suspected of false positives and get a verify-then-decide task of their own, so the gate stays green either way.

**Tech Stack:** Vale 3.17.1 (pinned as a pre-commit hook rev), pytest, pre-commit.

## Global Constraints

- Correctness command is `python scripts/verify`. It is the one gate.
- Stage explicit paths in `git add`. Never `git add -A`, `--all`, `-u`, or `.`.
- The Vale gate is offline. `vale sync` is a **manual refresh**, never a gate step — no network inside `scripts/verify`.
- Vale's scope is `^docs/.*\.md$` minus `^docs/superpowers/`, owned by `.pre-commit-config.yaml`. This plan does not change scope.
- `MinAlertLevel = error` stays. Every rule enabled here is assigned `error` explicitly.
- Spelling belongs to cspell. Vale owns terminology and usage. `Vale.Spelling = NO` stays.
- Do not edit `design-history/` — frozen, and outside Vale's scope anyway.
- Every task verifies current state with a command and its expected result before changing anything.

---

### Task 1: Vendor the three packages

**Files:**
- Create: `.vale/styles/Microsoft/` (48 files, ~196K)
- Create: `.vale/styles/alex/` (13 files, ~84K)
- Create: `.vale/styles/write-good/` (10 files, ~56K)
- Modify: `.vale.ini`
- Modify: `.gitignore` (only if it currently excludes anything under `.vale/`)

**Interfaces:**
- Consumes: nothing.
- Produces: the three vendored style directories. Task 2 enables rules from them by the names `Microsoft.<Rule>`, `alex.<Rule>`, `write-good.<Rule>`.

The pre-commit Vale hook runs `vale` against the committed `StylesPath`. It does not run `vale sync`. Vendoring is therefore not a convenience — it is what keeps the gate offline and reproducible.

- [ ] **Step 1: Verify the current Vale surface**

Run:

```bash
find .vale -type f
grep -c . .vale/styles/config/vocabularies/Memoria/reject.txt
```

Expected: exactly two files (`accept.txt`, `reject.txt`) under `.vale/styles/config/vocabularies/Memoria/`, and `reject.txt` at 4 lines — all comments, no entries. That is the whole of what Vale enforces today beyond `Vale.Repetition`: casing on five proper nouns.

- [ ] **Step 2: Locate the pinned Vale binary**

Run:

```bash
find ~/.cache/pre-commit -maxdepth 4 -name vale -type f | head -1
```

Expected: a path like `~/.cache/pre-commit/repo<hash>/golangenv-default/bin/vale`. If nothing is found, install the hook environments first with `pre-commit install-hooks`, then re-run.

Export it for the rest of this task:

```bash
export VALE=$(find ~/.cache/pre-commit -maxdepth 4 -name vale -type f | head -1)
"$VALE" --version
```

Expected: `vale version 3.17.1`, matching the rev in `.pre-commit-config.yaml`. A different version means the hook env is stale — run `pre-commit install-hooks` and re-check.

- [ ] **Step 3: Declare the packages**

In `.vale.ini`, add a `Packages` line directly below `StylesPath`, with the comment explaining why the styles are committed:

```ini
StylesPath = .vale/styles

; Vendored, not synced. The pre-commit hook runs `vale` and never `vale sync`,
; so the gate must never need the network. `.vale/styles/{Microsoft,alex,
; write-good}/` are committed; each carries a meta.json recording its version.
; To refresh: `vale sync`, review the diff, commit. Only the rules named in the
; [*.md] block below are enabled — a package is a source of rules here, not a
; style guide this project adopts.
Packages = Microsoft, alex, write-good
```

- [ ] **Step 4: Sync the packages into the tree**

Run:

```bash
"$VALE" sync
ls .vale/styles
```

Expected: `SUCCESS Synced 3 package(s)` and `ls` showing `Microsoft  alex  config  write-good`.

- [ ] **Step 5: Verify nothing gitignores the vendored styles**

Run:

```bash
git check-ignore -v .vale/styles/Microsoft/Avoid.yml || echo "not ignored - good"
git status --short .vale/styles | head -5
```

Expected: `not ignored - good`, and `git status` showing the new directories as untracked. If `git check-ignore` reports a matching rule, remove or narrow that rule in `.gitignore` — the vendored styles must be committed or the gate cannot run offline.

- [ ] **Step 6: Confirm the gate still passes with packages present but no rules enabled**

Run:

```bash
pre-commit run vale --hook-stage manual --all-files
```

Expected: PASS. Declaring `Packages` and syntax-checking the styles changes nothing until rules are named in the `[*.md]` block — that happens in Task 2. If this fails, the failure is in the existing `Vale`/vocabulary config, not the new packages; fix it before continuing.

- [ ] **Step 7: Run the full gate — vendoring adds 71 files to other tools' scopes**

Run:

```bash
python scripts/verify
```

Expected: `verify: OK`.

This step matters more than it looks. The vendored packages are Vale rule files written in YAML, and yamllint's hook is scoped `\.(yaml|yml)$` across the whole tree — so 71 third-party files just entered its scope. `test_lint_coverage.py` (if the lint-ownership plan has landed) will also now see them.

If yamllint fails on the vendored styles, the fix is to exempt them rather than to reformat third-party content. In `.yamllint`, add to the `ignore` block:

```yaml
  .vale/styles/Microsoft/
  .vale/styles/alex/
  .vale/styles/write-good/
```

with a comment noting these are vendored upstream rule files, refreshed by `vale sync` and never hand-edited — the same reasoning that already exempts `**/.obsidian/`.

- [ ] **Step 8: Commit**

```bash
git add .vale.ini .vale/styles/Microsoft .vale/styles/alex .vale/styles/write-good
git commit -m "chore: vendor the Microsoft, alex, and write-good Vale styles

Committed rather than synced: the pre-commit hook never runs vale sync, so the
gate must not need the network. No rules enabled yet."
```

If Step 7 required a `.yamllint` change, stage that file too.

---

### Task 2: Enable the nine clean rules and fix their findings

**Files:**
- Modify: `.vale.ini`
- Modify: whichever files under `docs/` the rules report — measured at 35 findings across roughly 30 files

**Interfaces:**
- Consumes: the vendored styles from Task 1.
- Produces: the `[*.md]` rule block in `.vale.ini`. Task 3 appends two more rules to it, or does not.

- [ ] **Step 1: Measure the nine rules before enabling them**

Run:

```bash
export VALE=$(find ~/.cache/pre-commit -maxdepth 4 -name vale -type f | head -1)
git ls-files 'docs/*.md' 'docs/**/*.md' | grep -v '^docs/superpowers/' > /tmp/vale_scope.txt
wc -l < /tmp/vale_scope.txt
```

Expected: `181` files in scope (the count will drift; what matters is that `docs/superpowers/` is excluded, matching the hook).

- [ ] **Step 2: Enable the nine rules**

In `.vale.ini`, replace the `[*.md]` section:

```ini
[*.md]
BasedOnStyles = Vale
Vale.Spelling = NO

; Individual rules, not packages. Measured against this tree 2026-08: running
; Microsoft and Google together triple-counts the same sentence (Passive fires
; from three styles at once), and 93% of the combined error tier was three
; house-style rules — Contractions, Dashes, EmDash — two of which contradict the
; spaced em dash used throughout this repo. What survives is the set below.
;
; Each rule is assigned `error` explicitly so MinAlertLevel stays at error and
; a rule's upstream severity cannot silently change what this gate enforces.
Microsoft.Avoid = error             ; banned terms — the mechanism reject.txt was created for
Microsoft.Quotes = error            ; punctuation inside quotes; CONTRIBUTING mandates American English
Microsoft.Jargon = error            ; 'leverage' and friends
Microsoft.HeadingPunctuation = error
Microsoft.UIVerbs = error           ; 'click' — the vault has no click target
alex.Condescending = error          ; 'simply', 'simple', 'easy', 'obviously'
alex.Race = error                   ; 'master' → primary / hub / reference
write-good.ThereIs = error          ; sentences opening "There is"
write-good.So = error               ; sentences opening "So "
```

- [ ] **Step 3: Run Vale and read every finding**

Run:

```bash
pre-commit run vale --hook-stage manual --all-files
```

Expected: FAIL, roughly 35 findings. As measured 2026-08:

```
11  alex.Condescending          'simply' / 'simple' / 'easy'
10  write-good.ThereIs          sentence opens with "There is"
 3  alex.Race                   'master' in why-write-half-is-bounded.md, design-principles.md
 3  Microsoft.Avoid             'backend' in glossary.md, search.md, query-the-vault.md
 3  Microsoft.Quotes            punctuation outside the quotes, all in glossary.md
 2  write-good.So               sentence opens with "So "
 1  Microsoft.HeadingPunctuation  README.md
 1  Microsoft.Jargon            'leverage' in literature-pushback.md
 1  Microsoft.UIVerbs           'click' in explanation/surfaces/README.md
```

- [ ] **Step 4: Fix the prose**

Rewrite each flagged passage. Guidance per rule:

- `alex.Condescending` — delete the word. "Simply run X" becomes "Run X". Never substitute another hedge.
- `write-good.ThereIs` / `write-good.So` — rewrite the sentence to lead with its subject. "There is a check that validates X" becomes "A check validates X".
- `Microsoft.Avoid` — `backend` is the flagged term. **Before rewriting, check [glossary.md](docs/reference/data-model/glossary.md)**: if `backend` is a defined Memoria term, this is a terminology ruling, not a typo, and the right fix may be to record the ruling and add `backend` to `.vale/styles/config/vocabularies/Memoria/accept.txt` instead. Canonical term definitions live in the glossary and nowhere else.
- `alex.Race` — replace `master` with the term the sentence actually means (`primary`, `main`, `reference`). If it names the git branch `main`, the finding is already correct and the text is wrong.
- `Microsoft.Quotes` — move the comma or period inside the closing quote. American English.
- `Microsoft.Jargon`, `Microsoft.UIVerbs`, `Microsoft.HeadingPunctuation` — one site each, follow the message.

- [ ] **Step 5: Verify the gate is green**

Run:

```bash
pre-commit run vale --hook-stage manual --all-files
```

Expected: PASS.

- [ ] **Step 6: Verify the prose edits did not break the docs gates**

Run:

```bash
pre-commit run cspell --hook-stage manual --all-files
pre-commit run markdownlint-structural --hook-stage manual --all-files
python3 scripts/checks/doc_link_targets.py
python3 scripts/checks/doc_cited_paths.py
python3 scripts/checks/doc_claims_gate.py
```

Expected: all pass. Rewriting a sentence can break a link's surrounding text or a claim a gate checks — these four are the ones that read docs prose.

- [ ] **Step 7: Commit**

```bash
git add .vale.ini docs
git commit -m "feat: enable nine curated Vale rules and fix the 35 findings

Rules, not packages: running Microsoft and Google together triple-counts the
same sentence, and 93% of the error tier was house-style rules contradicting
this repo's own conventions."
```

---

### Task 3: Verify-then-decide on the two suspect rules

**Files:**
- Modify: `.vale.ini` (only if the rules survive review)
- Modify: files under `docs/` (only if the rules survive review)

**Interfaces:**
- Consumes: the `[*.md]` block from Task 2.
- Produces: either two more enabled rules, or a comment recording why they were rejected.

`write-good.Weasel` (14 findings) and `Microsoft.OxfordComma` (8 findings) were held back because their messages look like parse artifacts — `OxfordComma` quotes fragments such as `', for the PI to clear or amend.'`, which does not read like a list needing a serial comma, and `Weasel`'s token list overlaps `alex.Condescending` on `clearly` and `obviously`, so some of its 14 may be double reports of findings Task 2 already fixed.

This task is a decision, not an implementation. Either outcome is a correct completion.

- [ ] **Step 1: Produce the findings in isolation**

Run:

```bash
export VALE=$(find ~/.cache/pre-commit -maxdepth 4 -name vale -type f | head -1)
mkdir -p /tmp/vale_suspect && cat > /tmp/vale_suspect/.vale.ini <<'EOF'
StylesPath = /home/eranr/memoria-vault/.vale/styles
MinAlertLevel = error

[*.md]
BasedOnStyles = Vale
Vale.Spelling = NO
write-good.Weasel = error
Microsoft.OxfordComma = error
EOF
"$VALE" --config=/tmp/vale_suspect/.vale.ini $(cat /tmp/vale_scope.txt)
```

Expected: a findings list. The count will be lower than 22 if Task 2's rewrites already removed some `Weasel` hits — that overlap is itself part of the evidence.

- [ ] **Step 2: Read every finding against its source line**

For each, open the file at the reported line and judge:

- **`Microsoft.OxfordComma`** — is the flagged text actually a three-or-more-item list missing its serial comma? If the rule is firing on a two-item list or on a comma that is not a list separator at all, it is a false positive and the rule is wrong for this corpus.
- **`write-good.Weasel`** — is the flagged word doing real work? In technical prose `several` and `relatively` are sometimes precise-enough and sometimes vague. Count how many are genuine vagueness.

- [ ] **Step 3: Decide, and record the decision either way**

**If a rule earns its place** (most findings are genuine), add it to the `[*.md]` block in `.vale.ini`:

```ini
write-good.Weasel = error           ; vague quantifiers; overlaps alex.Condescending on 'clearly'/'obviously'
Microsoft.OxfordComma = error
```

Then fix the findings and re-run `pre-commit run vale --hook-stage manual --all-files` until it passes.

**If a rule does not earn its place**, record the rejection in the same block so it is not re-litigated:

```ini
; Measured and rejected 2026-08: write-good.Weasel (14 findings) and
; Microsoft.OxfordComma (8) were reviewed line by line. <N> of <M> were false
; positives — <the specific reason>. Re-enable only with new evidence.
```

Replace `<N>`, `<M>`, and the reason with what Step 2 actually found. A rejection with no measurement in it is the thing this task exists to prevent.

- [ ] **Step 4: Verify the gate**

Run:

```bash
pre-commit run vale --hook-stage manual --all-files
```

Expected: PASS, under whichever decision was made.

- [ ] **Step 5: Clean up and commit**

```bash
rm -rf /tmp/vale_suspect /tmp/vale_scope.txt
git add .vale.ini docs
git commit -m "feat: decide on write-good.Weasel and Microsoft.OxfordComma

Reviewed line by line; the decision and its count are recorded in .vale.ini."
```

If no file under `docs/` changed (the rejection path), drop `docs` from the `git add` line.

---

### Task 4: Pin the rule set with a test

**Files:**
- Create: `tests/test_vale_rules.py`

**Interfaces:**
- Consumes: the `[*.md]` block from Tasks 2 and 3.
- Produces: nothing.

Vale's config is the one lint surface in this repo with no test behind it. Every other tool has one — `test_node_tooling.py` holds the pins equal, `test_cspell_scope.py` holds the scope single-sourced. The failure this prevents: a rule silently dropped from `.vale.ini` leaves the gate green and nobody notices, which is the same shape as the shellcheck alternation that matched nothing.

- [ ] **Step 1: Verify no such test exists**

Run:

```bash
grep -rln "vale" tests/*.py || echo "no vale test - as expected"
```

Expected: `no vale test - as expected`.

- [ ] **Step 2: Write the test**

Create `tests/test_vale_rules.py`:

```python
"""Pins the curated Vale rule set and the offline-vendoring invariant.

Vale enforces terminology and usage over published docs prose. The rules are
chosen individually rather than by adopting a package: measured 2026-08,
adopting Microsoft and Google together triple-counted the same sentence, and
93% of the combined error tier was house-style rules contradicting this repo's
own conventions.

A rule dropped from .vale.ini leaves the gate green and silent, the same shape
as a `files:` regex that matches nothing. This test is what makes that loud.
"""

from __future__ import annotations

import configparser

import pytest

from tests.paths import ROOT

pytestmark = pytest.mark.static

VALE_INI = ROOT / ".vale.ini"
STYLES = ROOT / ".vale/styles"

# The nine rules admitted in Task 2. Task 3 may add write-good.Weasel and
# Microsoft.OxfordComma; add them here in the same commit if it does.
REQUIRED_RULES = {
    "Microsoft.Avoid",
    "Microsoft.Quotes",
    "Microsoft.Jargon",
    "Microsoft.HeadingPunctuation",
    "Microsoft.UIVerbs",
    "alex.Condescending",
    "alex.Race",
    "write-good.ThereIs",
    "write-good.So",
}

VENDORED_PACKAGES = ("Microsoft", "alex", "write-good")


def _parsed() -> configparser.ConfigParser:
    """`.vale.ini` starts with keys before any [section], which configparser rejects.

    Vale's own format allows that; `configparser` raises MissingSectionHeaderError.
    Prepending a synthetic header is what lets the same parser read both halves.
    """
    parser = configparser.ConfigParser(allow_no_value=True, delimiters=("=",))
    parser.optionxform = str  # rule names are case-sensitive
    parser.read_string("[global]\n" + VALE_INI.read_text(encoding="utf-8"))
    return parser


def _markdown_section() -> dict[str, str]:
    return dict(_parsed()["*.md"])


def test_every_curated_rule_is_enabled_at_error():
    section = _markdown_section()
    missing = sorted(rule for rule in REQUIRED_RULES if rule not in section)
    assert missing == [], f"curated Vale rules dropped from .vale.ini: {missing}"
    wrong_level = sorted(
        rule for rule in REQUIRED_RULES if section[rule].split(";")[0].strip() != "error"
    )
    assert wrong_level == [], (
        f"these rules are not set to `error`, so MinAlertLevel silently drops them: {wrong_level}"
    )


def test_spelling_stays_with_cspell():
    assert _markdown_section().get("Vale.Spelling", "").split(";")[0].strip() == "NO", (
        "Vale must not spell-check; cspell owns spelling (CONTRIBUTING, Spelling)"
    )


def test_styles_are_vendored_so_the_gate_runs_offline():
    """`vale sync` is a manual refresh. The hook runs `vale` and never syncs."""
    for package in VENDORED_PACKAGES:
        directory = STYLES / package
        assert directory.is_dir(), (
            f"{directory} is missing; run `vale sync` and commit it. The gate has no network."
        )
        assert (directory / "meta.json").is_file(), (
            f"{directory}/meta.json is missing, so the vendored version cannot be audited"
        )


def test_min_alert_level_is_error():
    level = _parsed()["global"].get("MinAlertLevel", "")
    assert level.split(";")[0].strip() == "error", (
        "MinAlertLevel must stay at error; lowering it turns every rule in "
        "REQUIRED_RULES into a warning the gate ignores"
    )
```

- [ ] **Step 3: Run the test**

Run:

```bash
python3 -m pytest tests/test_vale_rules.py -q
```

Expected: PASS. If `test_every_curated_rule_is_enabled_at_error` fails on a rule name, the `.vale.ini` spelling and the `REQUIRED_RULES` spelling disagree — fix whichever is wrong. If `configparser` raises on the `;` comments, note that `;` is a valid inline comment delimiter only at line start in `configparser`; move any trailing `;` comments in `.vale.ini` onto their own lines.

- [ ] **Step 4: Prove the test can fail**

Run:

```bash
sed -i 's/^alex.Race = error/# alex.Race = error/' .vale.ini
python3 -m pytest tests/test_vale_rules.py -q
sed -i 's/^# alex.Race = error/alex.Race = error/' .vale.ini
python3 -m pytest tests/test_vale_rules.py -q
```

Expected: FAIL naming `['alex.Race']`, then PASS after restoring. A completeness test that has never failed is a completeness test nobody has verified.

- [ ] **Step 5: Commit**

```bash
git add tests/test_vale_rules.py
git commit -m "test: pin the curated Vale rule set and the offline invariant

A rule dropped from .vale.ini leaves the gate green and silent."
```

---

### Task 5: Make Vale runnable from the editor without a second pin

**Files:**
- Create: `.vscode/tasks.json`
- Modify: `CONTRIBUTING.md` (the "Documentation authoring conventions" section)

**Interfaces:**
- Consumes: nothing.
- Produces: nothing.

The obvious move — recommend `ChrisChinchilla.vale-vscode` — is the wrong one here. That extension resolves its own Vale binary, and there is no `importStrategy: fromEnvironment` equivalent to hold it equal to the pinned hook. This repo already treats "two pins for one tool" as a defect and has two tests guarding against it (`ruff`, `oxlint`/`oxfmt`). A third instance that *cannot* be held equal should not be created.

Instead, give the editor a task that runs the pinned hook. One binary, one version, no skew.

- [ ] **Step 1: Verify no tasks file exists yet**

Run:

```bash
ls .vscode/
```

Expected: `extensions.json  settings.json`. If `tasks.json` already exists, merge the task below into its `tasks` array rather than overwriting the file.

- [ ] **Step 2: Add the task**

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "vale: lint docs prose",
      "type": "shell",
      "command": "pre-commit run vale --hook-stage manual --all-files",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      },
      "group": "test"
    },
    {
      "label": "vale: lint the current file",
      "type": "shell",
      "command": "pre-commit run vale --hook-stage manual --files ${file}",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "dedicated"
      },
      "group": "test"
    }
  ]
}
```

Both run the version-pinned hook binary. Deliberately no `ChrisChinchilla.vale-vscode` recommendation: the extension resolves its own Vale and cannot be pinned to the hook rev, which would create exactly the editor-versus-gate skew `tests/test_node_tooling.py` exists to prevent for ruff and oxfmt.

- [ ] **Step 3: Document how to run it**

In `CONTRIBUTING.md`, under "Documentation authoring conventions", add after the **Spelling** bullet:

```markdown
- **Terminology:** `.vale.ini` holds the usage rulings Vale enforces over
  published docs prose. Run them from the editor with the "vale: lint the
  current file" task (Ctrl+Shift+P → "Tasks: Run Task"), or from a shell with
  `pre-commit run vale --hook-stage manual --all-files`. Both use the pinned
  hook binary; do not install a separate Vale, which would lint with a version
  the gate does not use.
```

- [ ] **Step 4: Verify**

Run:

```bash
python3 -c "import json; json.load(open('.vscode/tasks.json')); print('tasks.json ok')"
pre-commit run vale --hook-stage manual --all-files
pre-commit run cspell --hook-stage manual --files CONTRIBUTING.md
```

Expected: `tasks.json ok`, Vale PASS, cspell PASS.

- [ ] **Step 5: Commit**

```bash
git add .vscode/tasks.json CONTRIBUTING.md
git commit -m "feat: run Vale from the editor through the pinned hook

A VS Code task rather than the Vale extension: the extension resolves its own
binary and cannot be held equal to the hook rev."
```

---

## Self-Review

**Spec coverage.** Vendoring for offline determinism (Task 1), the nine clean rules and their 35 findings (Task 2), the verify-then-decide on the 22 suspect findings the user asked for (Task 3), a completeness test matching the pattern every other tool here has (Task 4), and editor access without a second pin (Task 5).

**Placeholder scan.** Task 3 Step 3 contains `<N>`, `<M>`, and `<the specific reason>` — these are outputs of that task's own review step, not deferred work, and the step says so explicitly. Everywhere else the content is literal.

**Type consistency.** Rule names are spelled identically in `.vale.ini` (Task 2), `REQUIRED_RULES` (Task 4), and the measurement tables: `Microsoft.Avoid`, `Microsoft.Quotes`, `Microsoft.Jargon`, `Microsoft.HeadingPunctuation`, `Microsoft.UIVerbs`, `alex.Condescending`, `alex.Race`, `write-good.ThereIs`, `write-good.So`. Task 3's two candidates are `write-good.Weasel` and `Microsoft.OxfordComma` throughout.

**Dependency note.** Task 4's `REQUIRED_RULES` must be updated in the same commit as Task 3 if Task 3 enables either rule. That coupling is stated in the test's own comment so a reader of Task 4 alone still sees it.

**One risk worth naming.** Task 2 Step 4 flags `backend` in `glossary.md`. Fixing a glossary term by rewriting prose would be wrong — the glossary is the canonical home for term rulings, so that finding may resolve as an `accept.txt` entry plus a glossary ruling instead. The step says so rather than assuming a rewrite.
