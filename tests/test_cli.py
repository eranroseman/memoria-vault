from __future__ import annotations

import json
import os
import sys
import tomllib
from pathlib import Path

import pytest

from memoria_vault.cli import _build_parser, main
from memoria_vault.runtime import state
from memoria_vault.runtime.trusted_writer import append_journal_event
from memoria_vault.runtime.vaultio import read_frontmatter
from memoria_vault.runtime.worker import enqueue_operation

ROOT = Path(__file__).resolve().parent.parent


def _assert_alpha14_request_columns(columns: set[str]) -> None:
    assert {
        "input_refs_json",
        "output_intents_json",
        "primary_target",
        "precondition_hashes_json",
    } <= columns
    assert {"trigger_type", "target_path", "target_hash"}.isdisjoint(columns)


def _cli_command_surface() -> set[str]:
    parser = _build_parser()
    command_action = next(
        action for action in parser._actions if getattr(action, "dest", None) == "command"
    )
    commands: set[str] = set()
    for name, subparser in command_action.choices.items():
        child_action = next(
            (action for action in subparser._actions if getattr(action, "choices", None)),
            None,
        )
        if child_action is None:
            commands.add(f"memoria {name}")
            continue
        if not getattr(child_action, "required", False):
            commands.add(f"memoria {name}")
        commands.update(f"memoria {name} {child}" for child in child_action.choices)
    return commands


def test_cli_help_imports_without_adapter_environment(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])

    assert exc.value.code == 0
    assert "memoria" in capsys.readouterr().out


def test_pyproject_exposes_memoria_console_script() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["scripts"]["memoria"] == "memoria_vault.cli:main"


def test_alpha14_cli_command_surface_is_exact() -> None:
    assert _cli_command_surface() == {
        "memoria init",
        "memoria status",
        "memoria doctor",
        "memoria doctor bundle",
        "memoria doctor self-test",
        "memoria ask",
        "memoria work capture",
        "memoria work import",
        "memoria work enrich",
        "memoria work digest",
        "memoria work interview",
        "memoria work update",
        "memoria note capture",
        "memoria note propose",
        "memoria note accept",
        "memoria note reject",
        "memoria note link",
        "memoria project ask",
        "memoria project trace",
        "memoria project gaps",
        "memoria project suggest-hubs",
        "memoria project export",
        "memoria request answer",
        "memoria request amend",
        "memoria request cancel",
        "memoria request retry",
        "memoria request resume",
        "memoria request list",
        "memoria request show",
        "memoria attention list",
        "memoria attention show",
        "memoria attention resolve",
        "memoria attention worklist",
        "memoria operation list",
        "memoria operation run",
        "memoria steering show",
        "memoria steering edit",
        "memoria vocabulary list",
        "memoria vocabulary add",
        "memoria vocabulary rename",
        "memoria journal list",
        "memoria journal show",
        "memoria workspace scan",
        "memoria workspace run",
        "memoria workspace recover",
        "memoria workspace rollback",
        "memoria workspace check",
        "memoria workspace rebuild",
        "memoria workspace export",
        "memoria eval run",
        "memoria eval seeded-error-verdict",
    }


