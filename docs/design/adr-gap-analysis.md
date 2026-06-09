---
topic: explorations
title: ADR → implementation gap analysis
status: analysis
created: 2026-06-07
parent: Design notes
grand_parent: Explanation
nav_order: 2
---

# ADR → implementation gap analysis

A point-in-time audit of every **accepted** ADR (`docs/adr/01`–`33`) against the
**actual codebase** — what each decision mandates vs. what the repo does. Verified by
reading each ADR and grepping/reading the real files (no assumptions). Reviewed
**2026-06-07**.

> **Scope:** measured against the *currently approved* ADRs — **not** the proposed
> [four-layer redesign](memoria-redesign.md), which would supersede ADR-01/04 and amend
> many others. Where a gap overlaps the redesign, it's noted.

## Summary

**21 ✅ implemented · 10 🟡 partial · 2 ❌ not built** (of 33).

The architectural core is fully realized: the three-layer model and folder scheme
(01–04), the autonomy ceiling and its structural enforcement (21), the Hermes-native
config + plugin write-gate (22, 27, 28), the native obsidian MCP and access-over-MCP
posture (31, 32), memory substrates (23), and the install model (26). Gaps cluster in
**synthesis tooling, ingest depth, and doc/spec drift** — and most are already
known-deferred.

### Gaps that are claim-vs-reality (worth fixing — docs/config assert something the code doesn't do)

- **ADR-19** — the check-catalog + `linking.md` say a Tier-1 "topic needs a MOC" alert
  ships; **no detector and no dashboard query implement it.**
- **ADR-08** — `link-related-claims.md` says `schema-check` flags off-vocabulary
  `relations:` keys; `detectors.py` only checks required-field presence. The `supports`
  leg also has no runtime consumer.
- **ADR-33** — clustering is unbuilt **and** the dead `scikit-learn`/`umap-learn` skill
  grants are still active in `mapper.yaml`, with `cluster-mapping` docs instructing that
  non-runnable path. Mapper clustering is granted-but-non-functional.
- **ADR-30** — the ADR-mandated PDF-parsing **sandbox** (subprocess + `rlimit`, MuPDF CVE
  surface) is not implemented; extract does a lazy in-process import.
- **ADR-06** — the BBT citekey format string differs three ways (ADR
  `[title.lower:select,1,1]` vs every doc `[shorttitle1_0]`) — real citekey-mismatch risk.
- **ADR-05** — `memoria.bib` is documented as "excluded from git" but is git-tracked (an
  intentional empty stub) with no `.gitignore` entry.

### Gaps that are known-deferred (tracked; not surprises)

ADR-11 (vault-eval — entirely unbuilt, deferred), ADR-15 (project-hints not yet consumed
by classify), ADR-20 (CiteME fixture unbuilt; `disposition`/`cost` telemetry blocked on a
Hermes upstream limit), ADR-29 (L2b runtime harness deferred), ADR-30 (full-text
fallback chain shortened to PMC + local-PDF), ADR-25 (narrative session-summary writer
not yet coded).

---

## Per-ADR detail

Legend: ✅ implemented · 🟡 partial · ❌ not built · ⚪ superseded/N-A.

### ADR-01 — Three-layer architecture (board · workers · vault) — ✅
- **Decision:** separate board state, execution (profiles), settled knowledge (vault);
  worker→vault boundary enforced at runtime by the policy MCP.
- **Evidence:** vault scaffolded by `scripts/install.sh`; 7 profiles under
  `vault/.memoria/profiles/`; board fields in `board_export.py`; boundary in
  `policy_mcp.py` (`PolicyEngine.check`/`decide`, default-deny + SHA-256 audit).
- **Gap:** none.

### ADR-02 — Seven specialist profiles — ✅
- **Decision:** exactly seven profiles; no Orchestrator/Reviewer; static routing; review
  is a human action; agents advise via `agent_recommendation`.
- **Evidence:** 7 profile dirs + 7 lane-overrides + 7 `SOUL.md`; no orchestrator/reviewer;
  `board_export.py` reads `assignee`/`review_status`/`agent_recommendation`; per-profile
  write-walls self-tested in `policy_mcp.py`.
- **Gap:** none.

### ADR-03 — Structural review gate via policy MCP — ✅
- **Decision:** writes to the four canonical zones degrade to `dry_run`; only human
  `review_status: approved` reaches canonical; promotion is manual.
