# tests/

Pytest suite for the repo's test levels (see AGENTS.md → *Ground truth*).
Tests live here as standalone files, not inline in shipped modules, so the
deployed vault carries no test code.

- `test_*.py` — behavior, contract, or subsystem tests. Name files for the
  current behavior they protect, not for the release that introduced it. Each
  file declares its own level with a module-level
  `pytestmark = pytest.mark.<level>`, placed after the imports; a file that
  already carries another module mark combines them in a list. A new test file
  without one runs in no selection, so `test_testing_levels.py` fails it.
- `pyproject.toml` — declares install metadata for `memoria.*` plus pytest
  `pythonpath` entries and registered level markers.
- `tests/helpers.py` and `tests/cli_test_helpers.py` — shared fixture builders
  and CLI-surface helpers used by several test modules.

| Level | Purpose |
| --- | --- |
| `static` | formatting, lint, schema, spell, design history, workflow safety |
| `unit` | deterministic Python behavior |
| `contract` | CLI, operations, capability manifests, concept writers, projections |
| `package` | wheel build/install smoke, e2e smoke, and package-facing helper tests |
| `runtime` | worker loops, recovery, idempotence, state transitions, long checks |
| `live` | real external services/providers |

Which levels the gate runs is owned by `PYTEST_MARKERS` in `scripts/verify` —
read it there rather than restating it here. Target one level with
`python3 -m pytest tests/ -q -m unit`; use `-m "not slow"` for the fast local
loop; run a level the gate excludes the same way on demand (e.g. `-m live`).

The installer end-to-end harness is a separate disposable-vault check:

```bash
bash scripts/test_vault/install-test-vault-local-llm.sh --root ~/memoria-vault/test-vault
```

## Coverage guidance

Coverage is a review signal, not a repo-wide merge gate yet. Prefer focused
contract tests over chasing a global percentage:

- Add small unit or contract tests near the seam when a focused seam exists.
  Use runtime tests only for worker loops, recovery, idempotence, or full
  workflow behavior that cannot be proven cheaper.
- Any changed check script under `scripts/checks/` must add positive and negative
  cases for each new rule, including malformed input and "should be ignored" paths.
- Any changed runtime module should cover the main success path, fail-closed/error
  path, idempotency behavior, and boundary cases for path/schema handling.
- Use `python3 -m pytest tests/ --cov=. --cov-branch` locally when reviewing risk.
  Treat large drops or uncovered changed branches as review findings.

Do not add a hard global coverage threshold until the project adopts a ratcheting
baseline; a blanket threshold would reward broad, shallow tests and make unrelated
coverage gaps block small fixes.
