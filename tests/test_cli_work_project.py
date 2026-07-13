from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.cli import _build_parser, main
from memoria_vault.runtime import state
from memoria_vault.runtime.vaultio import read_frontmatter
from tests.helpers import mark_file_status


def _assert_request_columns(columns: set[str]) -> None:
    assert {
        "input_refs_json",
        "output_intents_json",
        "primary_target",
        "precondition_hashes_json",
    } <= columns
    assert {"trigger_type", "target_path", "target_hash"}.isdisjoint(columns)


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
    assert output["result"]["work_id"] == "doi-10.1000_import.2026"
    assert output["enrichment_job"]["operation_id"] == "enrich-source"
    assert output["enrichment_job"]["status"] == "pending"
    assert not (workspace / "catalog/sources/doi-10.1000_import.2026/source.md").exists()
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT title, check_status, content_path FROM catalog_sources WHERE work_id = ?",
            ("doi-10.1000_import.2026",),
        ).fetchone()
        enrich = conn.execute(
            "SELECT operation_id, status, actor FROM operation_requests WHERE request_id = ?",
            ("enrich-doi-10.1000_import.2026_import-bibtex",),
        ).fetchone()
    assert tuple(row) == (
        "Alpha Import",
        "unchecked",
        output["result"]["content_path"],
    )
    assert tuple(enrich) == ("enrich-source", "pending", "operation")