def test_cli_init_dry_run_reports_runtime_setup_without_mutation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"

    rc = main(["init", "--workspace", str(workspace), "--dry-run", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["dry_run"] is True
    assert output["workspace"] == str(workspace)
    assert output["workspace_exists"] is False
    assert output["db"] == {"path": ".memoria/memoria.sqlite", "exists": False}
    assert "capabilities" in output["skeleton"]["directories"]
    assert ".memoria/index/qmd/checked" in output["skeleton"]["missing"]
    assert output["package"]["seed_files"] == ["steering.md", "system/vocabulary.md"]
    assert "capabilities" in output["package"]["seed_trees"]
    assert {
        "index.md",
        "catalog/index.md",
        "knowledge/index.md",
        "capabilities/index.md",
        "references.bib",
        "capabilities/_generated/capability-index.json",
    } <= set(output["generated_targets"])
    assert output["concepts"] == {
        "steering": "steering.md",
        "vocabulary": "system/vocabulary.md",
    }
    assert output["qmd"] == {
        "collection": "memoria-checked",
        "checked_root": ".memoria/index/qmd/checked",
        "config_dir": ".memoria/index/qmd/config",
        "index_path": ".memoria/index/qmd/index.sqlite",
        "mask": "**/*.md",
    }
    assert output["provider_config"] == {
        "path": ".memoria/config/providers.yaml",
        "seeded": True,
        "exists": False,
    }
    assert not workspace.exists()


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
    assert not (workspace / ".memoria/index/qmd/cache").exists()
    assert not (workspace / "catalog/sources/doi-10.1000_alpha/source.md").exists()
    assert (workspace / output["result"]["content_path"]).is_file()
    with state.connect(workspace) as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(operation_requests)")}
        row = conn.execute(
            "SELECT operation_id, provenance_json FROM operation_requests WHERE request_id = ?",
            ("capture-alpha",),
        ).fetchone()
    _assert_alpha14_request_columns(columns)
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
    assert output["enrichment_job"]["operation_id"] == "enrich-source"
    assert output["enrichment_job"]["status"] == "pending"
    assert not (workspace / "catalog/sources/doi-10.1000_import.2026/source.md").exists()
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT title, check_status, content_path FROM catalog_sources WHERE source_id = ?",
            ("doi-10.1000_import.2026",),
        ).fetchone()
        enrich = conn.execute(
            "SELECT operation_id, status FROM operation_requests WHERE request_id = ?",
            ("enrich-doi-10.1000_import.2026",),
        ).fetchone()
    assert tuple(row) == (
        "Alpha Import",
        "unchecked",
        output["result"]["content_path"],
    )
    assert tuple(enrich) == ("enrich-source", "pending")


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
    interview_fixture = tmp_path / "interview.json"
    interview_fixture.write_text(
        json.dumps(
            {
                "prompt": "What matters?",
                "response": "The PI cares about the methods caveat.",
                "project_id": "knowledge/projects/project-alpha.md",
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
                "capture",
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
    assert interview["result"]["source_id"] == "doi-10.1000_alpha"
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
    assert read_frontmatter(digest)["evidence_set"] == ["catalog/sources/doi-10.1000_alpha"]
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
    _assert_alpha14_request_columns(columns)
    assert row["operation_id"] == "analyze-gaps"
    assert json.loads(row["args_json"]) == {
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
                "supports",
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


def test_cli_note_propose_can_derive_candidate_from_work_digest(
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
        "title: Alpha source\n"
        "description: Alpha\n"
        "source_id: catalog/sources/source-alpha\n"
        "---\n"
        "## Synthesis\n\nFraming changes which outcomes matter.\n",
        encoding="utf-8",
    )

    rc = main(
        [
            "note",
            "propose",
            "--workspace",
            str(workspace),
            "--work-id",
            "source-alpha",
            "--json",
            "--idempotency-key",
            "note-propose-work",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    [note_path] = output["result"]["note_paths"]
    note = workspace / note_path
    note_fm = read_frontmatter(note)
    assert note_fm["check_status"] == "checked"
    assert note_fm["status"] == "candidate"
    assert note_fm["source_id"] == "catalog/sources/source-alpha"
    assert "Framing changes which outcomes matter." in note.read_text(encoding="utf-8")


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


def test_cli_operation_list_rejects_directory_only_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    asset_dir = workspace / "capabilities/operations/directory-only"
    asset_dir.mkdir()
    (asset_dir / "prompt.md").write_text("# Prompt\n", encoding="utf-8")

    rc = main(["operation", "list", "--workspace", str(workspace), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output["ok"] is False
    assert (
        output["error"] == "directory-only capability manifest is invalid: "
        "capabilities/operations/directory-only; "
        "expected sibling capabilities/operations/directory-only.md"
    )


def test_cli_workspace_run_reports_schedule_id_for_queue_drain(
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
        idempotency_key="pending-gaps",
    )

    rc = main(
        [
            "workspace",
            "run",
            "--workspace",
            str(workspace),
            "--schedule-id",
            "queue-drain",
            "--limit",
            "1",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["schedule_id"] == "queue-drain"
    assert output["ran"] == 1
    assert output["results"][0]["status"] == "done"


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
    assert shown["request"]["input_refs"] == []
    assert shown["request"]["output_intents"] == []
    assert shown["request"]["primary_target"] == ""
    assert shown["request"]["precondition_hashes"] == {}
    assert "target_path" not in shown["request"]
    assert "target_hash" not in shown["request"]

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


def test_cli_attention_list_show_worklist_and_resolve_projection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    attention = workspace / "inbox/flag-alpha.md"
    attention.parent.mkdir(parents=True, exist_ok=True)
    attention.write_text(
        "---\n"
        "title: Alpha flag\n"
        "projection: attention\n"
        "attention_kind: flag\n"
        "attention_status: open\n"
        "target: knowledge/notes/alpha.md\n"
        "---\n"
        "# Finding\n\nCheck this.\n",
        encoding="utf-8",
    )
    work_prompt = workspace / "inbox/work-alpha.md"
    work_prompt.write_text(
        "---\n"
        "title: Alpha work\n"
        "projection: attention\n"
        "attention_kind: work-prompt\n"
        "attention_status: open\n"
        "target: knowledge/projects/alpha.md\n"
        "---\n"
        "# Action\n\nWork this.\n",
        encoding="utf-8",
    )

    assert main(["attention", "list", "--workspace", str(workspace), "--json"]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert [row["path"] for row in listed["attention"]] == [
        "inbox/flag-alpha.md",
        "inbox/work-alpha.md",
    ]

    assert main(["attention", "worklist", "--workspace", str(workspace), "--json"]) == 0
    worklist = json.loads(capsys.readouterr().out)
    assert [row["path"] for row in worklist["attention"]] == ["inbox/work-alpha.md"]

    assert (
        main(
            [
                "attention",
                "show",
                "--workspace",
                str(workspace),
                "inbox/flag-alpha.md",
                "--json",
            ]
        )
        == 0
    )
    shown = json.loads(capsys.readouterr().out)
    assert shown["attention"]["frontmatter"]["title"] == "Alpha flag"
    assert "# Finding" in shown["attention"]["body"]

    rc = main(
        [
            "attention",
            "resolve",
            "--workspace",
            str(workspace),
            "inbox/flag-alpha.md",
            "--reason",
            "PI resolved",
            "--json",
            "--idempotency-key",
            "attention-resolve",
        ]
    )
    resolved = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert resolved["result"]["resolution"]["target_id"] == "inbox/flag-alpha.md"
    assert resolved["result"]["resolution"]["reason"] == "PI resolved"
    assert resolved["result"]["resolution"]["outcome"] == "resolved"
    fm = read_frontmatter(attention)
    assert fm["attention_status"] == "resolved"
    assert "resolved_at" in fm
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, args_json FROM operation_requests WHERE request_id = ?",
            ("attention-resolve",),
        ).fetchone()
    assert row["operation_id"] == "resolve-attention"
    assert json.loads(row["args_json"]) == {
        "target_id": "inbox/flag-alpha.md",
        "reason": "PI resolved",
        "outcome": "resolved",
    }

    rc = main(
        [
            "attention",
            "resolve",
            "--workspace",
            str(workspace),
            "inbox/work-alpha.md",
            "--outcome",
            "dismissed",
            "--json",
            "--idempotency-key",
            "attention-dismiss",
        ]
    )
    dismissed = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert dismissed["result"]["resolution"]["target_id"] == "inbox/work-alpha.md"
    assert dismissed["result"]["resolution"]["resolution"] == "resolved"
    assert dismissed["result"]["resolution"]["outcome"] == "dismissed"
    assert dismissed["result"]["resolution"]["reason"] == "PI dismissed attention"
    fm = read_frontmatter(work_prompt)
    assert fm["attention_status"] == "resolved"
    assert "resolved_at" in fm
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, args_json FROM operation_requests WHERE request_id = ?",
            ("attention-dismiss",),
        ).fetchone()
    assert row["operation_id"] == "resolve-attention"
    assert json.loads(row["args_json"]) == {
        "target_id": "inbox/work-alpha.md",
        "reason": "PI dismissed attention",
        "outcome": "dismissed",
    }


def test_cli_wires_alpha14_maintenance_and_pi_commands(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    zotero = tmp_path / "zotero.json"
    export_path = tmp_path / "workspace-export.json"
    zotero.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "key": "ZOT1",
                        "itemType": "journalArticle",
                        "title": "Zotero Exported Work",
                        "DOI": "10.1000/zotero",
                        "creators": [{"firstName": "Ada", "lastName": "River"}],
                        "abstractNote": "Portable Zotero JSON.",
                        "date": "2026",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    assert (workspace / "steering.md").is_file()
    assert (workspace / "system/vocabulary.md").is_file()
    assert (workspace / "index.md").is_file()
    assert (workspace / "references.bib").is_file()

    assert main(["doctor", "self-test", "--workspace", str(workspace), "--json"]) == 0
    self_test = json.loads(capsys.readouterr().out)
    assert self_test["checks"]["operation_catalog"] is True

    assert main(["doctor", "bundle", "--workspace", str(workspace), "--redacted", "--json"]) == 0
    bundle = json.loads(capsys.readouterr().out)
    assert bundle["redacted"] is True

    assert (
        main(
            [
                "work",
                "import",
                "--workspace",
                str(workspace),
                "--format",
                "zotero-export",
                "--file",
                str(zotero),
                "--json",
                "--idempotency-key",
                "import-zotero",
            ]
        )
        == 0
    )
    imported = json.loads(capsys.readouterr().out)
    assert imported["result"]["source_id"] == "ZOT1"

    assert (
        main(
            [
                "work",
                "update",
                "--workspace",
                str(workspace),
                "--work-id",
                "ZOT1",
                "--title",
                "Updated Zotero Work",
                "--standing",
                "archived",
                "--research-area",
                "personal-informatics",
                "--json",
                "--idempotency-key",
                "update-zotero",
            ]
        )
        == 0
    )
    updated = json.loads(capsys.readouterr().out)
    assert updated["result"]["work"]["title"] == "Updated Zotero Work"
    assert updated["result"]["work"]["csl_json"]["memoria"]["standing"] == "archived"
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, status FROM operation_requests WHERE request_id = ?",
            ("update-zotero",),
        ).fetchone()
    assert tuple(row) == ("update-work", "done")

    assert (
        main(
            [
                "note",
                "capture",
                "--workspace",
                str(workspace),
                "--title",
                "Captured PI note",
                "--body",
                "The PI captured this.",
                "--tag",
                "personal-informatics",
                "--json",
            ]
        )
        == 0
    )
    captured = json.loads(capsys.readouterr().out)
    assert read_frontmatter(workspace / captured["note_path"])["check_status"] == "unchecked"

    digest = workspace / "knowledge/digests/hub-seed.md"
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text(
        "---\n"
        "type: digest\n"
        "check_status: checked\n"
        "title: Hub seed\n"
        "description: Hub seed\n"
        "source_id: catalog/sources/ZOT1\n"
        "tags: [personal-informatics]\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    assert (
        main(
            [
                "project",
                "suggest-hubs",
                "--workspace",
                str(workspace),
                "--min-count",
                "1",
                "--json",
            ]
        )
        == 0
    )
    hubs = json.loads(capsys.readouterr().out)
    assert hubs["suggestions"] == [{"count": 1, "topic": "personal-informatics"}]

    enqueue_operation(
        workspace,
        "answer-query",
        payload={"query": "status", "k": 1},
        idempotency_key="recoverable-request",
    )
    assert (
        main(
            [
                "request",
                "answer",
                "--workspace",
                str(workspace),
                "recoverable-request",
                "note=ready",
                "--json",
            ]
        )
        == 0
    )
    answered = json.loads(capsys.readouterr().out)
    assert answered["request"]["args"]["answers"] == {"note": "ready"}

    assert (
        main(
            [
                "request",
                "amend",
                "--workspace",
                str(workspace),
                "recoverable-request",
                "k=3",
                "--json",
            ]
        )
        == 0
    )
    amended = json.loads(capsys.readouterr().out)
    assert amended["request"]["args"]["k"] == 3

    assert (
        main(
            [
                "request",
                "cancel",
                "--workspace",
                str(workspace),
                "recoverable-request",
                "--reason",
                "not needed",
                "--json",
            ]
        )
        == 0
    )
    cancelled = json.loads(capsys.readouterr().out)
    assert cancelled["request"]["status"] == "cancelled"

    assert (
        main(
            [
                "request",
                "list",
                "--workspace",
                str(workspace),
                "--status",
                "cancelled",
                "--json",
            ]
        )
        == 0
    )
    cancelled_list = json.loads(capsys.readouterr().out)
    assert [row["request_id"] for row in cancelled_list["requests"]] == ["recoverable-request"]

    assert (
        main(["request", "retry", "--workspace", str(workspace), "recoverable-request", "--json"])
        == 0
    )
    retried = json.loads(capsys.readouterr().out)
    assert retried["request"]["status"] == "pending"

    assert (
        main(["request", "retry", "--workspace", str(workspace), "recoverable-request", "--json"])
        == 2
    )
    retry_pending = json.loads(capsys.readouterr().out)
    assert retry_pending["ok"] is False
    assert "failed or cancelled" in retry_pending["error"]

    assert main(["steering", "show", "--workspace", str(workspace), "--json"]) == 0
    steering = json.loads(capsys.readouterr().out)
    assert steering["path"] == "steering.md"

    assert (
        main(
            [
                "steering",
                "edit",
                "--workspace",
                str(workspace),
                "--body",
                "# Steering\n\nUpdated.",
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert "Updated." in (workspace / "steering.md").read_text(encoding="utf-8")

    assert main(["vocabulary", "list", "--workspace", str(workspace), "--json"]) == 0
    vocabulary = json.loads(capsys.readouterr().out)
    assert "research_area" in vocabulary["vocabulary"]

    assert (
        main(
            [
                "vocabulary",
                "add",
                "--workspace",
                str(workspace),
                "research_area",
                "alpha-topic",
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert (
        main(
            [
                "vocabulary",
                "rename",
                "--workspace",
                str(workspace),
                "research_area",
                "alpha-topic",
                "beta-topic",
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert "beta-topic" in (workspace / "system/vocabulary.md").read_text(encoding="utf-8")

    assert main(["workspace", "scan", "--workspace", str(workspace), "--json"]) == 0
    scan = json.loads(capsys.readouterr().out)
    assert scan["result"]["observed_count"] == 1
    assert scan["result"]["paths"] == ["knowledge/digests/hub-seed.md"]

    assert (
        main(
            [
                "workspace",
                "check",
                "--workspace",
                str(workspace),
                "--schedule-id",
                "structural-check",
                "--json",
            ]
        )
        == 0
    )
    check = json.loads(capsys.readouterr().out)
    assert check["ok"] is True
    assert check["schedule_id"] == "structural-check"
    assert {job["request_envelope"]["schedule_id"] for job in check["jobs"]} == {"structural-check"}

    assert (
        main(
            [
                "workspace",
                "export",
                "--workspace",
                str(workspace),
                "--output",
                str(export_path),
                "--json",
            ]
        )
        == 0
    )
    exported = json.loads(capsys.readouterr().out)
    assert exported["export"]["output"] == str(export_path)
    assert export_path.is_file()

    assert main(["journal", "list", "--workspace", str(workspace), "--limit", "5", "--json"]) == 0
    journal = json.loads(capsys.readouterr().out)
    event_id = journal["events"][0]["event_id"]
    assert main(["journal", "show", "--workspace", str(workspace), str(event_id), "--json"]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["event"]["event_id"] == event_id


def test_cli_doctor_repair_restores_packaged_seed_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    operation = workspace / "capabilities/operations/compile-source-digest.md"
    provider_config = workspace / ".memoria/config/providers.yaml"
    template_operation = ROOT / "vault-template/capabilities/operations/compile-source-digest.md"
    template_provider_config = ROOT / "vault-template/.memoria/config/providers.yaml"
    operation.unlink()
    provider_config.write_text("broken: true\n", encoding="utf-8")

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["checks"]["state_db"] is True
    assert "capabilities" in output["repaired"]
    assert operation.read_text(encoding="utf-8") == template_operation.read_text(encoding="utf-8")
    assert provider_config.read_text(encoding="utf-8") == template_provider_config.read_text(
        encoding="utf-8"
    )


def test_cli_workspace_scan_fixture_quarantines_generated_projection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "workspace",
                "scan",
                "--workspace",
                str(workspace),
                "--fixture",
                "direct-write-generated-projection",
                "--json",
            ]
        )
        == 0
    )
    scan = json.loads(capsys.readouterr().out)

    assert scan["fixture"] == {
        "name": "direct-write-generated-projection",
        "path": "knowledge/index.md",
    }
    assert scan["quarantine"]["finding_count"] == 1
    assert scan["quarantine"]["findings"][0]["target_id"] == "knowledge/index.md"
    assert "knowledge/index.md" in scan["regeneration"]["changed"]
    assert scan["result"]["observed_count"] == 0
    assert (workspace / "knowledge/index.md").is_file()
    assert "direct-write-generated-projection fixture" not in (
        workspace / "knowledge/index.md"
    ).read_text(encoding="utf-8")
    assert (workspace / ".memoria/quarantine/knowledge/index.md").is_file()
    with state.connect(workspace) as conn:
        consumable = conn.execute(
            "SELECT output_id FROM consumable_outputs WHERE output_id = 'knowledge/index.md'"
        ).fetchone()
    assert consumable is None


def test_cli_workspace_recover_fixture_replays_pending_materialization(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    assert (
        main(
            [
                "workspace",
                "recover",
                "--workspace",
                str(workspace),
                "--fixture",
                "crash-before-materialization",
                "--json",
            ]
        )
        == 0
    )
    recovered = json.loads(capsys.readouterr().out)

    target = "knowledge/notes/crash-before-materialization.md"
    assert recovered["fixture"] == {"name": "crash-before-materialization", "path": target}
    assert recovered["restored"] == [target]
    assert read_frontmatter(workspace / target)["check_status"] == "checked"
    with state.connect(workspace) as conn:
        consumable = conn.execute(
            "SELECT output_id FROM consumable_outputs WHERE output_id = ?", (target,)
        ).fetchone()
    assert consumable["output_id"] == target


def test_cli_workspace_check_asserts_no_legacy_work_markdown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    legacy = workspace / "catalog/sources/old-work/source.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_text(
        "---\ntype: source\ncheck_status: checked\ntitle: Old Work\n---\nBody.\n",
        encoding="utf-8",
    )

    rc = main(
        [
            "workspace",
            "check",
            "--workspace",
            str(workspace),
            "--schedule-id",
            "legacy-work-gate",
            "--assert",
            "no-legacy-work-markdown",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert output["ok"] is False
    assert output["assertions"] == [
        {
            "assertion": "no-legacy-work-markdown",
            "ok": False,
            "findings": ["catalog/sources/old-work/source.md"],
        }
    ]


def test_cli_journal_list_operation_alias_includes_digest_workflow(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    append_journal_event(
        workspace,
        {"event": "run", "workflow": "compile-source-digest", "status": "done"},
        machine="memoria-cli",
    )
    append_journal_event(
        workspace,
        {"event": "run", "workflow": "regenerate-tracked-projections", "status": "done"},
        machine="memoria-cli",
    )

    assert (
        main(
            [
                "journal",
                "list",
                "--workspace",
                str(workspace),
                "--operation",
                "work.digest",
                "--json",
            ]
        )
        == 0
    )
    journal = json.loads(capsys.readouterr().out)

    assert [event["payload"]["workflow"] for event in journal["events"]] == [
        "compile-source-digest"
    ]


def test_cli_journal_list_filters_by_request_path_decision_and_date(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    alpha = append_journal_event(
        workspace,
        {
            "event": "policy",
            "operation": "check-source-metadata",
            "request_id": "req-alpha",
            "target_id": "knowledge/notes/alpha.md",
            "decision": "deny",
        },
        machine="memoria-cli",
    )
    append_journal_event(
        workspace,
        {
            "event": "policy",
            "operation": "check-source-metadata",
            "request_id": "req-beta",
            "target_id": "knowledge/notes/beta.md",
            "decision": "allow",
        },
        machine="memoria-cli",
    )

    assert (
        main(
            [
                "journal",
                "list",
                "--workspace",
                str(workspace),
                "--operation",
                "check-source-metadata",
                "--request-id",
                "req-alpha",
                "--path",
                "knowledge/notes/alpha.md",
                "--decision",
                "deny",
                "--date",
                alpha["timestamp"][:10],
                "--json",
            ]
        )
        == 0
    )
    journal = json.loads(capsys.readouterr().out)

    assert [event["payload"]["request_id"] for event in journal["events"]] == ["req-alpha"]


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

    assert (
        main(
            [
                "eval",
                "run",
                "--workspace",
                str(workspace),
                "--json",
                "--idempotency-key",
                "eval-run",
            ]
        )
        == 0
    )
    eval_run = json.loads(capsys.readouterr().out)
    assert eval_run["ok"] is True
    assert eval_run["result"]["operation_id"] == "eval-run"
    assert eval_run["result"]["outputs"] == ["system/eval/last-run.md"]
    assert eval_run["result"]["dry_run"] is False
    assert (workspace / "system/eval/last-run.md").is_file()


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
    _assert_alpha14_request_columns(columns)


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
    assert output["checks"]["qmd_collection"] is True
    assert output["checks"]["qmd_collection_root"] is True
    assert output["checks"]["qmd_collection_mask"] is True
    assert output["qmd_source"] == "npm-global"
    assert output["qmd_path"].startswith(str(tmp_path))


def test_cli_doctor_runner_constructs_local_pydantic_ai_agent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    seen = {}

    class FakeProvider:
        def __init__(self, **kwargs):
            seen["provider_kwargs"] = kwargs

    class FakeModel:
        def __init__(self, model_name, *, provider):
            seen["model_name"] = model_name
            seen["provider"] = provider

    class FakeAgent:
        def __init__(self, model):
            seen["model"] = model

    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    monkeypatch.setenv("MEMORIA_MODEL_BASE_URL", "http://127.0.0.1:11434/v1")
    monkeypatch.setenv("MEMORIA_MODEL", "local-test-model")
    monkeypatch.setattr(
        "memoria_vault.runtime.operations._load_pydantic_ai_openai",
        lambda: (FakeAgent, FakeModel, FakeProvider),
    )

    rc = main(
        [
            "doctor",
            "--workspace",
            str(workspace),
            "--check",
            "runner",
            "--provider",
            "local",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["provider"] == "local"
    assert output["base_url"] == "http://127.0.0.1:11434/v1"
    assert output["model"] == "local-test-model"
    assert output["checks"]["runner_dependency"] is True
    assert output["checks"]["runner_base_url"] is True
    assert output["checks"]["runner_agent_constructed"] is True
    assert seen["provider_kwargs"] == {"base_url": "http://127.0.0.1:11434/v1"}
    assert seen["model_name"] == "local-test-model"
    assert seen["model"] is not None


def test_cli_doctor_runner_uses_local_default_base_url(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    seen = {}

    class FakeProvider:
        def __init__(self, **kwargs):
            seen["provider_kwargs"] = kwargs

    class FakeModel:
        def __init__(self, model_name, *, provider):
            seen["model_name"] = model_name

    class FakeAgent:
        def __init__(self, model):
            seen["model"] = model

    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    for name in (
        "MEMORIA_MODEL_BASE_URL",
        "OPENAI_BASE_URL",
        "MEMORIA_MODEL_API_KEY",
        "OPENAI_API_KEY",
        "KILOCODE_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(
        "memoria_vault.runtime.operations._load_pydantic_ai_openai",
        lambda: (FakeAgent, FakeModel, FakeProvider),
    )

    rc = main(
        [
            "doctor",
            "--workspace",
            str(workspace),
            "--check",
            "runner",
            "--provider",
            "local",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["base_url"] == "http://127.0.0.1:11434/v1"
    assert output["checks"]["runner_base_url"] is True
    assert seen["provider_kwargs"] == {"base_url": "http://127.0.0.1:11434/v1"}
    assert seen["model_name"] == "doctor"


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
    assert output["qmd"]["index_path"] == f"{workspace}/.memoria/index/qmd/index.sqlite"
    assert output["qmd"]["cache_home"] == ""
    assert (workspace / ".memoria/index/qmd/checked/knowledge/notes/qmd.md").is_file()
    lines = qmd_log.read_text(encoding="utf-8").splitlines()
    qmd_env = f"{workspace}/.memoria/index/qmd/config|{workspace}/.memoria/index/qmd/index.sqlite|"
    assert lines == [
        f"doctor|{qmd_env}",
        f"collection remove memoria-checked|{qmd_env}",
        "collection add "
        f"{workspace}/.memoria/index/qmd/checked --name memoria-checked --mask **/*.md"
        f"|{qmd_env}",
        f"update|{qmd_env}",
        f"embed --chunk-strategy auto|{qmd_env}",
    ]


def test_cli_doctor_qmd_requires_embedding_models_for_required_qmd(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    _fake_qmd_toolchain(tmp_path, monkeypatch)
    monkeypatch.setenv("QMD_DOCTOR_OUTPUT", "model cache: missing 3/3")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(["doctor", "--workspace", str(workspace), "--check", "qmd", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert output["ok"] is False
    assert output["checks"]["qmd_doctor"] is True
    assert output["checks"]["qmd_embedding_models"] is False
    assert "model cache: missing" in output["qmd_doctor_output"]


def test_cli_doctor_qmd_rejects_wrong_collection_registration(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    _fake_qmd_toolchain(tmp_path, monkeypatch)
    monkeypatch.setenv("QMD_COLLECTION_PATH", str(tmp_path / "wrong"))
    monkeypatch.setenv("QMD_COLLECTION_MASK", "*.txt")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(["doctor", "--workspace", str(workspace), "--check", "qmd", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert output["ok"] is False
    assert output["checks"]["qmd_collection"] is True
    assert output["checks"]["qmd_collection_root"] is False
    assert output["checks"]["qmd_collection_mask"] is False
    assert "Pattern:  *.txt" in output["qmd_collection_output"]


def test_cli_doctor_qmd_rejects_ambiguous_path_binary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "node").write_text(f"#!{sys.executable}\nprint('v22.11.0')\n", encoding="utf-8")
    (bin_dir / "qmd").write_text(f"#!{sys.executable}\nprint('wrong qmd')\n", encoding="utf-8")
    (bin_dir / "node").chmod(0o755)
    (bin_dir / "qmd").chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(["doctor", "--workspace", str(workspace), "--check", "qmd", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert output["ok"] is False
    assert output["checks"]["qmd"] is False
    assert output["qmd_source"] == "path"
    assert "MEMORIA_QMD_BIN" in output["qmd_error"]


def test_cli_workspace_rebuild_ignores_missing_qmd_collection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    _fake_qmd_toolchain(tmp_path, monkeypatch)
    monkeypatch.setenv("QMD_REMOVE_MISSING", "1")
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    note = workspace / "knowledge/notes/qmd.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(
        "---\ntype: note\ncheck_status: checked\ntitle: qmd\n---\nalpha search\n",
        encoding="utf-8",
    )

    rc = main(["workspace", "rebuild", "--workspace", str(workspace), "--search", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True


def _fake_qmd_toolchain(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    npm_root = tmp_path / "npm-global"
    npm_bin = npm_root / "bin"
    npm_bin.mkdir(parents=True)
    qmd_log = tmp_path / "qmd.log"
    node = bin_dir / "node"
    node.write_text(f"#!{sys.executable}\nprint('v22.11.0')\n", encoding="utf-8")
    npm = bin_dir / "npm"
    npm.write_text(f"#!{sys.executable}\nprint({str(npm_root)!r})\n", encoding="utf-8")
    qmd = npm_bin / "qmd"
    qmd.write_text(
        f"#!{sys.executable}\n"
        "import os, pathlib, sys\n"
        "pathlib.Path(os.environ['QMD_LOG']).open('a', encoding='utf-8').write(\n"
        "    ' '.join(sys.argv[1:]) + '|' + os.environ.get('QMD_CONFIG_DIR', '')\n"
        "    + '|' + os.environ.get('INDEX_PATH', '')\n"
        "    + '|' + os.environ.get('XDG_CACHE_HOME', '') + '\\n'\n"
        ")\n"
        "if sys.argv[1:3] == ['collection', 'remove'] and os.environ.get('QMD_REMOVE_MISSING'):\n"
        "    print('Collection not found: memoria-checked', file=sys.stderr)\n"
        "    sys.exit(1)\n"
        "if sys.argv[1:] == ['collection', 'show', 'memoria-checked']:\n"
        "    root = pathlib.Path(os.environ['QMD_CONFIG_DIR']).parent / 'checked'\n"
        "    path = os.environ.get('QMD_COLLECTION_PATH', str(root))\n"
        "    mask = os.environ.get('QMD_COLLECTION_MASK', '**/*.md')\n"
        "    print('Collection: memoria-checked')\n"
        "    print(f'  Path:     {path}')\n"
        "    print(f'  Pattern:  {mask}')\n"
        "    sys.exit(0)\n"
        "if sys.argv[1:] == ['doctor']:\n"
        "    print(os.environ.get('QMD_DOCTOR_OUTPUT', 'model cache: ready'))\n",
        encoding="utf-8",
    )
    node.chmod(0o755)
    npm.chmod(0o755)
    qmd.chmod(0o755)
    monkeypatch.setenv("QMD_LOG", str(qmd_log))
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
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
