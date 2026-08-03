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

# 1733: the xdist_group pins this module to one worker under --dist
# loadgroup so its module-scoped seed_vault fixture builds once per run
# instead of once per worker (~30s per rebuild).
pytestmark = [pytest.mark.floor, pytest.mark.xdist_group("floor-sweep-reads-seed")]

ACTIONS_BY_ID = actions_by_id()
READ_ACTIONS = sorted(
    a for a, d in ACTIONS_BY_ID.items() if d["kind"] == "read" and not d.get("reserved")
)
TRANSPORTS = ("cli", "http", "mcp")


def _assert_response_envelope(action_id: str, payload: dict) -> None:
    """ok is always required. api_version is only required when the action's
    surface_contract entry declares a response_version — actions whose
    transport response intentionally isn't a Memoria read-API envelope (e.g.
    surface.openapi's raw OpenAPI document over http) leave response_version
    unset and carry no api_version key."""
    assert payload.get("ok") is True
    expected_version = ACTIONS_BY_ID[action_id].get("response_version")
    if expected_version is not None:
        assert payload.get("api_version") == expected_version


# Real, pre-existing contract/implementation mismatches the sweep uncovers —
# not ARG_TABLE binding errors. Register a genuine gap here as
# (action_id, transport) -> reason and the test below marks it
# `xfail(strict=True)`: a real bug gets flagged rather than papered over by a
# weakened assertion, and `strict=True` means an unexpected pass fails the
# suite, so resolving a registered gap requires removing its entry here.
KNOWN_CONTRACT_GAPS: dict[tuple[str, str], str] = {}


def _dispatch_and_check(v, action_id: str, binding, transport: str, manifest) -> None:
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
    _assert_response_envelope(action_id, payload)
    assert_invariants(v)


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
        # test_floor_coverage.py, not by an erroring sweep case.
        pytest.skip(f"{action_id} not yet in ARG_TABLE")
    binding = entry.get(transport)
    if binding is None:
        pytest.skip(f"{action_id} declares no {transport} binding")
    _dispatch_and_check(v, action_id, binding, transport, manifest)


# (action_id, overlay) pairs flattened out of VARIANTS, one case per
# hand-picked pairwise combination — see floor_lib.py's VARIANTS notes for
# why individual overlay values have the shapes they do.
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
    _dispatch_and_check(v, action_id, binding, transport, manifest)
