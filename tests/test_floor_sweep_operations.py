"""Operation sweep: every cataloged operation run through the worker.

Spec: docs/superpowers/specs/2026-07-13-development-pipeline-spec.md §3.4.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from memoria_vault.runtime.capabilities import iter_capability_manifests
from tests.floor_lib import OPERATION_REGISTRY, _fill, assert_invariants, seed_vault, vault_digest

OPERATION_IDS = sorted(
    m["frontmatter"]["operation_id"] for m in iter_capability_manifests("operation")
)

# Known bugs the floor sweep uncovered: the operation is expected (by
# manifest/design) to complete via the offline deterministic-fixture runner,
# but a real defect in the current implementation makes every seeded run of
# it crash. Recorded here — not silently special-cased — so the strict xfail
# turns into a loud failure the moment the underlying bug is fixed without
# this entry being updated. See task-6-report.md for the full trace.
_KNOWN_BUGS: dict[str, str] = {
    "check-falsifiability": (
        "run_prompt_operation (runtime/operations.py) commits its staged "
        "output via commit_writer_changes(..., [stage['staging_id']]), but "
        ".memoria/staging/ is gitignored by the packaged workspace "
        ".gitignore template; `git add` (trusted_writer.py:_commit_writer_"
        "changes, no -f) fails with 'ignored by one of your .gitignore "
        "files' on any vault built via `memoria init`. Affects every "
        "prompt-family op sharing run_prompt_operation (analyze-claims, "
        "check-falsifiability, compare-and-contrast, extract-claim-stubs, "
        "red-team-argument, summarize-for-recall)."
    ),
}

OPERATION_PARAMS = [
    pytest.param(
        operation_id, marks=pytest.mark.xfail(reason=_KNOWN_BUGS[operation_id], strict=True)
    )
    if operation_id in _KNOWN_BUGS
    else operation_id
    for operation_id in OPERATION_IDS
]


@pytest.mark.parametrize("operation_id", OPERATION_PARAMS)
def test_operation(tmp_path: Path, operation_id: str) -> None:
    from memoria_vault.runtime.worker import enqueue_operation, run_next_job

    vault, manifest = seed_vault(tmp_path)
    entry = OPERATION_REGISTRY.get(operation_id)
    if entry is None:
        # Not yet registered — completeness is enforced by
        # test_floor_coverage.py (Task 7), not by an erroring sweep case.
        pytest.skip(f"{operation_id} not yet in OPERATION_REGISTRY")
    payload = _fill(entry["payload"], manifest)
    queued = enqueue_operation(
        vault,
        operation_id,
        payload=payload,
        idempotency_key=f"floor:{operation_id}",
        actor="agent",
    )
    done = run_next_job(vault, machine="floor")
    assert done is not None, queued
    if entry["expect"] == "done":
        assert done["status"] == "done", (operation_id, done)
        for rel in _fill(entry.get("creates", []), manifest):
            assert (vault / rel).exists(), f"{operation_id} missing output {rel}"
    else:
        assert done["status"] != "done", (operation_id, done)
        assert entry["reason"] in str(done), (operation_id, done)
    # Journal recorded the run, and the vault is still coherent — always.
    kinds = vault_digest(vault)["journal_kinds"]
    assert kinds, "operation left no journal event"
    assert_invariants(vault)
