---
release: vX.Y.Z
status: draft        # draft | candidate | released
released: false      # machine cut-flag; true ONLY when every gate below is `done`
---

# Release plan — vX.Y.Z

<!-- ===========================================================================
  THIS IS A TEMPLATE. It is a single, self-contained release plan: everything a
  release NEEDS lives here, in one file. Bookkeeping (the gate/stage STATE tables)
  and prose (scope, reasoning, cut steps) sit side by side. Placeholders are
  written as {{ fill me }}.

  ── To start a new release ──────────────────────────────────────────────────
  1. Copy this file to  release-plan-<version>.md  (e.g. release-plan-v0.2.md).
  2. Bump `release:` and set `released: false`.
  3. Reset every Gate (§2) and Stage (§3) State to `todo`.
  4. Rewrite the per-release prose (status line, scope, limitations).
  5. Start a sibling  release-plan-<version>-appendix.md  for anything too
     detailed to belong in a crisp plan (see §9).

  ── The one rule that keeps this from rotting ───────────────────────────────
  SINGLE SOURCE OF STATE. This file holds PROSE, not state. Gate (G#) and Stage
  (S#) STATE lives ONLY as the checklist in the "Release vX.Y" tracking issue (a
  GitHub progress bar); §2/§3 here list the gate/stage DEFINITIONS, not their
  state. Scope = the milestone; build gaps = GitHub issues; scope cuts = deferred-status ADRs in docs/adr/;
  version + notes = release-please. Edit each fact in exactly one place.
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
     NOT. One paragraph. Out-of-scope detail → §5 + deferred-status ADRs in docs/adr/. -->

{{ What this version delivers, in one paragraph. Name the boundary: what is in,
what is deliberately later. }}

## 2. Definition of done — gates

<!-- DEFINITIONS, not state. The release ships when every gate is ticked in the
     "Release vX.Y" tracking issue. List each gate's name + what it PROVES here;
     its state is the checkbox in the issue, never a column in this file. Keep
     gates few and verifiable — a gate is a yes/no verdict. -->

vX.Y.Z ships when **every gate box in the [Release vX.Y tracking issue]({{ #NN }})
is ticked.** Definitions (confirm/adjust the thresholds for this release):

| Gate | Proves | Verified by | Issue |
| --- | --- | --- | --- |
| G1 | {{ what passing this gate proves }} | {{ Sx / CI / manual }} | {{ #NN or — }} |
| G2 | {{ … }} | {{ … }} | {{ … }} |
| G3 | {{ … }} | {{ … }} | {{ … }} |
<!-- add/remove gate rows as the release requires -->

## 3. Validation — stages

<!-- DEFINITIONS + procedure. The staged test plan that turns built artifacts into
     VERIFIED ones. List each stage + what it proves; the prose under it is the
     (reusable) procedure. Stage STATE is a checkbox in the tracking issue. -->

The staged test plan that turns `shipped` into `approved`. A release candidate
must re-run **all stages green from a fresh clone** on a clean target box (track
the runs as boxes in the [Release vX.Y tracking issue]({{ #NN }})).

| Stage | Proves |
| --- | --- |
| S0 | {{ static checks: parse, formatting, presence }} |
| S1 | {{ unit / self-test suites }} |
| S2 | {{ dry-run / substitution }} |
| S3 | {{ real install / integration }} |
| S4 | {{ live: connectivity, enforcement }} |
| S5 | {{ end-to-end / GUI / acceptance }} |
<!-- stages are cumulative; adjust the set per release -->

## 4. Blockers

<!-- POINTERS, not a third list. A second copy of "what's blocking" drifts from the
     gate table and the issue tracker. State the rule, then point. -->

Not enumerated here — a second list would drift. **By definition the blockers
are** any gate in §2 not yet `done`, plus any open **P0** issue in the project
issue tracker.

## 5. Out of scope (deferred)

<!-- PROSE. What this release consciously leaves out. Per-artifact deferred set lives
     in docs/adr/ (deferred) — point, don't duplicate. -->

{{ Scope-level exclusions for this release. Point to the deferred-status ADRs for the
per-artifact deferred set. }}

## 6. Known limitations (state in the release notes)

<!-- PROSE bullets. Carried verbatim into the published release notes at cut. -->

- {{ limitation 1 }}
- {{ limitation 2 }}

## 7. Cut procedure

<!-- NUMBERED steps. The reusable checklist for cutting THIS release. -->

1. **Every gate + stage box ticked** in the "Release vX.Y" tracking issue; required CI green on `main`; no open **P0**.
2. **Re-run all stages from a fresh clone** on a clean target → all green; tick the stage boxes.
3. **Merge the release-please "Release vX.Y" PR** — it bumps `CHANGELOG.md`, tags `vX.Y`, and publishes the GitHub Release (fold the §6 known-limitations into the notes). This replaces manual version-bump + tagging.
4. **Flip `released: false` → `true`** in this file's frontmatter and set `status: released`.
5. **Close the milestone and the tracking issue**, rolling any unfinished issues to the next release.

## 8. Roadmap after this release

<!-- BRIEF summary only — a few rows. The full phase steps / week-by-week detail go
     in the appendix file (§9), not here. -->

| Phase | When | Goal |
| --- | --- | --- |
| {{ phase }} | {{ when }} | {{ goal in one line }} |

Full phase steps and detail: see the appendix file (§9).

## 9. Appendix — what does NOT belong in this file

<!-- The release plan stays crisp and reusable. Anything that is detailed,
     long-lived, or version-specific lives in a sibling appendix file:
       release-plan-<version>-appendix.md
     Typical appendix: exhaustive per-phase steps & exit criteria, deep
     investigation write-ups, migration notes, raw test logs. The plan SUMMARIZES
     and links; the appendix holds the long tail. Nothing is lost — it just
     doesn't crowd the plan. -->

Detailed phase steps, investigation notes, and migration detail live in
`release-plan-vX.Y.Z-appendix.md`. This plan links to it rather than absorbing it.
