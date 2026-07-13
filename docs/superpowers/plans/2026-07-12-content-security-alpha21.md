# Content-security & provenance-integrity (alpha.21) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the three alpha.21 trust items the archive gap analysis surfaced: CS1 exfiltration neutralization (embeds/HTML/URLs in machine-written text can't beacon), CS3 out-of-band change witness (foreign edits to human files + restriction-key removal are detected), and `mc`-hash-binding (a verification label can't survive an edit to the text it vouches for).

**Architecture:** Three independent PRs. CS1 is pure text transformation (no
schema). `mc`-hash-binding uses a derived evidence-set column plus an immutable
binding ledger; CS3 uses a file-baseline table. The completed implementation is
schema v12. Each builds on existing seams — explicit machine/third-party field
boundaries in operations and knowledge flows, the final export-content choke,
the observe-edit sweep (`trusted_writer.observe_pi_edits_from_status`), and the
evidence-set store (`evidence_sets` table).

**Tech Stack:** Python 3 stdlib + SQLite (no new deps). Tests: pytest via `python scripts/verify`.

Spec: `docs/superpowers/specs/2026-07-12-beta.1-content-security.md` (CS1, CS3) + `docs/superpowers/specs/2026-07-12-archive-gap-analysis.md` gap #10 (`mc`). Companion to `2026-07-12-foundation.md` (F1–F4); this is the "Related alpha.21 scope" it points at. Milestone `0.1.0-alpha.21`.

## Design decisions (made here; confirm at review)

1. **CS1 scope — neutralize every demonstrably machine/model/third-party prose region at apply, then neutralize assembled content again at export.** The audited apply boundaries are prompt-operation model output; source-digest and hub-suggestion title/description/topic/body fields; model-emitted note-candidate prose; generated outline reasoning; composed-draft copied headings/excerpts; promoted machine-draft passages; provider-derived enrichment attention/candidate prose; report-derived worklist prose; and code-owned edge-candidate prompt prose. Structural identifiers and paths remain unchanged state; rendered occurrences are trusted structure or code spans. The final export-content choke covers both argument and direct-draft exports. Generic mixed-author seams (`stage_concept`, `write_work_prompt`, and caller-owned record writers) remain byte-preserving because they cannot infer inline authorship; their code-owned callers neutralize provenance-known fields before invoking them. The work-title canary deliberately seeds the source title because title and description are live third-party fields, not deferred O2 work.
2. **`mc`-hash-binding — close only the fail-closed hash-survival slice of archive gap #10.** The first observed appearance of an evidence ID records its anchored block hash, or `null` when unresolved, in the immutable `evidence_bindings` ledger. Rebuilds use that ledger even after marker removal and reappearance, and verification compares current text with the preserved value. A missing stored hash or an unresolvable current block is itself a blocking verification finding. The larger DB-authoritative inversion (stop rebuilding evidence truth from markers) is explicitly deferred and remains unshipped; Tasks 5–7 do not claim to close all of gap #10.

## Global Constraints

- Correctness gate: `python scripts/verify` must pass before each PR.
- **Schema version:** the completed implementation uses `SCHEMA_VERSION = 12` and matching `PRAGMA user_version`. Pre-beta vaults are disposable and rebuild, so this plan requires no migration code. Future schema work must read the current value first and bump both values together.
- Test only against disposable vaults (`tests/helpers.init_cli_workspace` / `tmp_path`); never a personal vault.
- Every new test file MUST be registered in `tests/conftest.py` `TEST_LEVELS` (`"unit"` pure fns, `"runtime"` vault-mutating flows, `"contract"` CLI/API); `test_testing_levels.py` enforces this.
- Stage explicit paths only — never `git add -A`.
- Trust rule (spec): a safety defense may never be credited to the human noticing a marker; CS3 returns structured `route: ask` findings, **never blocks**, and creates no attention projection.
- PR boundaries: PR-CS1 after Task 4, PR-MC after Task 7, PR-CS3 after Task 12. PR titles: `feat(security): …` / `fix(verify): …` / `feat(integrity): …`.

