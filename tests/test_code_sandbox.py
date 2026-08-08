"""The bwrap sandbox's isolation properties, pinned behaviorally.

These execute real code inside the real sandbox. Locally they skip when bwrap
is unavailable (the pwsh precedent), but under MEMORIA_REQUIRE_SANDBOX=1 (CI) a
skip becomes a hard failure, so a runner-image change cannot silently return
this module to never running.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from memoria_vault.runtime.code.execution import execution_availability, run_artifact
from memoria_vault.runtime.code.records import create_code_artifact
from memoria_vault.runtime.policy.audit import sha256_file

pytestmark = pytest.mark.runtime


@pytest.fixture
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
    """--unshare-net is the sandbox's core claim; before this test existed,
    deleting it failed nowhere else."""
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
    assert run["run_status"] == "succeeded"  # blocked network is the *expected* outcome


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
    artifact = _probe_artifact(
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
    source = sandbox_vault / artifact["source_dir"]
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
    assert run["run_status"] == "succeeded"
    assert run["output_hashes"] == {out_rel: sha256_file(host_file)}


def test_a_run_that_overstays_its_timeout_is_failed_and_says_so(sandbox_vault: Path) -> None:
    _probe_artifact(sandbox_vault, "slow-probe", "import time\ntime.sleep(60)\n")

    run = run_artifact(sandbox_vault, "slow-probe", run_id="slow-1", timeout_s=2)

    assert run["run_status"] == "failed"
    assert run["timeout_result"] == "timeout"
    assert run["exit_status"] == 124


def test_sandboxed_code_dies_when_its_runner_is_killed(sandbox_vault: Path) -> None:
    heartbeat_rel = "projects/project-alpha/code/parent-death/outputs/heartbeat.txt"
    heartbeat = sandbox_vault / heartbeat_rel
    _probe_artifact(
        sandbox_vault,
        "parent-death",
        "from pathlib import Path\n"
        "import time\n"
        "heartbeat = Path('/outputs/heartbeat.txt')\n"
        "scratch = Path('/outputs/heartbeat.tmp')\n"
        "counter = 0\n"
        "while True:\n"
        "    scratch.write_text(f'{counter}\\n', encoding='utf-8')\n"
        "    scratch.replace(heartbeat)\n"
        "    counter += 1\n"
        "    time.sleep(0.1)\n",
        declared_outputs=[heartbeat_rel],
    )
    helper_program = (
        "import sys\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "from pathlib import Path\n"
        "from memoria_vault.runtime.code.execution import run_artifact\n"
        "run_artifact(Path(sys.argv[2]), 'parent-death', "
        "run_id='parent-death-1', timeout_s=60)\n"
    )
    helper = subprocess.Popen(
        [
            sys.executable,
            "-c",
            helper_program,
            str(Path(__file__).parents[1] / "src"),
            str(sandbox_vault),
        ],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        seen: set[int] = set()
        progress_deadline = time.monotonic() + 10
        while len(seen) < 2 and time.monotonic() < progress_deadline:
            try:
                seen.add(int(heartbeat.read_text(encoding="utf-8").strip()))
            except (FileNotFoundError, ValueError):
                pass
            assert helper.poll() is None, f"artifact runner exited early: {helper.returncode}"
            time.sleep(0.05)
        assert len(seen) >= 2, "sandbox heartbeat did not advance"

        os.kill(helper.pid, signal.SIGKILL)
        helper.wait(timeout=5)

        last_value = heartbeat.read_text(encoding="utf-8")
        stable_since = time.monotonic()
        stability_deadline = stable_since + 8
        while time.monotonic() < stability_deadline:
            time.sleep(0.1)
            value = heartbeat.read_text(encoding="utf-8")
            if value != last_value:
                last_value = value
                stable_since = time.monotonic()
            if time.monotonic() - stable_since >= 2:
                break
        else:
            pytest.fail("sandbox heartbeat continued after its runner was killed")
    finally:
        try:
            os.killpg(helper.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            helper.wait(timeout=5)
        except subprocess.TimeoutExpired:
            helper.kill()
            helper.wait(timeout=5)


def test_stdout_is_truncated_at_the_declared_cap(sandbox_vault: Path) -> None:
    _probe_artifact(sandbox_vault, "loud-probe", "print('x' * 1000)\n")

    run = run_artifact(sandbox_vault, "loud-probe", run_id="loud-1", max_output_bytes=64)

    raw = (sandbox_vault / run["stdout_path"]).read_bytes()
    assert len(raw) == 64  # <= would pass vacuously on empty stdout too
