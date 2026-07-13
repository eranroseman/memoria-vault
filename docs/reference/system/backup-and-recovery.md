---
title: Backup and recovery
parent: System and infrastructure
nav_order: 6
grand_parent: Reference
---

# Backup and recovery

Memoria backs up the non-rebuildable SQLite and blob stores that Git does not
carry. The backup also binds the journal head needed to verify the restored
event log. Backup and restore are PI-only maintenance commands and serialize
against workspace writers.

## Commands

| Command | Contract |
| --- | --- |
| `memoria workspace backup <target>` | Verifies and reconciles the journal, then publishes one complete snapshot outside the live vault. |
| `memoria workspace restore <source>` | Validates a snapshot and restores it only when no live Memoria database exists. |
| `memoria workspace restore <source> --force` | Replaces the live database, blobs, journal head, and derived journal exports with the validated snapshot. |
| `memoria journal verify` | Verifies the authoritative chain, live head, committed-prefix anchor, and JSONL export subset. |

The CLI defaults to the `pi` actor. Passing `--actor agent` to backup or restore
fails before any filesystem effect.

## Backup directory

| Path | Contents |
| --- | --- |
| `manifest.json` | Format version, creation time, database hash, blob file count and inventory hash, and journal-head binding. |
| `memoria.sqlite` | A SQLite backup-API snapshot containing verdicts, provenance, requests, and the authoritative event log. |
| `blobs/` | The source-content blob tree, including an empty tree when the workspace has no blobs. |
| `journal-head` | The live chain head. It is absent only when the backed-up empty chain has no anchor. |

The target must not overlap the live vault. Memoria writes a temporary sibling,
then renames it into place. A missing target is created. An existing target is
replaceable only when its versioned manifest identifies it as a Memoria
backup; arbitrary directories, files, and symlinks are refused. If replacement
fails, the previous recognized backup is restored.

## Restore validation

Restore copies the source into sibling staging and validates it before moving
any live component:

- the manifest uses the supported format and fixed component paths;
- the database and blob tree match their manifest hashes;
- SQLite `quick_check` succeeds;
- the staged journal chain and head verify;
- every journal machine is a nonblank canonical filename before JSONL exports
  are rebuilt;
- per-machine JSONL exports rebuild from the restored `event_log`; and
- the Git-committed journal head is `GENESIS` or a prefix of the restored
  chain.

A backup older than the committed journal head is refused. An unavailable or
unreadable Git anchor also fails closed. Check out the Git revision whose
committed head belongs to that backup before restoring it.

The live swap includes `memoria.sqlite`, stale WAL/SHM sidecars, `blobs/`,
`journal-head`, and `journal/`. A failure restores every prior component. A
successful swap appends a PI-attributed `workspace-restored` event, verifies
the resulting chain, preserves the backup source, and removes staging data.
If restoring the prior live components also fails, Memoria preserves the
sibling `.<vault>.restore-rollback-*` directory as recovery material instead
of deleting the only saved originals.

## Doctor status

`memoria doctor` and `memoria doctor bundle` fail when the workspace contains
blob files without current coverage. Coverage is one of:

- configured `blob-sync.yaml`/`blob-sync.json`;
- configured general `backup.yaml`/`backup.json`; or
- `.memoria/config/last-backup`, whose JSON stamp matches both the current blob
  inventory and a present, valid backup target.

SQLite-only Litestream configuration does not cover blobs. Empty directories
do not count as blob content. Changing a blob or removing the stamped target
makes the local-backup status fail until a new backup succeeds.
`last-backup` is ignored by Git because its absolute target is machine-local.

## Related

- [Failure modes](failure-modes.md) — recovery symptoms and responses.
- [On-disk layout](on-disk-layout.md) — live workspace paths.
- [CLI](../commands-and-transports/cli.md) — command inventory.
