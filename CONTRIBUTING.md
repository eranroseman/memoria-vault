# Contributing to Memoria

Memoria is a standalone local research CLI and runtime. Contributions to the
installer, runtime package, packaged workspace seed, and docs are welcome.

## Before you start

- Check [open issues](https://github.com/eranroseman/memoria-vault/issues) to avoid duplicate work.
- Open an issue first for significant changes: new operation surfaces, installer
  overhauls, schema changes, provider integrations, or architecture decisions.
- Small docs, typo, script, and test fixes can go straight to a PR.
- AI agents must follow [AGENTS.md](AGENTS.md); it is authoritative for worktrees, branch safety, PR flow, docs routing, and required checks.

## Development setup

**Requirements:** Git, WSL2 or Linux, Python 3.12+ with venv support, Node 22 for
contributor prose tools, and any provider keys needed for the flow you are testing.

```bash
git clone https://github.com/eranroseman/memoria-vault.git
cd memoria-vault

# One-time contributor tooling: dev requirements, pre-commit hooks, prose tools.
bash scripts/dev/setup.sh

# Installer syntax and dry-run checks.
bash -n scripts/install.sh
bash scripts/install.sh --dry-run
```

`scripts/dev/setup.sh` sets up the contributor toolchain only; it does not install or run
Memoria. Runtime package dependencies come from `pyproject.toml` and install into
the workspace-local `.memoria/.venv`.
Recommended VS Code extensions are listed in [.vscode/extensions.json](.vscode/extensions.json).

See [Quickstart](docs/how-to-guides/setup/quickstart.md) for the product install walkthrough.

## Where work lives

| Work | Home |
|---|---|
| Bugs, enhancements, docs fixes, and questions | [GitHub issues](https://github.com/eranroseman/memoria-vault/issues) |
| Live planning state | Memoria Issue Tracker project fields |
| Release scope | GitHub milestones |
| Release readiness | The parent "Release <version>" issue and its sub-issues |
| Decisions and durable rationale | [Design history](design-history/README.md) |

The Project carries two fields:

| Field | Values | Rule |
|---|---|---|
| Status | `Backlog`, `In progress`, `In review`, `Done` | Workflow state only |
| Readiness | `Ready`, `Needs shaping`, `Blocked`, `Later` | Why work is or is not ready |

Labels stay minimal: use `bug` and `documentation` for repo-wide search, plus
bot-managed labels such as `dependencies`, `python`, `github_actions`, `release`,
and `autorelease:*`. Do not recreate status, readiness, priority, or subsystem
taxonomies as labels.

## Testing and verification

Testing is organized by promotion gate, not by tool. Use the cheapest gate that
proves the change, then run the normal PR gate before handoff when the change is
broader than a narrow doc edit.

| Gate | Proves | Front door |
|---|---|---|
| Source | Repo contracts, docs, schemas, Python tests, and static checks are coherent. | `scripts/verify pr` |
| Package | A disposable vault assembles and the offline workflow replay works. | `scripts/verify package` |
| Runtime | Live model endpoint, optional transports, scheduled-task wrappers, and policy boundaries work in a disposable workspace. | `scripts/verify runtime` |
| Release candidate | Source, Package, and Runtime run as a candidate prefix. Product/manual evidence still belongs in release issues. | `scripts/verify rc` |

Product, manual GUI, failure/recovery, and release cut evidence lives in the
relevant release parent issue or sub-issues, not in repository docs. Do not test
installers against the real `~/Memoria`.

## Coding conventions

- **Python:** Ruff is both linter and formatter for repo tooling and runtime code
  (`src/memoria_vault/`, `scripts/`, `.github/scripts/`, and `tests/`). `ruff format`
  owns layout at line length 100.
- **Shell:** `scripts/install.sh` targets Bash on Ubuntu/WSL2. Run `shellcheck`
  before submitting installer changes.
- **PowerShell:** `scripts/install.ps1` targets Windows PowerShell 5.1. Test on
  Windows when the change affects Windows behavior.
- **Optional adapters:** do not add installed profile packages or lane overrides
  to the package seed; adapters must wrap the standalone CLI/engine boundary.
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
feat: add semantic scholar enrichment replay
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
path. In Memoria, breaking changes include CLI command or JSON-contract changes,
vault folder restructuring, provider/config field renames, and required
frontmatter contract changes.

## Releases and changelog

Milestones are releases. Versioning, release notes, tags, GitHub Releases, and
`CHANGELOG.md` are release-maintainer work owned by release-please when formal
release automation is active. Do not hand-cut a release, hand-tag, or hand-edit
the changelog as part of an ordinary PR.

## Questions?

Open a [GitHub Discussion](https://github.com/eranroseman/memoria-vault/discussions)
or file an issue. Use `bug` or `documentation` only when they apply.
