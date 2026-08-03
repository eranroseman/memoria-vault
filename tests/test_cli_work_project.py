from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.cli import _build_parser, main
from memoria_vault.runtime import state
from memoria_vault.runtime.vaultio import read_frontmatter, split_frontmatter
from memoria_vault.runtime.vocabulary.edges import LINK_RELATIONS
from tests.helpers import _assert_request_columns, set_concept_verdict

pytestmark = pytest.mark.contract


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
            "--enrich",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["entries_total"] == 1
    assert output["admitted"] == ["doi-10.1000_import.2026"]
    assert len(output["enrichment_jobs"]) == 1
    assert not (workspace / "catalog/sources/doi-10.1000_import.2026/source.md").exists()
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT title, check_status, content_path FROM catalog_sources WHERE work_id = ?",
            ("doi-10.1000_import.2026",),
        ).fetchone()
        enrich = conn.execute(
            "SELECT operation_id, status, actor FROM operation_requests WHERE request_id = ?",
            (output["enrichment_jobs"][0],),
        ).fetchone()
    assert tuple(row) == (
        "Alpha Import",
        "unchecked",
        ".memoria/blobs/source-content/doi-10.1000_import.2026/content.txt",
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
    set_concept_verdict(workspace, "digests/source-alpha.md", "digest")
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
    assert gaps["catalog-only"]["kind"] == "undigested"
    assert gaps["catalog-only"]["kind"] == "undigested"
    assert gaps["catalog-only"]["why"]
    assert gaps["catalog-only"]["next_actions"]
    assert gaps["catalog-only"]["source_count"] == 1
    assert gaps["sleep"]["kind"] == "undigested"
    assert gaps["new area"]["kind"] == "new-topic"
    assert output["result"]["project_path"] == "projects/project-alpha/project.md"
    assert output["result"]["argument_gap_count"] == 2
    assert output["result"]["summary"]["total"] == output["result"]["gap_count"]
    assert output["result"]["saturation"]["claims"] == 1
    assert output["result"]["saturation"]["ready"] is True
    assert {
        gap["finding_kind"]
        for gap in output["result"]["gaps"]
        if gap["kind"].startswith("argument-")
    } == {"thin-argument", "conflict"}
    assert {
        gap["kind"] for gap in output["result"]["gaps"] if gap["kind"].startswith("argument-")
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
    blocked = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert blocked["ok"] is False
    assert "project is not export-ready" in blocked["result"]["error"]
    assert not (workspace / "exports/project-alpha.md").exists()

    rc = main(
        [
            "project",
            "export",
            "--workspace",
            str(workspace),
            "project-alpha",
            "--allow-not-ready",
            "--format",
            "markdown",
            "--output",
            "exports/project-alpha.md",
            "--json",
            "--idempotency-key",
            "project-export-allow-not-ready",
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
    assert result["retrieval_backend"] == "bm25"
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


def test_cli_project_resolve_evidence_supports_defer_and_edit(
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
                "compose-for-dispositions",
            ]
        )
        == 0
    )
    composed = json.loads(capsys.readouterr().out)
    evidence_id = composed["result"]["evidence_markers"][0]["id"]

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
            "defer",
            "--reason",
            "revisit tomorrow",
            "--json",
            "--idempotency-key",
            "verify-for-defer",
        ]
    )
    deferred = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert deferred["ok"] is True
    assert deferred["decision"] == "defer"
    assert deferred["event"]["suppressed_until"].endswith("T00:00:00Z")

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
            "edit",
            "--json",
            "--idempotency-key",
            "verify-for-edit",
        ]
    )
    edited = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert edited["event"]["edit_target"]["draft_path"] == "projects/project-alpha/draft.md"