- **Evidence:** `policy_mcp.py` `REVIEW_GATED_PREFIXES` (claims/reference/moc/deliverables);
  `decide()` degrades to `dry_run`; audit with before/after hash; weekly-review surfaces an
  evergreen "Reference promotion backlog" (human action), no auto-promotion in code.
- **Gap:** none.

### ADR-04 — Folders encode lifecycle, not topic — ✅
- **Decision:** six numbered lifecycle folders; topics in frontmatter; `40-workbench/`
  unit is the project.
- **Evidence:** `install.sh` scaffolds `00-meta … 50-deliverables` + project sub-stages;
  templates carry `topic: []`/`methods: []`; documented in `docs/explanation/architecture/vault.md`.
- **Gap:** none (folders are created at install time per ADR-26, not committed).

### ADR-05 — Zotero + Better BibTeX backbone — 🟡
- **Decision:** Zotero canonical; `memoria.bib` source of truth (read-only for Librarian);
  pinned citekey required; bib **excluded from git**; PDFs stay in Zotero (`pdf_uri`).
- **Evidence:** `vault/.memoria/memoria.bib` with "Zotero owns it" header; Librarian lane
  grants no `.memoria/` write; `ingest_paper.py` resolves by citekey; no PDFs in `vault/`.
- **Gap:** the ADR says the bib is "excluded from git," but it's **git-tracked** (an
  intentional empty stub) with no `.bib` entry in `.gitignore`. Reconcile ADR or gitignore.

### ADR-06 — Citekey naming convention — 🟡
- **Decision:** `authoryearword`; BBT formula `[auth.lower][year][title.lower:select,1,1]`;
  pin immediately.
- **Evidence:** `paper-note.md` has `citekey`; docs teach the convention + pin discipline.
- **Gap:** **format-string drift** — ADR mandates `[title.lower:select,1,1]`, but every
  user doc (`quickstart`, `set-up-zotero`, tutorial, `frontmatter`, `pin-a-citekey`) says
  `[shorttitle1_0]`. Reconcile to one canonical BBT string.

### ADR-07 — Code agent attachment — ✅
- **Decision:** Coder delegates substantive coding to an external agent; scaffolds
  `code-note` handoffs; owns commit/review gate.
- **Evidence:** `memoria-coder/SOUL.md` + `coder.yaml` (allowlist `codex`/`claude-code`,
  write scope `40-workbench/*/06-code/**`); `code-note.md` template; `kilocode` is the
  model provider, distinct from a coding skill.
- **Gap:** none.

### ADR-08 — Typed `relations:` frontmatter — 🟡
- **Decision:** nested human-set `relations:` (`supports`/`contradicts`) on claim-notes;
  Linter flags keys outside the vocabulary.
- **Evidence:** schema slot in `claim-note.md`; documented in `frontmatter.md`;
  `contradicts` consumed by the dashboard.
- **Gap:** the **Linter vocabulary check is missing** — `frontmatter_schema_check()` in
  `detectors.py` only checks required-field presence; docs claim `schema-check` enforces
  the vocabulary. `supports` has no runtime consumer.

### ADR-09 — Contradictions dashboard — ✅
- **Decision:** Dataview dashboard over human-set `relations.contradicts`; no LLM; framed
  as "worth resolving."
- **Evidence:** `vault/00-meta/01-dashboards/contradictions.md` (dataviewjs, dedupes
  symmetric pairs, deferred-NLI empty state).
- **Gap:** none.

### ADR-10 — Claim supersession — ✅
- **Decision:** top-level `superseded_by`; currency derived from it; query/write exclude
  superseded; FAMA-style Linter detector.
- **Evidence:** `superseded_by` in `claim-note.md`; `fama_exposure()` in `detectors.py`
  (HIGH severity, self-tested); exclusion documented for retrieval.
- **Gap:** none material.

### ADR-11 — vault-eval maintenance capability — ❌
- **Decision:** scheduled `eval` card fans gold tasks to profiles; non-committing eval
  writes; Linter scores (recall@k/support-rate/FAMA); results to `99-system/metrics/eval/`.
- **Evidence:** only docs/placeholders — `on-disk-layout.md` marks `metrics/`+`eval/`
  "deferred"; no `eval/`, no metrics dir, no scheduled card, no scoring code.
