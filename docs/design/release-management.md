---
topic: explorations
title: Release management — review and alternatives
status: analysis
created: 2026-06-08
parent: Design notes
grand_parent: Explanation
nav_order: 21
nav_exclude: true
---

# Release management — review and alternatives

A review of how Memoria manages releases today (`project/release/`) and the
alternatives weighed, with the tiered path chosen. Reviewed **2026-06-08**.

## Current approach — "self-contained plan file"

One folder per version (`project/release/vX.Y/`) holding a single
`release-plan-vX.Y.md` — frontmatter `released:` flag, §2 Gates (`G1–G11` state
table), §3 Validation stages (`S0–S5`), scope, cut procedure, roadmap — plus
sibling run records (gui-test-plan, manual-testing, validation-log,
readiness-review). Scope lives in the **GitHub milestone**; notes in
`CHANGELOG.md`; a `v*` tag triggers `release.yml` → a GitHub Release. The `/release`
skill scaffolds it. Strong "single source of state" discipline (gate/stage state
only in §2/§3; build gaps only in issues; scope cuts only in proposals).

**What works:** git-tracked, reviewable in PRs, self-contained, holds rich prose
(cut procedure, known-limitations) GitHub can't, works offline.

**Where it hurts (observed, not hypothetical):**

- **Hand-maintained markdown state tables drift.** The template itself wishes for
  "a future status-doctor check"; meanwhile the `/release` skill referenced
  `project/releases/` (now `release/`), `decisions/` (now `adr/`), "Tier `T#`" (the
  plan uses Stage `S#`), and "auto-merge after Kilo" (Kilo was removed) — and the
  v0.1 plan linked `../../decisions/27…` (stale).
- **No live status surface** — to know "where is the release," you read a file.
- **8 files per release** + two places to keep aligned (plan gates ↔ milestone/issues).

## Alternatives weighed

| Category | Strongest option | Pros | Cons |
|---|---|---|---|
| **File folders** | `status-doctor` check over today's files | lowest effort; kills drift; stays in git | doesn't add a live surface; state still hand-edited |
| **GitHub-native** | gates as a checklist in a "Release vX.Y" tracking issue (live progress bar); milestone = scope | live status free; retires the hand-tables; no markdown editing | state leaves git (GitHub-only); offline visibility lost |
| **VS Code extensions** | GitHub PR/Issues extension (already installed) | manage milestones/issues in-editor | a viewer, not a system of record |
| **Other tools** | release-please (Conventional Commits → version + CHANGELOG + Release PR); a `scripts/release.sh` cut script; `status-doctor` | automates notes/versioning + the cut | another workflow to own; opinionated |

VS Code extensions are a UI over whichever model you pick, never the model itself.
release-please automates only the *notes/versioning* half, not *readiness*.

## Tiers (additive — stop anywhere, escalate later without rework)

**Tier 1 — Minimal.** Fix the drift + add `status-doctor`.
*Pros:* hours of work; no new deps/lock-in; CI-enforces the single-source invariant the template wanted; preserves the prose; fully reversible.
*Cons:* no live surface; gate state still hand-edited markdown; still 8 files/release; manual cut.

**Tier 2 — Medium.** + gates as a "Release vX.Y" tracking-issue checklist + release-please.
*Pros:* live status free (progress bar + milestone %); retires the §2/§3 hand-tables (the main drift source); automates CHANGELOG/version/tag/Release; gates become trackable.
*Cons:* splits the record (prose in git, state in GitHub); release-please is opinionated and replaces `release.yml`; offline gate-state visibility lost; one-time migration.

**Tier 3 — Maximal.** + a Projects "Release" view with a Gate-status field + `scripts/release.sh` one-command cut.
*Pros:* richest dashboard (gate status in the 6-value vocabulary, grouped by milestone); reproducible one-command cut.
*Cons:* most moving parts; Projects field/view config isn't in git (same gap as the kanban board); highest lock-in; the Projects layer is marginal at solo cadence. (The cut **script** is the higher-value half and can be taken without the Projects field.)

## Decision (2026-06-08)

**Tier 1 now + Tier 2 adopted.** The drift was fixed and the release scaffolding
(template / `README` / `/release` skill) moved to the **gates-as-tracking-issue
checklist** model; **release-please** owns version/CHANGELOG/Release (retiring the
tag-only `release.yml`). The in-flight **v0.1** plan keeps its §2/§3 tables as the
at-cut record (with a pointer to its "Release v0.1" tracking issue); **v0.2+** uses
the checklist model from the start. Tier 3's Projects-field layer is **deferred** —
revisit only if release cadence rises; the cut script can be pulled in standalone if
manual cuts become a chore.
