# Retire fully-folded alpha.21-alpha.23 working records

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Retire the 25 `docs/superpowers/{specs,plans}/` working records whose content
now has a durable home in `design-history/21-alpha.21.md` (frozen), `design-history/
22-alpha.22.md` (frozen), `design-history/23-alpha.23.md` (unfrozen but committed), or
shipped code — per the docs-only audit conducted 2026-08-02.

**Architecture:** Docs-only, one atomic task: verify no live cross-reference exists,
delete the 25 files, apply the one required follow-up edit, commit. This mirrors
precedent commits `b15a3302`, `00ea3af8`, `8fcc8b8a`, `9d22ac3e`, all of which retired
fully-folded working records in a single commit once their content had a durable home.

**Tech Stack:** Markdown only. Gate: `python scripts/verify`.

Source: the 2026-08-02 audit (14 parallel mapper agents + adversarial verification per
candidate) that produced this file list. Every citation below (design-history section,
issue number, code path) was independently re-verified during that audit's Verify phase.

## Global Constraints

- **Retirement = deletion** (owner ruling, `docs/superpowers/plans/2026-07-12-docs-migration.md`
  line 20): no archive folder, no banner-keeping. `git rm` the files; git history is the
  archive.
- **Stage explicit paths only** — never `git add -A` (this repo's shared-index rule,
  AGENTS.md).
