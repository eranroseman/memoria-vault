---
topic: dashboards
---

# `skill-lifecycle` — design summary

> **Status: deferred — maybe later if needed.** This dashboard depends on the [skill governance discipline](../../project/roadmap/skill-governance.md), which is itself deferred. The design summary below is preserved for the case where skill governance is later stood up; the dashboard would ship at that point, not before. See [future-directions.md §"Skill governance"](../../project/roadmap/future-directions.md#skill-governance) for the deferral context.

**Runtime artifact (when activated).** Ships at `00-meta/01-dashboards/skill-lifecycle.md` in the [starter vault](https://github.com/eranroseman/memoria-vault) and runs in Obsidian via Dataview; the runtime queries would live there once the feature is active. This page covers the design role.

## Mission

Track every Hermes skill across the lifecycle: `intake → proposed → scaffolded → testing → needs-review → approved → active → archived`. Open when adding a new skill, promoting a `rest-passthrough` use to a dedicated skill, or auditing what each lane can call. The dashboard's job is to make the skill registry queryable from inside Obsidian without dropping to the CLI — useful when designing or reviewing skill onboarding.

## What this dashboard is not

- **Not the authoritative skill registry.** The authoritative entries are `skill-note` files in `00-meta/07-skills/` (one per skill). This dashboard is a *view* over them.
- **Not the Hermes-side runtime registry.** The Hermes skill registry is what each profile actually loads at session start (controlled by `policy.allow.skills` in each lane-override). Skill-lifecycle is the *design-side* registry — what skills exist and their lifecycle stage, which is upstream of Hermes loading.
- **Not actionable on its own.** Adding a skill, promoting a stage, or archiving requires editing the relevant `skill-note` file directly (or running the onboarding checklist). Skill-lifecycle shows the *current state*, not the *next action* (beyond making stalled stages visible).

## Design decisions

- **Reads `00-meta/07-skills/` for `type: skill-note`.** Each skill is one note with frontmatter (`skill_name`, `lane`, `networked`, `owner`, `stage`, `updated_at`, `next_action`).
- **Two sections: active by lane, onboarding pipeline.** The active view answers "what can each lane do right now?" — sorted by lane, then skill name. The onboarding view answers "what's in flight?" — anything not yet `active`, sorted by stage.
- **Two-week stall threshold.** If a skill sits in `testing` or `needs-review` for more than two weeks, it's stalled — the human should promote, archive, or remove the entry. The threshold is a documented heuristic in the dashboard, not enforced.
- **Graceful degradation.** Until the human has authored ~5+ skill-notes, the dashboard is a placeholder — the discipline only matters once skill count is non-trivial. Recommended timing: enable with the skill-governance discipline (see roadmap).

## Related

- [roadmap/skill-governance.md](../../project/roadmap/skill-governance.md) — the lifecycle state machine, onboarding checklist, registry format
- [profiles/README.md](../profiles/README.md) — per-lane `policy.allow.skills` declarations; skills listed there should appear here in `stage: active`
- [glossary.md](../../reference/glossary.md) — "restrictive skill" and skill-conditional policy definitions
