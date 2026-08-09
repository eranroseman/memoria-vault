---
title: Return to work
parent: Inbox
grand_parent: How-to guides
nav_order: 1
---

# Return to work

Three checks before starting a research session after being away. They catch the
common standalone runtime failures before they cost time mid-session.

## Steps

**1. Confirm the CLI runtime is healthy.**

```bash
memoria doctor bundle --workspace <workspace>
memoria status --workspace <workspace>
memoria journal verify --workspace <workspace>
```

If `memoria` is not on `PATH`, run the workspace-local command:

```bash
<workspace>/.memoria/.venv/bin/memoria doctor bundle --workspace <workspace>
```

**2. Confirm provider config and search are ready.**

```bash
memoria workspace rebuild --workspace <workspace> --search
memoria request list --workspace <workspace>
```

Provider settings live under `<workspace>/.memoria/config/providers.yaml` and
environment variables consumed by the standalone CLI/engine. There is no
profile `.env` propagation step in the standalone baseline.

**3. Confirm the local workspace is clean.**

```bash
cd <workspace>
git status --short
```

Expected: no output. The supported operating model is one local workstation and
one writer. Git records history and supports recovery; it does not synchronize
Memoria runtime state between writers. If Git reports an unexpected divergent
branch, stop before starting work and follow [Recover a divergent vault
branch](../troubleshooting/resolve-a-diverged-vault-branch.md).

Then run `memoria attention list --workspace .` and work the open Inbox items.
If an optional adapter implements the planned rail, its health band may point
you to Drift watch, Loose ends, and Board; those dashboard groupings are not a
standalone CLI surface today.

## What's Fragile

**Optional UI adapter not responding** — keep working through the `memoria` CLI
and repair the adapter separately.

**search index stale** — rebuild it with [Rebuild the search index](../operate/rebuild-the-search-index.md).

**Unexpected Git divergence** — do not resolve a `.memoria/journal-head`
conflict or merge two journal-bearing histories. Preserve the histories and
follow [Recover a divergent vault branch](../troubleshooting/resolve-a-diverged-vault-branch.md).

## Related

- Safe mode: [Safe mode](../troubleshooting/safe-mode.md)
- Unexpected divergence: [Recover a divergent vault branch](../troubleshooting/resolve-a-diverged-vault-branch.md)
- Rebuild search index: [Rebuild the search index](../operate/rebuild-the-search-index.md)
- Backup procedure: [Back up and restore the workspace](../operate/back-up-and-restore-the-workspace.md)
- Failure catalog: [Failure modes](../../reference/system/failure-modes.md)
