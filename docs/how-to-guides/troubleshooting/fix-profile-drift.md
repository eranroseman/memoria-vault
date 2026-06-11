---
title: Fix profile drift
parent: Troubleshooting
nav_order: 6
---


# Fix profile drift

**Symptom:** a deployed Hermes profile runs stale behavior — an edit you made to a `SOUL.md`, skill, or lane-override doesn't show up, or a profile acts like a version you've since changed. The deployed copy in `~/.hermes/profiles/` no longer matches the vault source in `<vault>/.memoria/profiles/`.

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

Exactly the five `memoria-*` profiles — a retired v0.1.0-alpha.1 name (`mapper` / `socratic` / `verifier` / `coder` / `linter`) still registered is drift too; the installer prunes them on the next run.

## Diagnose before fixing

There are two causes with different implications:

**Cause A: The vault source changed and the install script hasn't been re-run.**
This is the normal case after a `git pull` or after editing a `SOUL.md`. Fix: re-run the profile install (below).

**Cause B: Someone edited the deployed copy directly.**

If the diff shows meaningful changes in the deployed copy (not in the vault source), decide:

- **Promote the edit to vault source:** copy the change into `<vault>/.memoria/profiles/memoria-<name>/`, commit, then re-deploy (below)
- **Discard the edit:** just re-deploy (it overwrites the deployed copy with the vault source)

## Fix

Re-run the profile install after resolving Cause A or B (from the repo clone):

```bash
bash scripts/install.sh --profiles-only --vault <vault>      # Linux / WSL2
```

```powershell
.\scripts/install.ps1 -ProfilesOnly          # Windows (forwards to WSL2)
```

To fix drift on a single profile only:

```bash
bash scripts/install.sh --profiles-only --only memoria-librarian
```

```powershell
.\scripts/install.ps1 -ProfilesOnly -Only memoria-librarian
```

## Verify

- The `diff -r` above is clean for every profile (modulo `.env` and placeholders)
- `hermes profile list` shows exactly the five `memoria-*` profiles
- `hermes profile show memoria-<name>` reflects the edit you expected to land

## Related

- Redeploy profiles (normal workflow): [Redeploy profiles](../operate/redeploy-profiles.md)
- Profile configuration: [Configure a profile](../hermes-agent/configuration.md)
- Full failure-modes catalog: [Failure modes](../../reference/failure-modes.md)
- The idempotency mechanism behind the fix: [Distribution model](../../explanation/deployment/distribution-model.md)
