# ExecPlan — Hermetic developer toolchain (pre-commit-managed lint versions + declarative runtimes)

## 0. Metadata

- **Task:** Make the local pre-commit toolchain and CI run the *same pinned versions* by construction, so "green locally" implies "green in CI", and a fresh clone reaches a working state with one command — closing the version-drift class that produced a run of avoidable failures.
- **Worktree / branch:**
  - Layer 1 implementation → `~/memoria-vault/worktrees/precommit-managed-hooks` · `feat/precommit-managed-hooks`
  - Layer 2 implementation → `~/memoria-vault/worktrees/mise-runtimes` · `feat/mise-runtimes`
  - This plan file → `scratch/workflow-audit/exec-plan-hermetic-dev-toolchain.md`, pushed to `origin/scratch`
- **Decision record:** `scratch/releases/0.1.0-beta.1/decisions.md` —
  *Pinned pre-commit environments define third-party lint tools*. ADR-131 was not
  created because PR #1273 retired `docs/adr/` as the live decision mechanism.
- **Related issues / milestone:** no separate implementation issue was created;
  PR #1273 completed the repo-owned implementation and routed the durable
  decision to the beta.1 release ledger.
- **Started:** 2026-07-05 · **Last updated:** 2026-07-06

## 1. Purpose / big picture

Contributors run quality gates twice: locally via **pre-commit** (a git-hook framework that runs linters on `git commit`) and again in **CI** (GitHub Actions on every PR). At plan start, those two paths shared only *version numbers written in text files* — they executed the tools through entirely different mechanisms and, critically, the local hooks resolved each tool from the developer's ambient `PATH`. On a real machine that `PATH` is a jumble (conda base, `~/.local/bin` standalone binaries, global npm, Windows npm via WSL interop), so the version that actually ran locally was whatever happened to be first — not the pin. When it disagreed with CI, the contributor discovered it only after pushing.

This work makes version parity **structural instead of conventional**: pre-commit owns the pinned lint-tool versions in isolated per-hook environments, CI runs those *same* hooks, and the language runtimes (Python, Node) are pinned declaratively so the ambient `PATH` stops mattering. After it lands, a fresh clone runs one setup command and gets byte-identical tool behavior to CI; a wrong tool on `PATH` can no longer shadow a pinned one; and a missing tool (e.g. gitleaks) or an under-version runtime (Node < 22) fails **loudly and actionably** instead of silently skipping or emitting a cryptic error.

Observable end states (each proven in §5): `pre-commit run --all-files` uses the pinned versions regardless of `PATH`; every required CI check runs the identical hook; a clean clone + `mise install && pre-commit install --install-hooks` reproduces the toolchain; `scripts/dev/setup.sh` hard-fails on Node < 22.

## 2. Context and orientation

Assume no prior exposure to this repo. Terms are defined on first use.

**Repository & working layout** (from `AGENTS.md` §"Where things live"): the project container is `~/memoria-vault`. Durable source is the `main` checkout at `~/memoria-vault/main`. Task work happens in a **git worktree** (a second working directory backed by the same repository, with its own branch and index) under `~/memoria-vault/worktrees/<name>`. This plan file lives on the **scratch branch** — an orphan branch whose tracked tree holds only scratch-only roots (`releases/`, `workflow-audit/`, …), checked out at the locked linked worktree `~/memoria-vault/scratch`. Never edit repo source from the scratch worktree.

**Baseline quality gate before PR #1273** (verified 2026-07-05 against `main`):