- **Gap:** entire capability unbuilt (deferred). The FAMA *check* exists (ADR-10); the
  harness does not.

### ADR-12 — obsidian-linter reference-only — ✅
- **Decision:** incompatible; do not install; markdownlint owns hygiene, Memoria Linter
  owns frontmatter/structure.
- **Evidence:** listed "Incompatible — do not install" in `obsidian-plugins.md`; absent
  from `vault/.obsidian/plugins/`; markdownlint + `detectors.py` own their domains.
- **Gap:** none.

### ADR-13 — Homepage front-door — ✅
- **Decision:** thin `home.md` Dataview note opened on launch by view-only
  obsidian-homepage (recommended).
- **Evidence:** `vault/home.md` launchpad; plugin installed + enabled,
  `data.json: {value: home, openOnStartup: true, refreshDataview: true}`.
- **Gap:** none.

### ADR-14 — Advisor-review exports outside the frozen-deliverable contract — ✅
- **Decision:** static citeproc → frozen `50-deliverables/`; live-citation exports are
  non-deliverable working artifacts (not in `50-deliverables/`).
- **Evidence:** `export-a-draft.md` writes live routes (zotero.lua, ODF Scan) to
  `40-workbench/<project>/04-drafts/`, not `50-deliverables/`.
- **Gap:** none.

### ADR-15 — Project membership from per-project topic hint — 🟡
- **Decision:** optional `.memoria/project-hints.yaml`; Librarian scores candidate topic
  overlap to propose `projects` in `_proposed_classification`.
- **Evidence:** ships as `project-hints.yaml.example`; how-to + schema refs present.
- **Gap:** the classify step doesn't yet **consume** the hint (the Librarian
  classification skill scores only topic/methods/study_design). ADR-flagged as deferred to
  the classify impl.

### ADR-16 — Adopt-on-demand systematic review — ✅
- **Decision:** keep review-mode/PRISMA/quality fields/screening out of baseline; activate
  per-project on demand.
- **Evidence:** baseline carries none of the deferred fields; the single `review_mode`
  mention is framed as deferred; `run-a-systematic-review.md` is a manual procedure.
- **Gap:** minor — the glossary lacks the single explicit three-way "Review"
  disambiguation entry the ADR's see-also calls for. Decision holds.

### ADR-17 — Shared candidate frontmatter — ✅
- **Decision:** `candidate-note` as the 16th type; unified schema; Verifier gap-cards
  unified under `source: gap`; weekly-review query.
- **Evidence:** `candidate-note.md` template with the exact schema; registered in
  `note-types.md`; schema in `frontmatter.md`.
- **Gap:** none.

### ADR-18 — Rename `agent_verdict` → `agent_recommendation` — ✅
- **Decision:** rename across schema, `board_export.py`, dashboards, docs; values
  unchanged.
- **Evidence:** `board_export.py` reads `agent_recommendation` (legacy fallback,
  self-tested); new name across docs + Linter SOUL; old name only in historical refs.
- **Gap:** none.

### ADR-19 — Agent-proposed MOCs (threshold alert; Mapper stub deferred) — 🟡
- **Decision:** Tier-1 report-only "MOC threshold crossed" alert in the Linter/dashboard;
  Tier-2 Mapper stub deferred.
- **Evidence:** threshold in `linking.md`; check catalogued (Tier-1, "dashboard signal");
  Tier-2 correctly absent.
- **Gap:** **Tier-1 is documented but not implemented** — no MOC-threshold detector in
  `detectors.py`, no dashboard query surfaces "topic X ≥15 notes and no MOC." Catalog
  asserts it ships; nothing wires it.

### ADR-20 — Publication path: benchmark first, capture now — 🟡
- **Decision:** (1) commit to the vault-eval/CiteME benchmark paper first; (2) start
  six-signal instrumented capture in v0.1.
- **Evidence:** six-signal schemas in `telemetry.md`; `board_export.py` emits them
  (self-tested); cron wired; Verifier + FAMA signal present.
- **Gap:** (1) the public **CiteME vault fixture is unbuilt**; (2) `disposition.jsonl` +
  `cost.jsonl` stay **empty** (Hermes doesn't surface card `metadata` — documented
  upstream block); (3) the ADR's own links point at stale `project/releases/`+`proposals/`.

