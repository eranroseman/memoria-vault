# Contributing to Memoria

Thanks for your interest in contributing. Memoria is a research operating system built on [Hermes Agent](https://hermes-agent.nousresearch.com) and [Obsidian](https://obsidian.md) — contributions to the installer, agent profiles, vault templates, and docs are all welcome.

## Before you start

- Check [open issues](https://github.com/eranroseman/memoria-vault/issues) to avoid duplicating work.
- For significant changes (new agents, installer overhauls, new profile capabilities), open an issue to discuss first.
- For small fixes (docs, typos, script bugs), a PR is fine without prior discussion.

## Development setup

**Requirements:** Git, WSL2 (Windows) or Linux, a `KILOCODE_API_KEY`.

```bash
git clone https://github.com/eranroseman/memoria-vault.git
cd memoria-vault

# One-time: wire the local quality gate (installs requirements-dev.txt tooling,
# pre-commit hooks, and MCP self-test deps). Git does NOT activate repo hooks on clone.
bash scripts/dev-setup.sh

# Validate the installer without running it
bash -n scripts/install.sh

# Dry-run (shows every command, changes nothing)
bash scripts/install.sh --dry-run
```

`dev-setup.sh` sets up the **contributor toolchain** only; it does not install or run
the Memoria product (that's `scripts/install.sh`). The root `requirements-dev.txt`
is for local/CI tooling such as `pre-commit`, `pytest`, `ruff`, and `yamllint`;
vault runtime dependencies stay under `src/.memoria/mcp/requirements.txt`. The
setup script runs `pre-commit install` to wire the hooks defined in
`.pre-commit-config.yaml` — a fast local mirror of the required CI checks. The
hooks also run an advisory grammar check with
[harper](https://github.com/elijah-potter/harper) (output is informational; it never
blocks a commit). Bypass all hooks for a single commit, rarely, with
`git commit --no-verify`. Recommended VS Code extensions are listed in
[.vscode/extensions.json](.vscode/extensions.json) (VS Code prompts to install them on
first open).

If Node ≥22 is present, `dev-setup.sh` also installs the repo-local
[qmd](https://github.com/tobi/qmd) code-search engine (a `devDependency`, never deployed)
and builds a project-local `./.qmd/` index of this repo for coding agents — see
[Searching the codebase (qmd)](AGENTS.md#searching-the-codebase-qmd). It is optional and
not part of the commit gate; if Node is missing the step is skipped with a pointer to
install it. Run `bash scripts/qmd-codebase-index.sh --embed` to add semantic vectors.

See [docs/tutorials/01-set-up-from-zero.md](docs/tutorials/01-set-up-from-zero.md) for a full walkthrough.

### Optional: a git safety alias

The most common foot-gun is losing uncommitted work to `reset --hard` or `checkout` (see AGENTS.md §4). This makes "stash everything first" one keystroke:

```bash
git config --global alias.save 'stash push -u -m wip'   # save → git save  ·  restore → git stash pop
```

The structural fix is a worktree per branch (AGENTS.md §1/§4): switching becomes `cd`, so there's no dirty tree to lose.

## What to work on

| Area | Where |
|---|---|
| Installer (`scripts/install.sh` / `scripts/install.ps1`) | `scripts/` |
| Agent profiles | `src/.memoria/profiles/memoria-*/` |
| Vault templates & structure | `src/` |
| Documentation (Diátaxis) | `docs/` — tutorials, how-to-guides, reference, explanation |
| Scripts | `scripts/` |

## Coding conventions

- **Python:** Ruff is both the linter and the formatter for repo tooling and runtime
  code (`scripts/`, `.github/scripts/`, `src/.memoria/`, and `tests/`). `ruff format`
  (line-length 100) owns layout so style stays consistent across the many agent
  sessions that generate this code — run it (or `pre-commit`) before submitting; CI
  fails on unformatted code via `ruff format --check`.
- **Shell:** `scripts/install.sh` targets Bash on Ubuntu/WSL2. Use `shellcheck` before submitting. Avoid bashisms if POSIX portability matters.
- **PowerShell:** `scripts/install.ps1` targets Windows PowerShell 5.1. Test on a real Windows machine or WSL2 bridge.
- **Profiles:** Agent profiles live under `src/.memoria/profiles/`. Follow the existing `SOUL.md` / `config.yaml` / `distribution.yaml` / `skills/` structure used by the existing five profiles (the shared `AGENTS.md` layer is vault-level, not per-profile).
- **Docs:** Follow the [Diátaxis](https://diataxis.fr/) framework — tutorials teach, how-to guides direct, reference informs, explanation discusses. Keep docs in the right quadrant.
- **Markdown:** one shared config, `.markdownlint.json`, holds the structural rule set (5 rules that catch real rendering bugs on `docs/`, with no Obsidian false positives). The editor, pre-commit, and CI all enforce exactly that set. The editor additionally shows style-only hints (e.g. MD013 line-length) via the `markdownlint.config` key in `.vscode/settings.json` — those do **not** gate a PR, so the editor intentionally flags a little more than CI blocks.

## Submitting a pull request

Branch off `main`, test your change (`--dry-run` at minimum, plus `bash -n scripts/install.sh` and `markdownlint '**/*.md'` if you touched docs), then open a PR against `main` and fill out the template. The authoritative branch, PR, and merge-discipline rules live in [AGENTS.md](https://github.com/eranroseman/memoria-vault/blob/main/AGENTS.md); the human-facing checklists and recovery steps are in [Contributing workflow](docs/contributing/process.md).

## Commit style

Use short, lowercase imperative subject lines following [Conventional Commits](https://www.conventionalcommits.org/):

```text
fix: installer fails when KILOCODE_API_KEY is unset
docs: add WSL2 troubleshooting section
profiles: extend Librarian skill for Zotero groups
```

| Type | Use for | Version intent |
|---|---|---|
| `feat` | New capability or integration | Minor |
| `fix` | Bug fix, regression, broken automation | Patch |
| `docs` | Documentation only | — |
| `refactor` | Code change with no behavior change | — |
| `chore` | Tooling, deps, config, maintenance | — |
| `test` | Test plans or `--self-test` coverage | — |
| `research` | Evaluation or investigation outcomes | — |

### Breaking changes

Mark a breaking change with `!` in the header or a `BREAKING CHANGE:` footer, and state **what changed**, **who is affected**, **what action is required**, and **the replacement path**:

```text
feat!: rename profile config field `enabled_agents` → `agents.enabled`

BREAKING CHANGE: existing config.yaml files must rename the field before upgrading.
```

What counts as a breaking change in Memoria, and how the commit types map to SemVer, is defined in [Contributing workflow](docs/contributing/process.md).

## Changelog

User-visible changes go in [Changelog](CHANGELOG.md) at the repo root, which follows
[Keep a Changelog](https://keepachangelog.com/) + [SemVer](https://semver.org/). Keep an
`[Unreleased]` section at the top; entries move into a versioned section when a release is cut.

- **Sections:** Added · Changed · Fixed · Removed · Deprecated · Security.
- **Each bullet** starts with a verb, names the affected system, and explains user impact
  (not implementation detail). Include migration guidance for breaking changes.
- **Include:** new user-facing features, behavior/schema changes, breaking changes, and
  integration changes (GitHub, vault, Hermes).
- **Exclude:** pure refactors, routine dependency bumps, and test-only changes.

## Questions?

Open a [GitHub Discussion](https://github.com/eranroseman/memoria-vault/discussions) or file an issue with the `question` label.