- **`.pre-commit-config.yaml`** — every hook is `language: system`, meaning pre-commit does *not* manage the tool; it runs whatever the entry command resolves to on `PATH`. The lint hooks are:
  - `gitleaks` → `gitleaks protect --staged --redact --verbose` (secret scanner; `always_run`)
  - `ruff` → `ruff check --force-exclude` and `ruff-format` → `ruff format --force-exclude` (Python linter/formatter)
  - `yamllint` → `yamllint`
  - `shellcheck` → `shellcheck --severity=warning` (files: `scripts/install.sh`, `scripts/install/*.sh`)
  - Node prose tools `cspell` and `markdownlint` run via `bash -lc 'PATH=node_modules/.bin:$PATH cspell …'` — i.e. they are **already** pinned to the repo-local `node_modules/.bin` (installed by `npm ci` from `package.json` + `package-lock.json`). These are *not* part of the drift problem; only bare interactive calls can shadow them, which never touches a gate.
  - The first-party "doctors" (`scripts/checks/docs_doctor.py`, `agents_doctor.py`, `status_doctor.py`, `github_doctor.py`, `ruleset_doctor.py`, `gen_adr_index.py`, `plugin_provenance_doctor.py`, …) are repo Python scripts, correctly `language: system`; they are **out of scope** — they are not third-party tools with an upstream pin.
