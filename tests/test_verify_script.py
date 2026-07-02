"""Tests for the verification gate wrapper."""

from __future__ import annotations

import hashlib
import json
import runpy
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_verify_dry_run_writes_evidence(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/verify",
            "--dry-run",
            "--evidence-dir",
            str(tmp_path),
            "package",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["mode"] == "package"
    assert summary["result"] == "dry-run"
    assert summary["gates"] == ["source", "package"]
    assert [step["display"] for step in summary["steps"]] == [
        "bash scripts/test.sh source",
        f"python3 -m pip wheel --no-build-isolation --wheel-dir {tmp_path}/dist .",
        f"python3 -m venv --clear {tmp_path}/venv",
        (
            f"{tmp_path}/venv/bin/python -m pip install --force-reinstall --no-index "
            f"--find-links {tmp_path}/dist memoria-vault"
        ),
        f"{tmp_path}/venv/bin/python -c 'import memoria_vault; print(memoria_vault.__version__)'",
        "bash scripts/e2e-smoke.sh",
    ]
    assert summary["artifacts"] == []
    assert summary["versions"] == {
        "package_init": "0.1.0a10",
        "pyproject": "0.1.0a10",
    }


def test_verify_live_dry_run_includes_standalone_runtime_gates(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/verify",
            "--dry-run",
            "--evidence-dir",
            str(tmp_path),
            "live",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["mode"] == "live"
    assert summary["result"] == "dry-run"
    assert summary["gates"] == ["runtime"]
    assert [step["display"] for step in summary["steps"]] == [
        "python3 -m pytest tests/test_alpha11_cycle.py -q",
        (
            "python3 -m pytest tests/test_cli.py tests/test_seeded_errors.py "
            "tests/test_worker_queue.py -q"
        ),
    ]


def test_verify_runtime_dry_run_keeps_gate_order(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/verify",
            "--dry-run",
            "--evidence-dir",
            str(tmp_path),
            "runtime",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["gates"] == ["source", "package", "runtime"]
    assert [step["display"] for step in summary["steps"]] == [
        "bash scripts/test.sh source",
        f"python3 -m pip wheel --no-build-isolation --wheel-dir {tmp_path}/dist .",
        f"python3 -m venv --clear {tmp_path}/venv",
        (
            f"{tmp_path}/venv/bin/python -m pip install --force-reinstall --no-index "
            f"--find-links {tmp_path}/dist memoria-vault"
        ),
        f"{tmp_path}/venv/bin/python -c 'import memoria_vault; print(memoria_vault.__version__)'",
        "bash scripts/e2e-smoke.sh",
        "python3 -m pytest tests/test_alpha11_cycle.py -q",
        (
            "python3 -m pytest tests/test_cli.py tests/test_seeded_errors.py "
            "tests/test_worker_queue.py -q"
        ),
    ]


def test_verify_rc_dry_run_keeps_manual_release_gates(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/verify",
            "--dry-run",
            "--evidence-dir",
            str(tmp_path),
            "rc",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["gates"] == ["source", "package", "runtime"]
    assert [step["display"] for step in summary["steps"]] == [
        "bash scripts/test.sh source",
        f"python3 -m pip wheel --no-build-isolation --wheel-dir {tmp_path}/dist .",
        f"python3 -m venv --clear {tmp_path}/venv",
        (
            f"{tmp_path}/venv/bin/python -m pip install --force-reinstall --no-index "
            f"--find-links {tmp_path}/dist memoria-vault"
        ),
        f"{tmp_path}/venv/bin/python -c 'import memoria_vault; print(memoria_vault.__version__)'",
        "bash scripts/e2e-smoke.sh",
        "python3 -m pytest tests/test_alpha11_cycle.py -q",
        (
            "python3 -m pytest tests/test_cli.py tests/test_seeded_errors.py "
            "tests/test_worker_queue.py -q"
        ),
    ]
    assert summary["manual_follow_up"] == [
        "Complete product/manual release evidence in the release parent issue.",
        "Follow .agents/playbooks/release.md for release cut checks.",
    ]


def test_artifact_hashes_reports_built_distribution(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    artifact = dist / "memoria_vault-0.1.0a10-py3-none-any.whl"
    artifact.write_bytes(b"wheel bytes")
    namespace = runpy.run_path(str(ROOT / "scripts/verify"))

    assert namespace["artifact_hashes"](tmp_path) == [
        {
            "file": str(artifact),
            "bytes": 11,
            "sha256": hashlib.sha256(b"wheel bytes").hexdigest(),
        }
    ]


def test_cleanup_package_build_artifacts_removes_local_build_outputs(tmp_path: Path) -> None:
    namespace = runpy.run_path(str(ROOT / "scripts/verify"))
    namespace["cleanup_package_build_artifacts"].__globals__["ROOT"] = tmp_path
    (tmp_path / "build").mkdir()
    (tmp_path / "src" / "memoria_vault.egg-info").mkdir(parents=True)
    (tmp_path / "dist").mkdir()

    namespace["cleanup_package_build_artifacts"]()

    assert not (tmp_path / "build").exists()
    assert not (tmp_path / "src" / "memoria_vault.egg-info").exists()
    assert (tmp_path / "dist").is_dir()


def test_prepare_package_evidence_removes_stale_artifact_state(tmp_path: Path) -> None:
    namespace = runpy.run_path(str(ROOT / "scripts/verify"))
    (tmp_path / "dist").mkdir()
    (tmp_path / "venv").mkdir()
    (tmp_path / "summary.json").write_text("keep", encoding="utf-8")

    namespace["prepare_package_evidence"](tmp_path)

    assert not (tmp_path / "dist").exists()
    assert not (tmp_path / "venv").exists()
    assert (tmp_path / "summary.json").read_text(encoding="utf-8") == "keep"
