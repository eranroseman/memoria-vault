---
release: vX.Y.Z
status: draft        # draft | candidate | complete | released
released: false      # machine cut-flag; true ONLY for a formal tagged release
title: Release plan — vX.Y.Z
parent: Releasing
nav_order: 2
---

# Release plan — vX.Y.Z

<!-- ===========================================================================
  THIS IS A TEMPLATE. It is a single, self-contained release-plan prose file:
  scope, reasoning, gate/stage definitions, limitations, and cut/checkpoint
  procedure. Placeholders are written as {{ fill me }}.

  ── To start a new release ──────────────────────────────────────────────────
  1. Copy this file to  docs/releasing/<version>/release-plan-<version>.md.
  2. Bump `release:`, set `status: draft`, and set `released: false`.
  3. Create the "Release vX.Y" parent issue with one sub-issue per gate/stage.
  4. Rewrite the per-release prose (status line, scope, limitations).
  5. Start a sibling  release-plan-<version>-appendix.md  for anything too
     detailed to belong in a crisp plan (see §12).

  ── The one rule that keeps this from rotting ───────────────────────────────
  SINGLE SOURCE OF STATE. This file holds PROSE, not state. Gate (G#) and Stage
  (S#) STATE lives ONLY in the "Release vX.Y" parent issue and its sub-issues; §2/§3
  here list the gate/stage DEFINITIONS, not their state. Scope = the milestone +
  Memoria Issue Tracker view; build gaps = GitHub issues; automated evidence =
  Actions runs/artifacts; scope cuts = deferred-status ADRs in docs/adr/; version
  + notes = release-please. Edit each fact in exactly one place.
============================================================================ -->

<!-- PER-RELEASE STATUS LINE — one short paragraph. What is the state of this
     release in plain words? Replace every release. -->
**Current status: {{ pre-release | release candidate | released }}.** {{ One or
two sentences: is it shipped? what's the single biggest thing standing between
here and cut? }} `released:` in the frontmatter is the formal-release machine flag:
it flips to `true` only for a tagged GitHub Release. Internal checkpoints use
`status: complete`, `released: false` when their release parent issue is closed.

## 1. Scope — what this release is

<!-- PROSE. What the release IS (the unit of delivery) and what it explicitly is
     NOT. One paragraph. Out-of-scope detail → §5 + deferred-status ADRs in docs/adr/. -->

{{ What this version delivers, in one paragraph. Name the boundary: what is in,
what is deliberately later. }}

## 2. Definition of done — gates

<!-- DEFINITIONS, not state. The release ships when every gate sub-issue under the
     "Release vX.Y" parent issue is closed. List each gate's name + what it PROVES
     here; its state is the sub-issue, never a column in this file. Keep gates few
     and verifiable — a gate is a yes/no verdict. -->

vX.Y.Z ships when **every gate sub-issue under [Release vX.Y]({{ #NN }}) is closed.**
Definitions (confirm/adjust the thresholds for this release):

| Gate | Proves | Verified by | Issue |
| --- | --- | --- | --- |
| G1 | {{ what passing this gate proves }} | {{ Sx / CI / manual }} | {{ #NN or — }} |
| G2 | {{ … }} | {{ … }} | {{ … }} |
| G3 | {{ … }} | {{ … }} | {{ … }} |
<!-- add/remove gate rows as the release requires -->

## 3. Validation — stages

<!-- DEFINITIONS + procedure. The staged test plan that turns built artifacts into
     VERIFIED ones. List each stage + what it proves; the prose under it is the
     (reusable) procedure. Stage STATE is a sub-issue under the release parent issue. -->

The staged test plan that turns `shipped` into `approved`. A release candidate
must re-run **all stages green from a fresh clone** on a clean target box (track
the runs in the relevant sub-issues under [Release vX.Y]({{ #NN }})).

| Stage | Proves |
| --- | --- |
| S0 | {{ static checks: parse, formatting, presence }} |
| S1 | {{ pytest component suite }} |
| S2 | {{ dry-run / substitution }} |
| S3 | {{ real install / integration }} |
| S4 | {{ live: connectivity, enforcement }} |
| S5 | {{ end-to-end / GUI / acceptance }} |
<!-- stages are cumulative; adjust the set per release -->

## 4. Blockers

<!-- POINTERS, not a third list. A second copy of "what's blocking" drifts from the
     gate table and the issue tracker. State the rule, then point. -->

Not enumerated here — a second list would drift. **By definition the blockers
are** any open gate/stage sub-issue, plus any open High-priority blocker in
[Memoria Issue Tracker](https://github.com/users/eranroseman/projects/1).

## 5. Out of scope (deferred)

<!-- PROSE. What this release consciously leaves out. Per-artifact deferred set lives
     in docs/adr/ (deferred) — point, don't duplicate. -->

{{ Scope-level exclusions for this release. Point to the deferred-status ADRs for the
per-artifact deferred set. }}

## 6. Known limitations (state in the release notes)

<!-- PROSE bullets. Carried verbatim into the published release notes at cut.
     Keep each limitation user-facing and actionable; the issue/ADR remains the
     durable state/decision record. -->

- Limitation: {{ user-visible limitation }}. Impact: {{ practical impact }}. Workaround: {{ workaround or "none" }}. Tracking: {{ issue/ADR }}.
- Limitation: {{ user-visible limitation }}. Impact: {{ practical impact }}. Workaround: {{ workaround or "none" }}. Tracking: {{ issue/ADR }}.

## 7. Documentation integrity

<!-- Fresh analysis, not copied-forward assumptions. This section defines the
     release's documentation quality bar; detailed findings live in issues,
     ADRs, docs edits, or the appendix when they are worth preserving. -->

Before the release candidate is approved, complete a fresh documentation sweep:

1. **Coverage:** every shipped feature, operation, profile behavior, installer path, and runtime expectation has current coverage in `docs/how-to-guides/` or `docs/reference/`, with explanatory context in `docs/explanation/` when the "why" matters.
2. **Single source of truth:** scan the repository docs for implementation-documentation gaps, duplicate/competing authorities, contradictions, and subtle cross-document drift. Fix defects rather than recording known-bad prose as limitations.
3. **Diataxis placement and indexing:** review `docs/explanation/`, `docs/how-to-guides/`, `docs/tutorials/`, `docs/reference/`, and their README/index pages for quadrant fit, titles, links, `nav_order`, guide-map coverage, and section README shape.
4. **Related links:** review "Related" sections for missing, stale, weak, or incorrectly ordered links. Keep only strong semantic or explicit workflow links; remove weak proximity links.
5. **Terminology and glossary drift:** scan for overloaded terms, renamed concepts, inconsistent stage/status/profile names, and undefined terms that need `docs/reference/vocabulary.md` or another central reference entry.
6. **Third-party and example freshness:** verify claims, commands, config keys, snippets, and examples that mention Hermes, Obsidian, Zotero, bundled plugins, skills, package managers, or external CLIs against the current implementation or upstream docs when relevant.
7. **ADR capture:** any durable decision, scope cut, or design rationale discovered during the release is captured in `docs/adr/` or folded into an existing ADR; release `tmp/` files are not the only record of a decision.

Record the sweep's output in the relevant gate/stage issue or appendix when it
should remain durable. Findings are grouped **Critical / Major / Minor**, and each
finding cites `file:line`, issue type, reasoning, and the recommended edit. Include
the checker summary (`docs_doctor`, docs links, `status_doctor`, cspell, and any
manual/subagent scan coverage) so the evidence is reproducible.

## 8. Runtime readiness

<!-- Target-environment checks. Adjust per release, but keep this section concrete
     enough that "works in CI" cannot hide a broken installed runtime. -->

Record runtime evidence for each target environment this release claims to support:

1. **Fresh clone:** all validation stages pass from a clean checkout, not only the working branch.
2. **Installer target:** a real install or upgrade path succeeds against a disposable vault, never the user's production vault.
3. **WSL/Linux host:** package updates needed for the release are applied or explicitly deferred; command resolution uses the intended binaries.
4. **Hermes profiles:** installed profile configs match the shipped templates, secrets stay in `.env`, and no placeholder values remain.
5. **Local services:** required local endpoints are reachable, including the local LLM endpoint for test-mode releases and the Obsidian Local REST API/native MCP bridge when the release depends on them.
6. **GUI acceptance:** any Obsidian, Bases, workspace, portal, or plugin behavior changed by the release is opened and checked in the runtime vault or a disposable vault.

Evidence should include the command or manual check, date, target machine/environment,
pass/fail summary, and a link to the issue comment, Actions artifact, or
`validation-log.md` entry when the evidence should remain durable.

## 9. Release close-out sweep

<!-- Disposition before cut/checkpoint close. This keeps tracked scratch from
     becoming either hidden state or deleted institutional memory. -->

Before cutting a formal release or closing an internal checkpoint:

1. **Review every tracked `docs/releasing/*/tmp/` file.** If the work was implemented, move the durable content into ADRs, system documentation, reference docs, how-to docs, explanation docs, or release notes as appropriate.
2. **Move unfinished release scratch forward.** If a `tmp/` file still describes unimplemented or deferred work, move it to the next release folder's `tmp/` and update any links.
3. **Delete completed-release `tmp/` folders only after disposition.** Do not delete `tmp/` as cleanup until each file has either been captured durably or moved forward.
4. **Retire-sweep ADRs.** Delete any ADR whose question this release dissolved or whose decision it superseded, keeping the Alternatives-considered memory in the surviving ADR when needed; leave the number gap.
5. **Clean release bookkeeping.** Close or roll forward issues, close the milestone, close the release parent issue, and make sure no release state remains only in a local note.
6. **Git hygiene:** ensure the work is committed, merged through PR, remote branch deleted, local task worktree removed, and the dedicated main checkout fast-forwarded with a clean status.

## 10. Cut procedure

<!-- NUMBERED steps. The reusable checklist for cutting THIS release. -->

1. **Every gate + stage sub-issue closed** under "Release vX.Y"; required CI green on `main`; no open High-priority blocker.
2. **Re-run all stages from a fresh clone** on a clean target → all green; record evidence in the relevant sub-issues or Actions artifacts.
3. **Complete §7 documentation integrity, §8 runtime readiness, and §9 close-out sweep.**
4. **Formal release path:** merge the release-please "Release vX.Y" PR — it bumps `CHANGELOG.md`, tags `vX.Y`, and publishes the GitHub Release. Fold the §6 known limitations into the notes. Then set this file's frontmatter to `status: released`, `released: true`.
5. **Internal checkpoint path:** do not cut a tag or GitHub Release. Set this file's frontmatter to `status: complete`, `released: false` after the release parent issue is closed.
6. **Close the milestone and the release parent issue**, rolling any unfinished issues to the next release.

## 11. Roadmap after this release

<!-- BRIEF summary only — a few rows. The full phase steps / week-by-week detail go
     in the appendix file (§12), not here. -->

| Phase | When | Goal |
| --- | --- | --- |
| {{ phase }} | {{ when }} | {{ goal in one line }} |

Full phase steps and detail: see the appendix file (§12).

## 12. Appendix — what does NOT belong in this file

<!-- The release plan stays crisp and reusable. Anything that is detailed,
     long-lived, or version-specific lives in a sibling appendix file:
       release-plan-<version>-appendix.md
     Typical appendix: exhaustive per-phase steps & exit criteria, deep
     investigation write-ups, migration notes, raw test logs. The plan SUMMARIZES
     and links; the appendix holds the long tail. Nothing is lost — it just
     doesn't crowd the plan. -->

Detailed phase steps, investigation notes, and migration detail live in
`release-plan-vX.Y.Z-appendix.md`. This plan links to it rather than absorbing it.
