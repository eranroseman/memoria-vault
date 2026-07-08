"""Tests for the removed-surface negative gate."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.checks import removed_surface_gate as gate


def write_contract(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "search_roots": ["docs"],
                "allow_text_files": ["docs/allowed.md"],
                "rules": [
                    {
                        "kind": "path",
                        "needle": "old/package",
                        "owner": "tests",
                        "reason": "retired package surface",
                    },
                    {
                        "kind": "text",
                        "needle": "OldSurface",
                        "owner": "tests",
                        "reason": "retired prose reference",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def test_reports_removed_paths_and_text_from_contract(tmp_path: Path) -> None:
    contract = tmp_path / "removed_surfaces.json"
    write_contract(contract)
    (tmp_path / "old" / "package").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "bad.md").write_text("OldSurface\n", encoding="utf-8")
    (tmp_path / "docs" / "allowed.md").write_text("OldSurface\n", encoding="utf-8")

    assert gate.find_violations(tmp_path, contract) == [
        "forbidden path exists: old/package",
        "docs/bad.md: contains OldSurface",
    ]