def test_cli_work_add_file_stages_text_without_source_markdown(
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
            "add",
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
    assert output["result"]["work_id"] == "work"
    assert not (workspace / "catalog/sources/work/source.md").exists()
    assert (workspace / output["result"]["content_path"]).read_text(encoding="utf-8") == (
        "Full text from the PI.\n"
    )


def test_cli_work_add_url_fetches_text_without_source_markdown(
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
            "add",
            "--workspace",
            str(workspace),
            "--url",
            "https://example.test/source",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    work_id = output["result"]["work_id"]
    assert output["result"]["check_status"] == "unchecked"
    assert not (workspace / f"catalog/sources/{work_id}/source.md").exists()
    assert "Fetched full text." in (workspace / output["result"]["content_path"]).read_text(
        encoding="utf-8"
    )


def test_cli_work_add_pdf_extracts_text_without_source_markdown(
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
            "add",
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
    assert output["result"]["work_id"] == "paper"
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
    interview_fixture = tmp_path / "interview.json"
    interview_fixture.write_text(
        json.dumps(
            {
                "prompt": "What matters?",
                "response": "The PI cares about the methods caveat.",
                "project_id": "projects/project-alpha/project.md",
            }
        ),
        encoding="utf-8",
    )
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    assert (
        main(
            [
                "work",
                "add",
                "--workspace",
                str(workspace),
                "--doi",
                "10.1000/alpha",
                "--title",
                "Alpha Source",
                "--text",
                "Alpha full text about framing, methods, outcomes, gaps, and impact.",
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
                "doi-10.1000_alpha",
                "--fixture",
                str(interview_fixture),
                "--json",
                "--idempotency-key",
                "interview-alpha",
            ]
        )
        == 0
    )
    interview = json.loads(capsys.readouterr().out)
    assert interview["result"]["work_id"] == "doi-10.1000_alpha"
    assert interview["result"]["turn_id"].startswith("journal:copi-interview:")

    rc = main(
        [
            "work",
            "digest",
            "--workspace",
            str(workspace),
            "doi-10.1000_alpha",
            "--json",
            "--idempotency-key",
            "digest-alpha",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["result"]["digest_path"] == "digests/doi-10.1000_alpha.md"
    assert output["result"]["interview_count"] == 1
    digest = workspace / output["result"]["digest_path"]
    assert digest.is_file()
    body = digest.read_text(encoding="utf-8")
    assert "Alpha Source" in body
    digest_fm = read_frontmatter(digest)
    assert digest_fm["id"] == "doi-10.1000_alpha"
    assert digest_fm["work_id"] == "doi-10.1000_alpha"
    assert "evidence_set" not in digest_fm
    assert "citations" not in digest_fm
    assert not (workspace / "catalog/sources/doi-10.1000_alpha/source.md").exists()
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, args_json FROM operation_requests WHERE request_id = ?",
            ("interview-alpha",),
        ).fetchone()
    assert row["operation_id"] == "record-copi-interview"
    assert json.loads(row["args_json"]) == {
        "work_id": "doi-10.1000_alpha",
        "prompt": "What matters?",
        "response": "The PI cares about the methods caveat.",
        "project_id": "projects/project-alpha/project.md",
    }


def test_cli_thin_knowledge_loop_runs_end_to_end(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    replay = tmp_path / "providers.json"
    replay.write_text(json.dumps(_doi_provider_payloads()), encoding="utf-8")
    interview_fixture = tmp_path / "interview.json"
    interview_fixture.write_text(
        json.dumps(
            {
                "prompt": "What matters?",
                "response": "The PI cares about methods caveats and framing.",
                "project_id": "projects/project-alpha/project.md",
            }
        ),
        encoding="utf-8",
    )

    def run_json(*argv: str) -> dict:
        rc = main([*argv, "--json"])
        output = json.loads(capsys.readouterr().out)
        assert rc == 0, output
        assert output["ok"] is True
        return output

    run_json("init", "--workspace", str(workspace), "--yes")
    _write_project_argument_fixture(workspace)

    run_json(
        "work",
        "add",
        "--workspace",
        str(workspace),
        "--doi",
        "10.1000/alpha",
        "--title",
        "Alpha Source",
        "--text",
        "Alpha full text about framing, methods, outcomes, gaps, and impact.",
        "--idempotency-key",
        "loop-capture",
    )
    run_json(
        "work",
        "enrich",
        "--workspace",
        str(workspace),
        "doi-10.1000_alpha",
        "--provider-replay",
        str(replay),
        "--idempotency-key",
        "loop-enrich",
    )
    updated = run_json(
        "work",
        "update",
        "--workspace",
        str(workspace),
        "doi-10.1000_alpha",
        "--research-area",
        "personal-informatics",
        "--methodology",
        "rct",
        "--idempotency-key",
        "loop-update",
    )
    memoria = updated["result"]["work"]["csl_json"]["memoria"]
    assert memoria["research_area"] == ["personal-informatics"]
    assert memoria["methodology"] == ["rct"]
    assert "topics" not in memoria
    run_json(
        "work",
        "interview",
        "--workspace",
        str(workspace),
        "doi-10.1000_alpha",
        "--fixture",
        str(interview_fixture),
        "--idempotency-key",
        "loop-interview",
    )
    digest = run_json(
        "work",
        "digest",
        "--workspace",
        str(workspace),
        "doi-10.1000_alpha",
        "--idempotency-key",
        "loop-digest",
    )
    digest_path = digest["result"]["digest_path"]

    note = run_json(
        "new",
        "note",
        "Loop note",
        "--workspace",
        str(workspace),
        "--body",
        "Framing changes which outcomes matter.",
        "--tag",
        "framing",
        "--idempotency-key",
        "loop-note-new",
    )
    note_path = note["path"]
    run_json(
        "check",
        "--workspace",
        str(workspace),
        note_path,
        "--idempotency-key",
        "loop-note-check",
    )
    run_json(
        "link",
        "--workspace",
        str(workspace),
        note_path,
        "notes/thesis.md",
        "--rel",
        "supports",
        "--reason",
        "PI linked the checked note to the thesis",
        "--idempotency-key",
        "loop-note-link",
    )

    answer = run_json(
        "ask",
        "--workspace",
        str(workspace),
        "--question",
        "framing outcomes",
        "--idempotency-key",
        "loop-ask",
    )
    assert {source["path"] for source in answer["result"]["sources"]} & {
        digest_path,
        note_path,
        "fulltexts/doi-10.1000_alpha.md",
    }

    project_answer = run_json(
        "project",
        "ask",
        "--workspace",
        str(workspace),
        "project-alpha",
        "--question",
        "what matters",
        "--idempotency-key",
        "loop-project-ask",
    )
    assert project_answer["result"]["project_context"]["project_path"] == (
        "projects/project-alpha/project.md"
    )

    gaps = run_json(
        "project",
        "gaps",
        "--workspace",
        str(workspace),
        "project-alpha",
        "--seed-term",
        "new area",
        "--dense-threshold",
        "1",
        "--idempotency-key",
        "loop-gaps",
    )
    assert gaps["result"]["gap_count"] >= 1
    assert gaps["result"]["project_path"] == "projects/project-alpha/project.md"
    assert gaps["result"]["argument_gap_count"] >= 1

    exported = run_json(
        "project",
        "export",
        "--workspace",
        str(workspace),
        "project-alpha",
        "--output",
        "exports/project-alpha.md",
        "--idempotency-key",
        "loop-export",
    )
    assert exported["result"]["output_path"] == "exports/project-alpha.md"
    assert (workspace / "exports/project-alpha.md").is_file()

    recovered = run_json(
        "workspace",
        "recover",
        "--workspace",
        str(workspace),
        "--fixture",
        "crash-before-materialization",
    )
    assert recovered["restored"] == ["notes/crash-before-materialization.md"]

    with state.connect(workspace) as conn:
        operations = {
            row["operation_id"]
            for row in conn.execute(
                """
                SELECT operation_id
                FROM operation_requests
                WHERE request_id LIKE 'loop-%'
                """
            )
        }
    assert {
        "capture-source",
        "enrich-source",
        "update-work",
        "record-copi-interview",
        "compile-source-digest",
        "mark-checked",
        "curate-note-link",
        "answer-query",
        "analyze-gaps",
        "export-project",
    } <= operations


def test_cli_work_update_rejects_retired_topic_flag() -> None:
    with pytest.raises(SystemExit) as exc:
        _build_parser().parse_args(
            [
                "work",
                "update",
                "--workspace",
                "/tmp/disposable-vault",
                "work-alpha",
                "--topic",
                "personal-informatics",
            ]
        )

    assert exc.value.code == 2


def test_cli_project_gaps_runs_gap_analysis_request(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    digest = workspace / "digests/source-alpha.md"
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text(
        "---\n"
        "type: digest\n"
        "title: Alpha digest\n"
        "work_id: source-alpha\n"
        "tags: [sleep]\n"
        "links: {}\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "digests/source-alpha.md", "digest")
    state.upsert_catalog_record(
        workspace,
        work_id="db-alpha",
        title="DB Alpha",
        text_status="full-text",
        check_status="checked",
        csl_json={"memoria": {"research_area": ["catalog-only"]}},
    )
    _write_project_argument_fixture(workspace)

    rc = main(
        [
            "project",
            "gaps",
            "--workspace",
            str(workspace),
            "project-alpha",
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
    assert gaps["catalog-only"]["gap_type"] == "undigested"
    assert gaps["catalog-only"]["kind"] == "undigested"
    assert gaps["catalog-only"]["why"]
    assert gaps["catalog-only"]["next_actions"]
    assert gaps["catalog-only"]["source_count"] == 1
    assert gaps["sleep"]["gap_type"] == "undigested"
    assert gaps["new area"]["gap_type"] == "new-topic"
    assert output["result"]["project_path"] == "projects/project-alpha/project.md"
    assert output["result"]["argument_gap_count"] == 2
    assert output["result"]["summary"]["total"] == output["result"]["gap_count"]
    assert output["result"]["saturation"]["claims"] == 1
    assert output["result"]["saturation"]["ready"] is True
    assert {
        gap["finding_kind"]
        for gap in output["result"]["gaps"]
        if gap["gap_type"].startswith("argument-")
    } == {"thin-argument", "conflict"}
    assert {
        gap["kind"] for gap in output["result"]["gaps"] if gap["gap_type"].startswith("argument-")
    } == {"argument-unsupported", "argument-fragile"}
    with state.connect(workspace) as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(operation_requests)")}
        row = conn.execute(
            "SELECT operation_id, args_json FROM operation_requests WHERE request_id = ?",
            ("project-gaps",),
        ).fetchone()
    _assert_request_columns(columns)
    assert row["operation_id"] == "analyze-gaps"
    assert json.loads(row["args_json"]) == {
        "project_path": "project-alpha",
        "seed_terms": ["new area"],
        "dense_threshold": 1,
    }


def test_cli_project_trace_and_export_markdown(
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
            "--format",
            "markdown",
            "--output",
            "exports/project-alpha.md",
            "--json",
            "--idempotency-key",
            "project-export",
        ]
    )
    exported = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert exported["ok"] is True
    assert exported["result"]["format"] == "markdown"
    assert exported["result"]["output_path"] == "exports/project-alpha.md"
    assert exported["result"]["content"] == ""
    exported_text = (workspace / "exports/project-alpha.md").read_text(encoding="utf-8")
    assert "# Alpha project" in exported_text
    assert "## Argument Snapshot" in exported_text
    assert "- Stage: developing" in exported_text
    assert "- Support --supports--> Thesis" in exported_text
    assert "- Refute --contradicts--> Thesis" in exported_text
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
        ("project-export", "export-project"),
        ("project-trace", "analyze-project-argument"),
    ]


def test_cli_project_slice_writes_outline(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    _write_project_argument_fixture(workspace)

    rc = main(
        [
            "project",
            "slice",
            "--workspace",
            str(workspace),
            "project-alpha",
            "--query",
            "support thesis",
            "--limit",
            "2",
            "--json",
            "--idempotency-key",
            "project-slice",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    result = output["result"]
    assert result["retrieval_engine"] == "bm25"
    assert result["outline_path"] == "projects/project-alpha/outline.md"
    assert result["member_count"] == 2
    assert {member["path"] for member in result["members"]} == {
        "notes/support.md",
        "notes/thesis.md",
    }
    assert result["edges"] == [
        {"source": "notes/support.md", "target": "notes/thesis.md", "type": "supports"}
    ]
    outline = (workspace / "projects/project-alpha/outline.md").read_text(encoding="utf-8")
    assert "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 — BM25 score " in outline
    assert "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 — BM25 score " in outline
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id FROM operation_requests WHERE request_id = ?",
            ("project-slice",),
        ).fetchone()
    assert row["operation_id"] == "write-project-slice"


def test_cli_project_compose_writes_draft(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    _write_project_argument_fixture(workspace)
    (workspace / "projects/project-alpha/outline.md").write_text(
        "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 -- Support first\n"
        "- 01ARZ3NDEKTSV4RRFFQ69G5FA1 -- Thesis second\n",
        encoding="utf-8",
    )

    rc = main(
        [
            "project",
            "compose",
            "--workspace",
            str(workspace),
            "project-alpha",
            "--token-budget",
            "400",
            "--json",
            "--idempotency-key",
            "project-compose",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    result = output["result"]
    assert result["draft_path"] == "projects/project-alpha/draft.md"
    assert result["member_count"] == 2
    assert result["evidence_set_count"] == 2
    evidence_ids = [marker["id"] for marker in result["evidence_markers"]]
    draft = (workspace / "projects/project-alpha/draft.md").read_text(encoding="utf-8")
    assert "## Support" in draft
    assert "%%ev:" in draft
    rc = main(
        [
            "project",
            "verify",
            "--workspace",
            str(workspace),
            "project-alpha",
            "--json",
            "--idempotency-key",
            "project-verify",
        ]
    )
    verified = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert verified["ok"] is True
    assert verified["result"]["ready"] is False
    assert verified["result"]["max_findings"] == 20
    assert verified["result"]["triaged_count"] == 4
    rc = main(
        [
            "project",
            "export",
            "--workspace",
            str(workspace),
            "project-alpha",
            "--draft",
            "--json",
            "--idempotency-key",
            "project-export-draft",
        ]
    )
    refused = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert refused["ok"] is False
    assert "project draft is not export-ready" in refused["result"]["error"]
    for evidence_id in evidence_ids:
        rc = main(
            [
                "project",
                "resolve-evidence",
                "--workspace",
                str(workspace),
                "project-alpha",
                "--evidence-id",
                evidence_id,
                "--decision",
                "accept",
                "--reason",
                "PI accepted fixture evidence",
                "--json",
            ]
        )
        resolved = json.loads(capsys.readouterr().out)
        assert rc == 0
        assert resolved["ok"] is True
        assert resolved["evidence_id"] == evidence_id
    rc = main(
        [
            "project",
            "verify",
            "--workspace",
            str(workspace),
            "project-alpha",
            "--json",
            "--idempotency-key",
            "project-verify-after-disposition",
        ]
    )
    verified_after_disposition = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert verified_after_disposition["ok"] is True
    assert verified_after_disposition["result"]["ready"] is True
    with state.connect(workspace) as conn:
        rows = conn.execute(
            """
            SELECT request_id, operation_id
            FROM operation_requests
            WHERE request_id IN (
              'project-compose',
              'project-verify',
              'project-export-draft',
              'project-verify-after-disposition'
            )
            ORDER BY request_id
            """
        ).fetchall()
    assert [(row["request_id"], row["operation_id"]) for row in rows] == [
        ("project-compose", "compose-project-draft"),
        ("project-export-draft", "export-project"),
        ("project-verify", "verify-project-draft"),
        ("project-verify-after-disposition", "verify-project-draft"),
    ]


def test_cli_project_resolve_evidence_verifies_current_draft_before_disposition(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    _write_project_argument_fixture(workspace)
    (workspace / "projects/project-alpha/outline.md").write_text(
        "- 01ARZ3NDEKTSV4RRFFQ69G5FA2 -- Support\n",
        encoding="utf-8",
    )
    assert (
        main(
            [
                "project",
                "compose",
                "--workspace",
                str(workspace),
                "project-alpha",
                "--json",
                "--idempotency-key",
                "compose-before-stale-resolution",
            ]
        )
        == 0
    )
    composed = json.loads(capsys.readouterr().out)
    old_id = composed["result"]["evidence_markers"][0]["id"]
    current_id = "ev-deadbeef"
    draft = workspace / "projects/project-alpha/draft.md"
    draft.write_text(
        draft.read_text(encoding="utf-8").replace(old_id, current_id),
        encoding="utf-8",
    )

    rc = main(
        [
            "project",
            "resolve-evidence",
            "--workspace",
            str(workspace),
            "project-alpha",
            "--evidence-id",
            current_id,
            "--decision",
            "accept",
            "--json",
            "--idempotency-key",
            "verify-before-stale-resolution",
        ]
    )
    resolved = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert resolved["ok"] is True
    assert resolved["evidence_id"] == current_id
    assert {row["id"] for row in state.evidence_sets(workspace)} == {current_id}
    with state.connect(workspace) as conn:
        verification = conn.execute(
            "SELECT operation_id, status FROM operation_requests WHERE request_id = ?",
            ("verify-before-stale-resolution",),
        ).fetchone()
    assert tuple(verification) == ("verify-project-draft", "done")


def test_cli_new_note_check_and_link_flow(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(
        [
            "new",
            "note",
            "Framing changes the question",
            "--workspace",
            str(workspace),
            "--body",
            "The source reframes the problem before measuring outcomes.",
            "--description",
            "A framing note.",
            "--tag",
            "framing",
            "--json",
            "--idempotency-key",
            "note-new",
            "--actor",
            "agent",
        ]
    )
    created = json.loads(capsys.readouterr().out)

    assert rc == 0
    note_path = created["path"]
    assert created["result"]["check_status"] == "unchecked"
    note_fm = read_frontmatter(workspace / note_path)
    assert note_fm["description"] == "A framing note."
    assert "check_status" not in note_fm
    assert state.concept_check_status(workspace, note_path) == "unchecked"
    with state.connect(workspace) as conn:
        request = conn.execute(
            "SELECT operation_id, actor, primary_target FROM operation_requests WHERE request_id = ?",
            ("note-new",),
        ).fetchone()
    assert tuple(request) == ("create-concept", "agent", note_path)

    assert main(["show", "--workspace", str(workspace), note_path, "--json"]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["check_status"] == "unchecked"
    assert shown["body_data"] == {
        "kind": "untrusted_text",
        "text": (
            "# Framing changes the question\n\n"
            "The source reframes the problem before measuring outcomes.\n"
        ),
    }
    assert (
        main(
            [
                "new",
                "note",
                "Framing changes the question",
                "--workspace",
                str(workspace),
                "--body",
                "The source reframes the problem before measuring outcomes.",
                "--description",
                "A framing note.",
                "--tag",
                "framing",
                "--json",
                "--idempotency-key",
                "note-new",
                "--actor",
                "agent",
            ]
        )
        == 0
    )
    repeated = json.loads(capsys.readouterr().out)
    assert repeated["path"] == note_path
    assert not (workspace / "notes/framing-changes-the-question-2.md").exists()

    assert (
        main(
            [
                "new",
                "note",
                "Framing changes the question",
                "--workspace",
                str(workspace),
                "--body",
                "The source reframes the problem before measuring outcomes.",
                "--description",
                "A framing note.",
                "--tag",
                "framing",
                "--json",
                "--idempotency-key",
                "note-new",
                "--actor",
                "pi",
            ]
        )
        == 2
    )
    conflict = json.loads(capsys.readouterr().out)
    assert conflict == {
        "ok": False,
        "error": "idempotency key is already bound to a different request",
    }

    assert (
        main(
            [
                "check",
                "--workspace",
                str(workspace),
                note_path,
                "--json",
                "--idempotency-key",
                "note-check",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert state.concept_check_status(workspace, note_path) == "checked"

    target = workspace / "notes/target.md"
    target.write_text(
        "---\ntype: note\ntitle: Target\ntags: []\nlinks: {}\n---\nTarget body.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "notes/target.md", "note")
    assert (
        main(
            [
                "link",
                "--workspace",
                str(workspace),
                note_path,
                "notes/target.md",
                "--rel",
                "supports",
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
    assert read_frontmatter(workspace / note_path)["links"] == {"supports": ["notes/target.md"]}


@pytest.mark.parametrize(
    ("argv", "request_id", "concept_type", "path_prefix", "expected_body"),
    [
        (
            [
                "new",
                "hub",
                "framing",
                "--title",
                "Framing Hub",
                "--description",
                "Frame work.",
                "--body",
                "Hub body from the concept contract.",
            ],
            "hub-new",
            "hub",
            "hubs/",
            "# Framing Hub\n\nHub body from the concept contract.\n",
        ),
        (
            [
                "new",
                "project",
                "Alpha Project",
                "--description",
                "Project brief.",
                "--direction",
                "Project direction from the concept contract.",
            ],
            "project-new",
            "project",
            "projects/",
            "# Alpha Project\n\nProject direction from the concept contract.\n",
        ),
    ],
)
def test_cli_new_hub_project_use_create_concept_request_boundary(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    request_id: str,
    concept_type: str,
    path_prefix: str,
    expected_body: str,
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(
        [
            *argv,
            "--workspace",
            str(workspace),
            "--json",
            "--idempotency-key",
            request_id,
            "--actor",
            "agent",
        ]
    )
    created = json.loads(capsys.readouterr().out)

    assert rc == 0
    concept_path = created["path"]
    assert concept_path.startswith(path_prefix)
    assert created["result"]["check_status"] == "unchecked"
    frontmatter = read_frontmatter(workspace / concept_path)
    assert frontmatter["type"] == concept_type
    assert "check_status" not in frontmatter
    assert (workspace / concept_path).read_text(encoding="utf-8").split("---\n", 2)[-1] == (
        expected_body
    )
    assert state.concept_check_status(workspace, concept_path) == "unchecked"
    with state.connect(workspace) as conn:
        request = conn.execute(
            "SELECT operation_id, actor, primary_target FROM operation_requests WHERE request_id = ?",
            (request_id,),
        ).fetchone()
    assert tuple(request) == ("create-concept", "agent", concept_path)


def test_cli_work_digest_blocks_checked_metadata_only_source(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "work",
                "add",
                "--workspace",
                str(workspace),
                "--doi",
                "10.1000/metadata",
                "--title",
                "Metadata only",
                "--json",
            ]
        )
        == 0
    )
    captured = json.loads(capsys.readouterr().out)
    work_id = captured["result"]["work_id"]
    assert captured["result"]["text_status"] == "metadata-only"
    with state.connect(workspace) as conn:
        conn.execute(
            "UPDATE catalog_sources SET check_status = 'checked' WHERE work_id = ?",
            (work_id,),
        )

    assert (
        main(
            [
                "work",
                "digest",
                "--workspace",
                str(workspace),
                work_id,
                "--json",
            ]
        )
        == 1
    )
    output = json.loads(capsys.readouterr().out)

    assert output["ok"] is False
    assert output["result"]["status"] == "failed"
    assert "checked digest requires full-text source content" in output["result"]["error"]
    assert "attention_path is inbox/flag-digest-full-text-" in output["result"]["error"]
    assert not (workspace / f"digests/{work_id}.md").exists()
    attention = workspace / f"inbox/flag-digest-full-text-{work_id}.md"
    assert read_frontmatter(attention)["target"] == f"catalog/sources/{work_id}"


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
                "references": [
                    {
                        "DOI": "10.1000/book.ref",
                        "title": "Referenced Book Work",
                    }
                ],
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
    assert output["result"]["work_id"] == "book2026"
    assert not (workspace / "catalog/sources/book2026/source.md").exists()
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT title, check_status, identifiers_json FROM catalog_sources WHERE work_id = ?",
            ("book2026",),
        ).fetchone()
        edge = conn.execute(
            """
            SELECT relation_type, target_id, target_title, target_doi, source_provider
            FROM work_graph_edges
            WHERE work_id = ?
            """,
            ("book2026",),
        ).fetchone()
        columns = {
            column["name"] for column in conn.execute("PRAGMA table_info(operation_requests)")
        }
    assert row["title"] == "Standalone Book"
    assert row["check_status"] == "unchecked"
    assert json.loads(row["identifiers_json"]) == {"isbn": "9780000000002"}
    assert tuple(edge) == (
        "references",
        "doi:10.1000/book.ref",
        "Referenced Book Work",
        "10.1000/book.ref",
        "import",
    )
    _assert_request_columns(columns)


def _write_project_argument_fixture(workspace: Path) -> None:
    project = workspace / "projects/project-alpha/project.md"
    project.parent.mkdir(parents=True, exist_ok=True)
    project.write_text(
        "---\n"
        "type: project\n"
        "check_status: checked\n"
        "title: Alpha project\n"
        "thesis: notes/thesis.md\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "projects/project-alpha/project.md", "project")
    notes = {
        "thesis": (
            "type: note\ncheck_status: checked\ntitle: Thesis\nstatus: accepted\n"
            "id: 01ARZ3NDEKTSV4RRFFQ69G5FA1\n"
        ),
        "support": (
            "type: note\ncheck_status: checked\ntitle: Support\nstatus: accepted\n"
            "id: 01ARZ3NDEKTSV4RRFFQ69G5FA2\n"
            "links:\n  supports:\n    - notes/thesis.md\n"
        ),
        "refute": (
            "type: note\ncheck_status: checked\ntitle: Refute\nstatus: accepted\n"
            "id: 01ARZ3NDEKTSV4RRFFQ69G5FA3\n"
            "links:\n  contradicts:\n    - notes/thesis.md\n"
        ),
    }
    for name, frontmatter in notes.items():
        note = workspace / f"notes/{name}.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(f"---\n{frontmatter}---\nBody.\n", encoding="utf-8")
        mark_file_status(workspace, f"notes/{name}.md", "note")


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
