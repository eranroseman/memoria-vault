# ADR implementation-gap audit

**Date:** 2026-06-21
**Question:** For each `status: accepted` ADR, does the code actually implement the decision? (Implementation-gap analysis — distinct from "does the ADR name its enforcement mechanism.")
**Verified against:** `src/.memoria/` (gate, profiles, operations, schemas, scripts), `memoria/runtime/` (repo-root package), `scripts/`, `tests/`, `src/.obsidian/`, and the installed Hermes v0.14.0 runtime at `~/.hermes/`. Code is the source of truth; the ADR's own prose is not.

## Coverage note

- **112** ADR files total; status distribution: **75 accepted**, 19 proposed, 14 superseded, 2 rejected, 1 untagged (template/index), 1 malformed status line.
- **75 / 75 accepted ADRs audited** (74 freshly audited across six parallel agents + ADR-60, the supplied UNIMPLEMENTED template). Full coverage, no sampling.
- **No `status: deferred` ADRs exist** — this repo uses `proposed` for forward-looking/deferred decisions (per the ADR-only decision model). Spot-checked the highest-risk proposed ADRs for silent half-builds (89 learning-to-rank, 90 claim-sentence-classification, 93 keyphrase tags, 94 record-linkage dedup, 96 keep-revert loop, 108 liteparse): **none are half-built** — none of their named libraries/mechanisms appear anywhere in `src/`. The proposed set is cleanly un-started.

### Classification counts (accepted ADRs)

| Class | Count | ADRs |
|---|---|---|
| **UNIMPLEMENTED** | 4 | 60, 83, 35, 39 (last three forward-looking/deferred-by-own-text; 66 is contract-only) |
| **DIVERGED** | 1 | 55 (`golden_restore upgrade` is test-forbidden) |
| **PARTIAL** | 10 | 27, 41, 77, 30, 56, 78, 10, 45, 76, 73 |
| **IMPLEMENTED** | 60 | (the rest — see bulk list) |

> Note: a handful of ADRs are dual-classified in the body (e.g. 77 = IMPLEMENTED logic / PARTIAL on the Bases-view surface; 66 = contract-only). They are counted once, by their dominant gap.

---

## Tier 1 — UNIMPLEMENTED & DIVERGED (the real surprises)

### ADR-60 — Cross-vault and cross-project knowledge sharing — **UNIMPLEMENTED**
*(supplied calibration template — restated for completeness, not re-investigated)*
- **ADR claim:** cross-vault read-only sharing, enforced by the policy hook's vault-root resolution.
- **Code reality:** `src/.memoria/mcp/policy_hook.py:155-157` `vault_root()` returns `parents[2]` of the hook file — a single vault root. There is no multi-vault path, no cross-vault read scope, no second-root resolution anywhere in the gate.
- **Impact:** the headline cross-vault capability does not exist; the named enforcer is single-vault only.
- **Recommendation:** mark-deferred (or implement if cross-vault is in scope for a release).

