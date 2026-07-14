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
# this entry being updated. See task-6-report.md for the full trace; filed as
# GitHub issue #1391 ("run_prompt_operation commits the gitignored staging
# path — 6 prompt-family operations crash on real init vaults").
_PROMPT_STAGING_GITIGNORE_BUG = (
    "run_prompt_operation (runtime/operations.py) commits its staged "
    "output via commit_writer_changes(..., [stage['staging_id']]), but "
    ".memoria/staging/ is gitignored by the packaged workspace "
    ".gitignore template; `git add` (trusted_writer.py:_commit_writer_"
    "changes, no -f) fails with 'ignored by one of your .gitignore "
    "files' on any vault built via `memoria init`. Affects every "
    "prompt-family op sharing run_prompt_operation (analyze-claims, "
    "check-falsifiability, compare-and-contrast, extract-claim-stubs, "
    "red-team-argument, summarize-for-recall). GitHub issue #1391."
)
_KNOWN_BUGS: dict[str, str] = {
    "check-falsifiability": _PROMPT_STAGING_GITIGNORE_BUG,
    # Task 7b-1: registered alongside check-falsifiability's Task-6 finding
    # — same root cause, confirmed live against a real seeded vault (see
    # task-7b1-report.md), not assumed by analogy alone.
    "analyze-claims": _PROMPT_STAGING_GITIGNORE_BUG,
    "compare-and-contrast": _PROMPT_STAGING_GITIGNORE_BUG,
    "extract-claim-stubs": _PROMPT_STAGING_GITIGNORE_BUG,
    # Task 7b-2: the fifth of the six run_prompt_operation ids named in
    # #1391 — same root cause, confirmed live (see task-7b2-report.md).
    "red-team-argument": _PROMPT_STAGING_GITIGNORE_BUG,
    # Task 7b-2: the sixth and last of the six run_prompt_operation ids
    # named in #1391 — same root cause, confirmed live (see
    # task-7b2-report.md). #1391's full blast radius is now entirely
    # registered and xfailed.
    "summarize-for-recall": _PROMPT_STAGING_GITIGNORE_BUG,
    # Task 7b-2: a distinct, newly-found bug (not #1391). worker.py's
    # verify-project-draft dispatch branch (worker.py:680-699)
    # unconditionally reads `result["max_findings"]` and
    # `result["triaged_count"]` off knowledge.py:verify_project_draft's
    # return value, but that function's own "missing-draft" early return
    # (knowledge.py:2106-2117 — the case where the project has no draft.md
    # yet, the default state before compose-project-draft has ever run)
    # omits both keys, so the worker job crashes with `KeyError:
    # 'max_findings'` instead of completing "done" with
    # `verification_status: "missing-draft"`. Confirmed live against a real
    # seeded vault (see task-7b2-report.md). Not yet filed as a GitHub
    # issue (flagged for the controller in task-7b2-report.md).
    "verify-project-draft": (
        "knowledge.py:verify_project_draft's missing-draft early return "
        "(knowledge.py:2106-2117) omits max_findings/triaged_count, which "
        "worker.py's verify-project-draft dispatch branch "
        "(worker.py:680-699) reads unconditionally — every project without "
        "a draft.md yet (the default pre-compose state) crashes with "
        "KeyError: 'max_findings' instead of completing done with "
        "verification_status: 'missing-draft'."
    ),
    # Task 7b-2: a third distinct, newly-found bug (not #1391, not the
    # verify-project-draft KeyError above). write-project-slice itself
    # completes "done" and writes outline.md correctly — the bug is a side
    # effect on a DIFFERENT tracked projection. render_project_argument_
    # canvas (knowledge.py:1735-1743) branches on outline.md's mere
    # existence: with no outline.md it renders canvas nodes/edges from
    # analyze_project_argument's full graph traversal; once outline.md
    # exists it renders from the BM25-ranked project slice instead (a
    # different, order-dependent node/edge set). check_tracked_projections
    # (projections.py:56-78) — the floor's own tracked-projection drift
    # detector, asserted after every operation via assert_invariants — calls
    # this same render function as its "live" canonical renderer. So any
    # project whose argument.canvas was already rendered (via
    # render-project-argument-canvas, e.g. during typed-graph seeding)
    # *before* its first write-project-slice run is retroactively flagged
    # "stale" the moment outline.md appears, even though write-project-slice
    # never touches, recommits, or is documented to invalidate the canvas
    # file. Confirmed live: assert_invariants' check_tracked_projections
    # reports `{"path": "projects/package-gate/argument.canvas", "status":
    # "stale"}` immediately after a real write-project-slice run against the
    # seed. Not yet filed as a GitHub issue (flagged for the controller in
    # task-7b2-report.md).
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
