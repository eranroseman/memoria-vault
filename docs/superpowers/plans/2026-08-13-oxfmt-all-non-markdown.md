# Oxfmt all-non-Markdown Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Oxfmt the pinned formatter for every tracked non-Markdown file it supports, including generated seeded artifacts, while preserving the adapter build and floor contracts.

**Architecture:** First make the Obsidian adapter build canonicalize its own generated JavaScript and CSS through its package-local Oxfmt API. Then broaden the pre-commit hook, editor settings, and policy tests to every Oxfmt-supported non-Markdown suffix; format the existing corpus and regenerate only the resulting seed digests. The adapter build remains the single source of truth for generated release bytes.

**Tech Stack:** Oxfmt 0.63.0, Svelte 5.56.8, pre-commit, Node 22+, esbuild, Pytest, PyYAML, TOML parsing, VS Code Oxc extension.

## Global Constraints

- Before making a code change, follow `AGENTS.md` issue policy: work only from an unassigned, unblocked `ready-for-agent` issue, then claim it before the first edit.
- Use `oxfmt@0.63.0` and `svelte@5.56.8` exactly in both the adapter package and the Oxfmt hook environment. Do not use a system-wide Oxfmt binary as proof.
- Oxfmt must cover only these non-Markdown suffixes: `.js`, `.mjs`, `.cjs`, `.jsx`, `.ts`, `.mts`, `.cts`, `.tsx`, `.json`, `.jsonc`, `.json5`, `.yaml`, `.yml`, `.toml`, `.css`, `.scss`, `.less`, `.pcss`, `.postcss`, `.wxss`, `.graphql`, `.gql`, `.graphqls`, `.html`, `.htm`, `.hta`, `.xhtml`, `.component.html`, `.vue`, `.svelte`, `.hbs`, `.handlebars`, and `.mjml`.
- Do not format `.md`, `.markdown`, or `.mdx`; preserve their existing editor and hook behavior.
- Keep filename passing enabled for the Oxfmt hook. Its `types_or` must be exactly `[file]`; never give it `pass_filenames: false` or a catch-all `files` regex.
- The adapter build must format only generated `main.js` and `styles.css`. It must copy `manifest.json` as source bytes.
- Remove no seeded artifact from Oxfmt coverage and do not relax `npm run check --prefix packages/memoria-obsidian` byte parity.
- Regenerate floor goldens only through `MEMORIA_FLOOR_UPDATE_GOLDENS=1`; then rerun the same floor suite without that variable. Review that every golden change is a seed-file digest change.
- Preserve semantic values in YAML, JSON, and TOML; validate vendor styles with Vale after formatting.
- Stage explicit paths only. Never use `git add -A`, `git reset --hard`, or `git checkout --`.
- Retire this plan and its companion spec only after the final branch review and full verification pass. Delete them rather than changing their dated status headers.

---

## File structure

- `packages/memoria-obsidian/scripts/build.mjs` — constructs the committed Obsidian release artifacts; will canonicalize generated JS and CSS through the package-local formatter.
- `tests/test_memoria_obsidian_package.py` — adapter build and seeded-artifact contract tests; will assert the committed generated files are Oxfmt-idempotent.
- `.oxfmtrc.json` — global formatting options and only the Markdown/disposable-directory exclusions.
- `.pre-commit-config.yaml` — pinned Oxfmt hook, explicit non-Markdown suffix scope, and pinned Svelte runtime for the hook.
- `packages/memoria-obsidian/package.json` and `packages/memoria-obsidian/package-lock.json` — editor/build dependencies; will pin the Svelte runtime used by Oxfmt.
- `.github/dependabot.yml` — freezes coupled Oxfmt/Svelte formatter updates until a reviewed synchronized upgrade.
- `.vscode/settings.json` — makes the Oxc extension the on-save formatter for each non-Markdown language mode it supports.
- `tests/test_lint_coverage.py` — derives the Oxfmt file-policy boundary from tracked paths and hook configuration.
- `tests/test_node_tooling.py` — pins hook/package/editor/dependency parity.
- `tests/fixtures/floor/goldens/` — 39 seed-digest fixtures updated only after generated and seeded JSON bytes change.

