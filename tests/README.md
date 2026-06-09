# tests/

L1 component tests (pytest), per [ADR-44](../docs/adr/44-tests-in-pytest-tree.md).
These were formerly inline `--self-test` blocks inside the modules; they now live here
so the shipped vault carries no test code.

- `test_*.py` — one per module under test; imports the module and asserts its contract
  on synthetic fixtures (no vault runtime, no network).
- `conftest.py` — puts the module directories on `sys.path`.
- `_util.py` — `load_script()` for the hyphenated `scripts/` tools, and the shared
  `TestHarness`.

Run: `python -m pytest tests/ -q` (or `scripts/test.sh l1`). CI runs them in the
`python-selftest` job. Higher layers (L2–L5) are the manual/semi-automated plans in
[docs/testing/](../docs/testing/).
