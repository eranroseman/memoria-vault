"""Filtered qmd wrapper applies the alpha.11 checked-only read barrier."""

from pathlib import Path

import qmd_filter_mcp as qmd


def _note(vault: Path, name: str, status: str = "checked") -> str:
    path = vault / "knowledge" / "notes" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\ntype: note\ncheck_status: {status}\ntitle: {name}\n---\n# {name}\n",
        encoding="utf-8",
    )
    return f"qmd://vault/knowledge/notes/{name}.md"


def test_unchecked_results_are_filtered_by_default(tmp_path):
    live = _note(tmp_path, "live")
    unchecked = _note(tmp_path, "unchecked", "unchecked")
    quarantined = _note(tmp_path, "quarantined", "quarantined")
    rows = [
        {"file": unchecked, "title": "Unchecked"},
        {"file": live, "title": "Live"},
        {"file": quarantined, "title": "Quarantined"},
    ]

    filtered = qmd.filter_results(tmp_path, rows)

    assert [row["title"] for row in filtered] == ["Live"]


def test_checked_concept_detection_handles_missing_and_unchecked(tmp_path):
    checked = _note(tmp_path, "checked")
    unchecked = _note(tmp_path, "unchecked", "unchecked")

    assert qmd.is_checked_concept(tmp_path, qmd.qmd_result_path(checked, tmp_path))
    assert not qmd.is_checked_concept(tmp_path, qmd.qmd_result_path(unchecked, tmp_path))
    assert not qmd.is_checked_concept(tmp_path, "knowledge/notes/missing.md")