### ADR-21 — L3 autonomy ceiling, structurally enforced — ✅
- **Decision:** enforce the ceiling via the policy MCP (not prompts); promotions route to
  the human gate; scheduled ops write `10-inbox/` only; Coder is the sole keep/revert
  exception (`40-workbench/*/06-code/`).
- **Evidence:** `policy_mcp.py` `REVIEW_GATED` + `dry_run` degrade; `coder.yaml` allows
  only `06-code/**`, denies the canonical zones; rationale in `why-not-autonomous.md`.
- **Gap:** none.

### ADR-22 — Build on the Hermes runtime — ✅
- **Decision:** build on Hermes; Memoria supplies only conventions (gate overlay, policy
  MCP, SOULs, vault schema) on extension points, without modifying Hermes.
- **Evidence:** profiles use Hermes-native `config.yaml` (model routing + `mcp_servers`);
  installer deploys to `~/.hermes/profiles/`; gate overlay rides card `metadata`; no
  Hermes-internals changes.
- **Gap:** none.

### ADR-23 — Seven scoped memory substrates — ✅
- **Decision:** seven substrates (3 Hermes-native + 4 Memoria), each scoped.
- **Evidence:** `memory.md` lists exactly 7; the four Memoria ones are concrete
  (program = `research-focus.md`, project = `40-workbench/<project>/`, audit =
  `99-system/logs/` append-only, handoff = card `metadata`).
- **Gap:** none of substance.

### ADR-24 — Single-researcher scope — ✅
- **Decision:** one judgment-owner; multi-user review semantics out of scope.
- **Evidence:** stated in `what-memoria-is.md`; **zero** multi-user/per-user/shared-queue
  leakage in code; `review_status` is single-verdict.
- **Gap:** none — a constraint ADR satisfied by the absence of multi-user machinery.

### ADR-25 — Two session logs (audit vs. narrative) — 🟡
- **Decision:** append-only SHA-256-chained `audit.jsonl` (policy MCP) + per-session
  `sessions/YYYY-MM-DD-HHMM.jsonl` (Linter); `sessions/` created by installer.
- **Evidence:** `policy_mcp.py` audit (`append_audit`, `sha256_file`, before/after hash);
  `install.sh` creates `logs/sessions`; `vault-hash-drift` detector documented.
- **Gap:** (1) the "hash-chain" is **per-path drift detection, not a sequential
  cross-entry chain** as the ADR describes; (2) the per-session **narrative summary writer
  is prose-instruction only** (no code).

### ADR-26 — Repo is the install unit; idempotent profile deploy — ✅
- **Decision:** clone the repo; `install.sh` (+ `install.ps1` thin launcher); hand-authored
  profiles (compiler deferred to ADR-42); idempotent `--profiles-only` preserving `.env`.
- **Evidence:** `install.sh` (`--profiles-only`, `seed_profile_env`, rsync preserves
  notes+`.env`); `install.ps1` thin launcher; 7 hand-authored profiles; vault→docs use
  Pages URLs.
- **Gap:** none.

### ADR-27 — Hermes-native config; toolset allowlist gate — ✅
- **Decision:** `mcp_servers` per `config.yaml`; `disabled_toolsets = all − allowlist`;
  obsidian the only write path for the 5 non-terminal lanes; seed `.env`.
- **Evidence:** `config.yaml`s carry `mcp_servers {policy, obsidian}` +
  `disabled_toolsets` + `terminal.cwd` + `checkpoints`; standalone `mcp.json` retired.
- **Gap:** none beyond the documented partial supersession — the enforcement *mechanism*
  was replaced by ADR-28's plugin (`superseded_by: [28]`, mechanism-scoped). Config model
  stands.

### ADR-28 — Write gate as a Hermes Python plugin — ✅
- **Decision:** `memoria-policy-gate` plugin; fail-closed `pre_tool_call` +
  `post_tool_call`; reuse `policy_hook`; remove `hooks:` block; deploy via installer.
- **Evidence:** `plugins/memoria-policy-gate/__init__.py` (fail-closed `_gate`, both
  hooks); `plugin.yaml`; `deploy_policy_plugin` in installer; `plugins.enabled` set, no
  `hooks:` block; `policy_hook.py` defense-in-depth + self-test.
- **Gap:** none (the optional startup assertion remains a flagged follow-up).

