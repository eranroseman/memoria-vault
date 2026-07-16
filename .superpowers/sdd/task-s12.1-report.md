# Task S12.1 report — `code-warrant` to `code-grounds`

## Outcome

Renamed the computed-evidence identifier family to `code-grounds` with no
compatibility alias or migration. The runtime parser, state-derived evidence
resolution, code-run verifier, and draft-number route now use the new family.
The retained negative test proves both direct parsing and generic reference
classification reject the retired `code-warrant:` marker.

Changed task paths:

- `src/memoria_vault/runtime/evidence.py`
- `src/memoria_vault/runtime/state.py`
- `src/memoria_vault/runtime/code/runs.py`
- `src/memoria_vault/runtime/knowledge.py`
- `tests/test_evidence_markers.py`
- `tests/test_code_artifacts.py`
- `tests/test_draft_verification.py`
- `CHANGELOG.md`

The draft-verification route test is parameterized over exactly
`analysis-computed`, `analysis code`, and `code-grounds`.

## TDD evidence

### RED

Before production edits, ran:

```text
python -m pytest -vv \
  tests/test_evidence_markers.py::test_code_grounds_refs_validate_and_retired_code_warrant_refs_fail_closed \
  tests/test_code_artifacts.py::test_computed_evidence_tracks_code_run_output_hash \
  'tests/test_draft_verification.py::test_draft_verification_routes_analysis_number_references_to_incomplete[code-grounds]'
```

Result: `3 failed` for the intended missing behavior:

- `parse_code_grounds_ref` did not exist.
- A `code-grounds:` item did not rebuild into an evidence row.
- The `code-grounds` spelling did not route to
  `analysis-number-evidence-incomplete`.

### GREEN

After the minimal identifier-family rename, the same three focused nodes
passed (`3 passed in 0.98s`). The test was then renamed to avoid retaining an
old identifier in a test symbol, and a controller-requested direct assertion
was added to prove `parse_code_grounds_ref(code-warrant:...)` raises
`ValueError` with the `invalid code-grounds ref` message. The focused
three-node proof was rerun and passed (`3 passed in 7.42s`).

The final affected-suite run was:

```text
python -m pytest -q \
  tests/test_evidence_markers.py \
  tests/test_code_artifacts.py \
  tests/test_draft_verification.py
```

Result: `46 passed in 232.49s`.

## Full gate

Ran the required approved full gate after the final test change:

```text
python scripts/verify
```

Result: exit `0`; `1889 passed, 9 skipped, 1 warning in 282.84s`; the offline
vault smoke, compile, shell syntax, JSON syntax, and product-integrity checks
all passed; final output was `verify: OK`.

The warning is the existing `test_worker_queue` multiprocessing-fork
deprecation warning. It did not fail the gate and is unrelated to this rename.

## Self-review and concerns

Read-only review found no material findings. The final diff is limited to the
task paths above, `git diff --check` is clean, and the renamed runtime files
contain no retired code-warrant identifiers or aliases. No purpose enum or
migration, `under-warranted`, NLI/Toulmin terminology, historic records, or G2
`warrant_ref` metadata was changed.

No remaining implementation concern. Published documentation still contains
some `code-warrant` prose, deliberately left for its separately scoped S12.4
sweep; the historical Alpha.19 changelog entry also remains intact.
