# Contributing to Memoria

Memoria is a standalone local research CLI and runtime. Contributions to the
installer, runtime package, packaged workspace seed, and docs are welcome.

## Before you start

- Check [open issues](https://github.com/eranroseman/memoria-vault/issues) to avoid duplicate work.
- Which changes need an issue opened first, and which can go straight to a PR,
  is in [AGENTS.md](AGENTS.md#issue-conventions), Issue conventions.
- AI agents follow [AGENTS.md](AGENTS.md) for repo facts; how work happens is owned by your installed skills, not by this repo.

## Development setup

**Requirements:** Git, WSL2 or Linux, Python 3.12+ with venv support, and any
provider keys needed for the flow you are testing. Node 22 is needed only when
developing the Obsidian adapter (its node test suite lives under
`packages/memoria-obsidian`).

```bash
git clone https://github.com/eranroseman/memoria-vault.git
cd memoria-vault

# One-time contributor tooling: dev requirements and pre-commit hooks.
bash scripts/dev/setup.sh

# Installer syntax and dry-run checks.
bash -n scripts/install.sh
bash scripts/install.sh --dry-run
```

`scripts/dev/setup.sh` sets up the contributor toolchain. It installs the repository
package editable with its optional MCP SDK so `python scripts/verify` can exercise the MCP
transport. It does not install or run a vault-local Memoria runtime; the product installer
puts runtime dependencies in the workspace-local `.memoria/.venv`.
The `cspell` and `markdownlint` hooks run in pre-commit-managed Node
environments; no root `node_modules/` install is required for prose checks.
When developing the Obsidian adapter, install and check only its package; do
not run `npm ci` at the repo root:

```bash
npm ci --prefix packages/memoria-obsidian
npm run check --prefix packages/memoria-obsidian
```

Recommended VS Code extensions are listed in [.vscode/extensions.json](.vscode/extensions.json).

See [Quickstart](docs/how-to-guides/setup/quickstart.md) for the product install walkthrough.

## Where work lives

File work as [GitHub issues](https://github.com/eranroseman/memoria-vault/issues);
[design history](design-history/README.md) holds the decisions and durable
rationale behind the current shape.

Everything else about where work is tracked — working specs and plans,
rejected-enhancement records, release scope, the label vocabulary and the rules
for applying it — is policy. It lives in [AGENTS.md](AGENTS.md), under
[Where things live](AGENTS.md#where-things-live) and
[Issue conventions](AGENTS.md#issue-conventions). Read it there rather than
here; a second copy would be free to drift, and was.

## Testing and verification

Run `python scripts/verify` before every PR — what it covers and what CI
requires are in [AGENTS.md](AGENTS.md#ground-truth), Ground truth.

Which pytest levels the gate runs is owned by `PYTEST_MARKERS` in
`scripts/verify`. Target a subset while iterating with
`python3 -m pytest tests/ -q -m unit` (or `contract`, `static`); levels the
gate excludes run the same way on demand.

## Coding conventions

- **Python:** Ruff is both linter and formatter for repo tooling and runtime code
  (`src/memoria_vault/`, `scripts/`, and `tests/`). `ruff format` owns layout at
  line length 100.
- **Shell:** `scripts/install.sh` targets Bash on Ubuntu/WSL2. `shellcheck`
  gates every shell script under `scripts/` through the pinned pre-commit hook.
- **PowerShell:** `scripts/install.ps1` targets Windows PowerShell 5.1. Test on
  Windows when the change affects Windows behavior.
- **Configuration is read, not restated.** A literal copy of a config value
  drifts the moment the source changes, and nothing fails until behavior is
  already wrong. `search_index` re-spelled `folders.yaml`'s bundle roots and so
  missed the `categories` fallback every other consumer honored — search
  silently indexed nothing on a vault that declared only that key. A docs gate
  re-spelled `docs/_config.yml`'s exclude list and kept treating an excluded
  directory as published. Load through the shared reader instead.
- **Optional adapters:** do not add installed profile packages or lane overrides
  to the package seed; adapters must wrap the standalone CLI/engine boundary.
- **Docs:** follow [Diátaxis](https://diataxis.fr/): tutorials teach, how-to
  guides direct, reference informs, and explanation discusses.
- **Markdown:** `.markdownlint.json` holds the structural rules enforced locally
  and in CI. Editor-only style hints in `.vscode/settings.json` do not gate PRs.

## Documentation authoring conventions

For contributors editing the published docs under `docs/`. Generic Diátaxis
craft is out of scope here; the rules below are the Memoria-specific ones.

- **Routing:** tutorials teach, how-to guides direct, reference informs,
  explanation discusses. Mixed-purpose content pages are wrong — split them.
- **Portals:** the docs landing page and section `README.md` indexes are routing
  portals. Their mixed link menus are intentional and exempt from the
  single-quadrant rule. A section with exactly one guide may collapse index and
  guide into its `README.md` (currently: Using Obsidian).
- **Onboarding exception:**
  [Quickstart](docs/how-to-guides/setup/quickstart.md) is Tutorial 00, listed in
  Setup so new users can install a vault before the numbered tutorials. It
  intentionally does not assume prior Memoria knowledge.
- **Links:** inside `docs/`, use relative links following the target's Pages
  route. Link unpublished targets (root files, `design-history/`) by GitHub blob
  URL. Never relative-link into `src/` (those 404 on the site) — cite a source
  file as an inline-code path.
- **Indexing:** every new page goes in its section README; each new how-to also
  belongs in its section index. The intentionally shallow `how-to-guides/README.md`
  lists sections rather than every guide. Set `nav_order` for a logical sequence.
- **Citations:** new works go in
  [the bibliography](docs/reference/evidence-and-integrations/bibliography.md)
  (ACM author-date, `<a id>` anchor); link in-text mentions to the published
  anchor.
- **Spelling:** American English (`-ize`/`-or`); `cspell` is the gate. Add a real
  unknown term to `project-words.txt` (lowercase, sorted) — never inline-suppress.
- **Terminology:** `.vale.ini` holds the usage rulings Vale enforces over
  published docs prose. Run them from the editor with the "vale: lint the
  current file" task (Ctrl+Shift+P → "Tasks: Run Task"), or from a shell with
  `pre-commit run vale --hook-stage manual --all-files`. Both use the pinned
  hook binary; do not install a separate Vale, which would lint with a version
  the gate does not use.
- **Diagrams:** the site renders mermaid client-side, and `mermaid-parse` gates
  fence syntax against the version `docs/_config.yml` pins — so what needs
  saying here is what a parser cannot see. A diagram earns its place only where
  prose makes the reader assemble a structure: a graph, a branching flow, a
  state machine. Every node and edge traces to prose on the page; nothing the
  page marks Planned is drawn, and the diagram supplements the prose rather
  than replacing it. Never set per-fence `config:` or `theme:` frontmatter — the
  site theme is pinned deliberately and a fence that restyles itself drifts from
  it. Break labels with `<br/>`, and quote any label containing `()[]{}#;:,./`.

## Pull requests

Keep one scope per branch and PR. Each session works in its own worktree (see
[AGENTS.md](AGENTS.md)).

Before opening a PR:

- Reference the issue when one exists. Agents claim it first — see
  [AGENTS.md](AGENTS.md#issue-conventions), Issue conventions.
- Rebase on `origin/main`.
- Stage explicit paths — see [AGENTS.md](AGENTS.md#ground-truth), Ground truth.
- Run `python scripts/verify`.
- Open the PR against `main` and fill out the template.

Branch protection and merge policy are in [AGENTS.md](AGENTS.md#ground-truth),
Ground truth.

## Commit style

Commit-message format policy is in [AGENTS.md](AGENTS.md#ground-truth),
Ground truth. Clear, lowercase, imperative subjects are encouraged;
[Conventional Commits](https://www.conventionalcommits.org/) prefixes (`feat`,
`fix`, `docs`, `refactor`, `chore`, `test`, `research`) are a fine convention.

Call out breaking changes explicitly — CLI command or JSON-contract changes,
vault folder restructuring, provider/config field renames, and required
frontmatter contract changes — stating what changed, who is affected, what action
is required, and the replacement path.

## Releases and changelog

What a milestone means and where the per-release record lives are in
[AGENTS.md](AGENTS.md#where-things-live), Where things live.

There is no release automation right now: `CHANGELOG.md` is a hand-curated
dated record, and versioning, tags, and GitHub Releases return with release
tooling when distribution needs them. Do not hand-cut a release or hand-tag as
part of an ordinary PR.

## Questions?

Open a [GitHub Discussion](https://github.com/eranroseman/memoria-vault/discussions)
or file an issue. Leave labeling to triage — see [AGENTS.md](AGENTS.md#issue-conventions),
Issue conventions.
