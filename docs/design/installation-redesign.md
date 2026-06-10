---
topic: explorations
title: Installation redesign — src/ + scaffold-and-populate + a restorable golden copy
status: exploration
created: 2026-06-09
parent: Design notes
grand_parent: Explanation
nav_order: 27
nav_exclude: true
---

# Installation redesign — src/ + scaffold-and-populate + a restorable golden copy

> **Status: exploration (v0.3 direction).** Rework the install model so the repo ships
> *source files*, not a live vault, and so the system can **self-heal**. Amends
> [ADR-26](../adr/26-repo-as-install-unit.md) and the installer docs
> ([Bootstrap installer](../explanation/deployment/bootstrap-installer.md),
> [Installer (bootstrap)](../reference/installer.md)). Not for v0.2.

## The problem

Today the repo carries a top-level **`vault/`** — effectively a *live vault template*. That
is error-prone: it blurs "source of truth" with "a running instance," invites accidental
edits to the template, and makes the runtime vault and the repo drift apart. There is also
**no recovery path**: if a system file in a deployed vault is corrupted or hand-edited, the
Linter can *detect* the drift but cannot *restore* it.

## The proposal

1. **`vault/` → `src/`.** The repo ships **source files only** (templates, profiles,
   skills, dashboards, patterns, schemas) under `src/` — never a live vault.
2. **Scaffold, then populate.** The installer **creates the vault's folder structure**
   (with `.gitkeep`s for the empty content dirs) and then **populates the system files
   from `src/`**. The user's *content* dirs start empty; only *system* files are seeded.
3. **A restorable golden copy in `.memoria/`.** Stage a canonical copy of every system
   file under **`.memoria/`** (hidden runtime). This makes the Linter a **recovery tool**:
   on detected drift/corruption it can restore a system file from the golden copy — the
   natural extension of *archive-never-delete* and the Linter's integrity role. (`.memoria/`
   is hidden runtime, so the golden copy never pollutes content or the graph.)

So `src/` (in the repo) is the *authoring* source; `.memoria/` (in the vault) is the
*runtime* source-of-restore; the live vault is *derived* from both.

## The installer flow

1. **Create** the vault folder structure (`.gitkeep` the empty content dirs).
2. **Download** the repo / release.
3. **Populate** system files from `src/` (and stage the `.memoria/` golden copy).
4. **Install Hermes** (the runtime).
5. **Install profiles** (the agents).
6. **Install Obsidian** (the GUI) — *if not already present.*
7. **Print "how to finish setup"** — the few manual steps that can't be automated
   (enable plugins, open the vault, etc.).

**Zotero is dropped from the installer** — its setup moves to the tutorial (it's a
user-side, optional bibliographic-backbone step, not core provisioning).

## Why the golden copy is the standout idea

It turns the Linter from a *detector* into a *repairer*. Combined with the schema-check
and graph-health detectors, a deployed vault becomes **self-healing for system files**:
drift is flagged *and* fixable from a known-good baseline, without re-running the whole
installer. This is the part most worth promoting to an **ADR** (a small, sharp decision:
*ship a restorable golden copy of system files in `.memoria/`*).

## Impact

- **Amends [ADR-26](../adr/26-repo-as-install-unit.md)** — the install unit becomes `src/`
  - a scaffold-and-populate installer, not a shipped `vault/`.
- Updates the installer docs
  ([Bootstrap installer](../explanation/deployment/bootstrap-installer.md),
  [Installer (bootstrap)](../reference/installer.md)) — the new flow, and Zotero moving to
  the tutorial.
- Composes with the [native-Windows reevaluation](native-windows.md): both are
  installer-shaped v0.3 work and should be sequenced together (the native-Windows port also
  rewrites provisioning).

## Open / to decide

- **`src/` populate vs `.memoria/` populate** — do we populate the live vault *from* `src/`
  at install and *also* stage `.memoria/`, or populate the vault *from* `.memoria/` (one
  source-of-restore)? Leaning: install seeds both; the Linter restores from `.memoria/`.
- **Update path** — how a later release refreshes the golden copy + re-populates changed
  system files without touching user content (a `migrate`/`update` command).
- **Scope of "system files"** — exactly which files are golden-copied (templates · profiles
  · skills · dashboards · patterns · schemas) vs left user-owned.
