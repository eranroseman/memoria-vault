# Test-Suite Speedups Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the four measured test-suite speedups from the post-#1733 analysis — restore the starved tmpfs fast path and stop the leaks that starved it, guard `state.connect()`'s per-connect schema re-execution, replace one redundant 76s seeded-error run with the existing fake-verdict pattern, and fold the duplicated 70s thin-loop CLI test into the runtime gate replay.

**Architecture:** Nothing speculative — every task implements a change that was measured on this machine (measurements quoted per task). The tmpfs lever already exists in `tests/conftest.py` and is merely starved by temp-dir leaks; the fix is cleanup plus self-healing, not new mechanism. The `connect()` guard is a two-line early return in product code that also speeds the shipped CLI. The two test restructures each carry an explicit coverage argument for what remains and where the dropped coverage already lives.

**Tech Stack:** Python 3.12, pytest + xdist (existing); no new dependencies.

## Global Constraints

- Correctness command: `python scripts/verify`; `main` requires PR + `verify` + `gitleaks`; squash merge.
- Work in a worktree: `git worktree add .claude/worktrees/test-speed -b wip/test-speed origin/main`, then `EnterWorktree(path: ".claude/worktrees/test-speed")`. Stage explicit paths only, never `git add -A`.
- CI keeps the real filesystem BY DESIGN (`tests/conftest.py` docstring: "CI keeps the real filesystem on purpose: it is the authoritative gate"). Nothing in this plan may weaken durability on CI — the tmpfs work is local-loop only, which is the existing contract.
- Test invocation: `env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest <path> -v`.
- Formatter: `pre-commit run ruff-format --hook-stage manual --files <touched .py>` before each commit.
- The shared machine invalidates absolute timings — when a step says "measure", report load (`uptime`) with the number and compare ratios, not walls.

## Explicitly out of scope (evidence-based rejections — do not implement)

- Journal appends opening one connection per row (37.3 → 3.9 ms/append reusing one connection): needs a design ruling on whether per-row connections are deliberate crash isolation. File an issue if touched territory makes it relevant; do not change it here.
- A `MEMORIA_TEST_FAST_IO` fsync/synchronous knob: measured 10-15x but redundant with the tmpfs path this plan restores.
- A disk-keyed cross-process floor-seed cache: its cache key under-invalidates (seed bytes depend on the whole runtime); a stale seed silently green-lighting goldens is unacceptable.
- Parametrizing `test_runtime_gate_replay` (stateful pipeline; splitting forces a workspace per step) or cutting `test_worker_knowledge_cycle` (irreducible PI-actor composition contract).

---

### Task 1: Restore the tmpfs fast path — clean the litter, fix the leaks, make the guard self-healing

Measured basis: `tests/conftest.py` redirects TMPDIR to `/dev/shm` for a documented 443s → 89s suite effect, gated on ≥ 4 GiB free (`TMPFS_MIN_FREE_BYTES`, line 13). `/dev/shm` sits at ~3.96 GiB because of ~6.6 GB of retained `pytest-of-<user>` trees plus 823 leaked `memoria-floor-seed-*` dirs (`tests/floor_lib.py:227` `mkdtemp`, never cleaned) — and `tests/conftest.py:67` leaks a `memoria-test-xdg-*` dir per run the same way. The guard defeats itself exactly as litter accumulates.

**Files:**
- Modify: `tests/conftest.py` (lines 13-58: add prune helper, call it before the guard; line 67: register cleanup)
- Modify: `tests/floor_lib.py` (line 227 vicinity: register cleanup for the seed cache)
- Test: `tests/test_conftest_scratch.py` (create)

**Interfaces:**
- Produces: `_prune_stale_scratch(candidate: Path, now: float | None = None) -> int` in `tests/conftest.py` (returns count of pruned entries; Task 6 quotes it in the PR).

- [ ] **Step 1: One-time cleanup of the existing litter (shell, not code)**

