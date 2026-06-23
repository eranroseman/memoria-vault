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
