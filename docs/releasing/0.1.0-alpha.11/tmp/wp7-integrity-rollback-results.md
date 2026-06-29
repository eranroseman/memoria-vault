# WP7 Integrity Rollback Slice Results

Timestamp: 2026-06-29T05:35:06Z

Scope: first WP7 implementation slice for check routing and trace rollback:

- `check_evidence_integrity()` scans checked `digest` and `note` Concepts,
  flags unresolved `source_id`/`evidence_set` references, and flags checked
  evidence marked `lifecycle: retracted` or `archived` as `evidence-current`;
- `check_quote_anchor_support()` flags checked notes whose quoted span is absent
  from checked source text declared by `source_id`/`evidence_set`;
- `check_prompt_injection_markers()` flags checked sources, digests, or notes
  containing explicit prompt-injection marker text; it is a high-precision
  marker check, not semantic injection detection;
- `check_provenance_checkpoint()` flags checked notes or digests that depend on
  checked sources whose metadata is still partial, unverified, or not indexed;
  this is the deterministic provenance/risk checkpoint for fresh external
  source use, not semantic injection detection;
- `check_contradiction_links()` flags checked digests whose explicit
  `contradictions` targets are missing, unchecked, or stale;
- `check_link_targets()` flags checked Concepts whose explicit path-like
  `links` targets are missing, unchecked, or stale; it is structural
  link-target integrity, not semantic false-link detection;
- `check_source_metadata()` flags checked sources with thin metadata and now
  catches deterministic DOI conflicts between `identifiers.doi` and
  `csl_json.DOI`;
- `check_source_metadata()` also flags checked sources linked to a checked
  person/venue entity whose capture metadata records
  `metadata.identity_status: ambiguous`, routing objective catalog identity
  conflicts to PI attention instead of silently accepting the merge;
- `record_integrity_check()` records `check-fired` rows with shadow-first
  routing (`drop` while shadowed, `ask` for active failures, `act` only when an
  auto-revert check explicitly opts in);
- `trace_downstream()` rebuilds the downstream graph from journal
  `derived.inputs`;
- `cascade_rollback()` quarantines machine-derived downstream Concepts, appends
  `resolved` plus inverse `derived` events for the rollback commit, and leaves
  PI-derived downstream Concepts live while flagging them with route `ask`.

This is not the full WP7 detector suite. Live identifier enrichment, semantic
span entailment beyond exact quote anchoring, semantic prompt-injection
detection, semantic contradiction discovery, semantic false-link detection,
calibration bars, and live checkpoint-cost calibration remain open WP7/WP-Gate
work. The current deterministic seeded-error verdict is tracked in
`wp-gate-seeded-error-results.md`.

Verification:

```bash
python -m pytest tests/test_integrity.py
python -m pytest tests/test_integrity.py tests/test_trusted_writer.py tests/test_knowledge.py
python -m pytest tests/test_capture.py tests/test_integrity.py -q
python -m pytest tests/test_package_spine.py
python -m ruff check src/memoria_vault/runtime/integrity.py src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/__init__.py tests/test_integrity.py
python -m ruff check src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/integrity.py tests/test_capture.py tests/test_integrity.py
python -m ruff format --check src/memoria_vault/runtime/integrity.py src/memoria_vault/runtime/trusted_writer.py src/memoria_vault/runtime/__init__.py tests/test_integrity.py
python -m ruff format --check src/memoria_vault/runtime/capture.py src/memoria_vault/runtime/integrity.py tests/test_capture.py tests/test_integrity.py
python scripts/docs_doctor.py docs
python scripts/status_doctor.py
python scripts/agents_doctor.py --write
python scripts/agents_doctor.py
git diff --check
```

Result: passed.
