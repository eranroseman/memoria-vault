# Content-security & provenance-integrity (alpha.21) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the three alpha.21 trust items the archive gap analysis surfaced: CS1 exfiltration neutralization (embeds/HTML/URLs in machine-written text can't beacon), CS3 out-of-band change witness (foreign edits to human files + restriction-key removal are detected), and `mc`-hash-binding (a verification label can't survive an edit to the text it vouches for).

**Architecture:** Three independent PRs. CS1 is pure text transformation (no schema). `mc`-hash-binding and CS3 each add one schema column/table and ride the next `SCHEMA_VERSION` bump. Each builds on existing seams — the machine-write path (`trusted_writer`), the export renderer (`knowledge.render_project_*_export`), the observe-edit sweep (`trusted_writer.observe_pi_edits_from_status`), and the evidence-set store (`evidence_sets` table).

**Tech Stack:** Python 3 stdlib + SQLite (no new deps). Tests: pytest via `python scripts/verify`.

Spec: `docs/superpowers/specs/2026-07-12-beta.1-content-security.md` (CS1, CS3) + `docs/superpowers/specs/2026-07-12-archive-gap-analysis.md` gap #10 (`mc`). Companion to `2026-07-12-foundation.md` (F1–F4); this is the "Related alpha.21 scope" it points at. Milestone `0.1.0-alpha.21`.

## Design decisions (made here; confirm at review)

