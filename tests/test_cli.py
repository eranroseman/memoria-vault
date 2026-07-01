from __future__ import annotations

import json
import os
import sys
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


def test_cli_work_capture_file_stages_text_without_legacy_markdown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    text = tmp_path / "work.txt"
    text.write_text("Full text from the PI.\n", encoding="utf-8")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(
        [
            "work",
            "capture",
            "--workspace",
            str(workspace),
            "--file",
            str(text),
            "--title",
            "PI text",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["result"]["source_id"] == "work"
    assert not (workspace / "catalog/sources/work/source.md").exists()
    assert (workspace / output["result"]["content_path"]).read_text(encoding="utf-8") == (
        "Full text from the PI.\n"
    )


def test_cli_work_capture_url_fetches_text_without_legacy_markdown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"

    def fake_read(url: str, timeout: float) -> bytes:
        assert url == "https://example.test/source"
        assert timeout == 10.0
        return b"<html><title>Fetched</title><body><p>Fetched full text.</p></body></html>"

    monkeypatch.setattr("memoria_vault.runtime.capture._read_url_bytes", fake_read)
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(
        [
            "work",
            "capture",
            "--workspace",
            str(workspace),
            "--url",
            "https://example.test/source",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    source_id = output["result"]["source_id"]
    assert output["result"]["check_status"] == "unchecked"
    assert not (workspace / f"catalog/sources/{source_id}/source.md").exists()
    assert "Fetched full text." in (workspace / output["result"]["content_path"]).read_text(
        encoding="utf-8"
    )


def test_cli_work_capture_pdf_extracts_text_without_legacy_markdown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF fixture")

    monkeypatch.setattr(
        "memoria_vault.runtime.capture._extract_pdf_pages",
        lambda raw: [{"page": 1, "text": "Extracted PDF text."}],
    )
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(
        [
            "work",
            "capture",
            "--workspace",
            str(workspace),
            "--pdf",
            str(pdf),
            "--title",
            "PDF work",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["result"]["source_id"] == "paper"
    assert not (workspace / "catalog/sources/paper/source.md").exists()
    assert "Extracted PDF text." in (workspace / output["result"]["content_path"]).read_text(
        encoding="utf-8"
    )


def test_cli_work_digest_compiles_checked_db_work_after_enrichment(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    replay = tmp_path / "providers.json"
    replay.write_text(json.dumps(_doi_provider_payloads()), encoding="utf-8")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    assert (
        main(
            [
                "work",
                "capture",
                "--workspace",
                str(workspace),
                "--doi",
                "10.1000/alpha",
                "--title",
                "Alpha Source",
                "--json",
                "--idempotency-key",
                "capture-alpha",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert (
        main(
            [
                "work",
                "enrich",
                "--workspace",
                str(workspace),
                "--work-id",
                "doi-10.1000_alpha",
                "--provider-replay",
                str(replay),
                "--json",
                "--idempotency-key",
                "enrich-alpha",
            ]
        )
        == 0
    )
    capsys.readouterr()

    rc = main(
        [
            "work",
            "digest",
            "--workspace",
            str(workspace),
            "--work-id",
            "doi-10.1000_alpha",
            "--json",
            "--idempotency-key",
            "digest-alpha",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["result"]["digest_path"] == "knowledge/digests/doi-10.1000_alpha.md"
    digest = workspace / output["result"]["digest_path"]
    assert digest.is_file()
    body = digest.read_text(encoding="utf-8")
    assert "Alpha Source" in body
    assert "10.1000/alpha" in body
    assert not (workspace / "catalog/sources/doi-10.1000_alpha/source.md").exists()


def test_cli_project_gaps_runs_gap_analysis_request(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    digest = workspace / "knowledge/digests/source-alpha.md"
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text(
        "---\n"
        "type: digest\n"
        "check_status: checked\n"
        "title: Alpha digest\n"
        "tags: [sleep]\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )

    rc = main(
        [
            "project",
            "gaps",
            "--workspace",
            str(workspace),
            "--seed-term",
            "new area",
            "--dense-threshold",
            "1",
            "--json",
            "--idempotency-key",
            "project-gaps",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    gaps = {gap["topic"]: gap for gap in output["result"]["gaps"]}
    assert gaps["sleep"]["gap_type"] == "undigested"
    assert gaps["new area"]["gap_type"] == "new-topic"
    with state.connect(workspace) as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(operation_requests)")}
        row = conn.execute(
            "SELECT operation_id, args_json FROM operation_requests WHERE request_id = ?",
            ("project-gaps",),
        ).fetchone()
    assert "trigger_type" not in columns
    assert row["operation_id"] == "analyze-gaps"
    assert json.loads(row["args_json"]) == {
        "seed_terms": ["new area"],
        "dense_threshold": 1,
    }


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


def test_cli_doctor_qmd_checks_workspace_local_state(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    _fake_qmd_toolchain(tmp_path, monkeypatch)
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(["doctor", "--workspace", str(workspace), "--check", "qmd", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["checks"]["node_22"] is True
    assert output["checks"]["qmd_absolute"] is True
    assert output["qmd_path"].startswith(str(tmp_path))


def test_cli_workspace_rebuild_runs_qmd_with_workspace_local_state(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    qmd_log = _fake_qmd_toolchain(tmp_path, monkeypatch)
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    note = workspace / "knowledge/notes/qmd.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(
        "---\ntype: note\ncheck_status: checked\ntitle: qmd\n---\nalpha search\n",
        encoding="utf-8",
    )

    rc = main(
        [
            "workspace",
            "rebuild",
            "--workspace",
            str(workspace),
            "--search",
            "--embeddings",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["qmd"]["manifest"]["documents"][0]["path"] == "knowledge/notes/qmd.md"
    assert (workspace / ".memoria/index/qmd/checked/knowledge/notes/qmd.md").is_file()
    lines = qmd_log.read_text(encoding="utf-8").splitlines()
    assert lines == [
        "collection add "
        f"{workspace}/.memoria/index/qmd/checked --name memoria-checked --mask **/*.md"
        f"|{workspace}/.memoria/index/qmd/config|{workspace}/.memoria/index/qmd/cache",
        f"update|{workspace}/.memoria/index/qmd/config|{workspace}/.memoria/index/qmd/cache",
        "embed --chunk-strategy auto"
        f"|{workspace}/.memoria/index/qmd/config|{workspace}/.memoria/index/qmd/cache",
    ]


def _fake_qmd_toolchain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    qmd_log = tmp_path / "qmd.log"
    node = bin_dir / "node"
    node.write_text(f"#!{sys.executable}\nprint('v22.11.0')\n", encoding="utf-8")
    qmd = bin_dir / "qmd"
    qmd.write_text(
        f"#!{sys.executable}\n"
        "import os, pathlib, sys\n"
        "pathlib.Path(os.environ['QMD_LOG']).open('a', encoding='utf-8').write(\n"
        "    ' '.join(sys.argv[1:]) + '|' + os.environ.get('XDG_CONFIG_HOME', '')\n"
        "    + '|' + os.environ.get('XDG_CACHE_HOME', '') + '\\n'\n"
        ")\n",
        encoding="utf-8",
    )
    node.chmod(0o755)
    qmd.chmod(0o755)
    monkeypatch.setenv("QMD_LOG", str(qmd_log))
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    return qmd_log


def _doi_provider_payloads() -> dict[str, object]:
    return {
        "crossref": {
            "message": {
                "DOI": "10.1000/alpha",
                "URL": "https://doi.org/10.1000/alpha",
                "type": "journal-article",
                "title": ["Alpha Source"],
                "container-title": ["Journal of Testable Systems"],
                "author": [{"given": "Ada", "family": "River"}],
                "issued": {"date-parts": [[2026]]},
                "relation": {},
            }
        },
        "openalex": {
            "id": "https://openalex.org/W123",
            "doi": "https://doi.org/10.1000/alpha",
            "title": "Alpha Source",
            "authorships": [
                {
                    "author": {
                        "id": "https://openalex.org/A123",
                        "display_name": "Ada River",
                    },
                    "institutions": [],
                }
            ],
            "primary_location": {"source": {"display_name": "Journal of Testable Systems"}},
            "topics": [{"display_name": "Research workflows"}],
        },
        "unpaywall": {
            "doi": "10.1000/alpha",
            "is_oa": True,
            "oa_status": "gold",
            "best_oa_location": {"url_for_pdf": "https://example.test/alpha.pdf"},
        },
    }
