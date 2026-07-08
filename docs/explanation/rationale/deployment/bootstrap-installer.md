---
title: Bootstrap installer
parent: Deployment rationale
grand_parent: Design rationale
nav_order: 2
---

# Bootstrap installer

The bootstrap installers take a user from nothing to a runnable Memoria install in one command. [`scripts/install.sh`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/install.sh) and [`scripts/install.ps1`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/install.ps1) create the workspace, install the `memoria` package into the vault-local venv, initialize the vault from the packaged workspace seed, and wire local integrity hooks. The standalone baseline does not install external search tooling, Hermes profiles, Hermes crons, the Obsidian app, or live Zotero integration; the package seed does include Memoria's default Obsidian plugin/settings.

This page explains *why* the installer is shaped the way it is. The concrete inventories — platform matrix, install-flow steps, the component checklist, the secrets and skills tables — are reference material in [Installer (bootstrap)](../../../reference/system/installer.md).

## Why a bootstrap

Before the bootstrap, the shipped installer did only one of the setup steps — register the Hermes profiles from an already-cloned repo. Everything else was manual and spread across five how-to guides, and a new user had to already have the whole stack installed before any of it worked. The gap was a single, guided first-run path — which is what the bootstrap is.

## The shape of the flow

The distribution mechanism is the packaged workspace seed plus the installed Memoria package ([Distribution model](distribution-model.md)). The installer adds the flow:
create a workspace, initialize it from the package seed, and wire the local runtime.
Ordered steps and the component checklist are owned by [Installer (bootstrap)](../../../reference/system/installer.md).

One installer-specific sequencing choice worth calling out: Zotero stays outside
the installer. It is an optional import/export workflow, not core provisioning,
so its setup lives in the dedicated Zotero how-to. Hermes also stays outside the
installer baseline: optional adapters may wrap the CLI/engine, but this bootstrap
path is standalone.

The install contract is narrow: fresh install, detect-then-install, no
clobbering user content, no writing secrets, and no in-place release migration.

## Entry point and safety model

The primary path is inspect-first: download, read, then run. The one-liner is convenience only.
The safety model is deliberately boring: show the plan, ask before acting, make
dry-run possible, and stop instead of silently escalating privileges.

## Standalone-only bootstrap

Both supported installer entry points install the standalone CLI/runtime
workspace. Editor adapters and external runtime experiments are separate from the
bootstrap contract and must not reintroduce installed profiles or profile-only
redeploy modes into the core installer.

## Simplifying decisions

Each trades breadth for less installer code. The installer avoids app installs,
upstream version parsing, sync topology branching, and synthetic Git identity.
Those are setup choices the user can make after the core workspace works.

## Trade-offs

The accepted cost is clear: users who want optional adapters, live-provider
secrets, or migration behavior need separate setup. The benefit is a core install
path with one mental model.

## Related

- **Reference:** [Installer (bootstrap)](../../../reference/system/installer.md) — platform matrix, install-flow steps, component checklist, secrets and skills tables.
- **Decisions:** [alpha.15 standalone engine checkpoint](https://github.com/eranroseman/memoria-vault/blob/main/design-history/15-alpha.15.md) (standalone CLI + engine; absorbs the former repo-as-install-unit decision).
- **Design:** [Distribution model](distribution-model.md).
- **How-to:** [Quickstart](../../../how-to-guides/setup/quickstart.md), [Set up the vault](../../../how-to-guides/setup/set-up-the-vault.md).
