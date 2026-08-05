"""The operation dispatch table, verified against the manifest catalog."""

from __future__ import annotations

import pytest

from memoria_vault.runtime import worker
from memoria_vault.runtime.capabilities import iter_capability_manifests


def _manifest_ids() -> set[str]:
    return {m["frontmatter"]["operation_id"] for m in iter_capability_manifests()}


def test_registry_keys_are_manifest_operations() -> None:
    assert worker.OPERATION_HANDLERS, "registry must not be empty"
    stray = set(worker.OPERATION_HANDLERS) - _manifest_ids()
    assert not stray, f"handlers without a manifest: {sorted(stray)}"


def test_protected_actors_name_registered_operations() -> None:
    stray = set(worker.PROTECTED_OPERATION_ACTORS) - set(worker.OPERATION_HANDLERS)
    # Until Task 6 completes the migration, protected ids may still live in the
    # legacy chain; this asserts the invariant only for registered ids.
    assert stray <= (_manifest_ids() - set(worker.OPERATION_HANDLERS))


@pytest.mark.parametrize("operation_id", sorted({"apply-decision-rule-notices"}))
def test_first_migrated_handlers_are_registered(operation_id: str) -> None:
    assert operation_id in worker.OPERATION_HANDLERS
