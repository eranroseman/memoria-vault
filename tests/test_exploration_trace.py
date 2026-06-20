"""ADR-100 exploration-trace capture contracts."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "src" / ".memoria" / "profiles" / "memoria-librarian" / "skills"
METHODS = SKILLS / "map-cluster-corpus" / "references" / "methods.md"


def test_scope_and_gap_reports_define_companion_trace_artifact():
    for skill in ("map-scope-project", "map-report-coverage"):
        text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
        for marker in (
            "exploration-trace",
            "notes/fleeting/maps/",
            "type: fleeting",
            "lifecycle: proposed",
            "origin: agent",
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
        "notes/fleeting/maps/",
        "project-local map context",
        "not canonical knowledge",
        "never auto-promoted into claims, sources, hubs, or project state",
    ):
        assert marker in text