```bash
find /dev/shm -maxdepth 1 -user "$USER" -name 'memoria-floor-seed-*' -exec rm -rf {} +
find /dev/shm -maxdepth 1 -user "$USER" -name 'memoria-test-xdg-*' -exec rm -rf {} +
find "/dev/shm/pytest-of-$USER" -mindepth 1 -maxdepth 1 -user "$USER" -mmin +1440 -exec rm -rf {} + 2>/dev/null
df -h /dev/shm
```

Expected: `/dev/shm` free space rises well above 4 GiB. Record the before/after `df` lines in your report.

- [ ] **Step 2: Write the failing test**

Create `tests/test_conftest_scratch.py`:

```python
"""The tmpfs guard must self-heal: stale scratch litter must not starve it."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

import tests.conftest as conftest_module

pytestmark = pytest.mark.unit


def test_prune_removes_only_stale_memoria_scratch(tmp_path: Path) -> None:
    now = time.time()
    stale_seed = tmp_path / "memoria-floor-seed-old"
    stale_xdg = tmp_path / "memoria-test-xdg-old"
    fresh_seed = tmp_path / "memoria-floor-seed-live"
    unrelated = tmp_path / "someone-elses-dir"
    for d in (stale_seed, stale_xdg, fresh_seed, unrelated):
        d.mkdir()
    two_hours_ago = now - 2 * 3600 - 60
    for d in (stale_seed, stale_xdg):
        import os

        os.utime(d, (two_hours_ago, two_hours_ago))

    pruned = conftest_module._prune_stale_scratch(tmp_path, now=now)

    assert pruned == 2
    assert not stale_seed.exists()
    assert not stale_xdg.exists()
    assert fresh_seed.exists(), "a dir younger than the threshold must survive"
    assert unrelated.exists(), "non-memoria dirs are never touched"


def test_prune_survives_missing_candidate(tmp_path: Path) -> None:
    assert conftest_module._prune_stale_scratch(tmp_path / "absent") == 0
```

- [ ] **Step 3: Run test to verify it fails**

Run: `env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_conftest_scratch.py -v`
Expected: FAIL — `AttributeError: module 'tests.conftest' has no attribute '_prune_stale_scratch'`

- [ ] **Step 4: Implement the prune helper and wire it before the guard**

In `tests/conftest.py`, after the `TMPFS_MIN_FREE_BYTES` constant, add:

```python
# Scratch prefixes this suite creates outside pytest's managed basetemp. Both
# were leaking permanently (mkdtemp with no cleanup) and 823 accumulated
# floor-seed dirs were what starved the tmpfs guard below its 4 GiB floor.
_SCRATCH_PREFIXES = ("memoria-floor-seed-", "memoria-test-xdg-")
_SCRATCH_STALE_SECONDS = 2 * 3600  # no healthy run holds one this long


def _prune_stale_scratch(candidate: Path, now: float | None = None) -> int:
    """Remove this suite's own stale scratch dirs so the guard self-heals."""
    import shutil
    import time as _time

    if not candidate.is_dir():
        return 0
    clock = _time.time() if now is None else now
    pruned = 0
    for entry in candidate.iterdir():
        if not entry.name.startswith(_SCRATCH_PREFIXES):
            continue
        try:
            if clock - entry.stat().st_mtime > _SCRATCH_STALE_SECONDS:
                shutil.rmtree(entry, ignore_errors=True)
                pruned += 1
        except OSError:
            continue
    return pruned
```

In `_tmpfs_tmpdir`, immediately before the `stats = os.statvfs(candidate)` line, add:

```python
    _prune_stale_scratch(candidate)
```

- [ ] **Step 5: Fix both leaks at their source**

In `tests/conftest.py`, replace the `pytest_configure` XDG line (line 67):

