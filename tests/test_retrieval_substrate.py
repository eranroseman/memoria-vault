from __future__ import annotations

import tomllib
from pathlib import Path

from memoria_vault.runtime import state
from memoria_vault.runtime.knowledge import exploration_channel
from memoria_vault.runtime.search_index import (
    rebuild_checked_search_index as _rebuild_checked_search_index,
)
from tests.helpers import ROOT, call_with_context, copy_memoria_dirs


def rebuild_checked_search_index(vault: Path, *args, **kwargs):
    return call_with_context(_rebuild_checked_search_index, vault, *args, **kwargs)


def test_packaged_search_has_no_vector_dependency() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = {
        dependency.split("[", 1)[0].split(">=", 1)[0].split("==", 1)[0]
        for dependency in pyproject["project"]["dependencies"]
    }
    installer = (ROOT / "scripts/install.sh").read_text(encoding="utf-8")

    vector_dependencies = {"sentence-transformers", "sqlite-vec", "sqlite_vec"}
    assert dependencies.isdisjoint(vector_dependencies)
    assert all(name not in installer for name in vector_dependencies)


def test_bm25_verdict_matches_rebuild_manifest(tmp_path: Path) -> None:
    copy_memoria_dirs(tmp_path, "schemas")
    note = tmp_path / "notes/checked.md"
    note.parent.mkdir(parents=True)
    note.write_text(
        "---\ntype: note\ncheck_status: checked\ntitle: checked\n---\nalpha\n",
        encoding="utf-8",
    )

    manifest = rebuild_checked_search_index(tmp_path)

    assert manifest["backend"] == "bm25"


def test_exploration_channel_keeps_relevance_substrate_independent(tmp_path: Path) -> None:
    state.upsert_catalog_record(
        tmp_path,
        work_id="source-alpha",
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

    assert result["mode"] == "mmr-baseline"
    assert result["relevance_independent"] is True