def test_cli_project_resolve_evidence_accept_carries_warrant(
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
                "compose-for-warrant",
            ]
        )
        == 0
    )
    composed = json.loads(capsys.readouterr().out)
    evidence_id = composed["result"]["evidence_markers"][0]["id"]

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
            "reviewed",
            "--warrant",
            "Spans jointly entail the claim.",
            "--json",
            "--idempotency-key",
            "verify-for-warrant",
        ]
    )
    accepted = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert accepted["ok"] is True
    assert accepted["event"]["warrant"] == "Spans jointly entail the claim."


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
    set_concept_verdict(workspace, "notes/target.md", "note")
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
    assert output["entries_total"] == 1
    assert output["admitted"] == ["book2026"]
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
    set_concept_verdict(workspace, "projects/project-alpha/project.md", "project")
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
        set_concept_verdict(workspace, f"notes/{name}.md", "note")


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


THREE_ENTRY_BIB = """@article{alpha2026,
  title = {Alpha Import},
  doi = {10.1000/alpha.2026},
  abstract = {First fixture entry.}
}

@article{beta2026,
  title = {Beta Import},
  doi = {10.1000/beta.2026},
  abstract = {Second fixture entry.}
}

@article{gamma2026,
  title = {Gamma Import},
  doi = {10.1000/gamma.2026},
  abstract = {Third fixture entry.}
}
"""


def _bulk_import(workspace: Path, source: Path, *extra: str) -> list[str]:
    return [
        "work",
        "import",
        "--workspace",
        str(workspace),
        "--format",
        "bibtex",
        "--file",
        str(source),
        "--json",
        *extra,
    ]


