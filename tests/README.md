# tests/

L1 component tests (pytest), per [ADR-44](../docs/adr/44-tests-in-pytest-tree.md).
These were formerly inline `--self-test` blocks inside the modules; they now live here
so the shipped vault carries no test code.

- `test_*.py` — one per module under test; imports the module and asserts its contract
  on synthetic fixtures (no vault runtime, no network).
- `conftest.py` — puts the module directories on `sys.path`.
- `_util.py` — the shared `CheckHarness`.

Run: `python -m pytest tests/ -q` (or `scripts/test.sh l1`). CI runs them in the
`python-selftest` job. Higher layers (L2–L5) are the manual/semi-automated plans in
[docs/testing/](../docs/testing/).

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
legacy gaps block small fixes.
