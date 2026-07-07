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
    "test_alpha11_cycle.py": "runtime",
    "test_alpha12_state.py": "runtime",
    "test_alpha13_enrichment.py": "runtime",
    "test_alpha15_runtime_gate.py": "runtime",
    "test_alpha15_dogfood_checkpoint.py": "runtime",
    "test_alpha17_draft_compose.py": "runtime",
    "test_alpha17_evidence_markers.py": "unit",
    "test_alpha17_evidence_sets.py": "runtime",
    "test_alpha17_exploration.py": "runtime",
    "test_alpha17_gate_calibration.py": "unit",
    "test_alpha17_slice_outline.py": "runtime",
    "test_alpha17_verification.py": "runtime",
    "test_alpha17_writeback.py": "runtime",
    "test_alpha18_bundle_roots.py": "contract",
    "test_alpha18_concept_types.py": "contract",
    "test_alpha18_frontmatter.py": "contract",
    "test_alpha18_gap_freejoin.py": "contract",
    "test_alpha18_renames.py": "contract",
    "test_alpha18_schema_doc_lint.py": "static",
    "test_alpha18_schema_version.py": "contract",
    "test_alpha19_code_lane.py": "runtime",
    "test_alpha19_query_substrate.py": "contract",
    "test_bases.py": "contract",
    "test_capabilities.py": "contract",
    "test_capture.py": "contract",
    "test_cli.py": "contract",
    "test_cspell_scope.py": "static",
    "test_detectors.py": "static",
    "test_diagnostics.py": "unit",
    "test_docs_doctor.py": "static",
    "test_e2e_smoke_helpers.py": "package",
    "test_eval.py": "contract",
    "test_engine_api.py": "contract",
    "test_eval_score.py": "contract",
    "test_exploration_trace.py": "contract",
    "test_github_doctor.py": "static",
    "test_hub_handoff.py": "contract",
    "test_http_transport.py": "contract",
    "test_inbox_cards.py": "contract",
    "test_mcp_transport.py": "contract",
    "test_installer_skeleton.py": "package",
    "test_install_test_vault_local_llm.py": "package",
    "test_integrity.py": "runtime",
    "test_knowledge.py": "runtime",
    "test_live_runner.py": "live",
    "test_live_docs_links.py": "static",
    "test_loudness.py": "unit",
    "test_node_tooling.py": "static",
    "test_operations.py": "contract",
    "test_parity_fixture.py": "contract",
    "test_package_spine.py": "package",
    "test_patterns.py": "contract",
    "test_plugin_provenance.py": "static",
    "test_policy_gate_completeness.py": "contract",
    "test_policy_gate_plugin.py": "contract",
    "test_policy_hook.py": "contract",
    "test_pr_policy.py": "static",
    "test_precommit_schema.py": "static",
    "test_profiles.py": "contract",
    "test_project_structural_impact.py": "contract",
    "test_projections.py": "contract",
    "test_refresh_test_vault.py": "package",
    "test_retrieval_substrate.py": "contract",
    "test_ruleset_doctor.py": "static",
    "test_runtime_helpers.py": "unit",
    "test_runtime_policy.py": "contract",
    "test_sample_vault.py": "package",
    "test_schemas.py": "contract",
    "test_search_index.py": "contract",
    "test_seeded_errors.py": "runtime",
    "test_session_summary.py": "contract",
    "test_status_doctor.py": "static",
    "test_sweeps_retraction.py": "contract",
    "test_templates.py": "contract",
    "test_test_env_harness.py": "package",
    "test_testing_levels.py": "static",
    "test_trusted_writer.py": "runtime",
    "test_verify_script.py": "package",
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