### Task 1: Canonicalize generated Obsidian artifacts in the build

**Files:**
- Modify: `packages/memoria-obsidian/scripts/build.mjs:1-49`
- Modify: `tests/test_memoria_obsidian_package.py:1-120`
- Modify: `src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/main.js`
- Modify: `src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/styles.css`
- Modify: `tests/fixtures/floor/goldens/` (39 JSON files)

**Interfaces:**
- Consumes: Oxfmt's package-local `format(fileName, sourceText, options)` API, returning `{ code, errors }`; existing `packageDir`, `seedDir`, and esbuild output buffers in `build.mjs`.
- Produces: `npm run build --prefix packages/memoria-obsidian` writes Oxfmt-canonical `main.js` and `styles.css`; `npm run check --prefix packages/memoria-obsidian` compares those same canonical bytes.

- [ ] **Step 1: Inspect the starting adapter parity contract and establish the issue claim**

Run:

```bash
git status --short
npm run check --prefix packages/memoria-obsidian
gh issue list --state open --limit 500 --search 'Oxfmt non-Markdown in:title'
```

Expected: the worktree is clean, the current adapter check passes, and the issue search either names an existing ready-for-agent issue to claim or returns no duplicate. If no matching issue exists, file `Format all supported non-Markdown files with Oxfmt` without labels, have a triage session apply exactly its category and `ready-for-agent` state, reread the frontier, then assign the current GitHub identity before proceeding. Do not begin implementation from an untriaged issue.

- [ ] **Step 2: Write the failing canonical-artifact test**

Add this helper and test beside the existing adapter package tests in `tests/test_memoria_obsidian_package.py`:

```python
_OXFMT_FORMAT_PROBE = """
import { readFile } from "node:fs/promises";
import { format } from "oxfmt";

const [filename, sourcePath, configPath] = process.argv.slice(1);
const options = JSON.parse(await readFile(configPath, "utf8"));
delete options.$schema;
delete options.ignorePatterns;
const result = await format(filename, await readFile(sourcePath, "utf8"), options);
if (result.errors.length) {
  throw new Error(result.errors.map(({ message }) => message).join("\\n"));
}
process.stdout.write(result.code);
"""


def _format_with_adapter_oxfmt(filename: str, source: Path) -> str:
    result = subprocess.run(
        [
            "node",
            "--input-type=module",
            "-e",
            _OXFMT_FORMAT_PROBE,
            filename,
            str(source),
            str(ROOT / ".oxfmtrc.json"),
        ],
        cwd=PLUGIN,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def test_memoria_obsidian_seeded_release_artifacts_are_oxfmt_canonical() -> None:
    assert _format_with_adapter_oxfmt("main.js", SEED_PLUGIN / "main.js") == (
        SEED_PLUGIN / "main.js"
    ).read_text(encoding="utf-8")
    assert _format_with_adapter_oxfmt("styles.css", PLUGIN / "styles.css") == (
        SEED_PLUGIN / "styles.css"
    ).read_text(encoding="utf-8")
```

The test uses the adapter's installed Oxfmt package and the same root options that the build will use. It does not invoke a PATH-resolved binary.

- [ ] **Step 3: Run the test to verify it fails for the expected reason**

Run:

```bash
python -m pytest tests/test_memoria_obsidian_package.py::test_memoria_obsidian_seeded_release_artifacts_are_oxfmt_canonical -q
```

Expected: FAIL because the currently committed raw esbuild bundle and stylesheet are not Oxfmt-idempotent. Do not change the expected test output to accept the raw artifacts.

- [ ] **Step 4: Make `build.mjs` produce canonical generated bytes**

At the top of `packages/memoria-obsidian/scripts/build.mjs`, add:

```javascript
import { format } from "oxfmt";
```

After `packageDir` is calculated, load the root config and remove path-selection fields before passing it to Oxfmt:

