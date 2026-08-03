# Coverage Repairs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the coverage gaps the 2026-08-02 test-coverage analysis confirmed — the unexercised code
sandbox, the check-script gates that mutation testing gutted without a failure, the calibration gate never
observed failing, and the vacuous-test cluster — and delete the one feature that is dead code wearing tests.

**Architecture:** Nine independent tasks, each its own commit and reviewable alone. Task 1 is the only one
touching CI. Tasks are ordered by consequence, not dependency — they can execute in any order and in parallel
worktrees, except that tasks 4 and 5 both add check-script tests and merge cleanest in sequence.

**Tech Stack:** Python 3.12, pytest (+xdist), bubblewrap (bwrap) in CI, AST/mutation verification by hand.

## Execution amendments (2026-08-02)

> Read this before the tasks below. This plan is tracked and is bound for `design-history/` as the frozen
> record of what was planned — but execution in `.claude/worktrees/covrep` (branch `wip/covrep`) disproved
> five of its instructions, and the corrections lived only in that worktree's `.superpowers/sdd/progress.md`
> ledger, which `.gitignore` excludes. This section folds those corrections back into the tracked plan so a
> future reader does not inherit instructions the branch itself disproved.

1. **Task 7's premise was false.** Its text below asserts the `pair_key[0] == pair_key[1]` guard in
   `tier1_tension_candidates` is unreachable and instructs deleting it. It is not: `canonical_id = id or
   work_id or rel`, and only the **ULID** path collapses two files onto one concept row before the pair loop
   runs. With a non-ULID shared frontmatter `id` (or a shared `work_id`), two rows carry the same
   `canonical_id` and the pair loop does reach them — deleting the arm turns `candidate_count` from 0 to 1.
   The guard was untested, not unreachable. It stays; the branch restored it and added
   `test_a_duplicate_non_ulid_canonical_id_reaches_the_pair_loop`, which kills the deletion.

2. **Task 1 Step 1's CI snippet includes `sudo sysctl kernel.apparmor_restrict_unprivileged_userns=0`.** A PI
   ruling made before execution dropped it: try bubblewrap in CI without relaxing the kernel's AppArmor
   hardening first, and add the sysctl only if CI proves it necessary. The branch shipped without it.

