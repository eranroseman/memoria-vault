from __future__ import annotations

import json
from pathlib import Path

from memoria_vault.runtime.knowledge import read_project_slice, write_project_argument_canvas
from tests.helpers import write_checked_concept


def test_outline_membership_drives_edges_and_large_slice_canvas(tmp_path: Path) -> None:
    write_checked_concept(
        tmp_path,
        "projects/project-alpha/project.md",
        "type: project\ncheck_status: checked\ntitle: Alpha project\n",
        "project",
    )
    outline_lines = []
    for index in range(1, 22):
        note_id = f"note-id-{index:02d}"
        links = ""
        if index == 1:
            links = "links:\n  supports:\n    - notes/note-02.md\n"
        if index == 3:
            links = "links:\n  supports:\n    - notes/outside.md\n"
        write_checked_concept(
            tmp_path,
            f"notes/note-{index:02d}.md",
            f"type: note\ncheck_status: checked\ntitle: Note {index:02d}\nid: {note_id}\n{links}",
            "note",
        )
        outline_lines.append(f"- {note_id} — Reason {index:02d}")
    write_checked_concept(
        tmp_path,
        "notes/outside.md",
        "type: note\ncheck_status: checked\ntitle: Outside\nid: outside-id\n",
        "note",
    )
    outline = tmp_path / "projects/project-alpha/outline.md"
    outline.write_text("\n".join(reversed(outline_lines)) + "\n", encoding="utf-8")

    project_slice = read_project_slice(tmp_path, "project-alpha")
    canvas_result = write_project_argument_canvas(tmp_path, "project-alpha")
    canvas = json.loads((tmp_path / canvas_result["canvas_path"]).read_text(encoding="utf-8"))

    assert [member["path"] for member in project_slice["members"]][:2] == [
        "notes/note-21.md",
        "notes/note-20.md",
    ]
    assert project_slice["edges"] == [
        {"source": "notes/note-01.md", "target": "notes/note-02.md", "type": "supports"}
    ]
    assert len(canvas["nodes"]) == 21
    assert {node["file"] for node in canvas["nodes"]} == {
        f"notes/note-{index:02d}.md" for index in range(1, 22)
    }
    assert "notes/outside.md" not in {node["file"] for node in canvas["nodes"]}
