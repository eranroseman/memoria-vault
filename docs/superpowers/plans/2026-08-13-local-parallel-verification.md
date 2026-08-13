# Local Parallel Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (- [ ]) syntax for tracking.

**Goal:** Add an opt-in python scripts/verify --parallel mode that runs lint
before CPU-bounded test shards while preserving the current sequential verifier,
full failure visibility, and vault safety.

**Architecture:** The new mode is a coordinator, not a shard. It executes the
lint shard synchronously before launching contract, runtime, and sweep in
CPU-bounded batches as ordinary --shard child processes. The runtime child
remains the sole owner of the existing vault lock.

**Tech Stack:** Python 3.12, subprocess, tempfile, pytest.

## Global Constraints

- Execute only after #1832 is triaged enhancement + ready-for-agent, is
  unassigned/unblocked, and the executor claims it before modifying code.
- Bare python scripts/verify and every existing --shard invocation retain their
  exact sequential behavior and current gate roster.
- --parallel is mutually exclusive with --shard. VERIFY_DOCS_ONLY remains
  CI-only; do not add a local --docs-only option.
- The coordinator never calls _hold_single_run_lock. Its runtime child runs
  scripts/verify --shard runtime and therefore owns the lock around e2e smoke.
- Lint completes before any child starts. If lint fails, launch no children.
- Children never exceed available CPU capacity: on 1 core they run one at a
  time; on 2 cores, two then one; on 3+ cores all three run concurrently.
- Each child receives a numeric PYTEST_XDIST_AUTO_NUM_WORKERS override.
  Total active xdist workers must not exceed the detected CPU budget.
- Wait for and replay every launched child's labeled log even if one fails.
  Do not fail fast. On interrupt or spawn failure, terminate and reap active
  children so no xdist process is orphaned.
- Use the current interpreter and absolute verifier path for child commands.
  Do not invoke a bare python executable.
- Stage exact paths only; never use an unbounded git add form.

---

### Task 1: Define the CLI and CPU-budget seams

**Files:**
- Modify: scripts/verify
- Modify: tests/test_verify_script.py

**Interfaces:**
- Produces PARALLEL_SHARDS = ("contract", "runtime", "sweep").
- Produces _parse_args(argv: list[str]) -> tuple[str | None, bool].
- Produces _parallel_limits(cpu_count: int | None = None) -> tuple[int, int],
  returning (concurrency, workers_per_child).

- [ ] **Step 1: Write failing parser and budget tests**

Add to tests/test_verify_script.py:

~~~
def test_parallel_cli_is_opt_in_and_conflicts_with_a_shard() -> None:
    parse = _verify_namespace()["_parse_args"]
    assert parse([]) == (None, False)
    assert parse(["--shard", "runtime"]) == ("runtime", False)
    assert parse(["--parallel"]) == (None, True)
    with pytest.raises(SystemExit, match="--parallel cannot be combined with --shard"):
        parse(["--parallel", "--shard", "runtime"])

@pytest.mark.parametrize(
    ("cpus", "expected"),
    [(1, (1, 1)), (2, (2, 1)), (3, (3, 1)), (5, (3, 1)), (6, (3, 2)), (8, (3, 2))],
)
def test_parallel_limits_never_oversubscribe(cpus: int, expected: tuple[int, int]) -> None:
    namespace = _verify_namespace()
    concurrency, workers = namespace["_parallel_limits"](cpus)
    assert (concurrency, workers) == expected
    assert concurrency * workers <= cpus
~~~

Also assert PARALLEL_SHARDS exactly excludes lint and has the declared order.

- [ ] **Step 2: Prove the tests are red**

Run:

~~~
python3 -m pytest tests/test_verify_script.py -q
~~~

Expected: FAIL because the parser, shard tuple, and CPU-budget helper do not
exist.

- [ ] **Step 3: Implement parsing and limits**

Replace the narrow parser with:

~~~
PARALLEL_SHARDS = ("contract", "runtime", "sweep")

def _parse_args(argv: list[str]) -> tuple[str | None, bool]:
    if argv == []:
        return None, False
    if argv == ["--parallel"]:
        return None, True
    if "--parallel" in argv and "--shard" in argv:
        raise SystemExit("verify: --parallel cannot be combined with --shard")
    if "--parallel" in argv:
        raise SystemExit("verify: --parallel accepts no other arguments")
    if len(argv) != 2 or argv[0] != "--shard":
        raise SystemExit("verify: expected --parallel or --shard NAME")
    shard = argv[1]
    if shard not in SHARDS:
        raise SystemExit(f"verify: unknown shard {shard!r}; expected one of {', '.join(SHARDS)}")
    return shard, False

