"""Seeded-config two-class lifecycle: preferences survive repair; projections regenerate."""

from pathlib import Path

import pytest

from memoria_vault.cli import (
    SEED_CLASS_VIEW_PREFERENCE,
    SEED_CLASSES,
    SEED_FILES,
    SEED_TREES,
    VIEW_PREFERENCE_PATHS,
    main,
)
from memoria_vault.runtime.projections import (
    TRACKED_PROJECTION_PATHS,
    write_tracked_projections_explicit,
)
from tests.helpers import WORKSPACE_SEED


def _init(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> Path:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    return workspace


def test_seed_classes_manifest_is_exactly_the_nine_view_preferences() -> None:
    expected = frozenset(
        {
            "catalog.base",
            "claims.base",
            "inbox.base",
            "projects.base",
            "sources.base",
            ".obsidian/graph.json",
            ".obsidian/types.json",
            "steering.md",
            "system/vocabulary.md",
        }
    )

    assert SEED_CLASSES == dict.fromkeys(expected, SEED_CLASS_VIEW_PREFERENCE)
    assert VIEW_PREFERENCE_PATHS == expected


def test_seed_classes_manifest_covers_only_seeded_paths() -> None:
    seeded_file_targets = {target for _, target in SEED_FILES}
    tree_prefixes = tuple(f"{target}/" for _, target in SEED_TREES)
    for rel, cls in SEED_CLASSES.items():
        assert cls == SEED_CLASS_VIEW_PREFERENCE
        assert rel in seeded_file_targets or rel.startswith(tree_prefixes), rel


def test_data_projections_are_never_seeded() -> None:
    seeded = {target for _, target in SEED_FILES} | set(SEED_CLASSES)
    assert not seeded & set(TRACKED_PROJECTION_PATHS)


def test_repair_leaves_pi_modified_view_preferences(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = _init(tmp_path, capsys)
    pi_base = 'views:\n  - type: table\n    name: "Mine"\n    order:\n      - title\n'
    pi_graph = '{"colorGroups": []}\n'
    (workspace / "inbox.base").write_text(pi_base, encoding="utf-8")
    (workspace / ".obsidian/graph.json").write_text(pi_graph, encoding="utf-8")
    provider_config = workspace / ".memoria/config/providers.yaml"
    provider_config.write_text("broken: true\n", encoding="utf-8")

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])
    capsys.readouterr()

    assert rc == 0
    assert (workspace / "inbox.base").read_text(encoding="utf-8") == pi_base
    assert (workspace / ".obsidian/graph.json").read_text(encoding="utf-8") == pi_graph
    assert provider_config.read_text(encoding="utf-8") == (
        WORKSPACE_SEED / ".memoria/config/providers.yaml"
    ).read_text(encoding="utf-8")


def test_repair_reseeds_deleted_view_preferences(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = _init(tmp_path, capsys)
    (workspace / "inbox.base").unlink()

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])
    capsys.readouterr()

    assert rc == 0
    assert (workspace / "inbox.base").read_text(encoding="utf-8") == (
        WORKSPACE_SEED / "inbox.base"
    ).read_text(encoding="utf-8")


def test_regenerate_overwrites_data_projections(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = _init(tmp_path, capsys)
    (workspace / "bibliography.bib").write_text("PI edit\n", encoding="utf-8")

    result = write_tracked_projections_explicit(
        workspace, actor="operation", machine="test-machine"
    )

    assert "bibliography.bib" in result["changed"]
    assert (workspace / "bibliography.bib").read_text(encoding="utf-8") != "PI edit\n"