```javascript
const formatterOptions = JSON.parse(
  await readFile(resolve(packageDir, "../../.oxfmtrc.json"), "utf8"),
);
delete formatterOptions.$schema;
delete formatterOptions.ignorePatterns;

async function formatArtifact(name, contents) {
  const result = await format(name, contents.toString(), formatterOptions);
  if (result.errors.length) {
    throw new Error(
      `Oxfmt could not format ${name}:\n${result.errors
        .map(({ message }) => message)
        .join("\n")}`,
    );
  }
  return Buffer.from(result.code);
}
```

Replace only the `main.js` and `styles.css` values in `expected` with:

```javascript
["main.js", await formatArtifact("main.js", bundled.outputFiles[0].contents)],
["styles.css", await formatArtifact("styles.css", await readFile(resolve(packageDir, "styles.css")))],
```

Leave the existing `manifest.json` `readFile` value unchanged. Do not add a second build command, a formatter wrapper script, or a path-ignore bypass outside this helper.

- [ ] **Step 5: Regenerate release artifacts and prove the focused contract is green**

Run:

```bash
npm run build --prefix packages/memoria-obsidian
npm run check --prefix packages/memoria-obsidian
python -m pytest tests/test_memoria_obsidian_package.py -q
```

Expected: the build rewrites only the two seeded release artifacts, the parity command exits 0, and the adapter package tests pass including the new canonicalization test.

- [ ] **Step 6: Regenerate and review the first seed digest change**

Run:

```bash
MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_sweep_operations.py -q
python -m pytest tests/test_floor_sweep_operations.py -q
git diff --name-only -- tests/fixtures/floor/goldens
```

Expected: both floor invocations pass; the diff names all 39 golden files. Inspect each golden change: it may change only the hashes for seeded `main.js` and `styles.css`, not operation output, manifest structure, or unrelated vault files.

- [ ] **Step 7: Run the task-level checks and commit the self-contained build change**

Run:

```bash
git diff --check
pre-commit run oxfmt --hook-stage manual --files \
  packages/memoria-obsidian/scripts/build.mjs \
  src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/main.js \
  src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/styles.css
```

Expected: both commands pass. Stage only `packages/memoria-obsidian/scripts/build.mjs`, `tests/test_memoria_obsidian_package.py`, the two seeded artifacts, and `tests/fixtures/floor/goldens/`; then commit:

```bash
git commit -m "build: canonicalize seeded Obsidian artifacts with Oxfmt"
```

### Task 2: Enforce and migrate the complete non-Markdown formatter policy

**Files:**
- Modify: `.oxfmtrc.json`
- Modify: `.pre-commit-config.yaml:114-137`
- Modify: `.github/dependabot.yml:58-88`
- Modify: `.vscode/settings.json:27-55`
- Modify: `packages/memoria-obsidian/package.json`
- Modify: `packages/memoria-obsidian/package-lock.json`
- Modify: `tests/test_lint_coverage.py:40-90,300-390`
- Modify: `tests/test_node_tooling.py:117-145,230-260`
- Modify: every Oxfmt-supported tracked non-Markdown file reported by the pre-migration check, including vendored Vale styles, frozen JSON, configuration, seeded JSON, and package CSS.
- Modify: `tests/fixtures/floor/goldens/` (39 JSON files)

**Interfaces:**
- Consumes: Task 1's Oxfmt-canonical generated artifacts and the existing `_hook`, `_claims`, `_tracked`, `_unclaimed_reason`, and `_positive_glob_matches` test helpers.
- Produces: an Oxfmt hook with generic file classification and explicit supported suffix selection; package/hook/editor Svelte parity; a clean canonical tracked non-Markdown corpus.

- [ ] **Step 1: Add failing policy, parity, and editor tests**

In `tests/test_lint_coverage.py`, define this exact immutable suffix tuple next to `HOOK_FOR_OWNER`:

```python
OXFMT_NON_MARKDOWN_SUFFIXES = (
    ".component.html", ".graphqls", ".handlebars", ".postcss", ".jsonc", ".json5",
    ".yaml", ".yml", ".toml", ".scss", ".less", ".pcss", ".wxss", ".graphql",
    ".html", ".xhtml", ".svelte", ".mjs", ".cjs", ".jsx", ".mts", ".cts",
    ".tsx", ".json", ".css", ".gql", ".htm", ".hta", ".vue", ".hbs",
    ".mjml", ".js", ".ts",
)
```

