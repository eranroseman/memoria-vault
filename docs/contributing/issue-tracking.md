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
| **Project #1 — [Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1)** | Triage and planning surface; holds **Status / Readiness / Area / Type / Priority** fields and board/table views | Release prose or decision rationale |
| **Milestone** | Release phase only: `0.1.0-alpha.3`, `0.1.0-alpha.4`, `0.1.0` | Type, Status, Readiness, Priority, or Area |
| **Sub-issues** | Hierarchy / epics; a big issue composed of smaller issues | Loose "related to" links; use a mention for that |
| **Labels** | Repo-wide search chips and bot automation | Type, Area, Status, Readiness, or Priority |
| **ADRs** | Decisions: what, why, alternatives, and consequences | Task tracking |

The mental model: **an issue is the work; Project fields are how you slice the
work; the milestone is when; the ADR is why.**

## Project fields

Set these on every active issue from the Project board or table view. Issue
creation gives you title, body, labels, and milestone; the fields below live in
the Project.

### Status

| Value | Meaning |
|---|---|
| **Backlog** | Accepted, not started; the default for real work |
| **In progress** | Being worked now |
| **In review** | PR open or awaiting review |
| **Done** | Merged or closed |

Status is workflow-only: it answers "where is this in the work loop?" Keep the
order as Backlog -> In progress -> In review -> Done. Do not use Status for
blocked, deferred, research, or scoping state; that signal lives in Readiness.
If a status option must change, do it in the UI; API edits to single-select
options can erase existing item values.

### Readiness

| Value | Meaning |
|---|---|
| **Ready** | Clear enough to schedule or pick up |
| **Needs scoping** | Problem is real, but shape or acceptance criteria are unclear |
| **Research question** | Investigation or an answer is needed before implementation |
| **Blocked** | Cannot proceed until an internal or external dependency changes |
| **Future / deferred** | Valid idea intentionally parked for a later cadence review |

Readiness answers "why isn't this being worked right now?" A `Blocked` issue
should name the dependency in its body. A `Future / deferred` issue stays in
Status `Backlog` and is revisited during release cadence review; if it is a
deferred decision, the ADR itself carries `status: deferred`.

### Area

| Value | Covers |
|---|---|
| **capture** | Fleeting / URL / Zotero capture, capture forms |
| **ingest** | Ingest pipeline, metadata sources, extraction, scoring |
| **knowledge** | Notes, claims, links, hubs, schema, vocabulary, projects |
| **obsidian-ui** | Workspaces, `home.md`, dashboards, status bar, properties, client-agent pane |
| **operations** | Deterministic operations: Processing / Integrity / Cleanup / Telemetry, Linter, policy gate |
| **docs-site** | Jekyll / Diataxis docs and ADRs |
| **installer** | Install, upgrade, golden copy, platform, deployment |
| **integrations** | Zotero, MCP, external tools, messaging transports |
| **agents** | Profiles, Co-PI, skills, lanes, model selection |
| *(blank)* | Meta / positioning research with no subsystem fit |

`operations` follows [ADR-69](../adr/69-operations-layer-naming.md). Its four
categories are sub-kinds of operations work; keep Area as `operations` and name
the category in the issue body.

### Type

| Value | Use for | Former label |
|---|---|---|
| **Bug** | Something is broken | `bug` |
| **Feature** | New capability | most `enhancement` |
| **Refactor** | Internal restructure / rename / cleanup, no behavior change | `enhancement` |
| **Docs** | Documentation work | `documentation` |
| **Research** | Open investigation or question | `research`, `question` |
| **Decision** | Needs an ADR or an ADR acceptance/scoping call | `enhancement` |

### Priority

| Value | Reserve for |
|---|---|
| **High** | Release or core-loop urgency, for example defects that break a tutorial |
| **Normal** | Default for real work |
| **Low** | Nice-to-have, parked, or research |

Keep High small; if everything is High, nothing is. Use Readiness `Blocked` for
dependency-blocked work; do not make every blocked item High.