- **Gate:** `python scripts/verify` must pass before the commit.
- **Do not** touch any of the 23 files the audit marked KEEP (living release ledger,
  genuinely open work, or deferred future scope) — see the audit's §4-§6 for the full
  list and reasoning. In particular do not delete
  `docs/superpowers/specs/2026-07-15-surfaces-bootstrap-design.md` — the audit's own
  verification pass overturned an initial "safe to delete" call on this file (it is
  still load-bearing for two open GitHub issues, #1690 and U3-CANVAS.5's manual check).
- **Do not** delete the 6 files blocked only on the three still-open human-gated items
  (LOOP.13/#1702, U3-PLUG.11/#1690, U3-CANVAS.5): `alpha23-usable-loop.md`,
  `surfaces-bootstrap-and-plugins.md`, `o2-staged-import.md` + its design spec,
  `surfaces-bootstrap-design.md`, `surface-design-notes.md`. Those retire in a future
  pass once those three issues close.
- **PR required:** this repo requires a PR to `main` plus the `verify` and `gitleaks`
  checks (AGENTS.md); do not commit directly to `main`.

## Task 1: Cross-reference check, delete, follow-up edit, commit

**Interfaces:**

- Deletes: the 25 files listed below, and nothing else.
- Edits: `docs/superpowers/specs/2026-07-12-beta.1-consolidation.md` §7 only, to note
  that `docs-migration.md` has retired (mirrors how that section already records the
  disposition of the earlier-retired `2026-07-11-foundations-reconcile*` pair).

**Steps:**

- [x] **Step 1: Cross-reference check.** Run, from the repo root:

  ```bash
  git ls-files -- '*.md' ':!:docs/superpowers/**' ':!:test-vault/**' ':!:node_modules/**' \
    | xargs grep -lE '2026-07-12-foundation-design|2026-07-14-warrant-grounds-rename-manifest|2026-07-14-i1-skeleton-design|2026-07-15-graph-nodes-identity-design|2026-07-15-graph-edges-roles-propagation-design|2026-07-15-graph-substrate|2026-07-16-i1-full-wiring-design|2026-07-16-i1-full-wiring\b|2026-07-16-o1-onboarding-seed|2026-07-16-v2-evidence-review-design|2026-07-16-v2-evidence-review\b|2026-07-17-u1-read-api-design|2026-07-17-u1-read-api\b|2026-07-17-u2-cockpit-design|2026-07-17-u2-cockpit\b|2026-07-17-r2-retrieval-modes-design|2026-07-17-r2-retrieval-modes\b|2026-07-15-u3-obsidian-cards-design|2026-07-15-u4-copi-agent-plugin-design|2026-07-15-coverage-remediation-design|2026-07-15-model-call-cost-telemetry-design|2026-07-15-alpha21-review-repairs|2026-07-15-alpha22-substrate-trust|2026-07-12-docs-migration|2026-07-31-docs-design-history-reconciliation' \
    2>/dev/null
  ```

  Expected: empty output (every hit the audit found was inside `docs/superpowers/`,
  already excluded above, or a self-citation inside frozen `design-history/` chapters,
  which is fine). **If this prints anything, stop and report NEEDS_CONTEXT** — do not
  delete the affected file(s) until the hit is understood; something changed since the
  audit.

- [x] **Step 2: Delete — explicit paths, never a wildcard or `-A`:**

  ```bash
  git rm \
    docs/superpowers/specs/2026-07-12-foundation-design.md \
    docs/superpowers/specs/2026-07-14-warrant-grounds-rename-manifest.md \
    docs/superpowers/specs/2026-07-14-i1-skeleton-design.md \
    docs/superpowers/specs/2026-07-15-graph-nodes-identity-design.md \
    docs/superpowers/specs/2026-07-15-graph-edges-roles-propagation-design.md \
    docs/superpowers/plans/2026-07-15-graph-substrate.md \
    docs/superpowers/specs/2026-07-16-i1-full-wiring-design.md \
    docs/superpowers/plans/2026-07-16-i1-full-wiring.md \
    docs/superpowers/plans/2026-07-16-o1-onboarding-seed.md \
    docs/superpowers/specs/2026-07-16-v2-evidence-review-design.md \
    docs/superpowers/plans/2026-07-16-v2-evidence-review.md \
    docs/superpowers/specs/2026-07-17-u1-read-api-design.md \
    docs/superpowers/plans/2026-07-17-u1-read-api.md \
    docs/superpowers/specs/2026-07-17-u2-cockpit-design.md \
    docs/superpowers/plans/2026-07-17-u2-cockpit.md \
    docs/superpowers/specs/2026-07-17-r2-retrieval-modes-design.md \
    docs/superpowers/plans/2026-07-17-r2-retrieval-modes.md \
    docs/superpowers/specs/2026-07-15-u3-obsidian-cards-design.md \
    docs/superpowers/specs/2026-07-15-u4-copi-agent-plugin-design.md \
    docs/superpowers/specs/2026-07-15-coverage-remediation-design.md \
    docs/superpowers/specs/2026-07-15-model-call-cost-telemetry-design.md \
    docs/superpowers/plans/2026-07-15-alpha21-review-repairs.md \
    docs/superpowers/plans/2026-07-15-alpha22-substrate-trust.md \
    docs/superpowers/plans/2026-07-12-docs-migration.md \
    docs/superpowers/plans/2026-07-31-docs-design-history-reconciliation.md
  ```

  Confirm exactly 25 files are staged as deleted (`git status --short | grep -c '^D'`).

- [x] **Step 3: Follow-up edit.** In
  `docs/superpowers/specs/2026-07-12-beta.1-consolidation.md` §7 "Corpus hygiene +
  source-doc disposition", find the bullet that names `plans/2026-07-12-docs-migration.md`
  as the destination for the retired `2026-07-11-foundations-reconcile*` records' prose,
  and add a note that `docs-migration.md` itself has now retired (its own #1366 closed,
  its outcome narrated in the frozen `design-history/21-alpha.21.md`). Keep the edit
  minimal — one clause or one appended sentence, matching this section's existing style
  for recording a disposition. Stage this file explicitly alongside the deletions.

- [x] **Step 4: Gate.** Run `python scripts/verify` — expected: `verify: OK`. This is a
  docs-only change; if anything fails, it is either the cspell/markdownlint hooks
  reacting to the §7 edit (fix wording) or evidence the cross-reference check in Step 1
  missed something (investigate, do not force past it).

- [x] **Step 5: Commit** (explicit paths, matching the shared-index rule):

  ```bash
  git add docs/superpowers/specs/2026-07-12-foundation-design.md \
    docs/superpowers/specs/2026-07-14-warrant-grounds-rename-manifest.md \
    docs/superpowers/specs/2026-07-14-i1-skeleton-design.md \
    docs/superpowers/specs/2026-07-15-graph-nodes-identity-design.md \
    docs/superpowers/specs/2026-07-15-graph-edges-roles-propagation-design.md \
    docs/superpowers/plans/2026-07-15-graph-substrate.md \
    docs/superpowers/specs/2026-07-16-i1-full-wiring-design.md \
    docs/superpowers/plans/2026-07-16-i1-full-wiring.md \
    docs/superpowers/plans/2026-07-16-o1-onboarding-seed.md \
    docs/superpowers/specs/2026-07-16-v2-evidence-review-design.md \
    docs/superpowers/plans/2026-07-16-v2-evidence-review.md \
    docs/superpowers/specs/2026-07-17-u1-read-api-design.md \
    docs/superpowers/plans/2026-07-17-u1-read-api.md \
    docs/superpowers/specs/2026-07-17-u2-cockpit-design.md \
    docs/superpowers/plans/2026-07-17-u2-cockpit.md \
    docs/superpowers/specs/2026-07-17-r2-retrieval-modes-design.md \
    docs/superpowers/plans/2026-07-17-r2-retrieval-modes.md \
    docs/superpowers/specs/2026-07-15-u3-obsidian-cards-design.md \
    docs/superpowers/specs/2026-07-15-u4-copi-agent-plugin-design.md \
    docs/superpowers/specs/2026-07-15-coverage-remediation-design.md \
    docs/superpowers/specs/2026-07-15-model-call-cost-telemetry-design.md \
    docs/superpowers/plans/2026-07-15-alpha21-review-repairs.md \
    docs/superpowers/plans/2026-07-15-alpha22-substrate-trust.md \
    docs/superpowers/plans/2026-07-12-docs-migration.md \
    docs/superpowers/plans/2026-07-31-docs-design-history-reconciliation.md \
    docs/superpowers/specs/2026-07-12-beta.1-consolidation.md

  git commit -m "$(cat <<'EOF'
  docs: retire 25 fully-folded alpha.21-23 working records

  Foundation (F1-F4), graph substrate (ERP/NID), evidence-grounds contract,
  I1 full-wiring, and the O1/U1/U2/R2/V2/U3/U4 "usable loop" units are all
  implemented on main and narrated in design-history/21-alpha.21.md (frozen),
  22-alpha.22.md (frozen), and 23-alpha.23.md (unfrozen but committed).

  Retirement = deletion per the 2026-07-12 owner ruling; git history is the
  archive. No functionality changes.
  EOF
  )"
  ```

  Do not include a `Closes #NNNN` trailer — every issue associated with these 25 files
  is already closed by a prior commit (verified during the audit).
