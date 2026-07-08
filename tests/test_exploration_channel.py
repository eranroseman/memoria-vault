from __future__ import annotations

import json
from pathlib import Path

from memoria_vault.cli import main
from memoria_vault.engine import api
from memoria_vault.runtime import state
from memoria_vault.runtime.knowledge import exploration_channel
from memoria_vault.runtime.policy.audit import sha256_file


def test_exploration_channel_surfaces_uncaptured_citation_candidate(tmp_path: Path) -> None:
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
    _checked_note(
        tmp_path,
        "notes/contrary.md",
        "type: note\ntitle: Contrary\ncontradictions:\n  - notes/thesis.md\n",
    )

    result = exploration_channel(tmp_path)

    assert result["mode"] == "mmr-baseline"
    assert result["relevance_independent"] is True
    assert result["empty"] is False
    assert result["items"] == [
        {
            "work_id": "source-alpha",
            "source_title": "Alpha",
            "candidate_work_id": "https://openalex.org/W999",
            "candidate_title": "Uncaptured Work",
            "candidate_doi": "10.1000/uncaptured",
            "relation_type": "references",
            "provider": "openalex",
            "why": (
                "Coverage candidate: checked source `source-alpha` references uncaptured "
                "work `https://openalex.org/W999`."
            ),
        }
    ]
    assert result["contrary_items"] == [
        {
            "path": "notes/contrary.md",
            "title": "Contrary",
            "target": "notes/thesis.md",
            "why": (
                "Contrary channel: checked concept `notes/contrary.md` declares "
                "contradiction `notes/thesis.md`."
            ),
        }
    ]


def test_exploration_channel_honestly_returns_empty_without_candidates(
    tmp_path: Path,
) -> None:
    state.upsert_catalog_record(
        tmp_path,
        work_id="source-alpha",
        title="Alpha",
        check_status="checked",
    )

    result = exploration_channel(tmp_path)
    readback = api.read_exploration(tmp_path)

    assert result["empty"] is True
    assert result["items"] == []
    assert result["contrary_items"] == []
    assert readback["exploration"]["empty"] is True


def test_exploration_channel_surfaces_nli_refuted_contrary_candidate(
    tmp_path: Path,
) -> None:
    _checked_note(
        tmp_path,
        "notes/left.md",
        "type: note\ntitle: Left\n",
        body="Reminder systems improve memory recall when cues are present.",
    )
    _checked_note(
        tmp_path,
        "notes/right.md",
        "type: note\ntitle: Right\n",
        body="Reminder systems do not improve memory recall when cues are present.",
    )

    result = exploration_channel(tmp_path)

    assert result["empty"] is False
    assert result["contrary_items"] == [
        {
            "path": "notes/left.md",
            "title": "Left",
            "target": "notes/right.md",
            "why": (
                "Contrary channel: NLI REFUTED candidate between `notes/left.md` "
                "and `notes/right.md` (high lexical overlap with opposite negation)."
            ),
        }
    ]


def test_cli_project_explore_returns_channel(tmp_path: Path, capsys: object) -> None:
    state.upsert_catalog_record(
        tmp_path,
        work_id="source-alpha",
        title="Alpha",
        check_status="checked",
    )

    rc = main(["project", "explore", "--workspace", str(tmp_path), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["exploration"]["mode"] == "mmr-baseline"


def _checked_note(vault: Path, rel: str, frontmatter: str, *, body: str = "Body.") -> None:
    path = vault / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\n{body}\n", encoding="utf-8")
    state.record_observed_file_edit(
        vault,
        output_id=rel,
        concept_type="note",
        output_sha256=sha256_file(path),
    )
    state.set_concept_verdict(vault, rel, "checked")
