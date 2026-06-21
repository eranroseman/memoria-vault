"""Filtered qmd wrapper hides superseded claims by default (ADR-10)."""

from pathlib import Path

import qmd_filter_mcp as qmd


def _claim(vault: Path, name: str, superseded_by: str = "") -> str:
    path = vault / "notes" / "claims" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "type: claim\n"
        "lifecycle: current\n"
        "maturity: seedling\n"
        f"superseded_by: {superseded_by}\n"
        "---\n"
        f"# {name}\n",
        encoding="utf-8",
    )
    return f"qmd://vault/notes/claims/{name}.md"


def test_superseded_claims_are_filtered_by_default(tmp_path):
    live = _claim(tmp_path, "live")
    old = _claim(tmp_path, "old", "[[live]]")
    rows = [
        {"file": old, "title": "Old"},
        {"file": live, "title": "Live"},
        {"file": "qmd://vault/catalog/papers/source.md", "title": "Source"},
    ]

    filtered = qmd.filter_results(tmp_path, rows)

    assert [row["title"] for row in filtered] == ["Live", "Source"]
    assert qmd.filter_results(tmp_path, rows, include_superseded=True) == rows


def test_get_blocks_superseded_claim_without_explicit_history(tmp_path):
    old = _claim(tmp_path, "old", "[[new]]")

    assert qmd.is_superseded_claim(tmp_path, old)
    assert not qmd.is_superseded_claim(tmp_path, "qmd://vault/notes/claims/missing.md")