## Field colors

GitHub single-select fields have eight colors. Use color semantically where it
matters and categorically where it does not:

| Field | Option colors |
|---|---|
| **Status** | Backlog `Gray`, In progress `Blue`, In review `Orange`, Done `Green` |
| **Readiness** | Ready `Green`, Needs scoping `Orange`, Research question `Yellow`, Blocked `Red`, Future / deferred `Purple` |
| **Priority** | High `Red`, Normal `Yellow`, Low `Gray` |
| **Type** | Bug `Red`, Feature `Green`, Refactor `Purple`, Docs `Blue`, Research `Yellow`, Decision `Orange` |
| **Sub-issues progress** | `Purple` bar, segmented, numerical value shown |
| **Area** | Auto-color; there are more areas than colors |

Set colors in Project settings -> field -> option color picker.

## Workflow

### Filing a new issue

1. Create the issue with a clear title, problem statement, concrete paths or repro
   steps for bugs, and **acceptance criteria**.
2. Add it to [Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1)
   if the auto-add workflow did not do it.
3. Set Type, Area, Priority, Readiness, and Status `Backlog`.
4. Set a milestone only when scheduling it into a release; no milestone means
   unscheduled backlog.
5. If it is a decision, open or point to an ADR and set Type `Decision`.

### Triaging

Use the Project table view. Filter for missing field values or no milestone, then
bulk-edit rows that share a value. Prefer UI multi-select for large passes.

### Working

Move `Backlog -> In progress`, assign yourself, open a PR, then move to `In review`.
When the PR merges and acceptance criteria are met, close the issue as `Done`.
Bug fixes should be reproduced before closing.

### Parking, blocking, or scoping

Keep Status `Backlog` and set Readiness:

- `Future / deferred` for valid work intentionally parked outside the current
  release phase.
- `Blocked` for work waiting on a named dependency.
- `Needs scoping` for work whose acceptance criteria or design shape are not
  clear enough to schedule.
- `Research question` for investigations that must answer "what should we do?"
  before implementation.

Deferred items are revisited each release cycle, not forgotten. If it is a
deferred decision, the ADR itself carries `status: deferred`; the issue only
tracks the work.

### Umbrellas / epics

For a big issue composed of smaller ones, make the small issues sub-issues of the
parent. The parent issue then exposes the Sub-issues progress field automatically.
Use ordinary mentions for loose related work.

## Project views

Keep these views in [Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1):

- **Board grouped by Status** for day-to-day flow.
- **Table grouped by Area** for triage and bulk edits.
- **Table grouped by Readiness** for blocked, research, scoping, and future-work
  review.
- **Table filtered by the current milestone**, sorted by Priority, for the release
  plan.
- **Filter `Readiness: Future / deferred`** for the parked set.

Useful filters include `field:Area:capture`, `field:Type:Bug`,
`field:Priority:High`, `field:Readiness:Blocked`, and
`milestone:"0.1.0-alpha.3"`.

## Labels

Keep labels to what needs repo-wide search or bot automation:

- Search chips: `bug`, `documentation`.
- Bot-managed labels: `dependencies`, `python`, `github_actions`, `release`,
  `autorelease: pending`, `autorelease: tagged`.

Do not recreate retired labels such as `enhancement`, `question`, `research`, or
`needs-scoping`; their signal moved to Project fields. The trade-off is that
Project fields filter inside the Project, while repo-wide `is:issue` search and
bots see labels. That is why `bug` and `documentation` stay as search labels.

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

1. One Type, one Status, one Readiness, one Priority; one or more Areas when applicable.
2. Milestone means release phase only.
3. High priority is for blockers.
4. Decisions are ADRs; issues track the work around them.
5. Status is workflow; Readiness carries blocked, scoping, research, and future/deferred state.
6. Umbrellas use sub-issues, not tracking labels.
7. Retired labels stay retired.
8. Acceptance criteria exist before an issue leaves Backlog.
