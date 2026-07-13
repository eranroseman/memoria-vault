from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from memoria_vault.cli import main
from memoria_vault.runtime import state
from memoria_vault.runtime.knowledge import promote_draft_passage as _promote_draft_passage
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.helpers import call_with_context, copy_memoria_dirs, init_git


def promote_draft_passage(vault: Path, *args, **kwargs):
    return call_with_context(_promote_draft_passage, vault, *args, **kwargs)


def test_promote_draft_passage_creates_unchecked_note_and_links_draft(tmp_path: Path) -> None:
    vault = _workspace(tmp_path)
    _checked_project(vault)
    draft = vault / "projects/project-alpha/draft.md"
    draft.write_text("# Alpha draft\n\nSelected claim text.\n", encoding="utf-8")

    result = promote_draft_passage(
        vault,
        "project-alpha",
        title="Selected Claim",
        passage="Selected claim text.",
        actor="pi",
        work_id="source-alpha",
    )

    assert result["note_path"] == "notes/selected-claim.md"
    assert result["check_status"] == "unchecked"
    note = vault / "notes/selected-claim.md"
    frontmatter = read_frontmatter(note)
    assert frontmatter["type"] == "note"
    assert frontmatter["title"] == "Selected Claim"
    assert frontmatter["work_id"] == "catalog/sources/source-alpha"
    assert "check_status" not in frontmatter
    assert state.concept_check_status(vault, "notes/selected-claim.md") == "unchecked"
    draft_text = draft.read_text(encoding="utf-8")
    assert "[Selected Claim](../../notes/selected-claim.md)" in draft_text
    assert "![[notes/selected-claim.md]]" not in draft_text


def test_promote_draft_passage_neutralizes_machine_draft_text(tmp_path: Path) -> None:
    vault = _workspace(tmp_path)
    _checked_project(vault)
    passage = (
        "![draft](http://beacon.example/draft.png) "
        "<script>signal()</script> http://beacon.example/bare"
    )
    draft = vault / "projects/project-alpha/draft.md"
    draft.write_text(f"# Alpha draft\n\n{passage}\n", encoding="utf-8")

    result = promote_draft_passage(
        vault,
        "project-alpha",
        title="Selected Claim",
        passage=passage,
        actor="pi",
    )

    rendered = (vault / result["note_path"]).read_text(encoding="utf-8")
    assert "![draft]" not in rendered
    assert "<script>" not in rendered
    assert "`http://beacon.example/draft.png`" in rendered
    assert "`http://beacon.example/bare`" in rendered


def test_promote_draft_passage_neutralizes_titles_composed_into_links(tmp_path: Path) -> None:
    pandoc = shutil.which("pandoc")
    if pandoc is None:
        pytest.skip("Pandoc is optional")
    vault = _workspace(tmp_path)
    _checked_project(vault)
    passage = "Selected claim text."
    draft = vault / "projects/project-alpha/draft.md"
    draft.write_text(f"# Alpha draft\n\n{passage}\n", encoding="utf-8")

    titles = (
        "x](javascript:alert(1))",
        "x](data:text/plain,unsafe)",
        "x](//evil.example/promote-protocol-relative)",
        "x](https://evil.example/promote-external)",
        r"brackets [stay] and \\slashes",
        '```\n<img src="https://evil.example/promote-fenced">\n```',
        r'\` <img src="https://evil.example/promote-escaped"> \`',
    )
    for title in titles:
        result = promote_draft_passage(
            vault,
            "project-alpha",
            title=title,
            passage=passage,
            actor="pi",
        )
        assert read_frontmatter(vault / result["note_path"])["title"] == title

    rendered = subprocess.run(
        [pandoc, "-f", "commonmark", "-t", "html"],
        input=draft.read_text(encoding="utf-8"),
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    assert "<img" not in rendered
    assert 'href="javascript:alert(1)"' not in rendered
    assert 'href="data:text/plain,unsafe"' not in rendered
    assert 'href="//evil.example/promote-protocol-relative"' not in rendered
    assert 'href="https://evil.example/promote-external"' not in rendered
    assert rendered.count('href="../../notes/') == len(titles)


def test_cli_project_promote_runs_writeback_operation(tmp_path: Path, capsys: object) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    _checked_project(workspace)
    draft = workspace / "projects/project-alpha/draft.md"
    draft.write_text("# Alpha draft\n\nSelected claim text.\n", encoding="utf-8")

    rc = main(
        [
            "project",
            "promote",
            "--workspace",
            str(workspace),
            "project-alpha",
            "--title",
            "Selected Claim",
            "--passage",
            "Selected claim text.",
            "--work-id",
            "source-alpha",
            "--json",
            "--idempotency-key",
            "project-promote",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["result"]["note_path"] == "notes/selected-claim.md"
    assert state.concept_check_status(workspace, "notes/selected-claim.md") == "unchecked"
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id FROM operation_requests WHERE request_id = ?",
            ("project-promote",),
        ).fetchone()
    assert row["operation_id"] == "promote-draft-passage"


def _workspace(tmp_path: Path) -> Path:
    copy_memoria_dirs(tmp_path, "schemas", "config")
    init_git(tmp_path, "writeback@example.invalid", "Writeback")
    return tmp_path


def _checked_project(vault: Path) -> None:
    path = vault / "projects/project-alpha/project.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\ntype: project\ntitle: Alpha project\ntags: []\nlinks: {}\n---\nBody.\n",
        encoding="utf-8",
    )
    state.record_observed_file_edit(
        vault,
        output_id="projects/project-alpha/project.md",
        concept_type="project",
        output_sha256=sha256_file(path),
    )
    state.set_concept_verdict(vault, "projects/project-alpha/project.md", "checked")
