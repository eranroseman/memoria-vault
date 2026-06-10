---
name: release
description: Scaffold and track a new Memoria release (vX.Y) — create the release folder + plan, the GitHub milestone (scope), and the "Release vX.Y" tracking issue (gate checklist). Use when starting a new version or cutting an existing one.
---

# release

Stand up or cut a Memoria release. Conventions: AGENTS.md "Work routing"; scaffold:
[docs/releasing/README.md](../../../docs/releasing/README.md).

## Where state lives (single source)

- **Scope** → the GitHub **milestone** `vX.Y` (assigned issues).
- **Readiness** (gate `G#` + validation-stage `S#` state) → the **"Release vX.Y"
  tracking issue** — a gate checklist GitHub renders as a progress bar. *Not* a
  markdown state table.
- **Prose** (scope summary, limitations, cut steps) → `release/vX.Y/release-plan-vX.Y.md`.
- **Build gaps** → GitHub issues. **Version + notes** → release-please.

## Starting a new release vX.Y

1. **Folder + plan.** Create `docs/releasing/v<N>.<M>/README.md` (thin index). Copy
   `docs/releasing/release-plan-template.md` → `docs/releasing/v<N>.<M>/release-plan-v<N>.<M>.md`.
   Fill the prose; frontmatter `status: draft`, `released: false`. The plan lists the
   gate/stage *definitions* — no state table.
2. **Milestone = scope.** `gh api repos/eranroseman/memoria-vault/milestones -f title=vX.Y`;
   assign the scoping issues.
3. **Tracking issue = readiness.** Open a **"Release vX.Y"** issue (label `release`,
   milestone `vX.Y`) whose body is the gate checklist (`- [ ]` per `G#`/`S#`). Tick
   boxes as gates go green.
4. **Overflow** (optional) → `release-plan-vX.Y-appendix.md`.

## Cutting a release

1. Every box in the tracking issue ticked; required CI green on `main`; no open **P0**.
2. **Retire-sweep the ADRs** — delete any whose question this release dissolved or whose decision it superseded; keep *Alternatives considered*, leave the number gap, regen the index. Criteria: `docs/adr/README.md` "When to retire an ADR". (Its own small PR before the cut.)
3. Merge the **release-please** "Release vX.Y" PR — it bumps `CHANGELOG.md`, tags
   `vX.Y`, and publishes the GitHub Release (fold in the plan's known-limitations).
4. Set the plan frontmatter `status: released`, `released: true`.
5. Close the milestone + tracking issue; roll unfinished issues forward.

## PR flow reminder

Changes land via the PR flow (branch → PR → squash; `main` is a protected ruleset).
Release-plan/`README` edits under `docs/releasing/` are safe-path → auto-approve;
anything touching `vault/`, `scripts/`, `.github/`, or `docs/adr/`
is `needs_human`. See AGENTS.md "PR flow" / "Required CI checks".
