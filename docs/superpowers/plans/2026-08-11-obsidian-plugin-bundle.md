# Obsidian Plugin Bundle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a single-file CommonJS Memoria Obsidian plugin that desktop Obsidian can load, with a build and regression contract that prevents a local `require("./…")` from returning.

**Architecture:** Make `packages/memoria-obsidian/` the only authored plugin source: its `src/` modules compile with esbuild into the package seed's generated `main.js`. The seed, runtime bundle writer, provenance doctor, and initialized vaults carry exactly `main.js`, `manifest.json`, and `styles.css`. Tests exercise package source for behavior and the emitted entrypoint in a directory that contains no helper modules.

**Tech Stack:** Node 22, esbuild, CommonJS, native Node test runner, pytest, Python package resources, GitHub Actions, Dependabot.

## Global Constraints

- Keep the plugin entrypoint CommonJS; bundle local modules, leave `obsidian` external, and leave Node built-ins such as `child_process` external through esbuild's `platform: "node"` behavior.
- Use an exact, package-local esbuild development dependency with a committed `packages/memoria-obsidian/package-lock.json`. Never add a root `node_modules` install or root npm dependency.
- `packages/memoria-obsidian/src/` is the sole authored JavaScript source. The workspace seed's plugin directory is a generated release artifact with exactly `main.js`, `manifest.json`, and `styles.css`.
- Preserve current plugin behavior, the manifest contract, token handling, and the no-Memoria-owned-vault-write policy. Do not migrate or modify an existing vault automatically.
- Run plugin tests under Node 22. Use `npm ci --prefix packages/memoria-obsidian` before commands that invoke esbuild.
- Test initialized vaults only through pytest `tmp_path` or other disposable paths; do not alter `test-vault/u3-plug-manual`.
- The human wizard must display `memoria init --workspace test-vault/u3-plug-manual --yes`, never the obsolete positional form.
- Keep the known local MCP environment mismatch out of this change; CI's required `verify` and `gitleaks` remain merge evidence.

## File Map

| Area | Responsibility after this plan |
| --- | --- |
| `packages/memoria-obsidian/src/` | Canonical `main.js` plus `schema.js`, `relate.js`, `handshake.js`, `pill.js`, and `viewspec.js` helper modules. |
| `packages/memoria-obsidian/scripts/build.mjs` | Deterministically bundle canonical source and synchronize or check the three committed release artifacts. |
| `src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/` | Generated plugin payload consumed by package resources and `memoria init`. |
| `src/memoria_vault/runtime/bundles.py` | Copy exactly the three generated plugin artifacts into a new vault and record their hashes. |
| `tests/test_memoria_obsidian_package.py` | Separate source-level behavior checks from a single-artifact host-loader regression proof. |
| CI, bootstrap, and contributor docs | Install and maintain the package-local build dependency without weakening the root no-node-dependency boundary. |

---

### Task 1: Establish the canonical source, generated artifact, and three-file runtime bundle

**Files:**