```python
def pytest_configure() -> None:
    for key in GIT_ENV_VARS:
        os.environ.pop(key, None)
    os.environ.setdefault("PRE_COMMIT_ALLOW_NO_CONFIG", "1")
    # Secrets hermeticity: never read the developer's ~/.config/memoria/secrets.env.
    xdg_dir = tempfile.mkdtemp(prefix="memoria-test-xdg-")
    os.environ["XDG_CONFIG_HOME"] = xdg_dir
    import atexit
    import shutil

    atexit.register(shutil.rmtree, xdg_dir, ignore_errors=True)
```

In `tests/floor_lib.py`, in `seed_vault` where the cache is created (line 227 vicinity):

```python
    if _SEED_CACHE is None or not (_SEED_CACHE / "vault").exists():
        cache = Path(tempfile.mkdtemp(prefix="memoria-floor-seed-"))
        import atexit

        atexit.register(shutil.rmtree, cache, ignore_errors=True)
        manifest = _build_floor_seed(cache / "vault")
        (cache / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        _SEED_CACHE = cache
```

(`shutil` and `json` are already imported at floor_lib module level; only `atexit` is new, imported locally to keep the diff minimal.)

- [ ] **Step 6: Run tests to verify they pass, plus a leak check**

Run: `env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_conftest_scratch.py tests/test_floor_invariants.py -v`
Expected: PASS. Then `ls /dev/shm | grep -c memoria-floor-seed` before and after the floor test — the count must NOT grow (atexit cleaned the seed cache).

- [ ] **Step 7: Confirm the redirect actually engages now**

Run: `python3 -c "import tests.conftest as c; print(c._TMPDIR)"`
Expected: `/dev/shm` (not `None`). If `None`, `df /dev/shm` and investigate before proceeding — this is the whole point of the task.

- [ ] **Step 8: Commit**

```bash
pre-commit run ruff-format --hook-stage manual --files tests/conftest.py tests/floor_lib.py tests/test_conftest_scratch.py
git add tests/conftest.py tests/floor_lib.py tests/test_conftest_scratch.py
git commit -m "tests: self-healing tmpfs guard; stop leaking floor-seed and xdg scratch dirs"
```

---

### Task 2: Guard `state.connect()` against re-running schema.sql on every connect

Measured basis: `connect()` costs 20.5 ms vs 0.91 ms bare because `_init` unconditionally `executescript`s the full 445-line `schema.sql` on every connection; heavy tests open 300-700 connections. With the guard (measured via monkeypatched throwaway copy): gate replay 40.8s → 12.7s, seeded structural 33.5s → 13.5s, knowledge cycle 27.3s → 9.0s. Also ~18 ms off every shipped CLI command's first connect.

**Files:**
- Modify: `src/memoria_vault/runtime/state/__init__.py:2818-2825` (`_init`)
- Test: `tests/test_schema_version.py` (append)

**Interfaces:**
- Consumes: existing `_init(conn)` contract — raises on unsupported versions, guarantees `user_version == SCHEMA_VERSION` after return.
- Produces: same contract, plus: a connection to an already-current DB executes no DDL.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_schema_version.py` (reuse its existing imports/fixtures style — read the file's head first and match it):

```python
def test_connect_skips_schema_script_when_db_is_current(tmp_path: Path, monkeypatch) -> None:
    """1733: _init re-ran the full schema.sql on EVERY connect (~19.6ms each,
    300-700 connects per heavy test). A current DB must skip the script."""
    import sqlite3

    from memoria_vault.runtime import state

    vault = tmp_path / "vault"
    vault.mkdir()
    with state.connect(vault):
        pass  # first connect creates and initializes the DB

    calls: list[str] = []
    original = sqlite3.Connection.executescript

    def counting(self: sqlite3.Connection, script: str):
        calls.append(script[:40])
        return original(self, script)

    monkeypatch.setattr(sqlite3.Connection, "executescript", counting)
    with state.connect(vault) as conn:
        version = int(conn.execute("PRAGMA user_version").fetchone()[0])

    assert calls == [], "second connect must not re-run schema.sql"
    assert version == state.SCHEMA_VERSION


