# Contributing to Memoria

Memoria is a standalone local research CLI and runtime. Contributions to the
installer, runtime package, packaged workspace seed, and docs are welcome.

## Before you start

- Check [open issues](https://github.com/eranroseman/memoria-vault/issues) to avoid duplicate work.
- Open an issue first for significant changes: new operation surfaces, installer
  overhauls, schema changes, provider integrations, or architecture decisions.
- Small docs, typo, script, and test fixes can go straight to a PR.
- AI agents follow [AGENTS.md](AGENTS.md) for repo facts and the installed superpowers skills for how work happens.

## Development setup

**Requirements:** Git, WSL2 or Linux, Python 3.12+ with venv support, and any
provider keys needed for the flow you are testing. Node 22 is needed only when
developing the optional `packages/memoria-obsidian` adapter package.

```bash
git clone https://github.com/eranroseman/memoria-vault.git
cd memoria-vault

# One-time contributor tooling: dev requirements and pre-commit hooks.
bash scripts/dev/setup.sh

# Installer syntax and dry-run checks.
bash -n scripts/install.sh
bash scripts/install.sh --dry-run
```

`scripts/dev/setup.sh` sets up the contributor toolchain only; it does not install or run
Memoria. Runtime package dependencies come from `pyproject.toml` and install into
the workspace-local `.memoria/.venv`.
The `cspell` and `markdownlint` hooks run in pre-commit-managed Node
environments; do not run `npm ci` at the repo root for prose checks.
Recommended VS Code extensions are listed in [.vscode/extensions.json](.vscode/extensions.json).

See [Quickstart](docs/how-to-guides/setup/quickstart.md) for the product install walkthrough.

## Where work lives

| Work | Home |
|---|---|
| Bugs, enhancements, docs fixes, and questions | [GitHub issues](https://github.com/eranroseman/memoria-vault/issues) |
| Release scope | GitHub milestones (a milestone is a release) |
| Working specs and plans | `docs/superpowers/` (tracked, not published) |
| Decisions and durable rationale | [Design history](design-history/README.md) |

Labels stay minimal: use `bug` and `documentation` for repo-wide search, plus
bot-managed labels such as `dependencies`, `python`, and `github_actions`. Do not
recreate status, priority, or subsystem taxonomies as labels.

## Testing and verification

`python scripts/verify` is the one gate. It runs lint, the product-integrity
checks, the `static`/`unit`/`contract` test suite, an offline end-to-end smoke,
and syntax checks; CI requires it plus `gitleaks`. Target a subset while
iterating with `python3 -m pytest tests/ -q -m unit` (or `contract`, `static`).
The `package`, `runtime`, and `live` test markers need a built wheel, a
disposable workspace, or a live provider and are run on demand, not in the gate.

Do not test installers against the real `~/Memoria`; use a disposable vault
under `test-vault/`.

## Coding conventions

- **Python:** Ruff is both linter and formatter for repo tooling and runtime code
  (`src/memoria_vault/`, `scripts/`, and `tests/`). `ruff format` owns layout at
  line length 100.
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

Keep one scope per branch and PR. Each session works in its own worktree (see
[AGENTS.md](AGENTS.md)).

Before opening a PR:

- Claim or reference the issue when one exists.
- Rebase on `origin/main`.
- Stage only files you changed.
- Run `python scripts/verify`.
- Open the PR against `main` and fill out the template.

`main` requires a PR plus the `verify` and `gitleaks` checks, and merges by squash.

## Commit style

No commit-message format is required. Clear, lowercase, imperative subjects are
encouraged; [Conventional Commits](https://www.conventionalcommits.org/) prefixes
(`feat`, `fix`, `docs`, `refactor`, `chore`, `test`, `research`) are a fine
convention and earn back a required role if release automation returns.

Call out breaking changes explicitly — CLI command or JSON-contract changes,
vault folder restructuring, provider/config field renames, and required
frontmatter contract changes — stating what changed, who is affected, what action
is required, and the replacement path.

## Releases and changelog

A milestone is a release. There is no release automation right now:
`CHANGELOG.md` is a hand-curated dated record, and versioning, tags, and GitHub
Releases return with release tooling when distribution needs them. Do not
hand-cut a release or hand-tag as part of an ordinary PR.

## Questions?

Open a [GitHub Discussion](https://github.com/eranroseman/memoria-vault/discussions)
or file an issue. Use `bug` or `documentation` only when they apply.
