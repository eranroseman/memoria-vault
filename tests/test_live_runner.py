"""Opt-in live runner checks for alpha.14."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from memoria_vault.cli import main


@pytest.mark.live
def test_live_runner_doctor_dispatches(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    if not (os.environ.get("MEMORIA_MODEL_BASE_URL") or os.environ.get("OPENAI_BASE_URL")):
        pytest.skip("set MEMORIA_MODEL_BASE_URL or OPENAI_BASE_URL to run live runner proof")

    workspace = tmp_path / "workspace"
    rc = main(["init", "--workspace", str(workspace), "--yes", "--json"])
    assert rc == 0, capsys.readouterr().out
    capsys.readouterr()

    provider = os.environ.get("MEMORIA_MODEL_PROVIDER", "local")
    rc = main(
        [
            "doctor",
            "--workspace",
            str(workspace),
            "--check",
            "runner",
            "--provider",
            provider,
            "--live",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0, output
    assert output["ok"] is True
    assert output["checks"]["runner_dependency"] is True
    assert output["checks"]["runner_agent_constructed"] is True
    assert output["checks"]["runner_live_dispatch"] is True