def _parallel_limits(cpu_count: int | None = None) -> tuple[int, int]:
    budget = max(1, cpu_count or 1)
    concurrency = min(len(PARALLEL_SHARDS), budget)
    return concurrency, max(1, budget // concurrency)
~~~

Add assertions for ["--parallel", "--parallel"], ["--shard"],
["--shard", "runtime", "extra"], and ["runtime"]. Each must raise
SystemExit; preserve the present unknown-shard diagnostic for an unknown name.

- [ ] **Step 4: Prove parser and budget contracts are green**

Run:

~~~
python3 -m pytest tests/test_verify_script.py -q
~~~

Expected: PASS. On every tested CPU count, active workers are within budget.

- [ ] **Step 5: Commit Task 1**

~~~
git add scripts/verify tests/test_verify_script.py
git commit -m "verify: define an opt-in parallel verification interface"
~~~

---

### Task 2: Run bounded shard batches and replay all failures

**Files:**
- Modify: scripts/verify
- Modify: tests/test_verify_script.py

**Interfaces:**
- Produces _shard_command(shard: str) -> list[str].
- Produces _run_parallel() -> int.
- Each child command is [sys.executable, ROOT / "scripts" / "verify",
  "--shard", shard].
- The coordinator launches slices of PARALLEL_SHARDS no larger than
  _parallel_limits()[0].

- [ ] **Step 1: Write failing coordinator tests**

Introduce this injectable child-launch seam. Add `import tempfile` and
`from typing import TextIO` to scripts/verify:

~~~
def _spawn_shard(
    shard: str, workers: int, log_path: Path
) -> tuple[subprocess.Popen[str], TextIO]:
    stream = log_path.open("w", encoding="utf-8")
    environment = os.environ | {"PYTEST_XDIST_AUTO_NUM_WORKERS": str(workers)}
    try:
        process = subprocess.Popen(
            _shard_command(shard),
            cwd=ROOT,
            env=environment,
            stdout=stream,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except BaseException:
        stream.close()
        raise
    return process, stream
~~~

Add this fake child type and use it to test batching through the injected
_spawn_shard global:

~~~
class _FakeProcess:
    def __init__(self, code: int, events: list[str], shard: str) -> None:
        self.code, self.events, self.shard, self.returncode = code, events, shard, None

    def wait(self) -> int:
        self.events.append(f"wait:{self.shard}")
        self.returncode = self.code
        return self.code

    def poll(self) -> int | None:
        return self.returncode

    def terminate(self) -> None:
        self.events.append(f"terminate:{self.shard}")

def test_parallel_stops_before_children_when_lint_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    namespace = _verify_namespace()
    globals_ = namespace["_run_parallel"].__globals__
    monkeypatch.setitem(globals_, "run", lambda command: 1)
    monkeypatch.setitem(globals_, "_spawn_shard", lambda *args: pytest.fail("child launched"))
    assert namespace["_run_parallel"]() == 1

def test_parallel_waits_replays_and_reports_every_child_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    namespace = _verify_namespace()
    globals_, events = namespace["_run_parallel"].__globals__, []
    codes = {"contract": 0, "runtime": 1, "sweep": 0}
    def spawn(shard: str, workers: int, path: Path):
        events.append(f"spawn:{shard}:{workers}")
        path.write_text(f"{shard} log\n", encoding="utf-8")
        return _FakeProcess(codes[shard], events, shard), path.open("a", encoding="utf-8")
    monkeypatch.setitem(globals_, "run", lambda command: 0)
    monkeypatch.setitem(globals_, "_parallel_limits", lambda: (3, 1))
    monkeypatch.setitem(globals_, "_spawn_shard", spawn)
    assert namespace["_run_parallel"]() == 1
    assert events == ["spawn:contract:1", "spawn:runtime:1", "spawn:sweep:1", "wait:contract", "wait:runtime", "wait:sweep"]
    assert capsys.readouterr().out.count("== verify: parallel") == 3

def test_parallel_batches_at_two_cpus_and_overrides_child_workers(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    namespace = _verify_namespace()
    globals_, events = namespace["_run_parallel"].__globals__, []
    def spawn(shard: str, workers: int, path: Path):
        events.append(f"spawn:{shard}:{workers}")
        path.write_text("ok\n", encoding="utf-8")
        return _FakeProcess(0, events, shard), path.open("a", encoding="utf-8")
    monkeypatch.setitem(globals_, "run", lambda command: 0)
    monkeypatch.setitem(globals_, "_parallel_limits", lambda: (2, 1))
    monkeypatch.setitem(globals_, "_spawn_shard", spawn)
    assert namespace["_run_parallel"]() == 0
    assert events == ["spawn:contract:1", "spawn:runtime:1", "wait:contract", "wait:runtime", "spawn:sweep:1", "wait:sweep"]

def test_parallel_reports_a_missing_child_and_runs_the_remaining_shards(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    namespace = _verify_namespace()
    globals_, events = namespace["_run_parallel"].__globals__, []
    def spawn(shard: str, workers: int, path: Path):
        if shard == "contract":
            raise FileNotFoundError("missing")
        events.append(f"spawn:{shard}:{workers}")
        path.write_text("ok\n", encoding="utf-8")
        return _FakeProcess(0, events, shard), path.open("a", encoding="utf-8")
    monkeypatch.setitem(globals_, "run", lambda command: 0)
    monkeypatch.setitem(globals_, "_parallel_limits", lambda: (3, 1))
    monkeypatch.setitem(globals_, "_spawn_shard", spawn)
    assert namespace["_run_parallel"]() == 1
    assert events == ["spawn:runtime:1", "spawn:sweep:1", "wait:runtime", "wait:sweep"]
    assert "command not found" in capsys.readouterr().out
~~~

Add a command assertion:

~~~
command = namespace["_shard_command"]("runtime")
assert command[-2:] == ["--shard", "runtime"]
assert command[0] == sys.executable
assert Path(command[1]) == ROOT / "scripts" / "verify"
~~~

- [ ] **Step 2: Prove coordinator tests are red**

Run:

~~~
python3 -m pytest tests/test_verify_script.py -q
~~~

Expected: FAIL because no child launcher, batching, or log replay exists.

- [ ] **Step 3: Implement coordinator behavior**

Implement _shard_command with sys.executable and ROOT / "scripts" / "verify".
Implement _spawn_shard by copying os.environ and overriding only:

~~~
"PYTEST_XDIST_AUTO_NUM_WORKERS": str(workers)
~~~

Use cwd=ROOT, text=True, stdout directed to an opened temporary log, and
stderr=subprocess.STDOUT. In _run_parallel():

1. Call run(_shard_command("lint")). Return 1 immediately if it fails.
2. Create TemporaryDirectory(prefix="memoria-verify-").
3. Get concurrency and workers from _parallel_limits().
4. Slice PARALLEL_SHARDS in concurrency-sized batches.
5. Spawn every child in the active batch before waiting for any of it.
6. Wait every child in declared order. After every wait, close its stream and
   print this stable heading with the current shard name:

~~~
== verify: parallel runtime
~~~

   then replay the entire log text.
7. Carry a failed flag across all batches. A failed child does not suppress
   later batches.
8. In a finally block, terminate then wait/reap every active child that has not
   exited before re-raising KeyboardInterrupt or a launch exception.

Treat a FileNotFoundError from one launch as a synthetic exit code 127 with the
log line "command not found: <command[0]>". Continue launching, waiting for,
and replaying eligible siblings. Return 1 iff any child failed.

- [ ] **Step 4: Prove all coordinator behavior is green**

Run:

~~~
python3 -m pytest tests/test_verify_script.py -q
~~~

Expected: PASS. Tests show no fail-fast behavior, correct batches, and an
explicit worker override for each child.

- [ ] **Step 5: Commit Task 2**

~~~
git add scripts/verify tests/test_verify_script.py
git commit -m "verify: run non-mutating shards in bounded parallel batches"
~~~

---

### Task 3: Integrate mode selection without taking the coordinator lock

**Files:**
- Modify: scripts/verify
- Modify: tests/test_verify_script.py

**Interfaces:**
- main(argv) selects _run_parallel before normal lock selection when parallel is
  true.
- Existing sequential main path remains unchanged for bare and --shard calls.

- [ ] **Step 1: Write the failing lock-ownership tests**

Add:

~~~
def test_parallel_coordinator_never_takes_the_vault_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    namespace = _verify_namespace()
    globals_ = namespace["main"].__globals__
    monkeypatch.setitem(globals_, "_hold_single_run_lock", lambda: pytest.fail("coordinator locked"))
    monkeypatch.setitem(globals_, "_run_parallel", lambda: 0)
    assert namespace["main"](["--parallel"]) == 0
~~~

Keep the existing test that runtime is the only vault-mutating shard. Add one
test that bare main([]) and main(["--shard", "runtime"]) still call the normal
selection path rather than _run_parallel.

- [ ] **Step 2: Prove lock tests are red**

Run:

~~~
python3 -m pytest tests/test_verify_script.py -q
~~~

Expected: FAIL because main has no parallel branch.

- [ ] **Step 3: Route parallel mode before lock selection**

At the start of main():

~~~
arguments = sys.argv[1:] if argv is None else argv
shard, parallel = _parse_args(arguments)
if parallel:
    return _run_parallel()
lock = _hold_single_run_lock() if _needs_vault_lock(shard) else None
~~~

Retain the existing run timing, shard banner, docs-only banner, gate loop,
extra-step loop, and final verify: OK behavior for the nonparallel path. Make
_run_parallel print its own total and verify: OK or verify: FAILED so the new
mode has the same terminal convention.

- [ ] **Step 4: Prove selection behavior is green**

Run:

~~~
python3 -m pytest tests/test_verify_script.py -q
python scripts/verify --parallel
~~~

Expected: focused tests PASS; the parallel run ends verify: OK in a clean,
idle worktree. If it reveals an existing environmental test failure, diagnose it
before changing the coordinator.

- [ ] **Step 5: Run full verification and benchmark**

Run sequentially, on the same clean idle worktree:

~~~
/usr/bin/time -f "sequential %e s" python scripts/verify
/usr/bin/time -f "parallel %e s" python scripts/verify --parallel
git diff --check
~~~

Expected: both end verify: OK, no whitespace errors, and parallel is no slower
than sequential. Record hardware, worker budget, each time, and any cache state
in the task report; do not make --parallel the default from a single benchmark.

- [ ] **Step 6: Commit Task 3**

~~~
git add scripts/verify tests/test_verify_script.py
git commit -m "verify: add an opt-in bounded parallel mode"
~~~
