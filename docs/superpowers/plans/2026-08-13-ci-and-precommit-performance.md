# CI and Pre-commit Performance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (- [ ]) syntax for tracking.

**Goal:** Reduce CI and pre-commit latency without narrowing the verification
contract.

**Architecture:** A fail-closed Actions scope job publishes a dynamic matrix
once; the existing shard job consumes it and installs only the resources its
shard owns. The existing CI-only VERIFY_DOCS_ONLY=1 mode replaces the full
manual hook stage with four prose hooks. CSpell keeps its scope in cspell.json
and becomes serial only at pre-commit's process boundary.

**Tech Stack:** GitHub Actions, Bash, Python 3.12, pytest, PyYAML, pre-commit,
Node/CSpell.

## Global Constraints

- Execute only after #1832 is triaged enhancement + ready-for-agent, is
  unassigned/unblocked, and the executor claims it before modifying code.
- python scripts/verify remains the one correctness gate and must end
  verify: OK.
- Normal PRs and every main push retain all four shards: lint, contract,
  runtime, and sweep. The required verify job remains a non-matrix fan-in.
- Invalid, incomplete, empty, 3,000-file, unavailable, or failed PR-file
  inspection uses the full matrix, ps1=true, and docs_only=false. A failed
  scope job or unavailable matrix must make the fan-in red.
- Classify both paths of a rename. Markdown under src/ is package data and is
  never docs-only. Retain the existing CI-only VERIFY_DOCS_ONLY=1; do not add a
  local --docs-only switch.
- Keep Verify's pre-commit cache separate from Gitleaks' cache. Keep
  pre-commit gc in the only job that restores Verify's cache.
- PSScriptAnalyzer runs only in lint, but all main pushes and unknown or
  PowerShell PR scope install it.
- CSpell keeps filename passing plus cspell.json files, enableGlobDot, and
  ignorePaths as its sole scope. Do not add --cache, pass_filenames: false, an
  exclude, or another file list.
- Stage exact paths only; never use an unbounded git add form.

---

### Task 1: Move scope detection to a fail-closed job

**Files:**
- Modify: .github/workflows/verify.yml
- Modify: tests/test_docs_only_scope.py
- Modify: tests/test_verify_script.py

**Interfaces:**
- Produces scope outputs matrix, ps1, and docs_only.
- matrix is exactly {"shard":["lint","contract","runtime","sweep"]} or
  {"shard":["lint","sweep"]}.
- shards consumes fromJSON(needs.scope.outputs.matrix); verify needs both
  scope and shards.

- [ ] **Step 1: Write the failing dynamic-matrix contracts**

In tests/test_docs_only_scope.py, make _scope_script() read the id: scope step
from workflow["jobs"]["scope"]. Decode outputs["matrix"] with json.loads.
Update every classifier expectation to include matrix:

~~~
FULL_MATRIX = {"shard": ["lint", "contract", "runtime", "sweep"]}
DOCS_MATRIX = {"shard": ["lint", "sweep"]}

assert result == {
    "ps1": "false",
    "docs_only": "true",
    "matrix": DOCS_MATRIX,
}
~~~

Complete docs-only data alone expects DOCS_MATRIX. Code, runtime Markdown,
rename origin, pagination, hostile filename, count mismatch, API failure, empty
input, and 3,000 records expect FULL_MATRIX and safe flags.

In tests/test_verify_script.py, assert the workflow shape:

~~~
assert workflow["jobs"]["shards"]["needs"] == "scope"
assert workflow["jobs"]["shards"]["strategy"]["matrix"] == (
    "$" + "{{ fromJSON(needs.scope.outputs.matrix) }}"
)
fan_in = workflow["jobs"]["verify"]
assert fan_in["needs"] == ["scope", "shards"]
assert fan_in["if"] == "always()"
assert "needs.scope.result" in fan_in["steps"][0]["run"]
assert "needs.shards.result" in fan_in["steps"][0]["run"]
~~~

Also assert scope.outputs is exactly matrix, ps1, docs_only, and that its shell
script initializes all three safe defaults before gh api.

- [ ] **Step 2: Run the contracts to prove they fail**

Run:

~~~
python3 -m pytest tests/test_docs_only_scope.py tests/test_verify_script.py -q
~~~

Expected: FAIL because scope is still a matrix-job step and publishes no matrix.

- [ ] **Step 3: Implement the top-level scope job**

Add this job before shards in .github/workflows/verify.yml:

~~~
scope:
  runs-on: ubuntu-latest
  outputs:
    matrix: ${{ steps.scope.outputs.matrix }}
    ps1: ${{ steps.scope.outputs.ps1 }}
    docs_only: ${{ steps.scope.outputs.docs_only }}
