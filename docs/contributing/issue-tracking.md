---
title: Issue tracking
parent: Contributing
nav_order: 2
---

# Issue tracking

Memoria uses GitHub for live work state and `docs/` for durable process prose. One
**GitHub Project** carries planning metadata as fields, **milestones** carry release
phase, **sub-issues** carry hierarchy, and **labels** stay minimal. The rule is:
each kind of metadata lives on the GitHub feature that models it best, never
duplicated across two places.

## The pieces

| Surface | Role | Do not also use for |
|---|---|---|
| **Issue** | The atomic unit of work: one bug, feature, task, decision, or question | Multi-topic dumps; split them |
| **Project #1 — [Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1)** | Triage and planning surface; holds **Status / Readiness** fields and board/table views | Release prose or decision rationale |
| **Milestone** | Release phase only: `0.1.0-alpha.3`, `0.1.0-alpha.4`, `0.1.0` | Status, Readiness, priority, type, or subsystem |
| **Sub-issues** | Hierarchy / epics; a big issue composed of smaller issues | Loose "related to" links; use a mention for that |
| **Labels** | Repo-wide search chips and bot automation | Status, Readiness, priority, or subsystem taxonomy |
| **ADRs** | Decisions: what, why, alternatives, and consequences | Task tracking |

The mental model: **an issue is the work; Project fields are how you slice the
work; the milestone is when; the ADR is why.**

## Project fields

Set these on every active issue from the Project board or table view. Issue
creation gives you title, body, labels, and milestone; the fields below live in
the Project because they answer questions the issue itself does not answer
cleanly.

### Status

| Value | Meaning |
|---|---|
| **Backlog** | Accepted, not started; the default for real work |
| **In progress** | Being worked now |
| **In review** | PR open or awaiting review |
| **Done** | Merged or closed |

Status is workflow-only: it answers "where is this in the work loop?" Keep the
order as Backlog -> In progress -> In review -> Done. Do not use Status for
blocked, later, or shaping state; that signal lives in Readiness.
If a status option must change, do it in the UI; API edits to single-select
options can erase existing item values.

### Readiness

| Value | Meaning |
|---|---|
| **Ready** | Clear enough to schedule or pick up |
| **Needs shaping** | Problem is real, but investigation, design shape, or acceptance criteria are unclear |
| **Blocked** | Cannot proceed until an internal or external dependency changes |
| **Later** | Valid idea intentionally parked outside the current planning horizon |

Readiness answers "why isn't this being worked right now?" A `Blocked` issue
should name the dependency in its body. A `Later` issue stays in
Status `Backlog` and is revisited during release cadence review. If the work
has an ADR, the ADR records the decision state; the issue records readiness.

## Field colors

GitHub single-select fields have eight colors. Use color semantically where it
matters and categorically where it does not:

| Field | Option colors |
|---|---|
| **Status** | Backlog `Gray`, In progress `Blue`, In review `Orange`, Done `Green` |
| **Readiness** | Ready `Green`, Needs shaping `Orange`, Blocked `Red`, Later `Purple` |
| **Sub-issues progress** | `Purple` bar, segmented, numerical value shown |

Set colors in Project settings -> field -> option color picker.

## Workflow

### Filing a new issue

1. Create the issue with a clear title, problem statement, concrete paths or repro
   steps for bugs, and **acceptance criteria**.
2. Add it to [Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1)
   if the auto-add workflow did not do it.
3. Set Readiness and Status `Backlog`.
4. Set a milestone only when scheduling it into a release; no milestone means
   unscheduled backlog.
5. If it is a decision, open or point to an ADR.

### Triaging

Use the Project table view. Filter for missing field values or no milestone, then
bulk-edit rows that share a value. Prefer UI multi-select for large passes.

### Working

Move `Backlog -> In progress`, assign yourself, open a PR, then move to `In review`.
When the PR merges and acceptance criteria are met, close the issue as `Done`.
Bug fixes should be reproduced before closing.

### Parking, blocking, or shaping

Keep Status `Backlog` and set Readiness:

- `Later` for valid work intentionally parked outside the current planning
  horizon.
- `Blocked` for work waiting on a named dependency.
- `Needs shaping` for work whose investigation, acceptance criteria, or design
  shape are not clear enough to schedule.

Later items are revisited each release cycle, not forgotten. If the item has an
ADR, the ADR records the decision; the issue tracks the work.

### Umbrellas / epics

For a big issue composed of smaller ones, make the small issues sub-issues of the
parent. The parent issue then exposes the Sub-issues progress field automatically.
Use ordinary mentions for loose related work.

## Project views

Keep these views in [Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1):

- **Board grouped by Status** for day-to-day flow.
- **Table grouped by Readiness** for blocked, shaping, ready, and later-work
  review.
- **Table filtered by the current milestone** for the release plan.
- **Filter `Readiness: Later`** for the parked set.

Useful filters include `field:Readiness:Blocked`, `field:Readiness:Ready`, and
`milestone:"0.1.0-alpha.3"`.

## Labels

Keep labels to what needs repo-wide search or bot automation:

- Search chips: `bug`, `documentation`.
- Bot-managed labels: `dependencies`, `python`, `github_actions`, `release`,
  `autorelease: pending`, `autorelease: tagged`.

Do not recreate retired labels such as `enhancement`, `question`, `research`,
`needs-scoping`, or `needs-shaping`; their signal lives in the issue title/body,
ADR links, milestone, or Readiness. The trade-off is that Project fields filter
inside the Project, while repo-wide `is:issue` search and bots see labels. That
is why `bug` and `documentation` stay as search labels.

## CLI notes

Projects need a project-scoped token. If the ambient `GITHUB_TOKEN` is repo-scoped,
`gh project ...` can fail. Use the keyring PAT by stripping the env token:

```bash
env -u GITHUB_TOKEN -u GH_TOKEN gh project list --owner eranroseman
```

Set a field on an item:

```bash
env -u GITHUB_TOKEN -u GH_TOKEN gh project item-edit \
  --project-id PVT_kwHODLXZf84BZv4R \
  --id <ITEM_ID> --field-id <FIELD_ID> --single-select-option-id <OPTION_ID>
```

Get `<ITEM_ID>` from `gh project item-list 1 --owner eranroseman --format json`
and field/option IDs from `gh project field-list 1 --owner eranroseman --format json`.

Link a sub-issue:

```bash
gh api -X POST repos/eranroseman/memoria-vault/issues/<PARENT>/sub_issues \
  -F sub_issue_id=<CHILD_DB_ID>
```

For agents: do not bulk-edit Project fields, milestones, labels, or sub-issues via
API unless the user explicitly asks. Prefer the UI for large human triage passes.

## Rules

1. One Status and one Readiness value per active issue.
2. Milestone means release phase only.
3. Decisions are ADRs; issues track the work around them.
4. Status is workflow; Readiness carries blocked, shaping, ready, and later state.
5. Umbrellas use sub-issues, not tracking labels.
6. Retired labels stay retired.
7. Acceptance criteria exist before an issue leaves Backlog.
