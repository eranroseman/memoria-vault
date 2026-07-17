# O2 Staged Import + Bulk Admission Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the O2 spec — multi-entry BibTeX/CSL import as a client-side loop over the shipped `capture-source` operation, with tiered adapters on the shipped item_type vocabulary, structural same-DOI dedupe plus cross-identifier duplicate flagging, one quiet run-scoped worklist per run, `import-run.v1` telemetry, and the pre-registered staged-import stop rule.

**Architecture:** A new `runtime/bulk_import.py` owns entry splitting, payload building, adapter normalization, fetch synthesis, and collision detection; the CLI driver loops the existing operation per entry under run-scoped idempotency keys with catalog pre-check resume; the worklists seam gains raised_by/loudness passthrough; instrumentation rides the I1 telemetry plane. Spec of record: `docs/superpowers/specs/2026-07-17-o2-staged-import-design.md` (main @ `51395f15`).

**Tech Stack:** Python 3 / SQLite / pytest; no new dependencies; no network in tests (injectable openers).

## Global Constraints

- **Sequencing precondition (spec §1, verbatim): implementation may not begin until the I1 full-wiring plan is implemented and merged** — instrumentation precedes all ingestion; the seeded-error battery must be green before any real-vault import; schema-before-corpus stands.
- Correctness gate: `python scripts/verify`; PR + `verify`/`gitleaks`; squash merge; explicit-path staging; disposable vaults only.
- Bulk admission is catalog-only, zero digests, fully keyless; the enrichment default flip (`--enrich`, off) is the one deliberate behavior change and is asserted as such.
- 1000-scale anything is beta.2 (spec §8); nothing here may assume corpus sizes beyond the 100-work stage.
- All line refs verified at origin/main `51395f15`; re-anchor by symbol if drifted.

## Cross-section contracts (BINDING — the manifests' seam resolutions)

1. **`runtime/bulk_import.py` module seams:** P.1's `split_bibtex_entries(text) -> list[str]` / `split_csl_entries(text) -> list[str]`; P.2's `build_entry_payload(fmt, entry_text) -> dict` (section A's interception point) and `entry_ref(fmt, entry_text, index) -> str` (citekey / CSL id / `entry-<index>` — the worklist item-ref vocabulary).
2. **The driver result** (P.2/P.3 produce; W consumes): `{ok, run_id (uuid4 hex), format, entries_total, admitted: [work_id…], skipped: [work_id…], failed: [{ref, error}…], duplicates: […], index_refresh_s, enrichment…}` — `admitted`/`skipped` use the **catalog's** work_id vocabulary (SPEC GAP P-1); zero-rows-PRESENT is the failure exit; run-scoped keys `import-<run_id>-<work_id>`.
3. **Adapter seams** (A produces): `_ENTRY_TYPE_MAP`, `entry_item_type(entry_fields) -> str` (shipped vocabulary `article/book/webpage/software/dataset/report`), `entry_type_mapped(entry_fields) -> bool`, `entry_fetch(entry_fields, identifiers) -> {method,url} | None` (PMCID→`pmc-oa`, arXiv→`arxiv-pdf`, `.pdf` URL→`pdf-url`, else None), `entry_capture_request(payload, fetch, *, mapped, opener)`, `detect_identifier_collisions(vault, work_id, identifiers) -> [{other_work_id, field}]`, `is_doi_collision_error(error) -> bool`.
4. **Worklist seams** (W produces): `emit_worklist(…, raised_by="worklists", loudness="notice")` passthrough (defaults = shipped behavior); `emit_import_worklist(vault, *, run_id, rows, entries_total, admitted) -> dict | None` (None on zero judgment rows — no worklist, no card); worklist id `import-<run_id>`; rows ranked duplicates → retraction → failed → unmapped.
5. **Telemetry** (W produces): `IMPORT_RUN_EVENT_SCHEMA = "import-run.v1"` + `validate_import_run_event` (typed ints, `format ∈ {bibtex, csl}`) in `engine/empirical_events.py`; dispatch branch in I1's `record_telemetry_event`; exactly one row per run.
6. **Cross-plan order tolerance:** O1 M.2's `resolve_fetch(row, *, opener)` is consumed by section A only (grep-first; if absent, land O1 M.2 first). I1's `runtime/telemetry.py` + seeded `decision-rules.yaml` are consumed by W.2/W.3 (grep-first; W.3 **blocks** with a stop-note if the I1 seed is absent). Section P consumes neither.
7. **Execution order:** P.1 → P.2 → P.3 → A.1 → A.2 → A.3 → W.1 → W.2 → W.3 → W.4. The worker `capture-bibtex-source` auto-enrichment (a different surface) is **not** flipped (SPEC GAP P-5).
8. **TEST_LEVELS:** `test_bulk_import.py: "contract"` (new, registered once in P.1; A and W extend it and other already-registered files with no further conftest change).

---
# P — Multi-entry parsing + the driver loop

Implements O2 spec §2 — entry iteration over the **unchanged** shipped builders, one worker request per entry under run-scoped idempotency keys `import-<run_id>-<work_id>`, resume via the `state.catalog_source` pre-check, per-row honesty with the zero-rows-PRESENT failure rule, the enrichment default flip behind `--enrich` (the one deliberate behavior change), and the explicit timed post-loop index refresh — slices 1–2 of spec §11. Spec §5's **structural same-DOI dedupe** lands here for free because it *is* the §2 skip path (same DOI ⇒ same `_bibtex_default_work_id` ⇒ pre-check hit ⇒ `skipped`), and P.2 pins it. Spec of record: `docs/superpowers/specs/2026-07-17-o2-staged-import-design.md` (§2, §5 first bullet, §10's single-entry-unchanged and flip-asserted criteria). All line refs verified at origin/main `51395f15`; re-anchor by symbol if drifted.

**Cross-plan order (binding).** The plan header's I1 precondition (2026-07-16-i1-full-wiring.md implemented + merged) governs the whole plan; section P itself consumes **no** I1 seam — it emits no telemetry. The `import-run.v1` emission (spec §6) belongs to this plan's telemetry section, which consumes P's run-summary dict (interface below) and I1's `record_telemetry_event(vault, event_type, payload) -> str` (`src/memoria_vault/runtime/telemetry.py`, I1 T.2) with that section's own grep-first tolerance. O1's `resolve_fetch(row, *, opener)` layer (`runtime/seed_install.py`, O1 M.2) is consumed by the adapter section (slice 3), **not** by P — P admits every entry through the shipped metadata-only capture path, so P has no O1 blocker. Grep-first anyway: `grep -rn "def resolve_fetch\|def record_telemetry_event" src/memoria_vault/` before starting — neither hit changes any P task; both absent is fine for P.

**What P deliberately does not do** (owned by later sections): item_type normalization + fetch synthesis (slice 3 consumes `build_entry_payload` as its interception point); cross-identifier duplicate flagging and the `doi UNIQUE` failure handler (slice 4 — `schema.sql:101` never fires in P because same-DOI entries are skipped before enqueue); worklist + quiet card minting (slice 5 consumes `entry_ref` and the `failed` rows; `emit_worklist` at `worklists.py:63-70` is untouched here); `import-run.v1` (slice 6 consumes the summary and its `index_refresh_s`).

**Execution order:** P.1 → P.2 → P.3. Tests: `tmp_path` vaults only; no network anywhere in P (BibTeX/CSL `capture-source` payloads perform no fetch — offline by construction; the injectable-opener rule bites in the adapter section).

**SPEC GAPS (each resolved inline; repo-convention resolutions, no mechanism changes):**

1. **Skipped-row identity.** The spec says "checks `state.catalog_source(vault, work_id)` and skips on a hit" but payload-level work_ids are unsanitized (`_bibtex_default_work_id`, capture.py:667-673, returns `doi-10.1000/alpha.2026` with the slash) while catalog rows carry the sanitized id (`doi-10.1000_alpha.2026`). Resolution: the driver records `skipped` using the catalog row's own `work_id` (the dict `catalog_source` returns, runtime/state.py:1603-1612), so `admitted` and `skipped` share one identity vocabulary — the catalog's.
2. **`--idempotency-key` on bulk.** `_common` (cli.py:560-566) gives `work import` a user-facing `--idempotency-key`; spec §2 fixes bulk keys as `import-<run_id>-<work_id>`. Resolution: the single-entry path keeps `args.idempotency_key` byte-identically (via `_enqueue_and_run`, cli.py:2087-2098); the bulk path ignores it in favor of run-scoped keys — noted here, honest in output via `run_id`.
3. **Zero-entry input.** A file with no parseable entry boundaries (empty file, empty CSL array) previously crashed with an uncaught `ValueError` traceback. Resolution: zero entries → the bulk path → `admitted`+`skipped` both empty → the spec's zero-rows-PRESENT failure, clean `ok: false` exit 1. A **single** malformed entry still takes the single-entry path and keeps the shipped `ValueError` surface (byte-identical).
4. **Refresh on a no-op run.** Spec §2 mandates the timed post-loop refresh; a re-run that admits nothing leaves the index unchanged. Resolution: refresh only when `admitted` is nonempty; otherwise `index_refresh_s: 0.0` — the honest measurement (a fabricated nonzero rebuild time on a no-op run would be the fiction §2 forbids).
5. **Flip scope.** The spec flips *`work import`* (cli.py:964 → `_queue_import_enrichment`, DOI gate at cli.py:2109). The worker operation `capture-bibtex-source` has its own auto-enrichment (worker.py:1232-1245) on a different surface — **not** flipped. Its pins (`tests/test_worker_capture_jobs.py:159-173`, `tests/test_worker_knowledge_cycle.py:116`) are **not** swept; the sweep target set (verified by `grep -rn "enrichment_job" tests/`) is exactly `tests/test_cli_work_project.py:53-54` and `:61-70` plus P.2's own transitional assert.
6. **Unclosed-container tail.** A BibTeX entry whose container never closes swallows the rest of the file in the shipped parser (`_matching_container`, capture.py:754-765 raises). Resolution: the splitter returns the remainder from that `@` as one final chunk; the driver names it as a failed row (per-row honesty) — entries *before* it are unaffected. Same single-token depth semantics as the shipped parser (a `)` inside a brace value of a paren-delimited entry miscounts there too — parity, not regression).

---

### Task P.1: Entry splitters in a new `runtime/bulk_import.py` (+ the truncation-defect pin)

**Files:**

- Create `src/memoria_vault/runtime/bulk_import.py`
- Create `tests/test_bulk_import.py`
- Modify `tests/conftest.py` — `TEST_LEVELS` dict at tests/conftest.py:18 (new-file registration, `"contract"`)

**Interfaces:**

- Consumes: `bibtex_capture_payload(bibtex: str, *, content_text=None, work_id=None, description=None) -> dict[str, Any]` (capture.py:295-329) and `csl_capture_payload(csl_json: dict[str, Any], *, raw_text: str, ...) -> dict[str, Any]` (capture.py:332-364) — in tests only, proving N chunks → N payloads through the **unchanged** builders; `parse_bibtex_entry` (capture.py:540-555) is the pinned-defect subject, not an import.
- Produces: `split_bibtex_entries(text: str) -> list[str]` (top-level `@` boundaries, brace/paren-aware, unclosed tail kept as a final failing chunk); `split_csl_entries(text: str) -> list[str]` (JSON array → per-item dumps; single object → `[text]`; non-object members and scalars raise `ValueError`).

- [ ] **Step 1: Write the failing tests** — create `tests/test_bulk_import.py`:

```python
"""Contract tests for multi-entry import splitting (O2 spec section 2, slice 1).

The first test pins the shipped defect the splitters fix: the shipped
single-entry builder silently truncates a multi-entry BibTeX file to its
first entry (parse_bibtex_entry stops at the first balanced container).
The splitters cut the file into per-entry chunks; the shipped builders
stay untouched and receive one chunk each.
"""

from __future__ import annotations

import json

import pytest

from memoria_vault.runtime.bulk_import import split_bibtex_entries, split_csl_entries
from memoria_vault.runtime.capture import bibtex_capture_payload, csl_capture_payload

TWO_ENTRIES = """@article{alpha2026,
  title = {Alpha Import},
  doi = {10.1000/alpha.2026},
  abstract = {First fixture entry.}
}

@article{beta2026,
  title = {Beta Import {With Nested Braces}},
  doi = {10.1000/beta.2026},
  abstract = {Second fixture entry, reachable at beta@example.org.}
}
"""


def test_shipped_builder_truncates_a_multi_entry_file_to_its_first_entry() -> None:
    payload = bibtex_capture_payload(TWO_ENTRIES)

    assert payload["citekey"] == "alpha2026"
    assert payload["identifiers"] == {"doi": "10.1000/alpha.2026"}


def test_split_bibtex_entries_yields_one_payload_per_entry() -> None:
    chunks = split_bibtex_entries(TWO_ENTRIES)

    assert len(chunks) == 2
    assert chunks[0].startswith("@article{alpha2026,")
    assert chunks[1].startswith("@article{beta2026,")
    payloads = [bibtex_capture_payload(chunk) for chunk in chunks]
    assert [payload["citekey"] for payload in payloads] == ["alpha2026", "beta2026"]
    assert payloads[1]["title"] == "Beta Import With Nested Braces"
    assert payloads[1]["identifiers"] == {"doi": "10.1000/beta.2026"}


def test_split_bibtex_entries_handles_paren_containers_and_inter_entry_junk() -> None:
    text = (
        "Comments outside entries are BibTeX junk and are ignored.\n"
        "@article(paren2026,\n"
        "  title = {Paren Container},\n"
        "  doi = {10.1000/paren.2026}\n"
        ")\n"
        "trailing junk without an at-sign\n" + TWO_ENTRIES
    )

    chunks = split_bibtex_entries(text)

    assert len(chunks) == 3
    assert chunks[0].startswith("@article(paren2026,")
    assert bibtex_capture_payload(chunks[0])["citekey"] == "paren2026"


def test_split_bibtex_entries_keeps_an_unclosed_tail_as_a_failing_chunk() -> None:
    text = TWO_ENTRIES + "\n@article{broken2026,\n  title = {Unclosed\n"

    chunks = split_bibtex_entries(text)

    assert len(chunks) == 3
    assert chunks[2].startswith("@article{broken2026,")
    with pytest.raises(ValueError):
        bibtex_capture_payload(chunks[2])


def test_split_csl_entries_array_yields_per_item_dumps() -> None:
    items = [
        {
            "id": "alpha-csl",
            "type": "article-journal",
            "title": "Alpha CSL",
            "DOI": "10.1000/alpha.csl",
        },
        {"id": "beta-csl", "type": "book", "title": "Beta CSL", "ISBN": "9780000000009"},
    ]

    chunks = split_csl_entries(json.dumps(items))

    assert len(chunks) == 2
    payloads = [csl_capture_payload(json.loads(chunk), raw_text=chunk) for chunk in chunks]
    assert [payload["work_id"] for payload in payloads] == ["alpha-csl", "beta-csl"]
    assert json.loads(chunks[1])["ISBN"] == "9780000000009"


def test_split_csl_entries_single_object_is_a_one_item_list_of_the_original_text() -> None:
    text = json.dumps({"id": "solo-csl", "type": "article-journal", "title": "Solo"})

    assert split_csl_entries(text) == [text]


def test_split_csl_entries_rejects_non_object_members_and_scalars() -> None:
    with pytest.raises(ValueError, match="item 2 must be a JSON object"):
        split_csl_entries('[{"id": "ok", "title": "OK"}, "not-an-object"]')
    with pytest.raises(ValueError, match="object or array"):
        split_csl_entries("42")
```