- Create: `packages/memoria-obsidian/src/main.js`
- Create: `packages/memoria-obsidian/src/schema.js`
- Create: `packages/memoria-obsidian/src/relate.js`
- Create: `packages/memoria-obsidian/src/handshake.js`
- Create: `packages/memoria-obsidian/src/pill.js`
- Create: `packages/memoria-obsidian/src/viewspec.js`
- Create: `packages/memoria-obsidian/manifest.json`
- Create: `packages/memoria-obsidian/styles.css`
- Create: `packages/memoria-obsidian/scripts/build.mjs`
- Create: `packages/memoria-obsidian/package-lock.json`
- Modify: `packages/memoria-obsidian/package.json`
- Modify: `packages/memoria-obsidian/scripts/test.mjs`
- Modify: `packages/memoria-obsidian/scripts/test-handshake.mjs`
- Modify: `packages/memoria-obsidian/scripts/test-pill.mjs`
- Modify: `packages/memoria-obsidian/scripts/test-relate.mjs`
- Modify: `packages/memoria-obsidian/scripts/test-viewspec.mjs`
- Modify: `src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/main.js`
- Modify: `src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/manifest.json`
- Modify: `src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/styles.css`
- Delete: `src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/schema.js`
- Delete: `src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/relate.js`
- Delete: `src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/handshake.js`
- Delete: `src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/pill.js`
- Delete: `src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/viewspec.js`
- Modify: `src/memoria_vault/runtime/bundles.py`
- Modify: `scripts/checks/plugin_provenance_doctor.py`
- Modify: `tests/test_memoria_obsidian_package.py`
- Modify: `tests/test_plugin_provenance.py`
- Modify: `tests/test_attention_view.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_installer_skeleton.py`
- Modify: `tests/test_package_spine.py`
- Modify: `tests/test_agent_bundle.py`
- Modify: `scripts/test_vault/e2e_smoke.py`
- Modify: `.gitignore`
- Modify (generated): all 38 tracked `tests/fixtures/floor/goldens/*.json` files.

**Interfaces:**

- Consumes: `esbuild.build(options)`; `seed_bundles(workspace, bundle_names=["obsidian"])`; package-resource paths declared by `BUNDLE_FILES["obsidian"]`.
- Produces: `npm run build --prefix packages/memoria-obsidian`, `npm run check --prefix packages/memoria-obsidian`, and `npm test --prefix packages/memoria-obsidian`; `BUNDLE_FILES["obsidian"] == (".obsidian/plugins/memoria-obsidian/main.js", ".obsidian/plugins/memoria-obsidian/manifest.json", ".obsidian/plugins/memoria-obsidian/styles.css")`; a seeded `main.js` that can load and complete `await new PluginClass().onload()` without sibling JavaScript files.

- [ ] **Step 1: Record the source and package-test baseline before changing the boundary**

Run:

~~~bash
git status --short
node --version
npm test --prefix packages/memoria-obsidian
python -m pytest \
  tests/test_memoria_obsidian_package.py \
  tests/test_plugin_provenance.py \
  tests/test_attention_view.py \
  tests/test_cli.py \
  tests/test_installer_skeleton.py \
  tests/test_package_spine.py \
  tests/test_agent_bundle.py -q
~~~

Expected: the worktree is clean, the selected Node major is 22, and the existing focused suite is green. If the shell selects another Node major, activate the repository's Node 22 toolchain before continuing; do not change the discovery-floor assertion to accommodate a different reporter.

- [ ] **Step 2: Write the failing source/artifact boundary tests**

In `tests/test_memoria_obsidian_package.py`, replace the seed-as-source constants with an explicit canonical-source and release-artifact contract:

~~~python
PLUGIN = ROOT / "packages" / "memoria-obsidian"
SOURCE = PLUGIN / "src"
SEED_PLUGIN = ROOT / (
    "src/memoria_vault/product/workspace_seed/"
    ".obsidian/plugins/memoria-obsidian"
)
SOURCE_MODULES = (
    "handshake.js",
    "main.js",
    "pill.js",
    "relate.js",
    "schema.js",
    "viewspec.js",
)
RELEASE_ARTIFACTS = ("main.js", "manifest.json", "styles.css")
~~~

Make every static behavior, command, schema, and color assertion read `SOURCE` (and package-root `styles.css` / `manifest.json`) rather than helper files in `SEED_PLUGIN`. Assert the seed directory's direct file roster equals `RELEASE_ARTIFACTS`, and add a test which runs `npm run check` and fails if the committed output is stale.

Replace the ordinary whole-directory Node load probe with an isolated release-artifact probe. It must:

1. call `seed_bundles` into `tmp_path / "vault"`;
2. assert that the resulting plugin directory contains exactly the three release artifacts;
3. leave the directory as-is (do not copy or create a sibling helper);
4. stub only `obsidian` using `Module._load`;
5. require its `main.js`, assert it exports a constructor, instantiate it, and await `onload()`; and
6. assert the emitted bytes contain no `require("./` substring.

