"""Parity across the floor harness's in-process transports.

Spec: docs/superpowers/specs/2026-07-13-development-pipeline-spec.md §3.4.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.floor_lib import run_cli, run_http, seed_vault

pytest.importorskip("mcp")
from tests.floor_lib import run_mcp


def test_status_parity_across_transports(tmp_path: Path) -> None:
    vault, _ = seed_vault(tmp_path)
    via_cli = run_cli(vault, ["status"])
    via_http = run_http(vault, "GET", "/status")
    via_mcp = run_mcp(vault, "status", {})
    for payload in (via_cli, via_http, via_mcp):
        assert payload.get("ok") is True
        assert payload.get("api_version") == "engine-read-api.v1"
    assert via_http.keys() == via_mcp.keys()
