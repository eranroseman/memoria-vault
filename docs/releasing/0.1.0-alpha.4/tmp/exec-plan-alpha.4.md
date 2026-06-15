# ExecPlan — finish v0.1.0-alpha.4

This is an ExecPlan: a single, self-contained, living document that carries the
remaining v0.1.0-alpha.4 work from its current state to a validated, observable
result. It follows `.agents/templates/exec-plan.md`; see
`.agents/playbooks/exec-plan.md` for how to run and maintain it. This instance is
tracked release scratch — it lives only here, under the alpha.4 `tmp/`, and is
deleted before the alpha.4 checkpoint closes.

## 0. Metadata

- **Task:** complete the v0.1.0-alpha.4 internal checkpoint — close the active
  build/defect/PI-surface issues, land the actionable packaging slice, and park
  the deferred items honestly.
- **Worktree / branch:** `~/mv-alpha4` · `docs/alpha4-execplan` (off `origin/main`)
- **Milestone:** `0.1.0-alpha.4` (#3) — 25 open, 0 closed at authoring.
- **Related ADRs:** ADR-30 (ingest), ADR-31 (native Obsidian MCP), ADR-54 (batch
  worklists), ADR-55 (golden copy / upgrade), ADR-57 (engines write, agents
  judge), ADR-69 (operations naming), ADR-76 (deferred — runtime as wheel).
- **Design inputs:** [the packaging design note](install-a-real-package.md)
  (ADR-76 / #494 / #521).
- **Started:** 2026-06-15 · **Last updated:** 2026-06-15

## 1. Purpose / big picture

v0.1.0-alpha.4 is an **internal checkpoint** (an alpha checkpoint is a private
milestone, not a tagged public GitHub Release). Finishing it means the milestone
#3 issue set is either **shipped and verifiable from the Obsidian UI** or
**consciously deferred to a cadence-reviewed ADR** — with nothing left in the
ambiguous middle. The observable end state: a fresh install of the alpha.4 vault
lets a researcher capture a real paper, see it enriched and filed, and reach the
shipped assist/linter surfaces directly from Obsidian; everything not delivered
has an open issue or a `status: deferred` ADR explaining why.

## 2. Context and orientation

For a reader new to this repo:

- **Vault / runtime split.** The Python runtime lives in `src/.memoria/` and is
  rsynced into a vault's `.memoria/` by `scripts/install.sh`. Vault data lives in
  the Obsidian vault (`~/Memoria` runtime; `~/Memoria-test` sandbox — never test
  against the real vault).
- **PI** ("Principal Investigator") is this project's internal name for the human
  owner. The **PI direct-access rule:** every feature must be reachable from the
  Obsidian UI directly, not only via CLI.
- **Lanes / engines / gate.** Work runs through MCP servers; the policy-gate
  plugin hard-denies disallowed tool calls (the MCP-only agent sandbox). Agents
  cannot write files — they act only through MCP.
- **ADR-only decision model.** Every decision is an ADR in `docs/adr/` at some
  status; there is no proposals or design-notes folder. **Heads-up for this
  plan:** several issues below still cite retired `docs/design/*.md` paths
  (e.g. `memoria-design-update.md`, `dashboards-design.md`,
  `design-system-and-visual-discipline.md`). Those design docs are retired — the
  source of truth is now the relevant ADR or current `docs/` page. Treat the
  `docs/design/` references as stale pointers to fix, not as live specs.
- **Release housekeeping done in this change.** Two alpha.4 `tmp/` notes that are
  *not* alpha.4 work were moved forward to `docs/releasing/0.1.0-alpha.5/tmp/`
  (`project-starter.md`, `test-env.md`). The packaging note
  (`install-a-real-package.md`) stays here and is folded into Workstream E below.

### 2.1 Scope — the 25 open alpha.4 issues, grouped

**A. Ingest / extraction engine (ADR-30)**

| # | Title | One-line scope |
|---|---|---|
| #438 | Unpaywall OA lookup FIRST in extraction | add an Unpaywall tier ahead of PMC + local PDF; OA PDF goes through the same detect path |
| #437 | PubMed/NCBI as a 4th metadata source | add `fetch_pubmed` to resolve/merge cross-check (MeSH, PMID/PMCID, pub types) |

**B. Security / transport**

| # | Title | One-line scope |
|---|---|---|
| #527 | HTTPS for Obsidian Local REST API + native MCP | close ADR-31's residual: bearer key currently travels over loopback HTTP; revisit once Hermes supports CA/insecure TLS |

**C. Defects / quality / contradictions**

| # | Title | One-line scope |
|---|---|---|
| #443 | Explanation pages describe unbuilt/retired behavior | five published pages violate zero-contradiction; re-scope to deferred or fix |
| #493 | Refactor tests off dynamic `globals()` imports | explicit module aliases; clears ~hundreds of `F821`; overlaps Workstream E step 1 |
| #472 | Code/test naming cleanup | script kebab→snake + retire `load_script()`; folder pluralization; rides ADR-69 |

**D. Obsidian PI surface + v0.1.2 project workspace (PI direct-access)**

| # | Title | One-line scope · note |
|---|---|---|
| #380 | Assist surface (Find/Search/Patterns/Ask/Draft/Explore) | in-Obsidian invocation (palette/pane/selection) → proposals · cites retired design doc |
| #375 | Status-bar ambient indicator | one indicator: Linter verdict + queue depths · cites retired design doc |
| #378 | Design-system enforcement | Linter anti-pattern checks + lifecycle link coloring · cites retired design doc |
| #376 | Callout producers `[!suggestions]` / `[!verification]` | deterministic top-K + LLM line (ADR-57 split) |
| #377 | verify-on-commit trigger | draft commit → verify-lane card |
| #343 | Graded-loudness routing | alert→push, block→hold until ack, quiet/notice pull-only · cites retired design doc |
| #145 | Property reorder / group / color-code | lifecycle stage is buried in frontmatter; define display order + coloring |
| #183 | Obsidian forms for structured capture | modal-form plugin → valid frontmatter into staging |
| #154 | Automate start-a-writing-project | form → script scaffolds `40-workbench/<project>/` + Mapper scope card |
| #336 | Batch worklists (Bases) | ADR-54 worklist surface; per-row lifecycle `decision`; one aggregate prompt |
| #381 | Remaining map skills | score-writability/readiness, graph-claims, canvas-hub · **blocked by #379** (calibration spec, unmilestoned) |
| #329 | Obsidian project-management research | survey PM plugins/methods → adopt/borrow/reject; feeds v0.1.2 |

**E. Runtime packaging (the `install-a-real-package.md` workstream)**

| # | Title | One-line scope |
|---|---|---|
| #521 | Deferred ADR-76: runtime as installable wheel | **deferred target** — cadence review, not an alpha.4 gate |
| #493 | (see C) tests off globals | the test side of step 1 below |

Folded-in design note → see §3 Workstream E and §10. Actionable now: the
**tooling-only `pyproject.toml`** step (pytest + ruff config, delete the
`conftest.py` `sys.path` block) — issue work, no ADR. The full wheel/deployment
flip stays deferred (ADR-76) pending the §4.5 policy-gate version-skew decision,
the ADR-69 `engines → operations` rename landing first, and a real distribution
need.

**F. Upgrade path**

| # | Title | One-line scope |
|---|---|---|
| #339 | Golden-copy update path on release upgrade | ADR-55 open question: three-way reconcile (golden-old/new/live) without clobbering PI edits |

**G. Deferred-ADR cadence tracking — listed for completeness, NOT alpha.4 deliverables**

| # | Tracks | Disposition |
|---|---|---|
| #414 | ADR-64 native Windows support | deferred; revisit each cadence |
| #412 | ADR-62 measurement/verification harnesses | deferred; revisit each cadence |
| #370 | ADR-38 pre-file similarity ratchet | deferred; revisit each cadence |
| #439 | ADR-19 Tier 2 Mapper handoff | deferred; decide build vs supersede at cadence |
| #296 | Migrate Windows WSL2 → native | v0.3 direction; v0.2 unaffected |

## 3. Plan of work

The work is sequenced so the load-bearing engine + security + integrity changes
land before the broad UI surface, and the deferred items are dispositioned (not
built):

1. **Workstream A/B/F first (engine, security, integrity).** These have the
   narrowest blast radius and the clearest acceptance: extraction/merge changes
   (#438, #437) are unit-testable against fixture papers; #527 is a transport
   swap behind ADR-31; #339 is an installer/upgrade-path change behind ADR-55.
2. **Workstream C (defects) in parallel.** #443 is a zero-contradiction fix that
   should not wait — either build the behavior or re-scope the page to deferred.
   #493 and #472 are quality refactors that also unblock Workstream E step 1.
3. **Workstream E step 1 (tooling pyproject)** rides #493: once tests stop using
   `globals()` injection, the `conftest.py` `sys.path` block moves into a
   tooling-only `pyproject.toml`. The wheel migration itself stays deferred.
4. **Workstream D (PI surface) last and incrementally.** Each verb/indicator is
   independently shippable and must satisfy the PI direct-access rule. Before
   building any D item, fix its retired `docs/design/` reference to the current
   ADR/doc (zero-contradiction). #381 is blocked by #379 (calibration spec) —
   either pull #379 in or leave #381 open.
5. **Workstream G — disposition, don't build.** Confirm each tracking issue's ADR
   is `status: deferred` with a current *When this matters*; record the cadence
   verdict in the Execution log. Any decision to build one is a new ADR, not a
   line in this plan.

## 4. Concrete steps

1. **Isolate the session** (`AGENTS.md` §1) — done for this plan:

   ```bash
   git fetch origin
   git worktree add ~/mv-alpha4 -b docs/alpha4-execplan origin/main
   cd ~/mv-alpha4
   ```

2. **Pick the next issue from §2.1 in the §3 order.** Open its own worktree +
   branch per item (one scope → one branch → one PR). Read the issue body and the
   ADR/source it names; if it cites a retired `docs/design/*` path, resolve to
   the current ADR/doc first.

3. **Implement against the source of truth**, then verify per §5 with focused
   tests (`scripts/test.sh`) and an Obsidian-UI check where the PI direct-access
   rule applies.

4. **Update this plan** (§7 Progress, §8 Execution log, §9 Surprises) at every
   stopping point, then open the PR.

   ```text
   (expected: each closed issue maps to a merged PR; each deferred issue maps to
    a status: deferred ADR with a current "When this matters")
   ```

## 5. Validation and acceptance

Per `.agents/playbooks/verify-change.md` — observable claims, lowest-cost
evidence, real transcripts:

- **#438:** Given a capture with no PMCID and a scanned local PDF, when extraction
  runs, then Unpaywall is queried **first** and an OA PDF (if found) is used
  ahead of PMC/local. *Prove with:* a focused extract test on a known-OA DOI.
- **#437:** Given a paper resolvable only via PMID, when resolve/merge runs, then
  `fetch_pubmed` contributes MeSH/PMID/PMCID to the cross-checked record. *Prove
  with:* a resolve_merge unit test.
- **#527:** Given the native Obsidian MCP, when a lane writes, then the bearer
  key travels over TLS (or the residual is re-documented if Hermes still lacks
  CA/insecure support). *Prove with:* a connection test against `~/Memoria-test`.
- **#339:** Given a vault with PI edits, when a release upgrade runs, then changed
  system files refresh and PI customizations survive (three-way reconcile).
  *Prove with:* a disposable-vault upgrade test — never `~/Memoria`.
- **Workstream D items:** Given the feature, when invoked **from the Obsidian
  UI**, then the result lands as a proposal in staging. *Prove with:* an attended
  Obsidian check (note residual risk if runtime-only).
- **Workstream E step 1:** Given the tooling `pyproject.toml`, when tests run
  without the `conftest.py` `sys.path` block, then `python -m pytest` and
  `ruff check .` stay green. *Prove with:* `scripts/test.sh all`.
- **Workstream G:** Given each tracking issue, when reviewed, then its ADR is
  `status: deferred` with a current *When this matters*. *Prove with:* the ADR
  file + a one-line cadence verdict in §8.

## 6. Idempotence and recovery

- **Safe to re-run:** each issue is its own branch/PR; re-running an unstarted
  issue is a no-op. This plan is regenerable from the milestone #3 issue list.
- **Rollback:** `git worktree remove` a per-issue worktree; revert the PR commit.
  The file moves in this PR are pure renames — revert restores them to alpha.4.

## 7. Progress

- [ ] 2026-06-15 — ExecPlan authored; `project-starter.md` + `test-env.md` moved
      to `docs/releasing/0.1.0-alpha.5/tmp/`; 25 issues inventoried + grouped.
- [ ] (next) Workstream A/B/F — engine, security, integrity.
- [ ] (next) Workstream C — defects/quality.
- [ ] (next) Workstream E step 1 — tooling `pyproject.toml`.
- [ ] (next) Workstream D — PI surface, incrementally.
- [ ] (next) Workstream G — cadence dispositions recorded.

## 8. Execution log

- 2026-06-15 — Scoped alpha.4 from milestone #3 (25 open). Tactical: grouped by
  blast radius (engine/security/integrity before broad UI), kept the deferred
  tracking issues out of the deliverable set. Architectural calls remain in their
  ADRs — e.g. the wheel migration is ADR-76 (deferred), not decided here.
- 2026-06-15 — Decision deferred to ADR, not recorded here: whether to un-defer
  ADR-76 (full wheel migration). Blocked on the §4.5 policy-gate version-skew
  choice and the ADR-69 rename ordering (see the packaging note).

## 9. Surprises & discoveries

- Several alpha.4-milestoned issues are **deferred-ADR tracking issues**
  (#521, #414, #412, #370, #439) — milestoned for visibility but not buildable
  deliverables. Listed in Workstream G so the active scope isn't overstated.
- Six PI-surface issues (#380, #375, #378, #343, #145-adjacent) cite **retired
  `docs/design/*` paths**. Each needs its reference repointed to the current
  ADR/doc before build — a zero-contradiction fix that travels with the feature.
- #381 is blocked by #379 (calibration threshold spec), which is **not in the
  alpha.4 milestone** — a cross-milestone dependency to surface.

## 10. Interfaces & dependencies

- **Ingest:** `src/.memoria/engines/ingest/extract.py` (ADR-30 tier order; #438),
  `src/.memoria/engines/ingest/resolve_merge.py` (`fetch_*`; #437). NCBI/Unpaywall
  keys already provisioned in profile `.env`.
- **Transport:** ADR-31 native Obsidian MCP over loopback; #527 depends on
  Hermes CA/insecure-TLS support (external dependency — verify before building).
- **Upgrade:** `golden.py` manifest + ADR-55 (#339).
- **Packaging:** full design + the policy-gate version-skew options (i/ii/iii)
  are in [the packaging design note](install-a-real-package.md); the wheel
  carries `assumes: [44, 46, 69, 73]` (not 55 — golden never covered code).
- **PI surface:** ADR-57 (deterministic top-K vs LLM line; #376), ADR-54
  (worklists; #336). Each D item needs an in-Obsidian affordance (PI rule).

## 11. Artifacts & notes

- File moves (this PR): pure git renames of `project-starter.md` and
  `test-env.md` from the alpha.4 `tmp/` into `docs/releasing/0.1.0-alpha.5/tmp/`
  (no content change).
- Per-issue transcripts to be pasted here as each workstream lands.

## 12. Outcomes & retrospective

- **Shipped:** (fill as workstreams close — each maps to a merged PR.)
- **Still open:** (remaining gaps → keep their GitHub issues open.)
- **Routed to:** decisions → ADRs (e.g. ADR-76 for packaging); readiness/scope →
  milestone #3 issues; this plan holds no durable record of its own.
- **Lessons:** (fill at checkpoint close, before deleting this `tmp/` note.)