Use a minimal host stub that supplies exactly the `onload()` seam:

~~~javascript
class Plugin {
  constructor() {
    this.app = {
      vault: { adapter: { basePath: "/tmp/memoria-plugin-test" } },
      workspace: { onLayoutReady() {} },
    };
  }
  async loadData() { return null; }
  addStatusBarItem() {
    return { empty() {}, createEl() { return {}; }, setText() {} };
  }
  addSettingTab() {}
  addCommand() {}
  register() {}
  registerView() {}
}
~~~

Return that class, inert classes for `AbstractInputSuggest`, `ItemView`, `Modal`, `Notice`, `PluginSettingTab`, and `Setting`, plus an inert `requestUrl` from the `obsidian` stub. Do not stub local paths: their absence is the regression proof.

Update the release-roster assertions in `tests/test_cli.py`, `tests/test_installer_skeleton.py`, `tests/test_package_spine.py`, `scripts/test_vault/e2e_smoke.py`, and `tests/test_agent_bundle.py` to name only the three artifacts. Point `tests/test_attention_view.py` at `packages/memoria-obsidian/src/{viewspec,relate}.js`. Add a direct `tests/test_plugin_provenance.py` equality assertion for the full allowlist so a retired helper cannot remain accidentally permitted.

- [ ] **Step 3: Run the new tests to confirm the current layout fails for the intended reasons**

Run:

~~~bash
python -m pytest \
  tests/test_memoria_obsidian_package.py \
  tests/test_plugin_provenance.py \
  tests/test_attention_view.py \
  tests/test_cli.py \
  tests/test_installer_skeleton.py \
  tests/test_package_spine.py \
  tests/test_agent_bundle.py -q
~~~

Expected: FAIL because `packages/memoria-obsidian/src/` and the build/check scripts do not exist, and because the old seed/runtime rosters still name five helper artifacts. The failure must not be accepted for a Node reporter-count mismatch; use Node 22 for this step.

- [ ] **Step 4: Move the authored inputs and define the package command contract**

Move, rather than copy, the six authored JavaScript modules from the seed to `packages/memoria-obsidian/src/`. Move `manifest.json` and `styles.css` to the package root. Preserve source bytes while moving the modules; the only intentional source comment change is to replace the stale `hand-authored (no build step)` statement with a statement that `main.js` is the esbuild entrypoint.

Use these path-preserving moves:

~~~bash
mkdir -p packages/memoria-obsidian/src
git mv src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/main.js packages/memoria-obsidian/src/main.js
git mv src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/schema.js packages/memoria-obsidian/src/schema.js
git mv src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/relate.js packages/memoria-obsidian/src/relate.js
git mv src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/handshake.js packages/memoria-obsidian/src/handshake.js
git mv src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/pill.js packages/memoria-obsidian/src/pill.js
git mv src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/viewspec.js packages/memoria-obsidian/src/viewspec.js
git mv src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/manifest.json packages/memoria-obsidian/manifest.json
git mv src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/styles.css packages/memoria-obsidian/styles.css
~~~

Set the package scripts to these exact command strings and add only an exact-pinned `esbuild` development dependency:

~~~json
"scripts": {
  "build": "node scripts/build.mjs",
  "check": "node scripts/build.mjs --check",
  "test": "node --test"
}
~~~

Before the package install creates its local dependency tree, add
`packages/memoria-obsidian/node_modules/` to `.gitignore`; that keeps the
package-local build dependency out of both this commit and future source diffs.

Generate and commit the lockfile with:

~~~bash
npm install --prefix packages/memoria-obsidian --save-dev --save-exact esbuild
~~~

Retarget each Node source test to its canonical package path. For example:

~~~javascript
const { sanitizeItemId, validateEvent } = require("../src/schema.js");
const PluginClass = require("../src/main.js");
~~~

