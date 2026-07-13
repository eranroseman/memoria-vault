"""Analyze-gaps free-join contract tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from memoria_vault.runtime import state
from memoria_vault.runtime.knowledge import analyze_gaps as _analyze_gaps
from tests.helpers import call_with_context


def analyze_gaps(vault: Path, *args, **kwargs):
    return call_with_context(_analyze_gaps, vault, *args, **kwargs)


@pytest.mark.parametrize(
    ("relation_type", "target_id", "target_title"),
    [
        ("authorship", "https://openalex.org/A1", "Ada Researcher"),
        ("institution", "https://openalex.org/I1", "Example Institute"),
        ("published_in", "https://openalex.org/S1", "Journal of Examples"),
    ],
)
def test_analyze_gaps_surfaces_shared_entity_freejoin(
    tmp_path: Path,
    relation_type: str,
    target_id: str,
    target_title: str,
) -> None:
    for work_id, title, standing in (
        ("source-alpha", "Alpha Source", ""),
        ("source-beta", "Beta Source", ""),
        ("source-archived", "Archived Source", "archived"),
    ):
        memoria = {"standing": standing} if standing else {}
        state.upsert_catalog_record(
            tmp_path,
            work_id=work_id,
            title=title,
            text_status="full-text",
            check_status="checked",
            csl_json={"memoria": memoria},
        )
        state.replace_work_graph_edges(
            tmp_path,
            work_id,
            [
                {
                    "relation_type": relation_type,
                    "target_id": target_id,
                    "target_title": target_title,
                    "source_provider": "openalex",
                }
            ],
        )

    result = analyze_gaps(tmp_path)

    gap = {row["topic"]: row for row in result["gaps"]}[target_title]
    assert gap["gap_type"] == "undigested"
    assert gap["source_count"] == 2
    assert gap["digest_count"] == 0
    assert gap["note_count"] == 0
    assert gap["work_ids"] == ["source-alpha", "source-beta"]
