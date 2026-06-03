---
title: How to return to work after a break
parent: Maintenance
nav_order: 10
---

# How to return to work after a break

Three checks before starting any research session after being away — a day, a week, or longer. Takes under two minutes. Catches the most common resumption failures before they cost time mid-session.

## Steps

**1. Confirm environment variables are loaded.**

```bash
echo $KILOCODE_API_KEY $OPENALEX_API_KEY
```

Both should return non-empty values. If either is blank, the corresponding Hermes operations will fail silently or with cryptic errors. Source your env file:

```bash
source ~/.hermes/profiles/memoria-librarian/.env
```

**2. Confirm Hermes is reachable.**

```bash
hermes --version
hermes profile list
```

`hermes --version` returns a version number. `hermes profile list` shows all seven `memoria-*` profiles registered. If profiles are missing, re-deploy them from the repo clone: `bash scripts/install.sh --profiles-only` (`.\scripts/install.ps1 -ProfilesOnly` on Windows).

**3. Confirm the vault is synced.**

```bash
cd <vault-path>
git pull --ff-only
git status
```

Expected: either "Already up to date" or a list of fast-forward changes. A merge conflict or diverged branch means another machine pushed while this one was offline — resolve before starting work.

## What's fragile

**ACP pane not responding** — all workflows have a terminal equivalent. `Cmd-P` commands that invoke Hermes can also be run from the CLI. The ACP pane is a convenience layer, not a requirement.

**qmd search index stale** — if you modified notes outside a Hermes session, the search index may lag. Rebuild: see [How to rebuild the search index](rebuild-the-search-index.md). Signs of staleness: Writer's `/draft` command returns no vault results.

**Syncthing not synced** — check the Syncthing status bar in Obsidian or open `http://localhost:8384`. Notes created on another device won't be queryable until sync completes.

## If something is broken

See [Safe mode: minimal working path](../recovery/safe-mode.md) — the three core workflows (ingest, triage, export) and their fallbacks when optional tooling is unavailable.

## Related

- Safe mode (when tools are broken): [Safe mode: minimal working path](../recovery/safe-mode.md)
- Rebuild search index: [How to rebuild the search index](rebuild-the-search-index.md)
- Fix a stale .bib: [How to fix a stale .bib](../recovery/fix-stale-bib.md)
- Reinstall missing profiles: [How to set up Hermes](../setup/set-up-hermes.md)
- The comprehensive failure catalog: [Failure modes](../../reference/failure-modes.md)