Use the corresponding `../src/handshake.js`, `../src/pill.js`, `../src/relate.js`, and `../src/viewspec.js` imports in the four helper suites.

- [ ] **Step 5: Implement the deterministic esbuild artifact writer and drift checker**

Create `packages/memoria-obsidian/scripts/build.mjs`. It accepts no argument or exactly `--check`; reject every other argument. Its emitted contract is:

~~~javascript
const bundled = await build({
  entryPoints: [resolve(sourceDir, "main.js")],
  outfile: resolve(seedDir, "main.js"),
  bundle: true,
  format: "cjs",
  platform: "node",
  external: ["obsidian"],
  write: false,
  logLevel: "silent",
});

const expected = new Map([
  ["main.js", bundled.outputFiles[0].contents],
  ["manifest.json", await readFile(resolve(packageDir, "manifest.json"))],
  ["styles.css", await readFile(resolve(packageDir, "styles.css"))],
]);
~~~

Resolve `packageDir` from `import.meta.url`, resolve `sourceDir` as `packageDir/src`, and resolve `seedDir` as the repository workspace-seed plugin directory. Compare every expected byte sequence against its seed target and also compare the seed directory's file names against `expected`.

For `--check`, report every missing, byte-different, or unexpected artifact and exit nonzero without writing. For the normal build, create `seedDir`, write the three expected byte sequences, and remove only the stale artifacts in that generated directory so the final file roster is exact. This writer owns the whole generated plugin directory; it must never copy helper modules beside the bundle.

After the build script exists, run:

~~~bash
npm run build --prefix packages/memoria-obsidian
~~~

Expected: the seed now has a generated `main.js`, byte-identical copied `manifest.json` and `styles.css`, and no `schema.js`, `relate.js`, `handshake.js`, `pill.js`, or `viewspec.js`.

- [ ] **Step 6: Wire the release roster through package resources and all static consumers**

Set `BUNDLE_FILES["obsidian"]` in `src/memoria_vault/runtime/bundles.py` to this exact tuple and revise its comment to describe one bundled entrypoint:

~~~python
(
    ".obsidian/plugins/memoria-obsidian/main.js",
    ".obsidian/plugins/memoria-obsidian/manifest.json",
    ".obsidian/plugins/memoria-obsidian/styles.css",
)
~~~

Reduce `ALLOWED_SEED_OBSIDIAN_FILES` in `scripts/checks/plugin_provenance_doctor.py` to the same three plugin paths plus the existing top-level Obsidian preference files. Update comments and test prose so they call the three files generated release artifacts, not hand-authored seed modules.

In `tests/test_memoria_obsidian_package.py`, retain the full normal Node behavior suite against source, but use the isolated emitted-artifact probe for the host-loader contract. The normal test must continue to assert the `NODE_SUITE_FILES` roster and its Node-22 test count. The source color sweep must scan all six `SOURCE_MODULES` plus package-root `styles.css`; the package release-roster assertion must scan only `RELEASE_ARTIFACTS`.

- [ ] **Step 7: Regenerate only the affected floor fixtures and verify the complete atomic boundary**

First inspect which package-resource hashes will change:

~~~bash
MEMORIA_FLOOR_UPDATE_GOLDENS=1 \
  python -m pytest tests/test_floor_sweep_operations.py -q
git diff --check
git diff -- tests/fixtures/floor/goldens
~~~

Expected: the 38 existing golden files change only because their seed file digests lose the five helper paths and gain the generated `main.js` digest. Do not add or remove a golden file and do not accept unrelated operation-state changes.

Then rerun the exact checks without the update environment:

~~~bash
npm ci --prefix packages/memoria-obsidian
npm run build --prefix packages/memoria-obsidian
npm run check --prefix packages/memoria-obsidian
npm test --prefix packages/memoria-obsidian
python -m pytest \
  tests/test_memoria_obsidian_package.py \
  tests/test_plugin_provenance.py \
  tests/test_attention_view.py \
  tests/test_cli.py \
  tests/test_installer_skeleton.py \
  tests/test_package_spine.py \
  tests/test_agent_bundle.py -q
