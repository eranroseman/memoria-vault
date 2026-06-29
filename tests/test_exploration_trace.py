"""ADR-100 exploration-trace capture contracts."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "vault-template" / ".memoria" / "profiles" / "memoria-librarian" / "skills"
METHODS = SKILLS / "map-cluster-corpus" / "references" / "methods.md"


def test_scope_and_gap_reports_define_companion_trace_artifact():
    for skill in ("map-scope-project", "map-report-coverage"):
        text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
        for marker in (
            "exploration-trace",
            "knowledge/notes/maps/",
            "type: note",
            "check_status: unchecked",
            "direction",
            "why_rejected",
            "evidence_checked",
            "retry_only_if",
            "never auto-promoted",
        ):
            assert marker in text, f"{skill} missing {marker!r}"
        assert "notes/claims/" not in text
        assert "notes/hubs/" not in text


def test_map_methods_keep_exploration_trace_project_local():
    text = METHODS.read_text(encoding="utf-8")
    for marker in (
        "Exploration trace companion",
        "*-exploration-trace.md",
        "knowledge/notes/maps/",
        "project-local map context",
        "not canonical knowledge",
        "never auto-promoted into sources, digests, hubs, or project state",
    ):
        assert marker in text


def test_cluster_map_candidate_surfaces_in_inbox():
    text = (SKILLS / "map-cluster-corpus" / "SKILL.md").read_text(encoding="utf-8")
    for marker in (
        "type: candidate",
        "lifecycle: proposed",
        '`action` = "read this cluster',
    ):
        assert marker in text


def test_too_small_cluster_map_blocks_for_board_export_gap():
    text = (SKILLS / "map-cluster-corpus" / "SKILL.md").read_text(encoding="utf-8")
    for marker in (
        "too few documents",
        "kanban_block",
        "current and required source counts",
        "`board_export.py` owns the `gap` card",
        "Do not `kanban_complete`",
    ):
        assert marker in text
