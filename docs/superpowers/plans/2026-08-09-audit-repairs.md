# Consistency-Audit Repairs Implementation Plan

> **Superseded. Do not execute without re-verifying.**
> The 2026-08-10 re-run of the same audit over the same corpus
> ([spec](../specs/2026-08-10-full-corpus-consistency-audit.md)) confirmed 42
> defects, of which only 15 overlap the 41 this plan derives from. It also
> refuted **Task 25** (`fulltext.yaml`'s `category`) — and a third run on
> 2026-08-11 overturned that refutation, establishing by `git log -S` that
> `c5af51be` renamed `fulltext` to `fulltexts` throughout `folders.yaml` and
> left the type schema behind. Task 25 stands. Every task's premise step exists
> for exactly this reason — run it.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the 29 evidence-settled repairs from the 2026-08-09 consistency audit of memoria-vault at HEAD `217fc358`, batched one pull request per section.

**Architecture:** Five batches, each an isolated worktree → branch → PR passing `python scripts/verify` on its own. Docs conform to code per the trust order (schema → tests → code → docs). The one code fix carries a test written first. Batches land sequentially; each re-verifies its premises against current `main` before editing, because earlier merges move the tree.

**Tech Stack:** Markdown docs (Diátaxis, Just-the-Docs), YAML schemas, Python 3.12 (pytest, ruff), the repo's gates in `scripts/checks/`.

## Global Constraints

- Each batch: `git worktree add .claude/worktrees/<name> -b wip/<name> origin/main` from the main checkout, then `EnterWorktree`. Never edit the caller's checkout.
- Stage explicit paths only — `git add -A` is hook-blocked; the index is shared per checkout.
- `python scripts/verify` must print `verify: OK` before any completion claim; on failure fix or revert, never adjust the gate.
- One PR per batch against `main`. Open it; merging is the owner's move.
- Docs conventions bind every edit: relative links by Pages route inside `docs/`, GitHub blob URLs for unpublished targets, never relative-link into `src/`, American spelling, cspell additions to `project-words.txt` (lowercase, sorted).
- `checked` never means approved/verified/trusted — `checked_terminology_gate` fails the build on it.
- Every task's first step verifies its own premise against the tree as it stands. A task whose premise has moved is skipped and reported, not forced.

## Not in this plan

**Twelve `owner-call` findings** are excluded by the skill: the audit framed their options and recommended one, but choosing is the owner's. They go to a `/grill-with-docs` decision pass, and each chosen option returns as a `direct-fix` for a later batch.

| Finding | The decision |
|---|---|
| `linter.md` + `detectors.py` (**HIGH**) | `fama-exposure` reads undeclared frontmatter. Schema-faithful bool, or add `superseded_by` for the successor pointer the design record promises? |
| `glossary.md` | Four names for the attention artifact. Rule "prompt" as the attention sense, or make "attention item" canonical? |
| `tutorials/03-connect-notes.md` | Tutorial claim has no real source. Promote 02's local capture to a main step, or re-domain the arc onto the corpus (cascades through 04, 05, 07)? |
| `export-a-draft.md` | Bare `pandoc` breaks the CSL prerequisite. Scope the docs to the direct-Pandoc routes, or change the export path? |
| `design-system.md` + `visual-discipline.md` | **One decision, two pages** — what the callout-palette rationale anchors to, since the promised content exists nowhere. |
| `okf-and-portability.md` | **One decision, three pages** — which page owns the nested-bundle passage. |
| `daily-glance.md` | **One decision, two pages** — which keeps the board-state rationale. |
| `consistency-audit-brief.md` | Narrow the `design-history/` exclusion to the frozen chapters, or leave it blanket? |
| `cross-tool-parity.md` | Kilo has no entry. Needs facts only the owner holds — its config is gitignored. |
| `set-up-zotero.md` | Version pin and menu path unverifiable offline. Check upstream, or de-specify? |
| `_sources.yml` | Delete the unread ledger, or repair it? |

**Two `graduate` findings** contribute their mechanical repair here (Tasks 12 and 17) and hold back their gate spec — a new checker is the decision AGENTS.md ranks last, and belongs in the same decision pass: a seed-inventory gate, and an engine-API roster gate.

---

## Batch 1 — How-to guides (`wip/audit-howto`)

Five guides whose commands cannot work as written. Highest reader consequence.

### Task 1: Create the batch worktree

- [ ] **Step 1:** From the main checkout: `git worktree add .claude/worktrees/audit-howto -b wip/audit-howto origin/main`
- [ ] **Step 2:** `EnterWorktree(path: ".claude/worktrees/audit-howto")`
- [ ] **Step 3:** Confirm clean: `git status --porcelain` → empty.

### Task 2: `inspect-session-logs.md` — vault-local invocation

**Files:** Modify: `docs/how-to-guides/operate/inspect-session-logs.md:59,63`

- [ ] **Step 1 (premise):** `grep -n "src/memoria_vault\|python3" docs/how-to-guides/operate/inspect-session-logs.md` → line 63 invokes by repo source path.
- [ ] **Step 2:** Line 63 → `./.memoria/.venv/bin/python -m memoria_vault.runtime.sweeps.linter.session_summary --vault .`
- [ ] **Step 3:** Line 59 → name the module, not the repo file: "Run `memoria_vault.runtime.sweeps.linter.session_summary` when you need them:"
- [ ] **Step 4:** Add the Windows note the siblings carry: "On Windows, replace `./.memoria/.venv/bin/python` with `.\.memoria\.venv\Scripts\python.exe`."

### Task 3: `run-a-retraction-sweep.md` — vault-local interpreter

**Files:** Modify: `docs/how-to-guides/operate/run-a-retraction-sweep.md:26,34`

- [ ] **Step 1 (premise):** `grep -n "python3" docs/how-to-guides/operate/run-a-retraction-sweep.md` → bare `python3` at 26 and 34.
- [ ] **Step 2:** Replace both with `./.memoria/.venv/bin/python`, flags unchanged (`--refresh`; `--sweep --vault .`). Add the lead-in `run-the-linter.md:25` carries ("From the vault root, use the interpreter installed with the vault:") and its Windows line.
- [ ] **Step 3:** Leave line 51's `superseded_by` phrasing alone — it depends on the HIGH owner-call and is not this plan's to touch.

### Task 4: `run-the-linter.md` — the unattended surface

**Files:** Modify: `docs/how-to-guides/operate/run-the-linter.md:16`

- [ ] **Step 1 (premise):** `grep -n "workspace check" docs/how-to-guides/operate/run-the-linter.md` → line 16 names it as the unattended Linter.
- [ ] **Step 2:** Replace with the page's own step-1 surface wired through cron/systemd: `<vault>/.memoria/.venv/bin/python -m memoria_vault.runtime.sweeps.linter.detectors --vault <vault> --json` (documented at `linter.md:56`, already used at `run-the-weekly-review.md:53`). `workspace check` runs the integrity sweep and never reaches the Linter — do not present it as a Linter surface.

### Task 5: `set-up-obsidian.md` — the plugin has no URL/token fields

**Files:** Modify: `docs/how-to-guides/setup/set-up-obsidian.md` (step 4); `docs/reference/evidence-and-integrations/integrations.md:103`

- [ ] **Step 1 (premise):** `grep -n "token\|URL" docs/how-to-guides/setup/set-up-obsidian.md` → step 4 instructs entering a server URL and token.
- [ ] **Step 2:** Rewrite step 4 to the settings that exist: turn on **Enable collection** (and set **Engine command** if the CLI is not on Obsidian's PATH — e.g. `wsl memoria` on WSL2) only when adapter actions or empirical event recording are wanted; the plugin obtains port and per-boot token itself via `memoria handshake --vault <path> --spawn --json` — there is nothing to paste. Mirror the correct wording at `integrations.md:91`.
- [ ] **Step 3:** Fix the same stale model at `integrations.md:103` in this commit.

### Task 6: `safe-mode.md` — non-circular export fallback

**Files:** Modify: `docs/how-to-guides/troubleshooting/safe-mode.md` (step 3 example, lines 44-45)

- [ ] **Step 1 (premise):** `grep -n "format\|pandoc" docs/how-to-guides/troubleshooting/safe-mode.md` → the fallback example uses a Pandoc-requiring format.
- [ ] **Step 2:** Step-3 example →
```bash
memoria project export --workspace <workspace> projects/<project>/project.md \
  --format markdown --output /tmp/output.md
```
- [ ] **Step 3:** Rewrite lines 44-45 so the missing-Pandoc branch routes to markdown, keeping direct Pandoc only for formats that need it. (Markdown is the CLI default per `cli.py:483` and the only prerequisite-free format per `export-a-draft.md:37`.)

### Task 7: Close Batch 1

- [ ] **Step 1:** `python scripts/verify` → `verify: OK`.
- [ ] **Step 2:** Stage explicit paths; commit `docs: how-to repairs from the 2026-08-09 consistency audit`.
- [ ] **Step 3:** Push, open the PR (body lists task numbers and finding titles), report CI. Owner merges.
- [ ] **Step 4:** After merge, from the main checkout: `git worktree remove .claude/worktrees/audit-howto`, `git worktree prune`, delete the branch.

---

## Batch 2 — Reference quadrant (`wip/audit-reference`)

### Task 8: Create worktree `audit-reference` from fresh `origin/main`

- [ ] As Task 1, name changed.

### Task 9: `frontmatter.md` + `linter.md` — "untyped" inversion

**Files:** Modify: `docs/reference/data-model/frontmatter.md:209`; `docs/reference/analysis-and-surfaces/linter.md:68`

- [ ] **Step 1 (premise):** `grep -n "untyped" docs/reference/data-model/frontmatter.md docs/reference/analysis-and-surfaces/linter.md`
- [ ] **Step 2:** `frontmatter.md:209` →
```
| Exemptions | `system/` infrastructure and vault-root navigation pages declare `type: system` for OKF conformance but have no per-type schema, so the hook exempts them by path. |
```
- [ ] **Step 3:** `linter.md:68`, final sentence →
```
Exempt by path: `system/` infrastructure, `inbox/` cards, project `outline.md`/`draft.md`, vault-root nav pages, and paths outside the vault — these declare a `type` for OKF conformance but have no per-type schema.
```

### Task 10: `telemetry.md` — runs.jsonl writer and schema

**Files:** Modify: `docs/reference/pipelines-and-io/telemetry.md:38,91-102`

- [ ] **Step 1 (premise):** `sed -n '89,102p' docs/reference/pipelines-and-io/telemetry.md`, compared against `src/memoria_vault/runtime/eval/eval_score.py:217-233`.
- [ ] **Step 2:** Line 91 → attribute to the scorer, matching the page's own inventory row at line 40: "One row per scoring run (`python3 -m memoria_vault.runtime.eval.eval_score --from-json`; `memoria eval run` only dispatches). Exact metric definitions: [Vault eval](../analysis-and-surfaces/vault-eval.md)."
- [ ] **Step 3:** Lines 94-102 → replace the example with the shape `eval_score.py:217-233` emits (field set copied from there, values illustrative; pinned by `tests/test_eval_score.py:242-257`).
- [ ] **Step 4:** Line 38 → mark `lint-findings.jsonl` as written only under the detector's `--jsonl-out` flag, not standing per-run output.

### Task 11: `integrations.md` — pane-era adapter rows

**Files:** Modify: `docs/reference/evidence-and-integrations/integrations.md:104,106`

- [ ] **Step 1 (premise):** compare rows against `src/memoria_vault/product/workspace_seed/.obsidian/plugins/memoria-obsidian/main.js:41-46,85-160`.
- [ ] **Step 2:** Reads row: `GET /status` → `GET /v1/status`; keep `GET /attention` and `GET /concept?target=<path>`; add `GET /v1/views/attention` and `GET /v1/views/evidence-review`.
- [ ] **Step 3:** Commands row: add the five missing entries — open attention pane, open evidence review, Relate, fork canvas to scratch, graduate scratch canvas edges (names from `main.js:85,94,99,155,160`).

### Task 12: `on-disk-layout.md` — seed inventory repairs (mechanical half of a graduate finding)

**Files:** Modify: `docs/reference/system/on-disk-layout.md:41-46,63-65,140-166,212`

- [ ] **Step 1 (premise):** `ls src/memoria_vault/product/workspace_seed/.memoria/schemas/` and `grep -n "concept-types\|session-diary" docs/reference/system/on-disk-layout.md` → both absent from the page.
- [ ] **Step 2:** Tree at 63-65 — insert the registry, redrawing branch characters:
```
├── schemas/                 single source for schema contracts
│   ├── types/<type>.yaml    per-type Concept schemas
│   ├── concept-types.yaml   required Concept-type registry; every type schema names a member
│   └── folders.yaml         type→folder homes, staging roots, quarantine, skeleton
```
- [ ] **Step 3:** Packaged Seed Inventory — add rows for `concept-types.yaml` and `system/templates/session-diary.md` (seeded by `cli.py:65`); add `session-diary.md` to the vault tree at 41-46.
- [ ] **Step 4:** Line 212 → type→folder homes live in `folders.yaml`, not "in table form" on Document types.
- [ ] **Step 5:** "Purpose and lifecycle" rows 162-166 → state the preserve-on-repair lifecycle for the two view-preference paths lacking it, matching their seven siblings.
- [ ] **Step 6:** Leave line 73 (`.memoria/code-runs/` gitignored) alone — the seed-side counterpart is an owner-call.
- [ ] **Step 7:** Do **not** build the seed-inventory gate here; that is the finding's `graduate` deliverable and awaits a decision.

### Task 13: `read-api.md` — three missing roster rows (mechanical half of a graduate finding)

**Files:** Modify: `docs/reference/commands-and-transports/read-api.md:17-50`

- [ ] **Step 1 (premise):** compare the module's public functions against the page's roster tables → three absent, including `evidence_review_queue`.
- [ ] **Step 2:** Add three rows beside their siblings, contract prose from docstrings, adding no completeness sentence. First row:
```
| `evidence_review_queue(workspace, routing_type="", project="", min_age_days=0, batch=10, read_scope=None)` | Reads the engine-direct evidence-review queue: raw rows, never cards — what the CLI front and the triage cockpit read. `batch=0` means every row. |
```
- [ ] **Step 3:** Do **not** build the roster gate here; it awaits a decision.

### Task 14: Reference one-liners

**Files:** Modify: `docs/reference/README.md:103`; `docs/reference/analysis-and-surfaces/retrieval-and-analysis-methods.md:25`; `docs/reference/commands-and-transports/prompt-operations.md:71`; `docs/reference/control-and-policy/empirical-events.md:92`; `docs/reference/control-and-policy/policy-audit-log.md:25`

- [ ] **Step 1 (premises):** grep each cited line; confirm the defect text is present.
- [ ] **Step 2:** `README.md:103` →
```
| [Zotero plugins](evidence-and-integrations/zotero-plugins.md) | Optional Zotero add-ons (Better BibTeX, RTF/ODF Scan) behind the live-citation export routes | Manual |
```
- [ ] **Step 3:** `retrieval-and-analysis-methods.md:25` → replace the dead `verify-check-citation` clause with:
```
**Used by:** Linter structural detectors, `integrity-citation-survival-check`
and `integrity-claim-quote-check`, schema validation, and ingest
type-detection dispatch.
```
- [ ] **Step 4:** `prompt-operations.md:71` → drop the two-value enumeration clause; the roster table at :32-42 is the single authority on `output_target`. Do not touch :93-96.
- [ ] **Step 5:** `empirical-events.md:92` → first cell `resolve-evidence-review` → `resolve-evidence`. Do not touch the code.
- [ ] **Step 6:** `policy-audit-log.md:25` →
```
| `action` | string | One of the eight actions defined in the [Action Vocabulary](policy-mcp.md#action-vocabulary) (`read` / `write` / `append` / `move` / `delete` / `mkdir` / `auto_fix` / `report`). |
```

### Task 15: SRD glossary entries (the `record` finding)

**Files:** Modify: `docs/reference/data-model/glossary.md`; `.vale/styles/config/vocabularies/Memoria/accept.txt`

- [ ] **Step 1 (premise):** `grep -n "^### SRD" docs/reference/data-model/glossary.md` → absent, while `work-the-evidence-set-review-queue.md` uses it load-bearing.
- [ ] **Step 2:** Add **SRD** — the software-requirements document derived from a project's checked slice; generation and contract are Planned, marked in the existing style of the `autoresearch` entry. Add **SRD gap** — an open `srd-gap` attention card riding the evidence-review queue as a read-only row carrying no evidence set.
- [ ] **Step 3 (Vale, same PR per `.vale.ini`):** run the admission test — append `SRD` to `accept.txt`, `pre-commit run vale --hook-stage manual --all-files`, keep only if clean; revert if it errors.
- [ ] **Step 4:** Do **not** add the attention-sense "Prompt" entry — that is an owner-call on the same file. If the decision pass has already settled it, that edit belongs to its own batch.

### Task 16: Close Batch 2

- [ ] As Task 7; commit `docs: reference-quadrant repairs from the 2026-08-09 consistency audit`.

---

## Batch 3 — Explanation quadrant (`wip/audit-explanation`)

### Task 17: Create worktree `audit-explanation` from fresh `origin/main`

- [ ] As Task 1.

### Task 18: `vault.md` — archive state correction

**Files:** Modify: `docs/explanation/architecture/vault.md:105-109`

- [ ] **Step 1 (premise):** `sed -n '105,109p'` → "runtime state" claim present.
- [ ] **Step 2:** Replace 107-109 with:
```
Archive is a state, not a folder move — but a Concept's and a Work's live in
different places. A Concept's archive state is the schema-declared frontmatter
`archived: bool` (see [Frontmatter fields](../../reference/data-model/frontmatter.md));
a catalog Work's archive/retraction standing is the journaled SQLite `standing`
(`current`, `archived`, `retracted`, `superseded`). Neither is `check_status`:
that is the separate read-state verdict.
```
(Code anchor: `grounding/__init__.py:2044-2048` separates the two.)

### Task 19: Status-banner and token repairs

**Files:** Modify: `docs/explanation/rationale/foundations/design-principles.md:91-93`; `docs/explanation/rationale/foundations/what-memoria-is.md:46`; `docs/explanation/knowledge/consequence-propagation.md:92-94`

- [ ] **Step 1 (premises):** grep each line for the quoted stale text.
- [ ] **Step 2:** `design-principles.md:91-93` → replace the "not yet shipped" banner with `> **Shipped:** Typed consequence propagation and blast-radius marking.` (Principle prose at :89 is accurate at HEAD.)
- [ ] **Step 3:** `what-memoria-is.md:46` →
```
> **Planned beta.1:** the copyable bundle boundary — folder-copy export and the
> foreign-bundle import path — plus the standard-Markdown links discipline for
> OKF-facing relationships. Core OKF v0.2 conformance over the whole tree ships
> today ([OKF compliance contract](../../../reference/data-model/okf-compliance.md)).
```
- [ ] **Step 4:** `consequence-propagation.md:92-94` → replace only the colliding token: "...its blast radius is computed and affected nodes are marked — `stale`, carrying the typed consequence that reached them, needing re-confirmation — so the knowledge base is always current...". Do not add `under-grounded` to the glossary.

### Task 20: Link and ordering repairs

**Files:** Modify: `docs/explanation/execution/control-plane/states.md:127`; `docs/explanation/rationale/boundaries/why-deterministic-methods.md:60`; `docs/explanation/architecture/session-logging.md:99`; the third routing page (found at execution); six Knowledge-section frontmatters

- [ ] **Step 1:** `states.md:127` label → `- Request states and the control that moves each: [Control plane reference](../../../reference/control-and-policy/control-plane.md)`. Target unchanged.
- [ ] **Step 2:** `grep -rn "execution/operations.md" docs/explanation/` → three Related entries promising Linter/vocabulary behavior. Repoint all three at `docs/reference/analysis-and-surfaces/linter.md`, each in its page's existing relative-depth form.
- [ ] **Step 3:** Knowledge `nav_order` renumber — six one-line edits, target order = the section README's existing rows: knowledge-cycle 2→3, note-body-structure 3→4, promotion-and-gated-zones 4→5, vocabulary-discipline 5→6, common-pitfalls 6→7, consequence-propagation 7→8. `what-checked-means.md` stays 2. No README change.

### Task 21: Close Batch 3

- [ ] As Task 7; commit `docs: explanation-quadrant repairs from the 2026-08-09 consistency audit`.

---

## Batch 4 — Policy and root files (`wip/audit-policy`)

### Task 22: Create worktree `audit-policy`; apply four repairs

**Files:** Modify: `AGENTS.md:74-77`; `CHANGELOG.md:9`; `README.md:137,140`; `docs/agents/triage-labels.md:5-15`

- [ ] **Step 1 (premises):** grep each site for the quoted text.
- [ ] **Step 2:** `AGENTS.md:74-77` — replace the retired-tracker clause with: "No GitHub Projects status fields — the state-role labels in \"Issue conventions\" below carry the triage-time readiness verdict, and assignee and blockers are read live. No release parent-issue ceremony." Keep the bullet structure.
- [ ] **Step 3:** `CHANGELOG.md:9` → "Memoria is in **v0.1 alpha development — there is no formal tagged release yet.**" Lines 10 and 12-14 need no change.
- [ ] **Step 4:** `README.md:137,140` → `~/memoria-vault/test-vault/vault` → `~/memoria-vault/test-vault` (twice).
- [ ] **Step 5:** `triage-labels.md` — delete line 15 (the install-time "edit the vocabulary" instruction, which AGENTS.md's closed vocabulary overrides); collapse the 5-11 table to two columns (label / meaning), since the mapping column duplicates its neighbour verbatim.
- [ ] **Step 6:** Leave `AGENTS.md:70` and the brief's `design-history/` exclusion alone — that pair is an owner-call.

### Task 23: Close Batch 4

- [ ] As Task 7; commit `agents+root: policy-file repairs from the 2026-08-09 consistency audit`.

---

## Batch 5 — Seed and code (`wip/audit-seed`)

### Task 24: Create worktree `audit-seed` from fresh `origin/main`

- [ ] As Task 1.

### Task 25: `fulltext.yaml` category, test first

**Files:** Modify: `tests/test_schemas.py:229`; `src/memoria_vault/product/workspace_seed/.memoria/schemas/types/fulltext.yaml:2`

- [ ] **Step 1 (premise):** `grep -n "category" src/memoria_vault/product/workspace_seed/.memoria/schemas/types/*.yaml` → only `fulltext.yaml` disagrees with its `folders.yaml` home.
- [ ] **Step 2 (tighten the test first):** `tests/test_schemas.py:229`: `assert home.startswith(types[name]["category"])` → `assert home == types[name]["category"]`
- [ ] **Step 3:** Run `python3 -m pytest tests/test_schemas.py -q` → **FAILS** on fulltext. The prefix match is what admitted the drift; equality rejects it.
- [ ] **Step 4:** `fulltext.yaml:2` → `category: fulltexts`.
- [ ] **Step 5:** Re-run → PASS. Commit test and fix together.

### Task 26: Seeded vocabulary note

**Files:** Modify: `src/memoria_vault/product/workspace_seed/system/vocabulary.md:28-29`

- [ ] **Step 1 (premise):** `sed -n '28,29p'` → routes taxonomies to a `_enrichment` note-frontmatter namespace; `grep -rn "_enrichment" src/memoria_vault/product/workspace_seed/.memoria/schemas/` → absent, and closed validation would reject it.
- [ ] **Step 2:** Replace, keeping the true negative half:
```
Reference taxonomies (MeSH, ACM CCS, OpenAlex fields-of-study) are **not** here.
Provider-supplied taxonomy terms that Memoria does ingest land on catalog Work
rows as enrichment graph edges — browse them with `memoria explore`, not in
note frontmatter.
```
- [ ] **Step 3:** Verify the final clause against the surface `read_explore` documents in `docs/reference/commands-and-transports/read-api.md`; if `memoria explore` overstates what ships, name the surface that page names instead.

### Task 27: Close Batch 5

- [ ] As Task 7; commit `seed: category repair and vocabulary-note correction from the 2026-08-09 consistency audit`.

---

## Self-Review

- [x] **Coverage:** 29 repairs → Tasks 2-6 (5 how-to), 9-15 (12 reference incl. the `record`), 18-20 (10 explanation), 22 (4 policy/root), 25-26 (2 seed). Twelve `owner-call` findings and two gate specs are listed under "Not in this plan" with their decisions stated.
- [x] **Placeholders:** every replacement is quoted where the audit supplied it. Three tasks depend on an execution-time read (Task 20's third routing page, Task 13's two remaining rows, Task 26's explore-surface check) and each names what to read and what the result must satisfy.
- [x] **Consistency:** the one code change (Task 25) writes its test first and fails before it passes; no task references a symbol another task was supposed to define.
