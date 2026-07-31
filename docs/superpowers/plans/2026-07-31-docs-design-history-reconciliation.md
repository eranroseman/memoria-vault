# Docs and Design-History Reconciliation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the published documentation and curated design-history record into line with the shipped alpha.21 repository without rewriting frozen historical evidence.

**Architecture:** Treat published reference/how-to pages, navigation, and curated design history as three independent documentation units. Each unit corrects verified facts at the public boundary while retaining the source code as the authority. Raw archival material remains a preserved source record; only its manifest explains how to recover pruned targets.

**Tech Stack:** Markdown, Jekyll-style documentation front matter, repository verification scripts.

## Global Constraints

- Do not modify runtime code, schemas, tests, or release versioning for this documentation-only change.
- Published pages must use relative Pages routes for published targets and inline-code paths for source files; do not relative-link into `src/`.
- State only shipped behavior. In particular, `memoria init --no-obsidian` still seeds the first-install agent/MCP bundle, while `memoria doctor --repair` never creates or overwrites that PI-owned bundle.
- Preserve the distinction between seeded `CLAUDE.md` and generated `AGENTS.md`.
- Frozen release chapters may receive only verified broken-link corrections. Do not add an alpha.22/alpha.23 history chapter or backfill post-checkpoint work into alpha.21.
- Preserve raw archive links as historical source text; explain recovery through `scratch-final` or Git history instead of rewriting the archive.
- Stage explicit paths only. Before integration, run `env VERIFY_DOCS_ONLY=1 python3 scripts/verify`, `git diff --check`, and the repository `python scripts/verify` gate.

---

### Task 1: Reconcile public behavior and bootstrap reference

**Files:**
- Modify: `docs/reference/system/on-disk-layout.md`
- Modify: `docs/reference/system/configuration.md`
- Modify: `docs/reference/system/installer.md`
- Modify: `docs/reference/commands-and-transports/cli.md`
- Modify: `docs/reference/commands-and-transports/system-actions.md`
- Modify: `docs/reference/commands-and-transports/system-actions-cli-and-pi.md`
- Modify: `docs/reference/evidence-and-integrations/integrations.md`
- Modify: `docs/how-to-guides/setup/set-up-the-vault.md`
- Modify: `docs/how-to-guides/setup/quickstart.md`

**Sources of truth:** `src/memoria_vault/cli.py` (`SEED_TREES`, `SEED_FILES`, `AGENT_BUNDLE_SEED_*`, `SEED_CLASSES`, and repair helpers); `src/memoria_vault/runtime/projections.py` (`AGENTS.md`); `src/memoria_vault/runtime/operations.py` (`MEMORIA_MODEL_TOKEN_CEILING`); `src/memoria_vault/runtime/secrets.py` (`CREDENTIAL_REGISTRY`); and `src/memoria_vault/product/capabilities/operations/resolve-evidence.md`.

- [x] **Step 1: Correct bootstrap ownership and lifecycle.**

  In the on-disk layout, replace the false claim that every packaged seed has a direct runtime reader. Inventory the five root Base files, `.obsidian/graph.json`, `.obsidian/types.json`, `.claude/`, `.codex/hooks.json`, `.mcp.json`, and `CLAUDE.md`. State that the agent/MCP files configure hosts but install no external runtime; `init` seeds them even with `--no-obsidian`; doctor repair neither recreates nor overwrites them. State separately that `AGENTS.md` is generated as a projection, not copied from the package seed. Preserve the view-preference ownership rule: repair restores a missing preference but preserves an existing PI copy.

- [x] **Step 2: Correct configuration and bootstrap guidance.**

  Split configuration ownership so the first-init agent/MCP bundle is PI-owned after bootstrap and does not use the repair lifecycle. Add `MEMORIA_MODEL_TOKEN_CEILING`: it accepts a nonnegative integer, unset or `0` disables it, actual model usage accumulates per process, and a later model call is refused after the ceiling has been reached. Update the CLI, installer, full setup guide, and Quickstart to name the first-init agent/MCP configuration and to say that `--no-obsidian` skips only editor settings and root Base views.

- [x] **Step 3: Correct the public operation and credential catalog.**

  Add `resolve-evidence` to the operation-manifest roster. Change the evidence-review description to the four accepted PI decisions: accept, reject, edit, and defer. Add `PUBMED_API_KEY` as an enhancing credential whose keyless behavior is the NCBI keyless tier when the reserved PubMed adapter lands.

- [x] **Step 4: Verify the published behavior unit.**

  Run `env VERIFY_DOCS_ONLY=1 python3 scripts/verify` and `git diff --check`. Confirm the diff contains no external-runtime installation claim and no claim that doctor repairs the agent/MCP bundle.

- [x] **Step 5: Commit the verified unit.**

  Stage only the nine files above and commit with message `docs: reconcile bootstrap and public references`.

