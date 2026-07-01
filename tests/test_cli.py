from __future__ import annotations

import json
import os
import sys
import tomllib
from pathlib import Path

import pytest

from memoria_vault.cli import main
from memoria_vault.runtime import state
from memoria_vault.runtime.vaultio import read_frontmatter
from memoria_vault.runtime.worker import enqueue_operation

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
    assert (
        main(
            [
                "work",
                "interview",
                "--workspace",
                str(workspace),
                "--work-id",
                "doi-10.1000_alpha",
                "--prompt",
                "What matters?",
                "--response",
                "The PI cares about the methods caveat.",
                "--project-id",
                "knowledge/projects/project-alpha.md",
                "--json",
                "--idempotency-key",
                "interview-alpha",
            ]
        )
        == 0
    )
    interview = json.loads(capsys.readouterr().out)
    assert interview["result"]["source_id"] == "catalog/sources/doi-10.1000_alpha/source.md"
    assert interview["result"]["turn_id"].startswith("journal:copi-interview:")

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
    assert output["result"]["interview_count"] == 1
    digest = workspace / output["result"]["digest_path"]
    assert digest.is_file()
    body = digest.read_text(encoding="utf-8")
    assert "Alpha Source" in body
    assert "10.1000/alpha" in body
    assert not (workspace / "catalog/sources/doi-10.1000_alpha/source.md").exists()
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, args_json FROM operation_requests WHERE request_id = ?",
            ("interview-alpha",),
        ).fetchone()
    assert row["operation_id"] == "record-copi-interview"
    assert json.loads(row["args_json"]) == {
        "source_id": "doi-10.1000_alpha",
        "prompt": "What matters?",
        "response": "The PI cares about the methods caveat.",
        "project_id": "knowledge/projects/project-alpha.md",
    }


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


