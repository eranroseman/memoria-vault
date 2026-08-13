"""Pins the flat verify roster — the one legitimate roster mirror, kept as a test."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

import pytest
import yaml

from tests.paths import ROOT

pytestmark = pytest.mark.static

VERIFY_WORKFLOW = ROOT / ".github/workflows/verify.yml"


def _verify_namespace() -> dict:
    # run_name != "__main__" so the module defines the roster without executing main().
    return runpy.run_path(str(ROOT / "scripts/verify"), run_name="_verify_probe")


def _verify_namespace_with_env(**updates: str | None) -> dict:
    previous = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        return _verify_namespace()
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


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


def test_parallel_cli_is_opt_in_and_conflicts_with_a_shard() -> None:
    parse = _verify_namespace()["_parse_args"]

    assert parse([]) == (None, False)
    assert parse(["--shard", "runtime"]) == ("runtime", False)
    assert parse(["--parallel"]) == (None, True)
    with pytest.raises(SystemExit, match="--parallel cannot be combined with --shard"):
        parse(["--parallel", "--shard", "runtime"])


@pytest.mark.parametrize(
    "argv",
    [["--parallel", "--parallel"], ["--shard"], ["--shard", "runtime", "extra"], ["runtime"]],
)
def test_parallel_cli_rejects_malformed_arguments(argv: list[str]) -> None:
    with pytest.raises(SystemExit):
        _verify_namespace()["_parse_args"](argv)


def test_parallel_cli_preserves_the_unknown_shard_diagnostic() -> None:
    with pytest.raises(
        SystemExit, match="unknown shard 'unknown'; expected one of lint, contract, runtime, sweep"
    ):
        _verify_namespace()["_parse_args"](["--shard", "unknown"])


@pytest.mark.parametrize(
    ("cpus", "expected"),
    [(1, (1, 1)), (2, (2, 1)), (3, (3, 1)), (5, (3, 1)), (6, (3, 2)), (8, (3, 2))],
)
def test_parallel_limits_never_oversubscribe(cpus: int, expected: tuple[int, int]) -> None:
    namespace = _verify_namespace()
    concurrency, workers = namespace["_parallel_limits"](cpus)

    assert namespace["PARALLEL_SHARDS"] == ("contract", "runtime", "sweep")
    assert (concurrency, workers) == expected
    assert concurrency * workers <= cpus


def test_parallel_shard_command_reinvokes_verify_with_current_python() -> None:
    namespace = _verify_namespace()

    command = namespace["_shard_command"]("runtime")

    assert command[-2:] == ["--shard", "runtime"]
    assert command[0] == sys.executable
    assert Path(command[1]) == ROOT / "scripts" / "verify"


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
    assert events == [
        "spawn:contract:1",
        "spawn:runtime:1",
        "spawn:sweep:1",
        "wait:contract",
        "wait:runtime",
        "wait:sweep",
    ]
    assert capsys.readouterr().out.count("== verify: parallel") == 3


def test_parallel_batches_at_two_cpus_and_overrides_child_workers(
    monkeypatch: pytest.MonkeyPatch,
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
    assert events == [
        "spawn:contract:1",
        "spawn:runtime:1",
        "wait:contract",
        "wait:runtime",
        "spawn:sweep:1",
        "wait:sweep",
    ]


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


def test_parallel_terminates_and_reaps_a_child_when_a_sibling_launch_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    namespace = _verify_namespace()
    globals_, events = namespace["_run_parallel"].__globals__, []

    def spawn(shard: str, workers: int, path: Path):
        if shard == "runtime":
            raise RuntimeError("launch failed")
        events.append(f"spawn:{shard}:{workers}")
        path.write_text("ok\n", encoding="utf-8")
        return _FakeProcess(0, events, shard), path.open("a", encoding="utf-8")

    monkeypatch.setitem(globals_, "run", lambda command: 0)
    monkeypatch.setitem(globals_, "_parallel_limits", lambda: (3, 1))
    monkeypatch.setitem(globals_, "_spawn_shard", spawn)

    with pytest.raises(RuntimeError, match="launch failed"):
        namespace["_run_parallel"]()

    assert events == ["spawn:contract:1", "terminate:contract", "wait:contract"]


def test_parallel_terminates_and_reaps_active_children_when_interrupted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    namespace = _verify_namespace()
    globals_, events = namespace["_run_parallel"].__globals__, []

    class InterruptingProcess(_FakeProcess):
        def wait(self) -> int:
            self.events.append(f"wait:{self.shard}")
            if self.events.count(f"wait:{self.shard}") == 1:
                raise KeyboardInterrupt
            self.returncode = self.code
            return self.code

    def spawn(shard: str, workers: int, path: Path):
        events.append(f"spawn:{shard}:{workers}")
        path.write_text("ok\n", encoding="utf-8")
        process = InterruptingProcess if shard == "contract" else _FakeProcess
        return process(0, events, shard), path.open("a", encoding="utf-8")

    monkeypatch.setitem(globals_, "run", lambda command: 0)
    monkeypatch.setitem(globals_, "_parallel_limits", lambda: (3, 1))
    monkeypatch.setitem(globals_, "_spawn_shard", spawn)

    with pytest.raises(KeyboardInterrupt):
        namespace["_run_parallel"]()

    assert events == [
        "spawn:contract:1",
        "spawn:runtime:1",
        "spawn:sweep:1",
        "wait:contract",
        "terminate:contract",
        "terminate:runtime",
        "terminate:sweep",
        "wait:contract",
        "wait:runtime",
        "wait:sweep",
    ]


def test_slow_test_telemetry_is_a_ci_only_opt_in() -> None:
    duration_flags = ["--durations=25", "--durations-min=0.25"]
    local = _verify_namespace_with_env(MEMORIA_PYTEST_DURATIONS=None)
    telemetry = _verify_namespace_with_env(MEMORIA_PYTEST_DURATIONS="1")

    local_pytest_commands = [gate.cmd for gate in local["GATES"] if "pytest" in gate.cmd]
    telemetry_pytest_commands = [gate.cmd for gate in telemetry["GATES"] if "pytest" in gate.cmd]
    assert all(flag not in command for command in local_pytest_commands for flag in duration_flags)
    assert all(
        command[
            command.index("-m", command.index("pytest") + 1) - len(duration_flags) : command.index(
                "-m", command.index("pytest") + 1
            )
        ]
        == duration_flags
        for command in telemetry_pytest_commands
    )

    workflow = yaml.safe_load(VERIFY_WORKFLOW.read_text(encoding="utf-8"))
    run_verify = next(
        step for step in workflow["jobs"]["shards"]["steps"] if step.get("name") == "Run verify"
    )
    assert run_verify["env"]["MEMORIA_PYTEST_DURATIONS"] == "1"


def test_roster_covers_lint_tests_and_product_gates() -> None:
    flat = [" ".join(gate.cmd) for gate in _verify_namespace()["GATES"]]

    assert flat[0] == "pre-commit run --hook-stage manual --all-files"
    for gate in (
        "python3 scripts/checks/schema_doc_drift.py",
        "python3 scripts/checks/removed_surface_gate.py",
        "python3 scripts/checks/checked_terminology_gate.py",
        "python3 scripts/checks/plugin_provenance_doctor.py",
        "python3 scripts/checks/doc_claims_gate.py",
        "python3 scripts/checks/doc_link_targets.py",
        "python3 scripts/checks/doc_cited_paths.py",
        "python3 scripts/checks/control_plane_actor_gate.py",
        "python3 scripts/checks/wheel_gate.py",
        "python3 scripts/test_vault/e2e_smoke.py",
        "memoria --version",
    ):
        assert gate in flat
    # The test gate is three entries, one per test shard. Their marker expressions
    # must together cover every registered level except `live`, or a whole level
    # stops running while the roster still looks complete.
    namespace = _verify_namespace()
    markers = {gate.markers for gate in namespace["GATES"] if gate.markers is not None}
    assert markers == {"contract", "runtime", "static or unit or package or floor"}
    covered = {level for expression in markers for level in expression.split(" or ")}
    assert covered == {"static", "unit", "contract", "runtime", "package", "floor"}
    assert any(f.startswith("python3 -m compileall") for f in flat)


def test_retired_doctors_are_absent_from_the_roster() -> None:
    flat = " ".join(" ".join(gate.cmd) for gate in _verify_namespace()["GATES"])

    for retired in (
        "agents_doctor",
        "ruleset_doctor",
        "status_doctor",
        "github_doctor",
        "docs_doctor",
    ):
        assert retired not in flat


def test_every_gate_belongs_to_exactly_one_declared_shard() -> None:
    namespace = _verify_namespace()
    gates, shards = namespace["GATES"], namespace["SHARDS"]

    assigned = {gate.shard for gate in gates}
    assert assigned <= set(shards), (
        f"gates name shards SHARDS does not declare: {assigned - set(shards)}"
    )
    assert set(shards) <= assigned, (
        f"SHARDS declares shards no gate belongs to: {set(shards) - assigned}"
    )


def test_the_shards_reproduce_the_full_roster_exactly_once() -> None:
    """The parity guarantee: sharded CI verifies what a bare local run verifies.

    Before sharding, parity rested on CI invoking the same command string, which
    nothing asserted. This is what replaces that — a gate dropped from every
    shard, or landing in two, fails here rather than silently changing what a
    green required check means.
    """
    namespace = _verify_namespace()
    gates_for_run = namespace["_gates_for_run"]

    full = [" ".join(cmd) for cmd in gates_for_run(False)]
    union: list[str] = []
    for shard in namespace["SHARDS"]:
        union += [" ".join(cmd) for cmd in gates_for_run(False, shard)]

    assert sorted(union) == sorted(full), (
        "the shards do not partition the roster; CI and `python scripts/verify` "
        "would verify different things"
    )


def test_ci_runs_every_shard() -> None:
    """Nothing else stops verify.yml listing three of four shards and staying green."""
    workflow = yaml.safe_load(VERIFY_WORKFLOW.read_text(encoding="utf-8"))

    scope = workflow["jobs"]["scope"]
    assert scope["outputs"] == {
        "matrix": "${{ steps.scope.outputs.matrix }}",
        "ps1": "${{ steps.scope.outputs.ps1 }}",
        "docs_only": "${{ steps.scope.outputs.docs_only }}",
    }
    scope_script = next(step for step in scope["steps"] if step.get("id") == "scope")["run"]
    for default in (
        'matrix=\'{"shard":["lint","contract","runtime","sweep"]}\'',
        "ps1=true",
        "docs_only=false",
    ):
        assert scope_script.index(default) < scope_script.index("gh api")

    shards = workflow["jobs"]["shards"]
    assert shards["needs"] == "scope"
    assert shards["strategy"]["matrix"] == "${{ fromJSON(needs.scope.outputs.matrix) }}"

    # A matrix job named `verify` would publish `verify (lint)`, `verify (contract)`,
    # ... and the `verify` check `main` requires would vanish, blocking every PR.
    aggregate = workflow["jobs"]["verify"]
    assert aggregate["needs"] == ["scope", "shards"]
    assert aggregate["if"] == "always()"
    assert "needs.scope.result" in aggregate["steps"][0]["run"]
    assert "needs.shards.result" in aggregate["steps"][0]["run"]


def test_ci_provisions_verification_dependencies_in_their_owner_shards() -> None:
    """CI must not install a shard's isolated tooling in its siblings."""
    workflow = yaml.safe_load(VERIFY_WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["shards"]["steps"]

    precommit_cache = next(
        step for step in steps if step.get("name") == "Cache pre-commit environments"
    )
    gc = next(
        step
        for step in steps
        if step.get("name") == "Drop hook environments no longer referenced by the config"
    )
    pssa_cache = next(step for step in steps if step.get("name") == "Cache PSScriptAnalyzer module")
    bubblewrap = next(
        step
        for step in steps
        if step.get("name") == "Enable the code-execution sandbox (bubblewrap)"
    )
    python = next(
        step for step in steps if step.get("uses", "").startswith("actions/setup-python@")
    )

    assert precommit_cache["if"] == "matrix.shard == 'lint'"
    assert gc["if"] == "matrix.shard == 'lint'"
    assert pssa_cache["if"] == "matrix.shard == 'lint' && needs.scope.outputs.ps1 != 'false'"
    assert bubblewrap["if"] == "matrix.shard == 'runtime'"
    assert python["with"]["cache-dependency-path"] == "requirements-dev.txt\npyproject.toml"


def test_docs_only_runs_the_narrowed_tests_in_exactly_one_shard() -> None:
    """Otherwise the same `static` set runs once per shard, for no added coverage."""
    namespace = _verify_namespace()
    gates_for_run = namespace["_gates_for_run"]

    running = [
        shard
        for shard in namespace["SHARDS"]
        if any("pytest" in " ".join(cmd) for cmd in gates_for_run(True, shard))
    ]
    assert len(running) == 1, (
        f"expected exactly one shard to run pytest under docs-only, got {running}"
    )
    assert all(
        cmd[-1] == "static" for cmd in gates_for_run(True, running[0]) if "pytest" in " ".join(cmd)
    )


def test_only_a_vault_mutating_selection_takes_the_lock() -> None:
    """`e2e_smoke.py` resets <checkout>/test-vault; nothing else in the roster does.

    Deriving the lock from that property rather than taking it unconditionally is
    what lets two shards run side by side in one checkout.
    """
    namespace = _verify_namespace()
    gates, needs_lock = namespace["GATES"], namespace["_needs_vault_lock"]

    mutating = [g for g in gates if g.mutates_vault]
    assert [" ".join(g.cmd) for g in mutating] == ["python3 scripts/test_vault/e2e_smoke.py"]

    assert needs_lock(None) is True, "a full local run includes the vault-mutating gate"
    assert needs_lock(mutating[0].shard) is True
    for shard in namespace["SHARDS"]:
        if shard != mutating[0].shard:
            assert needs_lock(shard) is False, f"shard {shard} mutates no vault but takes the lock"


def test_json_and_powershell_are_gate_steps() -> None:
    namespace = _verify_namespace()

    assert callable(namespace["check_json"])
    assert callable(namespace["check_powershell"])


def test_docs_only_scope_narrows_the_roster() -> None:
    namespace = _verify_namespace()
    gates_for_run = namespace["_gates_for_run"]

    full = [" ".join(cmd) for cmd in gates_for_run(False)]
    docs = [" ".join(cmd) for cmd in gates_for_run(True)]

    # Full scope is the unchanged roster.
    assert full == [" ".join(gate.cmd) for gate in namespace["GATES"]]

    # Docs scope replaces full lint with its first prose hook + every product gate.
    assert docs[0] == "pre-commit run vale --hook-stage manual --all-files"
    assert full[0] == "pre-commit run --hook-stage manual --all-files"
    for gate in (
        "python3 scripts/checks/schema_doc_drift.py",
        "python3 scripts/checks/removed_surface_gate.py",
        "python3 scripts/checks/checked_terminology_gate.py",
        "python3 scripts/checks/plugin_provenance_doctor.py",
        "python3 scripts/checks/doc_claims_gate.py",
        "python3 scripts/checks/doc_link_targets.py",
        "python3 scripts/checks/doc_cited_paths.py",
        "python3 scripts/checks/control_plane_actor_gate.py",
    ):
        assert gate in docs

    # Docs scope narrows pytest to `static` and drops the code-only gates.
    pytest_gates = [d for d in docs if "pytest" in d]
    assert len(pytest_gates) == 1, f"docs scope must run pytest once, got {len(pytest_gates)}"
    assert pytest_gates[0].endswith("-m static")
    assert not any("e2e_smoke.py" in d for d in docs)
    assert not any("compileall" in d for d in docs)
    assert not any(d.startswith("bash -n") for d in docs)
    assert not any("memoria --version" in d for d in docs)

    # a docs-only diff provably cannot change packaging, so the wheel gate is skipped
    assert not any("wheel_gate" in d for d in docs)


def test_docs_only_lint_runs_exactly_the_prose_hook_roster() -> None:
    namespace = _verify_namespace()

    assert namespace["DOCS_LINT_HOOKS"] == (
        "vale",
        "markdownlint-structural",
        "mermaid-parse",
        "cspell",
    )
    commands = namespace["_gates_for_run"](True, "lint")
    assert commands[:4] == [
        ["pre-commit", "run", hook, "--hook-stage", "manual", "--all-files"]
        for hook in namespace["DOCS_LINT_HOOKS"]
    ]
    text = "\n".join(" ".join(command) for command in commands)
    assert not any(
        tool in text for tool in ("ruff", "mypy", "yamllint", "shellcheck", "oxlint", "oxfmt")
    )


def test_gate_entries_run_under_docs_scope_unless_opted_out() -> None:
    # Fail-safe default: a new roster entry that never considered docs-only
    # scope still runs there; docs=False is the explicit "provably cannot be
    # affected by a docs diff" claim.
    gate_type = _verify_namespace()["Gate"]

    assert gate_type(["echo", "ok"]).docs is True


def test_run_reports_a_missing_executable_instead_of_raising(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # `check=False` only suppresses a nonzero exit; a missing executable (e.g. an
    # editable install whose console script never landed on PATH) raises
    # FileNotFoundError instead, which `memoria --version` -- the roster's own
    # probe for that failure (#1689) -- would trip first.
    code = _verify_namespace()["run"](["memoria-does-not-exist-on-this-machine", "--version"])

    assert code == 127
    assert "command not found: memoria-does-not-exist-on-this-machine" in capsys.readouterr().err


def test_single_run_lock_admits_the_first_gate(tmp_path: Path) -> None:
    handle = _verify_namespace()["_hold_single_run_lock"](tmp_path / "verify.lock")

    assert handle is not None
    assert (tmp_path / "verify.lock").read_text(encoding="utf-8") == str(os.getpid())


def test_single_run_lock_refuses_a_second_gate_in_the_same_checkout(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lock = tmp_path / "verify.lock"
    namespace = _verify_namespace()
    held = namespace["_hold_single_run_lock"](lock)

    with pytest.raises(SystemExit) as exit_info:
        namespace["_hold_single_run_lock"](lock)

    assert exit_info.value.code == 1
    assert f"already running in this checkout (pid {os.getpid()})" in capsys.readouterr().err
    held.close()


def test_single_run_lock_is_released_when_the_holder_lets_go(tmp_path: Path) -> None:
    # flock lives on the open file description, so a dead run leaves no stale
    # lock -- releasing has to let the next gate straight in.
    lock = tmp_path / "verify.lock"
    namespace = _verify_namespace()
    namespace["_hold_single_run_lock"](lock).close()

    assert namespace["_hold_single_run_lock"](lock) is not None


def test_lock_is_per_checkout_not_global() -> None:
    namespace = _verify_namespace()

    assert namespace["LOCK_PATH"] == namespace["ROOT"] / ".verify.lock"