### Task 2: Repair published navigation and link policy

**Files:**
- Modify: `docs/how-to-guides/operate/inspect-session-logs.md`
- Modify: `docs/explanation/surfaces/dashboards/README.md`
- Modify: `docs/how-to-guides/setup/add-a-second-vault.md`
- Modify: `docs/how-to-guides/README.md`
- Modify: `docs/reference/README.md`
- Modify: `docs/README.md`

**Sources of truth:** `docs/README.md` link/indexing rules; the existing child dashboard pages; and the Setup index ordering.

- [x] **Step 1: Repair the invalid source link and dashboard index.**

  Replace the `inspect-session-logs` Markdown link that escapes into `src/` with inline code `src/memoria_vault/runtime/subsystems/integrity/linter/session_summary.py`. Add a compact linked map for `daily-glance.md`, `synthesis-agenda.md`, `structural-health.md`, and `operational-health.md` to the dashboard section index.

- [x] **Step 2: Normalize navigation routes and ordering.**

  Change `add-a-second-vault.md` to `nav_order: 6`, leaving the optional gateway runner at `5`. Convert the eight top-level how-to map links from `{{ site.baseurl }}` URLs to their relative section routes. Link the seven Reference section headings to their child section indexes. Clarify the contributor convention so each new how-to belongs in its section index; the intentionally shallow top-level how-to index lists sections rather than every guide.

- [x] **Step 3: Verify the navigation unit.**

  Run `env VERIFY_DOCS_ONLY=1 python3 scripts/verify` and `git diff --check`. Confirm that `inspect-session-logs.md` contains no Markdown link into `src/`, the dashboard index links all four child pages, and Setup has distinct `nav_order` values.

- [x] **Step 4: Commit the verified unit.**

  Stage only the six files above and commit with message `docs: repair navigation and link policy`.

### Task 3: Reconcile curated design history without changing archival evidence

**Files:**
- Modify: `design-history/00-origins.md`
- Modify: `design-history/01-alpha.1-baseline.md`
- Modify: `design-history/arcs.md`
- Modify: `design-history/README.md`
- Modify: `design-history/archive/MANIFEST.md`

**Sources of truth:** existing `design-history/archive/` paths, the `scratch-final` recovery tag, current alpha.21 chapter, and `.github/workflows/verify.yml` / `pyproject.toml` for the completed runtime CI change.

- [x] **Step 1: Repair curated frozen-record links only.**

  In `00-origins.md`, point the two origin sources to `archive/researcher-notes.md` and `archive/old-skeleton/`. In `01-alpha.1-baseline.md`, point ADR-48 to `archive/notes/docs-exports/adr-full.md#adr-48-one-co-pi-fronts-everything-specialists-consolidate-to-posture-defined-agents`. Make no other historical-content edit.

- [x] **Step 2: Bring the living synthesis and indexes to alpha.21.**

  Remove the stale pending assertion that runtime CI must be widened, retaining the remaining crash/rebuild obligation. Replace deleted `docs/design/` and `docs/adr/` durable-source locations with current `docs/explanation/`, `docs/reference/`, and `archive/notes/docs-exports/adr-full.md`; extend the decision-record lineage through `21-alpha.21.md`. Link the latest completed checkpoint in the design-history README and change its reconstruction statement to say there are no release tags. Extend the archive manifest's compiled-history range through `21-alpha.21.md` and state that raw links retain their historical paths, with pruned targets recoverable from `scratch-final` or Git history.

- [x] **Step 3: Verify the curated-history unit.**

  Run `git diff --check` and inspect the five edited files. Confirm the repaired targets exist, `scratch-final` is named only as a recovery backstop, and no new release chapter has been added.

- [x] **Step 4: Commit the verified unit.**

  Stage only the five files above and commit with message `docs: reconcile curated design history`.

### Task 4: Whole-branch documentation verification and tracking

**Files:**
- Modify: `docs/superpowers/plans/2026-07-31-docs-design-history-reconciliation.md`

- [x] **Step 1: Mark completed task steps in this plan.**

  Replace each completed task checkbox with `- [x]` after its task reviewer approves the task.

- [x] **Step 2: Run the complete merge gate.**

  Run `python scripts/verify`, inspect its full output and exit code, then run `git status --short --branch` and `git diff main...HEAD --check`.

  Final verification after CSpell correction `333e377b`: the full gate exited 0 with 2707 passed, 11 skipped, and 1 warning; the offline e2e smoke was green and the final result was `verify: OK`.

- [x] **Step 3: Record issue tracking.**

  Add a concise completion comment to the existing documentation reconciliation tracker, GitHub issue `#1504`, naming the bootstrap/reference, navigation, and curated-history corrections plus the verification result. Do not close the tracker because it remains the additive documentation workstream.

- [x] **Step 4: Commit plan completion.**

  Stage only this plan file and commit with message `docs: record reconciliation verification`.
