"""Operation sweep: every cataloged operation run through the worker.

Spec: docs/superpowers/specs/2026-07-13-development-pipeline-spec.md §3.4.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from memoria_vault.runtime.capabilities import iter_capability_manifests
from tests.floor_lib import (
    OPERATION_REGISTRY,
    _fill,
    assert_golden,
    assert_invariants,
    seed_vault,
    vault_digest,
)

OPERATION_IDS = sorted(
    m["frontmatter"]["operation_id"] for m in iter_capability_manifests("operation")
)

# Known bugs the floor sweep uncovered: the operation is expected (by
# manifest/design) to complete via the offline deterministic-fixture runner,
# but a real defect in the current implementation makes every seeded run of
# it crash. Recorded here — not silently special-cased — so the strict xfail
# turns into a loud failure the moment the underlying bug is fixed without
# this entry being updated.
#
# The six run_prompt_operation ids (#1391) and verify-project-draft (#1393)
# were fixed and no longer have entries here; write-project-slice's bug is a
# side effect on a DIFFERENT tracked projection. render_project_argument_
# canvas (knowledge.py:1735-1743) branches on outline.md's mere existence:
# with no outline.md it renders canvas nodes/edges from
# analyze_project_argument's full graph traversal; once outline.md exists it
# renders from the BM25-ranked project slice instead (a different,
# order-dependent node/edge set). check_tracked_projections
# (projections.py:56-78) — the floor's own tracked-projection drift
# detector, asserted after every operation via assert_invariants — calls
# this same render function as its "live" canonical renderer. So any
# project whose argument.canvas was already rendered (via
# render-project-argument-canvas, e.g. during typed-graph seeding) *before*
# its first write-project-slice run is retroactively flagged "stale" the
# moment outline.md appears, even though write-project-slice never touches,
# recommits, or is documented to invalidate the canvas file. Confirmed
# live: assert_invariants' check_tracked_projections reports
# `{"path": "projects/package-gate/argument.canvas", "status": "stale"}`
# immediately after a real write-project-slice run against the seed. Filed
# as GitHub issue #1394.
_KNOWN_BUGS: dict[str, str] = {
    "write-project-slice": (
        "render_project_argument_canvas (knowledge.py:1735-1743) branches "
        "on outline.md's mere existence, switching from a full "
        "argument-graph traversal to a BM25-ranked project-slice ordering; "
        "check_tracked_projections (projections.py:56-78) uses the same "
        "renderer as its canonical 'expected' value, so write-project-slice "
        "retroactively marks any pre-existing argument.canvas 'stale' "
        "without itself regenerating or recommitting it."
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
    idempotency_key = (
        _fill(entry["idempotency_key"], manifest)
        if "idempotency_key" in entry
        else f"floor:{operation_id}"
    )
    queued = enqueue_operation(
        vault,
        operation_id,
        payload=payload,
        idempotency_key=idempotency_key,
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
    # Invariants (above) are the always-on correctness battery; the golden
    # digest is a supplement for exact-state regression detection, generated
    # only for the done branch (spec §3.4) — refused ops never write vault
    # state, and xfail ops (the known-bugs table above) crash before reaching
    # this line at all.
    if entry["expect"] == "done":
        assert_golden(operation_id, vault_digest(vault))
