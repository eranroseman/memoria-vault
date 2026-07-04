# WP3 Checked Index Slice Results

Timestamp: 2026-06-29T06:11:28Z

Scope: first WP3 implementation slice for the disposable checked-only search
index:

- `.memoria/index/qmd/` is part of the fresh skeleton and is gitignored except
  for `.gitkeep`;
- `rebuild_checked_qmd_source()` rebuilds a disposable qmd input tree under
  `.memoria/index/qmd/checked/` from current catalog/knowledge Concepts whose
  frontmatter has `check_status: checked`; capability Concepts are executable
  metadata and are not Ask/qmd content; stale `lifecycle` / `status` rows are
  hidden by default;
- `filter_checked_results()` applies the same read barrier to qmd-style JSON
  rows, so unchecked, quarantined, stale, missing, or non-Concept paths are
  dropped;
- `evaluate_bm25()` is a small stdlib BM25 baseline harness for later
  Ask/retrieval comparisons; it indexes only checked Concepts;
- `answer_query()` returns the deterministic Ask/Query answer contract over the
  BM25 baseline: `sources`, `unknowns`, `staleness`, and `contradictions`;
- the worker exposes the read-barrier helpers as `rebuild-checked-qmd-source`
  and `answer-query` jobs;
- `qmd_filter_mcp.py` now uses the checked-only read barrier instead of the old
  superseded-claim filter.

This is not the full Ask/retrieval implementation. Vector/hybrid qmd runs,
query expansion, reranking, and proof that hybrid beats BM25 stay in the later
retrieval eval track.

Verification:

```bash
python -m pytest tests/test_search_index.py tests/test_qmd_filter_mcp.py
python -m ruff check src/memoria_vault/runtime/search_index.py src/memoria_vault/runtime/__init__.py vault-template/.memoria/mcp/qmd_filter_mcp.py tests/test_search_index.py tests/test_qmd_filter_mcp.py
python -m ruff format --check src/memoria_vault/runtime/search_index.py src/memoria_vault/runtime/__init__.py vault-template/.memoria/mcp/qmd_filter_mcp.py tests/test_search_index.py tests/test_qmd_filter_mcp.py
python scripts/gen_reference_refs.py --write
python -m pytest tests/test_worker_queue.py tests/test_capabilities.py tests/test_search_index.py
python -m ruff check src/memoria_vault/runtime/worker.py src/memoria_vault/runtime/search_index.py tests/test_worker_queue.py tests/test_capabilities.py tests/test_search_index.py
python -m ruff format --check src/memoria_vault/runtime/worker.py src/memoria_vault/runtime/search_index.py tests/test_worker_queue.py tests/test_capabilities.py tests/test_search_index.py
```

Result: all passed.

## Reference and installer alignment update

Timestamp: 2026-06-29T11:51:14Z

Scope:

- removed the retired QuickAdd pre-file similarity telemetry from the current
  telemetry inventory/log-schema reference;
- changed qmd installer registration from the whole vault + optional vector
  embed to `.memoria/index/qmd/checked` with no vector prompt;
- updated the search rebuild how-to, Reference index, installer reference,
  integration reference, and methods catalog to state the checked-only BM25
  baseline and keep vector/hybrid work in the later eval track;
- corrected Peer-reviewer profile/skill prose so findings are worker-owned
  flag/gap attention projections and the profile has no direct Inbox write
  scope.

Verification:

```bash
bash -n scripts/install.sh scripts/install/*.sh
python -m pytest tests/test_search_index.py tests/test_worker_queue.py tests/test_profiles.py tests/test_skill_state_dashboard.py tests/test_installer_skeleton.py -q
python scripts/docs_doctor.py docs
python scripts/status_doctor.py
python scripts/agents_doctor.py
python scripts/gen_profiles_ref.py --check
git diff --check
```

Result: passed (`92 passed`; `git diff --check` emitted only the existing
`scripts/install.ps1` LF/CRLF warning).
