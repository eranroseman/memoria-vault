---
title: skill-state dashboard
parent: Operational health
nav_order: 3
grand_parent: Dashboards
---

# `skill-state` dashboard

Which skills are active in which lane. This is the visibility surface [ADR-43](../../../adr/43-skill-governance.md) adopted when the skill inventory no longer fit in the operator's head: "which lane can do what?" needs an answer that doesn't require opening ten YAML files.

## What it shows

The dashboard reads the runtime governance layer directly at view time — the lane ceilings in `.memoria/lane-overrides/*.yaml` (`policy.allow.skills` / `policy.deny.skills`) and the `SKILL.md` folders each profile ships under `.memoria/profiles/*/skills/` — and renders three views:

- **Lane policy at a glance** — per profile: the runtime skill gates the lane allows and denies, and how many skills the profile actually ships.
- **Shipped skills** — every `SKILL.md` with its declared lane, `skill_id`, and the runtime skills it relies on.
- **Consistency checks** — the decision queue: rows appear only where the lane policy and the shipped skills disagree (a skill folder whose frontmatter contradicts where it ships, a duplicate `skill_id`, a skill relying on a runtime gate its lane denies or doesn't list, a profile with no lane override). Empty is success.

Because it reads the live files rather than a generated snapshot, the dashboard cannot drift from the configuration — it *is* the configuration, rendered.

## What it is not

**Not a lifecycle tracker.** ADR-43's alternative shape — an `intake → … → archived` state machine with per-skill governance notes in `system/skills/` and an onboarding checklist — was explicitly not adopted ([ADR-43](../../../adr/43-skill-governance.md) records why). A skill has no recorded state beyond *shipped and allowed*; the lane-override files plus the profile `skills/` folders are the system of record.

**Not an enforcement surface.** The policy gate and the profile configs enforce; the Linter monitors; this dashboard only renders ([ADR-49](../../../adr/49-catalog-in-bases-linter-monitor.md): dashboards are the view layer). An "outside the allow list" row is a question for the operator, not a block — the dependency may be an MCP server governed by `config.yaml` rather than a skill gate.

## Related

- [ADR-43: Skill governance and lifecycle](../../../adr/43-skill-governance.md) — the dashboard-only decision and the rejected state machine
- [fleet-health dashboard](fleet-health.md) — how the lanes are *performing*; this dashboard is what they are *permitted*
- [audit-log dashboard](audit-log.md) — what the policy gate actually decided, write by write
- [Profile capabilities](../../../reference/profiles.md) — the lane model the overrides express