### ADR-83 — Direct PI relate control — **UNIMPLEMENTED**
- **ADR claim** (`83:27-31`): an Obsidian command / form action letting the PI pick source note + relation type + target, preview the frontmatter change, and apply it to the source's existing `links:` map.
- **Code reality:** no such control. No relate/relation command in QuickAdd (`src/.obsidian/plugins/quickadd/data.json`) or Commander (`cmdr/data.json`); `rg relate|relation type` over `src` returns nothing. Closest scripts are `link-claim.js` (a *suggestion delegator* — writes a callout + delegates a Librarian card) and `create-linked-claim.js` (creates a *new* claim, doesn't edit an existing `links:` map). No implementing PR in history.
- **Impact:** PI still hand-edits `links:` YAML — exactly the gap ADR-83 names.
- **Recommendation:** mark-deferred — ADR-83 is explicitly forward-looking ("When this matters…"); no code was expected yet, but it is `accepted` with zero implementation.

### ADR-35 — Cross-run skill-insights memory — **UNIMPLEMENTED** (deferred-by-own-text)
- **ADR claim** (`35:42`): a `00-meta/skill-insights/` log of cross-run meta-claims; ADR states "Files: none currently," trigger-gated on issue #371.
- **Code reality:** no `skill-insights/` dir, log, meta-claims schema, or recurrence sweep. The cited *prerequisite* (classify-miss instrumentation) does exist (`operations/processing/ingest/classify.py:187-191`), so the trigger signal is buildable; the memory is not built.
- **Impact:** low — ADR is honest about deferral.
- **Recommendation:** mark-deferred (no change needed; ADR already says so).

### ADR-39 — Per-note-type acceptance checklists ("frozen evaluator") — **UNIMPLEMENTED** (forward-looking)
- **ADR claim** (`39:17`): per-type acceptance criteria the agent checks *before filing* (e.g. claim = falsifiable, ≥1 citekey, title-is-the-claim, <250 words).
- **Code reality:** no pre-file checklist mechanism. `schemas/types/claim.yaml:7-12` + `operations/lib/schema.py:112` enforce only field presence/type/enums — no falsifiability, word-count, or title check. The only trace is an optional *pattern* (`system/patterns/check-falsifiability.md`), agent-run, not a gate.
- **Impact:** low — ADR frames this as a future direction with an unmet re-entry trigger (50+ claims).
- **Recommendation:** mark-deferred (re-entry trigger unmet).

### ADR-66 — Semi-auto triage / consensus pre-filter / tournament ranking — **UNIMPLEMENTED beyond the calibration contract**
- **ADR claim** (`66:36-43`): the ADR itself maps the shipped slice to a *contract only* (calibration thresholds, `production_enabled: false`).
- **Code reality:** `schemas/calibration.yaml:28-60` holds the null-threshold, `production_enabled: false` contract — no consensus pre-filter, no pairwise tournament, no batch-triage, no learning-to-rank anywhere in `src/`.
- **Impact:** low — matches the ADR's own mapping.
- **Recommendation:** mark-deferred (contract-only state is accurate).

### ADR-55 — repo ships src/, installer scaffolds+populates, golden copy restorable — **DIVERGED**
- **ADR claim** (`55:36-43,57`): `golden_restore.py upgrade --source SRC --apply` does a three-way reconcile (old-golden vs new-source vs live).
- **Code reality:** `operations/integrity/linter/golden_restore.py` implements only `stage|check|restore` (CLI choices `:156`). **There is no `upgrade` command, and `tests/test_golden_restore.py:125` (`test_upgrade_command_is_not_shipped`) actively asserts its absence.** The reconcile helper `_stage_from_source` is dead code. Single-release drift restore works; cross-release upgrade reconcile is unimplemented and test-forbidden.
- **Impact:** the ADR's fresh-install + three-way-merge upgrade promise is contradicted by a CI test.
- **Recommendation:** update-ADR-to-match-code — defer the `upgrade`/three-way clause to ADR-76 or retire it.

---

## Tier 2 — PARTIAL (built but under-delivers or diverges from the prose)

### ADR-10 — Claim supersession relation — **PARTIAL** (highest-value functional gap)
- **ADR claim** (`10:23`): "`query` and `write` exclude superseded claims **by default**."
- **Code reality:** the default-exclusion is enforced only in `link-claim.js:80` (link-candidate ranking) and the FAMA linter detector (`detectors.py:579-615`). It is **not** wired into the find skill (`catalog-find-source`) or draft skill (`draft-write-section`) — those SKILL.md files contain no superseded/lifecycle filter. The schema/FAMA machinery (4 of 5 claims) is otherwise fully built.
- **Impact:** a superseded claim can still surface in find/draft results — the exact FAMA failure ADR-10 exists to prevent, still live on two named surfaces.
- **Recommendation:** implement — add the superseded-by-default filter to the find and draft skills (or narrow the ADR's "query/write" scope to link-ranking + the linter).

### ADR-30 — Tiered ingest pipeline — **PARTIAL** (deterministic spine built; Tier-1 "value" layer absent)
- **ADR claim** (`30:57-86`): full-text chain (S2ORC/CORE/arXiv/OCR), embedding+zero-shot **tag suggestion** ("Tier-1 carries the system's value"), one hard-schema LLM classify call, Tier-2 NLI contradiction + arXiv→code.
- **Code reality:** deterministic spine is solid (ingest MCP, per-field best-source merge `resolve_merge_logic.py:71-123`, ID-keyed linking, sandboxed PDF parse, board-routed sweeps). But the full-text chain ships only Unpaywall→PMC→local-PDF (`extract.py:228-281` — **S2ORC/CORE/arXiv/OCR absent**); **tag-suggestion is entirely absent**; classify **diverged** to deterministic OpenAlex-topic classification (`classify.py:118-154`), not a schema-constrained LLM call; Tier-2 absent.
- **Impact:** high — the layer the ADR calls Tier-1's value (suggested tags) is unbuilt, and classify silently diverged.
- **Recommendation:** update-ADR-to-match-code (record the classify divergence + thinner full-text chain) and mark-deferred the tag/Tier-2 pieces with tracking.

### ADR-56 — Low-confidence extraction routes to a flag — **PARTIAL** (realized for the wrong dimension)
- **ADR claim** (`56:26-34`): below a confidence floor, **entity-resolution, dedup, and license/venue** calls emit an Inbox near-tie flag; floor in `calibration.yaml`.
- **Code reality:** the flag pattern exists only for **classification** (`classify.py:118-167`) — a dimension ADR-56 doesn't list. Entity resolution (`link.py:87-125`) is strictly ID-keyed find-or-create with **no fuzzy merge to gate**; `append_by_name_audit` only counts collisions (`:165-191`). The declared `entity_resolution.confidence_floor: 0.85` (`calibration.yaml:4-6`) is **dead config** (`model_version: null`, no model exists). Dedup / license-venue gates absent.
- **Impact:** medium — the ADR reads as if the wrong-merge path is confidence-flag-guarded; in practice the guard is "never fuzzy-merge," and the realized flag covers an unnamed dimension.
- **Recommendation:** update-ADR-to-match-code — record that entity-resolution is guarded by refusing fuzzy merges (recorded-by-name), the floor is reserved-but-unconsumed, and the realized flag dimension is classify.

### ADR-78 — Thesis note type — **PARTIAL**
- **ADR claim** (`78:24-46`): `thesis` type with full lifecycle, transition-to-`current` review-gated, **schema must reject a born-`current` thesis**.
- **Code reality:** type + lifecycle enum + promotion gate all present (`schemas/types/thesis.yaml`). But the validator (`operations/lib/schema.py:135-137`) enforces the gate only by requiring `promoted_at` provenance when `lifecycle == current`; `initial_lifecycle` is a declared field **no validator reads**. A note fabricating `promoted_at` would pass — "reject born-current" is approximated, not directly enforced.
- **Impact:** low/medium — practical guard holds for honest writers; literal ADR invariant unchecked.
- **Recommendation:** update-ADR-to-match-code (gate is "current requires promotion provenance") or implement an `initial_lifecycle` check.

### ADR-27 — Hermes-native config; toolset allowlist as the write-path boundary — **PARTIAL**
- **ADR claim** (`27:129-141`): "With no filesystem write tool, the agent's only way to write the vault is the obsidian MCP path."
- **Code reality:** the config model (mcp_servers in config.yaml, computed `disabled_toolsets`) is fully implemented across all profiles. But the premise that the allowlist *is* the boundary is false on v0.14.0: `disabled_toolsets` is schema-subtraction (hides the tool from the model); `registry.dispatch` runs any registered tool with no enablement check. What actually bounds the write path is the ADR-28 plugin's default-deny — already annotated on-box.
- **Impact:** the security framing is weaker than written; the plugin closes it.
- **Recommendation:** update-ADR-to-match-code (the supersession header + ADR-28 note already do this; no code change).

### ADR-41 — Configurable review-gate mode (blocking/advisory) — **PARTIAL**
- **ADR claim** (`41:21-26`): a single configurable `review_mode` with `blocking`/`advisory` values.
- **Code reality:** `REVIEW_MODE = "blocking"` is a **hardcoded module constant** with no config read (`memoria/runtime/policy/audit.py:14`), stamped into every audit row. No `advisory` branch exists; the decision core has no mode parameter. Only the audit *attribution* sliver shipped — the configurable advisory behavior does not.
- **Impact:** the publication comparison study cannot run an advisory arm.
- **Recommendation:** mark-deferred (the ADR itself scopes advisory behavior as study-gated, not day-1).

### ADR-45 — Release management: tracking-issue gates + release-please — **PARTIAL**
- **ADR claim:** release-please auto-owns versioning; a `/release` skill scaffolds the gate checklist.
- **Code reality:** release-please **manifest mode** is configured (`release-please-config.json`), but the workflow is **paused** — `release-please.yml:16-17` is `workflow_dispatch`-only (pre-alpha, manifest `0.0.0`), so it does not yet auto-own versioning. The **`/release` skill does not exist**; scaffolding moved to `.agents/playbooks/release.md`. `status_doctor.py` is CI-wired.
- **Impact:** low-medium — a reader expects live auto-releases + a `/release` skill, neither present.
- **Recommendation:** update-ADR-to-match-code (note release-please is paused; replace `/release` skill with the release playbook).

### ADR-76 — Versioned vault release / reconciling installer — **PARTIAL** (one stale path)
- **ADR claim** (`76:80-81`): policy core at `src/.memoria/memoria_runtime/policy/`; reconciling installer + release manifest.
- **Code reality:** steps 1-3 landed ahead of the doc (repo-root `pyproject.toml`, `memoria/` package, `memoria/runtime/{vaultio,jsonl,time,paths,policy}/`). **The cited path `src/.memoria/memoria_runtime/policy/` is deleted** — `test_package_spine.py:34-35` asserts its absence; the core moved to `memoria/runtime/policy/` (7 modules). Steps 4-5 (console scripts, reconciling installer, release manifest) correctly deferred — installer is still rsync/`cp`.
- **Impact:** low-medium — a reader trusting Decision 2's path looks in a deleted, CI-forbidden location.
- **Recommendation:** update-ADR-to-match-code (repoint Decision 2 to `memoria/runtime/policy/`).

### ADR-73 — Documentation reference conventions — **PARTIAL**
- **ADR claim:** Rule 3 — bare `(D##)` codes "purged"; Rule 2a — ADR refs gated by Diátaxis page-type.
- **Code reality:** Rules 1 (no published→src/ links) and 2b (no bare `(ADR-NN)`) are code-enforced in `scripts/docs_doctor.py` + CI. **Rule 3 is DIVERGED:** 7 bare `(D##)` codes remain (all inside `docs/adr/`, e.g. `49-...:18,32`, `46-...:73`) and no tool checks for `(D##)` — "purged" is literally false and unenforced (published prose is clean). **Rule 2a is convention-only** — the script's docstring declares page-type classification out of scope, yet the ADR presents it as a rule.
- **Impact:** low — doc hygiene; published pages are clean but the absolute claim and Rule 2a are overstated.
- **Recommendation:** update-ADR-to-match-code (soften "purged" → "purged from published pages"; mark Rule 2a convention-only, or add `check_bare_d_codes`).

### ADR-77 — Project gate — **PARTIAL on the Bases-view surface only** (core logic IMPLEMENTED)
- **ADR claim** (`77:32-43`): deterministic maturity logic + a "version-pinned pilot" custom Bases view.
- **Code reality:** maturity logic matches **exactly** — `structural_impact_analysis.py:61-66` (`>=5` relations, `>=1 supports`, `>=1 contradicts`; `MATURITY_RELATION_THRESHOLD=5`), thesis-rooted component BFS, saturation, articulation-point impact — all deterministic, no LLM. Could not confirm a working `registerBasesView` custom-view surface; the ADR itself flags it as the riskiest, narrowest piece.
- **Impact:** core gate is real; the Obsidian rendering surface is the soft spot (as the ADR predicts).
- **Recommendation:** implement → core done; verify/track the Bases-view pilot separately.

---

## Tier 3 — IMPLEMENTED (bulk)

These match their decision; deferred tails are correctly absent. Where noted, the *ADR prose* is slightly stale (code is correct) — an update-the-ADR, not implement, action.

| ADR | Title (short) | Note |
|---|---|---|
| 03 | Structural review gate | Enforced via decision-core `dry_run` (`decision.py:146`) + ADR-28 plugin block. |
| 21 | L3 autonomy ceiling | Canonical writes gated for all lanes; Engineer has no exec capability; no keep/revert loop. |
| 22 | Build on Hermes runtime | Thin overlay; rides `hermes kanban` CLI, never reimplements kanban.db. |
| 23 | Seven scoped memory substrates | Already self-corrected; substrate #3 (session_search) disabled in all 5 profiles. |
| 24 | Single-researcher scope | Constraint respected; no multi-user/per-user machinery. |
| 25 | Two session logs | Hash-paired audit.jsonl + deterministic 24h digests; all numeric claims (50 MB, 24h) confirmed. |
| 26 | Repo is install unit | `install.sh`/`.ps1` deploy from `src/`, idempotent `--profiles-only`, `.env` never clobbered. |
| 28 | Write gate as Hermes plugin | Plugin deployed to all 5 profiles, fail-closed on deny+exception. **Residual:** stale `DENY_DIRECT_TOOLS` (`policy_hook.py:88`) lists dead names + misses the real `process` tool; fails OPEN on register failure. |
| 29 | Layered testing framework | Coverage matrix, `check_test_refs.py` in CI, `test-l2.sh` fs-shim smoke. |
| 31 | Native obsidian MCP over HTTPS | All profiles → loopback HTTPS + Bearer; `DENY_OBSIDIAN` enforced + tested. ADR's `--self-test` flag is gone (now `tests/`). |
| 32 | External access over MCP | No terminal/file/code_execution shipped; retirement of the two terminal exceptions confirmed. ADR cites old `verify_mcp.py`; real engine is `retraction.py`. |
| 33 | BERTopic cluster MCP | Real NetworkX graph + optional BERTopic with structured degradation; lane sandbox intact. |
| 38 | Pre-file similarity gate | Shadow primitive exactly as ADR states (qmd search → callout → telemetry, no block). |
| 43 | Skill governance | Dashboard-only `skill-state.md` consistency view. ADR's "25 skills" is now 27 (cosmetic). |
| 46 | Seven-layer architecture | All seven layers have concrete homes; MCP-as-policy-gate realized. |
| 47 | Type-first category folders | `folders.yaml` machine-read; +`spaces` (correct ADR-101 evolution). |
| 48 | Co-PI + 5 profiles | Exactly 5 profiles; Co-PI read-only (`write_scope: []`); no legacy specialist profiles. |
| 49 | Catalog in Bases; Linter commit gate | Bases-are-views; schema-check pre-commit gate blocks git writes (exit 1). |
| 50 | Universal lifecycle & maturity | Exact 5-state chain + per-type subsets; maturity/recommendation soft signals; `reference` dropped; hub present. |
| 51 | Inbox category & honesty card | All 5 inbox types; honesty-card fields **required** on proposals; finding+verdict on verification cards. |
| 52 | Links vs relationships | Clean schema split (notes→`links`, entities→`relationships`); ingest builds relationships. *Soft:* "Linter rejects category errors" stronger than code (unknown fields allowed). |
| 53 | Pattern library | Patterns in `system/patterns/`; one runner refuses gated targets + logs provenance. |
| 54 | Two decision kinds + batch worklists | Approval-gate vs work-prompt; per-row `decision` field; one aggregate work-prompt per batch; no auto-accept. |
| 57 | Engines write, agents judge | Every mechanical writer named is Operations code; principle (no structural guard, by nature). |
| 62 | Measurement & verification harnesses | `metrics_aggregate.py` + cron shipped; deferred harnesses correctly absent. |
| 63 | Multi-machine deployment | Co-PI always-safe baseline holds; no premature VPS/Syncthing (matches guard). |
| 64 | Native Windows support | `install.ps1` is a real native installer (judged from script; not executed on Windows). |
| 67 | Drift procedures | golden-copy + skeleton/plugin-config drift detectors + daily lint cron. |
| 69 | Operations layer naming | `engines/`→`operations/` with all four category dirs; `golden_restore.py` present. Refactor landed. |
| 70 | Navigation gates/dashboards | Four surfaces as notes; JTBD action-first inbox; vocab now "spaces" (ADR-101). |
| 71 | Structured capture forms | `gen-forms.py` generates Modal Forms from schemas; `--check` fails CI on drift. |
| 72 | Command surfacing | Commander ribbon/header placement + 27 palette-reachable QuickAdd commands; Shell Commands absent. |
| 74 | Pinned plugin supply-chain | `plugin-provenance-lock.json` + doctor in CI; updater correctly deferred. |
| 75 | GitHub Project fields | Field set + parent/sub-issue model documented; GitHub-side config intentionally unversioned. |
| 79 | Argument graph & warrant | `supports`/`contradicts` graph; `warrant`/`unstated-warrant` reserved + off (as decided). |
| 80 | Ephemeral test-env | Phase 1 `workflow-replay` harness + `e2e-smoke.sh` in CI; Phase 2 (Docker/GPU) deferred. |
| 81 | Persistent gate dashboards | Four `spaces/*.md` Bases dashboards; one workspace; homepage → `spaces/inbox`. |
| 84 | Read-only Obsidian Inspector | Real custom plugin `memoria-inspector/main.js`, read-only, tested. "Readiness" issue #697 is stale. |
| 100 | Exploration-trace capture | QuickAdd "record exploration trace" → structured fleeting note, never auto-promoted. |
| 101 | Navigation spaces; gate reserved | Full migration: `space.yaml`, folders.yaml, detectors, `src/spaces/`, homepage — `src/gates/` gone. |
| 104 | Telemetry three planes | All three planes have writer + reader; minor: `cost-misses.jsonl` has a writer but no aggregator. |
| 105 | Diagnostic plane | Fully built + unit-tested in `memoria/runtime/diagnostics.py` (XDG dir, content-light, self-disarming raw). #736 stale. |
| 106 | Cost & disposition capture | Cost join works end-to-end; lives in `board_export_cost.py` (ADR says `board_export.py`); "version pinned" overstated. |
| 109 | Project management native views | `projects.base` + Modal Form + schema-frontmatter writes; zero rejected PM plugins bundled. |
| 05 | Zotero backbone | `.memoria/memoria.bib` tracked stub, populated bib gitignored; Better BibTeX capture flow. |
| 06 | Citekey convention | External Better BibTeX config; code consumes pinned citekey, never regenerates. |
| 07 | Code agent attachment | Engineer wires claude-code + codex per-agent; writes scoped to `projects/*/code/**`; aider planned-only. |
| 09 | Contradictions dashboard | Deterministic Dataview over `links.contradicts`, zero LLM (v1 exactly). |
| 11 | vault-eval | Dispatcher + deterministic scorer + dashboard + gold set + quarterly cron. Minor: eval-task note type now exists. |
| 12 | obsidian-linter reference-only | Plugin genuinely absent — constraint honored by absence. |
| 13 | Homepage front-door | Opens `spaces/inbox` (ADR says stale `gates/inbox`); writes nothing. |
| 14 | Advisor-review export | Documentation decision; export routes documented in `export-a-draft.md`. |
| 15 | Project membership from topic hint | `classify.py` reads optional hints, proposes by overlap count, logs stage; absent file = no-op. |
| 16 | Systematic-review adopt-on-demand | Baseline schema clean of PRISMA/review_mode/RoB/dual-rater — honored by absence. |
| 18 | agent_verdict→agent_recommendation | Rename everywhere; deliberately **one-way** (no fallback, asserted by test) — ADR's "may retain fallback" is stale. |
| 19 | MOC threshold alert | `hub_threshold(threshold=15)` LOW advisory + `hub_handoff` map-lane delegation; never auto-creates hubs. |
| 20 | Publication path | Six-signal capture wired (transitions/disposition/cost/FAMA); benchmark-paper half is forward-looking. |

---

## Cross-cutting observations

1. **One mechanism backs the whole safety cluster.** ADRs 03/21/46 are all enforced by the same decision core (`decision.py:146` `dry_run`) + the ADR-28 plugin block. So the **ADR-28 residual is the single highest-leverage real gap touching this cluster**: `DENY_DIRECT_TOOLS` (`policy_hook.py:88`) lists dead tool names (`write_file`, `patch`, `terminal`, `run_command`, `code_execution`, …) and **misses the real Hermes `process` tool**, and the plugin **fails OPEN if it fails to register**. The primary obsidian-write gate is live and fail-closed; the "hard-deny direct tools" layer is largely a no-op. (Known calibration item — recorded here because it sits under three IMPLEMENTED ADRs.)
2. **Stale-prose, correct-code is the dominant pattern.** Most PARTIALs and several IMPLEMENTEDs need an *ADR text update*, not code: ADR-13 (`spaces/inbox`), 18 (one-way rename), 11 (eval-task type), 27/46 (allowlist≠boundary), 31 (`--self-test` gone), 32 (`retraction.py`), 76 (policy path moved), 106 (file moved + version-pin overstated), 73 (Rule 3 "purged").
3. **Recent ADRs carry stale "implementation readiness" issues.** 84 (#697), 105 (#736) are fully built + tested — close the tracking issues.
4. **Genuine functional gaps requiring code (not doc) work:** ADR-10 (superseded-by-default not in find/draft skills — a live FAMA failure), ADR-30 (tag-suggestion layer absent + classify diverged), ADR-55 (`upgrade` reconcile test-forbidden), ADR-83 / ADR-60 (whole feature unbuilt).
5. **No proposed ADR is silently half-built** — the deferred set is cleanly un-started.
