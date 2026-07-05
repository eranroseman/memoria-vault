# tests/

Pytest suite for the repo's test levels (see AGENTS.md → *Test before opening a
PR*). Tests live here as standalone files, not inline in shipped modules, so the
deployed vault carries no test code.

- `test_*.py` — one per module under test; imports the module and asserts its contract
  on synthetic fixtures (no vault runtime, no network).
- `pyproject.toml` — declares install metadata for `memoria.*` plus pytest
  `pythonpath` entries and registered level markers.
- `tests/conftest.py` — assigns every `test_*.py` file to exactly one level.

| Level | Purpose | Runs |
| --- | --- | --- |
| `static` | formatting, lint, schema, docs refs, spell, ADR index, workflow safety | local hook, every PR |
| `unit` | deterministic Python behavior | every PR |
| `contract` | CLI, operations, capability manifests, templates, projections | every PR |
| `package` | wheel build/install smoke, installer/e2e smoke helpers | package-facing PRs, release PRs |
| `runtime` | worker loops, recovery, idempotence, state transitions, long checks | nightly, release candidate |
| `live` | real external services/providers | manual or scheduled only |

Run the PR source gate with `python scripts/verify pr`.
Target a level with `python -m pytest tests/ -q -m unit` or `python scripts/verify l1`.
Use `python -m pytest tests/ -q -m "not slow"` for the fast local loop.
Higher-gate procedure lives in
[verify-change](../.agents/playbooks/verify-change.md).

## Coverage guidance

Coverage is a review signal, not a repo-wide merge gate yet. Prefer focused
contract tests over chasing a global percentage:

- Any changed governance or doctor script must add positive and negative cases for
  each new rule, including malformed input and "should be ignored" paths.
- Any changed runtime module should cover the main success path, fail-closed/error
  path, idempotency behavior, and boundary cases for path/schema handling.
- Use `python -m pytest tests/ --cov=. --cov-branch` locally when reviewing risk.
  Treat large drops or uncovered changed branches as review findings.

Do not add a hard global coverage threshold until the project adopts a ratcheting
baseline; a blanket threshold would reward broad, shallow tests and make unrelated
coverage gaps block small fixes.
