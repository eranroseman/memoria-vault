# tests/

Pytest suite for the repo's test levels (see AGENTS.md → *Test before opening a
PR*). Tests live here as standalone files, not inline in shipped modules, so the
deployed vault carries no test code.

- `test_*.py` — behavior, contract, or subsystem tests. Name files for the
  current behavior they protect, not for the release that introduced it.
- `pyproject.toml` — declares install metadata for `memoria.*` plus pytest
  `pythonpath` entries and registered level markers.
- `tests/conftest.py` — assigns every `test_*.py` file to exactly one level.
- `tests/helpers.py` and `tests/cli_test_helpers.py` — shared fixture builders
  and CLI-surface helpers used by several test modules.

| Level | Purpose | Runs |
| --- | --- | --- |
| `static` | formatting, lint, schema, spell, design history, workflow safety | `scripts/verify`, every PR |
| `unit` | deterministic Python behavior | `scripts/verify`, every PR |
| `contract` | CLI, operations, capability manifests, concept writers, projections | `scripts/verify`, every PR |
| `package` | wheel build/install smoke, e2e smoke, and package-facing helper tests | on demand (built wheel) |
| `runtime` | worker loops, recovery, idempotence, state transitions, long checks | on demand (disposable workspace) |
| `live` | real external services/providers | manual only (live provider) |

`python scripts/verify` runs the `static`/`unit`/`contract` levels (plus lint,
product gates, offline smoke, and syntax checks). Target one level with
`python3 -m pytest tests/ -q -m unit`; use `-m "not slow"` for the fast local
loop. The `package`, `runtime`, and `live` levels run on demand after
`pip install -e .` — e.g. `python3 -m pytest tests/ -q -m package` — never in the
gate.

The installer end-to-end harness is a separate disposable-vault check:

```bash
bash scripts/sandbox/install-test-vault-local-llm.sh --root ~/memoria-vault/sandbox
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
