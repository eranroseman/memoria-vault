---
title: Bootstrap installer
parent: Deployment
nav_order: 2
---

# Bootstrap installer

The bootstrap installer — [`scripts/install.sh`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/install.sh) at the repo root, with [`scripts/install.ps1`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/install.ps1) as a thin WSL2 launcher — takes a user from nothing to a runnable Memoria install in one command: it scaffolds and populates the vault from `src/`, stages the golden copy, provisions the Hermes runtime and the five agent profiles, wires the crons, and installs Obsidian if absent.

This page explains *why* the installer is shaped the way it is. The concrete inventories — platform matrix, install-flow steps, the component checklist, the secrets and skills tables — are reference material in [Installer (bootstrap)](../../reference/installer.md).

## Why a bootstrap

Before the bootstrap, the shipped installer did only one of the setup steps — register the Hermes profiles from an already-cloned repo. Everything else was manual and spread across five how-to guides, and a new user had to already have the whole stack installed before any of it worked. The gap was a single, guided first-run path — which is what the bootstrap is.

## The flow: scaffold, populate, golden copy

The install model is [ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md): the repo ships **`src/` — source files, never a live vault** — and the installer derives a running vault from it:

1. **Scaffold.** Create the vault's folder tree. The skeleton is checked against the machine-read folder map (`.memoria/schemas/folders.yaml` — the same single source the Linter and the policy gate key off), and empty content dirs are recreated explicitly rather than shipped as placeholder files.
2. **Populate.** Copy the system files from `src/` (templates, profiles, schemas, dashboards, patterns, Obsidian config). On a refresh, author-owned files are overwritten and the user's notes and `.env` are kept — populate is idempotent.
3. **Stage the golden copy.** Every system file is copied to `<vault>/.memoria/golden/` with a hash manifest. This is what turns the Linter from a *detector* into a *repairer*: on drift or corruption it restores from the golden copy (`lint:restore`, propose-only by default) without re-running the installer.
4. **Wire the pre-commit gate.** If the vault is a git repo, the Linter's `schema-check` hook is installed — it *gates at commit, monitors between* (D50).
5. **Install Hermes**, then the **five profiles** (co-PI, Librarian, Writer, Peer-reviewer, Engineer), **pruning** any stale `memoria-*` profiles from earlier releases (fresh-install discipline — releases replace, never migrate in place).
6. **Optional cluster stack.** The clustering engine's topic modeling needs a heavy dependency set (~2 GB); it is an explicit opt-in prompt, and everything else works without it.
7. **Install Obsidian** if absent — and *only* Obsidian. **Zotero left the installer**: it is the PI's bibliographic-backbone choice, not core provisioning, so its setup moved to the tutorial.
8. **Wire the crons** — the board-export telemetry tick, the re-ingest sweeps, and the **daily lint** run (detectors + golden-copy drift), then print the few finish-setup steps that genuinely can't be automated (secrets, enabling plugins).

## Goals and non-goals

**Goals**

- One command from zero to a runnable vault on Linux (Ubuntu/Debian) and Windows.
- Idempotent: safe to re-run after a `git pull` (the per-profile redeploy path survives as `scripts/install.sh --profiles-only`).
- Detect-then-install; never clobber existing apps, credentials, or user content.
- Honest about what it cannot do (secrets, GUI steps) — explain, don't fake.

**Non-goals**

- macOS, and Linux distros other than Ubuntu/Debian.
- Writing the user's API keys for them.
- Auto-enabling WSL2 (needs a reboot/admin; the installer links Microsoft's guide instead).
- In-place migration between releases — rejected by D52; releases are delivered fresh-install.

## Entry point and safety model

The installer is offered two ways, with **inspect-first as the documented primary** (download, read, then run) and the `curl | bash` / `irm | iex` one-liner shown only as the convenience option. The standard precautions for a piped installer are applied: the entire script body is wrapped in a `main` function invoked on the last line, so a truncated download cannot execute a half-command; it prints a numbered plan and prompts for consent (skippable with `--yes` for CI); `--dry-run` prints every action without executing; and it never silently elevates — if a step needs `sudo`/admin it stops and prints the exact command. These rails are cheap insurance for a script that installs system software, and `--dry-run` doubles as the WSL command transcript (below).

## Windows and WSL2: the decided rule

Per Memoria's runtime model, **Hermes runs only on Linux/WSL2; Windows is the editing surface**. WSL2 is therefore a **hard prerequisite for the entire Windows install**, checked first:

> **Reevaluation (2026-06):** the two rationales for this rule have since weakened — Hermes now supports **native Windows** (out of beta) and the Python analysis-stack wheels exist, so WSL2 is no longer *forced* by capability. Native Windows is the direction **after v0.1.2** (it also removes the WSL2↔Windows fragility); see [Native Windows vs WSL2 — platform reevaluation](../../adr/64-native-windows-support.md). **This rule remains in force for the v0.1.x releases.**

- **No WSL2 → the installer does nothing.** It explains that Memoria on Windows requires WSL2, links Microsoft's guide, and exits without installing anything (enabling WSL2 needs admin + a reboot, so the installer won't attempt it).
- **WSL2 present → proceed.** The thin `scripts/install.ps1` ensures Obsidian on the Windows side, then hands the entire rest of the flow to `bash scripts/install.sh` inside WSL2.