python -m pytest tests/test_floor_sweep_operations.py -q
~~~

Expected: all commands pass. In particular, the isolated loader must execute `onload()` with no sibling helper files present, and `npm run check` must report no stale artifact.

- [ ] **Step 8: Commit the atomic source/artifact boundary**

~~~bash
git add \
  packages/memoria-obsidian/package.json \
  packages/memoria-obsidian/package-lock.json \
  packages/memoria-obsidian/manifest.json \
  packages/memoria-obsidian/styles.css \
  packages/memoria-obsidian/src \
  packages/memoria-obsidian/scripts \
  src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian \
  src/memoria_vault/runtime/bundles.py \
  scripts/checks/plugin_provenance_doctor.py \
  scripts/test_vault/e2e_smoke.py \
  tests/test_memoria_obsidian_package.py \
  tests/test_plugin_provenance.py \
  tests/test_attention_view.py \
  tests/test_cli.py \
  tests/test_installer_skeleton.py \
  tests/test_package_spine.py \
  tests/test_agent_bundle.py \
  .gitignore \
  tests/fixtures/floor/goldens
git commit -m "fix(plugin): bundle Obsidian entrypoint"
~~~

Expected: the commit contains only the canonical-source, generated-artifact, runtime-roster, regression-test, and golden changes named above.

### Task 2: Make the package-local build reproducible for contributors and CI

**Files:**

- Modify: `.github/workflows/verify.yml`
- Modify: `.github/dependabot.yml`
- Modify: `scripts/dev/setup.sh`
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `docs/explanation/rationale/deployment/distribution-model.md`
- Modify: `docs/reference/evidence-and-integrations/integrations.md`
- Modify: `tests/test_node_tooling.py`
- Modify: `tests/test_dev_setup.py`

**Interfaces:**

- Consumes: the Task 1 `package-lock.json` and the commands `npm ci --prefix packages/memoria-obsidian` and `npm run check --prefix packages/memoria-obsidian`.
- Produces: a verify workflow that installs the adapter build dependency before `python scripts/verify`; a bootstrap script and contributor docs that teach only the package-local install; Dependabot coverage for `/packages/memoria-obsidian`.

- [ ] **Step 1: Verify the completed bundle before changing developer plumbing**

Run:

~~~bash
npm ci --prefix packages/memoria-obsidian
npm run check --prefix packages/memoria-obsidian
python -m pytest tests/test_memoria_obsidian_package.py -q
~~~

Expected: all three commands pass from a fresh package-local dependency install.

- [ ] **Step 2: Add failing static contracts for the local dependency and automation**

Extend `tests/test_node_tooling.py` with a plugin-package contract that reads `packages/memoria-obsidian/package.json` and its lockfile. It must assert:

~~~python
assert package["scripts"]["build"] == "node scripts/build.mjs"
assert package["scripts"]["check"] == "node scripts/build.mjs --check"
assert RELEASE_TAG.fullmatch(package["devDependencies"]["esbuild"])
assert lock["packages"][""]["devDependencies"]["esbuild"] == package["devDependencies"]["esbuild"]
~~~

Also load `.github/workflows/verify.yml` and `.github/dependabot.yml` with the already-imported YAML parser and assert the former contains a dedicated `npm ci --prefix packages/memoria-obsidian` step before `python scripts/verify`, while the latter has exactly one `npm` ecosystem entry with `directory: "/packages/memoria-obsidian"`.

Extend `tests/test_dev_setup.py` to require the bootstrap script's package-local `npm ci` attempt, its success message, its actionable Node/npm-missing message, and contributor prose stating that root `npm ci` remains inappropriate.

- [ ] **Step 3: Run the new static tests and confirm missing plumbing is visible**

Run:

~~~bash
python -m pytest tests/test_node_tooling.py tests/test_dev_setup.py -q
~~~

