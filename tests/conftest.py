"""Pytest isolation for tests that create disposable git repositories."""

from __future__ import annotations

import os

import pytest

GIT_ENV_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_PREFIX",
)

TEST_LEVEL_NAMES = frozenset({"static", "unit", "contract", "package", "runtime", "live"})

TEST_LEVELS = {
    "test_agents_doctor.py": "static",
    "test_bases.py": "contract",
    "test_bundle_roots.py": "contract",
    "test_capabilities.py": "contract",
    "test_capture.py": "contract",
    "test_cli.py": "contract",
    "test_cli_doctor_eval.py": "contract",
    "test_cli_work_project.py": "contract",
    "test_cli_workspace_requests.py": "contract",
    "test_code_artifacts.py": "runtime",
    "test_concept_types.py": "contract",
    "test_cspell_scope.py": "static",
    "test_detectors.py": "static",
    "test_diagnostics.py": "unit",
    "test_docs_doctor.py": "static",
    "test_draft_compose.py": "runtime",
    "test_draft_verification.py": "runtime",
    "test_draft_writeback.py": "runtime",
    "test_e2e_smoke_helpers.py": "package",
    "test_eval.py": "contract",
    "test_empirical_events.py": "contract",
    "test_engine_api.py": "contract",
    "test_eval_score.py": "contract",
    "test_evidence_markers.py": "unit",
    "test_evidence_sets.py": "runtime",
    "test_exploration_channel.py": "runtime",
    "test_exploration_trace.py": "contract",
    "test_frontmatter_contract.py": "contract",
    "test_gap_analysis.py": "runtime",
    "test_gap_freejoin.py": "contract",
    "test_gate_calibration.py": "unit",
    "test_github_doctor.py": "static",
    "test_hub_handoff.py": "contract",
    "test_identifier_renames.py": "contract",
    "test_http_transport.py": "contract",
    "test_inbox_cards.py": "contract",
    "test_mcp_transport.py": "contract",
    "test_memoria_obsidian_package.py": "contract",
    "test_installer_skeleton.py": "package",
    "test_install_test_vault_local_llm.py": "package",
    "test_integrity.py": "runtime",
    "test_integrity_cascade_rollback.py": "runtime",
    "test_integrity_source_metadata.py": "runtime",
    "test_integrity_surface_tensions.py": "runtime",
    "test_knowledge.py": "runtime",
    "test_live_runner.py": "live",
    "test_loudness.py": "unit",
    "test_node_tooling.py": "static",
    "test_operations.py": "contract",
    "test_parity_fixture.py": "contract",
    "test_package_spine.py": "package",
    "test_patterns.py": "contract",
    "test_plugin_provenance.py": "static",
    "test_policy_gate_completeness.py": "contract",
    "test_policy_hook.py": "contract",
    "test_pr_policy.py": "static",
    "test_precommit_schema.py": "static",
    "test_profiles.py": "contract",
    "test_project_knowledge.py": "runtime",
    "test_removed_surface_gate.py": "static",
    "test_project_structural_impact.py": "contract",
    "test_projections.py": "contract",
    "test_query_substrate.py": "contract",
    "test_refresh_test_vault.py": "package",
    "test_retrieval_substrate.py": "contract",
    "test_runtime_gate_replay.py": "runtime",
    "test_ruleset_doctor.py": "static",
    "test_runtime_helpers.py": "unit",
    "test_runtime_policy.py": "contract",
    "test_runtime_state.py": "runtime",
    "test_sample_vault.py": "package",
    "test_schema_doc_drift.py": "static",
    "test_schema_version.py": "contract",
    "test_schemas.py": "contract",
    "test_search_index.py": "contract",
    "test_seeded_errors.py": "runtime",
    "test_session_summary.py": "contract",
    "test_slice_outline.py": "runtime",
    "test_source_enrichment.py": "runtime",
    "test_status_doctor.py": "static",
    "test_surface_contract.py": "contract",
    "test_sweeps_retraction.py": "contract",
    "test_test_env_harness.py": "package",
    "test_testing_levels.py": "static",
    "test_trusted_writer.py": "runtime",
    "test_verify_script.py": "package",
    "test_worker_capture_jobs.py": "runtime",
    "test_worker_integrity_jobs.py": "runtime",
    "test_worker_knowledge_cycle.py": "runtime",
    "test_worker_product_jobs.py": "runtime",
    "test_worker_queue.py": "runtime",
    "test_worklists.py": "contract",
}


def pytest_configure() -> None:
    for key in GIT_ENV_VARS:
        os.environ.pop(key, None)
    os.environ.setdefault("PRE_COMMIT_ALLOW_NO_CONFIG", "1")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        level = TEST_LEVELS.get(item.path.name)
        if level:
            item.add_marker(getattr(pytest.mark, level))
