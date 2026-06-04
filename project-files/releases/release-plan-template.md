---
release: vX.Y.Z
status: draft        # draft | candidate | released
released: false      # machine cut-flag; true ONLY when every gate below is `done`
---

# Release plan — vX.Y.Z

<!-- ===========================================================================
  THIS IS A TEMPLATE. It is a single, self-contained release plan: everything a
  release NEEDS lives here, in one file. Bookkeeping (the gate/tier STATE tables)
  and prose (scope, reasoning, cut steps) sit side by side. Placeholders are
  written as {{ fill me }}.

  ── To start a new release ──────────────────────────────────────────────────
  1. Copy this file to  release-plan-<version>.md  (e.g. release-plan-v0.2.md).
  2. Bump `release:` and set `released: false`.
  3. Reset every Gate (§2) and Tier (§3) State to `todo`.
  4. Rewrite the per-release prose (status line, scope, limitations).
  5. Start a sibling  release-plan-<version>-spillover.md  for anything too
     detailed to belong in a crisp plan (see §9).

  ── The one rule that keeps this from rotting ───────────────────────────────
  SINGLE SOURCE OF STATE. Gate (G#) and Tier (T#) state lives ONLY in the §2/§3
  tables of this file. No sibling doc may restate it — they point here. Likewise,
  build gaps live ONLY in GitHub issues; scope cuts in proposals/.
  Edit each fact in exactly one place. (A future status-doctor check can enforce
  this; see the README.)
============================================================================ -->

<!-- PER-RELEASE STATUS LINE — one short paragraph. What is the state of this
     release in plain words? Replace every release. -->
**Current status: {{ pre-release | release candidate | released }}.** {{ One or
two sentences: is it shipped? what's the single biggest thing standing between
here and cut? }} `released:` in the frontmatter is the machine flag — it flips to
`true` only when every gate in §2 is `done`.

## State values

The vocabulary used by every State cell in §2 and §3. (Kept in-file so each
release plan is self-contained.)

| Value | Meaning |
| --- | --- |
| **done** | Verified green. Ship-ready. |
| **in-progress** | Actively being built/wired right now. |
| **awaiting-verify** | Code/config landed; needs a live re-run to confirm (not a defect). |
| **blocked** | Cannot proceed — gated on an open issue or another row. |
| **todo** | Not yet started. |
| **deferred** | Consciously out of this release's scope. |

## 1. Scope — what this release is

<!-- PROSE. What the release IS (the unit of delivery) and what it explicitly is
     NOT. One paragraph. Out-of-scope detail → §5 + the build ledger's deferred rows. -->

{{ What this version delivers, in one paragraph. Name the boundary: what is in,
what is deliberately later. }}

## 2. Definition of done — gates

<!-- BOOKKEEPING. The release ships when EVERY gate is `done`. State lives HERE
     and nowhere else. Each gate maps to a validation tier (§3), a CI check, or a
     manual step. Keep gates few and verifiable — a gate is a yes/no verdict. -->

vX.Y.Z ships when **all gates (G1–G…) are green.**
_(Proposed gates — confirm/adjust the thresholds for this release.)_

| Gate | State | Proves | Verified by | Issue |
| --- | --- | --- | --- | --- |
| G1 | todo | {{ what passing this gate proves }} | {{ Tier 0–N / CI / manual }} | {{ #NN or — }} |
| G2 | todo | {{ … }} | {{ … }} | {{ … }} |
| G3 | todo | {{ … }} | {{ … }} | {{ … }} |
<!-- add/remove gate rows as the release requires -->

## 3. Validation — tiers

<!-- BOOKKEEPING + procedure. The tiered test plan that turns built artifacts into
     VERIFIED ones. Tier STATE lives HERE only. The table is state; the prose under
     it is the (reusable) procedure. -->

The tiered test plan that turns `shipped` into `approved`. A release candidate
must re-run **all tiers green from a fresh clone** on a clean target box.

| Tier | State | Proves |
| --- | --- | --- |
| T0 | todo | {{ static checks: parse, formatting, presence }} |
| T1 | todo | {{ unit / self-test suites }} |
| T2 | todo | {{ dry-run / substitution }} |
| T3 | todo | {{ real install / integration }} |
| T4 | todo | {{ live: connectivity, enforcement }} |
| T5 | todo | {{ end-to-end / GUI / acceptance }} |
<!-- tiers are cumulative; adjust the set per release -->

## 4. Blockers

<!-- POINTERS, not a third list. A second copy of "what's blocking" drifts from the
     gate table and the issue tracker. State the rule, then point. -->

Not enumerated here — a second list would drift. **By definition the blockers
are** any gate in §2 not yet `done`, plus any open **P0** issue in the project
issue tracker.

## 5. Out of scope (deferred)

<!-- PROSE. What this release consciously leaves out. Per-artifact deferred set lives
     in the build ledger's `deferred` rows — point, don't duplicate. -->

{{ Scope-level exclusions for this release. Point to the ledger / proposals for
the per-artifact deferred set. }}

## 6. Known limitations (state in the release notes)

<!-- PROSE bullets. Carried verbatim into the published release notes at cut. -->

- {{ limitation 1 }}
- {{ limitation 2 }}

## 7. Cut procedure

<!-- NUMBERED steps. The reusable checklist for cutting THIS release. -->

1. **Every gate (§2) and tier (§3) `done`; no P0 issues open.**
2. **Re-run all tiers from a fresh clone** on a clean target → all green; record results in §3.
3. **Confirm the version** is consistent across all version-bearing files.
4. **Cut the `CHANGELOG` section** for this version.
5. **Flip `released: false` → `true`** in this file's frontmatter.
6. **Tag and publish** the release with curated notes (§6 limitations included).
7. **Flip the relevant `shipped` rows to `approved`** in the build ledger once the candidate passes.

## 8. Roadmap after this release

<!-- BRIEF summary only — a few rows. The full phase steps / week-by-week detail go
     in the spillover file (§9), not here. -->

| Phase | When | Goal |
| --- | --- | --- |
| {{ phase }} | {{ when }} | {{ goal in one line }} |

Full phase steps and detail: see the spillover file (§9).

## 9. Spillover — what does NOT belong in this file

<!-- The release plan stays crisp and reusable. Anything that is detailed,
     long-lived, or version-specific lives in a sibling spillover file:
       release-plan-<version>-spillover.md
     Typical spillover: exhaustive per-phase steps & exit criteria, deep
     investigation write-ups, migration notes, raw test logs. The plan SUMMARIZES
     and links; the spillover holds the long tail. Nothing is lost — it just
     doesn't crowd the plan. -->

Detailed phase steps, investigation notes, and migration detail live in
`release-plan-vX.Y.Z-spillover.md`. This plan links to it rather than absorbing it.