- [ ] **Step 2: Register the test file** — in `tests/conftest.py`, `TEST_LEVELS` (line 18):

```python
# old
    "test_backup_restore.py": "runtime",
# new
    "test_backup_restore.py": "runtime",
    "test_bulk_import.py": "contract",
```

- [ ] **Step 3: Run and confirm the expected failure** — `python -m pytest tests/test_bulk_import.py -q` → collection error: `ModuleNotFoundError: No module named 'memoria_vault.runtime.bulk_import'`.

- [ ] **Step 4: Minimal implementation** — create `src/memoria_vault/runtime/bulk_import.py`:

```python
"""Multi-entry splitting for `memoria work import` (O2 spec section 2).

The shipped single-entry builders (`bibtex_capture_payload` /
`csl_capture_payload`, runtime/capture.py) parse exactly one entry and stay
untouched; these splitters cut a multi-entry file into per-entry chunks that
feed them. A BibTeX entry whose container never closes is returned as the
final chunk so the bulk driver can name the failure instead of dropping it.
"""

from __future__ import annotations

import json


def split_bibtex_entries(text: str) -> list[str]:
    """Split BibTeX text on top-level @ boundaries, brace- and paren-aware."""
    entries: list[str] = []
    index = text.find("@")
    while index != -1:
        end = _entry_end(text, index)
        if end is None:
            entries.append(text[index:].strip())
            break
        entries.append(text[index : end + 1].strip())
        index = text.find("@", end + 1)
    return entries


def _entry_end(text: str, start: int) -> int | None:
    """Index of the container close matching this entry's opener, or None.

    A second top-level ``@`` before any opener ends the (malformed) chunk
    just before it; an unclosed container returns None (tail chunk).
    """
    closer = ""
    depth = 0
    for index in range(start + 1, len(text)):
        char = text[index]
        if not closer:
            if char == "{":
                closer, depth = "}", 1
            elif char == "(":
                closer, depth = ")", 1
            elif char == "@":
                return index - 1
        elif char == "{" and closer == "}":
            depth += 1
        elif char == "(" and closer == ")":
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return index
    return None


def split_csl_entries(text: str) -> list[str]:
    """Split CSL-JSON: array -> per-item dumps; single object -> [text]."""
    data = json.loads(text)
    if isinstance(data, dict):
        return [text]
    if isinstance(data, list):
        items: list[str] = []
        for index, item in enumerate(data, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"CSL array item {index} must be a JSON object")
            items.append(json.dumps(item, ensure_ascii=False, sort_keys=True))
        return items
    raise ValueError("CSL import expects a JSON object or array of objects")
```

- [ ] **Step 5: Run to pass** — `python -m pytest tests/test_bulk_import.py -q` → 7 passed.

- [ ] **Step 6: Commit (explicit paths only):**

```bash
git add src/memoria_vault/runtime/bulk_import.py tests/test_bulk_import.py tests/conftest.py
git commit -m "feat(import): brace-aware BibTeX/CSL entry splitters (O2 P.1)

Pins the shipped single-entry truncation defect and fixes it at the
splitter seam; the shipped builders stay untouched.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task P.2: The bulk driver loop in `_cmd_work_import`

**Files:**

- Modify `src/memoria_vault/cli.py` — `_cmd_work_import` (cli.py:951-966; re-anchor by symbol) + new `_bulk_work_import` helper directly below it
- Modify `src/memoria_vault/runtime/bulk_import.py` — add `build_entry_payload` / `entry_ref`
- Modify `tests/test_bulk_import.py` (contract tests for the two new functions)
- Modify `tests/test_cli_work_project.py` (bulk CLI tests; file already registered `"contract"`)

**Interfaces:**

- Consumes: `state.catalog_source(vault: Path, source_ref: str) -> dict[str, Any] | None` (runtime/state.py:1603 — the O1 resume-pre-check pattern; it sanitizes `source_ref` internally, so raw payload work_ids match); `engine_api.run_operation(workspace, operation_id, payload, *, actor, idempotency_key=None, schedule_id=None, command="") -> {ok, job, result}` (engine/api.py:414-444); `_queue_import_enrichment(args, payload, output) -> dict | None` (cli.py:2101-2127, DOI-gated at :2109 — unchanged in this task: bulk keeps the shipped auto-enqueue default until P.3 flips it); `enqueue_operation`'s request-id derivation `job_id = safe_filename(idempotency_key)` (worker.py:123-141, paths.py:15-17) — makes bulk request ids greppable as `import-<run_id>-%`.
- Produces: `build_entry_payload(fmt: str, entry_text: str) -> dict[str, Any]` and `entry_ref(fmt: str, entry_text: str, index: int) -> str` in `runtime/bulk_import.py` (the adapter section's normalization interception point and the worklist section's failed-row item-ref rule, respectively); `_bulk_work_import(args, entries) -> dict` returning `{ok, run_id, format, entries_total, admitted, skipped, failed:[{ref,error}], enrichment_jobs}` (P.3 adds `index_refresh_s`); run-scoped idempotency keys `import-<run_id>-<work_id>` with `run_id = uuid.uuid4().hex`.

- [ ] **Step 1: Write the failing contract tests** — append to `tests/test_bulk_import.py`:

```python
def test_build_entry_payload_dispatches_per_format() -> None:
    from memoria_vault.runtime.bulk_import import build_entry_payload

    chunks = split_bibtex_entries(TWO_ENTRIES)
    assert build_entry_payload("bibtex", chunks[1])["citekey"] == "beta2026"

    csl_chunk = json.dumps({"id": "solo-csl", "type": "article-journal", "title": "Solo"})
    payload = build_entry_payload("csl", csl_chunk)
    assert payload["work_id"] == "solo-csl"
    assert payload["raw_text"] == csl_chunk + "\n"


def test_entry_ref_names_citekey_csl_id_or_entry_index() -> None:
    from memoria_vault.runtime.bulk_import import entry_ref

    assert entry_ref("bibtex", "@article{broken2026,\n  title = {Unclosed\n", 4) == "broken2026"
    assert entry_ref("bibtex", "@ not an entry at all", 4) == "entry-4"
    assert entry_ref("csl", '{"id": "beta-csl", "title": ""}', 2) == "beta-csl"
    assert entry_ref("csl", "not json", 2) == "entry-2"
```

- [ ] **Step 2: Write the failing CLI tests** — append to `tests/test_cli_work_project.py` (its existing imports — `json`, `Path`, `pytest`, `main`, `state` — suffice):

```python
THREE_ENTRY_BIB = """@article{alpha2026,
  title = {Alpha Import},
  doi = {10.1000/alpha.2026},
  abstract = {First fixture entry.}
}

@article{beta2026,
  title = {Beta Import},
  doi = {10.1000/beta.2026},
  abstract = {Second fixture entry.}
}

@article{gamma2026,
  title = {Gamma Import},
  doi = {10.1000/gamma.2026},
  abstract = {Third fixture entry.}
}
"""


def _bulk_import(workspace: Path, source: Path, *extra: str) -> list[str]:
    return [
        "work",
        "import",
        "--workspace",
        str(workspace),
        "--format",
        "bibtex",
        "--file",
        str(source),
        "--json",
        *extra,
    ]