1. **CS1 scope — neutralize at export (always) + at apply for demonstrably machine-compiled third-party text (digest bodies), not blanket over every machine write.** Blanket whole-body neutralization would corrupt legitimate human prose that flows through the machine writer (escaping a human's intended `<`, `![`, or URL). Authorship is file-granular in the code (no inline machine-span marker), so this plan neutralizes (a) the assembled *export* content — recipient-facing, always safe — and (b) *digest* bodies at apply (machine-compiled from source text). Broader apply-side neutralization of third-party metadata fields (source titles) rides O2 ingest (CS4/CS5), where the field boundaries are clean. The `neutralize_untrusted_markdown` helper is reusable by that later work.
2. **`mc`-hash-binding — bind the evidence label to a block-text hash and invalidate on mismatch, without yet inverting the file-authoritative rebuild to DB-authoritative.** The full "DB is authority, stop rebuilding from markers" inversion (gap #10) is larger and riskier; this plan adds `block_text_sha256` to `evidence_sets`, recomputes it at verify, and **refuses export / demotes** when a resolved block's current text hash ≠ the bound hash. That closes the fail-open (a label surviving edited text) with a small change; the authority inversion is noted as a follow-on.

## Global Constraints

- Correctness gate: `python scripts/verify` must pass before each PR.
- **Schema version:** current `SCHEMA_VERSION` is **8**; Foundation F1 targets **9**. Tasks that change `schema.sql` must **read the current `SCHEMA_VERSION` first** (`rg -n '^SCHEMA_VERSION' src/memoria_vault/runtime/state.py`) and bump to the next integer, editing `schema.sql`'s `PRAGMA user_version` to match; `state._init` already accepts `{0, SCHEMA_VERSION}`. Pre-beta vaults are disposable and rebuild — no migration code. **This plan's two schema PRs (`mc`, CS3) must land after Foundation F1's v9**; if F1 hasn't merged, coordinate the numbers (they take the next two integers).
- Test only against disposable vaults (`tests/helpers.init_cli_workspace` / `tmp_path`); never a personal vault.
- Every new test file MUST be registered in `tests/conftest.py` `TEST_LEVELS` (`"unit"` pure fns, `"runtime"` vault-mutating flows, `"contract"` CLI/API); `test_testing_levels.py` enforces this.
- Stage explicit paths only — never `git add -A`.
- Trust rule (spec): a safety defense may never be credited to the human noticing a marker; CS3 findings are flag-and-route (Review items), **never block**.
- PR boundaries: PR-CS1 after Task 4, PR-MC after Task 7, PR-CS3 after Task 12. PR titles: `feat(security): …` / `fix(verify): …` / `feat(integrity): …`.

---

## PR-CS1 · Exfiltration neutralization (no schema)

### Task 1: `neutralize_untrusted_markdown` helper

**Files:**
- Create: `src/memoria_vault/runtime/content_security.py`
- Test: `tests/test_content_security.py` (new — register `"unit"`)

**Interfaces:**
- Consumes: nothing.
- Produces: `content_security.neutralize_untrusted_markdown(body: str) -> str` — escapes Markdown image/embed syntax, inerts raw HTML tags, wraps external URLs as non-clickable code spans; leaves vault-internal `[[wikilinks]]` and existing code spans/fences untouched. Tasks 3–4 consume it.

- [ ] **Step 1: Write the failing test**

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

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_content_security.py -v`
Expected: FAIL — module does not exist.

Also add to `tests/conftest.py` `TEST_LEVELS` (alphabetical): `"test_content_security.py": "runtime",` (it grows vault-mutating cases in Task 4).

- [ ] **Step 3: Implement**

```python
"""src/memoria_vault/runtime/content_security.py — CS1 exfiltration neutralization."""

from __future__ import annotations

import re

# Split on fenced code blocks and inline code spans so we never rewrite code.
_CODE_SEGMENT_RE = re.compile(r"(```.*?```|`[^`\n]+`)", re.DOTALL)
_IMG_RE = re.compile(r"!(?=\[)")                       # leading ! of ![...] or ![[...]]
_HTML_TAG_RE = re.compile(r"<(/?[a-zA-Z!][^>]*)>")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
_BARE_URL_RE = re.compile(r"(?<![`(\w])https?://[^\s`)\]<]+")


def _neutralize_segment(text: str) -> str:
    text = _IMG_RE.sub(r"\\", text)                    # ![ -> \[  (image cannot render)
    text = _HTML_TAG_RE.sub(r"&lt;\1&gt;", text)       # raw HTML tags inert
    text = _MD_LINK_RE.sub(r"\1 (`\2`)", text)         # [t](url) -> t (`url`)
    text = _BARE_URL_RE.sub(lambda m: f"`{m.group(0)}`", text)  # bare url -> code span
    return text


def neutralize_untrusted_markdown(body: str) -> str:
    """Neutralize embeds/HTML/external-URLs in machine-written third-party text.

    Vault-internal ``[[wikilinks]]`` and existing code spans/fences are left
    untouched (they are authored/trusted structure, not exfiltration vectors).
    """
    parts = _CODE_SEGMENT_RE.split(body)
    # split() keeps the delimiters (code segments) at odd indices — leave those verbatim
    return "".join(
        part if i % 2 else _neutralize_segment(part) for i, part in enumerate(parts)
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_content_security.py -v`
Expected: PASS. (If `test_image_embed_cannot_render` still finds `![`, confirm `_IMG_RE` fired; the replacement `\\` + surviving `[` yields `\[`, no `![`.)

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/content_security.py tests/test_content_security.py tests/conftest.py
git commit -m "feat(security): neutralize_untrusted_markdown helper (CS1 embeds/HTML/URLs)"
```

### Task 2: Neutralize at export (draft + argument export)

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py` (`_render_draft_export_body` ~:3165; `write_project_export` ~:2380 at the `content = str(rendered["content"])` choke ~:2403)
- Test: `tests/test_draft_verification.py` (extend — it already covers export)

**Interfaces:**
- Consumes: `content_security.neutralize_untrusted_markdown` (Task 1).
- Produces: exported markdown from both renderers is neutralized before it lands to disk/Pandoc.

- [ ] **Step 1: Read** `_render_draft_export_body` (knowledge.py:3165) and `write_project_export` (:2380–2410) fully; confirm `content = str(rendered["content"])` (~:2403) is the single string handed to disk/Pandoc.

- [ ] **Step 2: Write the failing test** (append to `tests/test_draft_verification.py`; reuse its existing draft-export fixture — copy the setup from `test_verified_source_backed_draft_exports_without_internal_markers`):

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

- [ ] **Step 3: Implement** — at the top of `knowledge.py` add `from memoria_vault.runtime.content_security import neutralize_untrusted_markdown`. In `_render_draft_export_body`, wrap the returned body: `return neutralize_untrusted_markdown(<existing body>)`. In `render_project_export_markdown`, neutralize the assembled `"\n".join(lines)` content before returning. (Belt-and-suspenders: both the body transformer and the argument renderer.)

- [ ] **Step 4: Run** `python -m pytest tests/test_draft_verification.py -v` → PASS; full suite `-x -q` → PASS (confirm no existing export test asserts a raw external URL/HTML survives; if one does, it was asserting the vulnerability — update it).

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/knowledge.py tests/test_draft_verification.py
git commit -m "fix(security): neutralize exported draft/argument content (CS1 export side)"
```

### Task 3: Neutralize digest bodies at apply

**Files:**
- Modify: the digest-compile write path — locate: `rg -n "compile-source-digest|def .*digest" src/memoria_vault/runtime/operations.py src/memoria_vault/runtime/knowledge.py`; the digest body is machine-compiled from source text and written via `stage_concept`/`materialize`.
- Test: `tests/test_content_security.py` (extend, `runtime`)

**Interfaces:**
- Consumes: `neutralize_untrusted_markdown`.
- Produces: a compiled digest's body is neutralized before it is written to the bundle.

- [ ] **Step 1: Read the digest-compile function** found above; identify where the digest `body` string is assembled (from source/model text) before it goes to the writer.

- [ ] **Step 2: Write the failing test** — drive a digest compilation whose source content carries `![beacon](http://evil/x)` and a raw `<img>`; assert the written `digests/<id>.md` body has them neutralized. (Reuse the digest fixture from `tests/test_knowledge.py` / `test_draft_compose.py`.)

- [ ] **Step 3: Implement** — wrap the assembled digest body: `body = neutralize_untrusted_markdown(body)` immediately before the `stage_concept`/write call in the digest path. Do **not** touch `note`/human-authored writes (design decision 1).

- [ ] **Step 4: Run** the new test + `tests/test_knowledge.py` → PASS.

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/*.py tests/test_content_security.py
git commit -m "fix(security): neutralize machine-compiled digest bodies at apply (CS1)"
```

### Task 4: Canary drill + PR-CS1

**Files:**
- Test: `tests/test_content_security.py` (add the end-to-end canary)

- [ ] **Step 1: Write the canary test** — a single seeded payload (`![x](http://beacon/p)` + `<script>` + bare `http://beacon/y`) placed in a digest source; assert it survives neither the apply-written digest file nor a project export that cites it. Concrete fixture, no placeholders.

- [ ] **Step 2: Gate + PR**

```bash
python scripts/verify
git add tests/test_content_security.py
git commit -m "test(security): CS1 canary — seeded beacon survives neither apply nor export"
gh pr create --title "feat(security): exfiltration neutralization at export + digest apply (CS1)" --body "Part of alpha.21 content-security (spec 2026-07-12-beta.1-content-security.md CS1). Neutralizes embeds/HTML/external-URLs in machine-written third-party text at export (always) and in machine-compiled digest bodies at apply; helper reusable by O2 ingest for the metadata-field side. Whole-body human writes untouched (design decision 1)."
```

---

## PR-MC · Evidence block-text-hash binding (schema +1)

### Task 5: `block_text_sha256` column on `evidence_sets`

**Files:**
- Modify: `src/memoria_vault/runtime/schema.sql` (`evidence_sets` ~:326; bump `PRAGMA user_version`), `src/memoria_vault/runtime/state.py` (`SCHEMA_VERSION`)
- Test: `tests/test_evidence_sets.py` (extend) or a new `tests/test_mc_hash_binding.py` (`runtime`)

**Interfaces:**
- Consumes: current `SCHEMA_VERSION` (read it first).
- Produces: `evidence_sets` has a nullable `block_text_sha256 TEXT` column; schema at the next version. Task 6 populates it, Task 7 reads it.

- [ ] **Step 1: Write the failing test**

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

- [ ] **Step 2: Run** → FAIL (column absent).

- [ ] **Step 3: Implement** — in `schema.sql`, add to the `evidence_sets` table (after `run_id`): `block_text_sha256 TEXT`. Read the current `SCHEMA_VERSION` (`rg -n '^SCHEMA_VERSION' state.py`), set both `state.SCHEMA_VERSION` and `schema.sql`'s final `PRAGMA user_version` to `current + 1`.

- [ ] **Step 4: Run** the new test + `tests/test_evidence_sets.py` → PASS (disposable vaults rebuild at the new version).

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/schema.sql src/memoria_vault/runtime/state.py tests/test_mc_hash_binding.py tests/conftest.py
git commit -m "feat(verify): evidence_sets.block_text_sha256 column (schema bump)"
```

### Task 6: Bind the block-text hash when rebuilding evidence rows

**Files:**
- Modify: `src/memoria_vault/runtime/state.py` (`rebuild_evidence_sets_from_markers` ~:1530 and the row builder ~:1740; the block-ref anchor helper `_evidence_block_ref` ~:1811)
- Test: `tests/test_mc_hash_binding.py` (extend)

**Interfaces:**
- Consumes: Task 5's column; the block-anchor resolution (`^blk-<id>`) already used by the marker→row builder.
- Produces: each rebuilt `evidence_sets` row stores `block_text_sha256 = "sha256:" + sha256(<anchored block body text>)`. Function `state._block_text_sha256(vault, block_ref) -> str | None` (resolves the `path#^blk-id` to its block text, hashes it; None if unresolvable).

- [ ] **Step 1: Read** `rebuild_evidence_sets_from_markers` (:1530) + the row-insert (:1740) + how a `block_ref` (`{rel}#^blk-{id}`) maps to the block's text in the file (the anchor scan around knowledge.py:1967 / :3182).

- [ ] **Step 2: Write the failing test** — compose a draft with one `%%ev%%` marker on a block; rebuild; assert the row's `block_text_sha256` equals `"sha256:"+sha256` of that block's current text; then edit the block text on disk, rebuild, assert the hash changed.

- [ ] **Step 3: Implement** — add `_block_text_sha256(vault, block_ref)` (resolve anchor → block body substring → `sha256_file`-style hash of the bytes; reuse the anchor-resolution already in the marker scanner). In the row builder, set `block_text_sha256` from it. Store `None` when the anchor doesn't resolve.

- [ ] **Step 4: Run** → PASS; `tests/test_evidence_markers.py` + `test_evidence_sets.py` → PASS.

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/state.py tests/test_mc_hash_binding.py
git commit -m "feat(verify): bind evidence rows to their block-text hash"
```

### Task 7: Verify demotes + refuses export on block-text drift

**Files:**
- Modify: `src/memoria_vault/runtime/knowledge.py` (`verify_project_draft` ~:2061; the export-gate labels `_verification_finding_labels` ~:3069 / the refuse-export path `render_project_draft_export_markdown` ~:2445)
- Test: `tests/test_mc_hash_binding.py` + `tests/test_draft_verification.py` (extend)

**Interfaces:**
- Consumes: the stored `block_text_sha256` (Task 6).
- Produces: `verify_project_draft` emits a `evidence-text-drift` finding (kind added to the findings vocabulary) when a resolved block's current text hash ≠ the stored `block_text_sha256`; export refuses while any such finding is open (same gate as `evidence-incomplete`).

- [ ] **Step 1: Write the failing test** — verify a clean draft (passes/exports); then edit the anchored block text on disk *without* re-running compose (simulates file-only rebuild / human-edit-under-marker); re-verify → assert a `evidence-text-drift` finding and that export now **refuses** with that reason.

- [ ] **Step 2: Run** → FAIL (no drift check today; edited text exports clean — the fail-open).

- [ ] **Step 3: Implement** — in `verify_project_draft`, after loading evidence rows, recompute `_block_text_sha256` for each row's `block_ref` and compare to the stored `block_text_sha256`; on mismatch (and non-null stored), append a finding `{"kind":"evidence-text-drift","block_ref":…,"reason":"block text changed after the evidence label was bound"}`. Add `evidence-text-drift` to the set that `render_project_draft_export_markdown` refuses on (mirror the existing `review-required`/`evidence-incomplete` gate).

- [ ] **Step 4: Run** the drift test + `tests/test_draft_verification.py` → PASS; `python scripts/verify` → PASS.

- [ ] **Step 5: Commit + PR**

```bash
git add src/memoria_vault/runtime/knowledge.py tests/test_mc_hash_binding.py tests/test_draft_verification.py
git commit -m "fix(verify): demote + refuse export when block text drifts from its evidence label"
gh pr create --title "fix(verify): bind evidence labels to block-text hash (mc-hash-binding)" --body "Archive gap #10. evidence_sets gains block_text_sha256; verify recomputes it and refuses export when a block's text changed after its label was bound — closing the fail-open where a verification label survived edited text. Full DB-authoritative inversion (stop rebuilding from markers) noted as follow-on (design decision 2)."
```

---

## PR-CS3 · Out-of-band change witness (schema +1)

### Task 8: `file_baseline` table

**Files:**
- Modify: `src/memoria_vault/runtime/schema.sql` (new table; bump `PRAGMA user_version`), `state.py` (`SCHEMA_VERSION`)
- Test: `tests/test_content_security.py` or `tests/test_trusted_writer.py` (extend)

**Interfaces:**
- Produces: table `file_baseline(subject_id TEXT PRIMARY KEY, human_sha256 TEXT, restriction_keys_json TEXT NOT NULL DEFAULT '[]', observed_at TEXT NOT NULL)`; `state.upsert_file_baseline(vault, subject_id, *, human_sha256, restriction_keys)` and `state.file_baseline(vault, subject_id) -> dict | None`. Tasks 9–11 use them.

- [ ] **Step 1: Write the failing test** — assert the table exists and `upsert_file_baseline` + `file_baseline` round-trip a hash + a `["superseded"]` key list.

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement** — add the table to `schema.sql`; bump `SCHEMA_VERSION`/`user_version` to next integer (read current first — this is the second schema PR; it takes the integer after PR-MC). Add the two `state` helpers next to `record_observed_file_edit` (:451).

- [ ] **Step 4: Run** → PASS; `python scripts/verify` → PASS.

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/schema.sql src/memoria_vault/runtime/state.py tests/*.py tests/conftest.py
git commit -m "feat(integrity): file_baseline table for the change witness (schema bump)"
```

### Task 9: Record baselines during the observe sweep

**Files:**
- Modify: `src/memoria_vault/runtime/trusted_writer.py` (`observe_pi_edits_from_status` ~:211; `observe_pi_edit` ~:140)
- Test: `tests/test_trusted_writer.py` (extend)

**Interfaces:**
- Consumes: `state.upsert_file_baseline` (Task 9); `_head_sha256` (:695); the restriction-key set `{"superseded","local-only"}` plus `standing` values `{"archived","retracted","superseded"}`.
- Produces: after each observe sweep, every scanned bundle file has a `file_baseline` row with its current human_sha256 and its current restriction-key list (parsed from frontmatter). Helper `trusted_writer._restriction_keys(frontmatter) -> list[str]`.

- [ ] **Step 1: Write the failing test** — run `observe_pi_edits_from_status` over a vault with a note carrying `standing: superseded`; assert its `file_baseline` row records `human_sha256` and `["superseded"]`.

- [ ] **Step 2: Run** → FAIL (no baseline recorded).

- [ ] **Step 3: Implement** — add `_restriction_keys(frontmatter)` returning the restriction markers present (`local-only: true` → `"local-only"`; `standing`/`superseded` in the retract set → `"superseded"`). In the sweep, after processing each path, `upsert_file_baseline(vault, output_id, human_sha256=<current sha>, restriction_keys=_restriction_keys(fm))`.

- [ ] **Step 4: Run** → PASS.

- [ ] **Step 5: Commit**

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
- Produces: a foreign-edit finding when a file's current hash ≠ its `file_baseline.human_sha256` AND the change was not made through the writer (no matching journal `output_sha256` for the new content) — surfaced as an `observed_external_edit` Review item, flag-not-block. Closes the `vault_hash_drift` fail-open (files never audited get a baseline the first sweep, then are watched).

- [ ] **Step 1: Write the failing test** — establish a baseline for a human note (one sweep); then overwrite the file on disk out-of-band (simulate a foreign agent/sync — write bytes directly, no journal event); run the sweep; assert a finding/Review item names the file as an out-of-band edit.

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement** — in the sweep, for each scanned path with a `file_baseline` row, if current hash ≠ baseline hash and the current hash matches no journaled `output_sha256` (reuse `_known_current_hashes`), emit the observed-external-edit event/finding and refresh the baseline. (Route via the existing `EVENT_OBSERVED_EXTERNAL_EDIT` + Review surfacing already used by `observe_pi_edit`.)

- [ ] **Step 4: Run** → PASS; `tests/test_integrity.py` → PASS.

- [ ] **Step 5: Commit**

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
- Produces: a `restriction-key-removed` finding/Review item when a key present in the baseline is absent now (e.g. `superseded` deleted → a retracted work silently re-admitted to Ask/export). Flag-not-block.

- [ ] **Step 1: Write the failing test** — baseline a note with `standing: superseded`; remove the key on disk; run the sweep; assert a `restriction-key-removed` finding names the file and the key.

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement** — in the sweep, diff `set(baseline.restriction_keys)` − `set(_restriction_keys(current_fm))`; for each removed key, emit a `restriction-key-removed` Review finding (include `subject_id`, `key`), then refresh the baseline.

- [ ] **Step 4: Run** → PASS.

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/trusted_writer.py tests/test_content_security.py
git commit -m "feat(integrity): witness restriction-key removal (superseded/local-only) (CS3)"
```

### Task 12: Surface + PR-CS3

**Files:**
- Modify: confirm both new finding kinds route to the Review surface the way `observed_external_edit` already does (`rg -n "observed_external_edit|write_work_prompt|finding" src/memoria_vault/runtime/`); add any missing wiring.
- Test: `tests/test_worker_integrity_jobs.py` (extend — the sweep runs as an operation job)

- [ ] **Step 1: Write the failing test** — run the sweep through the worker operation (`observe-pi-edits` / the sweep op) and assert both a foreign-edit and a restriction-key-removal surface as Review items via the worker path (not just the direct function).

- [ ] **Step 2: Implement** any wiring gap so both findings reach Review through the worker.

- [ ] **Step 3: Gate + PR**

```bash
python scripts/verify
git add src/memoria_vault/runtime/*.py tests/*.py
git commit -m "feat(integrity): route change-witness findings to Review via the worker sweep"
gh pr create --title "feat(integrity): out-of-band change witness (CS3)" --body "alpha.21 content-security CS3 (spec 2026-07-12-beta.1-content-security.md). Adds a file_baseline table; the observe sweep now witnesses out-of-band edits to human-class files (closing the vault_hash_drift fail-open on never-audited files) and restriction-key removal (superseded/local-only), surfaced as flag-not-block Review items. Pairs F2 journal-trust."
```

---

## Self-review notes

- **Spec coverage:** CS1 → Tasks 1–4 (export + digest-apply; metadata-field apply deferred to O2 per decision 1). `mc`-hash-binding (gap #10) → Tasks 5–7. CS3 → Tasks 8–12 (both fail-open holes: foreign human-file edits + restriction-key removal). CS2/CS4–CS8 are explicitly other packages (U3/O2/W2/X1/beta.2), not this plan.
- **Schema coordination:** three tasks read `SCHEMA_VERSION` before bumping and land after Foundation F1's v9; PR-MC and PR-CS3 take the next two integers — the Global Constraints and each schema task state this.
- **Placeholder scan:** the investigate-then-fill steps (Tasks 2, 3, 6, 7 test setups) each name the exact existing fixture to copy and forbid leaving `...`
- **Type consistency:** `neutralize_untrusted_markdown(str)->str`, `_block_text_sha256(vault, block_ref)->str|None`, `upsert_file_baseline(...)/file_baseline(...)`, `_restriction_keys(frontmatter)->list[str]` are named identically where consumed. Finding kinds `evidence-text-drift` / `restriction-key-removed` are used consistently.
