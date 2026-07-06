"""Exploration-trace capture contracts."""

from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.capabilities import DEFAULT_RUNNER_POLICY, read_capability_manifest
from memoria_vault.runtime.knowledge import exploration_channel
from memoria_vault.runtime.vaultio import read_frontmatter

ROOT = Path(__file__).resolve().parent.parent
OPERATIONS = ROOT / "src/memoria_vault/product/capabilities/operations"


def test_gap_and_project_argument_operations_are_read_only_capabilities() -> None:
    for operation in ("analyze-gaps", "analyze-project-argument"):
        path = OPERATIONS / f"{operation}.md"
        text = path.read_text(encoding="utf-8")
        raw_fm = read_frontmatter(path)
        fm = read_capability_manifest("operation", operation)["frontmatter"]
        assert fm["type"] == "operation"
        assert "check_status" not in fm
        assert "standing" not in fm
        assert fm["operation_id"] == operation
        assert fm["allowed_tools"] == ["read_checked_concepts"]
        assert "runner" not in raw_fm
        assert fm["runner"] == DEFAULT_RUNNER_POLICY
        assert "write" not in text.lower()


def test_exploration_channel_items_carry_traceable_why(tmp_path: Path) -> None:
    state.upsert_catalog_record(
        tmp_path,
        source_id="source-alpha",
        title="Alpha",
        check_status="checked",
    )
    state.replace_work_graph_edges(
        tmp_path,
        "source-alpha",
        [
            {
                "relation_type": "references",
                "target_id": "https://openalex.org/W999",
                "target_title": "Uncaptured Work",
                "target_doi": "10.1000/uncaptured",
                "source_provider": "openalex",
            }
        ],
    )

    result = exploration_channel(tmp_path)

    assert result["items"][0]["why"] == (
        "Coverage candidate: checked source `source-alpha` references uncaptured "
        "work `https://openalex.org/W999`."
    )