def test_cli_work_import_bulk_admits_every_entry_with_run_scoped_keys(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    bib = tmp_path / "sources.bib"
    bib.write_text(THREE_ENTRY_BIB, encoding="utf-8")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(_bulk_import(workspace, bib))
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["entries_total"] == 3
    assert out["ok"] is True
    assert out["format"] == "bibtex"
    assert out["admitted"] == [
        "doi-10.1000_alpha.2026",
        "doi-10.1000_beta.2026",
        "doi-10.1000_gamma.2026",
    ]
    assert out["skipped"] == []
    assert out["failed"] == []
    run_id = out["run_id"]
    assert len(run_id) == 32 and set(run_id) <= set("0123456789abcdef")
    assert len(out["enrichment_jobs"]) == 3  # shipped default; P.3 flips enrichment to opt-in
    for work_id in out["admitted"]:
        assert state.catalog_source(workspace, work_id) is not None
    with state.connect(workspace) as conn:
        captures = conn.execute(
            "SELECT COUNT(*) FROM operation_requests"
            " WHERE operation_id = 'capture-source' AND request_id LIKE ?",
            (f"import-{run_id}-%",),
        ).fetchone()[0]
    assert captures == 3


def test_cli_work_import_bulk_rerun_skips_admitted_rows_without_new_requests(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    bib = tmp_path / "sources.bib"
    bib.write_text(THREE_ENTRY_BIB, encoding="utf-8")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    main(_bulk_import(workspace, bib))
    capsys.readouterr()

    rc = main(_bulk_import(workspace, bib))
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["entries_total"] == 3
    assert out["ok"] is True
    assert out["admitted"] == []
    assert out["skipped"] == [
        "doi-10.1000_alpha.2026",
        "doi-10.1000_beta.2026",
        "doi-10.1000_gamma.2026",
    ]
    assert out["failed"] == []
    with state.connect(workspace) as conn:
        captures = conn.execute(
            "SELECT COUNT(*) FROM operation_requests WHERE operation_id = 'capture-source'"
        ).fetchone()[0]
    assert captures == 3  # resume = the pre-check: no fetch, no enqueue, no journal event


def test_cli_work_import_bulk_names_failed_entries_and_continues(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    bib = tmp_path / "sources.bib"
    bib.write_text(
        """@article{alpha2026,
  title = {Alpha Import},
  doi = {10.1000/alpha.2026}
}

@article{broken2026,
  title {Missing Equals}
}

@article{gamma2026,
  title = {Gamma Import},
  doi = {10.1000/gamma.2026}
}
""",
        encoding="utf-8",
    )
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(_bulk_import(workspace, bib))
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["entries_total"] == 3
    assert out["ok"] is True
    assert out["admitted"] == ["doi-10.1000_alpha.2026", "doi-10.1000_gamma.2026"]
    assert len(out["failed"]) == 1
    assert out["failed"][0]["ref"] == "broken2026"
    assert "missing =" in out["failed"][0]["error"]


def test_cli_work_import_bulk_fails_only_when_zero_rows_are_present(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    bib = tmp_path / "sources.bib"
    bib.write_text(
        """@article{brokenone2026,
  title {Missing Equals One}
}

@article{brokentwo2026,
  title {Missing Equals Two}
}
""",
        encoding="utf-8",
    )
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(_bulk_import(workspace, bib))
    out = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert out["ok"] is False
    assert out["admitted"] == [] and out["skipped"] == []
    assert [row["ref"] for row in out["failed"]] == ["brokenone2026", "brokentwo2026"]


def test_cli_work_import_bulk_same_doi_pair_collapses_to_one_row(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Spec section 5: same DOI => same work_id => structural dedupe through the
    # section 2 skip path. Reported skipped, never a judgment row.
    workspace = tmp_path / "workspace"
    bib = tmp_path / "sources.bib"
    bib.write_text(
        """@article{alpha2026,
  title = {Alpha Import},
  doi = {10.1000/alpha.2026}
}

@article{alphadup2026,
  title = {Alpha Import, Second Citekey},
  doi = {10.1000/alpha.2026}
}
""",
        encoding="utf-8",
    )
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(_bulk_import(workspace, bib))
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["entries_total"] == 2
    assert out["admitted"] == ["doi-10.1000_alpha.2026"]
    assert out["skipped"] == ["doi-10.1000_alpha.2026"]
    assert out["failed"] == []


def test_cli_work_import_bulk_csl_array_admits_each_item(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    csl = tmp_path / "sources.csl.json"
    csl.write_text(
        json.dumps(
            [
                {"id": "alpha-csl", "type": "article-journal", "title": "Alpha CSL"},
                {"id": "beta-csl", "type": "book", "title": "Beta CSL"},
            ]
        ),
        encoding="utf-8",
    )
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(
        [
            "work",
            "import",
            "--workspace",
            str(workspace),
            "--format",
            "csl",
            "--file",
            str(csl),
            "--json",
        ]
    )
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["entries_total"] == 2
    assert out["ok"] is True
    assert out["admitted"] == ["alpha-csl", "beta-csl"]
```

- [ ] **Step 3: Run and confirm the expected failures** — `python -m pytest tests/test_bulk_import.py tests/test_cli_work_project.py -q` → the two new contract tests fail with `ImportError: cannot import name 'build_entry_payload'`; the bulk CLI tests fail with `KeyError: 'entries_total'` (the shipped path truncates a multi-entry file to one single-entry admission — the pinned defect), except the zero-rows test (`ValueError: BibTeX field 'title' is missing =` — shipped uncaught traceback) and the CSL-array test (`ValueError: CSL import expects one item`). The shipped single-entry tests (`test_cli_work_project.py:14-70`, `:1244-1317`) still pass — they are the byte-identity pin and are not edited in P.2.

- [ ] **Step 4: Minimal implementation.** First extend `src/memoria_vault/runtime/bulk_import.py` — add to the imports block:

```python
import re
from typing import Any

from memoria_vault.runtime.capture import bibtex_capture_payload, csl_capture_payload
```

and append:

```python
_CITEKEY = re.compile(r"@\s*\w+\s*[{(]\s*([^,\s{}()]+)")


def build_entry_payload(fmt: str, entry_text: str) -> dict[str, Any]:
    """Build one capture-source payload from one split entry chunk."""
    if fmt == "bibtex":
        return bibtex_capture_payload(entry_text)
    item = json.loads(entry_text)
    if not isinstance(item, dict):
        raise ValueError("CSL entry must be a JSON object")
    return csl_capture_payload(item, raw_text=entry_text)


def entry_ref(fmt: str, entry_text: str, index: int) -> str:
    """Name a failed entry: citekey / CSL id when recoverable, else the index."""
    if fmt == "bibtex":
        if match := _CITEKEY.match(entry_text.strip()):
            return match.group(1)
    else:
        try:
            item = json.loads(entry_text)
        except ValueError:
            item = None
        if isinstance(item, dict) and str(item.get("id") or "").strip():
            return str(item["id"])
    return f"entry-{index}"
```

Then in `src/memoria_vault/cli.py`, replace `_cmd_work_import` (cli.py:951-966) with the following two functions (`uuid`, `state`, `engine_api` are already imported at cli.py:14/24/26):

```python
def _cmd_work_import(args: argparse.Namespace) -> int:
    from memoria_vault.runtime.bulk_import import split_bibtex_entries, split_csl_entries

    path = Path(args.file)
    text = path.read_text(encoding="utf-8")
    entries = split_bibtex_entries(text) if args.format == "bibtex" else split_csl_entries(text)
    if len(entries) == 1:
        if args.format == "bibtex":
            from memoria_vault.runtime.capture import bibtex_capture_payload

            payload = bibtex_capture_payload(text)
        else:
            from memoria_vault.runtime.capture import csl_capture_payload

            csl_item = _read_csl_item(text)
            payload = csl_capture_payload(csl_item, raw_text=text)
        output = _enqueue_and_run(args, "capture-source", payload)
        if enrichment := _queue_import_enrichment(args, payload, output):
            output["enrichment_job"] = enrichment
        return _emit(output, args)
    return _emit(_bulk_work_import(args, entries), args)


def _bulk_work_import(args: argparse.Namespace, entries: list[str]) -> dict[str, Any]:
    from memoria_vault.runtime.bulk_import import build_entry_payload, entry_ref

    workspace = _workspace(args)
    run_id = uuid.uuid4().hex
    admitted: list[str] = []
    skipped: list[str] = []
    failed: list[dict[str, str]] = []
    enrichment_jobs: list[str] = []
    for index, entry_text in enumerate(entries, start=1):
        try:
            payload = build_entry_payload(args.format, entry_text)
        except ValueError as exc:
            failed.append({"ref": entry_ref(args.format, entry_text, index), "error": str(exc)})
            continue
        work_id = str(payload["work_id"])
        if (existing := state.catalog_source(workspace, work_id)) is not None:
            skipped.append(str(existing["work_id"]))
            continue
        output = engine_api.run_operation(
            workspace,
            "capture-source",
            payload,
            idempotency_key=f"import-{run_id}-{work_id}",
            schedule_id=args.schedule_id,
            actor=args.actor,
            command="capture-source",
        )
        result = output.get("result") if isinstance(output.get("result"), dict) else {}
        if output["ok"]:
            admitted.append(str(result.get("work_id") or work_id))
            if enrichment := _queue_import_enrichment(args, payload, output):
                enrichment_jobs.append(str(enrichment["job_id"]))
        else:
            error = str(result.get("error") or result.get("status") or "capture failed")
            failed.append({"ref": str(payload.get("citekey") or work_id), "error": error})
    return {
        "ok": bool(admitted or skipped),
        "run_id": run_id,
        "format": args.format,
        "entries_total": len(entries),
        "admitted": admitted,
        "skipped": skipped,
        "failed": failed,
        "enrichment_jobs": enrichment_jobs,
    }
```

The single-entry branch is the shipped cli.py:951-966 body verbatim (behavior byte-identical, `--idempotency-key` included); the bulk branch mints run-scoped keys and ignores `args.idempotency_key` (GAP 2).

- [ ] **Step 5: Run to pass** — `python -m pytest tests/test_bulk_import.py tests/test_cli_work_project.py -q` → all pass, including the untouched shipped single-entry tests.

- [ ] **Step 6: Commit (explicit paths only):**

```bash
git add src/memoria_vault/cli.py src/memoria_vault/runtime/bulk_import.py \
  tests/test_bulk_import.py tests/test_cli_work_project.py
git commit -m "feat(import): bulk driver loop with run-scoped keys and per-row honesty (O2 P.2)

Multi-entry work import loops capture-source per entry: run-scoped
idempotency keys, catalog_source resume pre-check (structural same-DOI
dedupe), named failed rows, zero-rows-present failure. Single-entry path
byte-identical.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task P.3: The enrichment default flip (`--enrich`) + the timed post-loop index refresh

**Files:**

- Modify `src/memoria_vault/cli.py` — import parser block (cli.py:207-211), `_cmd_work_import` / `_bulk_work_import` (as landed by P.2; re-anchor by symbol)
- Modify `tests/test_cli_work_project.py` — the auto-enrichment sweep (`:14-70` shipped test; P.2's transitional assert) + new default/flag tests
- Modify `docs/reference/commands-and-transports/system-actions-operations.md` — line 87, the `memoria work import --format csl` row's behavior claim

**Interfaces:**

- Consumes: `_queue_import_enrichment` (cli.py:2101-2127 — **unchanged**; the DOI gate at :2109 stands, per spec §2); `rebuild_checked_search_index_explicit(vault, output_root=SEARCH_INPUT_ROOT, *, actor, machine) -> dict` (runtime/search_index.py:47-65; CLI-precedent call at cli.py:1976-1978 passes `actor=args.actor, machine="memoria-cli"`); `time.monotonic` (`time` imported at cli.py:13).
- Produces: `memoria work import --enrich` (`store_true`, default **off** — the one deliberate behavior change, single-entry and bulk alike); `index_refresh_s: float` in the bulk run summary (`0.0` when nothing was admitted — GAP 4), which the telemetry section maps to `import-run.index_refresh_s` (spec §6).
- **LOOP.1 order tolerance (grep-first):** before writing the refresh call, run `grep -rn "stale_checked_search_documents\|refresh_stale" src/memoria_vault/runtime/`. If LOOP.1's incremental checked-search refresh has landed, call that seam inside the same timing envelope instead; if absent (only `indexing.refresh_stale_passages` hits, which is the passage layer, not the checked search index), keep the whole-index `rebuild_checked_search_index_explicit` — honestly the whole-index rebuild time, per spec §2.
- The command-surface pin (`test_cli_command_surface_is_exact`, tests/test_cli.py:73-146) pins commands, not flags — `--enrich` needs no surface-test change; the doc-claims gate checks CLI *paths*, so the new flag and the P.3 doc edit keep it green (spec §10's "no new CLI surface beyond the existing `work import` flags plus `--enrich`").

- [ ] **Step 1: Write the failing tests** — append to `tests/test_cli_work_project.py`:

```python
def test_cli_work_import_default_leaves_enrichment_unqueued(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The one deliberate O2 behavior change (spec section 2): work import no
    # longer auto-queues enrichment; --enrich restores the shipped behavior.
    workspace = tmp_path / "workspace"
    bibtex = tmp_path / "source.bib"
    bibtex.write_text(
        """@article{alpha2026,
  title = {Alpha Import},
  doi = {10.1000/alpha.2026},
  abstract = {Keyless-first single entry.}
}
""",
        encoding="utf-8",
    )
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(
        [
            "work",
            "import",
            "--workspace",
            str(workspace),
            "--format",
            "bibtex",
            "--file",
            str(bibtex),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert "enrichment_job" not in output
    assert "index_refresh_s" not in output  # single-entry path stays byte-identical
    with state.connect(workspace) as conn:
        pending = conn.execute(
            "SELECT COUNT(*) FROM operation_requests WHERE operation_id = 'enrich-source'"
        ).fetchone()[0]
    assert pending == 0


def test_cli_work_import_bulk_enrich_flag_queues_once_per_admitted_doi_work(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    bib = tmp_path / "sources.bib"
    bib.write_text(THREE_ENTRY_BIB, encoding="utf-8")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(_bulk_import(workspace, bib, "--enrich"))
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert len(out["enrichment_jobs"]) == 3
    assert out["index_refresh_s"] > 0.0
    assert (workspace / ".memoria/index/search/manifest.json").is_file()
    with state.connect(workspace) as conn:
        enrich = conn.execute(
            "SELECT COUNT(*) FROM operation_requests WHERE operation_id = 'enrich-source'"
        ).fetchone()[0]
    assert enrich == 3

    # Re-run with --enrich: skipped works never re-enrich (spec section 2),
    # and a no-op run reports no fabricated rebuild time.
    rc = main(_bulk_import(workspace, bib, "--enrich"))
    out2 = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out2["skipped"] == out["admitted"]
    assert out2["enrichment_jobs"] == []
    assert out2["index_refresh_s"] == 0.0
    with state.connect(workspace) as conn:
        enrich = conn.execute(
            "SELECT COUNT(*) FROM operation_requests WHERE operation_id = 'enrich-source'"
        ).fetchone()[0]
    assert enrich == 3
```

- [ ] **Step 2: Sweep the tests pinning the shipped auto-enrichment** (GAP 5 — the complete sweep set; the worker-side pins at `tests/test_worker_capture_jobs.py:159-173` and `tests/test_worker_knowledge_cycle.py:116` pin `capture-bibtex-source`, a different surface, and are **not** touched):

  In `test_cli_work_import_bibtex_seeds_unchecked_db_work_without_markdown` (tests/test_cli_work_project.py:33-47), the argv list gains the flag — it now pins that `--enrich` restores shipped parity exactly:

```python
# old
            str(bibtex),
            "--json",
            "--idempotency-key",
            "import-bibtex",
        ]
    )
# new
            str(bibtex),
            "--json",
            "--idempotency-key",
            "import-bibtex",
            "--enrich",
        ]
    )
```

  In P.2's `test_cli_work_import_bulk_admits_every_entry_with_run_scoped_keys`, replace the transitional assert:

```python
# old
    assert len(out["enrichment_jobs"]) == 3  # shipped default; P.3 flips enrichment to opt-in
# new
    assert out["enrichment_jobs"] == []  # the one deliberate change: enrichment is opt-in
    assert out["index_refresh_s"] > 0.0  # explicit post-loop refresh, timed (spec section 2)
```

- [ ] **Step 3: Run and confirm the expected failures** — `python -m pytest tests/test_cli_work_project.py -q` → `test_cli_work_import_default_leaves_enrichment_unqueued` fails (`AssertionError`: `enrichment_job` present); both `--enrich` tests fail with `SystemExit: 2` (argparse: unrecognized arguments: --enrich); the edited bulk assert fails (`enrichment_jobs` has 3 entries; `KeyError: 'index_refresh_s'`).

- [ ] **Step 4: Minimal implementation** — three edits in `src/memoria_vault/cli.py`.

  (a) Parser (cli.py:207-211):

```python
# old
    import_cmd.add_argument("--file", required=True)
    import_cmd.set_defaults(handler=_cmd_work_import)
# new
    import_cmd.add_argument("--file", required=True)
    import_cmd.add_argument("--enrich", action="store_true")
    import_cmd.set_defaults(handler=_cmd_work_import)
```

  (b) Single-entry gate in `_cmd_work_import`:

```python
# old
        if enrichment := _queue_import_enrichment(args, payload, output):
            output["enrichment_job"] = enrichment
# new
        if args.enrich and (enrichment := _queue_import_enrichment(args, payload, output)):
            output["enrichment_job"] = enrichment
```

  (c) Bulk gate + timed refresh in `_bulk_work_import` — gate the per-entry enqueue:

```python
# old
            if enrichment := _queue_import_enrichment(args, payload, output):
                enrichment_jobs.append(str(enrichment["job_id"]))
# new
            if args.enrich and (enrichment := _queue_import_enrichment(args, payload, output)):
                enrichment_jobs.append(str(enrichment["job_id"]))
```

  and replace the summary return with the refreshed tail (whole-index until LOOP.1 — see the grep-first tolerance above):

```python
    index_refresh_s = 0.0
    if admitted:
        from memoria_vault.runtime.search_index import rebuild_checked_search_index_explicit

        refresh_started = time.monotonic()
        rebuild_checked_search_index_explicit(workspace, actor=args.actor, machine="memoria-cli")
        index_refresh_s = time.monotonic() - refresh_started
    return {
        "ok": bool(admitted or skipped),
        "run_id": run_id,
        "format": args.format,
        "entries_total": len(entries),
        "admitted": admitted,
        "skipped": skipped,
        "failed": failed,
        "enrichment_jobs": enrichment_jobs,
        "index_refresh_s": index_refresh_s,
    }
```

  (d) Doc correction for the behavior claim the flip stales, `docs/reference/commands-and-transports/system-actions-operations.md:87`:

```markdown
# old
| Capture CSL source | `memoria work import --format csl` + runtime helper (`csl_capture_payload`) | Parses one CSL-JSON item into unchecked catalog metadata, a raw `.csl.json` blob, and a DOI enrichment request when a DOI is present. |
# new
| Capture CSL source | `memoria work import --format csl` + runtime helper (`csl_capture_payload`) | Parses each CSL-JSON item into unchecked catalog metadata and a raw `.csl.json` blob; `--enrich` also queues a DOI enrichment request when a DOI is present. |
```

- [ ] **Step 5: Run to pass, then the full gate** — `python -m pytest tests/test_cli_work_project.py tests/test_bulk_import.py -q` → all pass. Then `python scripts/verify` → green (lint, product gates, tests, offline smoke, syntax; the doc-claims gate stays green — `memoria work import` is a real CLI path and no new command was added).

- [ ] **Step 6: Commit (explicit paths only):**

```bash
git add src/memoria_vault/cli.py tests/test_cli_work_project.py \
  docs/reference/commands-and-transports/system-actions-operations.md
git commit -m "feat(import): flip enrichment to opt-in --enrich; timed post-loop index refresh (O2 P.3)

The one deliberate O2 behavior change: work import no longer auto-queues
enrich-source (keyless-first); --enrich restores the shipped DOI-gated
behavior for single-entry and bulk alike. Bulk runs time an explicit
whole-index refresh into index_refresh_s (LOOP.1 order tolerance noted).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
# A — Adapter normalization + duplicates

This section implements spec §4 (per-type adapter matrix: the normalization dict + heuristics onto the **shipped** `item_type` vocabulary, and the fetch-synthesis rule over the O1 resolve layer) and spec §5 (duplicates: identifier-exact detection, the `doi UNIQUE` failure classifier, the same-DOI structural skip) — implementation slices 3–4 of `docs/superpowers/specs/2026-07-17-o2-staged-import-design.md`.

Everything lands in a new `src/memoria_vault/runtime/bulk_import.py` as pure seams the driver-loop section wires into the entry loop; **no `cli.py` or `capture.py` change happens here** (single-entry parse/admission stays pinned, per slice 1). The normalization point is a decided contract: the driver calls the unchanged shipped builders (`bibtex_capture_payload` capture.py:295-329 / `csl_capture_payload` capture.py:332-364), then stamps `payload["item_type"] = entry_item_type(...)` — necessary because the shipped CSL builder passes the raw CSL type straight through (`capture.py:358`, e.g. `article-journal`), which is not the shipped catalog vocabulary. Shipped `_item_type` (capture.py:843-854) is **not duplicated as logic and not called from product code**: it silently maps every unknown type to `article`, which is exactly the behavior the §4 flag must not inherit. Instead the bulk map is one explicit dict (the spec's "the mapping ships as code; this table is its documentation"), and a parity test pins its BibTeX rows to `_item_type` so the two can never drift.

Cross-plan preconditions honored here: the plan-level I1 gate is carried by the plan header (this section emits no telemetry and does not consume `record_telemetry_event`); Task A.2 consumes O1's `resolve_fetch(row, *, opener)` (`runtime/seed_install.py`, O1 plan Task M.2 — merged but possibly unexecuted), so A.2 opens with a grep-first dependency check and lands O1 M.2 first if the symbol is absent.

Line references verified at `51395f15`; re-anchor by symbol if drifted.

### Task A.1: Normalization dict + heuristics (`entry_item_type`)

**Files:**

- Create `src/memoria_vault/runtime/bulk_import.py`
- Create `tests/test_bulk_import.py`
- Modify `tests/conftest.py` — `TEST_LEVELS` dict at :18 (register the new file; A.2/A.3 extend the registered file with no further conftest change)

**Interfaces:**

- Consumes: shipped `_item_type(entry_type: str) -> str` (capture.py:843-854, parity-pinned by test only — never called from `bulk_import.py`); `csl_capture_payload` raw-type passthrough (capture.py:358, demonstrated by test); the shipped vocabulary `article/book/webpage/software/dataset/report` (schema.sql:105 default `'article'`, no CHECK — the reserved CHECK reshape is substrate work, not O2).
- Produces: `entry_item_type(entry_fields: dict[str, Any]) -> str` and `entry_type_mapped(entry_fields: dict[str, Any]) -> bool` (False ⇒ the §4 "unknown → reference-only as `article` + worklist mapping row" flag; the driver section consumes both), plus module constant `_ENTRY_TYPE_MAP`. `entry_fields` is one flat dict serving both formats: for BibTeX the driver passes `{"type": entry["entry_type"], **entry["fields"]}` (field keys are lowercased by `_parse_bibtex_fields`, capture.py:793); for CSL it passes the raw item (keys `type`/`URL`/`DOI`).

Decisions made here (spec gaps resolved inline, recorded in the module docstring):
- `@misc` heuristic precedence: **repo-host URL → `software`** first, then **DataCite DOI prefix → `dataset`**, then **any URL → `webpage`**, else unmappable (`article` + flagged). Rationale: Zenodo software deposits carry DataCite DOIs *and* repo URLs; the URL is the stronger signal.
- The DataCite prefix heuristic is a curated frozenset of eight common data-repository prefixes (Zenodo, Dryad, figshare, Harvard Dataverse, Mendeley Data, ICPSR, GBIF, UCI ML) — offline and keyless, extension is a one-line diff. The spec names the heuristic without naming prefixes.
- BibTeX `@conference` (alias of `@inproceedings`) maps to `article`, mirroring `_csl_type`'s `inproceedings|conference` handling (capture.py:981); it is absent from the spec table but shipped-consistent.

- [ ] **Step 0: Order-tolerance check** — `grep -n "def entry_item_type" src/memoria_vault/runtime/bulk_import.py 2>/dev/null`. If the module already exists (another O2 section landed first), append the constants/functions from Step 3 into it instead of creating the file, and skip the conftest edit if `test_bulk_import.py` is already registered. At `51395f15` neither exists.

- [ ] **Step 1: Write the failing tests** — create `tests/test_bulk_import.py`:

```python
"""Contract tests for the bulk-import adapter layer (O2 spec sections 4-5).

Everything here is offline: no network, no default openers, tmp_path vaults
only (later tasks). The section-4 table is exercised as code assertions.
"""

from __future__ import annotations

from memoria_vault.runtime.bulk_import import entry_item_type, entry_type_mapped


def test_entry_item_type_maps_bibtex_and_csl_types_onto_shipped_vocabulary() -> None:
    # BibTeX rows of the spec section-4 table.
    assert entry_item_type({"type": "article"}) == "article"
    assert entry_item_type({"type": "inproceedings"}) == "article"
    assert entry_item_type({"type": "incollection"}) == "article"
    assert entry_item_type({"type": "book"}) == "book"
    assert entry_item_type({"type": "techreport"}) == "report"
    assert entry_item_type({"type": "phdthesis"}) == "report"
    assert entry_item_type({"type": "online", "url": "https://example.test/post"}) == "webpage"
    # CSL rows of the table.
    assert entry_item_type({"type": "article-journal"}) == "article"
    assert entry_item_type({"type": "paper-conference"}) == "article"
    assert entry_item_type({"type": "chapter"}) == "article"
    assert entry_item_type({"type": "thesis"}) == "report"
    assert entry_item_type({"type": "post-weblog"}) == "webpage"
    assert entry_item_type({"type": "webpage"}) == "webpage"
    assert entry_item_type({"type": "software"}) == "software"
    assert entry_item_type({"type": "dataset"}) == "dataset"
    assert entry_item_type({"type": "report"}) == "report"


def test_entry_item_type_agrees_with_shipped_item_type_for_bibtex_aliases() -> None:
    """Parity pin: the bulk map may not drift from capture.py's _item_type."""
    from memoria_vault.runtime.capture import _item_type

    bibtex_aliases = (
        "article",
        "inproceedings",
        "conference",
        "incollection",
        "book",
        "inbook",
        "booklet",
        "online",
        "webpage",
        "www",
        "dataset",
        "data",
        "software",
        "manual",
        "techreport",
        "report",
        "phdthesis",
        "mastersthesis",
    )
    for alias in bibtex_aliases:
        assert entry_item_type({"type": alias}) == _item_type(alias), alias


def test_normalization_covers_the_shipped_csl_raw_type_passthrough() -> None:
    """csl_capture_payload emits the raw CSL type (capture.py:358); the driver
    stamps entry_item_type over it -- that override is the normalization."""
    from memoria_vault.runtime.capture import csl_capture_payload

    payload = csl_capture_payload(
        {"id": "x", "type": "article-journal", "title": "T"}, raw_text="{}"
    )
    assert payload["item_type"] == "article-journal"  # shipped passthrough, unchanged
    assert entry_item_type(payload["csl_json"]) == "article"  # what the driver stamps


def test_misc_repo_host_url_maps_to_software_and_wins_over_dataset_doi() -> None:
    fields = {
        "type": "misc",
        "url": "https://github.com/org/tool",
        "doi": "10.5281/zenodo.123",
    }
    assert entry_item_type(fields) == "software"
    assert entry_type_mapped(fields) is True
    assert entry_item_type({"type": "misc", "url": "https://gitlab.com/o/r"}) == "software"
    assert entry_item_type({"type": "misc", "url": "https://codeberg.org/o/r"}) == "software"
    assert entry_item_type({"type": "misc", "url": "https://gist.github.com/o/1"}) == "software"


def test_misc_datacite_doi_prefix_maps_to_dataset() -> None:
    fields = {"type": "misc", "doi": "10.5061/dryad.abc123"}
    assert entry_item_type(fields) == "dataset"
    assert entry_type_mapped(fields) is True


def test_misc_with_plain_url_maps_to_webpage() -> None:
    fields = {"type": "misc", "url": "https://example.org/page"}
    assert entry_item_type(fields) == "webpage"
    assert entry_type_mapped(fields) is True


def test_unknown_types_fall_back_to_article_and_are_flagged() -> None:
    for fields in (
        {"type": "patent"},
        {"type": "misc"},
        {"type": ""},
        {"type": "misc", "doi": "10.1234/x"},  # non-DataCite DOI, no URL
    ):
        assert entry_item_type(fields) == "article", fields
        assert entry_type_mapped(fields) is False, fields
    assert entry_type_mapped({"type": "article"}) is True
```

- [ ] **Step 2: Register the file and watch the tests fail** — in `tests/conftest.py`, add to `TEST_LEVELS` (alphabetical slot, before `test_bundle_roots.py`):

```python
    "test_bulk_import.py": "contract",
```

(exact edit: replace the line `    "test_bundle_roots.py": "contract",` with the two lines `    "test_bulk_import.py": "contract",` and `    "test_bundle_roots.py": "contract",`.)

Run `python -m pytest tests/test_bulk_import.py -v` → collection error: `ModuleNotFoundError: No module named 'memoria_vault.runtime.bulk_import'`.

- [ ] **Step 3: Minimal implementation** — create `src/memoria_vault/runtime/bulk_import.py`:

```python
"""Bulk-import adapter layer: normalization, fetch synthesis, duplicates.

Implements sections 4-5 of the O2 staged-import design
(docs/superpowers/specs/2026-07-17-o2-staged-import-design.md). The
section-4 table is documentation for _ENTRY_TYPE_MAP below -- the mapping
ships here as code. The driver stamps entry_item_type over the unchanged
shipped builders' payloads (csl_capture_payload passes raw CSL types
through; capture.py's _item_type maps unknowns to article silently, so it
is parity-pinned by test but never called from here).

Decided heuristic order for @misc: repo-host URL -> software, then
DataCite DOI prefix -> dataset, then any URL -> webpage (a Zenodo software
deposit carries a DataCite DOI *and* a repo URL; the URL is the stronger
signal). The DataCite prefixes are a curated offline list, not a registry
lookup.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

#: One dict over the union of BibTeX entry types and CSL item types, onto
#: the shipped item_type vocabulary. BibTeX rows mirror capture.py's
#: _item_type (parity-pinned by test); CSL rows are the spec table's.
_ENTRY_TYPE_MAP: dict[str, str] = {
    # Shipped vocabulary passes through.
    "article": "article",
    "book": "book",
    "webpage": "webpage",
    "software": "software",
    "dataset": "dataset",
    "report": "report",
    # BibTeX aliases.
    "inproceedings": "article",
    "incollection": "article",
    "conference": "article",
    "inbook": "book",
    "booklet": "book",
    "online": "webpage",
    "www": "webpage",
    "data": "dataset",
    "manual": "software",
    "techreport": "report",
    "phdthesis": "report",
    "mastersthesis": "report",
    # CSL aliases.
    "article-journal": "article",
    "paper-conference": "article",
    "chapter": "article",
    "thesis": "report",
    "post-weblog": "webpage",
}

_REPO_HOSTS = ("github.com", "gitlab.com", "codeberg.org")

#: DataCite DOI-prefix heuristic: common data repositories (Zenodo, Dryad,
#: figshare, Harvard Dataverse, Mendeley Data, ICPSR, GBIF, UCI ML).
_DATASET_DOI_PREFIXES = frozenset(
    {"10.5281", "10.5061", "10.6084", "10.7910", "10.17632", "10.3886", "10.15468", "10.24432"}
)


def entry_item_type(entry_fields: dict[str, Any]) -> str:
    """Normalize one entry onto the shipped item_type vocabulary.

    entry_fields is one flat dict for both formats: BibTeX callers pass
    {"type": entry_type, **fields} (lowercased field keys); CSL callers
    pass the raw item (type/URL/DOI keys).
    """
    return _resolve_item_type(entry_fields)[0]


def entry_type_mapped(entry_fields: dict[str, Any]) -> bool:
    """False when entry_item_type guessed article for an unmappable type.

    The driver mints the section-4 worklist mapping row from this flag,
    and admits the entry reference-only (fail visible, never silent).
    """
    return _resolve_item_type(entry_fields)[1]


def _resolve_item_type(entry_fields: dict[str, Any]) -> tuple[str, bool]:
    raw_type = str(entry_fields.get("type") or "").strip().lower()
    if raw_type in _ENTRY_TYPE_MAP:
        return _ENTRY_TYPE_MAP[raw_type], True
    if raw_type == "misc":
        url = _entry_url(entry_fields)
        if _is_repo_host(url):
            return "software", True
        if _doi_prefix(entry_fields) in _DATASET_DOI_PREFIXES:
            return "dataset", True
        if url:
            return "webpage", True
    return "article", False


def _entry_url(entry_fields: dict[str, Any]) -> str:
    return str(entry_fields.get("url") or entry_fields.get("URL") or "").strip()


def _entry_doi(entry_fields: dict[str, Any]) -> str:
    return str(entry_fields.get("doi") or entry_fields.get("DOI") or "").strip()


def _doi_prefix(entry_fields: dict[str, Any]) -> str:
    return _entry_doi(entry_fields).partition("/")[0]


def _is_repo_host(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == repo or host.endswith(f".{repo}") for repo in _REPO_HOSTS)
```

- [ ] **Step 4: Run to pass** — `python -m pytest tests/test_bulk_import.py -v` → 7 passed.

- [ ] **Step 5: Commit** —

```
git add src/memoria_vault/runtime/bulk_import.py tests/test_bulk_import.py tests/conftest.py
git commit -m "feat(bulk-import): normalization dict + heuristics onto shipped item_type vocabulary

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task A.2: Fetch synthesis + admission-tier routing (`entry_fetch`, `entry_capture_request`)

**Files:**

- Modify `src/memoria_vault/runtime/bulk_import.py`
- Modify `tests/test_bulk_import.py`

**Interfaces:**

- Consumes: **O1's** `resolve_fetch(row: dict[str, Any], *, opener: Callable[[str], Any] | None = None) -> bytes` (`src/memoria_vault/runtime/seed_install.py`, O1 plan Task M.2 — the row's `fetch` dict is `{method, url}` with methods `{pmc-oa, pdf-url, arxiv-pdf}`; the opener returns a context-manager response exposing `.read()`; non-PDF payloads and OA-service errors raise `ValueError`). The shipped worker payload contracts this routing emits into: `capture-pdf-source` (worker.py:1276-1314 → `stage_pdf_source` capture.py:461-494), `capture-url-source` (worker.py:1249-1273 → `_store_url_source` capture.py:420-458, `item_type="webpage"` at :447), `capture-source` passthrough (worker.py:1131-1169 → `stage_capture_payload` capture.py:367-395). `safe_filename` (runtime/paths.py:15).
- Produces: `entry_fetch(entry_fields: dict[str, Any], identifiers: dict[str, Any]) -> dict[str, str] | None` (the §4 fetch-synthesis rule: PMCID → `pmc-oa` `oa.fcgi` URL; arXiv id → `arxiv-pdf` `export.arxiv.org/pdf/<id>`; entry URL ending `.pdf` → `pdf-url`; **bare DOI → None = metadata-only** — no DOI→PMCID conversion exists in beta.1) and `entry_capture_request(payload: dict[str, Any], fetch: dict[str, str] | None, *, mapped: bool = True, opener: Callable[[str], Any] | None = None) -> tuple[str, dict[str, Any]]` (the tier router: returns the `(operation_id, request_payload)` pair the driver enqueues). Decided seam contract: **a fetch failure raises** (the `ValueError` from `resolve_fetch` propagates); the driver's per-row try/except names the row failed (spec §2 "capture refusal") and iteration continues — no silent downgrade to metadata-only.

Tier policy encoded (spec §4 table): `article` may use any synthesized fetch; `report` only a `pdf-url` fetch (text "via a direct PDF URL when present"); `webpage` with a resource routes to the shipped `capture-url-source` path (which re-derives the same work_id — `_url_work_id`, capture.py:1019-1023, is also `_bibtex_default_work_id`'s URL branch at capture.py:671-672, so the §2 catalog pre-check converges; the shipped path does not carry citekey/csl metadata, accepted as shipped); `book` stays metadata-only (shipped behavior, unchanged); `software`/`dataset` are reference-only; unmapped rows (`mapped=False`) are reference-only regardless of identifiers.

- [ ] **Step 0: O1 dependency check (grep-first)** — `grep -n "def resolve_fetch" src/memoria_vault/runtime/seed_install.py 2>/dev/null`. **If the file or symbol is absent** (O1 plan merged but unexecuted — true at `51395f15`), land O1 plan Task M.2 first (`docs/superpowers/plans/2026-07-16-o1-onboarding-seed.md` — it creates `resolve_fetch` plus `tests/test_seed_install.py`), then return here.

- [ ] **Step 1: Write the failing tests** — append to `tests/test_bulk_import.py`:

```python
import base64

import pytest

from memoria_vault.runtime.bulk_import import entry_capture_request, entry_fetch

PDF_BYTES = b"%PDF-1.4 bulk fixture bytes\n"
OA_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC6099118"
PDF_HREF = "https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/aa/bb/PMC6099118.pdf"
PMC_XML = (
    b'<OA><records returned-count="1" total-count="1">'
    b'<record id="PMC6099118" license="CC BY">'
    b'<link format="pdf" '
    b'href="https://ftp.ncbi.nlm.nih.gov/pub/pmc/oa_pdf/aa/bb/PMC6099118.pdf"/>'
    b"</record></records></OA>"
)


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, *_exc: object) -> bool:
        return False


def _opener(responses: dict[str, bytes]):
    calls: list[str] = []

    def opener(url: str) -> _FakeResponse:
        calls.append(url)
        if url not in responses:
            raise AssertionError(f"unexpected fetch: {url}")
        return _FakeResponse(responses[url])

    opener.calls = calls
    return opener


def _poisoned_opener(url: str) -> _FakeResponse:
    raise AssertionError(f"this tier must not fetch: {url}")


def _payload(item_type: str, **overrides):
    payload = {
        "work_id": "w-1",
        "title": "Fixture Work",
        "description": "Fixture description.",
        "content_text": "Abstract text.",
        "raw_text": "@misc{x}\n",
        "raw_filename": "w-1.bib",
        "resource": "",
        "item_type": item_type,
        "identifiers": {},
        "csl_json": {"id": "w-1"},
        "provider_coverage": "partial",
        "text_status": "abstract-only",
        "citekey": "w1",
    }
    payload.update(overrides)
    return payload


def test_entry_fetch_synthesizes_only_o1_resolvable_methods() -> None:
    assert entry_fetch({}, {"pmcid": "PMC6099118"}) == {"method": "pmc-oa", "url": OA_URL}
    assert entry_fetch({}, {"pmcid": "6099118"})["url"].endswith("id=PMC6099118")
    assert entry_fetch({}, {"arxiv": "2411.14199"}) == {
        "method": "arxiv-pdf",
        "url": "https://export.arxiv.org/pdf/2411.14199",
    }
    assert (
        entry_fetch({}, {"arxiv": "arXiv:2411.14199v1"})["url"]
        == "https://export.arxiv.org/pdf/2411.14199v1"
    )
    assert entry_fetch({"url": "https://example.test/paper.PDF"}, {}) == {
        "method": "pdf-url",
        "url": "https://example.test/paper.PDF",
    }
    # Precedence: PMCID > arXiv > .pdf URL.
    both = entry_fetch(
        {"url": "https://example.test/p.pdf"},
        {"pmcid": "PMC1", "arxiv": "2411.14199"},
    )
    assert both["method"] == "pmc-oa"
    # A bare DOI admits metadata-only: no synthesized fetch, ever.
    assert entry_fetch({"url": "https://doi.org/10.1234/x"}, {"doi": "10.1234/x"}) is None
    assert entry_fetch({}, {}) is None


def test_article_with_pmcid_routes_through_pmc_oa_to_the_pdf_capture_seam() -> None:
    payload = _payload(
        "article",
        identifiers={"doi": "10.3389/fpsyg.2018.01483", "pmcid": "PMC6099118"},
    )
    fetch = entry_fetch({}, payload["identifiers"])
    opener = _opener({OA_URL: PMC_XML, PDF_HREF: PDF_BYTES})

    operation_id, request = entry_capture_request(payload, fetch, opener=opener)

    assert operation_id == "capture-pdf-source"
    assert base64.b64decode(request["raw_pdf_base64"]) == PDF_BYTES
    assert request["work_id"] == "w-1"
    assert request["item_type"] == "article"
    assert request["identifiers"] == payload["identifiers"]
    assert request["citekey"] == "w1"
    assert request["raw_filename"] == "w-1.pdf"
    assert opener.calls == [OA_URL, PDF_HREF]


def test_article_with_arxiv_id_routes_through_arxiv_pdf() -> None:
    payload = _payload("article", identifiers={"arxiv": "2411.14199"})
    fetch = entry_fetch({}, payload["identifiers"])
    url = "https://export.arxiv.org/pdf/2411.14199"
    opener = _opener({url: PDF_BYTES})

    operation_id, request = entry_capture_request(payload, fetch, opener=opener)

    assert operation_id == "capture-pdf-source"
    assert base64.b64decode(request["raw_pdf_base64"]) == PDF_BYTES


def test_report_gets_text_only_via_a_direct_pdf_url() -> None:
    pdf_url = "https://agency.test/report-42.pdf"
    with_url = _payload("report", resource=pdf_url)
    fetch = entry_fetch({"url": pdf_url}, {})
    opener = _opener({pdf_url: PDF_BYTES})
    operation_id, request = entry_capture_request(with_url, fetch, opener=opener)
    assert operation_id == "capture-pdf-source"
    assert base64.b64decode(request["raw_pdf_base64"]) == PDF_BYTES

    # An arXiv-only report stays metadata-only (spec table: direct PDF URL only).
    arxiv_only = _payload("report", identifiers={"arxiv": "2411.14199"})
    arxiv_fetch = entry_fetch({}, arxiv_only["identifiers"])
    operation_id, request = entry_capture_request(
        arxiv_only, arxiv_fetch, opener=_poisoned_opener
    )
    assert operation_id == "capture-source"
    assert request is arxiv_only


def test_metadata_and_reference_only_tiers_never_fetch() -> None:
    pdf_fetch = {"method": "pdf-url", "url": "https://example.test/p.pdf"}
    # book: metadata-only, shipped behavior unchanged.
    # software / dataset: reference-only.
    for item_type in ("book", "software", "dataset"):
        payload = _payload(item_type)
        operation_id, request = entry_capture_request(
            payload, pdf_fetch, opener=_poisoned_opener
        )
        assert operation_id == "capture-source", item_type
        assert request is payload
    # Unmapped rows admit reference-only regardless of identifiers.
    flagged = _payload("article", identifiers={"pmcid": "PMC6099118"})
    operation_id, request = entry_capture_request(
        flagged,
        entry_fetch({}, flagged["identifiers"]),
        mapped=False,
        opener=_poisoned_opener,
    )
    assert operation_id == "capture-source"
    assert request is flagged


def test_webpage_rows_route_to_the_shipped_capture_url_source_path() -> None:
    payload = _payload("webpage", resource="https://example.test/post")

    operation_id, request = entry_capture_request(payload, None, opener=_poisoned_opener)

    assert operation_id == "capture-url-source"
    assert request == {
        "url": "https://example.test/post",
        "title": "Fixture Work",
        "description": "Fixture description.",
    }


def test_fetch_failure_raises_for_the_driver_to_name_the_row_failed() -> None:
    payload = _payload("article", resource="https://example.test/p.pdf")
    fetch = {"method": "pdf-url", "url": "https://example.test/p.pdf"}
    opener = _opener({"https://example.test/p.pdf": b"<html>login wall</html>"})

    with pytest.raises(ValueError):
        entry_capture_request(payload, fetch, opener=opener)
```

- [ ] **Step 2: Run and watch it fail** — `python -m pytest tests/test_bulk_import.py -v` → collection error: `ImportError: cannot import name 'entry_capture_request' from 'memoria_vault.runtime.bulk_import'`.

- [ ] **Step 3: Minimal implementation** — in `src/memoria_vault/runtime/bulk_import.py`, extend the imports:

```python
import base64
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse

from memoria_vault.runtime.paths import safe_filename
```

(exact edit: the module currently imports only `Any` and `urlparse`; the block above replaces the import section, keeping `from __future__ import annotations` first.) Then append:

```python
def entry_fetch(
    entry_fields: dict[str, Any], identifiers: dict[str, Any]
) -> dict[str, str] | None:
    """Synthesize a fetch only for identifiers the O1 resolve methods handle.

    PMCID -> pmc-oa oa.fcgi URL; arXiv id -> arxiv-pdf export URL; entry URL
    ending .pdf -> pdf-url. A bare DOI returns None (= metadata-only): no
    DOI->PMCID conversion exists or is built in beta.1.
    """
    pmcid = str(identifiers.get("pmcid") or "").strip()
    if pmcid:
        if not pmcid.upper().startswith("PMC"):
            pmcid = f"PMC{pmcid}"
        return {
            "method": "pmc-oa",
            "url": f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={pmcid}",
        }
    arxiv = str(identifiers.get("arxiv") or "").strip()
    if arxiv.lower().startswith("arxiv:"):
        arxiv = arxiv[len("arxiv:") :].strip()
    if arxiv:
        return {"method": "arxiv-pdf", "url": f"https://export.arxiv.org/pdf/{arxiv}"}
    url = _entry_url(entry_fields)
    if url.lower().endswith(".pdf"):
        return {"method": "pdf-url", "url": url}
    return None


def entry_capture_request(
    payload: dict[str, Any],
    fetch: dict[str, str] | None,
    *,
    mapped: bool = True,
    opener: Callable[[str], Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Route one built capture payload to its section-4 admission tier.

    Returns the (operation_id, request_payload) pair the driver enqueues.
    A fetch failure raises (resolve_fetch's ValueError propagates); the
    driver names the row failed and continues -- never a silent downgrade.
    """
    item_type = str(payload.get("item_type") or "article")
    resource = str(payload.get("resource") or "").strip()
    if mapped and item_type == "webpage" and resource:
        return (
            "capture-url-source",
            {
                "url": resource,
                "title": str(payload.get("title") or ""),
                "description": str(payload.get("description") or ""),
            },
        )
    if fetch is not None and mapped and _fetch_allowed(item_type, fetch["method"]):
        from memoria_vault.runtime.seed_install import resolve_fetch

        raw_bytes = resolve_fetch(
            {"id": payload["work_id"], "title": payload.get("title", ""), "fetch": fetch},
            opener=opener,
        )
        work_id = str(payload["work_id"])
        return (
            "capture-pdf-source",
            {
                "work_id": work_id,
                "title": str(payload.get("title") or work_id),
                "description": str(payload.get("description") or ""),
                "raw_pdf_base64": base64.b64encode(raw_bytes).decode(),
                "raw_filename": f"{safe_filename(work_id)}.pdf",
                "resource": resource or fetch["url"],
                "item_type": item_type,
                "identifiers": payload.get("identifiers"),
                "csl_json": payload.get("csl_json"),
                "citekey": str(payload.get("citekey") or ""),
            },
        )
    return ("capture-source", payload)


def _fetch_allowed(item_type: str, method: str) -> bool:
    """Section-4 tier policy: article takes any fetch; report only pdf-url."""
    if item_type == "article":
        return True
    return item_type == "report" and method == "pdf-url"
```

- [ ] **Step 4: Run to pass** — `python -m pytest tests/test_bulk_import.py -v` → 14 passed (7 from A.1 + 7 new). Also re-run the O1 layer it consumes: `python -m pytest tests/test_seed_install.py -v` → green.

- [ ] **Step 5: Commit** —

```
git add src/memoria_vault/runtime/bulk_import.py tests/test_bulk_import.py
git commit -m "feat(bulk-import): fetch synthesis + admission-tier routing over the O1 resolve layer

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task A.3: Duplicates — cross-identifier detection, the doi-UNIQUE classifier, the structural skip

**Files:**

- Modify `src/memoria_vault/runtime/bulk_import.py`
- Modify `tests/test_bulk_import.py`

**Interfaces:**

- Consumes: `state.catalog_sources(vault: Path, *, checked_only: bool = True) -> list[dict[str, Any]]` (state.py:1615-1636; rows carry `identifiers` parsed from the `identifiers_json` TEXT column by `_source_row`, state.py:2465 — identifiers live **only** there for catalog sources; the `external_ids` table is enrichment-owned and not consulted); `state.catalog_source(vault, source_ref)` (state.py:1603-1612 — the §2 pre-check seam, work_id-normalizing via `state._work_id` exactly as `stage_catalog_source` normalizes on write, capture.py:96/660-664); `_bibtex_default_work_id` (capture.py:667-673 — DOI-bearing entries key as `doi-<doi.lower()>`); `doi TEXT UNIQUE` (schema.sql:101) with `upsert_catalog_record`'s `ON CONFLICT(work_id) DO UPDATE` (state.py:1558) — a *cross-work_id* DOI collision is not absorbed by the conflict clause and raises `sqlite3.IntegrityError: UNIQUE constraint failed: catalog_sources.doi` out of `stage_capture_payload` (capture.py:129), which the worker records verbatim as `{"status": "failed", "error": str(exc)}` (worker.py:224-226); test helpers `call_with_context`/`copy_memoria_dirs`/`init_git` (tests/helpers.py:71/201/222).
- Produces: `detect_identifier_collisions(vault: Path, work_id: str, identifiers: dict[str, Any]) -> list[dict[str, str]]` (rows `{"other_work_id": ..., "field": ...}`, fields checked: `arxiv`, `pmcid` — exact match only, per the §5 PI ruling; **contract: `work_id` is the admitted row id as returned in the capture result** (`result["work_id"]`, capture.py:171 / worker.py:1120-1128), already normalized, so self-exclusion is plain equality) and `is_doi_collision_error(error: str) -> bool` (the §5 `doi UNIQUE` edge classifier the driver applies to a failed job's `error` string to record the entry **failed-and-flagged duplicate** instead of a bare failure). The scan is honest: a full-catalog Python loop over `state.catalog_sources(checked_only=False)` — O(N) with no new SQL and no index, correct at beta.1's 100-work ceiling (spec §8); DOI is deliberately **not** a triage field (same-DOI is structural dedupe or the UNIQUE edge, never a judgment row).

- [ ] **Step 1: Write the failing tests** — append to `tests/test_bulk_import.py`:

```python
import sqlite3
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.bulk_import import (
    detect_identifier_collisions,
    is_doi_collision_error,
)
from tests.helpers import call_with_context, copy_memoria_dirs, init_git

BIB_DOI_ARXIV = """@article{smith2024,
  title = {Admitted Work},
  author = {Smith, Ada},
  doi = {10.1234/admitted},
  arxiv = {2411.14199},
  year = {2024}
}
"""

BIB_PMCID = """@article{jones2023,
  title = {PMC Work},
  author = {Jones, Bo},
  doi = {10.1234/pmc-work},
  pmcid = {PMC7399101},
  year = {2023}
}
"""

BIB_SAME_DOI_A = """@article{alpha2024,
  title = {Shared DOI Entry One},
  doi = {10.7777/Same},
  year = {2024}
}
"""

BIB_SAME_DOI_B = """@article{beta2024,
  title = {Shared DOI Entry Two},
  doi = {10.7777/same},
  year = {2024}
}
"""


def _vault(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas")
    init_git(tmp_path, "bulk@example.invalid", "Bulk Import")
    return tmp_path


def _admit(vault: Path, payload: dict) -> dict:
    from memoria_vault.runtime.capture import stage_capture_payload

    return call_with_context(stage_capture_payload, vault, payload)


def test_detect_identifier_collisions_matches_arxiv_and_pmcid_exactly(
    tmp_path: Path,
) -> None:
    from memoria_vault.runtime.capture import bibtex_capture_payload

    vault = _vault(tmp_path)
    arxiv_work = _admit(vault, bibtex_capture_payload(BIB_DOI_ARXIV))["work_id"]
    pmc_work = _admit(vault, bibtex_capture_payload(BIB_PMCID))["work_id"]

    # A DOI-less entry keyed by citekey carrying an admitted work's arXiv id.
    assert detect_identifier_collisions(vault, "citekey-2025", {"arxiv": "2411.14199"}) == [
        {"other_work_id": arxiv_work, "field": "arxiv"}
    ]
    assert detect_identifier_collisions(vault, "citekey-2025", {"pmcid": "PMC7399101"}) == [
        {"other_work_id": pmc_work, "field": "pmcid"}
    ]
    # Self-match is excluded: the admitted row is not its own duplicate.
    assert detect_identifier_collisions(vault, arxiv_work, {"arxiv": "2411.14199"}) == []
    # Exact means exact -- no partial or near matches.
    assert detect_identifier_collisions(vault, "other", {"arxiv": "2411.9999"}) == []
    # DOI is never a triage field (structural dedupe / UNIQUE edge own it).
    assert detect_identifier_collisions(vault, "other", {"doi": "10.1234/admitted"}) == []
    # No catalog DB at all -> no collisions, no crash.
    assert detect_identifier_collisions(tmp_path / "nowhere", "w", {"arxiv": "1"}) == []


def test_doi_unique_collision_raises_and_is_classified(tmp_path: Path) -> None:
    from memoria_vault.runtime.capture import csl_capture_payload

    vault = _vault(tmp_path)
    first = csl_capture_payload(
        {"id": "alpha-2020", "type": "article-journal", "title": "Alpha", "DOI": "10.9999/dup"},
        raw_text="{}",
    )
    _admit(vault, first)

    # A cross-derivation insert: different work_id (CSL id-keyed), same DOI.
    second = csl_capture_payload(
        {"id": "beta-2021", "type": "article-journal", "title": "Beta", "DOI": "10.9999/dup"},
        raw_text="{}",
    )
    with pytest.raises(sqlite3.IntegrityError) as excinfo:
        _admit(vault, second)

    # The worker records str(exc) as the job error (worker.py:224-226);
    # the classifier keys on the column sqlite3 names.
    assert is_doi_collision_error(str(excinfo.value))
    assert not is_doi_collision_error("UNIQUE constraint failed: catalog_sources.work_id")
    assert not is_doi_collision_error("capture refusal: no text")
    # The first row survives untouched.
    assert state.catalog_source(vault, "alpha-2020") is not None
    assert len(state.catalog_sources(vault, checked_only=False)) == 1


def test_same_doi_entries_collapse_structurally_to_one_row(tmp_path: Path) -> None:
    """Spec section 5: same DOI => same work_id => the section-2 skip path.

    Both fixture entries derive one work_id (DOI lowercased,
    _bibtex_default_work_id capture.py:667-673); after the first admits,
    the driver's pre-check (state.catalog_source) hits for the second --
    reported skipped, never a judgment row. One catalog row results.
    """
    from memoria_vault.runtime.capture import bibtex_capture_payload

    vault = _vault(tmp_path)
    first = bibtex_capture_payload(BIB_SAME_DOI_A)
    second = bibtex_capture_payload(BIB_SAME_DOI_B)

    assert first["work_id"] == second["work_id"] == "doi-10.7777/same"

    _admit(vault, first)

    # The pre-check hit that makes the driver skip the second entry.
    assert state.catalog_source(vault, second["work_id"]) is not None
    assert len(state.catalog_sources(vault, checked_only=False)) == 1
    # And the skipped entry raises no cross-identifier judgment row.
    assert detect_identifier_collisions(
        vault, second["work_id"], second["identifiers"]
    ) == []
```

- [ ] **Step 2: Run and watch it fail** — `python -m pytest tests/test_bulk_import.py -v` → collection error: `ImportError: cannot import name 'detect_identifier_collisions' from 'memoria_vault.runtime.bulk_import'`.

- [ ] **Step 3: Minimal implementation** — in `src/memoria_vault/runtime/bulk_import.py`, add to the imports:

```python
from pathlib import Path

from memoria_vault.runtime import state
```

and append:

```python
_DUPLICATE_IDENTIFIER_FIELDS = ("arxiv", "pmcid")


def detect_identifier_collisions(
    vault: Path, work_id: str, identifiers: dict[str, Any]
) -> list[dict[str, str]]:
    """Exact arXiv/PMCID matches against other catalog rows (admit-then-flag).

    work_id is the admitted row id as returned by the capture result
    (already normalized), so self-exclusion is plain equality. The scan is
    a full-catalog Python loop over the shipped identifiers_json payloads
    via state.catalog_sources -- honest O(N) at beta.1's 100-work ceiling.
    No similarity scoring; DOI is owned by structural dedupe and the
    UNIQUE edge, never flagged here.
    """
    wanted = {
        field: str(identifiers.get(field) or "").strip()
        for field in _DUPLICATE_IDENTIFIER_FIELDS
    }
    if not any(wanted.values()):
        return []
    collisions: list[dict[str, str]] = []
    for row in state.catalog_sources(vault, checked_only=False):
        if row["work_id"] == work_id:
            continue
        other = row["identifiers"] if isinstance(row["identifiers"], dict) else {}
        for field, value in wanted.items():
            if value and value == str(other.get(field) or "").strip():
                collisions.append({"other_work_id": row["work_id"], "field": field})
    return collisions


def is_doi_collision_error(error: str) -> bool:
    """True for the doi-UNIQUE edge (schema.sql:101) surfaced as job-error text.

    A cross-derivation insert with a colliding DOI raises
    sqlite3.IntegrityError('UNIQUE constraint failed: catalog_sources.doi')
    out of stage_capture_payload; the worker records it verbatim as the
    failed job's error (worker.py:224-226). The driver uses this to record
    the entry failed-and-flagged duplicate -- named row, iteration
    continues, no schema reshape, no crash.
    """
    return "catalog_sources.doi" in str(error)
```

- [ ] **Step 4: Run to pass** — `python -m pytest tests/test_bulk_import.py -v` → 17 passed.

- [ ] **Step 5: Section-final gate** — `python scripts/verify` → green (lint, product gates, tests, offline smoke, syntax). This is the one gate; fix anything it names before committing.

- [ ] **Step 6: Commit** —

```
git add src/memoria_vault/runtime/bulk_import.py tests/test_bulk_import.py
git commit -m "feat(bulk-import): exact-identifier duplicate detection + doi-UNIQUE failure classifier

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

# Section W — Bulk artifacts, telemetry, registry, protocol (spec §3, §6, §7, §8; slices 5–8)

This section lands the bulk-admission artifacts (spec §3: the `emit_worklist` raised_by/loudness seam co-change and the one run-scoped quiet worklist per run), the `import-run.v1` instrumentation row (spec §6), the `staged-import` decision-rule registry entry (spec §7), and the Phase 1 staged-run protocol block (spec §6 protocol-level rows, §7 stop rule, §8 beta.2 ceiling — nothing here assumes corpus sizes beyond the 100-work stage).

**Cross-plan preconditions (binding, from the plan header):** implementation may not begin until the I1 plan (`docs/superpowers/plans/2026-07-16-i1-full-wiring.md`) is implemented and merged. W.2 consumes I1 T.2's `runtime/telemetry.py` and W.3 consumes I1 H.3's seeded `decision-rules.yaml` + `tests/test_decision_rules.py` — both tasks open with a grep-first check and a stop-note. The O1 resolve layer (`runtime/seed_install.py resolve_fetch(row, *, opener)`, O1 plan M.2) is consumed by this plan's driver/adapter sections, not by Section W. All shipped line refs below are verified at `51395f15`; re-anchor by symbol if drifted.

**Driver stitches (for the plan assembler):** the slice-2 driver task calls `emit_import_worklist(...)` at most once per run (W.1's seam — zero judgment rows ⇒ it returns `None`, no worklist, no card) and calls `record_telemetry_event(vault, "import-run.v1", row)` exactly once per run, after the timed post-loop index refresh (W.2's seam). The acceptance criterion's *nonzero* `index_refresh_s` is a driver-section assertion; W.2's validator honestly allows `>= 0`.

No new test files in this section: `tests/test_worklists.py` (`tests/conftest.py:120`, `contract`) and `tests/test_empirical_events.py` (`tests/conftest.py:42`, `contract`) are shipped-registered; `tests/test_telemetry_events.py` and `tests/test_decision_rules.py` are created and registered by the I1 plan (T.2, H.3). No `TEST_LEVELS` change here.

### Task W.1: `emit_worklist` raised_by/loudness passthrough + the run-scoped import worklist (spec §3; slice 5)

**Files:**
- Modify: `src/memoria_vault/runtime/subsystems/lib/worklists.py` (`emit_worklist` signature `worklists.py:63-70`; hardcoded `raised_by="worklists"` at `:133` and `loudness="notice"` at `:135`; append `emit_import_worklist`)
- Test: `tests/test_worklists.py` (extend — already registered `"test_worklists.py": "contract"` at `tests/conftest.py:120`; the shipped test at `tests/test_worklists.py:49` pins `raised_by == "worklists"` for default callers and stays green, proving the defaults are today's values)

**Interfaces:**
- Consumes: `inbox.write_work_prompt(vault, title, action, what_happened, raised_by, target="", request_id="", posture="", loudness="notice", dedupe_slug="", prompt_kind="") -> Path | None` (`runtime/subsystems/lib/inbox.py:116-128` — both params already exist there and land in card frontmatter at `inbox.py:157`; the co-change is confined to `emit_worklist`). Shipped empty refusal `raise ValueError("a worklist needs at least one row")` (`worklists.py:78`). Shipped `_item_ref` fallback order including `citekey` (`worklists.py:38-43`) — failed rows carry `citekey` or an `entry-<index>` `item_ref`, per spec §3 (failed entries have no work_id). `inbox.LOUDNESS` includes `"quiet"` (`inbox.py:22`). The `raised_by="import"` producer key is what I1's `producer_mode(vault, raised_by)` throttle map (`attention.yaml` `producers:` map, I1 contract 5) governs for bulk runs.
- Produces: `emit_worklist(vault: Path, title: str, rows: list[dict[str, Any]], source_report: str = "", workflow: str = "screen", worklist_id: str = "", raised_by: str = "worklists", loudness: str = "notice") -> dict[str, Any]`; `emit_import_worklist(vault: Path, *, run_id: str, rows: list[dict[str, Any]], entries_total: int, admitted: int) -> dict[str, Any] | None` — the driver-facing seam: worklist id `import-<run_id>` (run-scoped, successive runs never collide), rows ranked duplicates → retraction → failed → unmapped, one quiet card with honest denominators in its title, `None` on an empty judgment set (no worklist, no card — the shipped empty refusal is respected, never reached).

- [ ] **Step 1: Write the failing tests** — append to `tests/test_worklists.py`:

```python
def test_emit_worklist_passes_raised_by_and_loudness_through(tmp_path):
    worklists.emit_worklist(
        tmp_path,
        "Bulk import batch",
        [{"title": "One", "item_ref": "doi-10.1234/x"}],
        raised_by="import",
        loudness="quiet",
    )

    [prompt] = list((tmp_path / "inbox").glob("work-prompt-*.md"))
    fm = _frontmatter(prompt)
    assert fm["raised_by"] == "import"
    assert fm["loudness"] == "quiet"


def test_emit_import_worklist_ranks_duplicates_first_with_honest_denominators(tmp_path):
    result = worklists.emit_import_worklist(
        tmp_path,
        run_id="20260717-a1b2",
        rows=[
            {"title": "Unmappable entry type", "item_ref": "misc-1", "group": "unmapped"},
            {"title": "Malformed entry", "citekey": "broken2024", "group": "failed"},
            {
                "title": "Enrichment-surfaced retraction",
                "item_ref": "doi-10.1234/z",
                "group": "retraction",
            },
            {
                "title": "Cross-identifier duplicate",
                "item_ref": "doi-10.1234/y",
                "group": "duplicate",
                "reason": "arXiv id matches admitted work doi-10.1234/q",
            },
            {"title": "Parse error at entry 7", "item_ref": "entry-7", "group": "failed"},
        ],
        entries_total=10,
        admitted=6,
    )

    assert result is not None
    assert result["worklist"] == "import-20260717-a1b2"
    by_rank = {}
    for path in result["items"]:
        fm = _frontmatter(path)
        by_rank[fm["rank"]] = (fm["group"], fm["item_ref"])
    assert by_rank == {
        1: ("duplicate", "doi-10.1234/y"),
        2: ("retraction", "doi-10.1234/z"),
        3: ("failed", "broken2024"),
        4: ("failed", "entry-7"),
        5: ("unmapped", "misc-1"),
    }
    [prompt] = list((tmp_path / "inbox").glob("work-prompt-*.md"))
    fm = _frontmatter(prompt)
    assert fm["raised_by"] == "import"
    assert fm["loudness"] == "quiet"
    for denominator in ("10 entries", "6 admitted", "5 need judgment"):
        assert denominator in fm["title"]


def test_emit_import_worklist_empty_judgment_set_mints_nothing(tmp_path):
    result = worklists.emit_import_worklist(
        tmp_path, run_id="20260717-c3d4", rows=[], entries_total=4, admitted=4
    )

    assert result is None
    assert not (tmp_path / "system" / "worklists").exists()
    assert not (tmp_path / "inbox").exists()
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest tests/test_worklists.py -v`
Expected: FAIL — `TypeError: emit_worklist() got an unexpected keyword argument 'raised_by'` and `AttributeError: module 'memoria_vault.runtime.subsystems.lib.worklists' has no attribute 'emit_import_worklist'`. The five shipped tests stay green.

- [ ] **Step 3: Implement.** Replace `emit_worklist` (`worklists.py:63-138`) with (body unchanged except the signature and the two previously hardcoded kwargs) and append `emit_import_worklist` directly after it:

```python
def emit_worklist(
    vault: Path,
    title: str,
    rows: list[dict[str, Any]],
    source_report: str = "",
    workflow: str = "screen",
    worklist_id: str = "",
    raised_by: str = "worklists",
    loudness: str = "notice",
) -> dict[str, Any]:
    """Write a file-backed worklist and one aggregate work-prompt.

    Returns the worklist slug, item paths, and the prompt path (or None when the
    deduped prompt already existed). Rows may contain title/name, item_ref/target,
    group, decision, rank, and reason.
    """
    if not rows:
        raise ValueError("a worklist needs at least one row")
    vault = Path(vault)
    slug = _slug(worklist_id or title)
    safe_title = neutralize_untrusted_markdown_fragment(title)
    worklist_dir = vault / "system" / "worklists" / slug
    worklist_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()
    item_paths: list[Path] = []

    for index, row in enumerate(rows, start=1):
        ref = _item_ref(row, index)
        item_title = _item_title(row, ref)
        safe_item_title = neutralize_untrusted_markdown_fragment(item_title)
        safe_ref = neutralize_untrusted_markdown_fragment(ref)
        decision = str(row.get("decision") or "proposed").strip()
        if decision not in DECISIONS:
            raise ValueError(f"decision must be one of {DECISIONS}")
        rank = int(row.get("rank") or index)
        group = str(row.get("group") or row.get("category") or workflow).strip()
        reason = str(row.get("reason") or row.get("evidence") or "").strip()
        safe_reason = neutralize_untrusted_markdown(reason)
        item_source = str(row.get("source_report") or source_report).strip()
        item_slug = _slug(f"{rank:03d}-{item_title}")
        path = worklist_dir / f"{item_slug}.md"
        frontmatter = {
            "title": safe_item_title,
            "projection": "worklist-item",
            "attention_status": "open",
            "decision": decision,
            "worklist": slug,
            "item_ref": ref,
        }
        if item_source:
            frontmatter["source_report"] = item_source
        if group:
            frontmatter["group"] = group
        frontmatter.update({"rank": rank, "created": today})
        body = [f"# {safe_item_title}", "", f"Reference: {markdown_code_span(safe_ref)}", ""]
        if safe_reason:
            body += ["# Reason", "", safe_reason, ""]
        write_text_durable(path, frontmatter_doc(frontmatter, "\n".join(body)))
        item_paths.append(path)

    target = f"system/worklists/{slug}/"
    prompt = inbox.write_work_prompt(
        vault,
        title=f"Review worklist: {safe_title}",
        action=(
            "Open the worklist folder, review the grouped rows, and set each "
            "item's decision to include, exclude, maybe, or archived."
        ),
        what_happened=neutralize_untrusted_markdown(
            f"{len(item_paths)} items were emitted into the {slug} "
            f"batch from {source_report or 'a report'}."
        ),
        raised_by=raised_by,
        target=target,
        loudness=loudness,
        dedupe_slug=f"worklist-{slug}",
    )
    return {"worklist": slug, "items": item_paths, "prompt": prompt}


IMPORT_GROUP_ORDER = ("duplicate", "retraction", "failed", "unmapped")


def emit_import_worklist(
    vault: Path,
    *,
    run_id: str,
    rows: list[dict[str, Any]],
    entries_total: int,
    admitted: int,
) -> dict[str, Any] | None:
    """Mint the one run-scoped bulk-admission worklist, or nothing at all.

    An empty judgment set mints no worklist and no card (the shipped empty
    refusal above is respected, never reached). Rows rank duplicates first,
    then retraction flags, then failed rows (item refs are citekeys or entry
    indexes — failed entries have no work_id), then unknown-mapping rows.
    The one quiet card carries honest denominators in its title.
    """
    if not rows:
        return None
    order = {group: position for position, group in enumerate(IMPORT_GROUP_ORDER)}
    fallback = len(IMPORT_GROUP_ORDER)

    def _rank_key(pair: tuple[int, dict[str, Any]]) -> tuple[int, int]:
        index, row = pair
        return order.get(str(row.get("group") or ""), fallback), index

    ranked = sorted(enumerate(rows), key=_rank_key)
    judged = [{**row, "rank": rank} for rank, (_, row) in enumerate(ranked, start=1)]
    title = (
        f"Import run {run_id}: {entries_total} entries · {admitted} admitted · "
        f"{len(judged)} need judgment"
    )
    return emit_worklist(
        vault,
        title,
        judged,
        source_report=f"import run {run_id}",
        workflow="import",
        worklist_id=f"import-{run_id}",
        raised_by="import",
        loudness="quiet",
    )
```

(The honest denominators live in the card **title**: `emit_worklist` composes `what_happened` itself, and widening the co-change with a message passthrough would exceed the seam the spec names — SPEC GAP resolved, recorded for review. This is producer behavior only; I1 §6's no-withholding invariant is untouched, and the card's `attention-admitted` flow telemetry is emitted by I1's admission wiring as normal — worklist *row* volume rides `import-run.v1` counts, not per-row flow events.)

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest tests/test_worklists.py -v`
Expected: PASS — all eight tests, including the shipped `raised_by == "worklists"` default pin at `tests/test_worklists.py:49`.

- [ ] **Step 5: Commit**

```bash
git add src/memoria_vault/runtime/subsystems/lib/worklists.py tests/test_worklists.py
git commit -m "feat(worklists): raised_by/loudness passthrough + run-scoped quiet import worklist (O2 spec §3)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task W.2: `import-run.v1` — typed validator + telemetry dispatch (spec §6; slice 6)

**Files:**
- Modify: `src/memoria_vault/engine/empirical_events.py` (append the `import-run.v1` constants after `READ_REQUIRED_FIELDS`, `empirical_events.py:101`, and the validator after `validate_read_event`, `:168-184`), `src/memoria_vault/runtime/telemetry.py` (`_validated` dispatch — I1 T.2's module)
- Test: `tests/test_empirical_events.py` (extend; registered `contract` at `tests/conftest.py:42`), `tests/test_telemetry_events.py` (extend; created and registered `contract` by I1 T.2)

**Interfaces:**
- Consumes: I1 T.2's `record_telemetry_event(vault: Path, event_type: str, payload: dict[str, Any]) -> str` and its `_validated` dispatch (`runtime/telemetry.py`); I1 T.1's `telemetry_events` table (columns `event_id, ts, event_type, session_id, surface, payload_json`); shipped private helpers `_missing` (`empirical_events.py:187`), `_string_field` (`:198`), `_reject_pathlike` (`:236`); `state.connect` bootstraps the schema on a bare `tmp_path` vault (`state.py:472-481`), so tests need no init and no network.
- Produces: `empirical_events.IMPORT_RUN_EVENT_SCHEMA = "import-run.v1"`; `empirical_events.validate_import_run_event(payload: dict[str, Any]) -> dict[str, Any]` — its own `IMPORT_RUN_REQUIRED_FIELDS` (the `edge-write.v1` pattern, graph plan ERP-D.6: a separate validator so integer fields are legal — `validate_empirical_event`'s `ALLOWED_FIELDS`/string coercion cannot carry counts); the `_validated` branch making `record_telemetry_event(vault, "import-run.v1", row)` a working call. Row shape (spec §6): `{run_id, format, entries_total, admitted, skipped, failed, duplicates_flagged, retraction_flags, duration_s, index_refresh_s}` — `run_id` an opaque string, `format ∈ {bibtex, csl}`, the six counts non-negative `int`s (bool rejected), the two timings non-negative numerics. One row per run, emitted by the driver after the timed post-loop index refresh (driver stitch, slice-2 task).

- [ ] **Step 1: Grep-first (order tolerance).** Run `grep -n "_validated\|edge-write.v1" src/memoria_vault/runtime/telemetry.py`. If the file is absent, the plan header's precondition is unmet — **STOP: land and merge the I1 plan (2026-07-16-i1-full-wiring.md, T.1/T.2) first.** If present but the `edge-write.v1` branch is absent (graph-plan ordering), insert the new branch in the same position relative to the native-fields fallback; anchor by symbol, not line.

- [ ] **Step 2: Write the failing tests** — append to `tests/test_empirical_events.py`:

```python
def _import_run_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "run_id": "import-20260717-a1b2",
        "format": "bibtex",
        "entries_total": 13,
        "admitted": 9,
        "skipped": 1,
        "failed": 2,
        "duplicates_flagged": 1,
        "retraction_flags": 0,
        "duration_s": 41.5,
        "index_refresh_s": 3.2,
    }
    row.update(overrides)
    return row


def test_validate_import_run_event_normalizes_one_row_per_run() -> None:
    from memoria_vault.engine.empirical_events import (
        IMPORT_RUN_EVENT_SCHEMA,
        validate_import_run_event,
    )

    assert IMPORT_RUN_EVENT_SCHEMA == "import-run.v1"
    event = validate_import_run_event(_import_run_row())
    assert event == _import_run_row()
    assert isinstance(event["entries_total"], int)
    assert isinstance(event["duration_s"], float)


def test_validate_import_run_event_rejects_bad_shapes() -> None:
    from memoria_vault.engine.empirical_events import validate_import_run_event

    with pytest.raises(ValueError, match="admitted must be an integer"):
        validate_import_run_event(_import_run_row(admitted=True))
    with pytest.raises(ValueError, match="entries_total must be an integer"):
        validate_import_run_event(_import_run_row(entries_total=13.0))
    with pytest.raises(ValueError, match="failed must be >= 0"):
        validate_import_run_event(_import_run_row(failed=-1))
    with pytest.raises(ValueError, match="format must be one of"):
        validate_import_run_event(_import_run_row(format="ris"))
    with pytest.raises(ValueError, match="missing required fields: run_id"):
        validate_import_run_event(
            {key: value for key, value in _import_run_row().items() if key != "run_id"}
        )
    with pytest.raises(ValueError, match="unsupported fields: verdict"):
        validate_import_run_event(_import_run_row(verdict="clean"))
    with pytest.raises(ValueError, match="opaque id"):
        validate_import_run_event(_import_run_row(run_id="../escape"))
    with pytest.raises(ValueError, match="index_refresh_s must be numeric"):
        validate_import_run_event(_import_run_row(index_refresh_s="3.2"))
```

And append to `tests/test_telemetry_events.py` (I1 T.2's file — it already imports `Path` and `pytest`; keep the runtime imports function-local, matching its style):

```python
def test_record_telemetry_event_routes_import_run_through_its_validator(tmp_path: Path) -> None:
    import json

    from memoria_vault.runtime import state
    from memoria_vault.runtime.telemetry import record_telemetry_event

    row = {
        "run_id": "import-20260717-a1b2",
        "format": "csl",
        "entries_total": 3,
        "admitted": 2,
        "skipped": 1,
        "failed": 0,
        "duplicates_flagged": 0,
        "retraction_flags": 0,
        "duration_s": 4.2,
        "index_refresh_s": 0.8,
    }

    event_id = record_telemetry_event(tmp_path, "import-run.v1", row)

    with state.connect(tmp_path) as conn:
        stored = conn.execute(
            "SELECT event_type, payload_json FROM telemetry_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
    assert stored["event_type"] == "import-run.v1"
    assert json.loads(stored["payload_json"]) == row

    with pytest.raises(ValueError, match="admitted must be an integer"):
        record_telemetry_event(tmp_path, "import-run.v1", {**row, "admitted": True})
```

- [ ] **Step 3: Run to verify failure**

Run: `python -m pytest tests/test_empirical_events.py tests/test_telemetry_events.py -v`
Expected: FAIL — `ImportError: cannot import name 'IMPORT_RUN_EVENT_SCHEMA'` in the first two tests; the dispatch test fails with `ValueError: unknown telemetry event type: import-run.v1`.

- [ ] **Step 4: Implement.** In `src/memoria_vault/engine/empirical_events.py`, append after `READ_REQUIRED_FIELDS` (`:101`):

```python
IMPORT_RUN_EVENT_SCHEMA = "import-run.v1"
IMPORT_RUN_FORMATS = frozenset({"bibtex", "csl"})
IMPORT_RUN_COUNT_FIELDS = (
    "entries_total",
    "admitted",
    "skipped",
    "failed",
    "duplicates_flagged",
    "retraction_flags",
)
IMPORT_RUN_TIMING_FIELDS = ("duration_s", "index_refresh_s")
IMPORT_RUN_REQUIRED_FIELDS = frozenset(
    {"run_id", "format", *IMPORT_RUN_COUNT_FIELDS, *IMPORT_RUN_TIMING_FIELDS}
)
```

Append after `validate_read_event` (`:168-184`):

```python
def validate_import_run_event(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a normalized per-run bulk-import event or raise ``ValueError``.

    One row per import run (O2 spec §6): analytics-only, routed to the
    telemetry table — never the journal. Counts are integers; timings are
    non-negative numerics (whole-index refresh time until LOOP.1 lands).
    """
    if not isinstance(payload, dict):
        raise ValueError("import-run event payload must be an object")
    unknown = sorted(set(payload) - IMPORT_RUN_REQUIRED_FIELDS)
    if unknown:
        raise ValueError(f"import-run event contains unsupported fields: {', '.join(unknown)}")
    missing = sorted(field for field in IMPORT_RUN_REQUIRED_FIELDS if _missing(payload.get(field)))
    if missing:
        raise ValueError(f"import-run event missing required fields: {', '.join(missing)}")
    run_id = _string_field("run_id", payload["run_id"])
    _reject_pathlike("run_id", run_id)
    entry_format = _string_field("format", payload["format"])
    if entry_format not in IMPORT_RUN_FORMATS:
        raise ValueError(f"format must be one of: {', '.join(sorted(IMPORT_RUN_FORMATS))}")
    event: dict[str, Any] = {"run_id": run_id, "format": entry_format}
    for field in IMPORT_RUN_COUNT_FIELDS:
        event[field] = _count_field(field, payload[field])
    for field in IMPORT_RUN_TIMING_FIELDS:
        event[field] = _elapsed_field(field, payload[field])
    return event
```

And append beside the existing private helpers (`:187-244`):

```python
def _count_field(field: str, value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must be >= 0")
    return value


def _elapsed_field(field: str, value: Any) -> float | int:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    if value < 0:
        raise ValueError(f"{field} must be >= 0")
    return value
```

In `src/memoria_vault/runtime/telemetry.py`, insert into `_validated` directly after the `edge-write.v1` branch (anchor by symbol — the I1 T.2 branch stack reads `EMPIRICAL_EVENT_SCHEMA` → `READ_EVENT_SCHEMA` → `edge-write.v1` → native-fields fallback):

```python
    if event_type == "import-run.v1" and hasattr(schemas, "validate_import_run_event"):
        return schemas.validate_import_run_event(payload)
```

(The `hasattr` guard is the file's guarded-absence house pattern for cross-plan branches; both halves land in this one commit, so it is order-tolerance parity, and an early call before this commit gets the honest `unknown telemetry event type` error.)

- [ ] **Step 5: Run to verify pass**

Run: `python -m pytest tests/test_empirical_events.py tests/test_telemetry_events.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/memoria_vault/engine/empirical_events.py src/memoria_vault/runtime/telemetry.py \
    tests/test_empirical_events.py tests/test_telemetry_events.py
git commit -m "feat(telemetry): import-run.v1 typed validator + dispatch, one analytics row per bulk run (O2 spec §6)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task W.3: `staged-import` decision-rule registry entry (spec §7; slice 7)

**Files:**
- Modify: `src/memoria_vault/product/workspace_seed/.memoria/config/decision-rules.yaml` (append one entry after the seeded file's final row, `id: canvas-authoring`), `tests/test_decision_rules.py` (extend; created and registered `contract` by I1 H.3)

**Interfaces:**
- Consumes: I1 H.3's seeded registry (entry shape `{id, blocker, metric, window, threshold, recommendation, check: auto|manual, status: armed|fired|retired}`), `load_decision_rules(vault) -> list[dict]`, and its pinned count tests — `test_seed_registers_all_sixteen_rules_with_four_auto` (`assert len(rules) == 16`) and `test_malformed_entry_is_skipped_not_fatal` (`assert len(rules) == 16`). Firing and retiring follow the I1 registry semantics (`update_rule_status`); a `manual` rule renders as an armed reminder — no evaluator change.
- Produces: the `staged-import` registry entry (`check: manual`, `status: armed`) with the spec §7 wording verbatim in `recommendation`; the seeded count moves 16 → 17.

- [ ] **Step 1: Grep-first (hard blocker).** Run `grep -n "canvas-authoring" src/memoria_vault/product/workspace_seed/.memoria/config/decision-rules.yaml && grep -n "== 16" tests/test_decision_rules.py`. **If either file is absent, this task BLOCKS: the I1 plan (2026-07-16-i1-full-wiring.md H.3) has not been executed and merged — the plan header's precondition is unmet. STOP and land I1 first; do not create these files here** (H.3 owns the sixteen-entry seed, the loader, and the conftest registration).

- [ ] **Step 2: Write the failing tests.** In `tests/test_decision_rules.py`, make three named edits: (a) rename `test_seed_registers_all_sixteen_rules_with_four_auto` to `test_seed_registers_all_seventeen_rules_with_four_auto`, change its `assert len(rules) == 16` to `assert len(rules) == 17`, and add `"staged-import"` to its id-superset assertion set; (b) in `test_malformed_entry_is_skipped_not_fatal`, change `assert len(rules) == 16   # the incomplete entry is dropped` to `assert len(rules) == 17   # the incomplete entry is dropped`; (c) append:

```python
def test_staged_import_rule_is_seeded_manual_and_armed(tmp_path: Path) -> None:
    vault = _vault_with_registry(tmp_path)

    rules = {rule["id"]: rule for rule in load_decision_rules(vault)}

    rule = rules["staged-import"]
    assert rule["check"] == "manual"
    assert rule["status"] == "armed"
    assert rule["recommendation"] == (
        "After each stage (10 works, then 100): if the run's triage worklist did not fit "
        "one session, or rebuild/query latency broke the session's flow, stop the protocol "
        "and record the observation in the diary and this rule — the observation IS the "
        "finding."
    )
    assert "import-run" in rule["metric"]
    assert "Shape-1/Shape-2 query latency" in rule["metric"]
```

- [ ] **Step 3: Run to verify failure**

Run: `python -m pytest tests/test_decision_rules.py -v`
Expected: FAIL — the renamed count test asserts `17` against 16 loaded rules; the new test fails with `KeyError: 'staged-import'`.

- [ ] **Step 4: Implement.** Append to `src/memoria_vault/product/workspace_seed/.memoria/config/decision-rules.yaml`, after the `canvas-authoring` entry (the `recommendation` carries the spec §7 rule wording verbatim; `threshold` restates the trigger clause and `metric` names the §6 rows plus the protocol-script measurements, both per H.3's manual-row convention and §7's own paragraph — SPEC GAP on blockquote→entry-shape mapping resolved inline, recorded for review):

```yaml
- id: staged-import
  blocker: "Staged import (O2 Phase 1 protocol)"
  metric: "import-run.duration_s / import-run.index_refresh_s / import-run.duplicates_flagged / import-run.retraction_flags; flow-panel attention-admitted counts; protocol-measured session-fit and Shape-1/Shape-2 query latency"
  window: "after each stage (10 works, then 100)"
  threshold: "the run's triage worklist did not fit one session, or rebuild/query latency broke the session's flow"
  recommendation: "After each stage (10 works, then 100): if the run's triage worklist did not fit one session, or rebuild/query latency broke the session's flow, stop the protocol and record the observation in the diary and this rule — the observation IS the finding."
  check: manual
  status: armed
```

- [ ] **Step 5: Run to verify pass**

Run: `python -m pytest tests/test_decision_rules.py -v`
Expected: PASS — 17 rules load, the four `auto` ids are unchanged, `staged-import` is `manual`/`armed` with the verbatim wording.

- [ ] **Step 6: Commit**

```bash
git add src/memoria_vault/product/workspace_seed/.memoria/config/decision-rules.yaml \
    tests/test_decision_rules.py
git commit -m "feat(decision-rules): pre-register the staged-import stop rule, seeded count 16 -> 17 (O2 spec §7)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

### Task W.4: The Phase 1 staged-run protocol block + section gate (spec §6 protocol rows, §7, §8; slice 8)

**Files:**
- Modify: none — this task is plan documentation plus the section gate. The recorded-metrics artifact (`docs/superpowers/specs/$(date +%F)-staged-import-acceptance-run.md`) is created **when the PI executes the protocol post-merge**, per LOOP.13 — never in this PR.
- Test: none — protocol run (LOOP.13 convention), then `python scripts/verify` closes the section.

**Interfaces:**
- Consumes: LOOP.13's amended acceptance block (`docs/superpowers/plans/2026-07-15-alpha23-usable-loop.md:2384-2503`) — its blocking preconditions (seeded-error battery green before any real-vault import; a fresh real vault, **never** `test-vault/`), its metrics document artifact, its ≤30-min/≤60-min bars, and its explicit supersession clause (`:2394-2397`: a shipped bulk command's plan supersedes the csplit loop body; measurements and bars stay). W.1's worklist, W.2's `import-run.v1` row, W.3's `staged-import` rule; the driver sections' `--enrich` flag (spec §2 flip) and run-scoped ids.
- Produces: the stage-1/stage-2 protocol block below — the documented shell block that replaces LOOP.13's per-entry loop body.

**Home decision (repo convention, verified):** LOOP.13 is the precedent — a staged protocol lives as documented shell steps inside a plan task ("This is not a pytest task: it is a measured protocol run on a real vault", alpha23 plan `:2398`), with a recorded-metrics spec doc as the run's artifact. No shipped script: nothing under `scripts/` carries protocol runs, and a script would imply a maintained product surface the doc-claims gate would then police. This block is therefore plan documentation, executed by the PI after this plan merges and LOOP.13's preconditions hold.

- [ ] **Step 1: Confirm the consumed pieces landed** (all in this section's commits):

Run: `grep -n "import-run.v1" src/memoria_vault/runtime/telemetry.py && grep -n "staged-import" src/memoria_vault/product/workspace_seed/.memoria/config/decision-rules.yaml && grep -n "emit_import_worklist" src/memoria_vault/runtime/subsystems/lib/worklists.py`
Expected: one hit each (W.2, W.3, W.1).

- [ ] **Step 2: The protocol block** (documentation — this text is the deliverable; it supersedes LOOP.13's csplit loop body, measurements and bars unchanged; beta.1 ceiling is the 100-work stage, spec §8 — 1000-scale is beta.2, nothing here may assume beyond it):

```bash
# ==== Phase 1 staged-run protocol (O2 spec §6/§7; supersedes LOOP.13's per-entry loop body) ====
# Preconditions (blocking, LOOP.13): I1 + this plan merged; battery green on the target vault.
VAULT="$HOME/memoria-beta1-vault"   # fresh real vault; NEVER test-vault/, never an existing personal vault
memoria eval seeded-error-verdict --workspace "$VAULT" --json \
  || { echo "BLOCKED: no real-vault import until the battery passes (empirical plan Phase 0)"; exit 1; }

# ---- Stage 1: 10 works (stage1.bib exported from Zotero as generic BibTeX) ----
# One bulk call per stage; --enrich is deliberate: this stage wants provider-load
# measurements (spec §2 — default is off, keyless-first).
memoria work import --workspace "$VAULT" --format bibtex --file stage1.bib --enrich --json \
  | tee stage1-import.json

# Product-side record: the run's one import-run.v1 row (duration_s, index_refresh_s, counts).
sqlite3 "$VAULT/.memoria/memoria.sqlite" \
  "SELECT payload_json FROM telemetry_events WHERE event_type='import-run.v1' ORDER BY ts DESC LIMIT 1;" \
  | tee -a staged-import-metrics.txt

# Query timing (protocol-level, spec §6 — honestly a protocol measurement, not a product event).
# Shape-1/Shape-2 definitions come from the R2/LOOP.7 spec; fall back to the two literals below.
time memoria ask --workspace "$VAULT" --question "targeted lookup: <Shape-1 query from the R2 spec>" --json
time memoria ask --workspace "$VAULT" --question "topic surfacing: <Shape-2 query from the R2 spec>" --json
time memoria project explore --workspace "$VAULT" --limit 10 --json
# >200 ms interactive at any stage triggers the substrate re-comparison early
# (query-mechanism-analysis §5) — record it either way.

# Store sizing (protocol-level, spec §6: journal/DB growth per stage).
sqlite3 "$VAULT/.memoria/memoria.sqlite" "SELECT COUNT(*) FROM event_log;" \
  | xargs -I{} echo "stage1_event_log_rows={}" | tee -a staged-import-metrics.txt
du -sh "$VAULT/.memoria" | tee -a staged-import-metrics.txt

# Triage: the ONE run-scoped worklist (import-<run_id>) inside one bounded batch (<= 60 min).
memoria attention worklist --workspace "$VAULT" --json | tee stage1-worklist.json
# Resolve every row via:
#   memoria attention resolve --workspace "$VAULT" <path> --apply|--reject|--defer --reason "<why>"
# timing the batch; record triage minutes and whether it fit the session.

# Stop-rule check (the staged-import registry entry, W.3 — check: manual): if the worklist
# did not fit one session, or rebuild/query latency broke the session's flow, STOP the
# protocol here: record the observation in the diary AND flip the rule to status: fired in
# "$VAULT/.memoria/config/decision-rules.yaml". The observation IS the finding.

# ---- Stage 2: 100 works ----
# Repeat the whole stage block with stage2.bib (100 entries). A re-run after an interruption
# is safe: the catalog pre-check skips admitted works, mints no second worklist and no card,
# and exits clean (spec §2/§3). The recorded metrics land in LOOP.13's artifact:
# docs/superpowers/specs/$(date +%F)-staged-import-acceptance-run.md
# ---- Ceiling: 100 works. The 1000-scale seed-corpus-load run is beta.2 (spec §8). ----
```

- [ ] **Step 3: Section gate**

Run: `python scripts/verify`
Expected: exit 0 — lint, product gates (including the doc-claims gate: no new CLI surface beyond the existing `work import` flags plus `--enrich`, spec §10), tests, offline smoke, syntax all green.

- [ ] **Step 4: No commit from this task.** W.1–W.3 committed every file this section touches; this plan document merges with its own PR, and the acceptance-run record is the PI's post-merge artifact (LOOP.13), never authored here.