Add a helper that selects a path when it ends in any member of that tuple, then add this boundary test:

```python
def test_oxfmt_covers_every_tracked_supported_non_markdown_file():
    oxfmt = _hook("oxfmt")
    assert oxfmt["types_or"] == ["file"]
    paths = [path for path in _tracked() if path.endswith(OXFMT_NON_MARKDOWN_SUFFIXES)]
    escaped = sorted(path for path in paths if not _claims("oxfmt", path))
    assert escaped == [], escaped
    markdown = [
        path for path in _tracked() if path.endswith((".md", ".markdown", ".mdx"))
    ]
    assert [path for path in markdown if _claims("oxfmt", path)] == []
```

Do not filter `paths` through `_unclaimed_reason`: the generated seed bundle remains exempt from Oxlint, but must be covered by Oxfmt.

In `tests/test_node_tooling.py`, extend the existing Oxc parity test so it requires all of the following:

```python
settings = json.loads(VSCODE_SETTINGS.read_text(encoding="utf-8"))
dependabot = yaml.safe_load(DEPENDABOT.read_text(encoding="utf-8"))
oxfmt_config = json.loads((ROOT / ".oxfmtrc.json").read_text(encoding="utf-8"))
oxfmt = _hook("oxfmt")
assert oxfmt["types_or"] == ["file"]
assert oxfmt["files"] == (
    r"\.(?:js|mjs|cjs|jsx|ts|mts|cts|tsx|json|jsonc|json5|yaml|yml|toml|"
    r"css|scss|less|pcss|postcss|wxss|graphql|gql|graphqls|html|htm|hta|xhtml|"
    r"component\.html|vue|svelte|hbs|handlebars|mjml)$"
)
assert oxfmt["additional_dependencies"] == ["oxfmt@0.63.0", "svelte@5.56.8"]
assert package["devDependencies"]["svelte"] == "5.56.8"
assert lock["packages"][""]["devDependencies"]["svelte"] == "5.56.8"
assert oxfmt_config["svelte"] is True
assert oxfmt_config["ignorePatterns"] == [
    "test-vault/**", ".kilo/**", "**/*.md", "**/*.markdown", "**/*.mdx"
]
assert settings["[markdown]"]["editor.formatOnSave"] is False
```

Add `OXFMT_EDITOR_LANGUAGE_IDS` to that test module with these exact IDs:

```python
(
    "javascript", "javascriptreact", "typescript", "typescriptreact", "json", "jsonc",
    "json5", "yaml", "toml", "css", "scss", "less", "postcss", "wxss", "graphql",
    "handlebars", "html", "vue", "svelte", "mjml",
)
```

For every ID, assert its language-specific settings object is exactly:

```python
{
    "editor.defaultFormatter": "oxc.oxc-vscode",
    "editor.formatOnSave": True,
}
```

Also assert the npm Dependabot entry ignores `svelte` exactly as follows, alongside the Oxfmt freeze. This prevents a package-only update from desynchronizing the hook and editor:

```python
npm_update = next(
    update for update in dependabot["updates"] if update["package-ecosystem"] == "npm"
)
svelte_ignore = next(
    ignored for ignored in npm_update["ignore"] if ignored["dependency-name"] == "svelte"
)
assert svelte_ignore["update-types"] == [
    "version-update:semver-major",
    "version-update:semver-minor",
    "version-update:semver-patch",
]
```

- [ ] **Step 2: Run the new tests and observe the old narrow policy fail**

Run:

```bash
python -m pytest \
  tests/test_lint_coverage.py::test_oxfmt_covers_every_tracked_supported_non_markdown_file \
  tests/test_node_tooling.py -q
```

Expected: FAIL because the current hook has JavaScript-only `types_or`, the package has no Svelte pin, and the non-JavaScript editor blocks explicitly disable formatting.

