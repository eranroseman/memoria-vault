# How to use the Memoria issue-tracking system

**Status:** working guide (scratch). If it proves useful, graduate it to `docs/contributing/`.
**Date:** 2026-06-14

This describes how issues are organized after the alpha.3 tracker cleanup: one **GitHub Project** carries the planning metadata as *fields*, **milestones** carry release phase, **sub-issues** carry hierarchy, and **labels** are kept minimal. The guiding rule: **each kind of metadata lives on the feature that models it best, never duplicated across two.**

---

## 1. The pieces (and what each is for)

| Surface | Role | Don't also use for |
|---|---|---|
| **Issue** | the atomic unit of work (one bug / feature / task / question) | multi-topic dumps — split them |
| **Project #1 — "Memoria Issue Tracker"** ([link](https://github.com/users/eranroseman/projects/1)) | the triage + planning surface; holds the **Status / Area / Type / Priority** fields and the board/table views | — |
| **Milestone** | **release phase** only: `0.1.0-alpha.2/3/4`, `0.1.0` | a Type or Status (the project fields do that) |
| **Sub-issues** (parent ⇄ child) | hierarchy / epics: a big issue composed of smaller ones | "related to" (that's just a mention) |
| **Labels** | repo-wide search chips (`bug`, `documentation`) + bot automation | Type/Area/Status/Priority — those are fields now |
| **ADRs** (`docs/adr/`) | **decisions** (what + why + alternatives), at any status | task tracking — that's an issue |

The mental model: **an issue is the work; the Project fields are how you slice the work; the milestone is when; the ADR is why.**

---

## 2. The Project fields (the core of the system)

Set these on every issue from the Project (board or table view). Issue creation only gives you Title + Body + Labels + Milestone; the four fields below are set in the Project.

### Status — where the work is (exactly one)
| Value | Meaning |
|---|---|
| **Backlog** | accepted, not started (the default for active work) |
| **In progress** | being worked now |
| **In review** | PR open / awaiting review |
| **Done** | merged/closed |
| **Deferred** | parked — not this phase (alpha.4+, deferred ADRs, future transports). Revisit each release cycle, don't delete. |

*(Optional additions if you want them: `Needs scoping` for vague issues, `Blocked` for waiting-on-another. Add via Project settings → Status field. Don't edit the field via API — it can wipe existing values.)*

### Area — which subsystem (one, sometimes more)
| Value | Covers |
|---|---|
| **capture** | fleeting / URL / Zotero capture, capture forms |
| **ingest** | the ingest pipeline, metadata sources, extraction, scoring |
| **knowledge** | notes / claims / links / hubs, schema, vocabulary, projects |
| **obsidian-ui** | workspaces, home.md, dashboards, status bar, properties, client-agent pane |
| **operations** | the deterministic engines (Processing/Integrity/Cleanup/Telemetry), Linter, policy gate |
| **docs-site** | the Jekyll/Diátaxis docs and ADRs |
| **installer** | install / upgrade / golden-copy / platform / deployment |
| **integrations** | Zotero, MCP, external tools, messaging transports |
| **agents** | profiles, Co-PI, skills, lanes, model selection |
| *(blank)* | meta/positioning research with no subsystem fit |

> Naming note: "operations" matches [ADR-69](../../../adr/69-operations-layer-naming.md) (the layer formerly called "engines"). Its four categories — Processing · Integrity · Cleanup · Telemetry — are the *sub-kinds* of operations work; keep the Area as `operations` and say which category in the issue body.

### Type — what kind of work (exactly one)
| Value | Use for | (old label) |
|---|---|---|
| **Bug** | something is broken | `bug` |
| **Feature** | new capability | most `enhancement` |
| **Refactor** | internal restructure/rename/cleanup, no behavior change | `enhancement` |
| **Docs** | documentation work | `documentation` |
| **Research** | open investigation / question | `research`, `question` |
| **Decision** | needs an ADR (or an ADR's acceptance/scoping call) | `enhancement` |

### Priority — how urgent (exactly one)
| Value | Reserve for |
|---|---|
| **High** | blockers — e.g. defects that break a tutorial / the core loop. Keep this set small so it stays meaningful. |
| **Normal** | the default for real work |
| **Low** | nice-to-have, parked, or research |

---

## 3. Workflows

### Filing a new issue
1. **Create the issue** (`gh issue create` or web): clear Title; Body with problem statement, concrete file paths / repro (for bugs), and **Acceptance criteria**.
2. **Add it to the Project** (auto-add workflow should do this; otherwise add manually).
3. **Set the fields:** Type (always), Area (always, unless meta), Priority, Status (`Backlog`).
4. **Set the Milestone** only if you're scheduling it into a release; otherwise leave blank (= backlog of unscheduled work).
5. If it's a **decision**, also open/point to an ADR and set Type `Decision`.

### Triaging the backlog
Open the Project **table view**, filter `Status: <empty>` or `No milestone`, and fill Type/Area/Priority. Multi-select rows that share a value and set it once (e.g. select all `ingest` issues → set Area).

### Working an issue
`Backlog` → `In progress` (assign yourself) → open a PR → `In review` → merge → `Done`. Keep the issue's acceptance criteria honest; close only when they're met (reproduce bug fixes live).

### Deferring
Set Status `Deferred`. If it's a deferred *decision*, it's an ADR with `status: deferred` (the issue just tracks it). Deferred items are revisited each release cycle — they're not a to-do that fired and got parked.

### Umbrellas / epics → sub-issues
For a big issue composed of smaller ones, make the small ones **sub-issues** of the parent (Project "Parent issue" field, or the issue's sub-issues panel). Examples already wired:
- **#443** (docs describe unbuilt behavior) → #375, #376, #377, #343
- **#465** (accept ADR-69 + rename) → #466, #472

The parent shows a **Sub-issues progress** bar automatically.

### Closing vs keeping
Close when done or obsolete. For an *answered research question*, either close with the finding or leave open at `Status: Backlog`, `Priority: Low` (don't let it masquerade as active work).

---

## 4. Views worth having in the Project
- **Board grouped by Status** — the kanban for day-to-day ("what's in progress / what's next").
- **Table grouped by Area** — see the whole backlog by subsystem; best for triage and bulk edits.
- **Table filtered `Milestone: 0.1.0-alpha.3`, sorted by Priority** — the current release plan.
- **Filter `Status: Deferred`** — the parked set (replaces the old "deferred" label hunt).

Useful filters: `field:Area:capture`, `field:Type:Bug`, `field:Priority:High`, `milestone:"0.1.0-alpha.3"`.

---

## 5. Labels — the minimal set
Keep labels to what needs repo-wide search or bot automation:
- **Search chips:** `bug`, `documentation` (mirror the Type field for `is:issue label:bug` search).
- **Bot-managed (don't rename/delete):** `dependencies`, `python`, `github_actions` (Dependabot); `release`, `autorelease: pending`, `autorelease: tagged` (release-please).

Retired (their signal moved to fields): `enhancement`→Type, `question`/`research`→Type:Research, `needs-scoping`→Status. **Don't recreate them** — add a Type/Status value instead.

The one trade-off: Project fields filter only *inside* the Project; repo-wide `is:issue` search and bots see labels. That's why `bug`/`documentation` stay as labels.

---

## 6. CLI notes (gotchas worth knowing)

- **Projects need a project-scoped token.** The ambient `GITHUB_TOKEN` here is repo-scoped only, so `gh project …` fails with "unknown owner type". Use the keyring PAT by stripping the env token:
  ```bash
  env -u GITHUB_TOKEN -u GH_TOKEN gh project list --owner eranroseman
  ```
- **Set a field on an item:**
  ```bash
  env -u GITHUB_TOKEN -u GH_TOKEN gh project item-edit \
    --project-id PVT_kwHODLXZf84BZv4R \
    --id <ITEM_ID> --field-id <FIELD_ID> --single-select-option-id <OPTION_ID>
  ```
  Get `<ITEM_ID>` from `gh project item-list 1 --owner eranroseman --format json` (map `content.number` → `id`); get field/option IDs from `gh project field-list 1 --owner eranroseman --format json`.
- **Link a sub-issue:**
  ```bash
  gh api -X POST repos/eranroseman/memoria-vault/issues/<PARENT>/sub_issues \
    -F sub_issue_id=<CHILD_DB_ID>     # child's .id, not its number
  ```
- **Bulk edits:** setting many fields/items via API is slow and can trip the harness's external-write guard. For large passes, prefer the **table view** (multi-select rows → set field). The one-time alpha.3 population was done via the API in one scripted batch (184 edits); see `project-field-mapping.md` for the per-issue values.
- **Don't bulk-edit milestones/labels across many issues you didn't author via API** — that's hard-blocked; do it in the UI or one at a time.

---

## 7. Conventions (the rules in one place)

1. **One Type, one Status, one Priority; one+ Area.** Every active issue has all four set.
2. **Milestone = release phase only.** Don't encode type/status as a label or milestone.
3. **High priority is for blockers.** If everything is High, nothing is.
4. **Decisions are ADRs.** Type `Decision` on the issue; the rationale lives in `docs/adr/`.
5. **Deferred is a Status, not a graveyard.** Re-judge the Deferred set each release cycle.
6. **Umbrellas use sub-issues**, not a tracking label.
7. **Don't recreate retired labels** — add a field value.
8. **Acceptance criteria on every issue** before it leaves Backlog; reproduce bug fixes live before closing.

---

## 8. Cheat sheet

- New work → file issue (Title + Body + **Acceptance**) → set **Type/Area/Priority**, Status `Backlog` → Milestone if scheduling.
- Triage → table grouped by Area → multi-select → set fields.
- Plan a release → filter by Milestone, sort by Priority.
- Park it → Status `Deferred` (+ ADR if it's a decision).
- Big thing → parent issue + **sub-issues**.
- Find it later → Project filters (Area/Type/Priority) or `is:issue label:bug` for the two search chips.
- Per-issue field values for the current backlog: `project-field-mapping.md`.
