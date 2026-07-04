"""Exploration-trace capture contracts."""

from pathlib import Path

from memoria_vault.runtime.vaultio import read_frontmatter

ROOT = Path(__file__).resolve().parent.parent
OPERATIONS = ROOT / "src/memoria_vault/product/capabilities/operations"


def test_gap_and_project_argument_operations_are_read_only_capabilities() -> None:
    for operation in ("analyze-gaps", "analyze-project-argument"):
        path = OPERATIONS / f"{operation}.md"
        text = path.read_text(encoding="utf-8")
        fm = read_frontmatter(path)
        assert fm["type"] == "operation"
        assert "check_status" not in fm
        assert "standing" not in fm
        assert fm["operation_id"] == operation
        assert fm["allowed_tools"] == ["read_checked_concepts"]
        assert fm["runner"] == {
            "test": {"provider": "local", "model": "deterministic-fixture", "temperature": 0},
            "live": {"provider": "gateway", "model": "deterministic-fixture", "temperature": 0},
        }
        assert "write" not in text.lower()
