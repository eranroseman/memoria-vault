# WP-G3 Basic Cycle Harness Results

Timestamp: 2026-06-29T08:11:52Z

Scope: deterministic G3 source-to-gap cycle harness in a disposable workspace.
This is CI evidence for the worker-boundary flow; it does not replace the later
attended `Memoria-test` Obsidian/product run required by the release plan.

Implemented check:

- `tests/test_alpha11_cycle.py` opens a checked project and seed thesis through
  `enqueue_trusted_write()`;
- the worker runs initial gap analysis and reports the seeded thesis as
  `under-warranted`;
- the worker captures a BibTeX source with stable `source_id`, citekey alias,
  DOI metadata, content path, and raw-copy path, records a Co-PI interview turn,
  compiles a checked digest plus five checked hub updates, proposes one anchored
  claim-bearing note with `annotation_ref` page/quote/bbox provenance, accepts
  it, and links it as `supports` to the thesis;
- the worker re-runs gap analysis and the original `Memory Consolidation` gap is
  closed;
- the worker answers an Ask query from checked Concepts, rebuilds the checked
  qmd input tree, and renders the project argument as `argument.canvas`;
- the worker runs `cascade-rollback` from the captured source after the usable
  path is proven, quarantines the machine-derived digest and accepted note, and
  leaves the source Concept itself in place because the target was not included;
- the harness asserts journal evidence for `model_call` and PI link curation,
  and checks that every indexed Concept is `check_status: checked`.

Verification:

```bash
python -m pytest tests/test_alpha11_cycle.py
python -m ruff check tests/test_alpha11_cycle.py
python -m ruff format --check tests/test_alpha11_cycle.py
```

Result: passed. Latest focused run after adding anchored-note provenance and
rollback coverage:
`python -m pytest tests/test_alpha11_cycle.py -q` → `1 passed`.

Runtime verifier wiring: `scripts/verify live --evidence-dir
/tmp/memoria-alpha11-verify-live-anchored` passed on 2026-06-29. The bundle ran
`python3 -m pytest tests/test_alpha11_cycle.py -q` before `bash
scripts/test-l2.sh`, so the deterministic G3 worker cycle is part of the
runtime verification prefix; evidence summary:
`/tmp/memoria-alpha11-verify-live-anchored/summary.json`.

Remaining G3 runtime evidence: fresh `Memoria-test` initialization, live
Obsidian panel activation, and the attended product run with the real plugin
surface. The local worker-boundary source-to-gap plus trace-to-rollback cycle is
covered by CI.
