---
topic: decisions
id: 64
title: "Native Windows support"
nav_exclude: true
status: accepted
date_proposed: 2026-06-11
date_resolved: 2026-06-16
assumes: [22, 26]
supersedes: []
superseded_by: []
---

# ADR-64: Native Windows support

## Context

Memoria's first shipped Windows path was **WSL2-only**: Hermes and the Python operations ran inside WSL2, while Windows hosted only the editing surface (Obsidian, Zotero, the vault files), reached across `/mnt/c` and a loopback bridge. `install.ps1` was a thin WSL2 launcher; `install.sh` was the real, apt-based bash installer.

That rule rested on two rationales that have since weakened:

1. **"Hermes is WSL2-only on Windows"** — no longer true. Nous's current official docs state Hermes runs natively on Windows 10/11 (no WSL, no Cygwin, no Docker), with a dedicated native installer that auto-provisions Python 3.11 / Node 22 / PortableGit. The feature matrix shows native CLI, TUI, gateway, cron scheduler, MCP stdio/HTTP, browser tool, dashboard, and login auto-start. The only called-out missing feature is the dashboard `/chat` embedded terminal pane, which needs a POSIX PTY; Memoria's Obsidian ACP pane does not depend on that pane.
2. **Windows build-pain for the analysis stack** — largely gone. Current pip wheels cover `umap-learn` (+ `numba`/`llvmlite`), `hdbscan`, `bertopic`, `torch` (CPU), and `faiss-cpu` on native Windows. That stack is also not shipped yet (it is the [ADR-125](125-standalone-cli-engine-architecture.md) cluster MCP follow-up), so it is a non-blocker today.

The alpha.4 decision was to stop treating WSL2 as the production Windows
runtime. Alpha.14 keeps that Windows-native support, but the default installer
runtime is now the standalone Memoria CLI/engine on both Windows and Linux/WSL;
Hermes is an optional adapter.

> **Cadence review (2026-06-16, 0.1.0-alpha.4): accepted.** The live Hermes
> Windows Native guide documents native Windows support for the runtime surfaces
> Memoria uses. This supersedes the WSL2-only rule and folds the broader
> migration tracked in [#296](https://github.com/eranroseman/memoria-vault/issues/296)
> into the native production installer.

## Decision

**Native Windows is supported without WSL2.** Keep two platform installers, but
make the standalone CLI/runtime the default on both:

- **Windows provisioning** — `scripts/install.ps1` is a native Windows installer. It lays down the vault from `vault-template/`, creates the vault-local runtime venv, installs the Memoria package, wires Git hooks, and registers qmd search. It does not carry a `-WithHermes` mode in alpha.15.
- **Linux/WSL provisioning** — `scripts/install.sh` installs the same standalone CLI/runtime workspace. It does not carry a `--with-hermes` adapter mode in alpha.15.
- **Scheduling and always-on** — the standalone runtime exposes deterministic CLI/worker commands and can be invoked manually, by file-change hooks, or by any external scheduler. Hermes cron support is not an alpha.15 installer surface.
- **Bridge removal** — the production path has no `/mnt/c` translation, no WSL2 gate, and no `windowsWslMode` requirement for ACP. The WSL bridge remains only in WSL-specific test docs.

This **supersedes the WSL2-only rule** ([Bootstrap installer](../design/bootstrap-installer.md), the [installer platform matrix](../reference/installer.md)), **amends [ADR-125](125-standalone-cli-engine-architecture.md)** (`install.ps1` is a real installer), and **narrows [ADR-125](125-standalone-cli-engine-architecture.md)** to the optional adapter path.

## Consequences

- Native Windows removes the WSL2↔Windows boundary problems — the `networkingMode=mirrored` production requirement for the Obsidian REST bridge ([ADR-130](130-read-api-surfaces-and-copi.md)), `/mnt/c` cross-boundary file-lock fights, OneDrive/WSL lock interactions, `/mnt/c` path translation, and `windowsWslMode` in the ACP pane.
- Linux/WSL remains valuable for CI and disposable validation, but it is no longer the only standalone installer path.
- Live Windows verification is still required before declaring a release candidate green; the architectural blocker is gone.

## Follow-up verification

- Run `scripts/install.ps1 -DryRun` and a full attended native Windows standalone install against a disposable vault before release-candidate signoff.
- Keep `-WithHermes` / `--with-hermes` absent from the alpha.15 installers until a future adapter ADR adds and tests that surface.
- If [ADR-125](125-standalone-cli-engine-architecture.md)'s stack ships, avoid base `hnswlib` on Windows: its sdist-only package needs MSVC to build. Swap to FAISS / `chroma-hnswlib` and pin Python 3.10-3.13.

## Related

- **Reinforced / assumed:** [ADR-125 (standalone CLI + engine)](125-standalone-cli-engine-architecture.md) (`install.ps1` becomes a real installer); [ADR-125 (standalone CLI + engine)](125-standalone-cli-engine-architecture.md) only for the optional adapter.
- **Affected decisions:** [ADR-130 (read-API surfaces)](130-read-api-surfaces-and-copi.md) (bridge simplifies on one OS), [ADR-125 (standalone CLI + engine)](125-standalone-cli-engine-architecture.md) (the Windows wheel edge).
- **Installer shape:** [Installer (bootstrap)](../reference/installer.md), [Bootstrap installer](../design/bootstrap-installer.md) (the WSL2-only rule this would supersede).
- **Tracking issue:** [#414](https://github.com/eranroseman/memoria-vault/issues/414) — revisit at each release cadence.