- [ ] **Step 3: Install the exact Svelte runtime and update its lockfile**

Run:

```bash
npm install --prefix packages/memoria-obsidian --save-dev --save-exact svelte@5.56.8 --package-lock-only
npm ci --prefix packages/memoria-obsidian
```

Expected: `package.json` and `package-lock.json` contain exact `5.56.8`, and the package-local `node_modules/svelte/compiler` is available to Oxfmt. Do not use a range, `latest`, or a global installation.

- [ ] **Step 4: Replace the narrow config, hook scope, and editor settings with the declared policy**

Set `.oxfmtrc.json` to retain its schema, set `"svelte": true`, and use exactly these ignore patterns:

```json
[
  "test-vault/**",
  ".kilo/**",
  "**/*.md",
  "**/*.markdown",
  "**/*.mdx"
]
```

Replace the Oxfmt hook's old directory-only JavaScript scope with this exact policy:

```yaml
- id: oxfmt
  types_or: [file]
  files: '\.(?:js|mjs|cjs|jsx|ts|mts|cts|tsx|json|jsonc|json5|yaml|yml|toml|css|scss|less|pcss|postcss|wxss|graphql|gql|graphqls|html|htm|hta|xhtml|component\.html|vue|svelte|hbs|handlebars|mjml)$'
  additional_dependencies: [oxfmt@0.63.0, svelte@5.56.8]
  stages: [pre-commit, manual]
```

Keep `pass_filenames` absent so its default remains true. Update the surrounding comment to explain that the hook now owns every listed non-Markdown suffix, uses a suffix regex to avoid unsupported-file failures, and relies on the adapter build to canonicalize generated artifacts.

In `.vscode/settings.json`, replace the existing JavaScript-only Oxc block and the disabled JSON/YAML/TOML/CSS/SCSS blocks with one exact two-key block for every ID in `OXFMT_EDITOR_LANGUAGE_IDS`. Preserve the Python, shell, plaintext, and Markdown blocks; keep the Markdown block's `formatOnSave: false` and explicit markdownlint action.

In `.github/dependabot.yml`, add a `svelte` ignore entry with all three semver update types and explain that Svelte participates in Oxfmt output. Update the existing adapter rebuild comment to say **39** floor goldens, not 38.

Update `tests/test_lint_coverage.py` wording so `.css` and `.toml` remain unclaimed by a syntax linter but are formatted by Oxfmt, and so the generated seed `main.js` exemption applies to Oxlint only rather than claiming formatting would fail.

- [ ] **Step 5: Validate configuration and make the policy tests green before the corpus migration**

Run:

```bash
pre-commit validate-config
python -m json.tool .oxfmtrc.json >/dev/null
python -m json.tool .vscode/settings.json >/dev/null
npm run check --prefix packages/memoria-obsidian
python -m pytest tests/test_lint_coverage.py tests/test_node_tooling.py -q
```

Expected: configuration parsing and focused tests pass. At this point `pre-commit run oxfmt --hook-stage manual --all-files` is expected to report the unformatted migration corpus; do not treat that expected drift as an ignored failure.

- [ ] **Step 6: Measure, preserve semantic evidence, and format every tracked non-Markdown input**

Create an exact candidate list from the same suffixes the hook declares, then measure it before writing:

```bash
mapfile -t oxfmt_paths < <(
  git ls-files | rg '\.(js|mjs|cjs|jsx|ts|mts|cts|tsx|json|jsonc|json5|yaml|yml|toml|css|scss|less|pcss|postcss|wxss|graphql|gql|graphqls|html|htm|hta|xhtml|component\.html|vue|svelte|hbs|handlebars|mjml)$'
)
packages/memoria-obsidian/node_modules/.bin/oxfmt --check --list-different "${oxfmt_paths[@]}"
```

Expected: 174 candidates and 25 changed files: 17 YAML, 6 JSON, 1 TOML, and 1 CSS. Task 1 already canonicalized the generated JavaScript and seeded CSS; the final branch migration still contains the original 27-file total.

