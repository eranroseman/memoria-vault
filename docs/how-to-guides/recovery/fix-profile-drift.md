---
title: Fix profile drift
parent: Recovery
nav_order: 6
---


# Fix profile drift

Resolve a mismatch where the deployed profile in `~/.hermes/profiles/` doesn't match the vault source in `vault/.memoria/profiles/`.

## Symptom

The Linter's `profile-install-drift` detector reports a SHA-256 mismatch:

```yaml
MEDIUM: profile-install-drift — memoria-linter/SOUL.md hash mismatch
  vault source:   8f4a...
  deployed copy:  3b2c...
```

Or you edited a profile in the vault and the deployed Hermes instance is running stale behavior.

## Detect

```bash
hermes -p memoria-linter chat -s health-report
# then, in the session:
/health-report --detectors profile-install-drift
```

This compares the SHA-256 of every file in `vault/.memoria/profiles/` against its deployed counterpart.

## Diagnose before fixing

There are two causes with different implications:

**Cause A: The vault source changed and the install script hasn't been re-run.**
This is the normal case after a `git pull` or after editing a `SOUL.md`. Fix: re-run the profile-install (`bash scripts/install.sh --profiles-only`, or `.\scripts/install.ps1 -ProfilesOnly` on Windows).

**Cause B: Someone edited the deployed copy directly.**

```powershell
diff (Get-Content "vault\.memoria\profiles\memoria-linter\SOUL.md") `
     (Get-Content "$env:USERPROFILE\.hermes\profiles\memoria-linter\SOUL.md")
```

If the diff shows meaningful changes in the deployed copy (not in the vault source), decide:

- **Promote the edit to vault source:** copy the change into `vault/.memoria/profiles/memoria-<name>/SOUL.md`, commit, then re-deploy (below)
- **Discard the edit:** just re-deploy (it overwrites the deployed copy with the vault source)

## Fix

Re-run the profile-install after resolving Cause A or B (from the repo clone):

```bash
bash scripts/install.sh --profiles-only      # Linux / WSL2
```

```powershell
.\scripts/install.ps1 -ProfilesOnly          # Windows
```

To fix drift on a single profile only:

```bash
bash scripts/install.sh --profiles-only --only memoria-linter
```

```powershell
.\scripts/install.ps1 -ProfilesOnly -Only memoria-linter
```

## Verify

```bash
hermes -p memoria-linter chat -s health-report
/health-report --detectors profile-install-drift
```

No drift reported for any profile.

## Related

- Redeploy profiles (normal workflow): [Redeploy profiles](../maintenance/redeploy-profiles.md)
- Profile configuration: [Configure a profile](../using-hermes-agent/configuration.md)
- Full failure-modes catalog: [Failure modes](../../reference/failure-modes.md)
- The idempotency mechanism behind the fix: [Distribution model](../../explanation/deployment/distribution-model.md)
