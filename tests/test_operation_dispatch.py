"""The operation dispatch table, verified against the manifest catalog."""

from __future__ import annotations

import pytest

from memoria_vault.runtime import worker
from memoria_vault.runtime.capabilities import iter_capability_manifests

pytestmark = pytest.mark.contract


def _manifest_ids() -> set[str]:
    return {m["frontmatter"]["operation_id"] for m in iter_capability_manifests()}


def test_registry_matches_the_manifest_catalog_exactly() -> None:
    manifest_ids = _manifest_ids()
    registered = set(worker.OPERATION_HANDLERS)
    assert registered == manifest_ids, (
        f"missing handlers: {sorted(manifest_ids - registered)}; "
        f"handlers without a manifest: {sorted(registered - manifest_ids)}"
    )


def test_protected_actors_name_registered_operations() -> None:
    stray = set(worker.PROTECTED_OPERATION_ACTORS) - set(worker.OPERATION_HANDLERS)
    assert not stray, f"protected ids without a handler: {sorted(stray)}"
