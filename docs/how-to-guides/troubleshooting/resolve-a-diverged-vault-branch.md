---
title: Recover a divergent vault branch
parent: Troubleshooting
grand_parent: How-to guides
nav_order: 7
---

# Recover a divergent vault branch

Use this procedure only when the vault's Git history unexpectedly diverges.
Memoria supports one local workstation and one writer. Git provides history and
recovery, not a multi-writer runtime synchronization path.

Do not use this guide to resolve an ordinary source-code repository conflict.
It restores one coherent vault lineage: the selected Git revision, its
`.memoria/journal-head`, and the matching SQLite-and-blob snapshot.

## Steps

**1. Stop every writer and preserve the evidence.**

Stop the CLI, workers, and any scheduled tasks that can write either vault.
Before selecting, checking out, restoring, or replacing anything, preserve
both Git histories and every available backup. Work only in a copy made for
recovery; retain the original vault directories and backup targets unchanged.

Record each candidate's Git commit and working-tree state for the PI:

```bash
cd <candidate-vault>
git rev-parse HEAD
git status --short
```

Do not discard uncommitted work, reset either history, or choose a side of a
conflicting `.memoria/journal-head`. Memoria has no command to merge two
journal-bearing histories or their SQLite event chains.

**2. Select one authoritative lineage.**

The PI chooses the known-good Git lineage and, when runtime state needs
restoring, its matching backup. A matching backup carries the event chain and
the journal head that belong to the selected lineage. The other lineage remains
preserved evidence; it is not imported or merged.

Stop here if authority is uncertain, no matching backup is available, or the
selected history cannot show that its committed journal-head anchor belongs to
the candidate event chain. Do not improvise a generic Git repair.

**3. Check out the matching Git revision in the recovery copy.**

In the preserved copy designated for recovery, check out the revision from the
authoritative lineage:

```bash
cd <recovery-vault>
git checkout <authoritative-revision>
```

That revision supplies the committed anchor that restore and journal
verification use. Checking it out does not reconcile runtime state.

**4. Restore the matching snapshot when the local runtime state is not already coherent.**

If the recovery copy does not retain the authoritative runtime state, restore
the matching backup into that copy:

```bash
memoria workspace restore --workspace <recovery-vault> <matching-backup> --force
```

Restore validates the snapshot and refuses a chain whose head does not contain
the selected revision's committed anchor. If it refuses, preserve its output
and stop. Do not substitute a different backup or edit `journal-head` to make
the check pass.

**5. Verify the recovered journal, then scan the workspace.**

Only after the selected Git revision and its matching runtime state are in the
same recovery copy, run:

```bash
memoria journal verify --workspace <recovery-vault>
memoria workspace scan --workspace <recovery-vault>
```

Run the scan only when `journal verify` succeeds. Verification checks the
authoritative event chain, the live head, the committed-anchor prefix, and the
derived JSONL export subset. The scan can then perform its normal maintenance
and observed-edit work, including reconciling or re-emitting derived JSONL
exports. It does not reconcile Git branches or merge histories.

If verification or the scan fails, stop writers and retain the copy, both
histories, backups, and command output for PI inspection.

## After recovery

Any content wanted from the non-authoritative branch is reintroduced only after
the recovery passes verification, as a deliberate PI edit through the normal
observed-writer path. Do not merge its SQLite database, journal, or derived
JSONL files into the recovered vault.

## Related

- Pre-session local-health checks: [Return to work](../inbox/return-to-work.md)
- Backup and restore procedure: [Back up and restore the workspace](../operate/back-up-and-restore-the-workspace.md)
- Full backup and journal-validation contract: [Backup and recovery](../../reference/system/backup-and-recovery.md)
- Recovery symptom catalog: [Failure modes](../../reference/system/failure-modes.md)
