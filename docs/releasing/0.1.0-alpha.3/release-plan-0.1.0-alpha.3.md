---
release: 0.1.0-alpha.3
status: draft
released: false
title: Release plan — 0.1.0-alpha.3
parent: 0.1.0-alpha.3
grand_parent: Releasing
nav_order: 2
---

# Release plan — 0.1.0-alpha.3

**Internal checkpoint (draft).** alpha.3 is the **UI build** — an internal milestone,
**not a formal, published release**: there is no tag, no GitHub Release, and
`released:` stays `false` for every alpha. It makes the PI's direct in-Obsidian loop
correct and frictionless: capture → triage → navigate → dashboards → `home.md`.

## 1. Scope — what this release is

alpha.3 resolves the Obsidian UX issues surfaced while reviewing alpha.2 before project
functionality lands. It fixes the core capture and triage defects, adopts form-based
capture and direct command surfacing, reframes the workspace shells as intent-named
gates, makes dashboards action-first or object-first according to their job, removes
user-facing `.memoria/` leaks, and lands the docs/decision hygiene needed to keep the
UI vocabulary coherent. It is **not** the Project-workspace checkpoint: project
scaffolding, project artifacts, and full Writer / Peer-reviewer / Engineer project
flows move to alpha.4.

## 2. Definition of done — gates

0.1.0-alpha.3 is complete when **every gate sub-issue under the
[Release 0.1.0-alpha.3](https://github.com/eranroseman/memoria-vault/issues/478)
parent issue is closed**. Definitions — state lives in the sub-issues, never a
column here:

| Gate | Proves | Verified by |
| --- | --- | --- |
| G1 | The core tutorial loop works: fleeting capture appears in its Base; URL/Zotero capture creates the expected candidate card; resolve-card and delegate-task actions are usable; Python/runtime errors guide the PI instead of dead-ending | S0-S5 plus tutorial smoke pass |
| G2 | Human capture is structured at entry while the Linter remains authoritative: Modal Forms-backed capture paths, controlled lifecycle values, and per-type property visibility are wired without duplicating schema authority | S0-S3 plus capture walkthrough |
| G3 | Every PI action is reachable directly from Obsidian: QuickAdd/native commands are surfaced through palette/hotkeys and Commander where ribbon/page-header placement is needed; the Co-PI is additive, not the only path | S0-S2 plus command catalog audit |
| G4 | Navigation is an intent-gate model on the existing workspace machinery: three gates now, Project deferred, maintenance ambient, and dashboards organized by job-to-be-done | S0 plus GUI/workspace pass |
| G5 | User-visible files and exports are discoverable without opening `.memoria/`: tutorials, Client Agent export settings, `system/eval`, `system/vocabulary.md`, and catalog Bases point to visible homes | S0-S5 plus docs walkthrough |
| G6 | Alpha.3 docs hygiene is locked: accepted ADRs published, stale D-number references removed, docs-to-source link convention applied, worst Diátaxis splits handled, "Co-PI" terminology normalized, and Operations vocabulary accepted without the structural rename | S0 plus docs-doctor |
| G7 | The alpha.3 checkpoint can be validated from a fresh clone and throwaway vault; required CI is green on `main`; no open High-priority blocker remains | S0-S5 plus CI |

## 3. Validation — stages

The staged test plan that turns built artifacts into verified ones. A candidate re-runs
**all stages green from a fresh clone** on a clean target box (track the runs in the
relevant gate/stage sub-issues).

| Stage | Proves |
| --- | --- |
| S0 | Static: parse, schema-correctness, docs link/title integrity, release-plan/status-doctor invariants |
| S1 | Pytest component suite — policy, hook, board-export, metrics, detectors, capture/write helpers |
| S2 | Agent/action wiring + per-lane policy-gate enforcement; command catalog direct-access audit |
| S3 | Real install into a throwaway vault; bundled plugins/config land; idempotent re-run |
| S4 | Live connectivity + gate enforcement (Obsidian MCP round-trip; a denied write is blocked and audited) |
| S5 | End-to-end + GUI: capture, triage, `home.md`, dashboards, workspaces, Zotero, and graceful no-data states |

## 4. Blockers

Not enumerated here — a second list would drift. **By definition the blockers are** any
open gate/stage sub-issue, plus any open High-priority blocker in Memoria Issue Tracker.

## 5. Out of scope (deferred)

The **Project gate** and project artifacts move to alpha.4: project brief, relevance
scan, knowledge map, gaps, outline, draft, verification, and code-handoff workflows.
Deep Knowledge/ZK management, the Operations code/tree rename, `scripts/*.py`
snake-case renames, folder pluralization, broad test-suite splitting, and the Diátaxis
long tail are deferred to dedicated follow-up passes. The per-artifact deferred set
lives in the deferred-status ADRs in [Decision records](../../adr/README.md).

## 6. Known limitations (state in the release notes)

- No installable release is cut yet — release automation remains paused and the
  release-please manifest stays at `0.0.0` until the first formal cut.
- Project workflows remain deferred to alpha.4; alpha.3 only prepares the UI and
  vocabulary they will use.
- The Operations vocabulary is accepted, but the code tree remains under `engines/`
  until the later dedicated refactor.
- Base Board is a sandbox pilot only; native Bases has no committed kanban view in
  this checkpoint.
- Propsec / Better Properties / Slash Commander remain optional pilots, not baseline
  enforcement or navigation dependencies.

## 7. Reaching the checkpoint

alpha.3 is an **internal checkpoint, not a formal release** — there is no
release-please cut, version tag, or GitHub Release. The checkpoint is reached when:

1. Every gate + stage sub-issue under
   [Release 0.1.0-alpha.3](https://github.com/eranroseman/memoria-vault/issues/478)
   is closed; required CI is green on `main`; no open High-priority blocker remains.
2. All stages re-run green from a fresh clone on a clean target box and throwaway
   vault, never the real `~/Memoria`.
3. The ADRs are retire-swept ([retirement criteria](../../adr/README.md)) as their own
   small PR.
4. `docs/releasing/0.1.0-alpha.3/tmp/` is deleted; tracked scratch is allowed only
   while the checkpoint is being designed.

Record it by setting `status: complete` and noting the date here; `released:` stays
`false` (alphas are never formally released). Close the milestone and release parent
issue, rolling unfinished issues forward to alpha.4. The first **formal** release — a
release-please tag and GitHub Release — is the beta (§8).

## 8. Roadmap after this release

| Phase | When | Goal |
| --- | --- | --- |
| 0.1.0-alpha.4 | next | The **Project workspace** — Writer / Peer-reviewer / Engineer compose, draft, verify, and code workflows over `projects/` |
| 0.1.0 (beta) | later | First **formally released** version — release-please tag + GitHub Release; release automation un-paused |

## 9. Appendix

No appendix yet. Long-form per-phase steps or investigation notes, if they become
needed, live in a sibling `release-plan-0.1.0-alpha.3-appendix.md` that this plan links
to rather than absorbing.
