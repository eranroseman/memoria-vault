---
title: Return to work
parent: Inbox
grand_parent: How-to guides
nav_order: 5
---

# Return to work

Three checks before starting a research session after being away. They catch the
common standalone runtime failures before they cost time mid-session.

## Steps

**1. Confirm the CLI runtime is healthy.**

```bash
memoria doctor bundle --workspace <workspace>
memoria status --workspace <workspace>
```

If `memoria` is not on `PATH`, run the workspace-local command:

```bash
<workspace>/.memoria/.venv/bin/python -m memoria_vault.cli doctor bundle --workspace <workspace>
```

**2. Confirm provider config and search are ready.**

```bash
memoria workspace rebuild --workspace <workspace> --search
memoria request list --workspace <workspace>
```

Provider settings live under `<workspace>/.memoria/config/providers.yaml` and
environment variables consumed by the standalone CLI/engine. There is no
profile `.env` propagation step in alpha.15.

**3. Confirm the workspace is synced and clean.**

```bash
cd <workspace>
git pull --ff-only
git status --short
```

Expected: a clean fast-forward or no remote changes. A diverged branch means
another machine pushed while this one was offline; resolve before starting work.

Then open the Inbox queue for **Needs me**. If the rail health band is non-zero,
open Maintenance for **Drift watch**, **Loose ends**, and **Board**.

## What's Fragile

**Optional UI adapter not responding** — keep working through the `memoria` CLI
and repair the adapter separately.

**qmd search index stale** — rebuild it with [Rebuild the search index](../operate/rebuild-the-search-index.md).

**Sync incomplete** — notes created on another device are not queryable until
sync completes; check Git/sync status before blaming retrieval.

## Related

- Safe mode: [Safe mode](../troubleshooting/safe-mode.md)
- Rebuild search index: [Rebuild the search index](../operate/rebuild-the-search-index.md)
- No installed profiles: [Installed profiles](../../reference/profile-capabilities.md)
- Failure catalog: [Failure modes](../../reference/failure-modes.md)
