# WP-Gate Seeded-Error Slice Results

Timestamp: 2026-06-29T06:20:17Z

Scope: expanded WP-Gate structural plus first blind-class slice for the
alpha.11 seeded-error verdict:

- `system/eval/alpha11-seeded-errors.json` is the frozen bundle for three
  structural `evidence-resolves` cases: `missing-evidence-source`,
  `unchecked-evidence-source`, and `missing-digest-evidence`;
- `load_seeded_error_bundle()` validates the frozen contract before fixture
  setup: version, numeric bars, required case fields, unique case IDs, unique
  targets, and the supported rollback mode;
- the bundle includes a structural contradiction-link case,
  `missing-contradiction-target`, checked by `contradiction-link` when a digest's
  explicit `contradictions` target is absent;
- the bundle includes a structural link-target case, `false-link-target`,
  checked by `link-target` when a checked Concept carries a path-like `links`
  target that does not resolve to a current checked Concept;
- the bundle includes a structural source-metadata case,
  `conflicting-doi-metadata`, checked by `source-metadata` when a checked
  source's `identifiers.doi` conflicts with `csl_json.DOI`;
- the bundle includes a second structural source-metadata case,
  `ambiguous-entity-identity`, checked by `source-metadata` when a checked
  source links to a checked catalog entity whose capture metadata records
  `metadata.identity_status: ambiguous`;
- the bundle also includes three deterministic blind-class cases:
  `unwarranted-claim`, checked by the high-precision `claim-quote-support`
  overlap check, and `stale-as-current`, checked by `evidence-current` when a
  note or digest cites checked evidence marked `lifecycle: retracted` or
  `archived`, plus `crafted-injection`, checked by the high-precision
  `prompt-injection` marker check;
- the bundle includes two model-free span cases: `wrong-extraction`, checked by
  `quote-anchor` when a note quote is absent from all checked source text
  declared by `source_id`/`evidence_set`, and `poisoned-span`, checked by
  `prompt-injection` when a checked source content span carries an explicit
  instruction-like marker;
- the bundle includes a provenance/risk checkpoint case,
  `fresh-uncorroborated-source`, checked by `provenance-checkpoint` when a
  checked note depends on a checked source whose metadata is still only
  `partial`;
- `run_seeded_error_verdict()` builds a disposable alpha.11 fixture, injects the
  missing/unchecked/stale evidence, false-link, ambiguous entity identity,
  wrong-extraction, unwarranted-claim, crafted-injection,
  fresh-uncorroborated-source, and poisoned-span cases, runs
  `check_evidence_integrity()`, `check_quote_anchor_support()`,
  `check_claim_quote_support()`, `check_prompt_injection_markers()`,
  `check_provenance_checkpoint()`, `check_contradiction_links()`,
  `check_link_targets()`, and `check_source_metadata()`,
  cascade-rolls-back the detected machine sources/notes/digests, and reports
  recall, false-positive rate, rollback completeness, residual error rate,
  no-checks residual baseline, residual reduction, ask-routed checkpoint value,
  check timings, per-target detection time, and per-error-class detection timing;
- the current frozen cases meet the bundle bars:
  recall `1.0`, false-positive rate `0.0`, rollback completeness `1.0`, and
  residual error rate `0.0`; the no-checks residual baseline is `1.0`,
  residual reduction is `1.0`, and ask-routed checkpoint value is `1.0`;
  per-error-class false positives are attributed to the classes whose
  `expected_check` matches the unexpected finding's check;
  verdict results now also include `check_timings`, `detection_times_ms`,
  `detection_timing_by_error_class`, and `bar_failures`, which is empty for the
  current frozen bundle.
- the worker exposes this verdict as `run-seeded-error-verdict`, executed in a
  disposable temp workspace so the active vault is not mutated by fixture setup
  or rollback; `tests/test_worker_queue.py` asserts the worker path returns
  `passed: true`, detects all 13 frozen cases, leaves no residual seeded errors,
  and does not write fixture Concepts into the caller vault.

This is the frozen deterministic local verdict for the current alpha.11 seeded
bundle. It does not settle broader semantic detector quality: prompt-injection
beyond explicit markers, semantic contradiction discovery, semantic
poisoned-span, semantic false-link detection, wrong-extraction beyond exact
quote anchoring, and live PI checkpoint adjudication cost remain follow-up
calibration work. The provenance checkpoint is deterministic and routes
fresh/uncorroborated source use to PI attention; it is not a semantic detector.

Verification:

```bash
python -m pytest tests/test_seeded_errors.py tests/test_integrity.py
python -m pytest tests/test_integrity.py tests/test_seeded_errors.py tests/test_worker_queue.py
python -m ruff check src/memoria_vault/runtime/seeded_errors.py src/memoria_vault/runtime/integrity.py src/memoria_vault/runtime/__init__.py tests/test_seeded_errors.py tests/test_integrity.py
python -m ruff format --check src/memoria_vault/runtime/seeded_errors.py src/memoria_vault/runtime/integrity.py src/memoria_vault/runtime/__init__.py tests/test_seeded_errors.py tests/test_integrity.py
python -m pytest tests/test_integrity.py tests/test_worker_queue.py tests/test_seeded_errors.py tests/test_capabilities.py -q
python -m pytest tests/test_seeded_errors.py tests/test_worker_queue.py::test_worker_runs_seeded_error_verdict_in_disposable_fixture tests/test_integrity.py::test_source_metadata_check_flags_ambiguous_linked_entity_identity -q
```

Result: passed.
