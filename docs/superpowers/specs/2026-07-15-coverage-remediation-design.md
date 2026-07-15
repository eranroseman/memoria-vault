# Test-coverage remediation — Design

Date: 2026-07-15. Status: design, pre-plan (sourced from a workflow-based
coverage review of the full `scripts/verify` coverage report; chat-recorded,
not yet issue-filed).

## Goal

The review's headline finding: coverage percentage and actual risk are nearly
**inversely correlated** in this codebase. The lowest numbers
(`mcp_transport.py` 27%, `code/runner.py` 33%, `scripts/verify` 41%) are
almost all deliberately gated (an optional dependency CI doesn't install, a
missing sandbox binary, a subprocess boundary coverage tooling can't see
across) with the underlying logic independently exercised elsewhere. The real
risk clusters in files sitting at 68–83% coverage, where the missing lines
are precisely the enforcement/audit/safety-net branches — the exact code a
"looks fine, it's in the high 70s" skim would miss. This spec closes the
confirmed-real gaps, cheapest and highest-value first, and explicitly leaves
the justified-as-is set alone.

## Design decisions (made here; confirm at review)

- **Scope is exactly the ten items below**, drawn from a completed
  investigation that read the actual missing lines/branches for every
  file under ~85% coverage and classified each as dead code, a defensive
  edge case, a deliberately-gated live/optional path, or a genuine gap. The
  much larger justified-acceptable set (`scripts/verify`, `e2e_smoke.py`,
  `test_live_runner.py`, `test_env_harness.py`,
  `plugin_provenance_doctor.py`, `state.py`'s Windows-only lock code,
  `backup.py`'s scattered fault-injection branches, `hub_handoff.py`,
  `paths.py`'s orphaned `resolve_vault()`) is **out of scope** — see "Out of
  scope" for the one-line reason each was already ruled acceptable, so it
  isn't re-litigated piecemeal later.
- **Item 1 (CI `mcp` extra) goes first and stands alone.** It is a CI-config
  change, not a test addition, and it unlocks an already-written,
  already-thorough test file for zero new code — the highest value-to-effort
  ratio in the set.
- **Items 2–10 are independent of each other and of item 1.** Each adds
  tests to existing, unchanged production code; none requires another item
  to land first. They can be picked off in any order or split across
  separate PRs.
- **No production behavior changes anywhere in this spec**, except the two
  cleanup items (11a/11b), which are a one-line `# pragma: no cover`
  addition and a dead-code deletion — not behavior changes either.
- **The `code/runner.py` bwrap-sandbox path stays deferred**, per the
  review: it's correctly fail-closed on an absent `bwrap` binary, and
  nothing in the repo currently calls `run_artifact`/`create_code_artifact`
  from a live operation. An opt-in local test (gated on
  `shutil.which("bwrap")`, mirroring `tests/test_live_runner.py`'s pattern)
  is worth adding *when* this runtime primitive gets wired to a real
  operation, not preemptively.

## Architecture

Ten independently testable items, ranked by risk (not by coverage
percentage), plus two trivial cleanups.

### 1. CI: install the `mcp` optional extra

`mcp` is declared in `pyproject.toml` (`[project.optional-dependencies] mcp
= ["mcp>=1.27"]`) but is absent from both the default install and
`requirements-dev.txt`. Every test in `tests/test_mcp_transport.py` from
`test_mcp_app_requires_non_root_read_scope` onward opens with
`pytest.importorskip("mcp")` and is silently skipped in the required CI
gate — not a bug in the tests, just an unexercised optional path. Add `mcp`
to CI's install step (`pip install -e ".[mcp]"` alongside
`requirements-dev.txt` in `verify.yml`, or add it directly to
`requirements-dev.txt`). It's a plain offline pip package with no live
service or secret behind it. This closes `mcp_transport.py`'s 27% and
`test_mcp_transport.py`'s 40% for free, with zero new test code.

### 2. `policy/hook.py` — audit deny-path and completion-failure handler

- `_audit_tool_policy_block` (`policy/hook.py:232`): its entire body past
  the `action is None` check (lines 238-261) never runs. Add a test that
  denies an Obsidian write tool via the actor allowlist with a valid
  `path`/`request_id`, asserting a deny row lands in `audit.jsonl`.
- `evaluate_post` (`policy/hook.py:380`): the exception handler when
  `PolicyEngine.complete_write()` raises (lines 413-434, `record_event(...,
  code="audit_completion_failed")` at line 425) is never triggered. Add a
  test that monkeypatches `complete_write` to raise, asserting
  `evaluate_post` records `audit_completion_failed` and still unlinks the
  pending stash.

This is the policy-enforcement hook the system's auditability rests on —
highest-priority item in this spec.

### 3. `retraction.py` — `sweep()`, `check_doi()`, and the severity tie-break

- `sweep()` (`retraction.py:303`) and `check_doi()` (`retraction.py:255`)
  have zero test coverage anywhere in the repo; only their pure helpers
  (`rw_lookup`, `crossref_retraction`, `combine`) are unit-tested with
  hand-built dicts. `sweep()` is what actually walks `catalog/sources/*/
  source.md` and writes the Inbox alert a researcher relies on to learn a
  cited DOI was retracted. Add a test with an offline RW-CSV fixture
  containing one retracted DOI plus a tmp-vault source note citing it,
  asserting checked/hit counts and that the Inbox alert is written with the
  right target/citekey.
- `check_doi`'s offline no-CSV path has a one-time stderr warning
  (documented in-code as existing so a CSV-less cron sweep "must not look
  healthy") that is itself unverified. Add a `capsys`-based test asserting
  it fires.
- `build_rw_index` (`retraction.py:97`)'s severity tie-break — "a real
  Retraction wins over a concern/correction" (its own docstring) — has no
  test feeding two rows sharing a DOI to prove it. Add one fixture with the
  same DOI appearing twice (an Expression-of-Concern row then a Retraction
  row), asserting the Retraction wins.

### 4. `diagnostics.py` — content-light guarantee and raw-bundle re-redaction

- `_content_light`'s handling of list/tuple/set values and its
  `str(value)` fallback for arbitrary objects (lines 89-91) is untested —
  every existing test only passes string/int detail values. Add a test
  passing a list/tuple and one non-JSON-primitive object as a details
  value, asserting no raw substring survives.
- `create_redacted_bundle(include_raw=True)`'s re-redaction of an
  already-captured `payload_redacted` field (lines 237-238) is untested.
  Add a test that sets the raw-capture-once env var, records a secret
  payload, calls `create_redacted_bundle(include_raw=True)`, and asserts
  the secret string never appears verbatim in the resulting bundle.

### 5. `http_transport.py` — real end-to-end auth and body-size gate

The entire `Handler` class inside `make_http_server` (lines 41-97) —
`do_GET`/`do_POST`, `_handle`'s Authorization-header check (the actual
bearer-token gate), and `_json_body`'s `Content-Length`/payload-too-large
guard — has zero coverage at the level that matters: every existing test
either calls internal `_dispatch()` directly (bypassing auth) or fakes the
server. Add one true end-to-end test that starts a real
`make_http_server(...)` on an ephemeral port and issues actual HTTP
requests (`http.client`/`urllib`): missing/wrong Authorization header
expecting 401, an oversized `Content-Length` expecting 413, and one normal
authorized GET. Also add a `_scope_intersection` case where the requested
scope is strictly inside the granted scope (line 292; only the widen-and-
clamp and disjoint cases are currently covered).

### 6. `scripts/checks/schema_doc_drift.py` — seeded-mismatch fixtures

Three drift dimensions run for real on every PR against
`docs/reference/data-model/frontmatter.md` but have never been proven to
actually fire: a documented `category` mismatch (`_schema_claim_errors`,
line 112), a `required_when` entry absent from the live schema
(`_map_section_errors`, line 141), and a `required_any`/`forbidden`
list-diff mismatch (`_list_subset_errors`, lines 168-175). The existing
`tests/test_schema_doc_drift.py` only seeds enum-value and doc-type-roster
mismatches. Add three seeded-mismatch fixtures, one per dimension, each
asserting its specific error string.

### 7. `scripts/checks/removed_surface_gate.py` — file-type search root

`iter_files`'s `root.is_file()` branch (lines 67-70) is live in production
today — the real `removed_surfaces.json` lists `.pre-commit-config.yaml`,
`AGENTS.md`, `CONTRIBUTING.md`, and `SECURITY.md` as file (not directory)
search roots — yet the existing test only exercises a directory root
(`docs`). Add a test using a file-type search root with a seeded
retired-text match inside that file, asserting it's caught. Separately
(design hardening, not just a test): line 98 (`if not root.exists():
continue`) silently skips a missing search root instead of failing loudly;
consider making a missing search root a hard failure so a typo'd/renamed
root can't quietly stop being scanned.

### 8. `worker.py` — remaining CLI subcommand dispatch

`worker.py`'s `main()` (lines 1436-1484) wires `scan`, `run-scheduled`,
`integrity-sweep`, `observe-pi-edits`, and `recover` from argv to their
handler functions; only `enqueue-operation` has a wiring test today
(`test_worker_cli_enqueues_operation_payload`). Confirmed via repo-wide
grep that this entry point is real, operator-facing surface (an external
cron/launchd job invokes it per `docs/reference/commands-and-transports/
operations.md`), not dead code — the underlying functions are well covered
through other paths, but a wiring bug in this specific dispatcher wouldn't
be caught by any existing test. Add one parametrized test per remaining
subcommand, mirroring the existing enqueue-operation test's shape.

### 9. `code/runner.py` — `run_artifact`'s validation guards

Two `raise ValueError` guards (lines 51, 54) — for an unknown
`artifact_id` and for a malformed/empty `approved_command` — are the only
backstop against executing a garbage command list, since
`create_code_artifact` doesn't itself validate `approved_command`. The one
existing test always passes a valid command. Add a plain unit test (pure
Python, no `bwrap` needed) asserting `run_artifact` raises `ValueError` for
both cases.

### 10. `test_workspace_seed_links.py` — wikilink-detector fixture

`_check_wikilink_aliases` and `_check_broken_wikilinks` (lines 101-108,
114-120) — the module's actual wikilink-discipline detection logic — have
never run their substantive logic, because none of the 3 markdown files
currently in the packaged seed contain any `[[wikilink]]` syntax. Add a
synthetic-fixture test that builds a tmp seed dir with a deliberately
broken wikilink and an un-aliased one, asserting both detectors flag them.

### 11. Cleanup (no test writing; two small, low-risk fixes)

- **11a.** `state.py`'s `_open_workspace_lock_file_windows` (~71% of that
  file's entire missed-line count) lacks the `# pragma: no cover` its
  sibling Windows-only import-fallback branches already carry a few lines
  above — an inconsistency, not a real gap. Add the pragma so `state.py`'s
  coverage number reflects its genuine (much smaller, low-risk) gaps
  instead of inflating on Windows-only code that cannot run on Linux CI.
- **11b.** `test_workspace_seed_links.py`'s `_check_template_frontmatter`/
  `DROPPED_KEYS`/`tmpl_dir` block (lines 24, 75-79, 127-130) targets
  `system/templates`, a seed directory retired from the shipped product
  (commit `cf6fcdae`) years before this test file was created (PR #1349) —
  dead code carried into a new file, not a held-in-reserve check. Delete
  it.

## Testing

Every item above (2–10) *is* a testing change — no separate test plan
beyond what's specified per item. Summary of what closes:

| Item | File | What the new test proves |
|---|---|---|
| 2 | `policy/hook.py` | Deny decisions are actually audited; audit-completion failures are recorded, not swallowed |
| 3 | `retraction.py` | A retracted, cited source is actually surfaced to the PI; severity tie-break is correct |
| 4 | `diagnostics.py` | Non-string payloads stay content-light; raw-bundle re-redaction actually redacts |
| 5 | `http_transport.py` | The bearer-token gate and body-size limit are enforced by the real `Handler`, not bypassed |
| 6 | `schema_doc_drift.py` | Three drift dimensions actually fire on a real mismatch |
| 7 | `removed_surface_gate.py` | A file-type search root (the real production shape) is actually scanned |
| 8 | `worker.py` | Every `main()` subcommand reaches its intended handler |
| 9 | `code/runner.py` | Malformed code-artifact input is rejected before execution |
| 10 | `test_workspace_seed_links.py` | The wikilink detectors actually detect a violation |

## Out of scope

The following were investigated in the same review and confirmed acceptable
as-is; re-checking them is not part of this spec:

- `scripts/verify` — `main()`/`run()` never fire under pytest by design
  (would recursively re-run the whole `GATES` roster); CI runs it directly
  as a real integration check on every PR.
- `scripts/test_vault/e2e_smoke.py` — the literal e2e smoke test, run
  wholesale and unmocked as its own `GATES` entry; mocking it to gain
  coverage credit would defeat its purpose.
- `tests/test_live_runner.py` — correctly, doubly gated (marker + runtime
  live-endpoint check); the one intentional opt-in real-network proof.
- `scripts/test_vault/test_env_harness.py` — missing branches are
  unhappy-path shapes the one golden cassette never triggers; ordinary
  passing-test shadow, not a real gap.
- `scripts/checks/plugin_provenance_doctor.py` — its actual violation-
  detecting logic is well covered; remaining misses are an argparse/print
  shim and a TOCTOU-only defensive branch.
- `src/memoria_vault/runtime/state.py` — bulk of its misses is Windows-only
  code that cannot run on Linux CI (see 11a for the pragma fix); the rest
  is defense-in-depth re-checks and a `supersede_request_id` path
  unreachable through any current caller.
- `src/memoria_vault/runtime/backup.py` — 134 misses scattered across a
  module already carrying 90 dedicated tests; remaining gaps mostly require
  forging on-disk transaction files or injecting real `OSError`s mid-copy.
- `src/memoria_vault/runtime/subsystems/integrity/linter/hub_handoff.py` —
  the uncovered parse-failure branch guards two already-implicitly-synced
  strings; `main()` is thin CLI wiring with no independent policy logic.
- `src/memoria_vault/runtime/paths.py`'s `resolve_vault()` — no caller
  anywhere in `src/`/`tests/` beyond its own definition; a deletion
  candidate per the repo's own "prefer deletion > mechanism" bias, not a
  test-writing candidate. Not deleted here since that's a product-code
  change outside this spec's testing-only scope — flagged for a follow-up
  decision, not resolved by this spec.
- `src/memoria_vault/runtime/code/runner.py`'s `bwrap` sandbox path (lines
  30-38, 68-89, 100-143, 167-182) — correctly fail-closed on an absent
  `bwrap` binary; deferred (see Design decisions) until wired to a live
  operation.

## Constraints (inherited)

- Correctness gate: `python scripts/verify` passes before merge.
- Test only against disposable vaults (`tmp_path` / `test-vault/`), never a
  personal vault.
- Stage explicit paths only — never `git add -A` (shared-index rule).
- No new dependencies — item 1 installs an already-declared optional extra
  in CI; nothing here adds a new `pyproject.toml` dependency.
- No `SCHEMA_VERSION` change — every item is test-only or (11a/11b)
  a pragma/dead-code cleanup; no production schema or behavior changes.
