---
title: Return to work
parent: Inbox
nav_order: 5
---

# Return to work

Three checks before starting any research session after being away — a day, a week, or longer. Takes under two minutes. Catches the most common resumption failures before they cost time mid-session.

## Steps

**1. Confirm Hermes and the profiles are healthy.**

```bash
hermes --version
hermes profile list
```

`hermes profile list` shows the five `memoria-*` profiles (`copi`, `librarian`, `writer`, `peer-reviewer`, `engineer`). If any is missing, re-deploy with the `--profiles-only` redeploy from the repo clone ([Set up Hermes](../setup/set-up-hermes.md)).

**2. Confirm the secrets are in place.**

```bash
grep -c '=' ~/.hermes/.env
cat ~/.hermes/profiles/memoria-librarian/.env | grep -E 'KILOCODE|OPENALEX|OBSIDIAN' | sed 's/=.*/=set/'
```

```powershell
(Get-Content "$env:LOCALAPPDATA\hermes\.env" | Where-Object { $_ -match '=' }).Count
Get-Content "$env:LOCALAPPDATA\hermes\profiles\memoria-librarian\.env" |
  Where-Object { $_ -match '^(KILOCODE|OPENALEX|OBSIDIAN)' } |
  ForEach-Object { $_ -replace '=.*', '=set' }
```

The five keys checked here should all show as set — see [Set up Hermes](../setup/set-up-hermes.md) for what each one is and where it comes from. A blank key or placeholder certificate path fails mid-task. If you rotated keys in the shared Hermes env file, propagate them with the `--profiles-only` redeploy above.

**3. Confirm the vault is synced.**

```bash
cd <vault-path>
git pull --ff-only
git status
```

Expected: "Already up to date" or a clean fast-forward. A diverged branch means another machine pushed while this one was offline — resolve before starting work.

Then open the Inbox space: the **Needs me**, **Drift watch**, and **Board** views show what accumulated while you were away (the crons kept running — sweeps every 15 minutes, lint daily).

## What's fragile

**ACP pane not responding** — the Co-PI also runs in a terminal: `hermes -p memoria-copi acp` to test the server, and every delegation has a CLI equivalent (`hermes kanban create`). The pane is a convenience layer; see [Safe mode](../troubleshooting/safe-mode.md).

**qmd search index stale** — if notes changed outside a session, vault search may lag. Rebuild: [Rebuild the search index](../operate/rebuild-the-search-index.md).

**Sync (Syncthing/multi-device) incomplete** — notes created on another device won't be queryable until sync completes; check before blaming retrieval.

## If something is broken

See [Safe mode](../troubleshooting/safe-mode.md) — the minimal working paths when optional tooling is down.

## Related

- Safe mode (when tools are broken): [Safe mode](../troubleshooting/safe-mode.md)
- Rebuild search index: [Rebuild the search index](../operate/rebuild-the-search-index.md)
- Fix a stale .bib: [Fix a stale .bib](../zotero/fix-stale-bib.md)
- Reinstall missing profiles: [Set up Hermes](../setup/set-up-hermes.md)
- The comprehensive failure catalog: [Failure modes](../../reference/failure-modes.md)
