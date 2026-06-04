---
topic: proposals
id: PROP-10
title: Skill governance and lifecycle
status: deferred
created: 2026-05-31
---

# PROP-10: Skill governance and lifecycle

Not part of the active design. Adding a skill today means editing `policy.allow.skills` in a lane-override file and dropping the `SKILL.md` into the right profile's `skills/` folder. That's sufficient until the human is regularly graduating passthrough-skills to dedicated ones or coordinating cross-lane permission changes.

## What

A formal lifecycle for skills: a state machine (`intake → proposed → scaffolded → testing → needs-review → approved → active → archived`), per-skill governance notes in `99-system/skills/`, a `skill-lifecycle` dashboard, and a 7-step onboarding checklist for new skills.

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

## Alternatives considered

**Keep the runtime mechanism (the current state).** Lane-override `policy.allow.skills` + a dropped `SKILL.md` is enough while skill count is low and graduations are rare; the bookkeeping fits in the human's head. Held until the adoption trigger fires.

**Stand up only the dashboard, skip the state machine.** A possible partial adoption (visibility without the lifecycle overhead). Defer the choice between full lifecycle and dashboard-only until the actual pain is known — confusion about *what's active* wants the dashboard; uncontrolled *graduations* want the state machine.

## Related

- **Runtime mechanism:** lane-override files (`policy.allow.skills`) + per-profile `skills/` folders.
- **Placeholder:** `99-system/skills/` ships empty until this is stood up (see [on-disk-layout.md](../../docs/reference/on-disk-layout.md)); the `skill-lifecycle` dashboard activates in the same phase ([release-plan-v0.1-appendix.md](../releases/v0.1/release-plan-v0.1-appendix.md)).

## Dependencies

None beyond the runtime mechanism that already exists. Standing up the governance layer is mostly authoring per-skill notes in `99-system/skills/` and enabling the dashboard.