3. **Task 2 Step 3's kill-check proves the wrong thing.** It instructs flipping `sha256_file(path) !=
   expected` to `==`. That mutation makes the guard fire whenever the hash *matches* — true immediately after
   a successful run — so it trips the pre-tamper sanity assertion (`verify_code_run(...)["ready"] is True`)
   and the test aborts there, before it ever reaches the tamper assertion the check exists to prove. The
   mutation that actually kills the tamper test disables mismatch detection outright, without inverting the
   ready case. Separately, the deleted-output test as specified used `"42\n"` fixture content; because
   `sha256_file` returns `EMPTY_SHA256` for a missing file rather than raising, a non-empty fixture lets the
   hash-mismatch comparison catch the deletion first, so the `not path.is_file()` operand the test is named
   for never actually runs — the fixture needs empty content to exercise that operand.

4. **Task 5 Step 2 says "Create `tests/test_removed_surface_gate.py`"** — the file already existed, with
   three tests covering `find_violations`. Following the step's snippet verbatim would have overwritten the
   file and deleted that coverage; the corrected approach appends to the existing file and reuses its
   established `as gate` import alias. The step's `match=` regexes also needed `(?s)` and raw-string prefixes
   (the real exit messages contain newlines and periods that `.` does not cross by default), and its assumed
   module-alias import for `test_schema_doc_drift.py` was wrong — that file imports symbols directly, which
   the step's own fallback instruction ("follow the file's existing spelling") already covered.

5. **Task 8 never updates `scripts/checks/removed_surfaces.json`.** In this repo, retiring a runtime-policy
   surface means registering its names in that gate's contract — the prior lane-policy retirement is the
   precedent, registered under `owner: "runtime policy"`. Task 8's Files list (below) does not include the
   registry, so the five retired names (`set_session_skill(`, `clear_session_skill(`, `_session_skill_deny`,
   `compose_skill_deny(`, `skill_deny_write`) went unregistered until a follow-up fix added them; as written,
   nothing would have stopped a future agent re-adding a half-wired `set_session_skill`.

Also: **Task 6's brief undercounted.** It names two dead-both-branch instances (`_review_seam_is_live`, the
`hasattr(cockpit, "trace_panel")` block). The branch closed **five** — the other three
(`_flow_seam_is_live`, a dead trace-panel-pending test, and a structurally impossible `_context_panel`
branch, whose own docstring says the honest-absence arm was deleted) were found by sweeping the file during
review, not by following the brief's finding list.

## Global Constraints

- **The one gate:** every task ends with `PYTEST_XDIST_AUTO_NUM_WORKERS=2 python scripts/verify` →
  `verify: OK`, then commit — a green worktree with an unformatted index is a known trap; `git status
  --porcelain` must be empty after the commit. The gate takes 10–55 min depending on load; run it detached
  (`nohup env ... python scripts/verify > log 2>&1 &`), never under a 10-minute tool timeout, and check
  `pgrep -f 'scripts/verify'` first — never kill another session's gate (scope kills by PID, not pattern).
- **Goldens must not move:** `git status --porcelain tests/fixtures/floor/goldens/` prints nothing, every task.
- **Schema rung 19 untouched.** No task here reads or writes `SCHEMA_VERSION` or `schema.sql`.
- **New test modules** declare a level via module-level `pytestmark` and must contain `import pytest` — a mark
  without the import raises `NameError` at collection and the module's tests vanish from every selection
  silently. After adding a file, confirm it collects:
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest <file> --collect-only -q | tail -1`.
- **Repo-root constant** in tests is `from tests.paths import ROOT` (runtime-free leaf) — never re-derive from
  `__file__`, and never import `tests.helpers` from a test that otherwise has no first-party imports.
- Stage explicit paths; never unbounded `git add` (a PreToolUse hook rejects it). `git stash` is forbidden.
  Commit style is plain (`area: what changed`). No dual dotted paths, no shims.
- **Every new guard gets a kill-check**: break the behavior it claims to catch, watch it fail, restore
  byte-for-byte, verify with `git status`. A guard never observed failing is decoration — three tests in this
  very plan exist because that rule was skipped once.

---

### Task 1: The sandbox executes for real — bwrap in CI, required there, and behaviorally tested

`runtime/code/runner.py` is 41% covered and the missing 59% is the sandbox itself. `bwrap` is installed
neither locally nor in CI; `--unshare-net`, `--ro-bind`, `--die-with-parent` appear in zero tests; deleting
`--unshare-net` fails nothing today. This task makes CI execute the sandbox and pins each isolation property
behaviorally. The skip/require split matters: locally the tests skip when bwrap is absent (the `pwsh`
precedent), but CI sets `MEMORIA_REQUIRE_SANDBOX=1` so a skip there is a **failure** — otherwise a CI image
change silently regresses to never running them again.

**Files:**
- Modify: `.github/workflows/verify.yml` (after the "Install runtime + dev tooling" step, ~line 45; and the
  `Run verify` step's `env:` block)
- Create: `tests/test_code_sandbox.py`

**Interfaces:**
- Consumes: `runtime.code.records.create_code_artifact(vault, project, artifact_id, *, approved_command,
  declared_outputs=...)` → dict with `source_dir` (`projects/<p>/code/<a>/src`), `output_dir`, `record_path`;
  `runtime.code.runner.run_artifact(vault, artifact_id, *, run_id=None, timeout_s=30, max_output_bytes=...)`;
  `runtime.code.runner.execution_availability(vault) -> Availability`;
  `state.code_run(vault, run_id)` → row with `state`, `output_hashes`, `stdout_sha256`, `artifact_id`;
  stdout file at `.memoria/code-runs/<normalized run_id>/stdout.txt`.
- Produces: env contract `MEMORIA_REQUIRE_SANDBOX=1` (skip becomes fail), consumed by nothing else in this
  plan but load-bearing for CI.

- [ ] **Step 1: Enable bwrap in CI**

In `.github/workflows/verify.yml`, insert after the "Install runtime + dev tooling" step:

```yaml
      - name: Enable the code-execution sandbox (bubblewrap)
        run: |
          sudo apt-get update -qq
          sudo apt-get install -y -qq bubblewrap
          # Ubuntu 24.04 restricts unprivileged user namespaces via AppArmor by
          # default; bwrap needs them. CI-only relaxation — WSL and desktop
          # distros this product targets already permit them.
          sudo sysctl -qw kernel.apparmor_restrict_unprivileged_userns=0 || true
```

And add to the `Run verify` step's `env:` block (it already carries `VERIFY_DOCS_ONLY`):

```yaml
          MEMORIA_REQUIRE_SANDBOX: "1"
```

- [ ] **Step 2: Try to enable bwrap locally**

Run: `sudo -n apt-get install -y bubblewrap 2>&1 || echo "NO-SUDO"`
If it installs, every test below runs locally. If `NO-SUDO`, the tests will skip locally and **CI is the
proof** — say so explicitly in your report; do not simulate green. The require-flag makes a CI skip
impossible, so the gap cannot silently reopen either way.

- [ ] **Step 3: Write the sandbox tests**

Create `tests/test_code_sandbox.py`:

```python
"""The bwrap sandbox's isolation properties, each pinned behaviorally.

These execute real code inside the real sandbox. Locally they skip when bwrap
is unavailable (the pwsh precedent); under MEMORIA_REQUIRE_SANDBOX=1 (CI) a
skip becomes a hard failure, so a runner-image change cannot silently return
this module to never running.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.code.records import create_code_artifact
from memoria_vault.runtime.code.runner import execution_availability, run_artifact
from memoria_vault.runtime.policy.audit import sha256_file

pytestmark = pytest.mark.runtime


@pytest.fixture()
def sandbox_vault(tmp_path: Path) -> Path:
    availability = execution_availability(tmp_path)
    if not availability.available:
        if os.environ.get("MEMORIA_REQUIRE_SANDBOX") == "1":
            pytest.fail(f"sandbox required but unavailable: {availability.reason}")
        pytest.skip(f"bwrap sandbox unavailable: {availability.reason}")
    return tmp_path


def _probe_artifact(vault: Path, artifact_id: str, script: str, **kwargs) -> dict:
    artifact = create_code_artifact(
        vault,
        "project-alpha",
        artifact_id,
        approved_command=["python3", "main.py"],
        **kwargs,
    )
    source = vault / artifact["source_dir"]
    source.mkdir(parents=True, exist_ok=True)
    (source / "main.py").write_text(script, encoding="utf-8")
    return artifact


def _stdout(vault: Path, run: dict) -> str:
    return (vault / run["stdout_path"]).read_text(encoding="utf-8")


def test_sandboxed_code_has_no_network(sandbox_vault: Path) -> None:
    """--unshare-net is the sandbox's core claim; deleting it fails nowhere else."""
    _probe_artifact(
        sandbox_vault,
        "net-probe",
        "import socket\n"
        "try:\n"
        "    socket.create_connection(('1.1.1.1', 53), timeout=3)\n"
        "    print('NET_OK')\n"
        "except OSError as exc:\n"
        "    print(f'NET_BLOCKED:{type(exc).__name__}')\n",
    )

    run = run_artifact(sandbox_vault, "net-probe", run_id="net-1")

    out = _stdout(sandbox_vault, run)
    assert "NET_OK" not in out
    assert "NET_BLOCKED" in out
    assert run["state"] == "succeeded"  # blocked network is the *expected* outcome


def test_host_environment_does_not_leak_into_the_sandbox(
    sandbox_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MEMORIA_SECRET_PROBE", "leak-me")
    _probe_artifact(
        sandbox_vault,
        "env-probe",
        "import json, os\nprint(json.dumps(sorted(os.environ)))\n",
    )

    run = run_artifact(sandbox_vault, "env-probe", run_id="env-1")

    keys = set(json.loads(_stdout(sandbox_vault, run)))
    assert "MEMORIA_SECRET_PROBE" not in keys
    assert {"HOME", "PATH"} <= keys


def test_the_workspace_bind_is_read_only(sandbox_vault: Path) -> None:
    _probe_artifact(
        sandbox_vault,
        "ro-probe",
        "try:\n"
        "    open('/workspace/poison.txt', 'w').write('x')\n"
        "    print('WRITE_OK')\n"
        "except OSError as exc:\n"
        "    print(f'WRITE_BLOCKED:{type(exc).__name__}')\n",
    )

    run = run_artifact(sandbox_vault, "ro-probe", run_id="ro-1")

    assert "WRITE_BLOCKED" in _stdout(sandbox_vault, run)
    source = sandbox_vault / "projects/project-alpha/code/ro-probe/src"
    assert not (source / "poison.txt").exists()  # the host side stayed clean


def test_outputs_land_on_the_host_and_their_hashes_are_recorded(sandbox_vault: Path) -> None:
    out_rel = "projects/project-alpha/code/out-probe/outputs/result.txt"
    _probe_artifact(
        sandbox_vault,
        "out-probe",
        "open('/outputs/result.txt', 'w').write('42\\n')\n",
        declared_outputs=[out_rel],
    )

    run = run_artifact(sandbox_vault, "out-probe", run_id="out-1")

    host_file = sandbox_vault / out_rel
    assert host_file.read_text(encoding="utf-8") == "42\n"
    assert run["state"] == "succeeded"
    assert run["output_hashes"] == {out_rel: sha256_file(host_file)}


def test_a_run_that_overstays_its_timeout_is_failed_and_says_so(sandbox_vault: Path) -> None:
    _probe_artifact(sandbox_vault, "slow-probe", "import time\ntime.sleep(60)\n")

    run = run_artifact(sandbox_vault, "slow-probe", run_id="slow-1", timeout_s=2)

    assert run["state"] == "failed"
    assert run["timeout_result"] == "timeout"
    assert run["exit_status"] == 124


def test_stdout_is_truncated_at_the_declared_cap(sandbox_vault: Path) -> None:
    _probe_artifact(sandbox_vault, "loud-probe", "print('x' * 1000)\n")

    run = run_artifact(sandbox_vault, "loud-probe", run_id="loud-1", max_output_bytes=64)

    raw = (sandbox_vault / run["stdout_path"]).read_bytes()
    assert len(raw) <= 64
```

If `state.record_code_run`'s returned row spells any of these keys differently (`stdout_path`,
`exit_status`), read the row shape from `state.code_run(vault, run_id)` — those keys are proven by
`runtime/code/runs.py`'s own reads — and adjust the *test* to the row, never the row to the test.

- [ ] **Step 4: Run them (or watch them skip, per step 2)**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_code_sandbox.py -q -p no:randomly`
Expected with bwrap: 6 passed. Without: 6 skipped, each naming the reason.
Also confirm the require-flag flips skips to failures:
`MEMORIA_REQUIRE_SANDBOX=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_code_sandbox.py -q 2>&1 | tail -2`
Expected without bwrap: 6 **failed** ("sandbox required but unavailable"). That inversion is itself the guard.

- [ ] **Step 5: Kill-check `--unshare-net` (only if bwrap runs locally)**

Temporarily delete the `"--unshare-net",` line from `_run_with_bwrap` in
`src/memoria_vault/runtime/code/runner.py` (leave `_bwrap_proof`'s copy — the availability probe is not the
sandbox). Run the net test. Expected: FAIL with `NET_OK` in stdout. Restore byte-for-byte; confirm
`git status --porcelain src/` is empty. If bwrap is unavailable locally, record in your report that this
kill-check is deferred to a deliberate CI experiment and must not be silently skipped forever.

- [ ] **Step 6: Full gate, then commit**

```bash
git add .github/workflows/verify.yml tests/test_code_sandbox.py
git commit -m "sandbox: execute bwrap isolation in CI and pin each property behaviorally"
```

---

### Task 2: `verify_code_run`'s refusals are produced, not assumed

All three refusal branches of the function that decides whether computed evidence counts as grounds are
unproduced: `missing-code-run`, non-`succeeded` state, and `output-hash-mismatch` (a declared output changed
on disk *after* the run). No sandbox needed — `state.record_code_run` is the direct producer.

**Files:**
- Modify: `tests/test_code_artifacts.py` (append; `pytestmark = pytest.mark.runtime` already present)

**Interfaces:**
- Consumes: `runtime.code.runs.verify_code_run(vault, run_id) -> dict` — exact shapes from source:
  `{"ready": False, "reason": "missing-code-run"}`, `{"ready": False, "reason": <state>}`,
  `{"ready": False, "reason": "output-hash-mismatch", "path": <rel>}`,
  `{"ready": True, "run_id": ..., "artifact_id": ...}`.

- [ ] **Step 1: Write the four tests**

Append to `tests/test_code_artifacts.py` (add `from memoria_vault.runtime.code.runs import verify_code_run`
to the imports):

```python
def _succeeded_run(tmp_path: Path, output_text: str = "42\n") -> str:
    output = tmp_path / "projects/project-alpha/code/analysis/outputs/result.txt"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(output_text, encoding="utf-8")
    output_rel = output.relative_to(tmp_path).as_posix()
    create_code_artifact(
        tmp_path,
        "project-alpha",
        "analysis",
        approved_command=["python3", "main.py"],
        declared_outputs=[output_rel],
    )
    state.record_code_run(
        tmp_path,
        run_id="run-1",
        artifact_id="analysis",
        command=["python3", "main.py"],
        cwd="projects/project-alpha/code/analysis/src",
        output_hashes={output_rel: sha256_file(output)},
        exit_status=0,
        sandbox_backend="bwrap",
        sandbox_profile_hash="sha256:" + "0" * 64,
        run_state="succeeded",
    )
    return output_rel


def test_verify_code_run_refuses_an_unknown_run(tmp_path: Path) -> None:
    assert verify_code_run(tmp_path, "no-such-run") == {
        "ready": False,
        "reason": "missing-code-run",
    }


def test_verify_code_run_refuses_a_run_that_did_not_succeed(tmp_path: Path) -> None:
    create_code_artifact(
        tmp_path, "project-alpha", "analysis", approved_command=["python3", "main.py"]
    )
    state.record_code_run(
        tmp_path,
        run_id="run-1",
        artifact_id="analysis",
        command=["python3", "main.py"],
        cwd="projects/project-alpha/code/analysis/src",
        exit_status=1,
        sandbox_backend="bwrap",
        sandbox_profile_hash="sha256:" + "0" * 64,
        run_state="failed",
    )

    assert verify_code_run(tmp_path, "run-1") == {"ready": False, "reason": "failed"}


def test_verify_code_run_refuses_an_output_rewritten_after_the_run(tmp_path: Path) -> None:
    """The tamper case: grounds must be exactly what the run produced."""
    output_rel = _succeeded_run(tmp_path)
    assert verify_code_run(tmp_path, "run-1")["ready"] is True  # sane before the tamper

    (tmp_path / output_rel).write_text("43\n", encoding="utf-8")

    assert verify_code_run(tmp_path, "run-1") == {
        "ready": False,
        "reason": "output-hash-mismatch",
        "path": output_rel,
    }


def test_verify_code_run_refuses_an_output_deleted_after_the_run(tmp_path: Path) -> None:
    output_rel = _succeeded_run(tmp_path)

    (tmp_path / output_rel).unlink()

    verdict = verify_code_run(tmp_path, "run-1")
    assert verdict == {"ready": False, "reason": "output-hash-mismatch", "path": output_rel}
```

- [ ] **Step 2: Run them**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_code_artifacts.py -q -p no:randomly`
Expected: all pass, including the four new ones.

- [ ] **Step 3: Kill-check the tamper branch**

In `src/memoria_vault/runtime/code/runs.py`, temporarily change `sha256_file(path) != expected` to
`sha256_file(path) == expected`. Expected: the rewritten-output test **and** the ready-before-tamper
assertion both fail. Restore byte-for-byte; `git status --porcelain src/` empty.

- [ ] **Step 4: Full gate, then commit**

```bash
git add tests/test_code_artifacts.py
git commit -m "tests: produce all three verify_code_run refusals"
```

---

### Task 3: The calibration gate is observed failing

`_bar_failures` decides pass/fail for the seeded-error verdict; every non-empty `bar_failures` in the suite
today is a hand-written literal, and the only real run asserts `== []`. Invert one comparison and the gate
reports PASS on a model that misses seeded errors. Also: `seeded_probe_review_batch`'s payload survives
replacing every field with `"MUT"` — the probes are proven only to be N sentinel-stamped dicts.

**Files:**
- Modify: `tests/test_seeded_errors.py` (append; add `_bar_failures` to its `seeded_errors` imports)
- Modify: `tests/test_gate_calibration.py` (append)

**Interfaces:**
- Consumes: `seeded_errors._bar_failures(metrics, bars) -> list[str]` — strict `<` against `*_min`, strict
  `>` against `*_max`; `seeded_probe_review_batch(cases, *, max_items=None)` — default cap 5, floor
  `max(1, int(max_items))`, per-case defaults `expected_disposition="reject"`, `certainty="low"`.

- [ ] **Step 1: Write the `_bar_failures` tests**

Append to `tests/test_seeded_errors.py`:

```python
_PASSING_METRICS = {
    "recall": 0.9,
    "false_positive_rate": 0.05,
    "rollback_completeness": 0.95,
    "residual_error_rate": 0.02,
    "checkpoint_value_rate": 0.8,
}
_BARS = {
    "recall_min": 0.8,
    "false_positive_rate_max": 0.1,
    "rollback_completeness_min": 0.9,
    "residual_error_rate_max": 0.05,
    "checkpoint_value_rate_min": 0.5,
}


def test_bar_failures_is_empty_when_every_bar_holds() -> None:
    assert _bar_failures(dict(_PASSING_METRICS), dict(_BARS)) == []


@pytest.mark.parametrize(
    ("metric", "breached_value"),
    [
        ("recall", 0.79),
        ("false_positive_rate", 0.11),
        ("rollback_completeness", 0.89),
        ("residual_error_rate", 0.06),
        ("checkpoint_value_rate", 0.49),
    ],
)
def test_each_bar_fails_alone_when_breached(metric: str, breached_value: float) -> None:
    metrics = dict(_PASSING_METRICS)
    metrics[metric] = breached_value

    assert _bar_failures(metrics, dict(_BARS)) == [metric]


@pytest.mark.parametrize(
    "metric",
    ["recall", "false_positive_rate", "rollback_completeness",
     "residual_error_rate", "checkpoint_value_rate"],
)
def test_a_metric_exactly_on_its_bar_passes(metric: str) -> None:
    """The comparisons are strict: landing on the bar is a pass. Pinning the
    boundary is what makes a later `<` -> `<=` edit visible (the 0.999/1.0
    lesson from the dwell tests)."""
    metrics = dict(_PASSING_METRICS)
    bar_key = next(k for k in _BARS if k.startswith(metric))
    metrics[metric] = float(_BARS[bar_key])

    assert _bar_failures(metrics, dict(_BARS)) == []


def test_multiple_breaches_report_in_bar_order() -> None:
    metrics = dict(_PASSING_METRICS)
    metrics["recall"] = 0.0
    metrics["checkpoint_value_rate"] = 0.0

    assert _bar_failures(metrics, dict(_BARS)) == ["recall", "checkpoint_value_rate"]
```

- [ ] **Step 2: Strengthen the probe-batch tests**

Append to `tests/test_gate_calibration.py`:

```python
def test_probe_payload_carries_the_case_not_a_sentinel_shape() -> None:
    """Replacing any field with a constant must fail here; before this test the
    whole payload survived a wholesale "MUT" substitution."""
    cases = [
        {
            "id": "case-a",
            "target_id": "notes/a.md",
            "error_class": "missing-evidence",
            "expected_disposition": "quarantine",
            "certainty": "high",
        }
    ]

    [probe] = seeded_probe_review_batch(cases)["probes"]

    assert probe["case_id"] == "case-a"
    assert probe["target_id"] == "notes/a.md"
    assert probe["error_class"] == "missing-evidence"
    assert probe["expected_disposition"] == "quarantine"
    assert probe["certainty"] == "high"


def test_probe_defaults_come_from_the_builder_not_the_case() -> None:
    [probe] = seeded_probe_review_batch([{"id": "bare", "target_id": "notes/b.md"}])["probes"]

    assert probe["expected_disposition"] == "reject"
    assert probe["certainty"] == "low"
    assert probe["error_class"] == ""
    assert "reviewer should check" in probe["self_rebuttal"]


def test_default_cap_is_five_and_the_floor_is_one() -> None:
    cases = [{"id": f"c{i}", "target_id": f"notes/{i}.md"} for i in range(7)]

    default_batch = seeded_probe_review_batch(cases)
    floored_batch = seeded_probe_review_batch(cases, max_items=0)

    assert default_batch["max_items_per_batch"] == 5
    assert len(default_batch["probes"]) == 5
    assert floored_batch["max_items_per_batch"] == 1
    assert len(floored_batch["probes"]) == 1
```

- [ ] **Step 3: Run both files, then kill-check**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_seeded_errors.py tests/test_gate_calibration.py -q -p no:randomly -k 'bar or probe or cap'`
Expected: all pass.

Kill-checks (each: mutate, run the named test, expect FAIL, restore, `git status` clean):
1. `seeded_errors.py` `_bar_failures`: `metrics["recall"] < float(...)` → `<=` — expected: the
   exactly-on-its-bar recall case fails.
2. `metrics["recall"] < ...` → `>` — expected: the breached-recall case fails.
3. `seeded_probe_review_batch`: `"case_id": str(case.get("id") or "")` → `"case_id": "MUT"` — expected:
   `test_probe_payload_carries_the_case_not_a_sentinel_shape` fails. (This exact mutation survived the whole
   suite before this task.)

- [ ] **Step 4: Full gate, then commit**

```bash
git add tests/test_seeded_errors.py tests/test_gate_calibration.py
git commit -m "tests: observe the calibration gate failing, pin the probe payload"
```

---

### Task 4: The terminology gate gets the behavioral tests its own README demands

`checked_terminology_gate.py` survived 6 of 6 mutations — including inverting `if not root.exists()`, which
makes it scan nothing and print `ok` forever. Its only presence in `tests/` is its command string in the
roster pin. `tests/README.md:48` states the rule this violates. The script's `errors()` hardcodes the repo
root, so step 1 parameterizes it (no behavior change at the CLI) and step 2 tests it on temp trees.

**Files:**
- Modify: `scripts/checks/checked_terminology_gate.py`
- Create: `tests/test_checked_terminology_gate.py`

**Interfaces:**
- Produces: `checked_terminology_gate.errors(base: Path = ROOT) -> list[str]` — same findings format
  (`<rel>:<line>: checked must not mean approved/verified/trusted`); `main()` unchanged.

- [ ] **Step 1: Parameterize the scan root**

In `scripts/checks/checked_terminology_gate.py`, replace `_skip` and `errors`:

```python
def _skip(path: Path, base: Path) -> bool:
    rel = path.relative_to(base).as_posix()
    return any(rel == part or rel.startswith(part + "/") for part in SKIP_PARTS)


def errors(base: Path = ROOT) -> list[str]:
    out: list[str] = []
    for root_name in SCAN_ROOTS:
        root = base / root_name
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.suffix not in SUFFIXES or _skip(path, base):
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for line_no, line in enumerate(lines, start=1):
                if any(pattern.search(line) for pattern in PATTERNS):
                    rel = path.relative_to(base).as_posix()
                    out.append(f"{rel}:{line_no}: checked must not mean approved/verified/trusted")
    return out
```

Run the real gate to prove the refactor is inert: `python3 scripts/checks/checked_terminology_gate.py`
Expected: `checked-terminology-gate: ok` (same as before the change).

- [ ] **Step 2: Write the behavioral tests**

Create `tests/test_checked_terminology_gate.py`:

```python
"""Positive and negative cases for the checked-terminology gate.

Before this file, all six mutation sites in the gate survived the whole suite
-- including inverting the scan-root existence check, which makes the gate
scan nothing and print ok forever. Each test below names the mutation class
it kills.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.checks import checked_terminology_gate as gate

pytestmark = pytest.mark.static


def _tree(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp_path


def test_forward_order_violation_is_found(tmp_path: Path) -> None:
    """Kills: a never-matching first pattern, and the scan-root existence
    inversion (an existing root that gets skipped finds nothing)."""
    base = _tree(tmp_path, {"docs/a.md": "intro\nA checked concept is approved by the PI.\n"})

    assert gate.errors(base) == [
        "docs/a.md:2: checked must not mean approved/verified/trusted"
    ]


def test_reversed_order_violation_is_found(tmp_path: Path) -> None:
    """Kills a dropped second pattern: bad word before 'checked'."""
    base = _tree(tmp_path, {"docs/a.md": "Approved once the item is checked.\n"})

    assert len(gate.errors(base)) == 1


def test_clean_wording_produces_no_finding(tmp_path: Path) -> None:
    """Kills a match-everything pattern."""
    base = _tree(
        tmp_path,
        {"docs/a.md": "A checked concept has passed the sha256 read barrier only.\n"},
    )

    assert gate.errors(base) == []


def test_trusted_writer_is_exempt_by_the_lookahead(tmp_path: Path) -> None:
    base = _tree(tmp_path, {"docs/a.md": "Every checked write goes through the trusted-writer.\n"})

    assert gate.errors(base) == []


def test_skip_parts_are_skipped(tmp_path: Path) -> None:
    """Kills an inverted _skip: a violation inside docs/superpowers must not count."""
    base = _tree(
        tmp_path,
        {
            "docs/superpowers/x.md": "checked means approved here, freely.\n",
            "docs/a.md": "clean\n",
        },
    )

    assert gate.errors(base) == []


def test_unrostered_suffixes_are_ignored(tmp_path: Path) -> None:
    base = _tree(tmp_path, {"docs/a.txt": "A checked concept is approved.\n"})

    assert gate.errors(base) == []


def test_a_missing_scan_root_contributes_nothing_but_an_existing_one_scans(
    tmp_path: Path,
) -> None:
    """The exists-check inversion: with only docs/ present, src/ and scripts/
    must be silently absent while docs/ is still genuinely scanned."""
    base = _tree(tmp_path, {"docs/a.md": "A checked concept is a verified concept.\n"})

    findings = gate.errors(base)

    assert len(findings) == 1 and findings[0].startswith("docs/a.md:1:")


def test_the_window_is_one_hundred_characters(tmp_path: Path) -> None:
    """Kills a widened window: the two words 150 chars apart must not match."""
    base = _tree(
        tmp_path,
        {"docs/a.md": "checked " + ("x" * 150) + " approved\n"},
    )

    assert gate.errors(base) == []


def test_matching_is_case_insensitive(tmp_path: Path) -> None:
    base = _tree(tmp_path, {"docs/a.md": "CHECKED items are APPROVED.\n"})

    assert len(gate.errors(base)) == 1
```

- [ ] **Step 3: Run, then kill the six mutants**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_checked_terminology_gate.py -q`
Expected: 9 passed.

Then, one at a time (mutate, run this file, expect ≥1 FAIL, restore, `git status` clean):
1. `if not root.exists():` → `if root.exists():` — expected killer: the missing-scan-root test.
2. `path.suffix not in SUFFIXES` → `in` — killers: forward-order (its .md stops matching) and the .txt test.
3. Delete the second entry of `PATTERNS` — killer: reversed-order.
4. `_skip(...)` result negated — killer: skip-parts.
5. `{0,100}` → `{0,200}` in both patterns — killer: the window test.
6. Drop `re.I` — killer: case-insensitivity.

Record the six kill results in the commit message body or the task report.

- [ ] **Step 4: Full gate, then commit**

```bash
git add scripts/checks/checked_terminology_gate.py tests/test_checked_terminology_gate.py
git commit -m "gates: behavioral tests for the terminology gate; scan root parameterized"
```

---

### Task 5: Harden the other three check scripts' untested arms

`wheel_gate.py` has only its roster-string pin; `removed_surface_gate.py` had 2 surviving mutations (both
`or`→`and` in input validation); `schema_doc_drift.py` had 3 (type-guard boolops and the single-match rule in
`_find_doc`).

**Files:**
- Create: `tests/test_wheel_gate_checks.py`
- Create: `tests/test_removed_surface_gate.py`
- Modify: `tests/test_schema_doc_drift.py` (append)

**Interfaces:**
- Consumes: `wheel_gate._check_contents(wheel: Path)` / `_expected_members()` (exits via `sys.exit(str)`);
  `removed_surface_gate.load_contract(path) -> Contract` (raises `ValueError`);
  `schema_doc_drift.check_schema_docs(schemas_dir, docs_dir) -> list[str]` and `load_types(schemas_dir)`.

- [ ] **Step 1: Wheel-gate unit tests**

Create `tests/test_wheel_gate_checks.py`:

```python
"""The wheel gate's two content legs, exercised without building a wheel.

The gate's integration behavior (build, install, probe) runs inside verify
itself; these pin the *decision* logic so a broken leg cannot hide behind a
green build.
"""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

import pytest

from scripts.checks import wheel_gate

pytestmark = pytest.mark.static


def _wheel(tmp_path: Path, members: dict[str, bytes]) -> Path:
    path = tmp_path / "memoria_vault-0.0.0-py3-none-any.whl"
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return path


def test_a_missing_tracked_file_fails_the_forward_leg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        wheel_gate, "_expected_members", lambda: {"memoria_vault/a.py", "memoria_vault/b.py"}
    )
    wheel = _wheel(tmp_path, {"memoria_vault/a.py": b""})

    with pytest.raises(SystemExit, match="missing from the wheel.*memoria_vault/b.py"):
        wheel_gate._check_contents(wheel)


def test_an_untracked_member_fails_the_reverse_leg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(wheel_gate, "_expected_members", lambda: {"memoria_vault/a.py"})
    wheel = _wheel(
        tmp_path, {"memoria_vault/a.py": b"", "memoria_vault/ghost.py": b""}
    )

    with pytest.raises(SystemExit, match="no tracked source.*memoria_vault/ghost.py"):
        wheel_gate._check_contents(wheel)


def test_dist_info_members_are_not_treated_as_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(wheel_gate, "_expected_members", lambda: {"memoria_vault/a.py"})
    wheel = _wheel(
        tmp_path,
        {"memoria_vault/a.py": b"", "memoria_vault-0.0.0.dist-info/METADATA": b""},
    )

    wheel_gate._check_contents(wheel)  # must not raise


def test_an_empty_git_listing_is_a_loud_failure_not_a_vacuous_pass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """git failing must not make `expected` empty and both legs meaningless."""
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout="", stderr=""),
    )

    with pytest.raises(SystemExit, match="git ls-files returned nothing"):
        wheel_gate._expected_members()
```

- [ ] **Step 2: removed-surface contract validation tests**

Create `tests/test_removed_surface_gate.py`:

```python
"""Malformed-contract arms of the removed-surface gate (the two or->and survivors)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.checks import removed_surface_gate as rsg

pytestmark = pytest.mark.static

_VALID = {
    "search_roots": ["src"],
    "allow_text_files": [],
    "rules": [
        {"kind": "text", "needle": "gone_symbol", "owner": "#1", "reason": "removed"}
    ],
}


def _contract(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_a_valid_contract_loads(tmp_path: Path) -> None:
    contract = rsg.load_contract(_contract(tmp_path, _VALID))
    assert contract.rules[0].needle == "gone_symbol"


@pytest.mark.parametrize("bad_roots", ["src", ["src", 7]], ids=["not-a-list", "non-string"])
def test_search_roots_must_be_a_list_of_strings(tmp_path: Path, bad_roots) -> None:
    data = dict(_VALID, search_roots=bad_roots)

    with pytest.raises(ValueError, match="search_roots must be a list of strings"):
        rsg.load_contract(_contract(tmp_path, data))


@pytest.mark.parametrize("missing", ["needle", "owner", "reason"])
def test_each_rule_field_is_required_alone(tmp_path: Path, missing: str) -> None:
    """or->and in the three-way check survives unless each field is dropped alone."""
    rule = dict(_VALID["rules"][0])
    rule[missing] = ""
    data = dict(_VALID, rules=[rule])

    with pytest.raises(ValueError, match="must include needle, owner, and reason"):
        rsg.load_contract(_contract(tmp_path, data))
```

- [ ] **Step 3: schema-doc-drift type-guard tests**

Append to `tests/test_schema_doc_drift.py` (match its existing imports; it already imports the module):

```python
def test_load_types_ignores_non_mapping_and_untyped_yaml(tmp_path: Path) -> None:
    """The and->or survivors: a list document and a dict without a string
    `type` must both be skipped, each alone."""
    types_dir = tmp_path / "schemas" / "types"
    types_dir.mkdir(parents=True)
    (types_dir / "list.yaml").write_text("- a\n- b\n", encoding="utf-8")
    (types_dir / "untyped.yaml").write_text("category: x\n", encoding="utf-8")
    (types_dir / "good.yaml").write_text("type: note\ncategory: x\n", encoding="utf-8")

    types = schema_doc_drift.load_types(tmp_path / "schemas")

    assert set(types) == {"note"}


def test_find_doc_uses_the_match_only_when_it_is_unique(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    (docs / "a").mkdir(parents=True)
    (docs / "b").mkdir(parents=True)
    (docs / "a" / "document-types.md").write_text("x", encoding="utf-8")

    unique = schema_doc_drift._find_doc(docs, "document-types.md")
    assert unique == docs / "a" / "document-types.md"

    (docs / "b" / "document-types.md").write_text("x", encoding="utf-8")
    ambiguous = schema_doc_drift._find_doc(docs, "document-types.md")
    assert ambiguous == docs / "document-types.md"  # the deterministic fallback
```

If `tests/test_schema_doc_drift.py` imports the module under a different name, follow the file's existing
import spelling rather than this snippet's.

- [ ] **Step 4: Run all three, kill-check the named survivors, full gate, commit**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_wheel_gate_checks.py tests/test_removed_surface_gate.py tests/test_schema_doc_drift.py -q`
Expected: all pass, and the two new files each collect (see Global Constraints).

Kill-checks: `removed_surface_gate.py:36` and `:55` `or`→`and` (each: exactly the matching parametrized case
fails); `schema_doc_drift.py:31` `and`→`or` (the load_types test fails). Restore each byte-for-byte.

```bash
git add tests/test_wheel_gate_checks.py tests/test_removed_surface_gate.py tests/test_schema_doc_drift.py
git commit -m "gates: pin the decision arms of wheel, removed-surface, and schema-drift checks"
```

---

### Task 6: Vacuous test repairs — loudness push-log ghosts and cockpit both-branch conditionals

Four `test_loudness.py` tests assert the absence of a `*push*.jsonl` that nothing has written since
`31e3bc1a` deleted the Telegram push feature — three of their bodies can be deleted entirely and they still
pass. And `test_cockpit.py` carries `if hasattr(...)/else` and `if _review_seam_is_live()/else` blocks whose
pending arms are dead now that `trace_panel` and the review seam have landed — a test asserting whichever
branch the implementation takes distinguishes nothing.

**Files:**
- Modify: `tests/test_loudness.py` (replace the four push-log tests)
- Modify: `tests/test_cockpit.py` (collapse the conditional assertions; sites near lines 554, 655, 1330)

**Interfaces:**
- Consumes: `inbox.write_finding(vault, kind, title, body, raised_by, *, loudness=..., dedupe_slug=...)`,
  `inbox.write_work_prompt(...)`, `inbox.write_proposal(...)` — exactly as the current tests call them; the
  existing `_card_loudness(path)` helper at the bottom of `test_loudness.py`.

- [ ] **Step 1: Replace the four loudness tests**

In `tests/test_loudness.py`, replace `test_alert_card_writes_no_push_log`,
`test_deduped_alert_finding_writes_no_push_log`, `test_deduped_alert_work_prompt_writes_no_push_log`, and
`test_notice_card_writes_no_push_log` with:

```python
def test_alert_finding_lands_on_the_card_at_alert(tmp_path):
    inbox.write_finding(
        tmp_path, "alert", "Critical drift", "system is stopped", "linter", loudness="alert"
    )

    [card] = list((tmp_path / "inbox").glob("*.md"))
    assert _card_loudness(card) == "alert"


def test_a_deduped_finding_writes_exactly_one_card(tmp_path):
    for _ in range(2):
        inbox.write_finding(
            tmp_path,
            "alert",
            "Critical drift",
            "system is stopped",
            "linter",
            loudness="alert",
            dedupe_slug="dedupe-probe",
        )

    cards = list((tmp_path / "inbox").glob("*.md"))
    assert len(cards) == 1
    assert _card_loudness(cards[0]) == "alert"


def test_a_deduped_work_prompt_writes_exactly_one_card_at_its_band(tmp_path):
    for _ in range(2):
        inbox.write_work_prompt(
            tmp_path,
            "Review the affected work",
            "Review the affected work and decide what to do next.",
            "A review gate needs PI attention.",
            "test",
            request_id="REQ-DEDUPE",
            loudness="alert",
            dedupe_slug="work-prompt-probe",
        )

    cards = list((tmp_path / "inbox").glob("*.md"))
    assert len(cards) == 1
    assert _card_loudness(cards[0]) == "alert"


def test_a_proposal_lands_at_notice(tmp_path):
    inbox.write_proposal(
        tmp_path,
        "candidate",
        "Maybe",
        "read it",
        "useful",
        "weak",
        "gap",
        "likely",
        "librarian",
        loudness="notice",
    )

    [card] = list((tmp_path / "inbox").glob("*.md"))
    assert _card_loudness(card) == "notice"
```

The old assertions checked for an artifact that cannot exist; these read the band off the card the real
producer wrote and pin dedupe as one-file-on-disk, which is its observable. (`_card_loudness` already exists
at the bottom of the file.) Note: the module-level docstring on the file still says "Graded-loudness routing
helpers" — accurate, leave it.

Body-deletion proof, before and after: with the *old* tests, deleting the `inbox.write_*` call left them
green (measured in the audit). With the new tests, deleting the producer call must fail on the glob
unpacking. Verify once for `test_alert_finding_lands_on_the_card_at_alert`: comment out the `write_finding`
call, run, expect `ValueError: not enough values to unpack`, restore.

- [ ] **Step 2: Collapse the cockpit conditionals**

In `tests/test_cockpit.py`:

Near line 554, replace:

```python
    if hasattr(cockpit, "trace_panel"):
        assert {"events", "total", "shown"} <= set(trace)
    else:
        assert trace["pending"] == "engine.cockpit.trace_panel (U2 plan section T)"
        assert "events" not in trace
```

with:

```python
    # trace_panel landed (U2 section T); the pending arm below it was dead and a
    # both-branch assert distinguishes nothing.
    assert {"events", "total", "shown"} <= set(trace)
    assert "pending" not in trace
```

Near line 655 (and the sibling near line 1330 — find both with
`grep -n '_review_seam_is_live' tests/test_cockpit.py`), replace each:

```python
    if _review_seam_is_live():
        assert "pending" not in panels["review"]
        assert panels["review"]["source_action"] == "views.evidence_review"
    else:
        assert panels["review"]["source_action"] == ""
```

with:

```python
    assert "pending" not in panels["review"]
    assert panels["review"]["source_action"] == "views.evidence_review"
```

Then delete the `_review_seam_is_live` helper **if and only if** `grep -c '_review_seam_is_live'
tests/test_cockpit.py` shows no remaining callers, and remove the now-dead comment above the trace block
("Both branches are legal here" is no longer true — both branches were the defect).

- [ ] **Step 3: Run, full gate, commit**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_loudness.py tests/test_cockpit.py -q -p no:randomly`
Expected: all pass.

```bash
git add tests/test_loudness.py tests/test_cockpit.py
git commit -m "tests: assert what producers write, not the absence of a deleted feature"
```

---

### Task 7: The tension dedupe is pinned at the layer that actually does it

`test_surface_tensions_dedupes_same_canonical_id` asserts `candidate_count == 0` — but the audit proved the
zero is produced one layer down: with a duplicated frontmatter `id:`, `_checked_tension_rows` yields **one**
row (the identity layer rejects the duplicate), so the pair loop never runs and the guard the test names
(`pair_key[0] == pair_key[1]` at `integrity.py:717`) is unreachable — deleting it survives the whole suite.
An unkillable branch is deleted or justified; this one is deleted, and the row-layer behavior gets the
differential test it never had.

**Files:**
- Modify: `src/memoria_vault/runtime/integrity.py` (the pair-loop guard in `tier1_tension_candidates`)
- Modify: `tests/test_integrity_surface_tensions.py` (rewrite the dedupe test)

**Interfaces:**
- Consumes: `integrity._checked_tension_rows(vault)` (already imported/reachable in the test module's
  namespace — follow the file's existing import style), `surface_tensions(vault)`, the file's raw-file
  fixture idiom from the current dedupe test (kept deliberately: the real producer *cannot* mint two files
  with one id, which is exactly the invariant under test).

- [ ] **Step 1: Rewrite the test as a differential pair**

Replace `test_surface_tensions_dedupes_same_canonical_id` with:

```python
def test_a_duplicate_canonical_id_collapses_at_the_row_layer(tmp_path: Path) -> None:
    """Two files sharing one frontmatter id yield ONE consumable row -- the
    identity layer rejects the duplicate before the pair loop ever runs. The
    old form of this test asserted candidate_count == 0 and credited it to a
    pair-loop guard that is unreachable (deleting it survived the suite); the
    zero was real but produced here, one layer down. The distinct-id control
    proves the fixture itself is candidate-capable, so the collapse is doing
    the work rather than an overlap threshold or a broken fixture.
    """
    shared_id = "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def _vault(base: Path, ids: tuple[str, str]) -> Path:
        vault = workspace(base)
        for (rel, body), note_id in zip(
            {
                "notes/recall-up.md": "The intervention improved recall.",
                "notes/recall-not-up.md": "The intervention did not improve recall.",
            }.items(),
            ids,
        ):
            path = vault / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "---\n"
                "type: note\n"
                f"id: {note_id}\n"
                f"title: {Path(rel).stem}\n"
                "tags: []\n"
                "links: {}\n"
                "---\n"
                f"# {Path(rel).stem}\n\n{body}\n",
                encoding="utf-8",
            )
            state.record_observed_file_edit(
                vault, output_id=rel, concept_type="note", output_sha256=sha256_file(path)
            )
            state.set_concept_verdict(vault, rel, "checked")
        return vault

    duplicated = _vault(tmp_path / "dup", (shared_id, shared_id))
    assert len(_checked_tension_rows(duplicated)) == 1  # the layer that dedupes
    assert surface_tensions(duplicated)["candidate_count"] == 0

    distinct = _vault(tmp_path / "distinct", (shared_id, "01BX5ZZKBKACTAV9WEVGEMMVS0"))
    assert len(_checked_tension_rows(distinct)) == 2  # the control: fixture is pair-capable
    assert surface_tensions(distinct)["candidate_count"] == 1
```

Add `_checked_tension_rows` to the test module's imports from `memoria_vault.runtime.integrity`, matching the
file's existing import block style. If `workspace(...)` cannot take a subdirectory of `tmp_path`, give each
vault its own `tmp_path_factory.mktemp(...)` instead — the differential structure is the requirement, not the
directory layout.

- [ ] **Step 2: Run it — it must pass BEFORE the deletion too**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_integrity_surface_tensions.py -q -p no:randomly`
Expected: all pass. (The new test pins the row layer, which exists regardless of the dead guard — if the
distinct-id control reports 0 candidates, the texts fell under the 0.55 overlap threshold; the two bodies
above share enough tokens that they clear it in the existing suite's sibling tests, so investigate rather
than loosening the assertion.)

- [ ] **Step 3: Delete the unreachable guard**

In `src/memoria_vault/runtime/integrity.py`, change:

```python
                pair_key = tuple(sorted((left["canonical_id"], right["canonical_id"])))
                if pair_key in seen or pair_key[0] == pair_key[1]:
                    continue
```

to:

```python
                pair_key = tuple(sorted((left["canonical_id"], right["canonical_id"])))
                # No same-id arm: two rows cannot share a canonical id, because
                # _checked_tension_rows consumes only files the identity layer
                # accepted and a duplicated frontmatter id is rejected there
                # (pinned by test_a_duplicate_canonical_id_collapses_at_the_row_layer).
                # The arm survived every test in the suite as a mutation target.
                if pair_key in seen:
                    continue
```

- [ ] **Step 4: Run the file and the neighbors, full gate, commit**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_integrity_surface_tensions.py tests/test_worker_integrity_jobs.py -q -p no:randomly`
Expected: all pass.

```bash
git add src/memoria_vault/runtime/integrity.py tests/test_integrity_surface_tensions.py
git commit -m "integrity: pin tension dedupe at the row layer, drop the unreachable pair guard"
```

---

### Task 8: Delete the inert skill-deny feature

`PolicyEngine.set_session_skill` / `clear_session_skill` have zero callers anywhere; the per-check
`PolicyEngine(workspace)` construction in `policy/hook.py` means registered state could never survive to a
gate decision anyway; and the unit tests exercise `decide(..., skill_deny_write=...)` directly, which is what
makes the feature read as working. Under this repo's rule (deletion > mechanism) the feature comes out whole.
If skill-scoped deny is ever wanted, it returns via a spec'd task that wires the hook — this commit is the
record of what to restore.

**Files:**
- Modify: `src/memoria_vault/runtime/policy/decision.py` (drop `skill_deny_write` param + its block, delete
  `compose_skill_deny`)
- Modify: `src/memoria_vault/runtime/policy/engine.py` (drop `_session_skill_deny`, both methods, the
  `skill_deny =` line and the `skill_deny_write=` argument; drop `compose_skill_deny` from the import)
- Modify: `src/memoria_vault/runtime/policy/__init__.py` (drop the re-export, lines 15 and 52)
- Modify: `tests/test_runtime_policy.py` (drop the import, the `sk` lambda parameter, and the
  "skill-conditional one-way narrowing" block at ~lines 256–265)

**Interfaces:**
- Produces: `decide(actor, action, npath, policy, *, flags=None)` — one parameter narrower. Nothing else in
  the repo passes `skill_deny_write` (verified: the only call site is `engine.py:142`).

- [ ] **Step 1: Delete, in this order**

1. `tests/test_runtime_policy.py`: remove `compose_skill_deny` from the import at line ~15; change the lambda
   at ~192 to `d = lambda p, a, pa, fl=None: decide(p.actor, a, pa, p, flags=fl).decision`; delete the
   `# ---- skill-conditional one-way narrowing ----` block (the `co_deny` lines).
2. `src/memoria_vault/runtime/policy/engine.py`: delete lines 26 (`_session_skill_deny`), 33–42 (both
   methods), 141 (`skill_deny = ...`); change 142 to
   `dec = decide(actor, action, npath, policy, flags=flags)`; remove `compose_skill_deny` from the line-14
   import.
3. `src/memoria_vault/runtime/policy/decision.py`: delete the `skill_deny_write` parameter, the
   `if skill_deny_write and ...` block (lines ~44–49), and `compose_skill_deny` (lines ~151–156).
4. `src/memoria_vault/runtime/policy/__init__.py`: delete the `compose_skill_deny` import line and its
   `__all__` entry.

- [ ] **Step 2: Prove zero references remain**

Run: `grep -rn 'skill_deny\|session_skill\|compose_skill' src/ tests/ scripts/ docs/reference --include='*.py' --include='*.md' | grep -v __pycache__`
Expected: no output. If anything appears that this task did not list, **stop and report it** — an unlisted
caller means the audit's zero-caller claim was wrong and deletion is off the table until re-verified.

- [ ] **Step 3: Run the policy suite, full gate, commit**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_runtime_policy.py -q`
Expected: all pass (minus the deleted block's assertions).

```bash
git add src/memoria_vault/runtime/policy tests/test_runtime_policy.py
git commit -m "policy: delete the never-wired skill deny feature (deletion over mechanism)"
```

---

### Task 9: `sync_file_verdicts` derives its roots instead of misspelling them

`tests/helpers.py::sync_file_verdicts` walks `("catalog", "knowledge", "notes", "hubs", "projects",
"digests", "fulltext")`. The product's roots are `CONCEPT_ROOTS = ("catalog/sources/", "notes/", "hubs/",
"digests/", "fulltexts/")` — so `"fulltext"` (singular) and `"knowledge"` match nothing, and
`if not base.exists(): continue` swallows both silently. No current consumer seeds those roots, so no test is
wrong today; the first one that seeds `fulltexts/` gets a helper that silently does nothing. Same shape as
the `_state_source()` finding, pre-loaded into a shared fixture builder.

**Files:**
- Modify: `tests/helpers.py` (the roster inside `sync_file_verdicts`)
- Create: `tests/test_fixture_helpers.py`

**Interfaces:**
- Consumes: `subsystems.lib.edges.CONCEPT_ROOTS`; `state.concept_check_status(vault, concept_id) -> str`.
- Produces: unchanged signature `sync_file_verdicts(vault)`, now covering every concept root plus
  `projects/`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_fixture_helpers.py`:

```python
"""The shared fixture builders must reach what they claim to reach."""

from __future__ import annotations

from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.subsystems.lib.edges import CONCEPT_ROOTS
from tests import helpers

pytestmark = pytest.mark.runtime


def test_sync_file_verdicts_reaches_every_concept_root(tmp_path: Path) -> None:
    """fulltexts/ is a real concept root; the old hand-typed roster spelled it
    'fulltext' and the exists-continue swallowed the miss silently."""
    rels = [root.rstrip("/") + "/probe.md" for root in CONCEPT_ROOTS]
    for rel in rels:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\ntype: note\ntitle: probe\ncheck_status: checked\n---\nbody\n",
            encoding="utf-8",
        )

    helpers.sync_file_verdicts(tmp_path)

    for rel in rels:
        assert state.concept_check_status(tmp_path, rel) == "checked", rel
```

- [ ] **Step 2: Run it to verify it fails on `fulltexts/`**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_fixture_helpers.py -q`
Expected: FAIL, with the failing `rel` being `fulltexts/probe.md` (and only that one). If it fails on a
*different* root, the helper's per-file requirements differ from this fixture's frontmatter — read the loop
body in `helpers.py` and adjust the frontmatter (e.g. a required `type:` value), not the claim.

- [ ] **Step 3: Derive the roster**

In `tests/helpers.py`, inside `sync_file_verdicts`, replace the hand-typed tuple with:

```python
    # Derived, not retyped: the hand-typed roster spelled fulltexts/ as
    # "fulltext" and listed a "knowledge" root that has never existed; the
    # exists-continue below made both misses silent.
    roots = tuple(dict.fromkeys(root.split("/", 1)[0] for root in CONCEPT_ROOTS)) + ("projects",)
    for root in roots:
```

with `from memoria_vault.runtime.subsystems.lib.edges import CONCEPT_ROOTS` added to the file's existing
first-party import block. (`helpers.py` already imports the runtime stack, so this adds no new weight — and
the runtime-free guards import `tests.paths`, not this module.)

- [ ] **Step 4: Run to green, full gate, commit**

Run: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_fixture_helpers.py tests/test_attention_lifecycle.py -q -p no:randomly`
Expected: PASS (the second file is `sync_file_verdicts`' heaviest consumer — it must be unaffected).

```bash
git add tests/helpers.py tests/test_fixture_helpers.py
git commit -m "tests: sync_file_verdicts derives its roots from CONCEPT_ROOTS"
```

---

## Explicit non-goals

- **A Windows CI runner** (the `install.ps1` and Windows-lock execution gap) — an infrastructure decision,
  not a task; the gap is recorded in the coverage analysis.
- **Mutation testing in CI** — the terminology-gate finding shows the need, but a standing mutation gate is
  its own design (budget, target selection, flake policy), not a task here.
- **Read-payload goldens for the floor sweep** — deliberate scope cut; the floor's role is completeness and
  state-drift, and payload content is owned by the per-surface suites.
- **`_confirm_tension_edge`'s four refusals** — suspected-only in the audit, not confirmed; verify before
  writing tests, and only under a task that owns it.

## Self-review record

- **Coverage of findings:** sandbox (T1), verify_code_run (T2), calibration + probe payload (T3), terminology
  gate (T4), wheel/removed-surface/schema-drift arms (T5), loudness + cockpit vacuity (T6), tension dedupe +
  unreachable guard (T7), inert skill-deny (T8), fixture-helper roster (T9). Deferred items are named
  non-goals rather than dropped silently.
- **Every code step carries the actual code**; the two places an implementer may legitimately diverge (row
  key spellings in T1, import spelling in T5 step 3) say what governs instead of leaving a blank.
- **Type consistency:** T1/T2 share `create_code_artifact` and `state.record_code_run` call shapes with the
  existing suite verbatim; T3's `_BARS` keys match `REQUIRED_BARS`; T4's `errors(base)` signature is used by
  every test in its file; T8's narrowed `decide` signature is applied to the one call site and the one lambda
  that exist.
- **Known risk:** T7's control pair depends on the 0.55 lexical-overlap threshold; the step says to
  investigate rather than loosen if it undershoots. T1 step 5's kill-check may be deferrable-only on this
  machine; the report contract makes that loud.