def test_connect_still_initializes_a_fresh_db(tmp_path: Path) -> None:
    from memoria_vault.runtime import state

    vault = tmp_path / "vault2"
    vault.mkdir()
    with state.connect(vault) as conn:
        version = int(conn.execute("PRAGMA user_version").fetchone()[0])
        tables = {
            r[0]
            for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }

    assert version == state.SCHEMA_VERSION
    assert "concepts" in tables
```

- [ ] **Step 2: Run tests to verify the first fails**

Run: `env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_schema_version.py -k connect_skips -v`
Expected: FAIL — `calls` contains the schema script.

- [ ] **Step 3: Implement the guard**

In `src/memoria_vault/runtime/state/__init__.py`, replace `_init` (lines 2818-2825):

```python
def _init(conn: sqlite3.Connection) -> None:
    current = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if current == SCHEMA_VERSION:
        # 1733: re-running the 445-line schema.sql here cost ~19.6ms on EVERY
        # connect (heavy tests open 300-700 connections; the CLI pays it per
        # command). The script is pure IF-NOT-EXISTS DDL, so on a current DB
        # it was always a semantic no-op. A version mismatch still hard-fails
        # below, and a dev editing schema.sql must bump SCHEMA_VERSION —
        # which tests/test_schema_version.py pins to the DDL already.
        return
    if current != 0:
        raise RuntimeError(f"unsupported Memoria DB schema version: {current}")
    conn.executescript(_schema_sql())
    applied = int(conn.execute("PRAGMA user_version").fetchone()[0])
    if applied != SCHEMA_VERSION:
        raise RuntimeError(f"Memoria DB schema initialization failed: {applied}")
