"""Exploration-trace capture contracts."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OPERATIONS = ROOT / "vault-template" / "capabilities" / "operations"
TRACE_SCRIPT = ROOT / "vault-template" / "system" / "scripts" / "record-exploration-trace.js"


def test_gap_and_project_argument_operations_are_read_only_checked_capabilities() -> None:
    for operation in ("analyze-gaps", "analyze-project-argument"):
        text = (OPERATIONS / f"{operation}.md").read_text(encoding="utf-8")
        for marker in (
            "type: operation",
            "check_status: checked",
            f"operation_id: {operation}",
            "allowed_tools:",
            "  - read_checked_concepts",
            "runner: pydantic-ai",
        ):
            assert marker in text, f"{operation} missing {marker!r}"
        assert "write" not in text.lower()


def test_record_exploration_trace_creates_unchecked_project_local_note() -> None:
    text = TRACE_SCRIPT.read_text(encoding="utf-8")
    for marker in (
        "knowledge/notes/maps/",
        "-exploration-trace-",
        "type: note",
        "check_status: unchecked",
        "Rejected direction",
        "Why rejected",
        "Evidence checked",
        "Retry only if",
        "project-local exploration context",
        "never adopted automatically into curated knowledge",
    ):
        assert marker in text


def test_record_exploration_trace_only_attaches_to_map_reports() -> None:
    text = TRACE_SCRIPT.read_text(encoding="utf-8")
    for marker in (
        "corpus-map-",
        "gap-report-",
        "cluster-map-",
        "Choose a report under",
    ):
        assert marker in text
