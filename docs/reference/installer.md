---
title: Installer (bootstrap)
parent: System and infrastructure
grand_parent: Reference
---

# Installer (bootstrap)

The bootstrap installers (`scripts/install.sh` for Linux/WSL and
`scripts/install.ps1` for Windows) create a standalone Memoria CLI/runtime
workspace. They do not install Hermes profiles, lane overrides, Obsidian setup, or
live Zotero integration.

The install model is **scaffold -> populate -> install package**: the repo ships
the workspace template under `vault-template/`, the installer copies it to the
target workspace, recreates schema-owned empty folders from `folders.yaml`,
installs the CLI package into the workspace venv, wires local Git hooks, and
registers qmd search. Product-file repair is a package/template reinstall or
fresh workspace refresh.

## Flags

| Flag | Effect |
| --- | --- |
| `--vault DIR` / `-Vault DIR` | Install the runtime workspace here (default `~/Memoria` on Linux/WSL, `%USERPROFILE%\Memoria` on Windows). Pick a folder outside any cloud-synced tree. |
| `--dry-run` / `-DryRun` | Print commands that would run; change nothing where practical. |
| `--yes` / `-Yes` | Non-interactive: accept defaults and run guided installs. |

## Flow

| Step | What happens |
| --- | --- |
| Prerequisites | Ensures `git` and Python 3.12+ with venv support. `pandoc` is optional and only needed for DOCX/PDF exports. |
| Source | Uses the local checkout or clones `memoria-vault` to a temporary staging directory. |
| Workspace copy | Copies `vault-template/` into a fresh target. The installer refuses an existing Memoria workspace. |
| Skeleton | Recreates schema-owned empty folders from `folders.yaml`. |
| Runtime dependencies | Creates `<workspace>/.memoria/.venv`, upgrades pip, then installs the Memoria Python package from the repo. |
| Git hooks | Initializes Git when needed and wires `.githooks/pre-commit`. The installer never commits, sets identity, or adds a remote. File-change work is observed with `memoria workspace scan`. |
| qmd | Registers `.memoria/index/qmd/checked` as the checked-only qmd collection using workspace-local qmd config/index state. |
| Next steps | Prints vault-local Python commands for `memoria doctor bundle`, `memoria workspace rebuild --search`, and `memoria ask`. |

## Scheduled Work

The alpha.15 installer does not register a host scheduler. Scheduled work is run
through ordinary CLI commands by whatever local scheduler the operator chooses.
The shipped `.memoria/scripts/` wrappers remain template inputs for that later
wiring; they are not installed as Hermes cron jobs.

## Host Scheduler Wiring

None. Alpha.15 does not wire Hermes cron jobs or any other host scheduler during
bootstrap.

## User-Supplied Values

| Item | Where |
| --- | --- |
| Runtime provider keys | Shell environment or workspace runtime configuration consumed by the standalone CLI. |
| Optional qmd/Node runtime | Node >=22 plus `@tobilu/qmd`, or an equivalent bundled qmd path. |
| git binary + Git workspace | The host must have `git` on `PATH`; checkpoints, hooks, rollback, and history need the runtime workspace to be a repo. |
| Bibliography imports | Portable BibTeX/CSL files passed to `memoria work import`; no live reference-manager authority is installed. |

## Related

- Runtime layout: [On-disk layout](on-disk-layout.md)
- CLI commands: [CLI](cli.md)
- Search and qmd: [Search](search.md)
