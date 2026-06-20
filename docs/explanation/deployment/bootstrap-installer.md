---
title: Bootstrap installer
parent: Deployment
nav_order: 2
---

# Bootstrap installer

The bootstrap installers — [`scripts/install.ps1`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/install.ps1) for native Windows production and [`scripts/install.sh`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/install.sh) for Linux/WSL testing — take a user from nothing to a runnable Memoria install in one command: they scaffold and populate the vault from `src/`, stage the golden copy, provision the Hermes runtime and the five agent profiles, wire the crons, and guide Obsidian setup.

This page explains *why* the installer is shaped the way it is. The concrete inventories — platform matrix, install-flow steps, the component checklist, the secrets and skills tables — are reference material in [Installer (bootstrap)](../../reference/installer.md).

## Why a bootstrap

Before the bootstrap, the shipped installer did only one of the setup steps — register the Hermes profiles from an already-cloned repo. Everything else was manual and spread across five how-to guides, and a new user had to already have the whole stack installed before any of it worked. The gap was a single, guided first-run path — which is what the bootstrap is.

## The flow: scaffold, populate, golden copy

What the installer ships and stages — the `src/`-not-a-live-vault separation and the hashed `<vault>/.memoria/golden/` restore baseline — is the distribution mechanism, owned by [Distribution model](distribution-model.md). What the installer adds is the *flow* over that mechanism: **scaffold** the folder tree (checked against the machine-read folder map `.memoria/schemas/folders.yaml`), **populate** it from `src/`, **stage the golden copy**, then wire the pre-commit hook, install Hermes and the five profiles, offer the optional cluster stack, install Obsidian if absent, and wire the crons. The ordered install-flow steps, the component checklist, and the cron list are owned by [Installer (bootstrap)](../../reference/installer.md); the five-profile roster is [Profile capabilities](../../reference/profiles.md).

One installer-specific sequencing choice worth calling out: Zotero deliberately *left* the installer — it is the PI's bibliographic-backbone choice, not core provisioning, so its setup moved to the tutorial.

## Goals and non-goals

**Goals**

- One command from zero to a runnable vault on native Windows production and Linux/WSL testing.
- Fresh-install by default, with an idempotent per-profile deployment path (`scripts/install.sh --profiles-only`) for profile source and secret changes.
- Detect-then-install; never clobber existing apps, credentials, or user content.
- Honest about what it cannot do (secrets, GUI steps) — explain, don't fake.

**Non-goals**

- macOS, and Linux distros other than Ubuntu/Debian.
- Writing the user's API keys for them.
- Supporting macOS or non-Debian Linux distributions as first-class install targets.
- In-place migration between releases — releases are delivered fresh-install, per [ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md).

## Entry point and safety model

The installer is offered two ways, with **inspect-first as the documented primary** (download, read, then run) and the `curl | bash` / `irm | iex` one-liner shown only as the convenience option. The standard precautions for a piped installer are applied: the entire script body is wrapped in a `main` function invoked on the last line, so a truncated download cannot execute a half-command; it prints a numbered plan and prompts for consent (skippable with `--yes` for CI); `--dry-run` prints every action without executing; and it never silently elevates — if a step needs `sudo`/admin it stops and prints the exact command. These rails are cheap insurance for a script that installs system software, and `--dry-run` doubles as the WSL command transcript (below).

## Production Windows and Linux testing

Per [ADR-64](../../adr/64-native-windows-support.md), Memoria now uses a
two-script platform split:

- **Windows production:** `scripts/install.ps1` is the native Windows installer. It runs the official Hermes Windows installer, copies `src/` into the production vault, creates the vault-local MCP venv, deploys profiles and the policy-gate plugin, and wires Hermes crons.
- **Linux/WSL testing:** `scripts/install.sh` remains the Linux/WSL test installer and CI/disposable-vault path.

This removes the old production WSL bridge: no `/mnt/c` vault path, no WSL2
gate in the PowerShell installer, and no `windowsWslMode` requirement for the
ACP pane on production Windows. WSL-specific docs still use mirrored networking
when validating the Linux/WSL test path against Windows Obsidian.

## Architecture: two installers, one source tree

There are two installers because production and testing deliberately run on
different operating systems:

- **`scripts/install.ps1` (PowerShell)** is the native Windows production installer. It owns Windows app guidance, Hermes native install, vault population, MCP deps, profile deployment, policy plugin deployment, and cron wiring.
- **`scripts/install.sh` (bash)** is the Linux/WSL testing installer. It keeps the same vault/profile contracts so CI and disposable Linux validation exercise the same authored source under `src/`.

Both files live at the repo root because the bootstrap is the clone/entry point,
not a vault-internal artifact. The duplication is intentional at the shell
boundary; shared behavior stays in the deployed vault source and deterministic
Python operations.

## Simplifying decisions

Each trades a little breadth for much less shell to build and maintain:

- **Guide app install, don't fully automate.** Detect Obsidian; if absent, print the exact `winget`/`apt` one-liner and run it on consent — no version parsing, no silent installs.
- **Presence checks, not version gates.** Check a tool is there; let `pip`/Hermes surface a clear error if it is too old.
- **Don't install language runtimes.** The Hermes installer provisions uv, Python, Node, ripgrep, and ffmpeg; the bootstrap adds only **Git** (pre-Hermes) and **Pandoc** (not provisioned by Hermes).
- **Assume `local-only` deployment.** No Syncthing/VPS/sync logic — multi-device is a later phase.
- **Default the vault off OneDrive** (`%USERPROFILE%\Memoria` on Windows, `~/Memoria` on Linux; prompt to override) — OneDrive fights Obsidian indexes and file locks, and Git is the backup, so losing OneDrive sync of the vault is fine.
- **The vault's git repo is the user's own.** The installer never `git init`s under a synthetic author; it prints the commands and the user commits with their own identity.

## Trade-offs

- **Surface area** is still nontrivial (WSL2 orchestration, cron wiring), cut hard by the simplifying decisions above; the residue leans on upstream installers and on guidance for the secret steps that genuinely can't be automated.
- **`curl | bash` trust** is inherent to the pattern; mitigated by inspect-first framing, the `main`-guard, consent, and `--dry-run`.
- **Partial automation can imply full automation** — the secrets steps are assisted, not automatic, so the UX must make that explicit.
- **Fresh release installs replace in-place migration.** This keeps the bootstrap small and avoids half-migrated vault states; profile redeploy remains the narrow idempotent path.

## Related

- **Reference:** [Installer (bootstrap)](../../reference/installer.md) — platform matrix, install-flow steps, component checklist, secrets and skills tables.
- **Decisions:** [ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md) (src/ + scaffold-populate + golden copy), [ADR-26](../../adr/26-repo-as-install-unit.md) (the repo is the install unit).
- **Explanation:** [Distribution model](distribution-model.md), [Why Hermes](../rationale/why-hermes.md) (the runtime the installer provisions).
- **How-to:** [Quickstart](../../how-to-guides/setup/quickstart.md), [Tutorial 01: Set up from zero](../../tutorials/01-set-up-from-zero.md).
