---
title: Fix profile drift
parent: Troubleshooting
grand_parent: How-to guides
nav_order: 6
---


# Fix profile drift

**Symptom:** a deployed Hermes profile runs stale behavior — an edit you made to a `SOUL.md`, skill, or lane-override doesn't show up. The deployed copy in `~/.hermes/profiles/` no longer matches the vault source in `<vault>/.memoria/profiles/`.

**Diagnosis:** either the vault source changed and the install script hasn't been re-run, or someone edited the deployed copy directly. Compare the two to confirm, then decide which case you're in before fixing.

**Fix:** resolve the cause, then re-run the profile install to bring the deployed copy back in sync.

## Detect

Compare the vault source against the deployed copy, per profile:

```bash
diff -r <vault>/.memoria/profiles/memoria-librarian ~/.hermes/profiles/memoria-librarian \
  --exclude .env   # config.yaml will differ by the substituted {{PYTHON}}/{{VAULT_PATH}} placeholders
```

Any difference beyond the `.env` and the placeholder substitutions is drift. Repeat for each of the five profiles (`copi`, `librarian`, `writer`, `peer-reviewer`, `engineer`).

Also confirm the registration list is clean:

```bash
hermes profile list
```

The five `memoria-*` profiles should be present.

## Diagnose before fixing

There are two causes with different implications:

**Cause A: The vault source changed and the install script hasn't been re-run.**
This is the normal case after a `git pull` or after editing a `SOUL.md`. Fix: re-run the profile install (below).

**Cause B: Someone edited the deployed copy directly.**

If the diff shows meaningful changes in the deployed copy (not in the vault source), decide:

- **Promote the edit to vault source:** copy the change into `<vault>/.memoria/profiles/memoria-<name>/`, commit, then re-deploy (below)
- **Discard the edit:** just re-deploy (it overwrites the deployed copy with the vault source)

## Fix

Once you've resolved Cause A or B, run the redeploy procedure — `install.sh --profiles-only` (whole fleet or `--only <profile>`) from the repo clone — per [Redeploy profiles](../operate/redeploy-profiles.md). That guide owns the install flags, the Windows variants, and the idempotency details.

## Verify

- The `diff -r` above is clean for every profile (modulo `.env` and placeholders)
- The redeploy verification passes — `hermes profile list` shows exactly the five `memoria-*` profiles and `hermes profile show memoria-<name>` reflects the edit you expected ([Redeploy profiles](../operate/redeploy-profiles.md))

## Related

- Redeploy profiles (normal workflow): [Redeploy profiles](../operate/redeploy-profiles.md)
- Profile configuration: [Configure a profile](../hermes-agent/configuration.md)
- Full failure-modes catalog: [Failure modes](../../reference/failure-modes.md)
- The idempotency mechanism behind the fix: [Distribution model](../../design/distribution-model.md)
