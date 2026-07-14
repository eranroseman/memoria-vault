---
title: Backup and recovery
parent: System and infrastructure
nav_order: 6
grand_parent: Reference
---

# Backup and recovery

Memoria backs up the non-rebuildable SQLite and blob stores that Git does not
carry. The backup also binds the journal head needed to verify the restored
event log. Backup, restore, and interrupted-transaction recovery are PI-only
maintenance commands. They serialize against workspace writers.

## Commands

| Command | Contract |
| --- | --- |
| `memoria workspace backup <target>` | Verifies and reconciles the journal, then publishes one complete snapshot outside the live vault. |
| `memoria workspace restore <source>` | Validates a snapshot and restores it only when no live Memoria database exists. |
| `memoria workspace restore <source> --force` | Replaces the live database, blobs, journal head, and derived journal exports with the validated snapshot. |
| `memoria workspace recover` | Completes recovery from an interrupted backup publication or restore before other workspace recovery work. |
| `memoria journal verify` | Verifies the authoritative chain, live head, committed-prefix anchor, and JSONL export subset. |

The CLI defaults to the `pi` actor. Passing `--actor agent` to backup, restore,
or recover fails before any filesystem effect.

## Backup directory

| Path | Contents |
| --- | --- |
| `manifest.json` | Format version, creation time, database hash, blob file count and inventory hash, and journal-head binding. |
| `memoria.sqlite` | A SQLite backup-API snapshot containing verdicts, provenance, requests, and the authoritative event log. |
| `blobs/` | The source-content blob tree, including an empty tree when the workspace has no blobs. |
| `journal-head` | The live chain head. It is absent only when the backed-up empty chain has no anchor. |

The target must not overlap the live vault. Memoria writes a temporary sibling,
records an identity-bound publication transaction, then renames the sibling
into place. A missing target is created. An existing target is
replaceable only when its versioned manifest and snapshot contents pass the
same validation used by restore; arbitrary directories, files, forged
manifests, symlinks, and junctions are refused. If replacement fails, the
previous recognized backup is restored when recovery can validate the
transaction material; otherwise, that material is preserved for PI inspection.
The live workspace's fixed database,
sidecar, blob, journal, configuration, and lock paths must not redirect through
symlinks or junctions.

## Restore validation

Restore copies the source into sibling staging and validates it before moving
any live component:

- the manifest uses the supported format and fixed component paths;
- the database and blob tree match their manifest hashes;
- SQLite `quick_check` succeeds;
- the staged journal chain and head verify;
- every journal machine is a non-empty canonical filename before JSONL exports
  are rebuilt;
- per-machine JSONL exports rebuild from the restored `event_log`; and
- the Git-committed journal head is `GENESIS` or a prefix of the restored
  chain.

A backup older than the committed journal head is refused. An unavailable or
unreadable Git anchor also fails closed. Check out the Git revision whose
committed head belongs to that backup before restoring it.

The backup source is trusted operator-owned storage. Manifest, database,
journal, and blob hashes detect corruption and internal inconsistency; they do
not authenticate a snapshot against malicious rewriting by someone who can
replace the backup and recompute those hashes.

**Unshipped/deferred:** cryptographic backup authenticity, including signing or
keyed verification for storage outside the operator's trust boundary.

The live swap includes `memoria.sqlite`, stale WAL/SHM/rollback-journal
sidecars, `blobs/`, `journal-head`, `journal/`, and the machine-local
`last-backup` stamp. Before publishing the marker, Memoria durably preserves
any live WAL or rollback journal in the bound rollback directory. On a failed
swap, recovery attempts to restore every prior component. A successful swap
appends a PI-attributed
`workspace-restored` event, verifies the resulting chain, preserves the backup
source, and removes staging data.
If restoring the prior live components also fails, Memoria preserves the
sibling `.<vault>.restore-rollback-*` directory as recovery material instead
of deleting the only saved originals. A durable, Git-ignored
`.memoria/restore-transaction.json` marker records which live components
existed and binds the rollback directory and stage to the live vault with a
transaction identity. While a swap is unresolved, `memoria workspace recover`
preserves any original that was not moved before interruption, restores the
saved live components and prior backup stamp, and, when a recovered database
exists, verifies its journal before recording a cleanup phase. Cleanup removes
directory contents before their transaction identities, so an interrupted
cleanup can resume. Once a marker is in cleanup, recovery verifies the retained
journal and completes cleanup only. A pre-swap workspace without a database
remains without one after rollback. When it cannot determine the pre-swap
state, it leaves the marker and sibling directories intact for the PI to
inspect rather than guessing. A separate `.memoria/backup-transaction.json`
marker covers every publication. Before the first rename, it identity-binds the
staged replacement and, when present, the prior target to one random
transaction. For an unresolved publication marker, recovery validates those
identities and recognized backup material before it restores the prior target,
removes an unpublished first snapshot, or retains a replacement whose publish
rename completed. Once a backup marker is in cleanup, the retained target must
keep its matching transaction identity while recovery writes the local backup
stamp and removes sibling transaction material. Recovery then removes the marker
and best-effort target identity cleanup follows. An interrupted identity cleanup
may leave that inert metadata in an otherwise valid backup target.

## Doctor status

`memoria doctor` and `memoria doctor bundle` fail when the workspace contains
blob files without current coverage. Coverage is one of:

- configured `blob-sync.yaml`/`blob-sync.json`;
- configured general `backup.yaml`/`backup.json`; or
- `.memoria/config/last-backup`, whose JSON stamp matches both the current blob
  inventory and a present, valid backup target.

Configured YAML/JSON coverage must be a readable mapping and must name a
non-empty `target`. If `enabled` is present, its value must be the Boolean
`true`. An empty, malformed, disabled, or target-free file does not count as
coverage.

SQLite-only Litestream configuration does not cover blobs. Empty directories
do not count as blob content. Changing a blob or removing the stamped target
makes the local-backup status fail until a successful backup, restore, or
recovery of a completed publish writes a matching stamp.
`last-backup` is ignored by Git because its absolute target is machine-local.

Before `doctor --repair` writes or `doctor bundle` opens SQLite, Memoria
checks the fixed runtime paths and pending transaction markers, acquires the
workspace lock without following path redirects, then repeats those checks
under that lock. Pending backup or restore work must be completed by
`memoria workspace recover` first. Repair also checks every skeleton,
seed, projection, SQLite, and existing Git-metadata target before its first
write. Its Git commands are bound to the workspace repository and ignore Git
environment variables that can redirect the index, object store, work tree,
configuration, or common directory. Repair refuses repository common-directory
indirection. Git system and global configuration are disabled for these
commands. `memoria init` and first-time migration stage and commit files only in
a repository they create. Repair never stages any repository, including one it
creates, so repository-configured clean filters cannot run. On POSIX, the
workspace lock requires atomic no-follow opens and refuses maintenance when the
platform lacks them. On Windows, it anchors the resolved workspace root, then
opens and inspects every lock-path component below it through parent-relative
native handles without resolving reparse points. It retains those handles until
the lock closes.

## Related

- [Back up and restore the workspace](../../how-to-guides/operate/back-up-and-restore-the-workspace.md) — how-to steps.
- [Failure modes](failure-modes.md) — recovery symptoms and responses.
- [On-disk layout](on-disk-layout.md) — live workspace paths.
- [CLI](../commands-and-transports/cli.md) — command inventory.
