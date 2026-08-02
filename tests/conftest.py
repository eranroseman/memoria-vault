"""Pytest isolation for tests that create disposable git repositories."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# Room for the temp vaults. A full run peaks near 0.8 GB and pytest retains the
# last three basetemp trees, so 4 GB leaves comfortable headroom.
TMPFS_MIN_FREE_BYTES = 4 * 1024**3

GIT_ENV_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_PREFIX",
)

TEST_LEVEL_NAMES = frozenset({"static", "unit", "contract", "package", "runtime", "live", "floor"})

TEST_LEVELS = {
    "test_operation_context.py": "runtime",
    "test_agent_bundle.py": "contract",
    "test_attention_lifecycle.py": "contract",
    "test_attention_view.py": "contract",
    "test_bases.py": "contract",
    "test_backup_restore.py": "runtime",
    "test_bulk_import.py": "contract",
    "test_bundle_roots.py": "contract",
    "test_capabilities.py": "contract",
    "test_capture.py": "contract",
    "test_cli.py": "contract",
    "test_cli_honesty.py": "contract",
    "test_cli_doctor_eval.py": "contract",
    "test_cli_work_project.py": "contract",
    "test_cli_review.py": "contract",
    "test_cli_workspace_requests.py": "contract",
    "test_cockpit.py": "contract",
    "test_cockpit_trace.py": "runtime",
    "test_cli_secrets.py": "contract",
    "test_code_artifacts.py": "runtime",
    "test_concept_type_registry.py": "contract",
    "test_concept_types.py": "contract",
    "test_content_security.py": "runtime",
    "test_context_read.py": "contract",
    "test_copi_conversational_ask.py": "contract",
    "test_cspell_scope.py": "static",
    "test_dashboard_view.py": "contract",
    "test_detectors.py": "static",
    "test_diagnostics.py": "unit",
    "test_doc_claims_gate.py": "static",
    "test_draft_compose.py": "runtime",
    "test_draft_verification.py": "runtime",
    "test_draft_writeback.py": "runtime",
    "test_e2e_smoke_helpers.py": "package",
    "test_edges.py": "unit",
    "test_eval.py": "contract",
    "test_empirical_events.py": "contract",
    "test_review_telemetry.py": "contract",
    "test_engine_api.py": "contract",
    "test_eval_score.py": "contract",
    "test_evidence_markers.py": "unit",
    "test_evidence_review_queue.py": "unit",
    "test_evidence_review_view.py": "contract",
    "test_evidence_sets.py": "runtime",
    "test_explore.py": "contract",
    "test_exploration_channel.py": "runtime",
    "test_exploration_trace.py": "contract",
    "test_export_acceptance.py": "runtime",
    "test_feedback_instrumentation.py": "contract",
    "test_floor_coverage.py": "floor",
    "test_floor_invariants.py": "floor",
    "test_floor_seed.py": "floor",
    "test_floor_sweep_operations.py": "floor",
    "test_floor_sweep_reads.py": "floor",
    "test_floor_transports.py": "floor",
    "test_frontmatter_contract.py": "contract",
    "test_gap_analysis.py": "runtime",
    "test_gap_freejoin.py": "contract",
    "test_gate_calibration.py": "unit",
    "test_grounded_synthesis.py": "contract",
    "test_graph_sql.py": "contract",
    "test_hub_candidates.py": "contract",
    "test_hub_handoff.py": "contract",
    "test_identifier_renames.py": "contract",
    "test_http_transport.py": "contract",
    "test_inbox_cards.py": "contract",
    "test_mcp_transport.py": "contract",
    "test_memoria_obsidian_package.py": "contract",
    "test_mc_hash_binding.py": "runtime",
    "test_installer_skeleton.py": "package",
    "test_install_test_vault_local_llm.py": "package",
    "test_integrity.py": "runtime",
    "test_integrity_cascade_rollback.py": "runtime",
    "test_integrity_source_metadata.py": "runtime",
    "test_integrity_surface_tensions.py": "runtime",
    "test_journal_trust.py": "runtime",
    "test_knowledge.py": "runtime",
    "test_live_runner.py": "live",
    "test_loudness.py": "unit",
    "test_node_tooling.py": "static",
    "test_onboarding.py": "unit",
    "test_onboarding_steps.py": "contract",
    "test_operations.py": "contract",
    "test_parity_fixture.py": "contract",
    "test_package_spine.py": "package",
    "test_patterns.py": "contract",
    "test_plugin_provenance.py": "static",
    "test_policy_gate_completeness.py": "contract",
    "test_policy_hook.py": "contract",
    "test_precommit_schema.py": "static",
    "test_profiles.py": "contract",
    "test_project_knowledge.py": "runtime",
    "test_removed_surface_gate.py": "static",
    "test_project_structural_impact.py": "contract",
    "test_projections.py": "contract",
    "test_propagation.py": "runtime",
    "test_propagation_engine.py": "runtime",
    "test_query_substrate.py": "contract",
    "test_read_api_auth_walk.py": "contract",
    "test_read_api_scope_walk.py": "floor",
    "test_refresh_test_vault.py": "package",
    "test_retrieval_fixtures.py": "contract",
    "test_rendezvous.py": "runtime",
    "test_retrieval_pipeline.py": "unit",
    "test_retrieval_substrate.py": "contract",
    "test_runtime_gate_replay.py": "runtime",
    "test_runtime_helpers.py": "unit",
    "test_runtime_policy.py": "contract",
    "test_revert_preview.py": "runtime",
    "test_runtime_state.py": "runtime",
    "test_sample_vault.py": "package",
    "test_schema_doc_drift.py": "static",
    "test_schema_v10.py": "unit",
    "test_schema_v16_identity.py": "contract",
    "test_schema_version.py": "contract",
    "test_schemas.py": "contract",
    "test_search_index.py": "contract",
    "test_seed_lifecycle.py": "contract",
    "test_seed_manifest.py": "contract",
    "test_seed_install.py": "contract",
    "test_seeded_errors.py": "runtime",
    "test_secrets.py": "unit",
    "test_session_summary.py": "contract",
    "test_slice_outline.py": "runtime",
    "test_source_enrichment.py": "runtime",
    "test_steering_tokens.py": "contract",
    "test_surface_contract.py": "contract",
    "test_sweeps_retraction.py": "contract",
    "test_telemetry_events.py": "contract",
    "test_telemetry_read_paths.py": "runtime",
    "test_test_env_harness.py": "package",
    "test_testing_levels.py": "static",
    "test_tmpfs_tmpdir.py": "static",
    "test_token_ceiling.py": "unit",
    "test_trusted_writer.py": "runtime",
    "test_vaultio.py": "unit",
    "test_verify_script.py": "static",
    "test_workspace_seed_links.py": "static",
    "test_worker_capture_jobs.py": "runtime",
    "test_worker_integrity_jobs.py": "runtime",
    "test_worker_knowledge_cycle.py": "runtime",
    "test_worker_product_jobs.py": "runtime",
    "test_worker_queue.py": "runtime",
    "test_worklists.py": "contract",
}


def _tmpfs_tmpdir(candidate: Path = Path("/dev/shm")) -> str | None:
    """Where the temp vaults should live, or None to leave TMPDIR alone.

    Every vault write in a test is a real `git commit` plus a
    `PRAGMA synchronous = FULL` sqlite write, so the suite is fsync-bound rather
    than CPU-bound. On WSL2 (ext4 on a VHDX) the fsyncs cost more wall time than
    all the actual work: the same run is ~706s of CPU either way, but 443s wall
    on disk against 89s on tmpfs. Nothing asserted changes -- a disposable
    per-test vault never needed the durability those fsyncs buy.

    This lives in conftest rather than in scripts/verify so that every entry
    point gets it. An IDE test runner and a bare `pytest` are the local loop
    just as much as the gate is, and they were paying full price.

    CI keeps the real filesystem on purpose: it is the authoritative gate, and
    the one place this durability should be exercised against a real disk. An
    explicit TMPDIR always wins, so this stays overridable.
    """
    if os.environ.get("CI") or "TMPDIR" in os.environ:
        return None
    # /dev/shm is tmpfs on every Linux distro and absent elsewhere, so its
    # writability is the whole platform check.
    if not os.access(candidate, os.W_OK):
        return None
    stats = os.statvfs(candidate)
    if stats.f_bavail * stats.f_frsize < TMPFS_MIN_FREE_BYTES:
        return None
    return str(candidate)


_TMPDIR = _tmpfs_tmpdir()
if _TMPDIR:
    # Set at import, which is before pytest resolves a basetemp. tempfile caches
    # the first gettempdir() result, so drop it or the stale value would win.
    os.environ["TMPDIR"] = _TMPDIR
    tempfile.tempdir = None


def pytest_configure() -> None:
    for key in GIT_ENV_VARS:
        os.environ.pop(key, None)
    os.environ.setdefault("PRE_COMMIT_ALLOW_NO_CONFIG", "1")
    # Secrets hermeticity: never read the developer's ~/.config/memoria/secrets.env.
    os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp(prefix="memoria-test-xdg-")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        level = TEST_LEVELS.get(item.path.name)
        if level:
            item.add_marker(getattr(pytest.mark, level))


@pytest.fixture(autouse=True)
def _isolated_memoria_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """Keep per-vault rendezvous state out of the developer's real state dir."""
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path_factory.mktemp("memoria-state")))
    monkeypatch.delenv("MEMORIA_MODEL_TOKEN_CEILING", raising=False)
