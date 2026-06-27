---
topic: decisions
id: 55
title: The repo ships src/, the installer scaffolds and populates, and a golden copy makes the vault restorable
nav_exclude: true
status: accepted
date_proposed: 2026-06-10
date_resolved: 2026-06-10
assumes: [26, 49]
supersedes: []
superseded_by: []
---

# ADR-55: The repo ships src/, the installer scaffolds and populates, and a golden copy makes the vault restorable

> **Verified on-box 2026-06-21.** The shipped mechanism is the SHA-256 golden
> manifest plus `check` and `restore`; `restore` is propose-only unless the caller
> passes `--apply`, and the absence of any release-upgrade reconcile command is
> test-pinned by `tests/test_golden_restore.py::test_upgrade_command_is_not_shipped`.

## Context

The repo carried a top-level `vault/` — effectively a live-vault template — which
blurred "source of truth" with "a running instance" and offered no recovery path when
a deployed system file drifted or was corrupted: the Linter could *detect* but not
*restore* (this ADR chooses
fresh-installed releases over in-place migration).

## Decision

The repo ships **`src/`** — source files only (templates, profiles, skills, schemas,
dashboards, patterns, `.obsidian` config), never a live vault. The installer
**scaffolds, then populates**: it creates the vault folder tree (the skeleton is
checked against `.memoria/schemas/folders.yaml`; empty content dirs get `.gitkeep`),
copies the system files from `src/`, and **stages a golden copy** of every system file
at `<vault>/.memoria/golden/` with a hash manifest. The **Linter restores from the
golden copy** on detected drift (`lint:restore` — propose-only by default; the PI or
cron applies). Installer flow: create → download → populate (+ golden copy) → install
Hermes → install profiles (pruning stale `memoria-*`) → install Obsidian → print the
finish-setup steps. **Zotero setup leaves the installer** and moves to the tutorial.
Releases are delivered **fresh-install** — build the complete system from `src/` and
replace the prototype, never migrate user content in place. Refreshing the test or
development vault is limited to overwriting shipped system files from `src/` and then
restaging `.memoria/golden/manifest.json` so later drift checks compare against the
installed source snapshot. There is no shipped in-place release-upgrade reconcile:
that broader layer-aware upgrade path belongs to the later versioned-release spine in
[ADR-76](76-versioned-vault-release-reconciling-installer.md).

This amends [ADR-26](26-repo-as-install-unit.md): the repo remains the install unit
and profiles remain hand-authored and idempotently deployed; what changes is the
shipped shape (`src/`, not a live vault) and the new restore capability.

## Consequences

- User content and system files are structurally separate from the first minute;
  current refresh/install paths repopulate shipped system files from `src/` and leave
  user content outside that scope.
- The Linter becomes a repairer, not just a detector — drift is fixable from a
  known-good baseline without re-running the installer.
- Cross-release, layer-aware upgrade reconciliation is not part of this ADR's shipped
  mechanism. ADR-76 owns that future versioned-release installer path.
- The installer gets simpler to reason about: scaffold and populate are idempotent,
  separately testable steps.
- Together with the lane ceilings this closes the template-protection question
  (#179) as **both**: agents cannot overwrite `system/templates/` because every
  shipped lane-override denies `system/**` (the Co-PI denies `**`) and no lane's
  `allow.write` / `write_scope` / auto-fix scope reaches into `system/`, enforced
  by the write gate ([ADR-28](28-write-gate-as-plugin.md)); an accidental *human*
  overwrite (or deletion) is detected as golden-copy drift and restored via
  `lint:restore`. Both halves are test-pinned (`tests/test_policy_mcp.py`,
  `tests/test_golden_restore.py`).

## Alternatives considered

**Keep shipping a live `vault/` template.** The drift and blurred-source-of-truth
problems this exists to fix. **In-place migration between releases.** Rejected by D52 —
half-migrated states are the failure mode; fresh-install sidesteps it.
**Populate the vault from `.memoria/golden/` instead of `src/`.** Equivalent at
install; `src/` populate + golden staging keeps authoring (repo) and restoring
(runtime) cleanly separate.

## Related

- **Related decisions / Depends on:** amends [ADR-26](26-repo-as-install-unit.md);
  [ADR-49](49-catalog-in-bases-linter-monitor.md), [ADR-47](47-type-first-category-folders.md)
- **Extended by (proposed):** [ADR-76: Distribute Memoria as a versioned vault release;
  deploy via a source-agnostic reconciling
  installer](76-versioned-vault-release-reconciling-installer.md) proposes extending this
  ADR's golden manifest to cover the code and authored-content layers; if accepted, its
  manifest supersedes this one.