---

## PR-CS1 · Exfiltration neutralization (no schema)

### Task 1: `neutralize_untrusted_markdown` helper

**Files:**
- Create: `src/memoria_vault/runtime/content_security.py`
- Test: `tests/test_content_security.py` (new — register `"runtime"` because Tasks 3–4 extend it with vault-mutating cases)

**Interfaces:**
- Consumes: nothing.
- Produces: `content_security.neutralize_untrusted_markdown(body: str) -> str` — escapes Markdown image/embed syntax, inerts raw HTML tags, wraps external URLs as non-clickable code spans, and leaves vault-internal `[[wikilinks]]` plus ordinary literal code spans/fences untouched. Pandoc raw-format attributes and fence headers are neutralized even when otherwise well formed; malformed or unclosed code candidates are treated as prose. Tasks 3–4 consume it.

- [x] **Step 1: Write the failing test**

```python
"""tests/test_content_security.py — CS1 neutralization."""

from memoria_vault.runtime.content_security import neutralize_untrusted_markdown


def test_image_embed_cannot_render():
    assert "![" not in neutralize_untrusted_markdown("![beacon](http://evil/x.png)")
    assert "![" not in neutralize_untrusted_markdown("![[remote.png]]")


def test_raw_html_is_inert():
    out = neutralize_untrusted_markdown('<img src="http://evil/x">hi<script>go()</script>')
    assert "<img" not in out and "<script" not in out
    assert "&lt;img" in out and "&lt;script" in out
    assert "hi" in out


def test_external_url_is_noninteractive_codespan():
    out = neutralize_untrusted_markdown("see [here](https://evil.example/x) now")
    assert "](https://evil.example/x)" not in out  # link syntax broken
    assert "`https://evil.example/x`" in out        # url preserved, non-clickable
    assert "here" in out
    bare = neutralize_untrusted_markdown("visit http://evil.example/y today")
    assert "`http://evil.example/y`" in bare


def test_vault_internals_and_code_untouched():
    src = "See [[notes/claim-1]] and `already code` and\n```\nhttp://x\n```\n"
    assert neutralize_untrusted_markdown(src) == src  # wikilinks + code spans/fences preserved
```

- [x] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_content_security.py -v`
Expected: FAIL — module does not exist.

Also add to `tests/conftest.py` `TEST_LEVELS` (alphabetical): `"test_content_security.py": "runtime",` (the file gains vault-mutating apply/export cases in Tasks 3–4).

- [x] **Step 3: Implement** — use a line scanner that preserves backtick and tilde fenced blocks plus variable-length inline code spans. Neutralize Markdown image/embed and link forms, raw HTML, and bare external URLs in every remaining segment. Choose a safe code-span delimiter and keep the transform idempotent so renderer plus final-write application is stable.

