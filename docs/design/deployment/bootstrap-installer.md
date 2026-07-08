---
title: Bootstrap installer
parent: Deployment
grand_parent: Design
nav_order: 2
---

# Bootstrap installer

The bootstrap installers take a user from nothing to a runnable Memoria install in one command. [`scripts/install.sh`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/install.sh) and [`scripts/install.ps1`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/install.ps1) scaffold and populate the vault from `vault-template/`, install the `memoria` package into the vault-local venv, and wire local integrity hooks. The standalone baseline does not install external search tooling, Hermes profiles, Hermes crons, Obsidian setup, or live Zotero integration.

This page explains *why* the installer is shaped the way it is. The concrete inventories — platform matrix, install-flow steps, the component checklist, the secrets and skills tables — are reference material in [Installer (bootstrap)](../../reference/installer.md).

## Why a bootstrap

Before the bootstrap, the shipped installer did only one of the setup steps — register the Hermes profiles from an already-cloned repo. Everything else was manual and spread across five how-to guides, and a new user had to already have the whole stack installed before any of it worked. The gap was a single, guided first-run path — which is what the bootstrap is.

## The shape of the flow

The distribution mechanism is `vault-template/` plus the installed Memoria package ([Distribution model](distribution-model.md)). The installer adds the flow:
create a workspace, populate it from the template, and wire the local runtime.
Ordered steps and the component checklist are owned by [Installer (bootstrap)](../../reference/installer.md).

One installer-specific sequencing choice worth calling out: Zotero deliberately
*left* the installer — it is an optional import/export adapter, not core
provisioning, so its setup lives in the dedicated Zotero how-to. Hermes likewise left the
installer baseline: optional adapters may wrap the CLI/engine later, but this
bootstrap path is standalone.

The install contract is narrow: fresh install, detect-then-install, no
clobbering user content, no writing secrets, and no in-place release migration.

## Entry point and safety model

The primary path is inspect-first: download, read, then run. The one-liner is convenience only.
The safety model is deliberately boring: show the plan, ask before acting, make
dry-run possible, and stop instead of silently escalating privileges.

## Standalone-only bootstrap

Both supported installer entry points install the standalone CLI/runtime
workspace. Any future editor adapter or external runtime experiment is separate
from the bootstrap contract and must not reintroduce installed profiles or
profile-only redeploy modes into the core installer.

## Simplifying decisions

Each trades breadth for less installer code. The installer avoids app installs,
upstream version parsing, sync topology branching, and synthetic Git identity.
Those are setup choices the user can make after the core workspace works.

## Trade-offs

The accepted cost is clear: users who want optional adapters, live-provider
secrets, or future migration behavior need separate setup. The benefit is a core
install path with one mental model.

## Related

- **Reference:** [Installer (bootstrap)](../../reference/installer.md) — platform matrix, install-flow steps, component checklist, secrets and skills tables.
- **Decisions:** [alpha.15 standalone engine checkpoint](https://github.com/eranroseman/memoria-vault/blob/main/design-history/15-alpha.15.md) (standalone CLI + engine; absorbs the former repo-as-install-unit decision).
- **Design:** [Distribution model](distribution-model.md), Hermes boundary.
- **How-to:** [Quickstart](../../how-to-guides/setup/quickstart.md), [Set up the vault](../../how-to-guides/setup/set-up-the-vault.md).
