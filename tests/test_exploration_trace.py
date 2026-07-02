"""Exploration-trace capture contracts."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OPERATIONS = ROOT / "vault-template" / "capabilities" / "operations"


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