- **Version pins** live in two files:
  - `requirements-dev.txt`: `pre-commit==4.6.0`, `pre-commit-hooks==6.0.0`, `pytest==9.1.1`, `PyYAML==6.0.3`, `ruff==0.15.20`, `shellcheck-py==0.11.0.1`, `yamllint==1.38.0`.
  - `package.json` devDependencies: `cspell 8.19.4` at plan start (PR #1272 later bumped it to `10.0.1`), `markdownlint-cli 0.49.0`. `engines.node: ">=22"`.
- **CI (`.github/workflows/`)** runs the tools through *three different mechanisms*, none of which is pre-commit:
  - `lint.yml` → job **`lint`** (a **required** check): `actions/setup-python@… 3.12` → `pip install -r requirements-dev.txt` → `python scripts/verify l0`. Ruff runs *inside* the l0 gate, from the pip-installed `ruff==0.15.20`. The l0 gate also runs the doctors + drift + syntax checks, so `lint` is much more than ruff.
  - `lint-installers.yml` → job **`shellcheck (scripts/install.sh)`** (**required**) uses the third-party GitHub Action `ludeeus/action-shellcheck` — which bundles *its own* shellcheck build, unrelated to the `shellcheck-py==0.11.0.1` pin. Job **`PSScriptAnalyzer (scripts/install.ps1)`** (**required**) runs `Invoke-ScriptAnalyzer` under `pwsh`.
  - `gitleaks.yml` → job **`gitleaks`** (**NOT** in the required roster) runs `docker run … ghcr.io/gitleaks/gitleaks:v8.30.1 detect …` with **`continue-on-error: true`** — i.e. CI gitleaks is *advisory and non-blocking*. The only enforcing secret-scan on the pre-merge path is therefore the *local* pre-commit `gitleaks` hook.
- **Required-check roster** is owned by `.github/ruleset-contract.yaml` and guarded by `scripts/checks/ruleset_doctor.py`; it is mirrored (drift-checked) in `AGENTS.md` §"Required CI checks". The required checks are exactly: `pr-policy`, `lint`, `shellcheck (scripts/install.sh)`, `PSScriptAnalyzer (scripts/install.ps1)`, `python-selftest`, `cspell`, `lint-config`, `markdownlint`. **Any change to a required-check job name changes this contract** and must update `ruleset-contract.yaml`, the live GitHub ruleset, and the `AGENTS.md` mirror together.
- **Runtimes.** Node comes from the **NodeSource** apt repo (`deb.nodesource.com`), which was pinned to `node_20.x` — *below* the declared `engines.node >=22` — until upgraded; the dev shell now reports `v24.18.0`. Python is provided by **conda/miniforge** (`~/miniforge3`, Python 3.13, only the `base` env exists, auto-activated by a `conda initialize` block in `~/.bashrc:119`). A system `/usr/bin/python3.12` (apt, `3.12.3`) also exists and satisfies `requires-python = ">=3.12"`.

**Why this plan exists — the root cause in one sentence:** `language: system` decouples the *declared* pin from the *executed* binary, and CI reaches the same tools through yet other mechanisms (l0-gate pip ruff, `action-shellcheck`, advisory docker gitleaks), so parity depends on convention rather than structure — and every failure below is an instance of that gap.

**Failures already observed (2026-07-05 session), each an instance of the root cause:**

- `~/.local/bin/ruff 0.15.15` (a standalone binary) shadowed the pinned `0.15.20` that conda actually had → local pre-commit linted with a different ruff than CI.
- `shellcheck-py` was installed at `0.10.0.1` (pre-dating the `0.11.0.1` pin bump); the PATH `shellcheck` was conda's `0.10.0` → local ≠ CI.
- **gitleaks was not installed at all** → the `gitleaks protect` hook died with `Executable 'gitleaks' not found`, blocking commits with a cryptic error; nothing in `scripts/dev/setup.sh` installs it.
- Node was `v20` < required `>=22` → `scripts/dev/setup.sh` *silently skipped* the Node tooling step instead of failing.
- Global npm `cspell@9.8.0` and a Windows-npm `markdownlint` shadowed the pinned versions for bare interactive calls (harmless to gates, but confusing).

## 3. Plan of work

Three phases, sequenced so the structural change lands first and alone (per `AGENTS.md` §"Merge discipline"). Phase 0 is already complete and recorded here so a stateless reader has the full picture.

**Phase 0 — version currency & local realignment (DONE 2026-07-05).** Independent groundwork already merged/opened: PR #1271 raised the `pydantic-ai-slim` floor `>=1.0 → >=2.0` (merged). PR #1272 bumps `cspell 8.19.4 → 10.0.1` (open, all checks green; needs `gh pr update-branch 1272` since #1271 merged ahead of it). Locally, the drifted tools were realigned to their pins: `ruff` reinstalled to `0.15.20` in `~/.local/bin`, `shellcheck-py` upgraded to `0.11.0.1`, and **gitleaks v8.30.1** installed to `~/.local/bin` (matching CI's docker image tag). These are stopgaps — they fix *this* machine, not the recurrence. Phases 1–2 fix the recurrence.

**Phase 1 — Layer 1: pre-commit owns the lint-tool versions, and CI runs the same hooks (PR-A, structural, merge first).** Convert the four `language: system` lint hooks — `ruff`/`ruff-format`, `shellcheck`, `gitleaks`, `yamllint` — to pinned upstream hooks so pre-commit builds an isolated, cached environment per hook at an exact `rev`, independent of ambient `PATH`. Then make CI execute those *same* hooks:
- `shellcheck (scripts/install.sh)` job: replace the `ludeeus/action-shellcheck` step with `pre-commit run shellcheck --all-files` (same job name → contract untouched).
- `gitleaks` job: replace the advisory docker step with `pre-commit run gitleaks --all-files`; decide in the durable decision record whether to keep it advisory (`continue-on-error`) or make it blocking (recommended: make it blocking, since it becomes cheap and the local hook was the only real gate at plan start).
- `lint` job: ruff currently runs inside `scripts/verify l0`. Add a `pre-commit run ruff ruff-format yamllint --all-files` step (or have `scripts/verify l0` shell out to `pre-commit run` for these three) so the *pinned hook* is the single ruff/yamllint execution both locally and in CI. Keep the doctors/drift portion of l0 as-is.
- Cache `~/.cache/pre-commit` in every job that runs pre-commit (`actions/cache` keyed on the hash of `.pre-commit-config.yaml`), or each job re-builds hook envs (~30–60 s).
- Remove `ruff`, `shellcheck-py`, `yamllint` from `requirements-dev.txt` (pre-commit now owns them); keep `pre-commit`, `pre-commit-hooks`, `pytest`, `PyYAML`. The single pin home for these three becomes the `rev:` in `.pre-commit-config.yaml`.
- Update the `AGENTS.md` §"Required CI checks" "Validates" prose where it now misdescribes a mechanism (it already says the stale `scripts/test.sh l0`; it is `scripts/verify l0`), and re-run `agents_doctor` / `ruleset_doctor` so the mirror stays clean.
- **Contract invariant:** required-check job *names* stay identical (`lint`, `shellcheck (scripts/install.sh)`, …) → `ruleset-contract.yaml` and the GitHub ruleset need no change. Only job *internals* change.

The node prose tools (`cspell`, `markdownlint`) are already effectively managed via `npm ci` + `node_modules/.bin`; leave them, or fold them into pre-commit `language: node` hooks in a later pass for uniformity (not required here).

**Phase 2 — Layer 2: pin the runtimes declaratively and retire conda (PR-B + a guarded personal-env change).** The one runtime that actually drifted is Node; Python is fine from either conda or system 3.12. The maintainer has decided conda is unwanted (only a `base` env exists; it is just the default-python host). Because retiring conda means Python must come from elsewhere, Python becomes a *second* managed runtime — which is exactly the condition under which a declarative version manager pays for itself. Adopt **mise** (`jdx/mise`, the asdf-successor: one `mise.toml` pins runtimes and manages `PATH` directly) as the *replacement* for conda's shell-integrated role, pinning `python@3.12` and `node@22`.
- Repo change (PR-B): add `mise.toml` pinning `python 3.12` + `node 22`; teach `scripts/dev/setup.sh` to prefer `mise install` when mise is present, and — regardless of mise — add a **hard `node >= 22` assertion** that fails with an actionable message (replacing the current silent skip). CI runtime pinning is already correct (`lint` uses `setup-python 3.12`, `cspell` uses `node 22`), so mise in CI is optional; keep the change local-dev-focused.
- Personal-env change (guarded, reversible until the final delete): install mise → `mise use -g python@3.12 node@22` → reinstall the dev toolchain against mise's Python (`pip install -r requirements-dev.txt`) → verify `pre-commit run --all-files` and the test suite green → **only then** remove the `conda initialize` block from `~/.bashrc` and delete `~/miniforge3`. **Pre-flight check:** confirm nothing outside this repo (a notebook workflow, another project) uses the conda base before deleting.

**Phase 3 — record the decision.** The ADR path was superseded while this plan
was running: PR #1273 retired live ADRs and made the active release decision
ledger the current record. The shipped decision is recorded in
`scratch/releases/0.1.0-beta.1/decisions.md`. Dependabot now owns pre-commit,
npm, pip, and GitHub Actions update PRs in `.github/dependabot.yml`; pre-commit.ci
was not enabled from repo code.

## 4. Concrete steps

Each step is idempotent and shows expected output. Steps run from the noted directory.

1. **Isolate the session for Layer 1** (`AGENTS.md` §1):

   ```bash
   git -C ~/memoria-vault/main fetch origin
   git -C ~/memoria-vault/main worktree add ~/memoria-vault/worktrees/precommit-managed-hooks -b feat/precommit-managed-hooks origin/main
   cd ~/memoria-vault/worktrees/precommit-managed-hooks
   ```

   Expected: `Preparing worktree (new branch 'feat/precommit-managed-hooks')` and `HEAD is now at <sha> …`.

2. **Convert the lint hooks to pinned upstream repos** in `.pre-commit-config.yaml`. Replace the four `language: system` blocks (`gitleaks`, `ruff` + `ruff-format`, `yamllint`, `shellcheck`) with pinned `repo:`/`rev:` hooks. Target revs (match the current pins): ruff `v0.15.20` (`astral-sh/ruff-pre-commit`), gitleaks `v8.30.1` (`gitleaks/gitleaks`), yamllint `v1.38.0` (`adrienverge/yamllint`), shellcheck `v0.11.0` (`gitleaks`… no — `shellcheck-py` at `v0.11.0.1` or `koalaman/shellcheck-precommit v0.11.0`; pick `shellcheck-py` to keep the exact pin already in use). Keep the `no-commit-to-branch`, `check-json`, doctors, `cspell`, `markdownlint-structural`, and drift hooks unchanged.

3. **Verify the hooks resolve to the pinned versions regardless of PATH**:

   ```bash
   pre-commit run ruff ruff-format shellcheck gitleaks yamllint --all-files
   ```

   Expected: all `Passed`. Then the parity proof — put a bogus older ruff first on PATH and confirm the hook is unaffected:

   ```bash
   mkdir -p /tmp/badbin && printf '#!/bin/sh\necho "ruff 0.0.1"\n' > /tmp/badbin/ruff && chmod +x /tmp/badbin/ruff
   PATH=/tmp/badbin:$PATH pre-commit run ruff --all-files   # still runs the rev-pinned 0.15.20, still Passed
   ```

4. **Repoint CI to the hooks** — edit `lint-installers.yml` (`shellcheck` job → `pre-commit run shellcheck --all-files`), `gitleaks.yml` (→ `pre-commit run gitleaks --all-files`), `lint.yml` (add a `pre-commit run ruff ruff-format yamllint --all-files` step, or route through `scripts/verify l0`). Add an `actions/cache` step for `~/.cache/pre-commit` keyed on `hashFiles('.pre-commit-config.yaml')` in each. Keep job **names** byte-identical.

5. **Drop the now-pre-commit-owned pins** from `requirements-dev.txt` (`ruff`, `shellcheck-py`, `yamllint`); keep `pre-commit`, `pre-commit-hooks`, `pytest`, `PyYAML`. Update the `AGENTS.md` §"Required CI checks" "Validates" prose to the current mechanism.

6. **Full local gate + push + PR**:

   ```bash
   pre-commit run --all-files
   python scripts/verify l0
   git add .pre-commit-config.yaml .github/workflows/lint.yml .github/workflows/lint-installers.yml .github/workflows/gitleaks.yml requirements-dev.txt AGENTS.md
   git commit -m "Manage lint-tool versions with pre-commit; run the same hooks in CI"
   git push -u origin feat/precommit-managed-hooks
   gh pr create --base main --fill
   gh pr checks <n> --watch
   ```

   Expected: every required check green; `shellcheck (scripts/install.sh)` and `gitleaks` now execute the rev-pinned hooks.

7. **Layer 2 worktree + `mise.toml` + setup.sh guard** (after PR-A merges):

   ```bash
   git -C ~/memoria-vault/main fetch origin
   git -C ~/memoria-vault/main worktree add ~/memoria-vault/worktrees/mise-runtimes -b feat/mise-runtimes origin/main
   cd ~/memoria-vault/worktrees/mise-runtimes
   printf '[tools]\npython = "3.12"\nnode = "22"\n' > mise.toml
   # edit scripts/dev/setup.sh: add `mise install` (if mise present) + a hard `node>=22` assertion (fail, don't skip)
   ```

8. **Retire conda (personal env — reversible until the delete)**:

   ```bash
   # pre-flight: confirm no non-repo use of the conda base
   ~/miniforge3/bin/conda env list          # expect only: base
   curl https://mise.run | sh               # install mise
   mise use -g python@3.12 node@22
   pip install -r requirements-dev.txt       # reinstall toolchain against mise's python
   pre-commit run --all-files && python scripts/verify l1   # verify green BEFORE removing conda
   # only after green: remove the conda-init block from ~/.bashrc and:  rm -rf ~/miniforge3
   ```

9. **Decision + update routing** (Phase 3): record the shipped decision in the
   active release decision ledger, verify Dependabot covers the pre-commit/npm/pip
   update surfaces, and run `python scripts/checks/agents_doctor.py` clean.

## 5. Validation and acceptance

- **Claim:** Given a wrong `ruff` first on `PATH`, when `pre-commit run ruff --all-files` runs, then it still executes the rev-pinned `0.15.20`.
  - **Prove with:** the `/tmp/badbin` transcript in step 3.
- **Claim:** Local and CI run the *same* shellcheck/gitleaks/ruff.
  - **Prove with:** CI job logs for `shellcheck (scripts/install.sh)` and `gitleaks` showing `pre-commit run …` and the same `rev`; local `pre-commit run --all-files` green.
- **Claim:** A fresh clone reproduces the toolchain in one command.
  - **Prove with:** `git clone` into a temp dir → `mise install && pre-commit install --install-hooks` → `pre-commit run --all-files` green, with `ruff --version`/`shellcheck --version`/`gitleaks version`/`node --version` all at the pins.
- **Claim:** A missing tool / under-version runtime fails loudly, not silently.
  - **Prove with:** with Node 20 active, `bash scripts/dev/setup.sh` exits non-zero with an actionable `node >= 22` message (not the old silent skip); on a box without gitleaks, `pre-commit install --install-hooks` provisions it (no `Executable not found`).
- **Claim:** The required-check contract is unchanged.
  - **Prove with:** `python scripts/checks/ruleset_doctor.py` clean; `git diff` shows no change to `.github/ruleset-contract.yaml` job names.

## 6. Idempotence and recovery

- **Safe to re-run:** worktree creation is create-or-noop; editing `.pre-commit-config.yaml` and workflows is declarative; `pre-commit run` and `scripts/verify` are read-only gates; `mise install` is idempotent.
- **Rollback:**
  - Layer 1: `git worktree remove ~/memoria-vault/worktrees/precommit-managed-hooks`; revert the PR commit. pre-commit hook envs live in `~/.cache/pre-commit` and can be discarded with `pre-commit clean`.
  - Layer 2: keep NodeSource + system python3.12 as the fallback; mise is removable (`rm -rf ~/.local/share/mise ~/.config/mise`). **Conda deletion is the one irreversible step** — do not run `rm -rf ~/miniforge3` until §5's green transcript exists; to be extra-safe, `tar czf ~/miniforge3-backup.tgz -C ~ miniforge3` first, or note the reinstall path (`https://github.com/conda-forge/miniforge`).

## 7. Progress

- [x] 2026-07-05 14:00 — Phase 0: version currency (#1271 and #1272 merged) + local realignment (ruff 0.15.20, shellcheck-py 0.11.0.1, gitleaks v8.30.1 installed)
- [x] 2026-07-05 — Phase 1 / PR-A: pre-commit-managed lint hooks + CI runs the same hooks (shipped in PR #1273)
- [x] 2026-07-05 — Phase 2 / PR-B: `mise.toml` + `scripts/dev/setup.sh` node>=22 assertion (shipped in PR #1273)
- [ ] Phase 2: retire conda (personal environment only; not repo-verifiable and not performed by this plan closeout)
- [x] 2026-07-05 — Phase 3: decision recorded in the beta.1 scratch ledger; Dependabot covers pre-commit/npm/pip updates
- [x] 2026-07-06 — Closeout audit: main implementation and documentation verified; this plan updated with shipped outcomes

## 8. Execution log

- 2026-07-05 — Chose to keep required-check job *names* identical and only change job *internals*, so `.github/ruleset-contract.yaml` and the GitHub ruleset need no edit (avoids the emergency-bypass path in `AGENTS.md` §PR flow). The architectural decision was later routed to the beta.1 release decision ledger after PR #1273 retired live ADRs.
- 2026-07-05 — Sequenced Layer 1 before Layer 2 (structural-first, `AGENTS.md` §Merge discipline); conda retirement gated behind a green verification because it is the only irreversible step.
- 2026-07-05 — PR #1273 merged the repo-owned work: pinned upstream pre-commit hook environments, CI callers, `mise.toml`, setup guard, Dependabot pre-commit updates, and the ADR-to-design-history routing change. The decision record moved from planned ADR-131 to `scratch/releases/0.1.0-beta.1/decisions.md`.
- 2026-07-06 — Closeout audit found no exact GitHub issue titled "Harden dev toolchain against version drift"; no retroactive issue was opened because PR #1273 completed the repo-owned implementation and no repo follow-up remains.

## 9. Surprises & discoveries

- CI ran the three lint tools via **three different mechanisms**, none of them pre-commit: ruff inside `scripts/verify l0` (pip), shellcheck via `ludeeus/action-shellcheck` (its own bundled build, unrelated to the `shellcheck-py` pin), gitleaks via docker `v8.30.1`. So local↔CI parity was never structural.
- The CI `gitleaks` job was **`continue-on-error: true`** and **not a required check** — advisory only. The *local* pre-commit `gitleaks` hook was therefore the only enforcing secret-scan pre-merge — and it was broken (binary not installed), so commits failed with `Executable 'gitleaks' not found`.
- conda is **load-bearing right now** (active `python3`, hosts pytest/pre-commit/shellcheck) even though only the `base` env exists — "unused" was the wrong description; removal requires replacing the Python source first.
- `scripts/dev/setup.sh` treats Node < 22 as a **silent skip**, so the qmd/Node tooling step just quietly doesn't run.
- `docs/adr/` was retired by the same workflow-audit implementation, so the
  plan's ADR-131 target became stale while the plan was running. The current
  source of truth is the beta.1 decision ledger.

## 10. Interfaces & dependencies

- **pre-commit hook sources (new pins, single source of truth for lint versions):** `astral-sh/ruff-pre-commit@v0.15.20` (hooks `ruff`, `ruff-format`), `gitleaks/gitleaks@v8.30.1` (hook `gitleaks`), `adrienverge/yamllint@v1.38.0` (hook `yamllint`), `shellcheck-py@v0.11.0.1` (hook `shellcheck`). Confirm exact tag spellings against each repo's `.pre-commit-hooks.yaml` at authoring time.
- **Contract files that must stay consistent:** `.github/ruleset-contract.yaml` (required-check roster; job names unchanged), its `AGENTS.md` §"Required CI checks" mirror (guarded by `scripts/checks/agents_doctor.py` + `ruleset_doctor.py`).
- **Runtime pins:** `mise.toml` → `python 3.12`, `node 22`. `package.json` `engines.node ">=22"` (unchanged). `pyproject.toml` `requires-python ">=3.12"` (unchanged).
- **Auto-update:** Dependabot for pre-commit, `package.json`/`package-lock.json`, `requirements-dev.txt`, and GitHub Actions. pre-commit.ci was not enabled from repo code.
- **Removed pins:** `ruff`, `shellcheck-py`, `yamllint` leave `requirements-dev.txt` (pre-commit owns them).

## 11. Artifacts & notes

- Phase 0 realignment (this session): `ruff --version` → `ruff 0.15.20` on `~/.local/bin`; `python -m pip show shellcheck-py` → `0.11.0.1`; `gitleaks version` → `8.30.1`; PR #1271 merged (`f8db508c` → main `79e73ab7`); PR #1272 later merged (`cspell` 10.0.1).
- Current required roster (`.github/ruleset-contract.yaml`): `pr-policy, lint, shellcheck (scripts/install.sh), PSScriptAnalyzer (scripts/install.ps1), python-selftest, cspell, lint-config, markdownlint`.
- Original CI mechanisms replaced by PR #1273: `lint.yml` (`python scripts/verify l0` using pip ruff), `lint-installers.yml` (`ludeeus/action-shellcheck`), `gitleaks.yml` (`docker … ghcr.io/gitleaks/gitleaks:v8.30.1`, `continue-on-error: true`).

## 12. Outcomes & retrospective

- **Shipped:** pre-commit-managed third-party lint hooks live in
  `.pre-commit-config.yaml`; CI runs ruff, ruff-format, yamllint, shellcheck, and
  gitleaks through those hooks; `requirements-dev.txt` no longer owns those tool
  pins; `mise.toml` pins Python 3.12 and Node 22; `scripts/dev/setup.sh` runs
  `mise install` when available and hard-fails on missing or under-version Node;
  `AGENTS.md`, `.agents/`, tests, and Dependabot were updated in PR #1273.
- **Still open:** personal conda retirement only. It is outside repo state and
  should be done manually after confirming no non-repo workflow depends on
  `~/miniforge3`. pre-commit.ci was not enabled; repo-native Dependabot
  pre-commit updates are the shipped update path.
- **Routed to:** PR #1273
  (`https://github.com/eranroseman/memoria-vault/pull/1273`) and
  `scratch/releases/0.1.0-beta.1/decisions.md`.
- **Closeout verification (2026-07-06):** `python -m pytest
  tests/test_node_tooling.py -q` → 6 passed; `pre-commit run ruff --all-files`,
  `pre-commit run ruff-format --all-files`, `pre-commit run yamllint
  --all-files`, `pre-commit run shellcheck --all-files`, and `pre-commit run
  gitleaks --all-files` → Passed; fake `ruff 0.0.1` first on `PATH` still left
  `pre-commit run ruff --all-files` Passed; `python scripts/verify l0` → 96
  static tests passed and L0 gate clean.
- **Lessons:** keep ExecPlans in the active release scratch tree and route
  durable decisions to release ledgers as soon as they are made; otherwise the
  plan can preserve an obsolete destination even after the implementation fixes
  the destination.
