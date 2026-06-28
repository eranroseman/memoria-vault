---
title: Bootstrap installer
parent: Design Book
grand_parent: Developers
nav_order: 25
---

# Bootstrap installer

The bootstrap installers — [`scripts/install.ps1`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/install.ps1) for native Windows production and [`scripts/install.sh`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/install.sh) for Linux/WSL testing — take a user from nothing to a runnable Memoria install in one command: they scaffold and populate the vault from `src/`, stage the golden copy, provision the Hermes runtime and the five agent profiles, wire the crons, and guide Obsidian setup.

This page explains *why* the installer is shaped the way it is. The concrete inventories — platform matrix, install-flow steps, the component checklist, the secrets and skills tables — are reference material in [Installer (bootstrap)](../reference/installer.md).

## Why a bootstrap

Before the bootstrap, the shipped installer did only one of the setup steps — register the Hermes profiles from an already-cloned repo. Everything else was manual and spread across five how-to guides, and a new user had to already have the whole stack installed before any of it worked. The gap was a single, guided first-run path — which is what the bootstrap is.

## The flow: scaffold, populate, golden copy

The distribution mechanism is `src/` plus the hashed `<vault>/.memoria/golden/` restore baseline ([Distribution model](distribution-model.md)). The installer adds the flow:

| Step | Purpose |
| --- | --- |
| Scaffold | Create the folder tree from `.memoria/schemas/folders.yaml`. |
| Populate | Copy system files from `src/`. |
| Stage golden copy | Save the restore baseline. |
| Wire runtime | Add the pre-commit hook, Hermes profiles, optional cluster stack, Obsidian guidance, and crons. |

Ordered steps, component checklist, and cron list are owned by [Installer (bootstrap)](../reference/installer.md); the profile roster is [Profile capabilities](../reference/profile-capabilities.md).

One installer-specific sequencing choice worth calling out: Zotero deliberately *left* the installer — it is the PI's bibliographic-backbone choice, not core provisioning, so its setup moved to the tutorial.

The install contract is narrow: fresh install by default, idempotent profile
redeploy for source/secret changes, detect-then-install, no clobbering user
content, no writing secrets, and no in-place release migration
([ADR-55](../adr/55-src-scaffold-populate-golden-copy.md)).

## Entry point and safety model

The primary path is inspect-first: download, read, then run. The one-liner is convenience only.

| Risk | Rail |
| --- | --- |
| Truncated piped download | Script body lives in `main`, invoked only at the last line. |
| Surprise actions | Numbered plan plus consent prompt; `--yes` is for CI. |
| Unclear effects | `--dry-run` prints actions without executing them. |
| Silent elevation | The installer stops and prints the exact `sudo`/admin command. |

## Production Windows and Linux testing

Per [ADR-64](../adr/64-native-windows-support.md), Memoria uses a two-script
platform split:

- **Windows production:** `scripts/install.ps1` is the native Windows installer. It runs the official Hermes Windows installer, copies `src/` into the production vault, creates the vault-local MCP venv, deploys profiles and the policy-gate plugin, and wires Hermes crons.
- **Linux/WSL testing:** `scripts/install.sh` remains the Linux/WSL test installer and CI/disposable-vault path.

The production path has no `/mnt/c` vault path, no WSL2 gate in the PowerShell
installer, and no `windowsWslMode` requirement for the Agent Client pane on production
Windows. WSL-specific test docs open the ext4 test vault with Linux Obsidian on
the native path; mirrored networking is only relevant for an explicit split
where WSL Hermes talks to Windows Obsidian serving a Windows-hosted vault.

## Simplifying decisions

Each trades breadth for less installer code:

| Choice | Keeps out |
| --- | --- |
| Guide app installs instead of fully automating them | Version parsing and silent installs. |
| Presence checks instead of version gates | Duplicating upstream installer logic. |
| Do not install language runtimes | Competing with Hermes for uv, Python, Node, ripgrep, and ffmpeg. |
| Assume `local-only` deployment | Syncthing/VPS/sync branching. |
| Default vaults off OneDrive | Obsidian index and file-lock conflicts. |
| Leave git identity to the user | Synthetic authorship and installer-owned repos. |

## Trade-offs

| Trade-off | Accepted cost |
| --- | --- |
| Native Windows plus Linux/WSL installers | More surface area, reduced by leaning on upstream installers. |
| One-line installer option | Inherent trust cost, mitigated by inspect-first docs and `--dry-run`. |
| Assisted secrets setup | The UX must say when automation stops. |
| Fresh release installs | No in-place migrations; profile redeploy remains the idempotent path. |

## Related

- **Reference:** [Installer (bootstrap)](../reference/installer.md) — platform matrix, install-flow steps, component checklist, secrets and skills tables.
- **Decisions:** [ADR-55](../adr/55-src-scaffold-populate-golden-copy.md) (src/ + scaffold-populate + golden copy), [ADR-26](../adr/26-repo-as-install-unit.md) (the repo is the install unit).
- **Design:** [Distribution model](distribution-model.md), [Why Hermes](why-hermes.md) (the runtime the installer provisions).
- **How-to:** [Quickstart](../how-to-guides/setup/quickstart.md), [Set up the vault](../how-to-guides/setup/set-up-the-vault.md).
