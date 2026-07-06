# Release

Use this playbook when starting, managing, or cutting a Memoria release.
Release state lives in GitHub; this playbook is the portable agent procedure.

## 1. Use the single sources of state

- **Scope** lives in the GitHub milestone plus the Memoria Issue Tracker table
  filtered to that milestone.
- **Readiness** lives in the **"Release <version>"** parent issue and its gate/stage
  sub-issues.
- **Release prose** lives in the release parent issue. Use
  [the release plan template](../templates/release-plan.md) as a drafting aid.
- **Build gaps** live as GitHub issues.
- **Scope cuts** live as GitHub issues with Readiness `Later`; release decision
  entries record the decision or rationale only when there is one.
- **Version and notes** are owned by release-please.
- **In-work release design notes** live on the `scratch` branch under
  `releases/<version>/` on the `scratch` branch while the release is being shaped and are deleted
  before the release/checkpoint is done.

Do not create a second markdown state table for gate or stage progress.

> **Token prerequisite.** release-please authenticates with the fine-grained
> `RELEASE_PLEASE_TOKEN` secret, **not** the default `GITHUB_TOKEN` (whose PRs do not
> trigger the required checks, so a release PR can never go green). Scopes, rationale, and
> the rotate-before-expiry rule live in the workflow comments
> ([`.github/workflows/release-please.yml`](../../.github/workflows/release-please.yml)) —
> releases break *silently* if the PAT lapses.

## 2. Start a release

1. Draft the release parent issue body from
   [`.agents/templates/release-plan.md`](../templates/release-plan.md).
2. Create the GitHub milestone:

   ```bash
   gh api repos/eranroseman/memoria-vault/milestones -f title=0.1.0
   ```

3. Assign scoped issues to the milestone and use the Memoria Issue Tracker table
   filtered to that milestone, using Status and Readiness as the live release state.
4. Open the **"Release <version>"** parent issue with label `release` and milestone
   `<version>`.
5. Create one sub-issue per gate/stage (`G#`, `S#`). Each sub-issue carries its
   own evidence, owner, comments, and close condition.
6. Put temporary tracked design scratch on the `scratch` branch under
   `releases/<version>/` on the `scratch` branch only when it must survive handoff.

## 3. Cut a release or checkpoint

1. Confirm every gate/stage sub-issue is closed, required CI is green on `main`,
   and no release-milestone issue has `Readiness: Blocked`.
2. Re-run the relevant Release Gate checks from a fresh clone or record why a
   check is not applicable.
3. Fold accepted/rejected release decisions into `design-history/`, update
   `design-history/arcs.md` with current and pending lines, and update
   `design-history/README.md`'s latest completed checkpoint marker.
4. Merge the release-please PR for formal releases. It owns version bump,
   changelog, tag, and GitHub Release notes.
5. Close the milestone and release parent issue, rolling unfinished issues forward.
6. Delete `releases/<version>/` design notes from the `scratch` branch
   before calling the release/checkpoint done, after routing durable content to
   `design-history/`, docs, or issues.

## 4. Verify

Run:

```bash
python scripts/checks/status_doctor.py
python scripts/checks/docs_doctor.py docs
```

For release/process changes that touch agent guidance, also run:

```bash
python scripts/checks/agents_doctor.py
```

Report which GitHub state changes were made, which could not be made locally, and
which agent guidance or templates changed.
