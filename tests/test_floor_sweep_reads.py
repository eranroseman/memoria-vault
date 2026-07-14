"""Read-action sweep: every read action x every declared transport.

Spec: docs/superpowers/specs/2026-07-13-development-pipeline-spec.md §3.4.
"""

from __future__ import annotations

import pytest

from memoria_vault.engine.surface_contract import actions_by_id
from tests.floor_lib import (
    ARG_TABLE,
    VARIANTS,
    _fill,
    _overlay,
    assert_invariants,
    read_only_guard,
    run_cli,
    run_http,
    seed_vault,
)

READ_ACTIONS = sorted(a for a, d in actions_by_id().items() if d["kind"] == "read")
TRANSPORTS = ("cli", "http", "mcp")

# Real, pre-existing contract/implementation mismatches uncovered by
# completing the ARG_TABLE (Task 7a) — not ARG_TABLE binding errors. The
# surface_contract entry for `surface.openapi` declares
# `response_version: "engine-read-api.v1"`, but its http handler
# (`http_transport.openapi_schema`) returns a raw OpenAPI 3.1 document
# (`{"ok": True, "openapi": "3.1.0", "info": {...}, "paths": {...}}`) with no
# `api_version` key — unlike every other read action, which goes through
# `engine_api._read_payload()` and always sets it. This is deliberate on the
# http side (a valid OpenAPI document has its own `openapi` version field;
# splicing in an unrelated `api_version` would be odd for tooling consuming
# `/openapi.json`), but it means the contract's declared response_version is
# not honored for this one action — a real, narrow inconsistency, not a
# sweep-harness mistake. `xfail(strict=True)`, following the same "found a
# real bug, don't fake the assertion, flag if it's ever silently fixed"
# convention `tests/test_floor_sweep_operations.py` set for
# `check-falsifiability` (task-6-report.md).
KNOWN_CONTRACT_GAPS = {
    ("surface.openapi", "http"): (
        "surface.openapi's http handler (http_transport.openapi_schema) returns a raw "
        "OpenAPI document with no api_version key, though its surface_contract entry "
        "declares response_version=engine-read-api.v1 — see test_floor_sweep_reads.py "
        "module docstring/comment for the full root cause."
    ),
}


@pytest.fixture(scope="module")
def vault(tmp_path_factory: pytest.TempPathFactory):
    v, manifest = seed_vault(tmp_path_factory.mktemp("floor-reads"))
    return v, manifest


@pytest.mark.parametrize("action_id", READ_ACTIONS)
@pytest.mark.parametrize("transport", TRANSPORTS)
def test_read_action(vault, action_id: str, transport: str, request: pytest.FixtureRequest) -> None:
    if reason := KNOWN_CONTRACT_GAPS.get((action_id, transport)):
        request.node.add_marker(pytest.mark.xfail(strict=True, reason=reason))
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


# Task 9: (action_id, overlay) pairs flattened out of VARIANTS, one case per
# hand-picked pairwise combination — see floor_lib.py's VARIANTS docstring
# for the corrections this table needed vs. the original brief.
VARIANT_CASES = [
    (action_id, index, overlay)
    for action_id, overlays in VARIANTS.items()
    for index, overlay in enumerate(overlays)
]


@pytest.mark.parametrize("transport", TRANSPORTS)
@pytest.mark.parametrize(
    ("action_id", "variant_index", "overlay"),
    VARIANT_CASES,
    ids=[f"{action_id}-{index}" for action_id, index, _ in VARIANT_CASES],
)
def test_read_action_variant(
    vault, action_id: str, variant_index: int, overlay: dict, transport: str
) -> None:
    """Each VARIANTS overlay x each transport the action declares a binding
    for — same read-only/ok/api_version contract as test_read_action above,
    just with `_overlay` splicing the extra params into the CLI flags / HTTP
    query / MCP arguments before dispatch."""
    v, manifest = vault
    entry = ARG_TABLE[action_id]
    binding = _overlay(entry, transport, overlay)
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
