---
topic: decisions
id: 43
title: Skill governance and lifecycle
nav_exclude: true
status: accepted
date_proposed: 2026-05-31
date_resolved: 2026-06-12
assumes: [24]
supersedes: []
superseded_by: []
---

# ADR-43: Skill governance and lifecycle

## Context

Adding a skill is a runtime operation: edit `policy.allow.skills` in a lane-override
file and drop the `SKILL.md` into the right profile's `skills/` folder. At low skill
count that is sufficient — the bookkeeping fits in the human's head. This ADR was
deferred until the count stopped fitting; at 0.1.0-alpha.2 the vault shipped **25
skills across five profiles** (threshold: > 15), and the open question became which of
two shapes to stand up:

- **Dashboard-only** — a `skill-state` dashboard giving visibility into which
  skills are active in which lane, with no new process.
- **Full lifecycle** — a state machine (`intake → proposed → scaffolded → testing →
  needs-review → approved → active → archived`), per-skill governance notes in
  `system/skills/`, and a 7-step onboarding checklist for new skills.

The deferral itself named the discriminator: confusion about *what's active* wants the
dashboard; uncontrolled *graduations* want the state machine.

## Decision

**Dashboard-only.** The `skill-state` dashboard ships in
`system/dashboards/skill-state.md`: a Dataview view that reads the runtime
governance layer directly (`.memoria/lane-overrides/*.yaml` and
`.memoria/profiles/*/skills/*/SKILL.md`) and renders, per lane, the allowed and denied
runtime skills, the shipped `SKILL.md` folders, and a consistency-check table that
surfaces any disagreement between lane policy and shipped skills.

**The lifecycle half is not adopted.** No state machine, no per-skill governance notes
in `system/skills/` (the folder is not created — the placeholder is retired), no
onboarding checklist. The signal that fired was skill *count*, and what count breaks is
*visibility*, which the dashboard restores. The lifecycle machinery answers a different
problem — coordinating graduations and approvals — that has not occurred (zero
passthrough-to-dedicated graduations to date) and that the single-researcher scope
([ADR-24](24-single-researcher-scope.md)) makes structurally unlikely: with one human
approver there is no hand-off an `intake → … → approved` pipeline would mediate, and
retroactive governance notes for 25 skills plus a checklist per new skill is pure
process overhead. Should graduation churn actually materialize, this half can be
revisited as a new proposal.

**The runtime mechanism is the system of record.** Lane-override files
(`policy.allow.skills` / `policy.deny.skills`) plus the per-profile `skills/` folders
*are* skill governance; the dashboard renders them at view time and therefore cannot
drift from them. Adding a skill remains a runtime operation, exactly as before.

## Consequences

- "Which skills are active in which lane?" has a one-glance answer that is always
  current — the dashboard reads the live files, not a generated snapshot.
- Mismatches (a skill relying on a runtime gate its lane denies, frontmatter
  contradicting the shipping profile, duplicate `skill_id`s) surface as dashboard rows
  instead of being discovered mid-run.
- Adding a skill stays friction-free: no checklist, no governance note, no state to
  advance. The cost is that skill *history* (why a skill was added or retired) lives
  only in git, which is acceptable at n=1 operator.
- `system/skills/` is never created; the on-disk layout is unchanged.
- The shape of the two file formats the dashboard parses is pinned by tests
  (`tests/test_skill_state_dashboard.py`), so a lane-override or `SKILL.md`
  restructuring fails CI rather than silently blanking the dashboard.

## Alternatives considered

**Full lifecycle (state machine + `system/skills/` notes + onboarding checklist).**
Rejected for now, per above: it solves a coordination problem a single-researcher
system doesn't have, at the cost of retroactive authoring for every existing skill and
standing friction on every new one. Not silently dropped — explicitly not adopted;
re-proposable if graduation churn appears.

**Keep the runtime mechanism alone (do nothing).** The pre-trigger state. Rejected:
at 25 skills the "what's active where?" question genuinely stopped being answerable
from memory, and answering it by opening ten YAML files is exactly the bookkeeping
failure the deferral predicted.

**A generated report instead of a live dashboard.** A cron script writing a markdown
snapshot would add a generator, a cadence, and a staleness window for no benefit — the
source files are small and local, so the view layer can read them directly
([ADR-116](116-obsidian-surface-architecture.md): views are surfaces, never a second
store).

## Related

- **Tracking issue:** [#368](https://github.com/eranroseman/memoria-vault/issues/368) — the trigger firing and the shape decision.
- **System of record:** lane-override files (`policy.allow.skills`) + per-profile `skills/` folders.
- **The dashboard:** `system/dashboards/skill-state.md`; rationale in [skill-state dashboard](../explanation/dashboards/operational-health.md#skill-state).
- **Scope premise:** [ADR-24](24-single-researcher-scope.md) — single researcher; one judgment owner.
