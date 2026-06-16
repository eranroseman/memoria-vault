---
topic: decisions
id: 64
title: "Native Windows support: production on Windows, testing on Linux"
status: accepted
date_proposed: 2026-06-11
date_resolved: 2026-06-16
assumes: [22, 26]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 64
---

# ADR-64: Native Windows support: production on Windows, testing on Linux

## Context

Memoria's first shipped Windows path was **WSL2-only**: Hermes and the Python operations ran inside WSL2, while Windows hosted only the editing surface (Obsidian, Zotero, the vault files), reached across `/mnt/c` and a loopback bridge. `install.ps1` was a thin WSL2 launcher; `install.sh` was the real, apt-based bash installer.

That rule rested on two rationales that have since weakened:

1. **"Hermes is WSL2-only on Windows"** — no longer true. Nous's current official docs state Hermes runs natively on Windows 10/11 (no WSL, no Cygwin, no Docker), with a dedicated native installer that auto-provisions Python 3.11 / Node 22 / PortableGit. The feature matrix shows native CLI, TUI, gateway, cron scheduler, MCP stdio/HTTP, browser tool, dashboard, and login auto-start. The only called-out missing feature is the dashboard `/chat` embedded terminal pane, which needs a POSIX PTY; Memoria's Obsidian ACP pane does not depend on that pane.
2. **Windows build-pain for the analysis stack** — largely gone. Current pip wheels cover `umap-learn` (+ `numba`/`llvmlite`), `hdbscan`, `bertopic`, `torch` (CPU), and `faiss-cpu` on native Windows. That stack is also not shipped yet (it is the [ADR-33](33-cluster-mcp-bertopic.md) cluster MCP follow-up), so it is a non-blocker today.

The alpha.4 decision is to stop treating WSL2 as the production Windows runtime.
Production installs run natively on Windows; Linux/WSL remains the test harness
and developer validation path.

> **Cadence review (2026-06-16, v0.1.0-alpha.4): accepted.** The live Hermes
> Windows Native guide documents native Windows support for the runtime surfaces
> Memoria uses. This supersedes the WSL2-only rule and folds the broader
> migration tracked in [#296](https://github.com/eranroseman/memoria-vault/issues/296)
> into the native production installer.

## Decision

**Native Windows is the production runtime. Linux/WSL is the testing runtime.**
Do the port as a two-script split, not as a runtime flag:

- **Production provisioning** — `scripts/install.ps1` is a native Windows installer. It wraps Hermes's native Windows installer, lays down the vault from `src/`, creates the vault-local MCP venv, deploys the five profiles with Windows paths, propagates `.env` values, deploys the policy-gate plugin, and wires Hermes cron wrappers.
- **Testing provisioning** — `scripts/install.sh` remains the Linux/WSL test installer. It is the path CI and disposable Linux/WSL validation use.
- **Scheduling and always-on** — use Hermes's native Windows gateway and cron support. The deterministic wrappers remain shared for now and execute through Hermes's Windows shell strategy.
- **Bridge removal** — the production path has no `/mnt/c` translation, no WSL2 gate, and no `windowsWslMode` requirement for ACP. The WSL bridge remains only in WSL-specific test docs.

This **supersedes the WSL2-only rule** ([Bootstrap installer](../explanation/deployment/bootstrap-installer.md), the [installer platform matrix](../reference/installer.md)), **amends [ADR-26](26-repo-as-install-unit.md)** (`install.ps1` is a real installer), and **reinforces [ADR-22](22-build-on-hermes-runtime.md)** (Memoria builds on Hermes rather than reimplementing a runtime).

## Consequences

- Native Windows removes the WSL2↔Windows boundary problems — the `networkingMode=mirrored` production requirement for the Obsidian REST bridge ([ADR-31](31-native-obsidian-mcp.md)), `/mnt/c` cross-boundary file-lock fights, OneDrive/WSL lock interactions, `/mnt/c` path translation, and `windowsWslMode` in the ACP pane.
- The Linux/WSL path remains valuable, but as a test environment rather than the production Windows recommendation.
- Live Windows verification is still required before declaring a release candidate green; the architectural blocker is gone.

## Follow-up verification

- Run `scripts/install.ps1 -DryRun` and a full attended native Windows install against a disposable vault before release-candidate signoff.
- Confirm ACP launches `hermes` natively with `windowsWslMode: false`.
- Confirm the verified HTTPS Obsidian MCP works with `OBSIDIAN_MCP_SSL_VERIFY`.
- If [ADR-33](33-cluster-mcp-bertopic.md)'s stack ships, avoid base `hnswlib` on Windows: its sdist-only package needs MSVC to build. Swap to FAISS / `chroma-hnswlib` and pin Python 3.10-3.13.

## Related

- **Reinforced / assumed:** [ADR-22 build on Hermes](22-build-on-hermes-runtime.md) (Hermes is now native), [ADR-26 repo is the install unit](26-repo-as-install-unit.md) (`install.ps1` becomes a real installer).
- **Affected decisions:** [ADR-31 native Obsidian MCP](31-native-obsidian-mcp.md) (bridge simplifies on one OS), [ADR-33 cluster MCP](33-cluster-mcp-bertopic.md) (the Windows wheel edge).
- **Installer shape:** [Installer (bootstrap)](../reference/installer.md), [Bootstrap installer](../explanation/deployment/bootstrap-installer.md) (the WSL2-only rule this would supersede).
- **Tracking issue:** [#414](https://github.com/eranroseman/memoria-vault/issues/414) — revisit at each release cadence.
