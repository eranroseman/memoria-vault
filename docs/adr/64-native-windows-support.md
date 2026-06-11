---
topic: decisions
id: 64
title: "Native Windows support (deferred): the port approach"
status: deferred
nav_exclude: true
date_proposed: 2026-06-11
date_resolved:
assumes: [22, 26]
supersedes: []
superseded_by: []
parent: Decisions
grand_parent: Explanation
nav_order: 64
---

# ADR-64: Native Windows support (deferred): the port approach

## Context

Memoria's shipped Windows path is **WSL2-only**: Hermes and the Python engines run inside WSL2, while Windows hosts only the editing surface (Obsidian, Zotero, the vault files), reached across `/mnt/c` and a loopback bridge. `install.ps1` is a thin WSL2 launcher; `install.sh` is the real, apt-based bash installer.

That rule rested on two rationales that have since weakened:

1. **"Hermes is WSL2-only on Windows"** — the load-bearing reason. Nous's official docs now state Hermes runs natively on Windows 10/11 (no WSL, no Cygwin, no Docker), with a dedicated native installer that auto-provisions Python 3.11 / Node 22 / Git via `uv`. The one remaining WSL2-only Hermes feature is the dashboard's embedded-terminal pane, which needs a POSIX PTY.
2. **Windows build-pain for the analysis stack** — largely gone. Current pip wheels cover `umap-learn` (+ `numba`/`llvmlite`), `hdbscan`, `bertopic`, `torch` (CPU), and `faiss-cpu` on native Windows. That stack is also not shipped yet (it is the [ADR-33](33-cluster-mcp-bertopic.md) cluster MCP follow-up), so it is a non-blocker today.

This deferred ADR records the native-Windows direction so the chosen approach is fixed, without committing to build it now.

## Decision

**If native Windows is pursued, do it as a port that collapses the two-OS topology into one — not as a runtime flag.** The L5 MCP boundary and the seven-layer runtime stack stay unchanged; only the OS underneath changes. The port's scope:

- **Provisioning** — replace apt/bash `install.sh` (~981 lines, nine steps) with winget/`uv` provisioning, or wrap Hermes's own native installer; `install.ps1` becomes a real installer rather than a WSL2 launcher.
- **Scheduling** — move Hermes-internal cron + bash cron-wrappers to Windows Task Scheduler, or to an in-process scheduler (APScheduler) for one cross-platform codebase.
- **Always-on** — move the systemd gateway/tunnel services to Windows services.
- **Scripts** — port the bash cron-wrappers / dev / test / link-check scripts to PowerShell or cross-platform Python.

Adopting this would **supersede the WSL2-only rule** ([Bootstrap installer](../explanation/deployment/bootstrap-installer.md), the [installer platform matrix](../reference/installer.md)), **amend [ADR-26](26-repo-as-install-unit.md)** (`install.ps1` becomes a real installer), and **reinforce [ADR-22](22-build-on-hermes-runtime.md)** (Hermes is now native).

## Consequences

- A meaningful share of the work is *deletion*: native Windows removes the WSL2↔Windows boundary problems — the `networkingMode=mirrored` requirement for the Obsidian REST bridge ([ADR-31](31-native-obsidian-mcp.md)), `/mnt/c` cross-boundary file-lock fights, the OneDrive-breaks-WSL-locks hazard, the `/mnt/c` path translation in the ingest pipeline, `windowsWslMode` in the ACP pane, and the "VPS tunnel drops on WSL2 restart" failure mode. So the port is smaller than it first looks.
- It is still too large to swap into the v0.1.x workspace releases, which are written and tested for WSL2.
- Until adopted, WSL2-on-Windows remains the single supported, tested Windows path.

## When this matters

This is a deferral, not a gate — revisit when these hold, rather than on a fixed trigger:

- **Hermes native Windows is confirmed GA.** The claim comes from Nous's own docs; a third-party source still calls it experimental, and the project is young. Re-check `hermes-agent.nousresearch.com/docs/user-guide/windows-native` at decision time.
- **The v0.1.x workspace releases have shipped** (revisit after v0.1.2, with or after the UI phase) so re-platforming does not disrupt a tested build.
- **The ACP pane's dependency is settled** — confirm Memoria's pane needs only the native CLI/MCP and not Hermes's WSL2-only embedded-terminal pane, which decides whether the pane works natively.
- **Vector search, if [ADR-33](33-cluster-mcp-bertopic.md)'s stack ships.** Avoid base `hnswlib` on Windows: its sdist-only package needs MSVC to build. Swap to FAISS / `chroma-hnswlib` and pin Python 3.10–3.13.

## Related

- **Reinforced / assumed:** [ADR-22 build on Hermes](22-build-on-hermes-runtime.md) (Hermes is now native), [ADR-26 repo is the install unit](26-repo-as-install-unit.md) (`install.ps1` becomes a real installer).
- **Affected decisions:** [ADR-31 native Obsidian MCP](31-native-obsidian-mcp.md) (bridge simplifies on one OS), [ADR-33 cluster MCP](33-cluster-mcp-bertopic.md) (the Windows wheel edge).
- **Installer shape:** [Installer (bootstrap)](../reference/installer.md), [Bootstrap installer](../explanation/deployment/bootstrap-installer.md) (the WSL2-only rule this would supersede).
- **Tracking issue:** [#414](https://github.com/eranroseman/memoria-vault/issues/414) — revisit at each release cadence.
