"""Contract tests for the derived-steering unit (runtime/steering.py)."""

from __future__ import annotations

from pathlib import Path

from memoria_vault.runtime.steering import (
    RELEVANCE_STOPWORDS,
    effective_steering_provenance,
    effective_steering_tokens,
    relevance_tokens,
    steering_overrides,
)
from tests.helpers import WORKSPACE_SEED


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _concept(path: Path, frontmatter: str) -> None:
    _write(path, f"---\n{frontmatter}---\n\nBody.\n")


def test_relevance_tokens_casefold_stopword_short_and_digit_filters() -> None:
    tokens = relevance_tokens("The Spaced-Repetition MODEL", "v2", 2024, None, "")

    assert tokens == {"spaced", "repetition", "model"}
    assert {"the", "steering", "works"} <= RELEVANCE_STOPWORDS


def test_steering_overrides_reads_only_watch_and_muted_bullets(tmp_path: Path) -> None:
    _write(
        tmp_path / "steering.md",
        "---\ntype: system\ntitle: Steering\n---\n\n"
        "# Steering\n\n"
        "Prose about desirable difficulties never contributes.\n\n"
        "## Watch for\n\n"
        "> guidance blockquote is ignored\n\n"
        "- retrieval practice\n"
        "* interleaving\n\n"
        "## Muted\n\n"
        "- spaced repetition\n\n"
        "## Legacy section\n\n"
        "- ignored bullet\n",
    )

    watch, mute = steering_overrides(tmp_path)

    assert watch == {"retrieval", "practice", "interleaving"}
    assert mute == {"spaced", "repetition"}


def test_steering_overrides_without_file_is_empty(tmp_path: Path) -> None:
    assert steering_overrides(tmp_path) == (set(), set())


def test_effective_steering_unions_projects_hubs_questions_and_watch(tmp_path: Path) -> None:
    _concept(
        tmp_path / "projects/tutorial/project.md",
        "type: project\ntitle: Testing Effect\nthesis: Retrieval strengthens memory\n"
        "tags: [cognition]\nlinks: {}\n",
    )
    _concept(
        tmp_path / "hubs/note-taking.md",
        "type: hub\ntitle: Note Taking\ntag: note-taking\ntags: [handwriting]\nlinks: {}\n",
    )
    _concept(
        tmp_path / "notes/q-offloading.md",
        "type: note\nmode: question\nquestion_status: open\n"
        "title: Does offloading erode recall\ntags: []\nlinks: {}\n",
    )
    _write(
        tmp_path / "steering.md",
        "---\ntype: system\ntitle: Steering\n---\n\n## Watch for\n\n- interleaving\n\n## Muted\n",
    )

    tokens = effective_steering_tokens(tmp_path)

    assert tokens == {
        "testing",
        "effect",
        "retrieval",
        "strengthens",
        "memory",
        "cognition",
        "note",
        "taking",
        "handwriting",
        "does",
        "offloading",
        "erode",
        "recall",
        "interleaving",
    }


def test_effective_steering_excludes_archived_and_resolved_artifacts(tmp_path: Path) -> None:
    _concept(
        tmp_path / "projects/old/project.md",
        "type: project\ntitle: Abandoned Cartography\narchived: true\ntags: []\nlinks: {}\n",
    )
    _concept(
        tmp_path / "hubs/dormant.md",
        "type: hub\ntitle: Dormant Volcanoes\ntag: volcanoes\narchived: true\n"
        "tags: []\nlinks: {}\n",
    )
    _concept(
        tmp_path / "notes/q-settled.md",
        "type: note\nmode: question\nquestion_status: resolved\n"
        "title: Settled Wording\ntags: []\nlinks: {}\n",
    )
    _concept(
        tmp_path / "notes/claim.md",
        "type: note\nmode: claim\nclaim_text: x\ntitle: Claim Notes Excluded\n"
        "tags: []\nlinks: {}\n",
    )

    assert effective_steering_tokens(tmp_path) == set()


def test_effective_steering_subtracts_muted_tokens_per_word(tmp_path: Path) -> None:
    _concept(
        tmp_path / "projects/srs/project.md",
        "type: project\ntitle: Spaced Repetition Scheduling\ntags: []\nlinks: {}\n",
    )
    _write(
        tmp_path / "steering.md",
        "---\ntype: system\ntitle: Steering\n---\n\n"
        "## Watch for\n\n## Muted\n\n- spaced repetition\n",
    )

    assert effective_steering_tokens(tmp_path) == {"scheduling"}


def test_effective_steering_provenance_labels_every_source(tmp_path: Path) -> None:
    _concept(
        tmp_path / "projects/tutorial/project.md",
        "type: project\ntitle: Retrieval Practice\ntags: []\nlinks: {}\n",
    )
    _concept(
        tmp_path / "hubs/note-taking.md",
        "type: hub\ntitle: Note Taking\ntag: note-taking\ntags: []\nlinks: {}\n",
    )
    _concept(
        tmp_path / "notes/q-offloading.md",
        "type: note\nmode: question\nquestion_status: open\n"
        "title: Offloading Retrieval\ntags: []\nlinks: {}\n",
    )
    _write(
        tmp_path / "steering.md",
        "---\ntype: system\ntitle: Steering\n---\n\n"
        "## Watch for\n\n- interleaving\n\n## Muted\n\n- practice\n",
    )

    provenance = effective_steering_provenance(tmp_path)

    by_token = {row["token"]: row["sources"] for row in provenance}
    assert [row["token"] for row in provenance] == sorted(by_token)
    assert by_token["retrieval"] == [
        "project:projects/tutorial/project.md",
        "question:notes/q-offloading.md",
    ]
    assert by_token["interleaving"] == ["watch"]
    assert by_token["note"] == ["hub:hubs/note-taking.md"]
    assert "practice" not in by_token


def test_shipped_seed_steering_is_override_only_and_contributes_no_tokens(
    tmp_path: Path,
) -> None:
    text = (WORKSPACE_SEED / "steering.md").read_text(encoding="utf-8")
    _write(tmp_path / "steering.md", text)

    assert "## Watch for" in text
    assert "## Muted" in text
    assert steering_overrides(tmp_path) == (set(), set())
    assert effective_steering_tokens(tmp_path) == set()