**One WSL2 path, not two.** The installer always attempts the automatic in-WSL invocation and **echoes each WSL command before running it**; if a step fails (or under `--dry-run`), those printed commands are the manual fallback. "Manual" is the transparency/recovery output of the single automatic path, not a separate mode — which keeps the one-line promise while staying debuggable.

## Architecture: one bash implementation, a thin PowerShell launcher

There are two files but **one implementation**:

- **`scripts/install.sh` (bash)** is the single real script. It holds the whole bootstrap flow *and* the profile-install logic. `--profiles-only` exposes just that path for the "re-run after `git pull`" redeploy; `--only NAME[,NAME]` restricts it to named profiles.
- **`scripts/install.ps1` (PowerShell)** is a **thin launcher only**: gate on WSL2 → ensure Obsidian Windows-side → `wsl bash scripts/install.sh` (forwarding flags). It contains no install logic.

This is correctness, not just simplification: Hermes is WSL2-only on Windows, so profiles must be installed *inside* WSL — a native PowerShell `hermes profile install` could never work end-to-end. The real logic has to live in bash; PowerShell can only be a doorway into the Linux side. Both files live at the repo root because the bootstrap is the clone/entry point, not a vault-internal artifact.

## Simplifying decisions

Each trades a little breadth for much less shell to build and maintain:

- **Guide app install, don't fully automate.** Detect Obsidian; if absent, print the exact `winget`/`apt` one-liner and run it on consent — no version parsing, no silent installs.
- **Presence checks, not version gates.** Check a tool is there; let `pip`/Hermes surface a clear error if it is too old.
- **Don't install language runtimes.** The Hermes installer provisions uv, Python, Node, ripgrep, and ffmpeg; the bootstrap adds only **Git** (pre-Hermes) and **Pandoc** (not provisioned by Hermes).
- **Assume `local-only` deployment.** No Syncthing/VPS/sync logic — multi-device is a later phase.
- **Default the vault off OneDrive** (`%USERPROFILE%\Memoria` on Windows, `~/Memoria` on Linux; prompt to override) — OneDrive fights Hermes's WSL writes across `/mnt/c`, and Git is the backup, so losing OneDrive sync of the vault is fine.
- **The vault's git repo is the user's own.** The installer never `git init`s under a synthetic author; it prints the commands and the user commits with their own identity.

## Trade-offs

- **Surface area** is still nontrivial (WSL2 orchestration, cron wiring), cut hard by the simplifying decisions above; the residue leans on upstream installers and on guidance for the secret steps that genuinely can't be automated.
- **`curl | bash` trust** is inherent to the pattern; mitigated by inspect-first framing, the `main`-guard, consent, and `--dry-run`.
- **Partial automation can imply full automation** — the secrets steps are assisted, not automatic, so the UX must make that explicit.
- **The golden-copy update path** (how a later release refreshes `.memoria/golden/` without clobbering user customizations) is the known open question, to resolve when v0.1.2 ships ([ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md)).

## Related

- **Reference:** [Installer (bootstrap)](../../reference/installer.md) — platform matrix, install-flow steps, component checklist, secrets and skills tables.
- **Decisions:** [ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md) (src/ + scaffold-populate + golden copy), [ADR-26](../../adr/26-repo-as-install-unit.md) (the repo is the install unit).
- **Explanation:** [Distribution model](distribution-model.md), [Why Hermes](../rationale/why-hermes.md) (the runtime the installer provisions).
- **How-to:** [Quickstart](../../how-to-guides/setup/quickstart.md), [Tutorial 01: Set up from zero](../../tutorials/01-set-up-from-zero.md).