~~~

Its id: scope shell step must initialize before any API call:

~~~
matrix='{"shard":["lint","contract","runtime","sweep"]}'
ps1=true
docs_only=false
paths='[]'
~~~

On pull_request, retain the current gh api --paginate --slurp and jq
validation: flatten pages, validate filename and previous_filename, require
0 < record_count < 3000, equal PR_CHANGED_FILES, and classify both paths.
Only a complete docs-only result changes the three values to:

~~~
matrix='{"shard":["lint","sweep"]}'
ps1=false
docs_only=true
~~~

Write all three values to GITHUB_OUTPUT at the end. On a push, make no PR API
call and retain defaults. Set the shards job exactly as follows; remove the old
per-shard scope step and read flags from needs.scope.outputs.

~~~yaml
shards:
  needs: scope
  strategy:
    fail-fast: false
    matrix: ${{ fromJSON(needs.scope.outputs.matrix) }}
~~~

Set verify needs to [scope, shards] and if to always(). Its check must exit 1
unless both needs.scope.result and needs.shards.result equal success. Do not put
if: always() on shards: an unevaluable matrix must skip and leave the fan-in red.

- [ ] **Step 4: Run focused verification**

Run:

~~~
python3 -m pytest tests/test_docs_only_scope.py tests/test_verify_script.py -q
pre-commit run yamllint --hook-stage manual --files .github/workflows/verify.yml
~~~

Expected: PASS. API failure and malformed output use the full matrix; a failed
scope job cannot make the required check green.

- [ ] **Step 5: Commit Task 1**

~~~
git add .github/workflows/verify.yml tests/test_docs_only_scope.py tests/test_verify_script.py
git commit -m "ci: derive a fail-closed verification matrix from PR scope"
~~~

---

### Task 2: Provision each CI dependency in its owner shard

**Files:**
- Modify: .github/workflows/verify.yml
- Modify: tests/test_node_tooling.py
- Modify: tests/test_verify_script.py

**Interfaces:**
- Consumes Task 1's matrix.shard and needs.scope.outputs.ps1.
- Produces explicit condition strings that mirror the verifier roster.

- [ ] **Step 1: Write failing resource-ownership tests**

In tests/test_node_tooling.py, replace the obsolete all-shards assertion with:

~~~
assert steps[install_index]["if"] == "matrix.shard == 'contract'"
node = next(step for step in steps if step.get("uses", "").startswith("actions/setup-node@"))
assert node["if"] == "matrix.shard == 'lint' || matrix.shard == 'contract'"
npm_cache = next(step for step in steps if step.get("name") == "Cache Obsidian npm downloads")
assert npm_cache["if"] == "matrix.shard == 'contract'"
assert npm_cache["with"]["path"] == "~/.npm"
assert "packages/memoria-obsidian/package-lock.json" in npm_cache["with"]["key"]
~~~

In tests/test_verify_script.py, find named workflow steps and assert:

~~~
assert precommit_cache["if"] == "matrix.shard == 'lint'"
assert gc["if"] == "matrix.shard == 'lint'"
assert pssa_cache["if"] == "matrix.shard == 'lint' && needs.scope.outputs.ps1 != 'false'"
assert bubblewrap["if"] == "matrix.shard == 'runtime'"
assert python["with"]["cache-dependency-path"] == "requirements-dev.txt\npyproject.toml"
~~~

- [ ] **Step 2: Prove the ownership tests are red**

Run:

~~~
python3 -m pytest tests/test_node_tooling.py tests/test_verify_script.py -q
~~~

Expected: FAIL because setup is still unconditional and the pip cache misses
pyproject.toml.

- [ ] **Step 3: Make the setup conditions exact**

Set the Python cache dependency path to:

~~~
requirements-dev.txt
pyproject.toml
~~~

Use actions/setup-node only when matrix.shard is lint or contract. Add the
contract-only cache step named Cache Obsidian npm downloads:

~~~
if: matrix.shard == 'contract'
uses: actions/cache@55cc8345863c7cc4c66a329aec7e433d2d1c52a9
with:
  path: ~/.npm
  key: ${{ runner.os }}-npm-obsidian-${{ hashFiles('packages/memoria-obsidian/package-lock.json') }}
~~~

Apply these exact conditions:

| Step | Condition |
| --- | --- |
| Adapter npm ci | matrix.shard == 'contract' |
| Bubblewrap setup/probe | matrix.shard == 'runtime' |
| Verify pre-commit cache and pre-commit gc | matrix.shard == 'lint' |
| PSScriptAnalyzer cache | matrix.shard == 'lint' && needs.scope.outputs.ps1 != 'false' |
| PSScriptAnalyzer install | matrix.shard == 'lint' && needs.scope.outputs.ps1 != 'false' && steps.pssa-cache.outputs.cache-hit != 'true' |

