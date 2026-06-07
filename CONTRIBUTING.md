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

# One-time: wire the local quality gate (activates the pre-commit hook, installs
# ruff + yamllint + MCP self-test deps). Git does NOT activate repo hooks on clone.
bash scripts/dev-setup.sh

# Validate the installer without running it
bash -n scripts/install.sh

# Dry-run (shows every command, changes nothing)
bash scripts/install.sh --dry-run
```

`dev-setup.sh` sets up the **contributor toolchain** only; it does not install or run
the Memoria product (that's `scripts/install.sh`). The pre-commit hook it enables is a
fast local mirror of the required CI checks — bypass a single block, rarely, with
`git commit --no-verify`. Recommended VS Code extensions are listed in
[.vscode/extensions.json](.vscode/extensions.json) (VS Code prompts to install them on
first open).

See [docs/tutorials/01-set-up-from-zero.md](docs/tutorials/01-set-up-from-zero.md) for a full walkthrough.

## What to work on

| Area | Where |
|---|---|
| Installer (`scripts/install.sh` / `scripts/install.ps1`) | `scripts/` |
| Agent profiles | `vault/.memoria/profiles/memoria-*/` |
| Vault templates & structure | `vault/` |
| Documentation (Diátaxis) | `docs/` — tutorials, how-to-guides, reference, explanation |
| Scripts | `scripts/` |

## Coding conventions

- **Shell:** `scripts/install.sh` targets Bash on Ubuntu/WSL2. Use `shellcheck` before submitting. Avoid bashisms if POSIX portability matters.
- **PowerShell:** `scripts/install.ps1` targets Windows PowerShell 5.1. Test on a real Windows machine or WSL2 bridge.
- **Profiles:** Agent profiles live under `vault/.memoria/profiles/`. Follow the existing `SOUL.md` / `AGENTS.md` / `skills/` structure used by the other seven profiles.
- **Docs:** Follow the [Diátaxis](https://diataxis.fr/) framework — tutorials teach, how-to guides direct, reference informs, explanation discusses. Keep docs in the right quadrant.
- **Markdown:** the editor lints with the full `.markdownlint.jsonc` (style aids — code-fence languages, trailing whitespace, etc.). **CI enforces only** the structural subset in `.github/markdownlint/docs-structural.json` (5 rules that catch real rendering bugs on `docs/`, with no Obsidian false positives). So the editor intentionally flags more than CI gates — by design; only the structural rules block a PR.

## Submitting a pull request

1. Fork the repo and create a branch off `main`.
2. Make your changes and test them (`--dry-run` at minimum; a live run if you can).
3. Run `bash -n scripts/install.sh` (syntax check) and `markdownlint '**/*.md'` if you touched docs.
4. Open a PR against `main`. Fill out the PR template.

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

Mark a breaking change with `!` in the header or a `BREAKING CHANGE:` footer:

```text
feat!: rename profile config field `enabled_agents` → `agents.enabled`

BREAKING CHANGE: existing config.yaml files must rename the field before upgrading.
```

State **what changed**, **who is affected**, **what action is required**, and **the replacement path**.

## Changelog

User-visible changes go in [CHANGELOG.md](CHANGELOG.md) at the repo root, which follows
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
