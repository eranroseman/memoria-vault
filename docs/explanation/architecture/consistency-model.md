---
title: Consistency model
parent: Architecture
grand_parent: Explanation
nav_order: 6
---

# Consistency model

Memoria runs two planes with different guarantees, joined by a fail-closed
boundary.

## ACID trust plane

Judgment state — verdicts, provenance, the request queue, the hash-chained
event log — lives in SQLite under `.memoria/`, with WAL, full synchronous
durability, CHECK constraints, and append-only triggers on the journal. What
the system asserts about trust is transactional: a verdict either committed
or it didn't.

The chain is a mechanism to check, not just to have: `memoria journal verify`
walks it end to end and reports the first broken link, so trust is a
verifiable claim with one authoritative read path, not an assumption resting
on WAL and CHECK constraints alone.

## BASE knowledge plane

The knowledge itself is plain files, edited by the researcher with any tool
at any time. Files are eventually consistent with the engine's view of them:
an edit exists before the engine has scanned it.

## Fail-closed reads: eventual freshness, immediate honesty

The boundary is the read barrier, and it fails closed. When a file's hash
does not match its checked state — an unscanned edit, an unmaterialized
output — reads *deny* rather than serve stale trust: content is treated as
unchecked until the scan catches up. Freshness is eventual; honesty is
immediate. No consumer is ever told "checked" about bytes the checks never
saw.

The two planes and the barrier branch that joins them:

```mermaid
flowchart TD
    subgraph acid ["ACID trust plane: a verdict either committed or it didn't"]
        judgment["Judgment state:<br/>verdicts, provenance, the request queue,<br/>the hash-chained event log"]
        sqlite["SQLite under .memoria/<br/>WAL, full synchronous durability,<br/>CHECK constraints,<br/>append-only triggers on the journal"]
        judgment -- "lives in" --> sqlite
    end

    subgraph base ["BASE knowledge plane: an edit exists before the engine has scanned it"]
        files["The knowledge itself: plain files,<br/>edited by the researcher<br/>with any tool at any time"]
    end

    subgraph barrier ["Fail-closed read barrier: freshness is eventual; honesty is immediate"]
        compare{"Does the file's hash match<br/>its checked state?"}
        served["Served as checked"]
        denied["Read denies rather than serving stale trust:<br/>content is treated as unchecked<br/>until the scan catches up"]
        compare -- "matches" --> served
        compare -- "does not match:<br/>an unscanned edit,<br/>an unmaterialized output" --> denied
    end

    sqlite -- "checked state" --> compare
    files -- "file's hash" --> compare
```

## Cross-substrate operations

> **Planned (beta.1):** The complete cross-substrate recovery sequence described below is not yet shipped.

Operations that touch both planes (stage → validate → promote → journal →
git) run as an outbox-style sequence coordinated from SQLite, with
fail-closed recovery as the compensation path: after a crash, every
interrupted machine operation resolves to committed-and-consumable,
retryable-and-pending, or failed-and-hidden. No torn output is ever visible
as checked.

## Durability beyond the database

WAL and synchronous commits protect against a mid-write crash; they do not
protect against a lost or corrupted disk. `memoria workspace backup <target>`
verifies and reconciles the journal, then publishes one complete snapshot
outside the live vault; `memoria workspace restore <source>` validates that
snapshot and restores it. `memoria doctor` fails when a blob has no
corresponding backup — an unbacked blob is a durability gap, not a passing
state.

## Related

- [Memory model](memory-model.md) — which substrate owns which data.
- [OKF and portability](okf-and-portability.md) — why the planes are separate.
- [Failure modes](../../reference/system/failure-modes.md) — the recovery matrix.
- [Back up and restore the workspace](../../how-to-guides/operate/back-up-and-restore-the-workspace.md) — how to run the backup and restore commands.
- [Backup and recovery](../../reference/system/backup-and-recovery.md) — the backup and restore reference.
