"""Fail-closed code execution gate for project code artifacts."""

from __future__ import annotations

import hashlib
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from memoria_vault.runtime import state
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.policy.paths import normalize_path
from memoria_vault.runtime.time import now_iso
from memoria_vault.runtime.vaultio import write_bytes_durable


@dataclass(frozen=True)
class Availability:
    status: str
    reason: str = ""

    @property
    def available(self) -> bool:
        return self.status == "available"


def execution_availability(vault: Path) -> Availability:
    if platform.system() != "Linux":
        return Availability("unsupported", "code execution requires Linux/WSL bwrap")
    bwrap = shutil.which("bwrap")
    if not bwrap:
        return Availability("unsupported", "bwrap is not installed")
    proof = _bwrap_proof(bwrap)
    if not proof.available:
        return proof
    return Availability("available")


def run_artifact(
    vault: Path,
    artifact_id: str,
    *,
    run_id: str | None = None,
    timeout_s: int = 30,
    max_output_bytes: int = 1_000_000,
) -> dict[str, Any]:
    artifact = state.code_artifact(vault, artifact_id)
    if artifact is None:
        raise ValueError(f"unknown code artifact: {artifact_id}")
    command = artifact["approved_command"]
    if not command or not all(isinstance(part, str) and part for part in command):
        raise ValueError("code artifact approved_command must be a non-empty argv list")
    run = run_id or f"{artifact['artifact_id']}:{now_iso()}"
    availability = execution_availability(vault)
    if not availability.available:
        return state.record_code_run(
            vault,
            run_id=run,
            artifact_id=artifact["artifact_id"],
            command=command,
            cwd=artifact["source_dir"],
            sandbox_backend="bwrap",
            run_state="unavailable",
            timeout_result=availability.reason,
        )
    return _run_with_bwrap(
        vault, artifact, run, timeout_s=timeout_s, max_output_bytes=max_output_bytes
    )


def _bwrap_proof(bwrap: str) -> Availability:
    proc = subprocess.run(
        [
            bwrap,
            *_base_bwrap_args(),
            "--unshare-net",
            "--die-with-parent",
            "--tmpfs",
            "/tmp",  # noqa: S108 - sandbox-local tmpfs, not host temp storage.
            "true",
        ],
        capture_output=True,
        check=False,
    )
    if proc.returncode:
        return Availability("unsupported", proc.stderr.decode(errors="replace").strip())
    return Availability("available")


def _run_with_bwrap(
    vault: Path,
    artifact: dict[str, Any],
    run_id: str,
    *,
    timeout_s: int,
    max_output_bytes: int,
) -> dict[str, Any]:
    bwrap = shutil.which("bwrap")
    if not bwrap:
        raise RuntimeError("bwrap disappeared after availability check")
    vault = Path(vault)
    source_dir = (vault / artifact["source_dir"]).resolve()
    output_dir = (vault / artifact["output_dir"]).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        bwrap,
        *_base_bwrap_args(),
        "--unshare-net",
        "--die-with-parent",
        "--ro-bind",
        str(source_dir),
        "/workspace",
        "--bind",
        str(output_dir),
        "/outputs",
        "--chdir",
        "/workspace",
        *artifact["approved_command"],
    ]
    started = now_iso()
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            timeout=timeout_s,
            check=False,
            env={"PATH": "/usr/bin:/bin", "HOME": "/tmp"},  # noqa: S108
        )
        timeout_result = ""
    except subprocess.TimeoutExpired as exc:
        proc = subprocess.CompletedProcess(command, 124, exc.stdout or b"", exc.stderr or b"")
        timeout_result = "timeout"
    stdout = bytes(proc.stdout or b"")[:max_output_bytes]
    stderr = bytes(proc.stderr or b"")[:max_output_bytes]
    run_root = vault / ".memoria/code-runs" / normalize_path(run_id)
    stdout_path = run_root / "stdout.txt"
    stderr_path = run_root / "stderr.txt"
    write_bytes_durable(stdout_path, stdout, create_parent=True)
    write_bytes_durable(stderr_path, stderr, create_parent=True)
    outputs = _output_hashes(vault, artifact["declared_outputs"])
    return state.record_code_run(
        vault,
        run_id=run_id,
        artifact_id=artifact["artifact_id"],
        command=artifact["approved_command"],
        cwd=artifact["source_dir"],
        sanitized_env=["HOME", "PATH"],
        input_hashes=_output_hashes(vault, artifact["declared_inputs"]),
        output_hashes=outputs,
        stdout_sha256=_sha256_bytes(stdout),
        stderr_sha256=_sha256_bytes(stderr),
        stdout_path=stdout_path.relative_to(vault).as_posix(),
        stderr_path=stderr_path.relative_to(vault).as_posix(),
        exit_status=int(proc.returncode),
        timeout_result=timeout_result,
        sandbox_backend="bwrap",
        sandbox_profile_hash=_sha256_bytes(b"bwrap:v1:no-network"),
        run_state="succeeded" if proc.returncode == 0 and not timeout_result else "failed",
        started_at=started,
        ended_at=now_iso(),
    )


def _base_bwrap_args() -> list[str]:
    args = []
    for path in ("/usr", "/bin", "/lib", "/lib64"):
        if Path(path).exists():
            args.extend(["--ro-bind", path, path])
    args.extend(["--dev", "/dev", "--proc", "/proc"])
    return args


def _output_hashes(vault: Path, relpaths: list[str]) -> dict[str, str]:
    hashes = {}
    for relpath in relpaths:
        rel = normalize_path(relpath)
        path = Path(vault) / rel
        if path.is_file():
            hashes[rel] = sha256_file(path)
    return hashes


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()
