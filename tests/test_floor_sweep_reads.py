"""Read-action sweep: every read action x every declared transport.

Spec: docs/superpowers/specs/2026-07-13-development-pipeline-spec.md §3.4.
"""

from __future__ import annotations

import pytest

from memoria_vault.engine.surface_contract import actions_by_id
from tests.floor_lib import (
    ARG_TABLE,
    _fill,
    assert_invariants,
    read_only_guard,
    run_cli,
    run_http,
    seed_vault,
)

READ_ACTIONS = sorted(a for a, d in actions_by_id().items() if d["kind"] == "read")
TRANSPORTS = ("cli", "http", "mcp")


@pytest.fixture(scope="module")
def vault(tmp_path_factory: pytest.TempPathFactory):
    v, manifest = seed_vault(tmp_path_factory.mktemp("floor-reads"))
    return v, manifest


@pytest.mark.parametrize("action_id", READ_ACTIONS)
@pytest.mark.parametrize("transport", TRANSPORTS)
def test_read_action(vault, action_id: str, transport: str) -> None:
    v, manifest = vault
    entry = ARG_TABLE.get(action_id)
    if entry is None:
        # Not yet registered — completeness is enforced by
        # test_floor_coverage.py (Task 7), not by an erroring sweep case.
        pytest.skip(f"{action_id} not yet in ARG_TABLE")
    binding = entry.get(transport)
    if binding is None:
        pytest.skip(f"{action_id} declares no {transport} binding")
    if transport == "mcp":
        pytest.importorskip("mcp")
        from tests.floor_lib import run_mcp
    with read_only_guard(v):
        if transport == "cli":
            payload = run_cli(v, _fill(binding, manifest))
        elif transport == "http":
            method, path = binding
            payload = run_http(v, method, _fill(path, manifest))
        else:
            tool, arguments = binding
            payload = run_mcp(v, tool, _fill(arguments, manifest))
    assert payload.get("ok") is True
    assert payload.get("api_version") == "engine-read-api.v1"
    assert_invariants(v)
