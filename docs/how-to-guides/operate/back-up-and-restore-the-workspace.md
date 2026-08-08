---
title: Back up and restore the workspace
parent: Operate
grand_parent: How-to guides
nav_order: 6
---

# Back up and restore the workspace

This guide makes the workspace state Git does not carry — the catalog
database, source blobs, and event journal under `.memoria/`, all gitignored —
durable with `memoria workspace backup`, and brings it back with `restore`.
Which copy of each file is authoritative is documented in
[On-disk layout](../../reference/system/on-disk-layout.md).

## When it runs without you

An operator-managed schedule can call `memoria workspace backup` on its own.
Configure ongoing coverage with `blob-sync.yaml`/`blob-sync.json` or
`backup.yaml`/`backup.json` (a mapping naming a non-empty `target`, `enabled`
true if present) so `memoria doctor` stops requiring a fresh manual run after
every blob change. Without configured coverage, `doctor` and `doctor bundle`
fail whenever blob files exist without a matching `last-backup` stamp — treat
that failure as "back up now," not as a bug.

## Steps

**1. Back up.**

```bash
memoria workspace backup --workspace . /path/to/backup-target
```

The target must not overlap the live vault. A missing target is created; an
existing one is replaced only if it is itself a valid prior backup. Backup is
PI-only — `--actor agent` fails.

**2. Confirm doctor sees it.**

```bash
memoria doctor bundle --workspace .
```

`doctor` fails on unbacked blobs. A passing result means the local
`last-backup` stamp (or configured coverage) matches the current blob
inventory and a present, valid backup target.

**3. Restore, when you need to.**

```bash
memoria workspace restore --workspace . /path/to/backup-target
```

Restore validates the snapshot — manifest format, database/blob hashes,
`quick_check`, the staged journal chain and head, and that the Git-committed
journal head is `GENESIS` or a prefix of the restored chain — before moving
anything. Plain `restore` only proceeds when no live database exists. To
replace a live workspace, add `--force`:

```bash
memoria workspace restore --workspace . /path/to/backup-target --force
```

A backup older than the committed journal head is refused; check out the Git
revision whose committed head matches the backup first.
Restore rebuilds the derived `.memoria/journal/` JSONL exports from SQLite's
authoritative `event_log`.

**4. Recover an interrupted backup or restore.**

```bash
memoria workspace recover --workspace .
```

If a backup publish or restore swap was interrupted, run this before any
other workspace recovery work. It resumes from the durable transaction
marker rather than guessing at partial state.

## Verify

- `memoria doctor bundle --workspace .` passes (or reports the specific
  coverage gap, if you expected one)
- `memoria journal verify --workspace .` passes on the restored workspace
- The restored `.memoria/blobs/` inventory matches what the manifest recorded

## Related

- Full contract and failure-mode detail: [Backup and recovery](../../reference/system/backup-and-recovery.md)
- Unexpected branch divergence: [Recover a divergent vault branch](../troubleshooting/resolve-a-diverged-vault-branch.md)
- Recovery symptoms and responses: [Failure modes](../../reference/system/failure-modes.md)
- Live workspace paths: [On-disk layout](../../reference/system/on-disk-layout.md)