### ADR-29 — Layered testing framework — 🟡
- **Decision:** L0–L5 + cross-cutting, indexed by a coverage matrix; determinism + drift
  (`check-test-refs.py`) + gate mapping; L2 split into hermetic L2a (in `--self-test`) and
  runtime L2b (opt-in `scripts/test-l2.sh`, nightly).
- **Evidence:** `docs/testing/coverage-matrix.md` + 5 plans; `check-test-refs.py` gating
  in CI; L1 self-tests in `python-selftest.yml`; template present.
- **Gap:** (1) ADR text says plans live in `project/tests/`; real dir is `project/test/`;
  (2) L2b harness (`scripts/test-l2.sh` + Option-B obsidian shim) unbuilt — described as
  future work; matrix openly tracks L5/recovery/security/perf/deploy as ⛔.

### ADR-30 — Tiered ingest pipeline — 🟡
- **Decision:** one pipeline / three tiers via the `ingest` MCP; agent fills two LLM holes
  and writes through the gated obsidian MCP.
- **Evidence:** all six scripts + `ingest_mcp.py` wired in `memoria-librarian/config.yaml`;
  per-field best-source merge with provenance; coherence gatekeeper + `degraded` flag;
  sweeps cron.
- **Gap:** (1) full-text **fallback chain shortened** (only PMC + local-PDF→pymupdf4llm;
  ADR's S2ORC→CORE→Unpaywall→OCR left as follow-ups); (2) **PDF parsing not
  subprocess/`rlimit`-sandboxed** (ADR-mandated MuPDF-CVE control missing).

### ADR-31 — Native obsidian MCP over HTTP — ✅
- **Decision:** point every profile at the plugin's native MCP over loopback HTTP; drop
  uvx `mcp-obsidian`; hard-deny `command_execute`/`vault_delete`/`vault_move`.
- **Evidence:** all 7 `config.yaml`s carry the native-HTTP `obsidian` block;
  `policy_hook.py` `DENY_OBSIDIAN` enforced + self-tested.
- **Gap:** none.

### ADR-32 — External access over MCP; deterministic tools self-hosted — ✅
- **Decision:** capability reaches the agent only over MCP; `code_execution`/`web`
  disabled fleet-wide; `terminal` only Coder + Linter; retraction self-hosted in
  `verify_mcp.py`.
- **Evidence:** Librarian wires ingest + paper_search + pyzotero; Verifier wires `verify`
  MCP (3-source retraction cascade + cron); only Coder/Linter keep `terminal`; `web`
  disabled everywhere.
- **Gap:** none material (the Retraction-Watch CSV is populated by the `--refresh` cron at
  deploy; degrades to live sources without it).

### ADR-33 — BERTopic cluster MCP for the Mapper — ❌
- **Decision:** `cluster_mcp.py` (BERTopic behind ~3 read-only tools); wire into the
  Mapper; retire the dead `scikit-learn`/`umap-learn` grants; update `cluster-mapping` to
  call the MCP.
- **Evidence:** **none landed** — no `cluster_mcp.py`; `mapper.yaml` still grants
  `scikit-learn` + `umap-learn`; `cluster-mapping` SKILL/methods/SOUL still instruct the
  non-runnable scikit/UMAP path; no BERTopic/sentence-transformers/hdbscan in any
  requirements.
- **Gap:** everything — the Mapper's clustering is granted-but-non-functional, the exact
  problem the ADR exists to fix. (ADR's own "implementation is a tracked follow-up" is
  still outstanding.)

---

## Cross-references

- **Redesign overlap:** the [four-layer redesign](memoria-redesign.md) would supersede
  ADR-01/04 and rework MOCs (ADR-19 → "hub") and clustering posture (ADR-33 builds on it).
  Don't invest in ADR-19's Tier-1-as-specified if the redesign is adopted.
- **Tracked-deferred:** ADR-11, ADR-20 (CiteME + disposition/cost), ADR-29 (L2b),
  ADR-15, ADR-30 (fallback chain) are flagged in the
  [v0.1 release plan](../releasing/v0.1/release-plan-v0.1.md) and/or the ADRs themselves.
- **AGENTS.md note:** "generated reports go in `_reports/`, never in `project/`." This
  file is a *durable* analysis (it informs ADRs + the redesign), not gitignored scratch —
  hence its home here. If that distinction should be explicit, AGENTS.md's work-routing
  could carve out "durable analyses → `docs/design/`".
