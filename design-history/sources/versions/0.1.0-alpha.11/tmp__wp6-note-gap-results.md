# WP6 Note/Gap Slice Results

Timestamp: 2026-06-29T05:59:18Z

Scope: first WP6 implementation slice for note candidates and deterministic gap
classification:

- `emit_note_candidates()` reads a checked `digest`, records `run` and
  `model_call` events, writes candidate `note` Concepts through the trusted
  writer, promotes them to `check_status: checked`, and commits notes plus
  journal together;
- machine-proposed notes carry `status: candidate`; `curate_note_candidate()`
  records PI accept/reject disposition by updating checked candidates to
  `status: accepted` or `status: rejected` and committing the note plus journal
  together;
- direct PI text edits to a candidate note are backfilled through the
  `observe_pi_edit_from_head()` path, rechecked with the `mark-checked` worker
  operation, and can then be accepted through `curate_note_candidate()` without
  renaming or losing the edited note;
- `curate_note_link()` records PI-authored `supports`, `contradicts`, or
  `extends` links by updating a checked note's typed `links` map and committing
  the note plus journal together;
- note candidates preserve caller-supplied `annotation_ref` maps, including the
  PDF fixture's source path, raw copy path, page, quoted span, and bbox selector;
- `analyze_gaps()` scans checked-current `source`, `digest`, and accepted
  `note` Concepts and classifies topic mismatches as `new-topic`, `undigested`,
  or `under-warranted`; balanced topics, below-threshold topics, unchecked
  Concepts, stale Concepts, and uncurated note candidates do not satisfy gap
  density; the worker exposes this as `analyze-gaps`;
- `analyze_project_argument()` follows checked, non-candidate note links around
  a checked project's `thesis` note and reports relation counts, argument
  stage, saturation conditions, confidence, gap findings, advisory findings,
  nodes, and edges; the worker exposes this as `analyze-project-argument`;
- `answer_query()` returns the deterministic Ask/Query contract over checked
  current BM25 hits: sources, unknowns, staleness, and contradictions;
- `capabilities/operations/propose-note-candidates.md` is the checked seed
  operation for this slice, and the worker exposes it as
  `propose-note-candidates`.

This is not the full WP6 runtime proof. The local WP6 contract is deterministic
checked-only Ask through `answer-query`; attended Obsidian use of that Ask
surface remains open product/runtime evidence.

Verification:

```bash
python -m pytest tests/test_knowledge.py
python -m ruff check src/memoria_vault/runtime/knowledge.py tests/test_knowledge.py
python -m ruff format --check src/memoria_vault/runtime/knowledge.py tests/test_knowledge.py
python -m pytest tests/test_search_index.py tests/test_qmd_filter_mcp.py
python -m ruff check src/memoria_vault/runtime/search_index.py tests/test_search_index.py
python -m ruff format --check src/memoria_vault/runtime/search_index.py tests/test_search_index.py
python -m pytest tests/test_knowledge.py tests/test_operations.py tests/test_capture.py tests/test_trusted_writer.py tests/test_worker_queue.py tests/test_search_index.py tests/test_qmd_filter_mcp.py tests/test_patterns.py tests/test_schemas.py tests/test_package_spine.py tests/test_installer_skeleton.py tests/test_detectors.py tests/test_quickadd.py tests/test_workspaces.py tests/test_modalforms.py tests/test_exploration_trace.py tests/test_hub_handoff.py tests/test_templates.py tests/test_bases.py tests/test_precommit_schema.py
python -m ruff check src/memoria_vault/runtime/knowledge.py src/memoria_vault/runtime/operations.py src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/search_index.py src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/worker.py src/memoria_vault/runtime/__init__.py tests/test_knowledge.py tests/test_operations.py tests/test_capture.py tests/test_trusted_writer.py tests/test_worker_queue.py tests/test_search_index.py tests/test_qmd_filter_mcp.py tests/test_patterns.py tests/test_schemas.py scripts/gen-forms.py scripts/gen_reference_refs.py
python -m ruff format --check src/memoria_vault/runtime/knowledge.py src/memoria_vault/runtime/operations.py src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/search_index.py src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/worker.py src/memoria_vault/runtime/__init__.py tests/test_knowledge.py tests/test_operations.py tests/test_capture.py tests/test_trusted_writer.py tests/test_worker_queue.py tests/test_search_index.py tests/test_qmd_filter_mcp.py tests/test_patterns.py tests/test_schemas.py scripts/gen-forms.py scripts/gen_reference_refs.py
python scripts/gen-forms.py --check
python scripts/gen_reference_refs.py --check
python scripts/docs_doctor.py docs
python scripts/agents_doctor.py --write
python scripts/agents_doctor.py
python scripts/status_doctor.py
bash -n scripts/install.sh scripts/install/manifest.sh
git diff --check
```

Result: all passed.
