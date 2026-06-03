# Changelog

All notable changes to Memoria are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Working toward the first tagged release, **v0.1.0** — **not yet cut.** No
`v0.1.0` tag or GitHub release exists; see the release gate in
[project-files/releases/v0.1/release-plan-v0.1.md](project-files/releases/v0.1/release-plan-v0.1.md).

### Added
- Seven specialist agent profiles: `librarian`, `mapper`, `socratic`, `writer`, `verifier`, `coder`, `linter`
- Obsidian starter vault (`vault/`) with the `.memoria/` tooling layer; Diátaxis engineering docs in `docs/`
- `scripts/install.sh` (Ubuntu/WSL2 bootstrap) and `scripts/install.ps1` (thin Windows → WSL2 launcher)
- Policy MCP write-gate + `policy_hook.py` pre/post tool-call hook (the structural review gate)
- Six-signal telemetry capture (`board_export.py`, `metrics_aggregate.py`, Linter `detectors.py`)
- CI required checks: `docs-doctor`, `shellcheck (scripts/install.sh)`, `PSScriptAnalyzer (scripts/install.ps1)`, `python-selftest`, `docs-links`
- Repo health: GitHub issue/PR templates, `CODEOWNERS`, `FUNDING.yml`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `LICENSE` (MIT), and `AGENTS.md` (agent workflow guidelines)

### Fixed

- Obsidian MCP bridge now receives its API key in live Hermes runs
  ([#39](https://github.com/eranroseman/memoria-vault/issues/39)) — the prior
  v0.1 release blocker; live HTTP 204 vault write confirmed (see ADR-27).

[Unreleased]: https://github.com/eranroseman/memoria-vault/commits/main
