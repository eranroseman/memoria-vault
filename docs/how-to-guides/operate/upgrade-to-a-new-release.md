---
title: Upgrade the vault to a new release
parent: Operate
nav_order: 7
---

# Upgrade the vault to a new release

Pull a newer Memoria source and reconcile it into your live vault without clobbering the system files you've customized. The installer does the reconcile for you; this guide is the end-to-end lifecycle and what to do when a customization and a release change collide. [Redeploy profiles](redeploy-profiles.md) covers only the profile half — this covers the full vault.

## What an upgrade touches

An upgrade reconciles three layers, each by its own rule ([ADR-55](../../adr/55-src-scaffold-populate-golden-copy.md)):

| Layer | Examples | What the upgrade does |
| --- | --- | --- |
| Runtime code | `.memoria/operations/`, `.memoria/mcp/`, `.memoria/memoria_runtime/` | Replaced wholesale from the new source — never hand-edited; recovery is reinstall, Git is the source of truth. |
| Authored system files | `system/templates/`, `system/dashboards/`, `system/patterns/`, `system/eval/`, `system/scripts/`, `home.md`, `system/vocabulary.md`, `AGENTS.md`, and the shipped `.obsidian` config | **Three-way reconciled** against the golden copy: clean release changes land, your customizations are preserved and reported, true conflicts are surfaced. |
| Per-vault state | your notes, `lane-overrides/`, `logs/`, rendered config, `.env`, the golden store | **Never touched** — defined as everything not in the release manifest. |

The reconcile compares three versions of each covered file: the **old golden** (the baseline staged at your last install), the **new source** (the release you're pulling), and your **live** vault copy.

## Prerequisites

- Your runtime vault is a clean Git working tree (commit or stash local note changes first — Git is the history layer for your notes)
- The repo clone that holds the installer, on the machine where Hermes runs ([Set up the vault](../setup/set-up-the-vault.md))

## Steps

**1. Pull the new source.**

In the repo clone (not the runtime vault):

```bash
cd <repo-clone>
git pull                      # or: git checkout <release-tag>
```

**2. Preview the reconcile (dry-run).**

Before changing anything, see what the upgrade would do. From the runtime vault, run the golden operation in propose-only mode (no `--apply`):

```bash
cd <vault>
python3 .memoria/operations/integrity/linter/golden_restore.py \
  --vault . upgrade --source <repo-clone>/src
```

It prints one line per changed file, bucketed: `would_apply` / `would_remove` (clean release changes), `customized` (your edit, preserved — the release didn't touch this file), and `conflicts` (both you and the release changed the same file). It exits `2` when there are conflicts, `0` otherwise — nothing is written.

**3. Run the installer.**

A full installer run syncs the new source in (without clobbering golden-covered files), then runs the same `upgrade --source <src> --apply` for you, refreshes the golden baseline to the new release, and redeploys the five profiles and the crons:

```bash
cd <repo-clone>
bash scripts/install.sh --vault <vault>          # Linux / WSL2
```

```powershell
.\scripts/install.ps1 -Vault <vault>             # Windows native production
```

Use the full run, **not** `--profiles-only` — the profile-only path skips the golden reconcile (it only redeploys profiles). If the installer warns that it *preserved customized system-file conflicts*, the upgrade left your conflicting files in place and you resolve them in step 4.

**4. Resolve any conflicts.**

A `conflicts` file is one both you and the release changed; the upgrade leaves your version in place rather than guess. List them, then merge by hand:

```bash
python3 .memoria/operations/integrity/linter/golden_restore.py --vault . check
```

`check` reports each covered file as `drifted` or `missing` against the now-current golden baseline. For each conflict, diff your live file against the new source under `<repo-clone>/src/<path>`, fold in the release change you want, and re-stage the baseline so the file reads clean next time:

```bash
python3 .memoria/operations/integrity/linter/golden_restore.py --vault . stage
```

**5. Rebuild the search index if templates or note shapes changed.**

A release that changes note structure can leave search stale: [Rebuild the search index](rebuild-the-search-index.md).

## Verify

- `golden_restore.py --vault . check` reports no `drifted`/`missing` files you didn't intend to keep
- `hermes profile list` shows exactly the five `memoria-*` profiles, and `hermes cron list` shows the maintenance crons with next-run times
- A spot-check note opens cleanly and the dashboards render — no template or Base view is broken
- `git status` in the runtime vault shows only changes you expect (your notes plus the reconciled system files)

## How the three-way reconcile decides

For each covered file, the outcome follows from comparing live against the old and new baselines:

| Your live file matches… | …and the release | Outcome |
| --- | --- | --- |
| the old baseline | changed the file | Take the new version (`would_apply` / `applied`). |
| the new version already | (any) | Nothing to do (`unchanged`). |
| neither baseline, release unchanged | left the file alone | Keep your edit (`customized`). |
| neither baseline, release changed it | changed it too | `conflict` — your version is kept; you merge by hand. |
| the old baseline, file dropped in release | removed the file | Remove it (`would_remove` / `removed`). |

The rule in one line: **a clean release change lands only where you hadn't touched the file; your customization is preserved wherever the release didn't change it; anything else is a conflict you own.**

## Related

- The golden copy and its manifest: [ADR-55: Scaffold, populate, golden copy](../../adr/55-src-scaffold-populate-golden-copy.md)
- Redeploying just the profiles: [Redeploy profiles](redeploy-profiles.md)
- The installer's flags and component checklist: [Installer (bootstrap)](../../reference/installer.md)
- If a deployed profile still mismatches the source: [Fix profile drift](../troubleshooting/fix-profile-drift.md)