Leave Python runtime/dev installation unconditional. Do not touch the Gitleaks
cache namespace.

- [ ] **Step 4: Prove ownership and YAML validity are green**

Run:

~~~
python3 -m pytest tests/test_node_tooling.py tests/test_verify_script.py -q
pre-commit run yamllint --hook-stage manual --files .github/workflows/verify.yml
~~~

Expected: PASS. No shard installs an unrelated runtime tool.

- [ ] **Step 5: Commit Task 2**

~~~
git add .github/workflows/verify.yml tests/test_node_tooling.py tests/test_verify_script.py
git commit -m "ci: provision verification dependencies by shard"
~~~

---

### Task 3: Restrict only verified docs-only lint to prose hooks

**Files:**
- Modify: scripts/verify
- Modify: tests/test_verify_script.py

**Interfaces:**
- Produces DOCS_LINT_HOOKS = ("vale", "markdownlint-structural",
  "mermaid-parse", "cspell").
- Preserves the normal first GATES command: pre-commit run --hook-stage manual
  --all-files.

- [ ] **Step 1: Write the failing exact-roster test**

Add to tests/test_verify_script.py:

~~~
def test_docs_only_lint_runs_exactly_the_prose_hook_roster() -> None:
    namespace = _verify_namespace()
    assert namespace["DOCS_LINT_HOOKS"] == (
        "vale", "markdownlint-structural", "mermaid-parse", "cspell",
    )
    commands = namespace["_gates_for_run"](True, "lint")
    assert commands[:4] == [
        ["pre-commit", "run", hook, "--hook-stage", "manual", "--all-files"]
        for hook in namespace["DOCS_LINT_HOOKS"]
    ]
    text = "\n".join(" ".join(command) for command in commands)
    assert not any(tool in text for tool in ("ruff", "mypy", "yamllint", "shellcheck", "oxlint", "oxfmt"))
~~~

Update the existing docs-only roster test to expect the first prose command,
and assert normal lint still begins with the full manual-stage command.

- [ ] **Step 2: Prove it is red**

Run:

~~~
python3 -m pytest tests/test_verify_script.py -q
~~~

Expected: FAIL because the tuple and replacement commands do not exist.

- [ ] **Step 3: Add the explicit docs-only command path**

Before GATES in scripts/verify, add:

~~~
FULL_LINT_COMMAND = ["pre-commit", "run", "--hook-stage", "manual", "--all-files"]
DOCS_LINT_HOOKS = ("vale", "markdownlint-structural", "mermaid-parse", "cspell")
DOCS_LINT_COMMANDS = tuple(
    ["pre-commit", "run", hook, "--hook-stage", "manual", "--all-files"]
    for hook in DOCS_LINT_HOOKS
)
~~~

Add manual_lint: bool = False to Gate and mark the first gate manual_lint=True.
In _gates_for_run(), when docs_only and gate.manual_lint, extend reduced with
copies of DOCS_LINT_COMMANDS and continue. Keep every other docs-only rule:
product gates stay, sweep runs static tests once, code-only gates stay out.

- [ ] **Step 4: Prove docs and normal modes are green**

Run:

~~~
python3 -m pytest tests/test_verify_script.py tests/test_docs_only_scope.py -q
~~~

Expected: PASS. Full lint is unchanged; docs-only runs exactly four prose hooks.

- [ ] **Step 5: Commit Task 3**

~~~
git add scripts/verify tests/test_verify_script.py
git commit -m "verify: limit proven docs-only lint to prose hooks"
~~~

---

### Task 4: Add CI-only slow-test telemetry

**Files:**
- Modify: scripts/verify
- Modify: .github/workflows/verify.yml
- Modify: tests/test_verify_script.py

**Interfaces:**
- MEMORIA_PYTEST_DURATIONS=1 adds --durations=25 and
  --durations-min=0.25; local commands remain unchanged.

- [ ] **Step 1: Write the failing environment-sensitive test**

Add a helper that temporarily updates os.environ, calls _verify_namespace(), and
restores prior values. Assert local pytest commands omit duration flags, while
commands built with MEMORIA_PYTEST_DURATIONS=1 include:

~~~
["--durations=25", "--durations-min=0.25"]
~~~

Assert the workflow Run verify environment sets MEMORIA_PYTEST_DURATIONS: "1".

- [ ] **Step 2: Prove it is red**