Before formatting, save every changed YAML, JSON, and TOML file into a temporary directory. Format the full candidate list, then compare each saved/current pair with its parser:

```bash
before_dir=$(mktemp -d)
mapfile -t changed_paths < <(
  packages/memoria-obsidian/node_modules/.bin/oxfmt --check --list-different "${oxfmt_paths[@]}" || true
)
for path in "${changed_paths[@]}"; do
  case "$path" in
    *.yaml|*.yml|*.json|*.toml)
      mkdir -p "$before_dir/$(dirname "$path")"
      cp "$path" "$before_dir/$path"
      ;;
  esac
done
packages/memoria-obsidian/node_modules/.bin/oxfmt --write "${oxfmt_paths[@]}"
```

Run this semantic comparison after formatting:

```bash
python - "$before_dir" "${changed_paths[@]}" <<'PY'
from __future__ import annotations

import json
import sys
import tomllib
from pathlib import Path

import yaml

before = Path(sys.argv[1])
for value in sys.argv[2:]:
    path = Path(value)
    prior = before / path
    if not prior.exists():
        continue
    if path.suffix in {".yaml", ".yml"}:
        load = lambda item: yaml.safe_load(item.read_text(encoding="utf-8"))
    elif path.suffix == ".json":
        load = lambda item: json.loads(item.read_text(encoding="utf-8"))
    elif path.suffix == ".toml":
        load = lambda item: tomllib.loads(item.read_text(encoding="utf-8"))
    else:
        continue
    assert load(prior) == load(path), path
    print(f"semantic values preserved: {path}")
PY
```

Expected: every preserved structured file reports equal parsed values. Inspect the 1,284-line Vale vendor indentation rewrite as a vendor formatting change, not a rule-content change.

- [ ] **Step 7: Rebuild seed output and update the second digest migration**

Run:

```bash
npm run build --prefix packages/memoria-obsidian
npm run check --prefix packages/memoria-obsidian
MEMORIA_FLOOR_UPDATE_GOLDENS=1 python -m pytest tests/test_floor_sweep_operations.py -q
python -m pytest tests/test_floor_sweep_operations.py -q
```

Expected: both package commands and both floor invocations pass. Relative to Task 1's committed baseline, the 39 golden diffs may now change only hashes for these two newly formatted seeded JSON files:

```text
src/memoria_vault/product/workspace_seed/.codex/hooks.json
src/memoria_vault/product/workspace_seed/.obsidian/community-plugins.json
```

If any golden changes another path, stop and diagnose rather than accepting the update.

- [ ] **Step 8: Prove all configured gates are clean and commit the policy plus migration**

Run:

```bash
pre-commit run oxfmt --hook-stage manual --all-files
pre-commit run vale --hook-stage manual --all-files
pre-commit run yamllint --hook-stage manual --all-files
python -m pytest \
  tests/test_lint_coverage.py \
  tests/test_node_tooling.py \
  tests/test_memoria_obsidian_package.py \
  tests/test_agent_bundle.py \
  tests/test_floor_sweep_operations.py -q
git diff --check
```

Expected: every command passes. Stage only the named policy, package, test, current corpus, seeded artifact, and floor-golden paths from this task; then commit:

```bash
git commit -m "style: format all supported non-Markdown files with Oxfmt"
```

## Final verification and record retirement

After both task reviews and the required final branch review report no Critical or Important findings, run the full gate once against the final worktree:

```bash
python scripts/verify
```

Expected: `verify: OK`. Then confirm `git status --short` contains no unrelated changes and delete exactly these completed working records with `apply_patch`:

```text
docs/superpowers/specs/2026-08-13-oxfmt-all-non-markdown-design.md
docs/superpowers/plans/2026-08-13-oxfmt-all-non-markdown.md
```

Do not edit their status text before deleting them. Run these checks, stage those two explicit deletions, and commit:

```bash
git diff --check
pre-commit run cspell --hook-stage manual --all-files
```

```bash
git commit -m "docs: retire completed Oxfmt planning records"
```

The Git history is the archive. Do not move either record into published docs or frozen design history.
