---
title: Installer (bootstrap)
parent: Reference
nav_order: 39
---

# Installer (bootstrap)

The bootstrap installers (`scripts/install.sh` for Linux/WSL and
`scripts/install.ps1` for Windows) create a standalone Memoria CLI/runtime
workspace. They do not install Hermes profiles, lane overrides, Obsidian setup, or
live Zotero integration.

The install model is **prepare target -> install package -> initialize
workspace**: the installer creates the target folder, installs the CLI package
into the workspace venv, runs `memoria init` so the package seed creates the
runtime-required files and schema-owned folders, and wires local Git hooks.
Product-file repair is `memoria doctor --repair` or a package reinstall, not a
repo tree copy.

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
| Runtime dependencies | Creates `<workspace>/.memoria/.venv`, upgrades pip, then installs the Memoria Python package from the repo. |
| Workspace init | Runs the installed `memoria init --workspace <workspace> --yes`, which copies the package seed and creates schema-owned folders from `folders.yaml`. The installer refuses an existing Memoria workspace. |
| Git hooks | Initializes Git when needed and wires `.githooks/pre-commit`. The installer never commits, sets identity, or adds a remote. File-change work is observed with `memoria workspace scan`. |
| Next steps | Prints vault-local Python commands for `memoria doctor bundle`, `memoria workspace rebuild --search`, and `memoria ask`. |

## Scheduled Work

The installer does not register a host scheduler. Scheduled work is run through
ordinary CLI commands by whatever local scheduler the operator chooses. No cron
wrapper payload ships in the baseline workspace.

## Host Scheduler Wiring

None. The installer does not wire Hermes cron jobs or any other host scheduler during
bootstrap.

## User-Supplied Values

| Item | Where |
| --- | --- |
| Runtime provider keys | Shell environment or workspace runtime configuration consumed by the standalone CLI. |
| git binary + Git workspace | The host must have `git` on `PATH`; checkpoints, hooks, rollback, and history need the runtime workspace to be a repo. |
| Bibliography imports | Portable BibTeX/CSL files passed to `memoria work import`; no live reference-manager authority is installed. |

## Related

- Runtime layout: [On-disk layout](on-disk-layout.md)
- CLI commands: [CLI](cli.md)
- Search: [Search](search.md)