Run:

~~~
python3 -m pytest tests/test_verify_script.py -q
~~~

Expected: FAIL because neither verifier nor workflow adds duration data.

- [ ] **Step 3: Implement the opt-in arguments**

Add:

~~~
def _duration_args() -> list[str]:
    return ["--durations=25", "--durations-min=0.25"] if os.environ.get(
        "MEMORIA_PYTEST_DURATIONS"
    ) == "1" else []
~~~

Call it in _pytest_cmd() immediately before -m, markers. Add
MEMORIA_PYTEST_DURATIONS: "1" only to workflow Run verify.

- [ ] **Step 4: Prove telemetry is green**

Run:

~~~
python3 -m pytest tests/test_verify_script.py -q
~~~

Expected: PASS. Bare local verification has no duration output.

- [ ] **Step 5: Commit Task 4**

~~~
git add scripts/verify .github/workflows/verify.yml tests/test_verify_script.py
git commit -m "ci: report slow verification tests"
~~~

---

### Task 5: Make CSpell one scoped pre-commit process

**Files:**
- Modify: .pre-commit-config.yaml
- Modify: tests/test_cspell_scope.py

**Interfaces:**
- Produces only require_serial: true on the existing local CSpell hook.

- [ ] **Step 1: Record a fresh three-run warm baseline**

Run:

~~~
pre-commit run cspell --hook-stage manual --all-files
for run in 1 2 3; do
  /usr/bin/time -f "baseline %e s" pre-commit run cspell --hook-stage manual --all-files
done
~~~

Expected: three green timings. Record the median in the task report. The prior
median was 6.12 seconds, but remeasure the execution machine.

- [ ] **Step 2: Write the failing batching assertion**

Append to test_precommit_hook_triggers_on_any_markdown:

~~~
assert hook["require_serial"] is True
assert "pass_filenames" not in hook
assert "cache" not in hook["entry"]
~~~

- [ ] **Step 3: Prove it is red**

Run:

~~~
python3 -m pytest tests/test_cspell_scope.py -q
~~~

Expected: FAIL with missing require_serial.

- [ ] **Step 4: Add the sole configuration change**

Place this beside files: \.md$ on the existing cspell hook:

~~~
require_serial: true
~~~

Do not edit CSpell's entry, dependencies, language, stages, or cspell.json.

- [ ] **Step 5: Prove scope and measured improvement**

Run:

~~~
python3 -m pytest tests/test_cspell_scope.py tests/test_node_tooling.py tests/test_lint_coverage.py -q
pre-commit run cspell --hook-stage manual --all-files --verbose
for run in 1 2 3; do
  /usr/bin/time -f "serial %e s" pre-commit run cspell --hook-stage manual --all-files
done
~~~

Expected: all checks pass, verbose output shows one CSpell process over the same
corpus (currently 284 files), and the median saves at least 0.5 seconds and 10%
versus Step 1. If it misses either threshold, reverse only the YAML line with
apply_patch, prove the focused test red again, and stop for owner direction.

- [ ] **Step 6: Commit Task 5**

~~~
git add .pre-commit-config.yaml tests/test_cspell_scope.py
git commit -m "pre-commit: run CSpell in one scoped process"
~~~

---

### Task 6: Integrate and measure the CI/pre-commit slice

**Files:**
- Modify: none unless the focused suite identifies a real integration defect.

- [ ] **Step 1: Run focused integration checks**

Run:

~~~
python3 -m pytest tests/test_docs_only_scope.py tests/test_verify_script.py tests/test_node_tooling.py tests/test_cspell_scope.py tests/test_lint_coverage.py -q
pre-commit run yamllint --hook-stage manual --files .github/workflows/verify.yml
~~~

Expected: PASS.

- [ ] **Step 2: Run the complete gate**

Run:

~~~
python scripts/verify
git diff --check
~~~

Expected: verify: OK and no whitespace errors.

- [ ] **Step 3: Commit an integration-only repair only if one exists**

Run:

~~~
git status --short
~~~

Expected: no uncommitted tracked changes. If a preceding task requires an
integration repair, stage only its named files and commit
ci: complete verification performance integration; otherwise create no empty
commit.

- [ ] **Step 4: Collect post-PR evidence**

After opening the implementation PR, record three green runs separately for
cache-hit and cache-miss conditions: workflow wall time, each shard's setup and
verify time, duration output, and the selected docs-only matrix. Expect runtime
to omit pre-commit/PSScriptAnalyzer, contract alone to install adapter
dependencies, and docs-only PRs to retain prose hooks plus static tests. Do not
add a test shard until those timings show a material imbalance.
