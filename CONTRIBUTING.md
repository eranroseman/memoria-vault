# Contributing to Memoria

Memoria is a research operating system built on
[Hermes Agent](https://hermes-agent.nousresearch.com) and
[Obsidian](https://obsidian.md). Contributions to the installer, agent profiles,
vault templates, and docs are welcome.

## Before you start

- Check [open issues](https://github.com/eranroseman/memoria-vault/issues) to avoid duplicate work.
- Open an issue first for significant changes: new agents, installer overhauls, profile capabilities, schema changes, or architecture decisions.
- Small docs, typo, script, and test fixes can go straight to a PR.
- AI agents must follow [AGENTS.md](AGENTS.md); it is authoritative for worktrees, branch safety, PR flow, docs routing, and required checks.

## Development setup

**Requirements:** Git, WSL2 or Linux, and the product keys needed for the flow you
are testing. The normal install path needs `KILOCODE_API_KEY`; full source ingest
also needs `OPENALEX_API_KEY`.

```bash
git clone https://github.com/eranroseman/memoria-vault.git
cd memoria-vault

# One-time contributor tooling: dev requirements, pre-commit hooks, qmd if available.
bash scripts/dev-setup.sh

# Installer syntax and dry-run checks.
bash -n scripts/install.sh
bash scripts/install.sh --dry-run
```

`dev-setup.sh` sets up the contributor toolchain only; it does not install or run
Memoria. Runtime vault dependencies stay under `src/.memoria/mcp/requirements.txt`.
Recommended VS Code extensions are listed in [.vscode/extensions.json](.vscode/extensions.json).

See [Quickstart](docs/how-to-guides/setup/quickstart.md) for the product install walkthrough.

## Where work lives

| Work | Home |
|---|---|
| Bugs, enhancements, docs fixes, and questions | [GitHub issues](https://github.com/eranroseman/memoria-vault/issues) |
| Live planning state | Memoria Issue Tracker project fields |
| Release scope | GitHub milestones |
| Decisions and durable rationale | [ADRs](docs/adr/) |
| Release prose | `docs/releasing/<version>/` |

The Project carries two fields:

| Field | Values | Rule |
|---|---|---|
| Status | `Backlog`, `In progress`, `In review`, `Done` | Workflow state only |
| Readiness | `Ready`, `Needs shaping`, `Blocked`, `Later` | Why work is or is not ready |

Labels stay minimal: use `bug` and `documentation` for repo-wide search, plus
bot-managed labels such as `dependencies`, `python`, `github_actions`, `release`,
and `autorelease:*`. Do not recreate status, readiness, priority, or subsystem
taxonomies as labels.

## Coding conventions

- **Python:** Ruff is both linter and formatter for repo tooling and runtime code
  (`scripts/`, `.github/scripts/`, `src/.memoria/`, and `tests/`). `ruff format`
  owns layout at line length 100.
- **Shell:** `scripts/install.sh` targets Bash on Ubuntu/WSL2. Run `shellcheck`
  before submitting installer changes.
- **PowerShell:** `scripts/install.ps1` targets Windows PowerShell 5.1. Test on
  Windows when the change affects Windows behavior.
- **Profiles:** profile source lives under `src/.memoria/profiles/`; keep the
  existing `SOUL.md`, `config.yaml`, `distribution.yaml`, and `skills/` shape.
- **Docs:** follow [Diátaxis](https://diataxis.fr/): tutorials teach, how-to
  guides direct, reference informs, and explanation discusses.
- **Markdown:** `.markdownlint.json` holds the structural rules enforced locally
  and in CI. Editor-only style hints in `.vscode/settings.json` do not gate PRs.

## Pull requests

Keep one scope per branch and PR. For agents, branch creation happens through the
worktree flow in [AGENTS.md](AGENTS.md#1-session-isolation--git-worktree).

Before opening a PR:

- Claim or reference the issue when one exists.
- Rebase on `origin/main`.
- Stage only files you changed.
- Run the smallest relevant check, then the standard repo check when the change
  is broader: `scripts/verify pr`.
- Open the PR against `main` and fill out the template.

Required CI checks and merge discipline are defined in [AGENTS.md](AGENTS.md).

## Commit style

Use short, lowercase imperative subject lines following
[Conventional Commits](https://www.conventionalcommits.org/):

```text
fix: installer fails when KILOCODE_API_KEY is unset
docs: add WSL2 troubleshooting section
profiles: extend librarian skill for zotero groups
```

| Type | Use for | Version intent |
|---|---|---|
| `feat` | New capability or integration | Minor |
| `fix` | Bug fix, regression, broken automation | Patch |
| `docs` | Documentation only | - |
| `refactor` | Code change with no behavior change | - |
| `chore` | Tooling, deps, config, maintenance | - |
| `test` | Test plans or self-test coverage | - |
| `research` | Evaluation or investigation outcomes | - |

Breaking changes use `!` in the header or a `BREAKING CHANGE:` footer, and must
state what changed, who is affected, what action is required, and the replacement
path. In Memoria, breaking changes include profile config field renames, vault
folder restructuring, removed profile capabilities or skills, and required
ADR-frontmatter changes.

## Releases and changelog

Milestones are releases. Versioning, release notes, tags, GitHub Releases, and
`CHANGELOG.md` are release-maintainer work owned by release-please when formal
release automation is active. Do not hand-cut a release, hand-tag, or hand-edit
the changelog as part of an ordinary PR.

## Questions?

Open a [GitHub Discussion](https://github.com/eranroseman/memoria-vault/discussions)
or file an issue. Use `bug` or `documentation` only when they apply.
