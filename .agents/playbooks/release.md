# Release

Use this playbook when starting, managing, or cutting a Memoria release.
[`docs/releasing/README.md`](../../docs/releasing/README.md) owns the durable
process prose; this playbook is the portable agent procedure for applying it.

## 1. Use the single sources of state

- **Scope** lives in the GitHub milestone plus the Memoria Issue Tracker table
  filtered to that milestone.
- **Readiness** lives in the **"Release vX.Y"** parent issue and its gate/stage
  sub-issues.
- **Prose** lives in `docs/releasing/<version>/release-plan-<version>.md`.
- **Build gaps** live as GitHub issues.
- **Scope cuts** live as deferred-status ADRs in `docs/adr/`.
- **Version and notes** are owned by release-please.
- **In-work release design notes** live under `docs/releasing/<version>/tmp/`
  while the release is being shaped and are deleted before the release/checkpoint
  is done.

Do not create a second markdown state table for gate or stage progress.

> **Token prerequisite.** release-please authenticates with the fine-grained
> `RELEASE_PLEASE_TOKEN` secret, **not** the default `GITHUB_TOKEN` (whose PRs do not
> trigger the required checks, so a release PR can never go green). Scopes, rationale, and
> the rotate-before-expiry rule live in the workflow comments
> ([`.github/workflows/release-please.yml`](../../.github/workflows/release-please.yml)) and
> [ADR-45](../../docs/adr/45-release-management-model.md) — releases break *silently* if the
> PAT lapses.

## 2. Start a release

1. Create `docs/releasing/<version>/README.md` as a thin index.
2. Copy `docs/releasing/release-plan-template.md` to
   `docs/releasing/<version>/release-plan-<version>.md`.
3. Fill the plan prose and set frontmatter to `status: draft` and `released: false`.
4. Create the GitHub milestone:

   ```bash
   gh api repos/eranroseman/memoria-vault/milestones -f title=vX.Y
   ```

5. Assign scoped issues to the milestone and use the Memoria Issue Tracker table
   filtered to that milestone, sorted by Priority, as the live release plan.
6. Open the **"Release vX.Y"** parent issue with label `release` and milestone
   `vX.Y`.
7. Create one sub-issue per gate/stage (`G#`, `S#`). Each sub-issue carries its
   own evidence, owner, comments, and close condition.

## 3. Cut a release or checkpoint

1. Confirm every gate/stage sub-issue is closed, required CI is green on `main`,
   and no High-priority blocker remains open.
2. Re-run the relevant release-candidate stages from a fresh clone or record why
   a stage is not applicable.
3. Retire-sweep ADRs in a small separate PR: delete ADRs whose question this
   release dissolved or superseded, keep the decision memory in git history, and
   regenerate the ADR index.
4. Merge the release-please PR for formal releases. It owns version bump,
   changelog, tag, and GitHub Release notes.
5. Set release-plan frontmatter:
   - Formal release: `status: released`, `released: true`
   - Internal checkpoint: `status: complete`, `released: false`
6. Close the milestone and release parent issue, rolling unfinished issues forward.
7. Delete the release folder's `tmp/` design notes before calling the
   release/checkpoint done.

## 4. Verify

Run:

```bash
python scripts/status-doctor.py
python scripts/docs-doctor.py docs
```

For release/process changes that touch agent guidance, also run:

```bash
python scripts/agents-doctor.py
```

Report which GitHub state changes were made, which could not be made locally, and
which release docs changed.