- [x] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_content_security.py -v`
If `test_image_embed_cannot_render` finds `![`, confirm `_IMG_RE` fired; the
replacement `\\` plus the surviving `[` yields `\[`, not `![`.

- [x] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/content_security.py tests/test_content_security.py tests/conftest.py
git commit -m "feat(security): neutralize_untrusted_markdown helper (CS1 embeds/HTML/URLs)"
```

**Current coverage:** `tests/test_content_security.py` covers inert images,
embeds, HTML, external URLs, raw-format directives, and literal-code handling.

### Task 2: Neutralize the final content at export (draft + argument export)

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py` (`write_project_export` and the renderer return contracts)
- Test: `tests/test_draft_verification.py` and `tests/test_project_knowledge.py` (extend existing draft and argument export coverage)

**Interfaces:**
- Consumes: `content_security.neutralize_untrusted_markdown` (Task 1).
- Produces: exported markdown from both renderers is neutralized at the shared `content = str(rendered["content"])` choke before it lands on disk or reaches Pandoc. Renderer-return tests also prove direct consumers receive neutralized content.

- [x] **Step 1: Read** `_render_draft_export_body`, `render_project_draft_export_markdown`, `render_project_export_markdown`, and `write_project_export` fully; confirm which return values are public and that `content = str(rendered["content"])` is the final disk/Pandoc choke.

- [x] **Step 2: Write the failing test** (append to `tests/test_draft_verification.py`; reuse its existing draft-export fixture — copy the setup from `test_verified_source_backed_draft_exports_without_internal_markers`):

```python
def test_export_neutralizes_embedded_beacon(tmp_path, capsys):
    # ... reuse the verified-draft fixture, but plant a beacon in a drafted passage ...
    # draft body contains: '![x](http://beacon.example/p.png)'
    # run the export operation (write_project_export / project export --draft)
    exported = ...  # the returned/loaded exported content
    assert "![x](http://beacon.example" not in exported
    assert "`http://beacon.example/p.png`" in exported or "\\[x]" in exported
```
Fill concretely from the existing fixture (no `...` in the final test).

- [x] **Step 3: Implement** — import `neutralize_untrusted_markdown`; neutralize each renderer's returned `content` so direct consumers are safe, and neutralize `str(rendered["content"])` again at `write_project_export` as the final default-deny choke. The helper is idempotent, so this defense-in-depth does not alter already-neutralized content.

- [x] **Step 4: Verify** — covered by [Current verification](#current-verification).

- [x] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/knowledge.py tests/test_draft_verification.py
git commit -m "fix(security): neutralize exported draft/argument content (CS1 export side)"
```

**Current coverage:** draft and argument renderer tests cover both returned content
and the final file-output boundary.

### Task 3: Neutralize every current machine/third-party apply region

**Files:**
- Modify: `src/memoria_vault/runtime/operations.py`, `knowledge.py`, `enrichment.py`, `trusted_writer.py`, and `subsystems/lib/worklists.py`
- Test: `tests/test_operations.py`, `test_knowledge.py`, `test_draft_verification.py`, `test_draft_writeback.py`, `test_project_knowledge.py`, `test_source_enrichment.py`, `test_worklists.py`, and `test_trusted_writer.py`

**Interfaces:**
- Consumes: `neutralize_untrusted_markdown`.
- Produces: known-untrusted prose is neutralized immediately before a code-owned Markdown insertion: prompt reports; digest/hub suggestions; candidate notes; outline reasoning; composed drafts; promoted passages; provider attention/candidates; worklists; and extracted-edge prompts. Human-only parameters, structural IDs, and generic mixed-author calls remain untouched.

- [x] **Step 1: Read** every Markdown write/stage path and classify its dynamic insertions as provenance-known prose, trusted structure, safe-by-construction values, or caller-owned mixed-author content.

- [x] **Step 2: Write failing tests** — cover every provenance-known apply class with the smallest existing fixture. For the digest, seed the source **title**, description, model body, and hub topic with distinct beacons. Include a mixed-author `stage_concept` characterization proving generic caller content is not rewritten.

- [x] **Step 3: Implement** — neutralize only provenance-known prose before formatting/staging. Preserve raw model output hashes in journal provenance; hash what the model returned, not the transformed rendering. Do not wrap generic mixed-author writers globally.

- [x] **Step 4: Verify** — covered by [Current verification](#current-verification).

- [x] **Step 5: Commit**

```bash
git add <explicit Task 3 runtime and test paths>
git commit -m "fix(security): neutralize machine and third-party text at apply (CS1)"
```

**Current coverage:** the affected runtime tests cover every provenance-known
apply path, raw model hashes, and byte-preserving mixed-author seams.

### Task 4: Canary drill + PR-CS1

**Files:**
- Test: `tests/test_content_security.py` (add the end-to-end canary)
- Current truth: `docs/reference/commands-and-transports/system-actions-operations.md`, `prompt-operations.md`, `docs/reference/pipelines-and-io/export.md`, and `docs/reference/control-and-policy/worklists.md`

- [x] **Step 1: Write the canary test** — seed a source **work title** (plus description/body) with `![x](http://beacon/p)`, `<script>`, and bare `http://beacon/y`; assert no live payload survives either the apply-written digest or a project export that cites it. This title canary is the regression proof that third-party metadata is in CS1 scope. Concrete fixture, no placeholders.

**Current coverage:** `test_work_title_canary_is_inert_at_apply_and_export`
covers capture through verified draft export with one seeded third-party title.

- [x] **Step 2: Gate + local handoff** — run the gate and commit current-truth docs. Do not push or open the PR in a session that lacks that authority.

```bash
python scripts/verify
git add tests/test_content_security.py
git commit -m "test(security): CS1 canary — seeded beacon survives neither apply nor export"
# Create this PR only in a session authorized to push/open PRs. This execution
# stops after local commits and verification.
gh pr create --title "feat(security): neutralize untrusted apply and export content (CS1)" --body "Part of alpha.21 content-security CS1. Neutralizes every current machine/model/third-party prose region at its apply boundary, including source title/description, and neutralizes final argument/draft export content again. Generic human writes remain untouched."
```

**Current verification:** See [Current verification](#current-verification). No
branch is pushed or PR opened by this plan.

---

## PR-MC · Evidence block-text-hash binding (schema +1)

### Task 5: `block_text_sha256` column on `evidence_sets`

**Files:**
- Modify: `src/memoria_vault/runtime/schema.sql` (`evidence_sets` ~:326; bump `PRAGMA user_version`), `src/memoria_vault/runtime/state.py` (`SCHEMA_VERSION`)
- Test: `tests/test_evidence_sets.py` (extend) or a new `tests/test_mc_hash_binding.py` (`runtime`)

**Interfaces:**
- Consumes: current `SCHEMA_VERSION` (read it first).
- Produces: `evidence_sets` has a nullable `block_text_sha256 TEXT` column; schema at the next version. Task 6 populates it, Task 7 reads it.

- [x] **Step 1: Write the failing test**

```python
"""tests/test_mc_hash_binding.py — evidence label bound to block text."""

from memoria_vault.runtime import state
from tests.helpers import init_cli_workspace


def test_evidence_sets_has_block_text_sha256(tmp_path, capsys):
    vault = init_cli_workspace(tmp_path, capsys)
    with state.connect(vault) as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(evidence_sets)")}
    assert "block_text_sha256" in cols
```
Register `"test_mc_hash_binding.py": "runtime"` in `tests/conftest.py`.

- [x] **Step 2: Run** → FAIL (column absent).

- [x] **Step 3: Implement** — in `schema.sql`, add to the `evidence_sets` table (after `run_id`): `block_text_sha256 TEXT`. Read the current `SCHEMA_VERSION` (`rg -n '^SCHEMA_VERSION' state.py`), set both `state.SCHEMA_VERSION` and `schema.sql`'s final `PRAGMA user_version` to `current + 1`.

- [x] **Step 4: Verify** — covered by [Current verification](#current-verification).

- [x] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/schema.sql src/memoria_vault/runtime/state.py tests/test_mc_hash_binding.py tests/conftest.py
git commit -m "feat(verify): evidence_sets.block_text_sha256 column (schema bump)"
```

**Current coverage:** schema, package, query, and evidence-binding tests assert
the v12 contract.

### Task 6: Bind the block-text hash when rebuilding evidence rows

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` (`rebuild_evidence_sets_from_markers` ~:1530 and the row builder ~:1740; the block-ref anchor helper `_evidence_block_ref` ~:1811)
- Test: `tests/test_mc_hash_binding.py` (extend)

**Interfaces:**
- Consumes: Task 5's column; the block-anchor resolution (`^blk-<id>`) already used by the marker→row builder.
- Produces: each rebuilt active `evidence_sets` row carries the preserved
  `block_text_sha256` from immutable `evidence_bindings(id,
  block_text_sha256)`. A first-observed ID records `"sha256:" +
  sha256(<anchored block body text>)`, or `null` if unresolvable. Function
  `state._block_text_sha256(vault, block_ref) -> str | None` resolves the
  `path#^blk-id` to its block text and hashes it.

- [x] **Step 1: Read** `rebuild_evidence_sets_from_markers` (:1530) + the row-insert (:1740) + how a `block_ref` (`{rel}#^blk-{id}`) maps to the block's text in the file (the anchor scan around knowledge.py:1967 / :3182).

- [x] **Step 2: Write the failing test** — compose a draft with one fresh `%%ev%%` marker on an anchored paragraph; rebuild and assert the row binds to `"sha256:"+sha256` of the canonical block text (anchor and evidence marker excluded). Edit that paragraph on disk, rebuild, and assert the stored hash **does not change** while `_block_text_sha256(vault, block_ref)` now returns a different current hash. Remove the marker, rebuild, then reintroduce the same ID on changed text and assert the original binding remains.

- [x] **Step 3: Implement** — add `_block_text_sha256(vault, block_ref)` (resolve `path#^anchor` to its enclosing Markdown paragraph/block, remove the block anchor and `%%ev...%%` control marker, trim outer whitespace, and hash the remaining UTF-8 bytes with the `sha256:` prefix). In the same `replace_evidence_sets` transaction, insert first-observed values into `evidence_bindings` with `ON CONFLICT DO NOTHING`, then rebuild the active projection from that ledger. The ledger rejects update and delete, so an existing ID keeps its prior value, including `None`, across every marker rebuild and reappearance. Never refresh a binding from current file text.

- [x] **Step 4: Verify** — covered by [Current verification](#current-verification).

- [x] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/state.py tests/test_mc_hash_binding.py
git commit -m "feat(verify): bind evidence rows to their block-text hash"
```

**Current coverage:** evidence-binding regressions cover changed text, an
unbound first observation, and removal/reappearance of an evidence ID.

### Task 7: Verify demotes + refuses export on block-text drift

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py` (`verify_project_draft` ~:2061; the export-gate labels `_verification_finding_labels` ~:3069 / the refuse-export path `render_project_draft_export_markdown` ~:2445)
- Test: `tests/test_mc_hash_binding.py` + `tests/test_draft_verification.py` (extend)

**Interfaces:**
- Consumes: the stored `block_text_sha256` (Task 6).
- Produces: `verify_project_draft` emits `evidence-text-drift` when current text differs from the preserved binding and `evidence-text-unbound` when the stored binding is missing or the current block cannot resolve. Either finding makes verification fail and therefore refuses export through the existing verification gate. Draft export renders the same snapshot it verifies.

- [x] **Step 1: Write failing tests** — verify a clean draft (passes/exports); edit the anchored paragraph on disk; rebuild; re-verify and assert `evidence-text-drift` plus export refusal. Separately delete/unresolve the anchor and create a row with a missing stored binding; each must emit `evidence-text-unbound` and refuse export. These tests prove rebuild cannot bless an edit and fail-open null/unresolvable states are gone.

- [x] **Step 2: Run** → FAIL (no drift check today; edited text exports clean — the fail-open).

- [x] **Step 3: Implement** — in the verified draft-snapshot helper, immediately after loading evidence rows, recompute the hash from that snapshot and compare it with the preserved stored value **before** disposition logic. Missing/unresolvable values append `evidence-text-unbound`; unequal non-null values append `evidence-text-drift`. The export renderer consumes the retained verified snapshot rather than rereading `draft.md`. Continue using the existing `ok = not findings` and verified-export refusal contract rather than adding a parallel allowlist that could miss a new finding kind.

- [x] **Step 4: Verify** — covered by [Current verification](#current-verification).

- [x] **Step 5: Commit + local handoff**

```bash
git add src/memoria_vault/runtime/knowledge.py tests/test_mc_hash_binding.py tests/test_draft_verification.py
git commit -m "fix(verify): demote + refuse export when block text drifts from its evidence label"
# Create this PR only in a session authorized to push/open PRs. This execution
# stops after local commits and verification.
gh pr create --title "fix(verify): bind evidence labels to block-text hash (mc-hash-binding)" --body "Partial archive gap #10 hardening: fresh evidence IDs bind once to anchored block text; rebuild preserves the prior hash; verify refuses drift, missing bindings, and unresolvable blocks. DB-authoritative evidence truth remains deferred and unshipped."
```

**Current coverage:** draft verification and export regressions cover drift,
unbound claims, and rendering from the verified snapshot. See
[Current verification](#current-verification).

---

## PR-CS3 · Out-of-band change witness (schema +1)

### Task 8: `file_baseline` table

**Files:**
- Modify: `src/memoria_vault/runtime/schema.sql` (new table; bump `PRAGMA user_version`), `state.py` (`SCHEMA_VERSION`)
- Test: `tests/test_content_security.py` or `tests/test_trusted_writer.py` (extend)

**Interfaces:**
- Produces: table `file_baseline(subject_id TEXT PRIMARY KEY, human_sha256 TEXT, restriction_keys_json TEXT NOT NULL DEFAULT '[]', observed_at TEXT NOT NULL)`; `state.upsert_file_baseline(vault, subject_id, *, human_sha256, restriction_keys)` and `state.file_baseline(vault, subject_id) -> dict | None`. Tasks 9–11 use them.

- [x] **Step 1: Write the failing test** — `test_file_baseline_round_trips_hash_and_restriction_keys` asserts the table exists and the helpers round-trip a hash plus `["superseded"]`.

- [x] **Step 2: Run** → FAIL (`file_baseline` did not exist before the schema change).

- [x] **Step 3: Implement** — added `file_baseline` plus the `state` helpers. Together with the immutable evidence-binding ledger, the completed schema and `user_version` are v12.

- [x] **Step 4: Verify** — covered by [Current verification](#current-verification).

- [x] **Step 5: Commit** — the file-baseline implementation is included in the local alpha.21 candidate.

```bash
git add src/memoria_vault/runtime/schema.sql src/memoria_vault/runtime/state.py tests/*.py tests/conftest.py
git commit -m "feat(integrity): file_baseline table for the change witness (schema bump)"
```

### Task 9: Record baselines during the observe sweep

**Files:**
- Modify: `src/memoria_vault/runtime/trusted_writer.py` (`observe_pi_edits_from_status` ~:211; `observe_pi_edit` ~:140)
- Test: `tests/test_trusted_writer.py` (extend)

**Interfaces:**
- Consumes: `state.upsert_file_baseline` (Task 8); `_head_sha256` (:695); the shipped restriction field `superseded: true`. Recognition of `local-only: true` may be recorded as forward-compatible groundwork only; no local-only privacy enforcement is claimed in alpha.21.
- Produces: reconciliation seeds and reconciles `file_baseline` rows from a single file-byte snapshot of each eligible bundle file. It covers clean files independently of Git status; Git-status targets remain the direct-PI-edit observation path. A direct PI edit receives its baseline only after the observed snapshot survives staging and commit, so a later concurrent edit remains dirty for the next sweep. Helper `trusted_writer._restriction_keys(frontmatter) -> list[str]`.

- [x] **Step 1: Write the failing test** — `test_observe_pi_edits_from_status_records_file_baseline_restrictions` sweeps a `superseded: true` note and asserts its baseline hash and `["superseded"]` keys.

- [x] **Step 2: Run** → FAIL (`file_baseline(...)` returned `None`).

- [x] **Step 3: Implement** — `_restriction_keys` records true `superseded` and the data-only `local-only` groundwork. Reconciliation seeds clean valid bundle files and uses a single file-byte snapshot for both hash and restriction keys; observed direct edits retain a matching observed snapshot without introducing a `standing` field.

- [x] **Step 4: Verify** — covered by [Current verification](#current-verification).

- [x] **Step 5: Commit** — `feat(integrity): record file baselines during observe sweep`.

```bash
git add src/memoria_vault/runtime/trusted_writer.py tests/test_trusted_writer.py
git commit -m "feat(integrity): record per-file baseline hash + restriction keys on observe sweep"
```

### Task 10: Detect foreign edits to never-audited human files

**Files:**
- Modify: `src/memoria_vault/runtime/trusted_writer.py` (the sweep) or `src/memoria_vault/runtime/subsystems/integrity/linter/detectors_audit.py` (extend `vault_hash_drift` ~:80)
- Test: `tests/test_trusted_writer.py` / `tests/test_detectors.py`

**Interfaces:**
- Consumes: `file_baseline` (prior-run hash), `_head_sha256` / current disk hash.
- Produces: a `foreign-edit` finding when a file's current hash differs from its expected trusted hash — the current journaled `output_sha256` when one exists, otherwise `file_baseline.human_sha256` — surfaced as an `observed_external_edit` ask-route result, flag-not-block. Clean files receive a baseline on their first sweep; a mismatch with no journal record does not advance that baseline.

- [x] **Step 1: Write the failing test** — `test_observe_pi_edits_from_status_flags_out_of_band_edit_after_baseline` establishes a baseline, rewrites the note directly with no journal event, then asserts the flag-and-route finding names the file.

- [x] **Step 2: Run** → FAIL (`findings` was absent from the sweep result).

- [x] **Step 3: Implement** — the sweep compares the prior baseline with the current hash and `_known_current_hashes`; a mismatch with no journaled current hash emits a `foreign-edit` finding (`route: ask`) paired with the existing `observed_external_edit` event and leaves the baseline intact. A journal-backed current hash reconciles the baseline instead.

- [x] **Step 4: Verify** — covered by [Current verification](#current-verification).

- [x] **Step 5: Commit** — `feat(integrity): witness out-of-band edits to human files`.

```bash
git add src/memoria_vault/runtime/*.py tests/*.py
git commit -m "feat(integrity): witness out-of-band edits to human files (CS3)"
```

### Task 11: Detect restriction-key removal (fails-open today)

**Files:**
- Modify: `src/memoria_vault/runtime/trusted_writer.py` (the sweep)
- Test: `tests/test_content_security.py`

**Interfaces:**
- Consumes: `file_baseline.restriction_keys_json` (prior run), current frontmatter keys.
- Produces: a `restriction-key-removed` ask-route finding when a key present in the baseline is absent now (for example, `superseded: true` is deleted). It is flag-not-block, and a mismatch with no journal record does not advance the baseline. `local-only` recognition is detection groundwork only, not shipped privacy, retrieval, export, or egress enforcement.

- [x] **Step 1: Write the failing test** — `test_observe_sweep_flags_removed_superseded_restriction` baselines a `superseded: true` note, removes the key directly, and asserts the finding names both the file and `superseded`.

- [x] **Step 2: Run** → FAIL (the expected `restriction-key-removed` finding was absent).

- [x] **Step 3: Implement** — the sweep diffs stored and current restriction keys and emits one ask-route `restriction-key-removed` finding per removal with `subject_id` and `key`. It preserves the baseline until a journal-backed current hash reconciles it. Recognized `local-only` remains data-only groundwork, not alpha.21 privacy enforcement.

- [x] **Step 4: Verify** — covered by [Current verification](#current-verification).

- [x] **Step 5: Commit** — `feat(integrity): witness restriction-key removal`.

```bash
git add src/memoria_vault/runtime/trusted_writer.py tests/test_content_security.py
git commit -m "feat(integrity): witness restriction-key removal (superseded/local-only) (CS3)"
```

### Task 12: Operation result + PR-CS3

**Files:**
- Modify: confirm both new finding kinds return structured `route: ask` operation findings (`rg -n "observed_external_edit|finding" src/memoria_vault/runtime/`); do not create an attention projection.
- Test: `tests/test_worker_integrity_jobs.py` (extend — the sweep runs as an operation job)

- [x] **Step 1: Write the failing test** — `test_worker_observe_sweep_surfaces_change_witness_findings` runs `observe-pi-edits` twice through the worker and asserts the second result contains both `foreign-edit` and `restriction-key-removed` `route: ask` findings.

- [x] **Step 2: Implement** — the worker exposes the sweep's `finding_count` and structured `findings` in its operation result. It does not create an attention projection.

- [x] **Step 3: Gate + local handoff** — covered by [Current verification](#current-verification). This session has local integration authority only: no branch is pushed and no PR is opened.

```bash
python scripts/verify
git add src/memoria_vault/runtime/*.py tests/*.py
git commit -m "feat(integrity): return change-witness findings from the worker sweep"
gh pr create --title "feat(integrity): out-of-band change witness (CS3)" --body "alpha.21 content-security CS3 (spec 2026-07-12-beta.1-content-security.md). Adds a file_baseline table; the observe sweep witnesses out-of-band edits to human-class files and restriction-key removal (superseded/local-only), returning flag-not-block ask-route findings in the worker result. Pairs F2 journal-trust."
```

## Current verification

- [x] `python3 scripts/verify` → `verify: OK`: 500 passed, 9 skipped, 891
  deselected; pre-commit, static checks, and offline smoke are green.

---

## Security invariants confirmed

- [x] A clean, tracked bundle Concept receives its first `file_baseline` during an observe sweep; its first later direct edit produces an ask-route `foreign-edit` finding.
- [x] A journal-backed current hash reconciles an affected baseline, while a generic writer commit cannot bless a disk edit with no journal record; a direct restore to an older revision remains witnessable.
- [x] The observe sweep binds the baseline to the journaled snapshot, verifies the file before staging, and verifies the staged bytes before commit; a concurrent later edit remains dirty for a later sweep rather than becoming the baseline.
- [x] The first observed evidence ID keeps its hash-or-null binding across marker removal and reappearance; verification and export use one draft snapshot.
- [x] Untrusted Markdown escapes Pandoc raw-format directives (`{=html}`, `{=latex}`, and other format names) on well-formed inline code and fence openers while retaining ordinary literal code spans and fences. Malformed or unclosed candidates are treated as prose.

Focused regressions cover each invariant, including Pandoc rendering for raw HTML attributes. The full repository gate is the final authority for this plan.

---

## Self-review notes

- **Spec coverage:** CS1 → Tasks 1–4 (every current provenance-known machine/model/third-party apply field, including work title, plus final export). `mc`-hash-binding → Tasks 5–7 and intentionally closes only the fail-closed hash-survival slice of gap #10; DB authority remains deferred/unshipped. CS3 → Tasks 8–12 (both fail-open holes: foreign human-file edits + removal of shipped `superseded: true`; optional `local-only` recognition is groundwork only). CS2/CS4–CS8 are explicitly other packages (U3/O2/W2/X1/beta.2), not this plan.
- **Schema coordination:** the resulting schema is v12. Each schema task uses the next actual merged version rather than relying on a stale hard-coded number.
- **Placeholder scan:** the investigate-then-fill steps (Tasks 2, 3, 6, 7 test setups) each name the exact existing fixture to copy and forbid leaving `...`
- **Type consistency:** `neutralize_untrusted_markdown(str)->str`, `_block_text_sha256(vault, block_ref)->str|None`, `upsert_file_baseline(...)/file_baseline(...)`, `_restriction_keys(frontmatter)->list[str]`, and the `evidence_bindings` ledger are named consistently where consumed. Finding kinds `evidence-text-drift`, `evidence-text-unbound`, and `restriction-key-removed` are used consistently.