```

- [ ] **Step 4: Run the schema and state suites**

Run: `env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_schema_version.py tests/test_schemas.py -v`
Expected: all PASS, including both new tests.

- [ ] **Step 5: Spot-measure one heavy test (report load with the number)**

Run: `uptime && /usr/bin/time -f "wall %es" env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_worker_knowledge_cycle.py -q`
Expected: materially faster than the ~27-30s pre-guard baseline at comparable load (measured 9.0s at load ~3 during analysis). Record the number and load in your report.

- [ ] **Step 6: Commit**

```bash
pre-commit run ruff-format --hook-stage manual --files src/memoria_vault/runtime/state/__init__.py tests/test_schema_version.py
git add src/memoria_vault/runtime/state/__init__.py tests/test_schema_version.py
git commit -m "state: skip schema.sql re-execution when the DB is already current (#1733 follow-up)"
```

---

### Task 3: Fake-verdict conversion of the redundant 76s seeded-error worker test

Measured basis: the trio re-exercising the seeded-error machinery costs ~256s at profile load. The unit pin (`tests/test_seeded_errors.py:157`) is `@pytest.mark.slow` — already outside the gate. The floor sweep case is the gate's legitimate real run. This task converts the third — `test_worker_runs_seeded_error_verdict_in_disposable_fixture` (76s) — to the fake-verdict pattern its own sibling (`test_seeded_error_verdict_resolves_target_operation_runner`, <1s) already uses, because the runner argument provably never influences the computation (used only for `_runner_identity` metadata and `non_sandbox_licensed`; the integrity checks never see it).

**Files:**
- Modify: `tests/test_worker_product_jobs.py:778-810`

**Interfaces:**
- Consumes: the sibling test's monkeypatch seams — `memoria_vault.runtime.operations.resolve_operation_runner` and `memoria_vault.runtime.seeded_errors.run_seeded_error_verdict`.

- [ ] **Step 1: Rewrite the test**

Replace the body of `test_worker_runs_seeded_error_verdict_in_disposable_fixture` (lines 778-810) with:

```python
def test_worker_runs_seeded_error_verdict_in_disposable_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The worker hands the verdict a DISPOSABLE fixture vault and cleans it up.

    1733: this ran the full real verdict (~76s) to prove two cheap plumbing
    facts. The real computation is pinned by the slow-marked unit contract in
    test_seeded_errors.py and exercised in-gate by the floor sweep's
    run-seeded-error-verdict case; the runner argument provably never reaches
    the integrity checks (seeded_errors.py uses it only for identity
    metadata). A fake verdict keeps both plumbing assertions real: the
    fixture path it receives must be a throwaway outside the vault, and it
    must be gone after the job completes.
    """
    vault = workspace(tmp_path)
    eval_dir = vault / ".memoria/eval"
    eval_dir.mkdir(parents=True)
    shutil.copyfile(
        WORKSPACE_SEED / ".memoria/eval/alpha15-seeded-errors.json",
        eval_dir / "alpha15-seeded-errors.json",
    )
    seen: dict[str, str] = {}

    def fake_verdict(
        vault_path: Path,
        *,
        template_root: Path,
        bundle_path: Path,
        runner: dict,
        operation_id: str,
        context,
    ) -> dict[str, object]:
        seen["fixture_vault"] = str(vault_path)
        assert (vault_path / ".memoria").is_dir(), "fixture vault must be initialized"
        return {"operation_id": operation_id, "mode": runner["mode"], "passed": True}

    monkeypatch.setattr(
        "memoria_vault.runtime.seeded_errors.run_seeded_error_verdict", fake_verdict
    )

    queued = enqueue_operation(
        vault,
        "run-seeded-error-verdict",
        payload={"mode": "test", "target_operation_id": "compile-source-digest"},
        idempotency_key="seeded-verdict",
        actor="operation",
        machine_authored=False,
    )
    done = run_next_job(vault, machine="test-machine")

    assert queued["kind"] == "operation"
    assert done is not None
    assert done["status"] == "done"
    assert done["passed"] is True
    fixture_vault = Path(seen["fixture_vault"])
    assert not fixture_vault.is_relative_to(vault), "fixture must be outside the real vault"
    assert not fixture_vault.exists(), "disposable fixture must be cleaned up after the job"
    assert not (vault / "catalog/sources/seed-source/source.md").exists()
```

Note: `mode` changes from `"live"` to `"test"` — with the verdict faked, requesting the live path buys nothing, and mode is metadata-only to the checks. If `run_next_job`'s result surface for this operation lacks any asserted key with the fake in place, adjust the fake's return dict to carry it — extend the fake, never weaken an assertion.

- [ ] **Step 2: Run the test and its siblings**

Run: `env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_worker_product_jobs.py -k seeded -v`
Expected: all PASS; the converted test completes in ~1-3s. If the disposability assertions fail, read `run_seeded_error_verdict`'s caller in the worker to find the actual TemporaryDirectory seam before adjusting anything — the assertions are the point of the test.

- [ ] **Step 3: Commit**

```bash
pre-commit run ruff-format --hook-stage manual --files tests/test_worker_product_jobs.py
git add tests/test_worker_product_jobs.py
git commit -m "tests: seeded-error worker plumbing via fake verdict; real runs stay in floor sweep and slow pin (#1733 follow-up)"
```

---

### Task 4: Fold the thin-loop's unique assertions into the gate replay; delete the thin loop

Measured basis: `test_cli_thin_knowledge_loop_runs_end_to_end` (70s at profile load) duplicates ~13 of ~15 steps of `test_runtime_gate_replay` verbatim (same DOI `10.1000/alpha`, same fixtures, same sequence; only idempotency-key prefixes differ). Unique content: the work-update metadata assertions, the `project gaps` step, and an export output-path variant the replay ALREADY covers (`test_runtime_gate_replay.py:300` asserts `output_path` from `--output`).

**Files:**
- Modify: `tests/test_runtime_gate_replay.py` (update block at lines 100-111; insertion before the export block at line 285)
- Modify: `tests/test_cli_work_project.py` (delete `test_cli_thin_knowledge_loop_runs_end_to_end`, lines ~304-527)

**Interfaces:**
- Consumes: the replay's `_run_json(capsys, ...)` helper and its `gate-*` idempotency-key convention.

- [ ] **Step 1: Extend the replay's `work update` step with the metadata contract**

In `tests/test_runtime_gate_replay.py`, the current update block (lines 100-111) discards its result. Replace:

```python
    _run_json(
        capsys,
        "work",
        "update",
        "--workspace",
        str(workspace),
        "doi-10.1000_alpha",
        "--research-area",
        "framing",
        "--idempotency-key",
        "gate-update",
    )
```

with:

```python
    updated = _run_json(
        capsys,
        "work",
        "update",
        "--workspace",
        str(workspace),
        "doi-10.1000_alpha",
        "--research-area",
        "framing",
        "--methodology",
        "rct",
        "--idempotency-key",
        "gate-update",
    )
    # Folded from the deleted thin-loop test: update writes list-valued
    # memoria metadata and never invents topics.
    updated_memoria = updated["result"]["work"]["csl_json"]["memoria"]
    assert updated_memoria["research_area"] == ["framing"]
    assert updated_memoria["methodology"] == ["rct"]
    assert "topics" not in updated_memoria
```

- [ ] **Step 2: Insert the `project gaps` step before the export block**

In the same file, immediately before the `export = _run_json(` block (line 285), insert:

```python
    gaps = _run_json(
        capsys,
        "project",
        "gaps",
        "--workspace",
        str(workspace),
        "project-alpha",
        "--seed-term",
        "new area",
        "--dense-threshold",
        "1",
        "--idempotency-key",
        "gate-gaps",
    )
    assert gaps["result"]["gap_count"] >= 1
    assert gaps["result"]["project_path"] == "projects/project-alpha/project.md"
    assert gaps["result"]["argument_gap_count"] >= 1
```

Check the replay's closing `operation_requests` set assertion (lines ~325-337): if it enumerates the exact operations run, add the gaps operation's id to the expected set rather than weakening the assertion.

- [ ] **Step 3: Run the replay to verify the folds pass**

Run: `env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_runtime_gate_replay.py -v`
Expected: PASS with the two folded blocks live. If `--methodology` is rejected by the update surface, check the thin loop's exact flag spelling at `tests/test_cli_work_project.py:360-373` and mirror it.

- [ ] **Step 4: Delete the thin-loop test**

In `tests/test_cli_work_project.py`, delete the entire `test_cli_thin_knowledge_loop_runs_end_to_end` function (the `def` through its final assertion, ~lines 304-527). Delete any now-unused module-level fixtures/imports that only it consumed (run `ruff check tests/test_cli_work_project.py` to catch orphaned imports).

- [ ] **Step 5: Run the remaining file plus the replay together**

Run: `env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_cli_work_project.py tests/test_runtime_gate_replay.py -v`
Expected: all PASS; the work-project file's other tests are untouched.

- [ ] **Step 6: Commit**

```bash
pre-commit run ruff-format --hook-stage manual --files tests/test_runtime_gate_replay.py tests/test_cli_work_project.py
git add tests/test_runtime_gate_replay.py tests/test_cli_work_project.py
git commit -m "tests: fold thin-loop's unique asserts into the gate replay, delete the duplicate loop (#1733 follow-up)"
```

---

### Task 5: Init-template copytree in `helpers.init_cli_workspace`

Measured basis: ~360 real `memoria init` runs per suite (~190 through this one helper), at 0.83-1.9s each vs 0.05s for a copytree of an initialized workspace (35-40x). Precedent: `tests/test_cli_review.py:225-238` already uses a module-scoped copytree template. CI keeps the real filesystem, so this is the lever CI actually feels (~300s aggregate there).

**Files:**
- Modify: `tests/helpers.py:215-221` (`init_cli_workspace`), plus a module-level template cache
- Test: `tests/test_helpers_init_template.py` (create)

**Interfaces:**
- Produces: `init_cli_workspace(tmp_path, capsys) -> Path` — signature unchanged; behavior: returns a workspace byte-equivalent to a fresh `memoria init`.
- Callers needing init variants (`--no-obsidian`, `--dry-run`, onboarding flows, double-init, init-output assertions) do NOT go through this helper today; do not migrate any call site that passes flags.

- [ ] **Step 1: Write the failing test**

Create `tests/test_helpers_init_template.py`:

```python
"""The init template must be indistinguishable from a fresh `memoria init`."""

from __future__ import annotations

from pathlib import Path

import pytest

from memoria_vault.runtime import state
from tests import helpers

pytestmark = pytest.mark.contract


class _NullCapsys:
    def readouterr(self):  # matches the only capsys method the helper uses
        return type("Out", (), {"out": "", "err": ""})()


def test_template_workspace_matches_fresh_init(tmp_path: Path) -> None:
    from memoria_vault.cli import main

    templated = helpers.init_cli_workspace(tmp_path / "a", _NullCapsys())
    fresh = tmp_path / "b" / "workspace"
    assert main(["init", "--workspace", str(fresh), "--yes", "--quiet"]) == 0

    templated_files = {p.relative_to(templated) for p in templated.rglob("*") if p.is_file()}
    fresh_files = {p.relative_to(fresh) for p in fresh.rglob("*") if p.is_file()}
    assert templated_files == fresh_files

    # The DB must be live and current, and the vault git repo intact.
    with state.connect(templated) as conn:
        assert int(conn.execute("PRAGMA user_version").fetchone()[0]) == state.SCHEMA_VERSION
    assert (templated / ".git").is_dir()


def test_two_template_workspaces_are_independent(tmp_path: Path) -> None:
    a = helpers.init_cli_workspace(tmp_path / "a", _NullCapsys())
    b = helpers.init_cli_workspace(tmp_path / "b", _NullCapsys())
    (a / "notes").mkdir(exist_ok=True)
    (a / "notes" / "probe.md").write_text("x", encoding="utf-8")
    assert not (b / "notes" / "probe.md").exists()
```

- [ ] **Step 2: Run to verify current behavior passes it (baseline), then implement**

Run: `env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_helpers_init_template.py -v`
Expected: PASS against the current real-init helper (this is an equivalence pin, written first so the swap must preserve it).

- [ ] **Step 3: Implement the template cache**

In `tests/helpers.py`, replace `init_cli_workspace` (lines 215-221):

```python
_INIT_TEMPLATE: Path | None = None


def _init_template_workspace() -> Path:
    """One real `memoria init` per process; every helper call copies it.

    1733: ~190 call sites ran a real init (0.8-1.9s, ~85% fsync wait) where a
    copytree is 0.05s. The equivalence pin lives in
    tests/test_helpers_init_template.py; call sites needing init flags or
    init-output assertions never used this helper and still run real init.
    """
    global _INIT_TEMPLATE
    if _INIT_TEMPLATE is None or not _INIT_TEMPLATE.exists():
        import atexit
        import tempfile

        from memoria_vault.cli import main

        cache = Path(tempfile.mkdtemp(prefix="memoria-init-template-"))
        atexit.register(shutil.rmtree, cache, ignore_errors=True)
        assert main(["init", "--workspace", str(cache / "workspace"), "--yes", "--quiet"]) == 0
        _INIT_TEMPLATE = cache / "workspace"
    return _INIT_TEMPLATE


def init_cli_workspace(tmp_path: Path, capsys: Any) -> Path:
    workspace = tmp_path / "workspace"
    shutil.copytree(_init_template_workspace(), workspace, symlinks=True)
    capsys.readouterr()
    return workspace
```

Also add `"memoria-init-template-"` to `_SCRATCH_PREFIXES` in `tests/conftest.py` (Task 1's tuple) so a killed run's template is pruned like the other scratch dirs.

- [ ] **Step 4: Run the equivalence pin and the heaviest consumer files**

Run: `env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_helpers_init_template.py tests/test_cli_workspace_requests.py tests/test_cli_doctor_eval.py -v`
Expected: all PASS. Any failure here means the template is NOT equivalent for some consumer — investigate the specific assertion (likely a test asserting on init's own JSON output; such a test must be moved off the helper to a real init, not accommodated by weakening the template).

- [ ] **Step 5: Spot-measure one consumer file (report load)**

Run: `uptime && /usr/bin/time -f "wall %es" env PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_cli_workspace_requests.py -q`
Expected: measurably faster than pre-change at comparable load; record both numbers.

- [ ] **Step 6: Commit**

```bash
pre-commit run ruff-format --hook-stage manual --files tests/helpers.py tests/conftest.py tests/test_helpers_init_template.py
git add tests/helpers.py tests/conftest.py tests/test_helpers_init_template.py
git commit -m "tests: per-process init template behind init_cli_workspace (35-40x per call site) (#1733 follow-up)"
```

---

### Task 6: Full gate, before/after numbers, PR

**Files:** none new.

- [ ] **Step 1: Run the full verify gate and capture the new timing lines**

Run: `python scripts/verify` (in the worktree, nothing else heavy running; note `uptime`).
Expected: `verify: OK`. The per-step timing added by #1735 prints the pytest stage wall — quote it against the pre-plan baseline (2,009s at heavy load / 1,068s at the issue's original load) with the load caveat stated.

- [ ] **Step 2: Push and open the PR**

```bash
git push -u origin wip/test-speed
gh pr create --title "test-suite speedups: restore tmpfs path, connect() schema guard, two redundancy folds (#1733 follow-up)" --body "Implements docs/superpowers/plans/2026-08-03-test-suite-speedups.md: self-healing tmpfs guard + scratch-leak fixes (restores the documented 443s->89s suite lever), state.connect() skips schema.sql on current DBs (measured 2.5-3.5x on DB-heavy tests, also ~18ms off every CLI connect), the redundant 76s seeded-error worker run becomes a fake-verdict plumbing test (real runs stay in the floor sweep and the slow-marked pin), the duplicated 70s thin-loop folds into the gate replay, and init_cli_workspace serves a per-process template (35-40x per call site; the lever CI actually feels). Measured numbers with load context in each commit."
```

- [ ] **Step 3: Merge on green, clean up worktree and branch**

Squash-merge after `verify` + `gitleaks` pass; remove the worktree and `wip/test-speed`; pull main.

---

## Self-review notes (for the executor)

- **Spec coverage:** analysis item 1 (tmpfs) → Task 1; item 2 (connect guard) → Task 2; item 3 trio → Task 3; item 3 thin-loop → Task 4; item 4 (init template) → Task 5. Rejected items are pinned in "Explicitly out of scope" so nobody re-litigates them mid-execution.
- **Verification points deferred to observed code (named resolutions, not TBDs):** Task 3 Step 1's note on the fake's return-dict keys; Task 4 Step 2's note on the closing `operation_requests` set; Task 5 Step 4's rule for consumers that assert init output (move them off the helper, never weaken the template pin).
- **Type consistency:** `_prune_stale_scratch(candidate, now=None) -> int` matches between Task 1's test and implementation; `_SCRATCH_PREFIXES` gains `"memoria-init-template-"` in Task 5 exactly as Task 1 defined the tuple; `init_cli_workspace(tmp_path, capsys) -> Path` signature is unchanged for all ~190 call sites.