def test_cli_work_import_bulk_admits_every_entry_with_run_scoped_keys(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    bib = tmp_path / "sources.bib"
    bib.write_text(THREE_ENTRY_BIB, encoding="utf-8")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(_bulk_import(workspace, bib, "--idempotency-key", "caller-key"))
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["entries_total"] == 3
    assert out["ok"] is True
    assert out["format"] == "bibtex"
    assert out["admitted"] == [
        "doi-10.1000_alpha.2026",
        "doi-10.1000_beta.2026",
        "doi-10.1000_gamma.2026",
    ]
    assert out["skipped"] == []
    assert out["failed"] == []
    run_id = out["run_id"]
    assert len(run_id) == 32 and set(run_id) <= set("0123456789abcdef")
    assert out["enrichment_jobs"] == []
    assert out["index_refresh_s"] > 0.0
    for work_id in out["admitted"]:
        assert state.catalog_source(workspace, work_id) is not None
    with state.connect(workspace) as conn:
        capture_ids = [
            row[0]
            for row in conn.execute(
                "SELECT request_id FROM operation_requests WHERE operation_id = 'capture-source'"
            )
        ]
        enrich_count = conn.execute(
            "SELECT COUNT(*) FROM operation_requests WHERE operation_id = 'enrich-source'"
        ).fetchone()[0]
    assert len(capture_ids) == 3
    assert all(request_id.startswith(f"import-{run_id}-") for request_id in capture_ids)
    assert all("caller-key" not in request_id for request_id in capture_ids)
    assert enrich_count == 0


def test_cli_work_import_bulk_ignores_at_signs_in_external_comments(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    bib = tmp_path / "sources.bib"
    bib.write_text("% contact: user@example.org\n" + THREE_ENTRY_BIB, encoding="utf-8")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(_bulk_import(workspace, bib))
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["entries_total"] == 3
    assert out["failed"] == []
    assert out["admitted"] == [
        "doi-10.1000_alpha.2026",
        "doi-10.1000_beta.2026",
        "doi-10.1000_gamma.2026",
    ]


def test_cli_work_import_bulk_rerun_skips_admitted_rows_without_new_requests(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    bib = tmp_path / "sources.bib"
    bib.write_text(THREE_ENTRY_BIB, encoding="utf-8")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    main(_bulk_import(workspace, bib))
    capsys.readouterr()

    rc = main(_bulk_import(workspace, bib))
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["entries_total"] == 3
    assert out["ok"] is True
    assert out["admitted"] == []
    assert out["skipped"] == [
        "doi-10.1000_alpha.2026",
        "doi-10.1000_beta.2026",
        "doi-10.1000_gamma.2026",
    ]
    assert out["failed"] == []
    with state.connect(workspace) as conn:
        captures = conn.execute(
            "SELECT COUNT(*) FROM operation_requests WHERE operation_id = 'capture-source'"
        ).fetchone()[0]
    assert captures == 3  # resume = the pre-check: no fetch, no enqueue, no journal event


def test_cli_work_import_default_leaves_enrichment_unqueued(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    bibtex = tmp_path / "source.bib"
    bibtex.write_text(
        """@article{alpha2026,
  title = {Alpha Import},
  doi = {10.1000/alpha.2026},
  abstract = {Keyless-first single entry.}
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
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["entries_total"] == 1
    assert output["enrichment_jobs"] == []
    assert output["index_refresh_s"] > 0.0
    with state.connect(workspace) as conn:
        pending = conn.execute(
            "SELECT COUNT(*) FROM operation_requests WHERE operation_id = 'enrich-source'"
        ).fetchone()[0]
    assert pending == 0


def test_cli_work_import_single_enrich_does_not_requeue_existing_doi(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    bibtex = tmp_path / "source.bib"
    bibtex.write_text(
        """@article{alpha2026,
  title = {Alpha Import},
  doi = {10.1000/alpha.2026}
}
""",
        encoding="utf-8",
    )
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    first = _bulk_import(workspace, bibtex, "--enrich", "--idempotency-key", "first-import")
    assert main(first) == 0
    first_out = json.loads(capsys.readouterr().out)
    assert len(first_out["enrichment_jobs"]) == 1

    retry = _bulk_import(workspace, bibtex, "--enrich", "--idempotency-key", "retry-import")
    assert main(retry) == 0
    retry_out = json.loads(capsys.readouterr().out)
    assert retry_out["enrichment_jobs"] == []
    with state.connect(workspace) as conn:
        enrich = conn.execute(
            "SELECT COUNT(*) FROM operation_requests WHERE operation_id = 'enrich-source'"
        ).fetchone()[0]
    assert enrich == 1


def test_cli_work_import_bulk_enrich_flag_queues_once_per_admitted_doi_work(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    bib = tmp_path / "sources.bib"
    bib.write_text(THREE_ENTRY_BIB, encoding="utf-8")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(_bulk_import(workspace, bib, "--enrich"))
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert len(out["enrichment_jobs"]) == 3
    assert out["index_refresh_s"] > 0.0
    assert (workspace / ".memoria/index/search/manifest.json").is_file()
    with state.connect(workspace) as conn:
        enrich = conn.execute(
            "SELECT COUNT(*) FROM operation_requests WHERE operation_id = 'enrich-source'"
        ).fetchone()[0]
    assert enrich == 3

    rc = main(_bulk_import(workspace, bib, "--enrich"))
    out2 = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out2["skipped"] == out["admitted"]
    assert out2["enrichment_jobs"] == []
    assert out2["index_refresh_s"] == 0.0
    with state.connect(workspace) as conn:
        enrich = conn.execute(
            "SELECT COUNT(*) FROM operation_requests WHERE operation_id = 'enrich-source'"
        ).fetchone()[0]
    assert enrich == 3


def test_cli_work_import_bulk_names_failed_entries_and_continues(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    bib = tmp_path / "sources.bib"
    bib.write_text(
        """@article{alpha2026,
  title = {Alpha Import},
  doi = {10.1000/alpha.2026}
}

@article{broken2026,
  title {Missing Equals}
}

@article{gamma2026,
  title = {Gamma Import},
  doi = {10.1000/gamma.2026}
}
""",
        encoding="utf-8",
    )
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(_bulk_import(workspace, bib))
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["entries_total"] == 3
    assert out["ok"] is True
    assert out["admitted"] == ["doi-10.1000_alpha.2026", "doi-10.1000_gamma.2026"]
    assert len(out["failed"]) == 1
    assert out["failed"][0]["ref"] == "broken2026"
    assert "missing =" in out["failed"][0]["error"]


def test_cli_work_import_bulk_reports_precheck_errors_and_continues(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    bib = tmp_path / "sources.bib"
    bib.write_text(
        """@article{alpha2026,
  title = {Alpha Import},
  doi = {10.1000/alpha.2026}
}

@article{../bad,
  title = {Invalid Work ID}
}

@article{gamma2026,
  title = {Gamma Import},
  doi = {10.1000/gamma.2026}
}
""",
        encoding="utf-8",
    )
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(_bulk_import(workspace, bib))
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["admitted"] == ["doi-10.1000_alpha.2026", "doi-10.1000_gamma.2026"]
    assert out["skipped"] == []
    assert out["failed"] == [{"ref": "../bad", "error": "path escapes vault root: '../bad'"}]


def test_cli_work_import_bulk_fails_only_when_zero_rows_are_present(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    bib = tmp_path / "sources.bib"
    bib.write_text(
        """@article{brokenone2026,
  title {Missing Equals One}
}

@article{brokentwo2026,
  title {Missing Equals Two}
}
""",
        encoding="utf-8",
    )
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(_bulk_import(workspace, bib))
    out = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert out["ok"] is False
    assert out["admitted"] == [] and out["skipped"] == []
    assert [row["ref"] for row in out["failed"]] == ["brokenone2026", "brokentwo2026"]


def test_cli_work_import_bulk_same_doi_pair_collapses_to_one_row(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Spec section 5: same DOI => same work_id => structural dedupe through the
    # section 2 skip path. Reported skipped, never a judgment row.
    workspace = tmp_path / "workspace"
    bib = tmp_path / "sources.bib"
    bib.write_text(
        """@article{alpha2026,
  title = {Alpha Import},
  doi = {10.1000/alpha.2026}
}

@article{alphadup2026,
  title = {Alpha Import, Second Citekey},
  doi = {10.1000/alpha.2026}
}
""",
        encoding="utf-8",
    )
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(_bulk_import(workspace, bib))
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["entries_total"] == 2
    assert out["admitted"] == ["doi-10.1000_alpha.2026"]
    assert out["skipped"] == ["doi-10.1000_alpha.2026"]
    assert out["failed"] == []


def test_cli_work_import_bulk_csl_array_admits_each_item(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    csl = tmp_path / "sources.csl.json"
    csl.write_text(
        json.dumps(
            [
                {"id": "alpha-csl", "type": "article-journal", "title": "Alpha CSL"},
                {"id": "beta-csl", "type": "book", "title": "Beta CSL"},
            ]
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
        ]
    )
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["entries_total"] == 2
    assert out["ok"] is True
    assert out["admitted"] == ["alpha-csl", "beta-csl"]


@pytest.mark.parametrize(
    "text",
    [
        "42",
        "[42]",
    ],
)
def test_cli_work_import_invalid_csl_reports_one_failed_bulk_row(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], text: str
) -> None:
    workspace = tmp_path / "workspace"
    csl = tmp_path / "invalid.csl.json"
    csl.write_text(text, encoding="utf-8")
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
        ]
    )
    out = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert out["ok"] is False
    assert out["entries_total"] == 1
    assert out["admitted"] == []
    assert out["skipped"] == []
    assert out["failed"] == [{"ref": "entry-1", "error": "CSL entry must be a JSON object"}]


@pytest.mark.parametrize(
    ("fmt", "contents", "filename"),
    [("bibtex", "", "empty.bib"), ("csl", "[]", "empty.csl.json")],
)
def test_cli_work_import_bulk_empty_input_reports_zero_rows(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    fmt: str,
    contents: str,
    filename: str,
) -> None:
    workspace = tmp_path / "workspace"
    source = tmp_path / filename
    source.write_text(contents, encoding="utf-8")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(
        [
            "work",
            "import",
            "--workspace",
            str(workspace),
            "--format",
            fmt,
            "--file",
            str(source),
            "--json",
        ]
    )
    out = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert out["ok"] is False
    assert out["entries_total"] == 0
    assert out["admitted"] == []
    assert out["skipped"] == []
    with state.connect(workspace) as conn:
        captures = conn.execute(
            "SELECT COUNT(*) FROM operation_requests WHERE operation_id = 'capture-source'"
        ).fetchone()[0]
    assert captures == 0


def test_cli_link_offers_every_served_relation_and_refuses_tension() -> None:
    """`--rel` choices are the served roster: all six parse, `tension` is not offered."""
    for relation in sorted(LINK_RELATIONS):
        parsed = _build_parser().parse_args(
            [
                "link",
                "--workspace",
                "/tmp/disposable-vault",
                "notes/source.md",
                "notes/target.md",
                "--rel",
                relation,
            ]
        )
        assert parsed.rel == relation

    with pytest.raises(SystemExit) as exc:
        _build_parser().parse_args(
            [
                "link",
                "--workspace",
                "/tmp/disposable-vault",
                "notes/source.md",
                "notes/target.md",
                "--rel",
                "tension",
            ]
        )

    assert exc.value.code == 2


# --- O2 I.1: the composed bulk driver (adapters + duplicates + run artifacts) ---

ARXIV_SHARED = "2411.14199v1"
ARXIV_MISSING = "9999.99999"
ARXIV_UNMAPPED = "2501.00001"

IMPORT_CSL_ITEMS: list[dict[str, object]] = [
    # mapped, no synthesizable fetch -> capture-source
    {"id": "alpha-csl", "type": "article-journal", "title": "Alpha", "DOI": "10.9000/alpha"},
    # mapped article + arXiv -> capture-remote-pdf-source
    {
        "id": "beta-csl",
        "type": "article-journal",
        "title": "Beta",
        "DOI": "10.9000/beta",
        "arXiv": ARXIV_SHARED,
    },
    # same arXiv id as beta, different DOI -> admitted, cross-identifier duplicate row
    {
        "id": "gamma-csl",
        "type": "article-journal",
        "title": "Gamma",
        "DOI": "10.9000/gamma",
        "arXiv": ARXIV_SHARED,
    },
    # type outside the shipped vocabulary -> admitted as article, unmapped row. It also
    # carries a resolvable arXiv id: the guessed type must NOT make it an eligible PDF
    # row, which is the only thing that distinguishes the mapped flag at the router.
    {
        "id": "delta-csl",
        "type": "song",
        "title": "Delta",
        "DOI": "10.9000/delta",
        "arXiv": ARXIV_UNMAPPED,
    },
    # alpha's DOI under a different CSL id -> catalog doi UNIQUE failure + duplicate row
    {"id": "epsilon-csl", "type": "article-journal", "title": "Epsilon", "DOI": "10.9000/alpha"},
    # eligible remote PDF whose fetch refuses -> named failed row, later entries unaffected
    {
        "id": "zeta-csl",
        "type": "article-journal",
        "title": "Zeta",
        "DOI": "10.9000/zeta",
        "arXiv": ARXIV_MISSING,
    },
]


def _offline_remote_pdf(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Replay the one allowed arXiv PDF; refuse the missing one. No network."""
    import io

    opened: list[str] = []

    def fixture_opener(url: str) -> io.BytesIO:
        opened.append(url)
        if ARXIV_MISSING in url:
            raise ValueError(f"remote PDF fetch refused: {url}")
        return io.BytesIO(b"%PDF-1.4 fixture\n")

    monkeypatch.setattr("memoria_vault.runtime.seed_install._default_opener", fixture_opener)
    monkeypatch.setattr(
        "memoria_vault.runtime.capture._extract_pdf_pages",
        lambda _raw: [{"page": 1, "text": "A remote PDF evidence block."}],
    )
    return opened


def _csl_import(workspace: Path, source: Path, *extra: str) -> list[str]:
    return [
        "work",
        "import",
        "--workspace",
        str(workspace),
        "--format",
        "csl",
        "--file",
        str(source),
        "--json",
        *extra,
    ]


def _worklist_rows(workspace: Path, worklist_id: str) -> list[dict[str, object]]:
    rows = []
    for path in sorted((workspace / "system" / "worklists" / worklist_id).glob("*.md")):
        frontmatter, body = split_frontmatter(path.read_text(encoding="utf-8"))
        rows.append({**frontmatter, "body": body})
    return sorted(rows, key=lambda row: int(row["rank"]))


def _import_cards(workspace: Path) -> list[dict[str, object]]:
    return [
        frontmatter
        for path in sorted((workspace / "inbox").glob("work-prompt-*.md"))
        if (frontmatter := read_frontmatter(path)).get("raised_by") == "import"
    ]


def _import_run_events(workspace: Path) -> list[dict[str, object]]:
    with state.connect(workspace) as conn:
        rows = conn.execute(
            "SELECT payload_json FROM telemetry_events WHERE event_type = 'import-run.v1'"
            " ORDER BY ts, rowid"
        ).fetchall()
    return [json.loads(row["payload_json"]) for row in rows]


def test_cli_work_import_composes_adapters_duplicates_and_one_run_artifact_set(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    csl = tmp_path / "sources.csl.json"
    csl.write_text(json.dumps(IMPORT_CSL_ITEMS), encoding="utf-8")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    opened = _offline_remote_pdf(monkeypatch)

    rc = main(_csl_import(workspace, csl))
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert out["ok"] is True
    assert out["entries_total"] == 6
    assert out["admitted"] == ["alpha-csl", "beta-csl", "gamma-csl", "delta-csl"]
    assert out["skipped"] == []
    assert [row["ref"] for row in out["failed"]] == ["epsilon-csl", "zeta-csl"]
    assert "catalog_sources.doi" in out["failed"][0]["error"]
    assert ARXIV_MISSING in out["failed"][1]["error"]
    assert out["duplicates_flagged"] == 2

    # Routing, per entry rather than in aggregate: an unmapped type never becomes an
    # eligible PDF row even when its identifiers would resolve one.
    run_id = out["run_id"]
    with state.connect(workspace) as conn:
        routes = {
            row["request_id"].removeprefix(f"import-{run_id}-"): row["operation_id"]
            for row in conn.execute(
                "SELECT request_id, operation_id FROM operation_requests WHERE request_id LIKE ?",
                (f"import-{run_id}-%",),
            )
        }
    assert routes == {
        "alpha-csl": "capture-source",
        "beta-csl": "capture-remote-pdf-source",
        "gamma-csl": "capture-remote-pdf-source",
        "delta-csl": "capture-source",
        "epsilon-csl": "capture-source",
        "zeta-csl": "capture-remote-pdf-source",
    }
    # The CLI itself never fetched -- the worker's injected opener did, once per
    # routed row and never for the metadata-only ones.
    assert opened == [
        f"https://export.arxiv.org/pdf/{ARXIV_SHARED}",
        f"https://export.arxiv.org/pdf/{ARXIV_SHARED}",
        f"https://export.arxiv.org/pdf/{ARXIV_MISSING}",
    ]

    # Normalization is stamped on the admitted row, not merely computed.
    assert state.catalog_source(workspace, "delta-csl")["item_type"] == "article"

    # One ranked worklist: duplicates, then failed, then unmapped.
    assert out["worklist"] == f"import-{run_id}"
    rows = _worklist_rows(workspace, out["worklist"])
    assert [(row["rank"], row["group"], row["item_ref"]) for row in rows] == [
        (1, "duplicate", "gamma-csl"),
        (2, "duplicate", "epsilon-csl"),
        (3, "failed", "zeta-csl"),
        (4, "unmapped", "delta-csl"),
    ]
    # A duplicate row names which identifier matched which admitted work; a failed
    # row carries the worker's own error, not a generic label.
    assert "arxiv matches admitted work beta-csl" in str(rows[0]["body"])
    assert "catalog_sources.doi" in str(rows[1]["body"])
    assert ARXIV_MISSING in str(rows[2]["body"])
    assert "'song' is outside the shipped vocabulary" in str(rows[3]["body"])

    # One quiet card for the batch, never one per entry.
    cards = _import_cards(workspace)
    assert len(cards) == 1
    assert cards[0]["loudness"] == "quiet"
    for denominator in ("6 entries", "4 admitted", "4 need judgment"):
        assert denominator in str(cards[0]["title"])

    # Exactly one nine-field telemetry row for this run.
    (event,) = _import_run_events(workspace)
    assert event["run_id"] == run_id
    assert event["format"] == "csl"
    assert event["entries_total"] == 6
    assert event["admitted"] == 4
    assert event["skipped"] == 0
    assert event["failed"] == 2
    assert event["duplicates_flagged"] == 2
    assert event["duration_s"] > 0.0
    assert event["index_refresh_s"] > 0.0
    assert set(event) == {
        "run_id",
        "format",
        "entries_total",
        "admitted",
        "skipped",
        "failed",
        "duplicates_flagged",
        "duration_s",
        "index_refresh_s",
    }


def test_cli_work_import_rerun_mints_a_new_run_whose_artifacts_describe_the_rerun(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # Idempotent re-import: admitted works are skipped, so the retry's worklist and
    # telemetry row must describe the retry -- not replay the first run's judgment.
    workspace = tmp_path / "workspace"
    csl = tmp_path / "sources.csl.json"
    csl.write_text(json.dumps(IMPORT_CSL_ITEMS), encoding="utf-8")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    _offline_remote_pdf(monkeypatch)
    main(_csl_import(workspace, csl))
    first = json.loads(capsys.readouterr().out)

    rc = main(_csl_import(workspace, csl))
    second = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert second["run_id"] != first["run_id"]
    assert second["admitted"] == []
    assert second["skipped"] == ["alpha-csl", "beta-csl", "gamma-csl", "delta-csl"]
    assert [row["ref"] for row in second["failed"]] == ["epsilon-csl", "zeta-csl"]
    assert second["duplicates_flagged"] == 1
    assert second["index_refresh_s"] == 0.0

    # A skip is never a judgment row: the retry's worklist holds only the two rows
    # that still need judgment, and the first run's four are untouched.
    assert [
        (row["rank"], row["group"], row["item_ref"])
        for row in _worklist_rows(workspace, second["worklist"])
    ] == [(1, "duplicate", "epsilon-csl"), (2, "failed", "zeta-csl")]
    assert len(_worklist_rows(workspace, first["worklist"])) == 4
    assert len(_import_cards(workspace)) == 2

    events = _import_run_events(workspace)
    assert [event["run_id"] for event in events] == [first["run_id"], second["run_id"]]
    assert events[1]["admitted"] == 0
    assert events[1]["skipped"] == 4
    assert events[1]["failed"] == 2
    assert events[1]["duplicates_flagged"] == 1
    assert events[1]["index_refresh_s"] == 0.0


def test_cli_work_import_clean_run_mints_no_worklist_and_no_card(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Zero judgment rows: no worklist, no card, still exactly one telemetry row.
    workspace = tmp_path / "workspace"
    bib = tmp_path / "sources.bib"
    bib.write_text(THREE_ENTRY_BIB, encoding="utf-8")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(_bulk_import(workspace, bib))
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert len(out["admitted"]) == 3
    assert out["worklist"] == ""
    assert out["duplicates_flagged"] == 0
    assert not (workspace / "system" / "worklists").exists()
    assert _import_cards(workspace) == []
    (event,) = _import_run_events(workspace)
    assert event["format"] == "bibtex"
    assert (event["admitted"], event["skipped"], event["failed"]) == (3, 0, 0)
    assert event["duplicates_flagged"] == 0


def test_cli_work_import_enrich_finalizes_at_return_with_children_still_queued(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # The #1517 obligation: the driver finalizes at command return. The queued
    # enrich-source children have not run, so the run contributes zero retraction
    # rows and the telemetry row carries no retraction field.
    workspace = tmp_path / "workspace"
    csl = tmp_path / "sources.csl.json"
    csl.write_text(json.dumps(IMPORT_CSL_ITEMS), encoding="utf-8")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    _offline_remote_pdf(monkeypatch)

    rc = main(_csl_import(workspace, csl, "--enrich"))
    out = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert len(out["enrichment_jobs"]) == 4
    with state.connect(workspace) as conn:
        pending = conn.execute(
            "SELECT COUNT(*) FROM operation_requests"
            " WHERE operation_id = 'enrich-source' AND status = 'pending'"
        ).fetchone()[0]
    assert pending == 4

    (event,) = _import_run_events(workspace)
    assert "retraction_flags" not in event
    rows = _worklist_rows(workspace, out["worklist"])
    assert {str(row["group"]) for row in rows} == {"duplicate", "failed", "unmapped"}
