# 0.1.0-beta.1 Decisions

This ledger captures release-time decisions as dated Y-statements. Historical
notes, ADRs, and design documents are evidence; the implemented system and this
release ledger are the decision-time record until the release closes into
`design-history/`.

## 2026-07-05 - Living design history replaces ADRs

Y: Memoria will retire `docs/adr/` as the live decision mechanism and use
release decision ledgers plus `design-history/` instead.

Because: alpha.1 through alpha.15 repeatedly reversed earlier architecture, so a
live ADR set makes older opinions look authoritative after implementation has
moved. Frozen release chapters preserve the facts, while `arcs.md` states the
current released line and pending unreleased work.

Pointers:
- Evidence: `scratch/design-history/memoria-design-history-alpha.1-to-alpha.15.md`
- Implementation target: `design-history/`
- Workflow target: `AGENTS.md`, `.agents/`

Status: accepted for the workflow-audit implementation.

## 2026-07-05 - Pinned pre-commit environments define third-party lint tools

Y: Memoria will pin ruff, ruff-format, yamllint, shellcheck, and gitleaks in
`.pre-commit-config.yaml`, and CI will run those same pre-commit hooks.

Because: the previous design pinned some tools in `requirements-dev.txt` while
CI used separate installers or Docker commands. That made local and CI behavior
depend on different installation paths. Pre-commit hook environments give one
versioned source for local commits and CI checks.

Pointers:
- Hook contract: `.pre-commit-config.yaml`
- CI callers: `.github/workflows/lint.yml`,
  `.github/workflows/lint-config.yml`, `.github/workflows/lint-installers.yml`,
  `.github/workflows/gitleaks.yml`
- Local setup: `scripts/dev/setup.sh`, `mise.toml`

Status: accepted for the workflow-audit implementation.
