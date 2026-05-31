---
status: deferred
created: 2026-05-31
---

# Skill governance and lifecycle

**Status: deferred — not part of the active design.** Adding a skill today means editing `policy.allow.skills` in a lane-override file and dropping the `SKILL.md` into the right profile's `skills/` folder. That's sufficient until the human is regularly graduating passthrough-skills to dedicated ones or coordinating cross-lane permission changes.

---

## What

A formal lifecycle for skills: a state machine (`intake → proposed → scaffolded → testing → needs-review → approved → active → archived`), per-skill governance notes in `00-meta/07-skills/`, a `skill-lifecycle` dashboard, and a 7-step onboarding checklist for new skills.

## Why

At low skill count, adding a skill is a runtime operation — it works without the governance overlay. At high skill count, bookkeeping in someone's head stops being sufficient: which skills are active in which lane? Which passthrough skills are candidates for graduation to dedicated skills? Which skills are stale?

## Trade-offs

Standing up the governance layer requires authoring per-skill notes for every existing skill retroactively. The onboarding checklist adds friction to adding new skills. Worth it only when the problem it solves is actually occurring.

## Adoption trigger

At least two of these are true:
- > 15 active skills across the seven profiles
- ≥ 2 passthrough-to-dedicated graduations per quarter
- Recurring confusion about which skills are active in which lane

## Guard

Do not stand up the governance layer as a preparatory measure. The runtime mechanism (lane-override files + SKILL.md) works correctly without it; the governance layer is a bookkeeping overlay, not a safety gate.

## Dependencies

None beyond the runtime mechanism that already exists. Standing up the governance layer is mostly authoring per-skill notes in `00-meta/07-skills/` and enabling the dashboard.
