from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

from memoria_vault.cli import main
from memoria_vault.runtime import state

ROOT = Path(__file__).resolve().parent.parent


def test_cli_help_imports_without_adapter_environment(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])

    assert exc.value.code == 0
    assert "memoria" in capsys.readouterr().out


def test_pyproject_exposes_memoria_console_script() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["scripts"]["memoria"] == "memoria_vault.cli:main"


def test_cli_init_and_work_capture_use_request_envelope_without_trigger_type(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"

    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    rc = main(
        [
            "work",
            "capture",
            "--workspace",
            str(workspace),
            "--doi",
            "10.1000/alpha",
            "--json",
            "--idempotency-key",
            "capture-alpha",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["result"]["source_id"] == "doi-10.1000_alpha"
    assert not (workspace / "catalog/sources/doi-10.1000_alpha/source.md").exists()
    assert (workspace / output["result"]["content_path"]).is_file()
    with state.connect(workspace) as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(operation_requests)")}
        row = conn.execute(
            "SELECT operation_id, provenance_json FROM operation_requests WHERE request_id = ?",
            ("capture-alpha",),
        ).fetchone()
    assert "trigger_type" not in columns
    assert row["operation_id"] == "capture-source"
    assert json.loads(row["provenance_json"]) == {
        "command": "capture-source",
        "surface": "memoria-cli",
    }


def test_cli_work_import_bibtex_seeds_unchecked_db_work_without_markdown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    bibtex = tmp_path / "source.bib"
    bibtex.write_text(
        """@article{alpha2026,
  title = {Alpha Import},
  author = {River, Ada},
  year = {2026},
  doi = {10.1000/import.2026},
  abstract = {Portable file import.}
}
""",
        encoding="utf-8",
    )
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(
        [
            "work",
            "import",
            "--workspace",
            str(workspace),
            "--format",
            "bibtex",
            "--file",
            str(bibtex),
            "--json",
            "--idempotency-key",
            "import-bibtex",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["result"]["source_id"] == "doi-10.1000_import.2026"
    assert not (workspace / "catalog/sources/doi-10.1000_import.2026/source.md").exists()
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT title, check_status, content_path FROM catalog_sources WHERE source_id = ?",
            ("doi-10.1000_import.2026",),
        ).fetchone()
    assert tuple(row) == (
        "Alpha Import",
        "unchecked",
        output["result"]["content_path"],
    )


def test_cli_work_import_csl_seeds_isbn_book_without_zotero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    csl = tmp_path / "book.csl.json"
    csl.write_text(
        json.dumps(
            {
                "id": "book2026",
                "type": "book",
                "title": "Standalone Book",
                "ISBN": "9780000000002",
                "author": [{"family": "River", "given": "Ada"}],
            }
        ),
        encoding="utf-8",
    )
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(
        [
            "work",
            "import",
            "--workspace",
            str(workspace),
            "--format",
            "csl",
            "--file",
            str(csl),
            "--json",
            "--idempotency-key",
            "import-csl",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["result"]["source_id"] == "book2026"
    assert not (workspace / "catalog/sources/book2026/source.md").exists()
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT title, check_status, identifiers_json FROM catalog_sources WHERE source_id = ?",
            ("book2026",),
        ).fetchone()
        columns = {
            column["name"] for column in conn.execute("PRAGMA table_info(operation_requests)")
        }
    assert row["title"] == "Standalone Book"
    assert row["check_status"] == "unchecked"
    assert json.loads(row["identifiers_json"]) == {"isbn": "9780000000002"}
    assert "trigger_type" not in columns
