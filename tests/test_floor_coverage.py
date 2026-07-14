"""Completeness meta-tests: every catalog entry has a floor registry entry.

Spec: docs/superpowers/specs/2026-07-13-development-pipeline-spec.md §3.4.

Task 7a seeded only the read-action coverage test (ARG_TABLE). Task 7b
(7b-1 + 7b-2) completed OPERATION_REGISTRY (all 52 cataloged operation ids),
so the operation-registry coverage tests are added here now.
"""

from __future__ import annotations

from memoria_vault.engine.surface_contract import actions_by_id
from memoria_vault.runtime.capabilities import iter_capability_manifests
from tests.floor_lib import ARG_TABLE, OPERATION_REGISTRY


def test_every_read_action_covers_every_declared_transport() -> None:
    problems = []
    for action_id, action in actions_by_id().items():
        if action["kind"] != "read":
            continue
        entry = ARG_TABLE.get(action_id)
        if entry is None:
            problems.append(f"{action_id}: no ARG_TABLE entry")
            continue
        for transport in ("cli", "http", "mcp"):
            declared = bool(action.get(transport))
            if declared and entry.get(transport) is None:
                problems.append(f"{action_id}: {transport} declared but not swept")
            if not declared and entry.get(transport) is not None:
                problems.append(f"{action_id}: {transport} swept but not declared")
    assert not problems, "\n".join(problems)


def test_every_operation_has_a_floor_entry() -> None:
    catalog = {m["frontmatter"]["operation_id"] for m in iter_capability_manifests("operation")}
    missing = sorted(catalog - OPERATION_REGISTRY.keys())
    assert not missing, f"operations without floor entries: {missing}"
    stale = sorted(OPERATION_REGISTRY.keys() - catalog)
    assert not stale, f"floor entries for retired operations: {stale}"


def test_refused_entries_carry_reasons() -> None:
    bad = [
        op
        for op, entry in OPERATION_REGISTRY.items()
        if entry["expect"] == "refused" and not entry.get("reason")
    ]
    assert not bad, f"refused without asserted reason: {bad}"
