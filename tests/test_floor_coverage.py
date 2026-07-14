"""Completeness meta-tests: every catalog entry has a floor registry entry.

Spec: docs/superpowers/specs/2026-07-13-development-pipeline-spec.md §3.4.

Task 7a seeds only the read-action coverage test (ARG_TABLE); the
operation-registry coverage test (OPERATION_REGISTRY) is Task 7b's, since
operations are not yet fully registered.
"""

from __future__ import annotations

from memoria_vault.engine.surface_contract import actions_by_id
from tests.floor_lib import ARG_TABLE


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