Expected: FAIL because neither CI nor `scripts/dev/setup.sh` yet installs the plugin package, Dependabot has no npm entry, and the contributor guidance does not distinguish the package-local install from the root boundary.

- [ ] **Step 4: Implement package-local installation and accurate ownership documentation**

In `.github/workflows/verify.yml`, add an `Install Obsidian adapter build dependency` step after Node setup and before `Run verify`:

~~~yaml
- name: Install Obsidian adapter build dependency
  run: npm ci --prefix packages/memoria-obsidian
~~~

In `scripts/dev/setup.sh`, add a non-product bootstrap section after the Python tooling section. When `npm` exists, run `npm ci --prefix packages/memoria-obsidian`; report success with a package-local message and report failure with the exact manual command. When `npm` is absent, report that Node 22/npm is needed for the adapter build. Keep the script's existing best-effort contributor-tooling behavior and do not install a vault runtime.

Add `packages/memoria-obsidian/node_modules/` to `.gitignore`. Add a monthly Dependabot `npm` entry for `/packages/memoria-obsidian` using the existing `chore` prefix and a single `adapter-build` group.

In `CONTRIBUTING.md` and `README.md`, retain the statement that prose tooling needs no root `node_modules`, then state that adapter development runs:

~~~bash
npm ci --prefix packages/memoria-obsidian
npm run check --prefix packages/memoria-obsidian
~~~

Update the deployment rationale and integrations reference so they state that `packages/memoria-obsidian/` owns adapter source, manifest, stylesheet, tests, and the build; the Python workspace seed owns only the committed generated three-file release artifact. Change the Mermaid adapter node and edge to show the package source builds the seed, rather than saying the source lives in the seed.

- [ ] **Step 5: Verify the contributor and CI contracts**

Run:

~~~bash
python -m pytest tests/test_node_tooling.py tests/test_dev_setup.py -q
npm ci --prefix packages/memoria-obsidian
npm run check --prefix packages/memoria-obsidian
git diff --check
~~~

Expected: all commands pass, the root `package.json` remains dependency-free, and the updated text never instructs a root `npm ci` for adapter work.

- [ ] **Step 6: Commit the reproducible build plumbing**

~~~bash
git add \
  .github/workflows/verify.yml \
  .github/dependabot.yml \
  .gitignore \
  scripts/dev/setup.sh \
  README.md \
  CONTRIBUTING.md \
  docs/explanation/rationale/deployment/distribution-model.md \
  docs/reference/evidence-and-integrations/integrations.md \
  tests/test_node_tooling.py \
  tests/test_dev_setup.py
git commit -m "build: provision Obsidian bundle tooling"
~~~

Expected: the commit contains only dependency-install, maintenance, documentation, and their static-contract changes.

### Task 3: Correct the human acceptance wizard's initialization command

**Files:**

- Modify: `scripts/human-acceptance-wizard.sh:254`
- Modify: `tests/test_human_acceptance_wizard.py`

**Interfaces:**

- Consumes: the CLI's `init` parser, whose workspace target is the optional `--workspace` flag and whose noninteractive confirmation is `--yes`.
- Produces: the plugin-stage displayed command `memoria init --workspace test-vault/u3-plug-manual --yes`, which a human can paste to recreate the disposable vault before opening it in desktop Obsidian.

- [ ] **Step 1: Check the current wizard syntax and static contract**

Run:

~~~bash
bash -n scripts/human-acceptance-wizard.sh
python -m pytest tests/test_human_acceptance_wizard.py -q
~~~

Expected: both pass, demonstrating that the existing tests do not yet pin the bad positional invocation.

- [ ] **Step 2: Add a failing assertion for the exact displayed initialization command**

Add a static test that isolates the plugin section between `if include_section plugin; then` and `if include_section canvas; then` and asserts:

~~~python
assert 'show_command "memoria init --workspace test-vault/u3-plug-manual --yes"' in plugin_section
assert 'show_command "memoria init test-vault/u3-plug-manual"' not in plugin_section
~~~