def test_cli_project_trace_and_export_argument_canvas(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    _write_project_argument_fixture(workspace)

    rc = main(
        [
            "project",
            "trace",
            "--workspace",
            str(workspace),
            "project-alpha",
            "--json",
            "--idempotency-key",
            "project-trace",
        ]
    )
    trace = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert trace["ok"] is True
    assert trace["result"]["argument_stage"] == "developing"
    assert trace["result"]["relation_count"] == 2
    assert trace["result"]["supports_count"] == 1
    assert trace["result"]["contradicts_count"] == 1

    rc = main(
        [
            "project",
            "export",
            "--workspace",
            str(workspace),
            "project-alpha",
            "--json",
            "--idempotency-key",
            "project-export",
        ]
    )
    exported = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert exported["ok"] is True
    assert exported["result"]["canvas_path"] == "knowledge/projects/project-alpha/argument.canvas"
    canvas = json.loads((workspace / exported["result"]["canvas_path"]).read_text(encoding="utf-8"))
    assert {edge["label"] for edge in canvas["edges"]} == {"supports", "contradicts"}
    with state.connect(workspace) as conn:
        rows = conn.execute(
            """
            SELECT request_id, operation_id
            FROM operation_requests
            WHERE request_id IN ('project-trace', 'project-export')
            ORDER BY request_id
            """
        ).fetchall()
    assert [(row["request_id"], row["operation_id"]) for row in rows] == [
        ("project-export", "render-project-argument-canvas"),
        ("project-trace", "analyze-project-argument"),
    ]


def test_cli_note_candidate_accept_and_link_flow(
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
        "description: Alpha\n"
        "source_id: catalog/sources/source-alpha\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )

    rc = main(
        [
            "note",
            "propose",
            "--workspace",
            str(workspace),
            "--digest-path",
            "knowledge/digests/source-alpha.md",
            "--candidate-json",
            json.dumps(
                {
                    "title": "Framing changes the question",
                    "body": "The source reframes the problem before measuring outcomes.",
                    "claim_text": "Framing changes which outcomes matter.",
                    "tags": ["Framing"],
                }
            ),
            "--candidate-json",
            json.dumps(
                {
                    "title": "Rejected framing aside",
                    "body": "This weaker candidate should be rejected.",
                }
            ),
            "--json",
            "--idempotency-key",
            "note-propose",
        ]
    )
    proposed = json.loads(capsys.readouterr().out)

    assert rc == 0
    note_path, rejected_note_path = proposed["result"]["note_paths"]
    note_fm = read_frontmatter(workspace / note_path)
    assert note_fm["check_status"] == "checked"
    assert note_fm["status"] == "candidate"

    assert (
        main(
            [
                "note",
                "accept",
                "--workspace",
                str(workspace),
                note_path,
                "--reason",
                "PI approved",
                "--json",
                "--idempotency-key",
                "note-accept",
            ]
        )
        == 0
    )
    accepted = json.loads(capsys.readouterr().out)
    assert accepted["result"]["curation_status"] == "accepted"
    assert read_frontmatter(workspace / note_path)["status"] == "accepted"

    assert (
        main(
            [
                "note",
                "reject",
                "--workspace",
                str(workspace),
                rejected_note_path,
                "--reason",
                "PI rejected",
                "--json",
                "--idempotency-key",
                "note-reject",
            ]
        )
        == 0
    )
    rejected = json.loads(capsys.readouterr().out)
    assert rejected["result"]["curation_status"] == "rejected"
    assert read_frontmatter(workspace / rejected_note_path)["status"] == "rejected"

    target = workspace / "knowledge/notes/target.md"
    target.write_text(
        "---\ntype: note\ncheck_status: checked\ntitle: Target\n---\nTarget body.\n",
        encoding="utf-8",
    )
    assert (
        main(
            [
                "note",
                "link",
                "--workspace",
                str(workspace),
                note_path,
                "--type",
                "supports",
                "--target",
                "knowledge/notes/target.md",
                "--reason",
                "PI linked notes",
                "--json",
                "--idempotency-key",
                "note-link",
            ]
        )
        == 0
    )
    linked = json.loads(capsys.readouterr().out)

    assert linked["result"]["link_type"] == "supports"
    assert read_frontmatter(workspace / note_path)["links"] == {
        "supports": ["knowledge/notes/target.md"]
    }


def test_cli_operation_list_and_run_use_workspace_operation_concepts(
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

    assert main(["operation", "list", "--workspace", str(workspace), "--json"]) == 0
    listed = json.loads(capsys.readouterr().out)
    operation_ids = {row["operation_id"] for row in listed["operations"]}
    assert {"analyze-gaps", "enrich-source", "integrity-citation-survival-check"} <= operation_ids

    rc = main(
        [
            "operation",
            "run",
            "--workspace",
            str(workspace),
            "analyze-gaps",
            "--payload-json",
            json.dumps({"seed_terms": ["new area"], "dense_threshold": 1}),
            "--json",
            "--idempotency-key",
            "operation-run-gaps",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    gaps = {gap["topic"]: gap for gap in output["result"]["gaps"]}
    assert gaps["sleep"]["gap_type"] == "undigested"
    assert gaps["new area"]["gap_type"] == "new-topic"
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, args_json FROM operation_requests WHERE request_id = ?",
            ("operation-run-gaps",),
        ).fetchone()
    assert row["operation_id"] == "analyze-gaps"
    assert json.loads(row["args_json"]) == {
        "seed_terms": ["new area"],
        "dense_threshold": 1,
    }


def test_cli_request_list_show_and_resume_pending_request(
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
    enqueue_operation(
        workspace,
        "analyze-gaps",
        payload={"seed_terms": ["new area"], "dense_threshold": 1},
        idempotency_key="resume-gaps",
        provenance={"surface": "test"},
    )

    assert (
        main(["request", "list", "--workspace", str(workspace), "--status", "pending", "--json"])
        == 0
    )
    listed = json.loads(capsys.readouterr().out)
    assert [row["request_id"] for row in listed["requests"]] == ["resume-gaps"]

    assert main(["request", "show", "--workspace", str(workspace), "resume-gaps", "--json"]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["request"]["operation_id"] == "analyze-gaps"
    assert shown["request"]["args"] == {"seed_terms": ["new area"], "dense_threshold": 1}
    assert shown["request"]["provenance"] == {"surface": "test"}

    rc = main(["request", "resume", "--workspace", str(workspace), "resume-gaps", "--json"])
    resumed = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert resumed["result"]["status"] == "done"
    gaps = {gap["topic"]: gap for gap in resumed["result"]["gaps"]}
    assert gaps["sleep"]["gap_type"] == "undigested"
    assert gaps["new area"]["gap_type"] == "new-topic"
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT status FROM operation_requests WHERE request_id = ?",
            ("resume-gaps",),
        ).fetchone()
    assert row["status"] == "done"


def test_cli_eval_seeded_error_verdict_uses_seeded_workspace_bundle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    assert (workspace / "system/eval/alpha12-seeded-errors.json").is_file()

    def fake_verdict(
        vault: Path, *, template_root: Path, bundle_path: Path, machine: str
    ) -> dict[str, object]:
        assert vault != workspace
        assert template_root == workspace
        assert bundle_path == workspace / "system/eval/alpha12-seeded-errors.json"
        assert machine == "memoria-cli"
        return {"passed": True, "metrics": {"expected_errors": 1}}

    monkeypatch.setattr(
        "memoria_vault.runtime.seeded_errors.run_seeded_error_verdict",
        fake_verdict,
    )

    rc = main(
        [
            "eval",
            "seeded-error-verdict",
            "--workspace",
            str(workspace),
            "--json",
            "--idempotency-key",
            "seeded-verdict",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["result"]["passed"] is True
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, args_json FROM operation_requests WHERE request_id = ?",
            ("seeded-verdict",),
        ).fetchone()
    assert row["operation_id"] == "run-seeded-error-verdict"
    assert json.loads(row["args_json"]) == {}


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


def _write_project_argument_fixture(workspace: Path) -> None:
    project = workspace / "knowledge/projects/project-alpha.md"
    project.parent.mkdir(parents=True, exist_ok=True)
    project.write_text(
        "---\n"
        "type: project\n"
        "check_status: checked\n"
        "title: Alpha project\n"
        "thesis: knowledge/notes/thesis.md\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    notes = {
        "thesis": "type: note\ncheck_status: checked\ntitle: Thesis\nstatus: accepted\n",
        "support": (
            "type: note\ncheck_status: checked\ntitle: Support\nstatus: accepted\n"
            "links:\n  supports:\n    - knowledge/notes/thesis.md\n"
        ),
        "refute": (
            "type: note\ncheck_status: checked\ntitle: Refute\nstatus: accepted\n"
            "links:\n  contradicts:\n    - knowledge/notes/thesis.md\n"
        ),
    }
    for name, frontmatter in notes.items():
        note = workspace / f"knowledge/notes/{name}.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(f"---\n{frontmatter}---\nBody.\n", encoding="utf-8")


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
