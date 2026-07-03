---
title: Bootstrap installer
parent: Design Book
grand_parent: Developers
nav_order: 25
---

# Bootstrap installer

The bootstrap installers take a user from nothing to a runnable Memoria install in one command. [`scripts/install.sh`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/install.sh) and [`scripts/install.ps1`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/install.ps1) scaffold and populate the vault from `vault-template/`, install the `memoria` package into the vault-local venv, register qmd search, and wire local integrity hooks. Alpha.15 does not install Hermes profiles, Hermes crons, Obsidian setup, or live Zotero integration.

This page explains *why* the installer is shaped the way it is. The concrete inventories — platform matrix, install-flow steps, the component checklist, the secrets and skills tables — are reference material in [Installer (bootstrap)](../reference/installer.md).

## Why a bootstrap

Before the bootstrap, the shipped installer did only one of the setup steps — register the Hermes profiles from an already-cloned repo. Everything else was manual and spread across five how-to guides, and a new user had to already have the whole stack installed before any of it worked. The gap was a single, guided first-run path — which is what the bootstrap is.

## The flow: scaffold, populate, install package

The distribution mechanism is `vault-template/` plus the installed Memoria package ([Distribution model](distribution-model.md)). The installer adds the flow:

| Step | Purpose |
| --- | --- |
| Scaffold | Create the folder tree from `.memoria/schemas/folders.yaml`. |
| Populate | Copy system files from `vault-template/`. |
| Wire runtime | Initialize Git, add the pre-commit hook, create the vault-local venv, install the Memoria package, and register qmd search. |

Ordered steps and the component checklist are owned by [Installer (bootstrap)](../reference/installer.md); the no-installed-profile contract is [Installed profiles](../reference/profile-capabilities.md).

One installer-specific sequencing choice worth calling out: Zotero deliberately
*left* the installer — it is an optional import/export adapter, not core
provisioning, so its setup moved to the tutorial. Hermes likewise left the
installer baseline: optional adapters may wrap the CLI/engine later, but this
bootstrap path is standalone.

The install contract is narrow: fresh install, detect-then-install, no
clobbering user content, no writing secrets, and no in-place release migration.

## Entry point and safety model

The primary path is inspect-first: download, read, then run. The one-liner is convenience only.

| Risk | Rail |
| --- | --- |
| Truncated piped download | Script body lives in `main`, invoked only at the last line. |
| Surprise actions | Numbered plan plus consent prompt; `--yes` is for CI. |
| Unclear effects | `--dry-run` prints actions without executing them. |
| Silent elevation | The installer stops and prints the exact `sudo`/admin command. |

## Standalone-only bootstrap

- **Linux/WSL default:** `scripts/install.sh` installs the standalone CLI/runtime workspace.
- **Windows default:** `scripts/install.ps1` installs the standalone CLI/runtime workspace.

The production path has no `/mnt/c` vault path and no WSL2 gate in the
PowerShell installer. Any future editor adapter or external runtime experiment is
separate from the bootstrap contract and must not reintroduce installed profiles
or profile-only redeploy modes into the core installer.

## Simplifying decisions

Each trades breadth for less installer code:

| Choice | Keeps out |
| --- | --- |
| Guide app installs instead of fully automating them | Version parsing and silent installs. |
| Presence checks instead of version gates | Duplicating upstream installer logic. |
| Use Python venv and npm qmd directly | Depending on Hermes to supply the core runtime. |
| Assume `local-only` deployment | Syncthing/VPS/sync branching. |
| Default vaults off OneDrive | Obsidian index and file-lock conflicts. |
| Leave git identity to the user | Synthetic authorship and installer-owned repos. |

## Trade-offs

| Trade-off | Accepted cost |
| --- | --- |
| Standalone-only installer | Users who want an external adapter need a separate adapter setup later, but the core install has one path. |
| One-line installer option | Inherent trust cost, mitigated by inspect-first docs and `--dry-run`. |
| Assisted secrets setup | The UX must say when automation stops. |
| Fresh release installs | No in-place migrations or profile redeploy modes. |

## Related

- **Reference:** [Installer (bootstrap)](../reference/installer.md) — platform matrix, install-flow steps, component checklist, secrets and skills tables.
- **Decisions:** [ADR-125](../adr/125-standalone-cli-engine-architecture.md) (standalone CLI + engine), [ADR-26](../adr/26-repo-as-install-unit.md) (historical repo install unit).
- **Design:** [Distribution model](distribution-model.md), [Hermes boundary](why-hermes.md).
- **How-to:** [Quickstart](../how-to-guides/setup/quickstart.md), [Set up the vault](../how-to-guides/setup/set-up-the-vault.md).