- [ ] **Step 3: Run the targeted test to prove the CLI contract regression is red**

Run:

~~~bash
python -m pytest tests/test_human_acceptance_wizard.py -q
~~~

Expected: FAIL only at the new command assertion because the wizard still displays a positional target.

- [ ] **Step 4: Replace the displayed command without changing the human-only safety flow**

At the `Open the disposable plugin vault` stage, replace only:

~~~bash
show_command "memoria init test-vault/u3-plug-manual"
~~~

with:

~~~bash
show_command "memoria init --workspace test-vault/u3-plug-manual --yes"
~~~

Leave the desktop interaction, token probe, confirmation gates, and cleanup display unchanged.

- [ ] **Step 5: Verify the shell and test contract**

Run:

~~~bash
bash -n scripts/human-acceptance-wizard.sh
shellcheck scripts/human-acceptance-wizard.sh
python -m pytest tests/test_human_acceptance_wizard.py -q
scripts/human-acceptance-wizard.sh --help
~~~

Expected: syntax, ShellCheck, and pytest pass; `--help` exits successfully without asking for input.

- [ ] **Step 6: Commit the wizard correction**

~~~bash
git add scripts/human-acceptance-wizard.sh tests/test_human_acceptance_wizard.py
git commit -m "fix(wizard): use init workspace flag"
~~~

Expected: the commit contains the one displayed command correction and its regression test.

### Task 4: Run the repository gate and prepare the reviewed branch

**Files:**

- Modify: none expected.
- Test: the committed changes from Tasks 1–3.

**Interfaces:**

- Consumes: the package-local dependency install, the generated release artifact, source/runtime contract tests, and the complete repository verifier.
- Produces: evidence suitable for a pull request: a clean branch, a passing `python scripts/verify` result, and a diff that contains no accidental editable vault content.

- [ ] **Step 1: Recheck the generated artifact before the repository gate**

Run:

~~~bash
npm ci --prefix packages/memoria-obsidian
npm run check --prefix packages/memoria-obsidian
git status --short
~~~

Expected: the artifact check passes and `git status --short` contains only committed work or intentionally untracked, ignored disposable-vault files; it must not contain package-local `node_modules`.

- [ ] **Step 2: Run the approved manual Obsidian acceptance**

Ask the project owner to run the already-approved human acceptance only after
the emitted artifact check is green. They must recreate their own disposable
plugin vault with:

~~~bash
memoria init --workspace test-vault/u3-plug-manual --yes
scripts/human-acceptance-wizard.sh --section plugin
~~~

They then open that newly initialized vault in desktop Obsidian 1.12, accept
the ordinary trust and community-plugin prompts, and record whether Memoria
loads without `Cannot find module './schema'` before continuing to the
connection checks. Do not automate Obsidian, delete the disposable vault, or
ask for any token; a failed or blocked manual check is evidence to record, not
a reason to weaken the isolated-loader test.

- [ ] **Step 3: Run the full verification gate**

Run:

~~~bash
python scripts/verify
~~~

Expected: PASS. If the known local MCP environment mismatch prevents the full local gate, capture its exact pre-existing failure separately and do not weaken source, test, or CI contracts; all focused plugin, build, wizard, and static checks above must still be green.

- [ ] **Step 4: Inspect the final diff and branch state**

Run:

~~~bash
git diff origin/main...HEAD --check
git diff --stat origin/main...HEAD
git status --short
~~~

Expected: no whitespace errors, only the planned plugin/source/seed/test/CI/docs/wizard changes, and a clean worktree apart from ignored package-local dependencies.

- [ ] **Step 5: Request code review and use the normal PR gate**

Use `superpowers:requesting-code-review` on the committed branch, address any validated findings, rerun the relevant checks, then follow `superpowers:finishing-a-development-branch` to rebase on current `origin/main`, push the branch, open a PR, and merge by squash only after required `verify` and `gitleaks` checks pass.
