"""Tests for the verification gate wrapper."""

from __future__ import annotations

import json
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
        "bash scripts/test.sh all",
        "bash scripts/e2e-smoke.sh",
    ]


def test_verify_live_dry_run_includes_alpha11_cycle(tmp_path: Path) -> None:
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
        "bash scripts/test-l2.sh",
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
        "bash scripts/test.sh all",
        "bash scripts/e2e-smoke.sh",
        "python3 -m pytest tests/test_alpha11_cycle.py -q",
        "bash scripts/test-l2.sh",
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
        "bash scripts/test.sh all",
        "bash scripts/e2e-smoke.sh",
        "python3 -m pytest tests/test_alpha11_cycle.py -q",
        "bash scripts/test-l2.sh",
    ]
    assert summary["manual_follow_up"] == [
        "Complete product/manual release evidence in the release parent issue.",
        "Follow .agents/playbooks/release.md for release cut checks.",
    ]
