from __future__ import annotations

import json
import tomllib
from pathlib import Path

from memoria_vault.runtime.retrieval_substrate import (
    RETRIEVAL_SUBSTRATE_VERDICT,
    SELECTED_RETRIEVAL_SUBSTRATE,
    evaluate_fts5_fixture,
)
from memoria_vault.runtime.search_index import rebuild_checked_search_index
from tests.helpers import ROOT, copy_memoria_dirs

FIXTURE = ROOT / "tests/fixtures/retrieval-substrate-spike.json"


def test_alpha15_retrieval_substrate_verdict_is_committed() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert fixture["verdict"]["selected"] == "bm25"
    assert fixture["verdict"]["cleared_replacement_bar"] is False
    assert SELECTED_RETRIEVAL_SUBSTRATE == fixture["verdict"]["selected"]
    assert RETRIEVAL_SUBSTRATE_VERDICT["selected"] == fixture["verdict"]["selected"]
    assert RETRIEVAL_SUBSTRATE_VERDICT["cleared_replacement_bar"] is False


def test_sqlite_fts5_fixture_keeps_semantic_gap_visible() -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    result = evaluate_fts5_fixture(fixture)

    assert result["available"] is True
    assert result["recall_by_slice"]["keyword"] == 1.0
    assert result["recall_by_slice"]["semantic"] < fixture["target_recall_by_slice"]["semantic"]
    assert result["recall_by_slice"]["hybrid"] < fixture["target_recall_by_slice"]["hybrid"]


def test_packaged_search_has_no_vector_dependency() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = {
        dependency.split("[", 1)[0].split(">=", 1)[0].split("==", 1)[0]
        for dependency in pyproject["project"]["dependencies"]
    }
    installer = (ROOT / "scripts/install.sh").read_text(encoding="utf-8")

    assert SELECTED_RETRIEVAL_SUBSTRATE == "bm25"
    vector_dependencies = {"sentence-transformers", "sqlite-vec", "sqlite_vec"}
    assert dependencies.isdisjoint(vector_dependencies)
    assert all(name not in installer for name in vector_dependencies)


def test_bm25_verdict_matches_rebuild_manifest(tmp_path: Path) -> None:
    copy_memoria_dirs(tmp_path, "schemas")
    note = tmp_path / "knowledge/notes/checked.md"
    note.parent.mkdir(parents=True)
    note.write_text(
        "---\ntype: note\ncheck_status: checked\ntitle: checked\n---\nalpha\n",
        encoding="utf-8",
    )

    manifest = rebuild_checked_search_index(tmp_path)

    assert SELECTED_RETRIEVAL_SUBSTRATE == "bm25"
    assert manifest["backend"] == SELECTED_RETRIEVAL_SUBSTRATE
