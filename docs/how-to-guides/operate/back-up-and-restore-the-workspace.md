---
title: Back up and restore the workspace
parent: Operate
grand_parent: How-to guides
nav_order: 6
---

# Back up and restore the workspace

`.memoria/memoria.sqlite`, `.memoria/blobs/`, and `.memoria/journal/` are
gitignored. They hold the catalog, evidence bindings, source blobs, and the
authoritative event log — none of it reaches a `git commit`. Backup and
restore are the durability mechanism for everything Git does not carry.

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

This verifies and reconciles the journal, then publishes one snapshot
(`manifest.json`, `memoria.sqlite`, `blobs/`, `journal-head`) outside the live
vault. The target must not overlap the live vault; a missing target is
created, an existing one is only replaced if it's itself a valid prior
backup. Backup is PI-only — passing `--actor agent` fails before any
filesystem effect.

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
- Recovery symptoms and responses: [Failure modes](../../reference/system/failure-modes.md)
- Live workspace paths: [On-disk layout](../../reference/system/on-disk-layout.md)
