# `skill-lifecycle.md` — Hermes skill registry view

**Location.** `00-meta/05-dashboards/skill-lifecycle.md`

**Decision.** Track every Hermes skill across the lifecycle (`intake → proposed → scaffolded → testing → needs-review → approved → active → archived`). Open when adding a new skill, promoting a `generic-rest-bridge` use to a dedicated skill, or auditing what each lane can call.

See [07-roadmap.md](../07-roadmap/skill-governance.md) for the state machine and onboarding checklist.

## Active skills by lane

The operational map. If a lane in [02-profiles.md](../02-profiles.md#lane-permissions-matrix) says it allows a skill, that skill should be visible here in `stage: active`.

```dataview
TABLE skill_name AS Skill, lane AS Lane, networked AS Networked, owner AS Owner, updated_at AS Updated
FROM "00-meta/07-skills"
WHERE type = "skill-note" AND stage = "active"
SORT lane ASC, skill_name ASC
```

## Onboarding pipeline

Skills not yet `active`. If anything sits in `testing` or `needs-review` for more than two weeks, it's stalled — promote, archive, or remove the entry.

```dataview
TABLE skill_name AS Skill, lane AS Lane, stage AS Stage, next_action AS "Next action", updated_at AS Updated
FROM "00-meta/07-skills"
WHERE type = "skill-note" AND stage != "active" AND stage != "archived"
SORT stage ASC, updated_at ASC
```

## Networked skills (external API surface)

The full set of skills that can make outbound network calls. Should be a small list, lane-restricted to Research. Anything here on Writer, Socratic, Cartographer, Verifier, or Linter lanes is a configuration bug.

```dataview
TABLE skill_name AS Skill, lane AS Lane, stage AS Stage
FROM "00-meta/07-skills"
WHERE type = "skill-note" AND networked = true AND stage = "active"
SORT lane ASC, skill_name ASC
```

## REST-bridge promotion candidates

Skills that started as `generic-rest-bridge` invocations and have crossed the promotion threshold (see [07-roadmap.md](../07-roadmap/skill-governance.md#bridge-to-dedicated-skill-graduation)). Track usage manually here until the audit log can be queried for endpoint frequency.

| Endpoint | Bridge call count | Auth complexity | Output normalization needed | Status |
| --- | --- | --- | --- | --- |
| _Add candidates as they emerge from the audit log._ | | | | |

## Stale skills (4-week review checkpoint)

Active skills that haven't been touched in 4+ weeks. Either confirm they're still in use, archive them, or update the skill-note with what changed.

```dataview
TABLE skill_name AS Skill, lane AS Lane, updated_at AS Updated
FROM "00-meta/07-skills"
WHERE type = "skill-note" AND stage = "active" AND updated_at < date(today) - dur(28 days)
SORT updated_at ASC
```

## Archived skills

Retained for history. Removed from `policy.allow.skills` in the lane-override files; cannot claim work.

```dataview
TABLE skill_name AS Skill, lane AS "Last lane", updated_at AS Archived
FROM "00-meta/07-skills"
WHERE type = "skill-note" AND stage = "archived"
SORT updated_at DESC
```
