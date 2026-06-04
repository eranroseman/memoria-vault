---
title: Bootstrap installer
parent: Deployment
nav_order: 2
---

# Bootstrap installer

The bootstrap installer — [`scripts/install.sh`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/install.sh) at the repo root, with [`scripts/install.ps1`](https://github.com/eranroseman/memoria-vault/blob/main/scripts/install.ps1) as a thin WSL2 launcher — takes a user from nothing to a runnable Memoria install in one command: it installs the desktop apps (Obsidian, Zotero), provisions the Hermes runtime and the seven profiles, lays the vault down off OneDrive, and walks the user through the few steps that cannot be automated (secrets, Zotero GUI clicks).

This page explains *why* the installer is shaped the way it is. The concrete inventories — platform matrix, install-flow steps, the component checklist, the secrets and skills tables — are reference material in [Installer (bootstrap)](../../reference/installer.md).

## Why a bootstrap

Before the bootstrap, the shipped installer did only one of the nine setup steps — register the seven Hermes profiles from an already-cloned repo. Everything else was manual and spread across five how-to guides, and a new user had to already have Obsidian, Zotero, Better BibTeX, Hermes, Python, Git, and Pandoc installed before any of it worked. The gap was a single, guided first-run path — which is what the bootstrap is.

## Goals and non-goals

**Goals**

- One command from zero to a runnable vault on Linux (Ubuntu/Debian) and Windows.
- Idempotent: safe to re-run after a `git pull` (the per-profile redeploy path survives as `scripts/install.sh --profiles-only`).
- Detect-then-install; never clobber existing apps or credentials.
- Honest about what it cannot do (GUI clicks, secrets) — explain, don't fake.

**Non-goals**

- macOS, and Linux distros other than Ubuntu/Debian (out of scope for v0.1).
- Headless Zotero plugin installation (Zotero supports GUI install only).
- Writing the user's API keys for them.
- Auto-enabling WSL2 (needs a reboot/admin; the installer links Microsoft's guide instead).

## Entry point and safety model

The installer is offered two ways, with **inspect-first as the documented primary** (download, read, then run) and the `curl | bash` / `irm | iex` one-liner shown only as the convenience option. The standard precautions for a piped installer are applied: the entire script body is wrapped in a `main` function invoked on the last line, so a truncated download cannot execute a half-command; it prints a numbered plan and prompts for consent (skippable with `--yes` for CI); `--dry-run` prints every action without executing; and it never silently elevates — if a step needs `sudo`/admin it stops and prints the exact command. These rails are cheap insurance for a script that installs system software, and `--dry-run` doubles as the WSL command transcript (below).

## Windows and WSL2: the decided rule

Per Memoria's runtime model, **Hermes runs only on Linux/WSL2; Windows is the editing surface**. WSL2 is therefore a **hard prerequisite for the entire Windows install**, checked first:

- **No WSL2 → the installer does nothing.** It explains that Memoria on Windows requires WSL2, links Microsoft's guide, and exits without installing anything (enabling WSL2 needs admin + a reboot, so the installer won't attempt it).
- **WSL2 present → proceed.** The thin `scripts/install.ps1` ensures Obsidian and Zotero on the Windows side, then hands the entire rest of the flow to `bash scripts/install.sh` inside WSL2.

**One WSL2 path, not two.** The installer always attempts the automatic in-WSL invocation and **echoes each WSL command before running it**; if a step fails (or under `--dry-run`), those printed commands are the manual fallback. "Manual" is the transparency/recovery output of the single automatic path, not a separate mode — which keeps the one-line promise while staying debuggable.

## Architecture: one bash implementation, a thin PowerShell launcher

There are two files but **one implementation**:

- **`scripts/install.sh` (bash)** is the single real script. It holds the whole bootstrap flow *and* the profile-install logic (refactored from a top-to-bottom script into a function the bootstrap calls). `--profiles-only` exposes just that function for the "re-run after `git pull`" redeploy path; `--only NAME[,NAME]` restricts it to named profiles.
- **`scripts/install.ps1` (PowerShell)** is a **thin launcher only**: gate on WSL2 → ensure the two GUI apps Windows-side → `wsl bash scripts/install.sh` (forwarding flags). It contains no install logic.

This is correctness, not just simplification: Hermes is WSL2-only on Windows, so profiles must be installed *inside* WSL — a native PowerShell `hermes profile install` could never work end-to-end. The real logic has to live in bash; PowerShell can only be a doorway into the Linux side. Both files live at the repo root because the bootstrap is the clone/entry point, not a vault-internal artifact — which is also why [`vault/` is no longer independently installable](distribution-model.md).

## Simplifying decisions (v0.1)

Each trades a little breadth for much less shell to build and maintain:

- **Guide app install, don't fully automate.** Detect Obsidian/Zotero; if absent, print the exact `winget`/`apt` one-liner and run it on consent — no version parsing, no `.deb`-URL upkeep, no silent installs.
- **Presence checks, not version gates.** Check a tool is there; let `pip`/Hermes surface a clear error if it is too old.
- **Don't install language runtimes.** The Hermes installer provisions uv, Python 3.11, Node 22, ripgrep, and ffmpeg; the bootstrap adds only **Git** (pre-Hermes) and **Pandoc** (not provisioned by Hermes).
- **Assume `local-only` deployment.** No Syncthing/VPS/sync logic — multi-device is a later phase.
- **Default the vault off OneDrive** (`%USERPROFILE%\Memoria` on Windows, `~/Memoria` on Linux; prompt to override) — OneDrive fights Hermes's WSL writes across `/mnt/c`, and Git is the backup, so losing OneDrive sync of the vault is fine.

## Trade-offs

- **Surface area** is still nontrivial (WSL2 orchestration + Zotero `.xpi` handling), cut hard by the simplifying decisions above; the residue leans on upstream installers and on guidance for the GUI/secret steps that genuinely can't be automated.
- **`curl | bash` trust** is inherent to the pattern; mitigated by inspect-first framing, the `main`-guard, consent, and `--dry-run`.
- **Partial automation can imply full automation** — the Zotero/secrets steps are assisted, not automatic, so the UX must make that explicit.
- **Distribution-model change:** `vault/` stops being independently distributable. Acceptable because the real workflow is cloning the whole repo, but it is a deliberate reversal recorded in [ADR-26](../../../project-files/decisions/26-repo-as-install-unit.md) and [Distribution model](distribution-model.md).

## Decisions (v0.1, settled)

1. **Default vault directory** off OneDrive; prompt to override.
2. **macOS** out of scope.
3. **Linux** Ubuntu/Debian only (Obsidian official `.deb`; Zotero via the `zotero-deb` apt repo).
4. **Pandoc** required at install time, not deferred.
5. **WSL2 modes:** one path, not two (automatic in-WSL invocation that echoes its commands).
6. **Windows without WSL2:** install nothing; link Microsoft's guide and exit.
7. **Model provider:** v0.1 is KiloCode-only; no separate Anthropic key required.
8. **One bash implementation; `scripts/install.ps1` is a thin WSL2 launcher.**
9. **Guide app install, don't fully automate** (detect, then show/run on consent).
10. **Presence checks, not version gates;** `local-only` deployment assumed.
11. **Keep the safety rails** — `--dry-run`, up-front consent, `main`-guard.

## Related

- **Reference:** [Installer (bootstrap)](../../reference/installer.md) — platform matrix, install-flow steps, component checklist, secrets and skills tables.
- **Decisions:** [ADR-26 the repo is the install unit](../../../project-files/decisions/26-repo-as-install-unit.md).
- **Explanation:** [Distribution model](distribution-model.md) (the repo as install unit), [Why Hermes](../rationale/why-hermes.md) (the runtime the installer provisions).
- **How-to:** [Quickstart](../../how-to-guides/setup/quickstart.md), [tutorial: set up from zero](../../tutorials/01-set-up-from-zero.md).
