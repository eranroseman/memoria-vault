---
topic: explorations
title: Native Windows vs WSL2 — platform reevaluation
status: exploration
created: 2026-06-09
parent: Design notes
grand_parent: Explanation
nav_order: 26
nav_exclude: true
---

# Native Windows vs WSL2 — platform reevaluation

> **Status: exploration.** A reevaluation of the v0.2 platform rule (Windows requires
> WSL2), prompted by Hermes leaving beta on native Windows. **Recommendation: keep WSL2
> for v0.2; make native Windows the v0.3 direction** via an ADR superseding the WSL2-only
> rule. The v0.2 rule in
> [Bootstrap installer](../explanation/deployment/bootstrap-installer.md) stays in force.

## The question

v0.2 requires **WSL2 on Windows**: Hermes and the Python engines run inside WSL2, while
Windows hosts only the editing surface (Obsidian, Zotero, the vault files), which WSL2
reaches across `/mnt/c` and a loopback bridge. Given Hermes now runs natively on Windows,
does the Windows path still *need* WSL2 — or can it be **native Windows only**?

## The current rule rests on two rationales — both have weakened

The WSL2-only rule ([Bootstrap installer](../explanation/deployment/bootstrap-installer.md),
the [installer platform matrix](../reference/installer.md), and ADR-22/26/27/31) was
justified by:

1. **"Hermes is WSL2-only on Windows"** — the load-bearing reason; a native PowerShell
   `hermes profile install` *"could never work end-to-end."* **No longer true:** Nous's
   official docs now state Hermes *runs natively on Windows 10/11 — no WSL, no Cygwin, no
   Docker*, with a dedicated native installer (auto-provisions Python 3.11 / Node 22 / Git
   via `uv`). The one remaining WSL2-only Hermes feature is the dashboard's
   **embedded-terminal pane** (it needs a POSIX PTY).
2. **Windows build-pain for the analysis stack** — **largely gone:** current pip wheels
   cover `umap-learn` (+ its `numba`/`llvmlite`), `hdbscan`, `bertopic`, `torch` (CPU), and
   `faiss-cpu` on native Windows (pin Python 3.10–3.13). The only sharp edge is base
   `hnswlib` (sdist-only → needs MSVC, or swap to FAISS / `chroma-hnswlib`). And that stack
   isn't even shipped yet — [ADR-33](../adr/33-cluster-mcp-bertopic.md)'s cluster MCP is a
   tracked follow-up — so it's a non-blocker today.

> ⚠️ **Verify before committing.** The Hermes-native-Windows claim comes from Nous's own
> docs; a third-party source still calls it experimental, and the project is young.
> Re-check `hermes-agent.nousresearch.com/docs/user-guide/windows-native` at decision time.

## What native Windows would *remove*

Most of the repo's documented Windows failure modes are WSL2↔Windows *boundary* problems.
Native Windows collapses the two-OS topology into one and deletes them:

- the `networkingMode=mirrored` requirement for the Obsidian REST bridge
  ([ADR-31](../adr/31-native-obsidian-mcp.md)) — on one OS, loopback is trivial;
- `/mnt/c` cross-boundary file-lock fights, and the **OneDrive-breaks-WSL-locks** hazard;
- the `/mnt/c` Windows→WSL path translation in the ingest pipeline;
- `windowsWslMode` in the ACP pane; the "VPS tunnel drops on WSL2 restart" failure mode.

## What it would *cost* (why it's v0.3, not v0.2)

The current build is deeply WSL2-wired; a native path is a **port**, not a flag:

- **Provisioning** — `install.sh` is apt-based bash (~830 lines, nine steps); native needs
  winget/`uv` provisioning (or wrapping Hermes's own native installer). Today
  `install.ps1` is only a thin WSL2 launcher.
- **Scheduling** — Hermes-internal cron + bash cron-wrappers → Windows Task Scheduler, or
  an in-process scheduler (APScheduler) for one cross-platform codebase.
- **Always-on** — the systemd gateway/tunnel services → Windows services.
- **Scripts** — the bash cron-wrappers / dev / test / link-check scripts → PowerShell or
  cross-platform Python.

A meaningful share of this is *deletion* (the bridge / path-translation / mirrored-network
layers largely go away), so it is smaller than it first looks — but still too large to
swap into a slim v0.2 late in the milestone.

## Recommendation

- **v0.2 — keep WSL2-on-Windows** as the single supported, tested Windows path. Do not
  re-platform now; the build is written and tested for WSL2.
- **v0.3 — make native Windows the target**, via an **ADR that supersedes the WSL2-only
  rule**. Justified by: both blockers have dissolved, and native Windows *removes*
  fragility rather than displacing it.

### What a v0.3 native-Windows ADR would touch

- **Supersedes** the WSL2-only rule in
  [Bootstrap installer](../explanation/deployment/bootstrap-installer.md) and the
  platform matrix in [Installer (bootstrap)](../reference/installer.md); updates the README platform
  badge.
- **Amends** [ADR-26](../adr/26-repo-as-install-unit.md) (`install.ps1` becomes a real
  installer), [ADR-27](../adr/27-hermes-native-config-and-gate-enforcement.md) and
  [ADR-31](../adr/31-native-obsidian-mcp.md) (the bridge simplifies on one OS);
  **reinforces** [ADR-22](../adr/22-build-on-hermes-runtime.md) (Hermes is now native).
- The runtime stack ([Memoria system architecture — the seven-layer stack](system-architecture.md)) is unchanged — the
  L5 MCP boundary stays; only the OS underneath it changes.

## To verify / open

- **Hermes native Windows** — confirm GA against the primary doc (above) before adopting.
- **The ACP pane** — does Memoria's pane depend on Hermes's WSL2-only embedded-terminal, or
  only on the CLI/MCP (which are native)? This decides whether the pane works natively.
- **Vector search** — if/when ADR-33's stack ships, avoid base `hnswlib` on Windows (use
  FAISS / `chroma-hnswlib`) and pin Python 3.10–3.13.
