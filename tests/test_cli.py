from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from memoria_vault.cli import _build_parser, main
from memoria_vault.runtime import state
from memoria_vault.runtime.policy.audit import sha256_file
from memoria_vault.runtime.trusted_writer import append_journal_event
from memoria_vault.runtime.vaultio import read_frontmatter
from memoria_vault.runtime.worker import enqueue_operation, enqueue_trusted_write

ROOT = Path(__file__).resolve().parent.parent


def git(workspace: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=workspace,
        check=False,
        text=True,
        capture_output=True,
    )
    if proc.returncode:
        raise AssertionError(proc.stderr or proc.stdout)
    return proc.stdout.strip()


def _assert_alpha14_request_columns(columns: set[str]) -> None:
    assert {
        "input_refs_json",
        "output_intents_json",
        "primary_target",
        "precondition_hashes_json",
    } <= columns
    assert {"trigger_type", "target_path", "target_hash"}.isdisjoint(columns)


def mark_file_status(workspace: Path, rel: str, concept_type: str, status: str = "checked") -> None:
    state.record_observed_file_edit(
        workspace,
        output_id=rel,
        concept_type=concept_type,
        output_sha256=sha256_file(workspace / rel),
    )
    state.set_concept_verdict(workspace, rel, status)


def write_runner_provider_config(
    workspace: Path, *, local_url: str = "http://model.test/v1"
) -> None:
    config = workspace / ".memoria/config/providers.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        "\n".join(
            [
                "version: 1",
                "runner_providers:",
                f"  local: {{url: {local_url}, key_env: null}}",
                "  gateway: {url: https://gateway.test/v1, key_env: KILOCODE_API_KEY}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _cli_command_surface() -> set[str]:
    parser = _build_parser()
    command_action = next(
        action for action in parser._actions if getattr(action, "dest", None) == "command"
    )
    commands: set[str] = set()
    for name, subparser in command_action.choices.items():
        child_action = next(
            (
                action
                for action in subparser._actions
                if isinstance(action, argparse._SubParsersAction)
            ),
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


def test_alpha15_cli_command_surface_is_exact() -> None:
    assert _cli_command_surface() == {
        "memoria init",
        "memoria status",
        "memoria doctor",
        "memoria doctor bundle",
        "memoria doctor self-test",
        "memoria ask",
        "memoria serve",
        "memoria mcp",
        "memoria new hub",
        "memoria new note",
        "memoria new project",
        "memoria work add",
        "memoria work import",
        "memoria work enrich",
        "memoria work digest",
        "memoria work interview",
        "memoria work update",
        "memoria work export",
        "memoria link",
        "memoria check",
        "memoria show",
        "memoria list",
        "memoria export",
        "memoria project ask",
        "memoria project trace",
        "memoria project frame-paper",
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
        "memoria vocab list",
        "memoria vocab add",
        "memoria vocab merge",
        "memoria vocab rename",
        "memoria journal tail",
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
        "memoria eval select-models",
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
    assert "capabilities" not in output["skeleton"]["directories"]
    assert ".memoria/index/qmd/checked" in output["skeleton"]["missing"]
    assert output["package"]["seed_files"] == [".gitignore", "steering.md", "system/vocabulary.md"]
    assert "capabilities" not in output["package"]["seed_trees"]
    assert {
        "index.md",
        "catalog/index.md",
        "knowledge/index.md",
        "knowledge/_views/index.md",
        "references.bib",
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
    assert output["git"] == {
        "repo": ".git",
        "would_init": True,
        "journal_head": state.JOURNAL_HEAD_REL,
        "overrides": ".memoria/overrides.jsonl",
        "gitignore": ".gitignore",
    }
    assert not workspace.exists()


def test_cli_init_and_work_add_use_request_envelope_without_trigger_type(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"

    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    tracked = set(git(workspace, "ls-files").splitlines())
    assert state.JOURNAL_HEAD_REL in tracked
    assert ".memoria/overrides.jsonl" in tracked
    assert (workspace / state.JOURNAL_HEAD_REL).read_text(encoding="utf-8").strip() == "GENESIS"
    assert (workspace / ".memoria/overrides.jsonl").read_text(encoding="utf-8") == ""
    assert git(
        workspace,
        "check-ignore",
        ".memoria/memoria.sqlite",
        ".memoria/config/providers.yaml",
        ".memoria/locks/worker.lock",
        ".memoria/schemas/folders.yaml",
        "journal/test-machine.jsonl",
    ).splitlines() == [
        ".memoria/memoria.sqlite",
        ".memoria/config/providers.yaml",
        ".memoria/locks/worker.lock",
        ".memoria/schemas/folders.yaml",
        "journal/test-machine.jsonl",
    ]

    rc = main(
        [
            "work",
            "add",
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


def test_cli_work_add_file_stages_text_without_legacy_markdown(
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
    assert output["result"]["source_id"] == "work"
    assert not (workspace / "catalog/sources/work/source.md").exists()
    assert (workspace / output["result"]["content_path"]).read_text(encoding="utf-8") == (
        "Full text from the PI.\n"
    )


def test_cli_work_add_url_fetches_text_without_legacy_markdown(
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
    source_id = output["result"]["source_id"]
    assert output["result"]["check_status"] == "unchecked"
    assert not (workspace / f"catalog/sources/{source_id}/source.md").exists()
    assert "Fetched full text." in (workspace / output["result"]["content_path"]).read_text(
        encoding="utf-8"
    )


def test_cli_work_add_pdf_extracts_text_without_legacy_markdown(
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
    assert interview["result"]["source_id"] == "doi-10.1000_alpha"
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
    assert output["result"]["digest_path"] == "knowledge/works/doi-10.1000_alpha.md"
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
                "project_id": "knowledge/projects/project-alpha.md",
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
        "--topic",
        "framing",
        "--idempotency-key",
        "loop-update",
    )
    assert updated["result"]["work"]["csl_json"]["memoria"]["topics"] == ["framing"]
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
        "knowledge/notes/thesis.md",
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
        "works/doi-10.1000_alpha.md",
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
        "knowledge/projects/project-alpha.md"
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
    assert gaps["result"]["project_path"] == "knowledge/projects/project-alpha.md"
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
    assert recovered["restored"] == ["knowledge/notes/crash-before-materialization.md"]

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


def test_cli_project_gaps_runs_gap_analysis_request(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    digest = workspace / "knowledge/works/source-alpha.md"
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text(
        "---\n"
        "type: work\n"
        "title: Alpha digest\n"
        "work_id: source-alpha\n"
        "tags: [sleep]\n"
        "links: {}\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "knowledge/works/source-alpha.md", "work")
    state.upsert_catalog_record(
        workspace,
        source_id="db-alpha",
        title="DB Alpha",
        text_status="full-text",
        check_status="checked",
        csl_json={"memoria": {"topics": ["catalog-only"]}},
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
    assert output["result"]["project_path"] == "knowledge/projects/project-alpha.md"
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
    _assert_alpha14_request_columns(columns)
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
        "text": "The source reframes the problem before measuring outcomes.\n",
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
                "--json",
                "--idempotency-key",
                "note-new",
            ]
        )
        == 0
    )
    repeated = json.loads(capsys.readouterr().out)
    assert repeated["path"] == note_path
    assert not (workspace / "knowledge/notes/framing-changes-the-question-2.md").exists()

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

    target = workspace / "knowledge/notes/target.md"
    target.write_text(
        "---\ntype: note\ntitle: Target\ntags: []\nlinks: {}\n---\nTarget body.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "knowledge/notes/target.md", "note")
    assert (
        main(
            [
                "link",
                "--workspace",
                str(workspace),
                note_path,
                "knowledge/notes/target.md",
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
    assert read_frontmatter(workspace / note_path)["links"] == {
        "supports": ["knowledge/notes/target.md"]
    }


@pytest.mark.parametrize(
    ("argv", "request_id", "concept_type", "path_prefix"),
    [
        (
            ["new", "hub", "framing", "--title", "Framing Hub", "--description", "Frame work."],
            "hub-new",
            "hub",
            "knowledge/hubs/",
        ),
        (
            ["new", "project", "Alpha Project", "--description", "Project brief."],
            "project-new",
            "project",
            "knowledge/projects/",
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
    assert state.concept_check_status(workspace, concept_path) == "unchecked"
    with state.connect(workspace) as conn:
        request = conn.execute(
            "SELECT operation_id, actor, primary_target FROM operation_requests WHERE request_id = ?",
            (request_id,),
        ).fetchone()
    assert tuple(request) == ("create-concept", "agent", concept_path)


def test_cli_operation_list_and_run_use_workspace_operation_concepts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    digest = workspace / "knowledge/works/source-alpha.md"
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text(
        "---\ntype: work\ncheck_status: checked\ntitle: Alpha digest\ntags: [sleep]\n---\nBody.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "knowledge/works/source-alpha.md", "work")

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
            "--mode",
            "live",
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
    assert gaps["sleep"]["kind"] == "undigested"
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT args_json FROM operation_requests WHERE request_id = ?",
            ("operation-run-gaps",),
        ).fetchone()
    assert json.loads(row["args_json"])["mode"] == "live"
    assert gaps["sleep"]["score"] == 4
    assert gaps["new area"]["gap_type"] == "new-topic"
    assert output["result"]["summary"]["total"] == output["result"]["gap_count"]
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, args_json FROM operation_requests WHERE request_id = ?",
            ("operation-run-gaps",),
        ).fetchone()
    assert row["operation_id"] == "analyze-gaps"
    assert json.loads(row["args_json"]) == {
        "seed_terms": ["new area"],
        "dense_threshold": 1,
        "mode": "live",
    }


def test_cli_operation_list_ignores_workspace_capability_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    write_runner_provider_config(workspace)
    asset_dir = workspace / "capabilities/operations/directory-only"
    asset_dir.mkdir(parents=True)
    (asset_dir / "prompt.md").write_text("# Prompt\n", encoding="utf-8")

    rc = main(["operation", "list", "--workspace", str(workspace), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert "directory-only" not in {row["operation_id"] for row in output["operations"]}


def test_cli_workspace_run_reports_schedule_id_for_queue_drain(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    digest = workspace / "knowledge/works/source-alpha.md"
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text(
        "---\ntype: work\ncheck_status: checked\ntitle: Alpha digest\ntags: [sleep]\n---\nBody.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "knowledge/works/source-alpha.md", "work")
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


def test_cli_workspace_scan_reports_schedule_id_for_file_watch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(
        [
            "workspace",
            "scan",
            "--workspace",
            str(workspace),
            "--schedule-id",
            "file-watch",
            "--idempotency-key",
            "scheduled-scan",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["schedule_id"] == "file-watch"
    assert output["job"]["request_envelope"]["schedule_id"] == "file-watch"
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, schedule_id FROM operation_requests WHERE request_id = ?",
            ("scheduled-scan",),
        ).fetchone()
    assert tuple(row) == ("observe-pi-edits", "file-watch")


def test_cli_serve_watch_once_runs_file_watch_scan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(
        [
            "serve",
            "--workspace",
            str(workspace),
            "--watch",
            "--once",
            "--idempotency-key",
            "serve-watch-once",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["schedule_id"] == "file-watch"
    assert output["job"]["request_envelope"]["schedule_id"] == "file-watch"
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, schedule_id FROM operation_requests WHERE request_id = ?",
            ("serve-watch-once",),
        ).fetchone()
    assert tuple(row) == ("observe-pi-edits", "file-watch")


def test_cli_workspace_scan_marks_pi_edits_unchecked_until_promoted(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    note = "---\ntype: note\ntitle: PI scan note\ntags: []\nlinks: {}\n---\nOriginal.\n"
    enqueue_trusted_write(
        workspace,
        "knowledge/notes/pi-scan.md",
        note,
        idempotency_key="write-pi-scan",
    )
    main(["workspace", "run", "--workspace", str(workspace), "--limit", "1", "--json"])
    capsys.readouterr()
    path = workspace / "knowledge/notes/pi-scan.md"
    assert "check_status" not in read_frontmatter(path)
    assert state.concept_check_status(workspace, "knowledge/notes/pi-scan.md") == "checked"

    path.write_text(path.read_text(encoding="utf-8") + "\nPI edit.\n", encoding="utf-8")

    assert (
        main(
            [
                "workspace",
                "scan",
                "--workspace",
                str(workspace),
                "--idempotency-key",
                "scan-pi-edit",
                "--json",
            ]
        )
        == 0
    )
    scanned = json.loads(capsys.readouterr().out)

    assert scanned["needs_check_count"] == 1
    assert scanned["needs_check_paths"] == ["knowledge/notes/pi-scan.md"]
    assert scanned["result"]["observed_count"] == 1
    assert "check_status" not in read_frontmatter(path)
    assert state.concept_check_status(workspace, "knowledge/notes/pi-scan.md") == "unchecked"
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT check_status FROM outputs WHERE output_id = ?",
            ("knowledge/notes/pi-scan.md",),
        ).fetchone()
        consumable = conn.execute(
            "SELECT output_id FROM consumable_outputs WHERE output_id = ?",
            ("knowledge/notes/pi-scan.md",),
        ).fetchone()
        event = conn.execute(
            """
            SELECT event_type
            FROM journal_events
            WHERE event_type = 'observed_external_edit'
            ORDER BY event_id DESC
            LIMIT 1
            """
        ).fetchone()
    assert row["check_status"] == "unchecked"
    assert consumable is None
    assert event["event_type"] == "observed_external_edit"

    assert (
        main(
            [
                "operation",
                "run",
                "--workspace",
                str(workspace),
                "mark-checked",
                "--payload-json",
                '{"target_path": "knowledge/notes/pi-scan.md"}',
                "--idempotency-key",
                "mark-pi-scan",
                "--json",
            ]
        )
        == 0
    )
    promoted = json.loads(capsys.readouterr().out)

    assert promoted["ok"] is True
    assert promoted["result"]["check"]["status"] == "passed"
    assert "check_status" not in read_frontmatter(path)
    assert state.concept_check_status(workspace, "knowledge/notes/pi-scan.md") == "checked"
    with state.connect(workspace) as conn:
        consumable = conn.execute(
            "SELECT output_id FROM consumable_outputs WHERE output_id = ?",
            ("knowledge/notes/pi-scan.md",),
        ).fetchone()
    assert consumable["output_id"] == "knowledge/notes/pi-scan.md"


def test_cli_request_list_show_and_resume_pending_request(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    digest = workspace / "knowledge/works/source-alpha.md"
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text(
        "---\ntype: work\ncheck_status: checked\ntitle: Alpha digest\ntags: [sleep]\n---\nBody.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "knowledge/works/source-alpha.md", "work")
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


def test_cli_request_cancel_preserves_trusted_write_envelope_args(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    enqueue_trusted_write(
        workspace,
        "knowledge/notes/queued.md",
        "---\ntype: note\ntitle: Queued\ntags: []\nlinks: {}\n---\nBody.\n",
        idempotency_key="trusted-request",
    )

    assert (
        main(
            [
                "request",
                "cancel",
                "--workspace",
                str(workspace),
                "trusted-request",
                "--json",
            ]
        )
        == 0
    )
    cancelled = json.loads(capsys.readouterr().out)

    assert cancelled["request"]["status"] == "cancelled"
    assert cancelled["request"]["args"]["target_path"] == "knowledge/notes/queued.md"
    assert cancelled["request"]["job"]["request_envelope"]["args"] == cancelled["request"]["args"]


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
        "routing_class: ask\n"
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
        "routing_class: act\n"
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
            "--apply",
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
    assert resolved["result"]["resolution"]["outcome"] == "apply"
    assert resolved["result"]["resolution"]["resolution_outcome"] == "apply"
    assert resolved["result"]["resolution"]["routing_class"] == "ask"
    assert "decided_at" in resolved["result"]["resolution"]
    fm = read_frontmatter(attention)
    assert fm["attention_status"] == "resolved"
    assert fm["resolution_outcome"] == "apply"
    assert fm["routing_class"] == "ask"
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
        "outcome": "apply",
        "routing_class": "ask",
    }

    rc = main(
        [
            "attention",
            "resolve",
            "--workspace",
            str(workspace),
            "inbox/work-alpha.md",
            "--defer",
            "--json",
            "--idempotency-key",
            "attention-defer",
        ]
    )
    deferred = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert deferred["result"]["resolution"]["target_id"] == "inbox/work-alpha.md"
    assert deferred["result"]["resolution"]["resolution"] == "resolved"
    assert deferred["result"]["resolution"]["outcome"] == "defer"
    assert deferred["result"]["resolution"]["resolution_outcome"] == "defer"
    assert deferred["result"]["resolution"]["routing_class"] == "act"
    assert deferred["result"]["resolution"]["reason"] == "PI chose to defer attention"
    fm = read_frontmatter(work_prompt)
    assert fm["attention_status"] == "deferred"
    assert fm["resolution_outcome"] == "defer"
    assert fm["routing_class"] == "act"
    assert "resolved_at" in fm
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, args_json FROM operation_requests WHERE request_id = ?",
            ("attention-defer",),
        ).fetchone()
    assert row["operation_id"] == "resolve-attention"
    assert json.loads(row["args_json"]) == {
        "target_id": "inbox/work-alpha.md",
        "reason": "PI chose to defer attention",
        "outcome": "defer",
        "routing_class": "act",
    }


def test_cli_wires_alpha14_maintenance_and_pi_commands(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    csl_file = tmp_path / "portable-work.csl.json"
    export_path = tmp_path / "workspace-export.json"
    csl_file.write_text(
        json.dumps(
            {
                "id": "portable-work",
                "type": "article-journal",
                "title": "Portable Exported Work",
                "DOI": "10.1000/portable",
                "abstract": "Portable CSL JSON.",
                "author": [{"family": "River", "given": "Ada"}],
                "issued": {"date-parts": [[2026]]},
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
                "csl",
                "--file",
                str(csl_file),
                "--json",
                "--idempotency-key",
                "import-csl",
            ]
        )
        == 0
    )
    imported = json.loads(capsys.readouterr().out)
    assert imported["result"]["source_id"] == "portable-work"

    assert (
        main(
            [
                "work",
                "update",
                "--workspace",
                str(workspace),
                "portable-work",
                "--title",
                "Updated Portable Work",
                "--standing",
                "archived",
                "--research-area",
                "personal-informatics",
                "--json",
                "--idempotency-key",
                "update-portable",
            ]
        )
        == 0
    )
    updated = json.loads(capsys.readouterr().out)
    assert updated["result"]["work"]["title"] == "Updated Portable Work"
    assert updated["result"]["work"]["csl_json"]["memoria"]["standing"] == "archived"
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT operation_id, status FROM operation_requests WHERE request_id = ?",
            ("update-portable",),
        ).fetchone()
    assert tuple(row) == ("update-work", "done")

    assert (
        main(
            [
                "new",
                "note",
                "Captured PI note",
                "--workspace",
                str(workspace),
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
    assert "check_status" not in read_frontmatter(workspace / captured["path"])
    assert state.concept_check_status(workspace, captured["path"]) == "unchecked"

    digest = workspace / "knowledge/works/hub-seed.md"
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text(
        "---\n"
        "type: work\n"
        "title: Hub seed\n"
        "description: Hub seed\n"
        "work_id: hub-seed\n"
        "source_id: catalog/sources/ZOT1\n"
        "tags: [personal-informatics]\n"
        "links: {}\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "knowledge/works/hub-seed.md", "work")
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
    assert answered["request"]["job"]["request_envelope"]["args"] == answered["request"]["args"]

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
    assert amended["request"]["job"]["request_envelope"]["args"] == amended["request"]["args"]

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
    assert cancelled["request"]["job"]["request_envelope"]["args"] == cancelled["request"]["args"]

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
    assert retried["request"]["job"]["request_envelope"]["args"] == retried["request"]["args"]

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

    assert main(["vocab", "list", "--workspace", str(workspace), "--json"]) == 0
    vocabulary = json.loads(capsys.readouterr().out)
    assert "research_area" in vocabulary["vocabulary"]

    assert (
        main(
            [
                "vocab",
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
                "vocab",
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
    assert scan["result"]["paths"] == ["knowledge/works/hub-seed.md"]

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

    assert main(["journal", "tail", "--workspace", str(workspace), "--limit", "5", "--json"]) == 0
    journal = json.loads(capsys.readouterr().out)
    event_id = journal["events"][0]["event_id"]
    assert main(["journal", "show", "--workspace", str(workspace), str(event_id), "--json"]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert shown["event"]["event_id"] == event_id


def test_cli_doctor_repair_restores_runtime_seed_files(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    provider_config = workspace / ".memoria/config/providers.yaml"
    template_provider_config = ROOT / "vault-template/.memoria/config/providers.yaml"
    provider_config.write_text("broken: true\n", encoding="utf-8")

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["checks"]["state_db"] is True
    assert "capabilities" not in output["repaired"]
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
        "path": "knowledge/_views/index.md",
    }
    assert scan["quarantine"]["finding_count"] == 1
    assert scan["quarantine"]["findings"][0]["target_id"] == "knowledge/_views/index.md"
    assert "knowledge/_views/index.md" in scan["regeneration"]["changed"]
    assert scan["result"]["observed_count"] == 0
    assert (workspace / "knowledge/_views/index.md").is_file()
    assert "direct-write-generated-projection fixture" not in (
        workspace / "knowledge/_views/index.md"
    ).read_text(encoding="utf-8")
    assert (workspace / ".memoria/quarantine/knowledge/_views/index.md").is_file()
    with state.connect(workspace) as conn:
        consumable = conn.execute(
            "SELECT output_id FROM consumable_outputs WHERE output_id = 'knowledge/_views/index.md'"
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
    assert "check_status" not in read_frontmatter(workspace / target)
    assert state.concept_check_status(workspace, target) == "checked"
    with state.connect(workspace) as conn:
        consumable = conn.execute(
            "SELECT output_id FROM consumable_outputs WHERE output_id = ?", (target,)
        ).fetchone()
    assert consumable["output_id"] == target


def test_cli_workspace_recover_fails_running_requests_for_retry(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    job = enqueue_operation(
        workspace,
        "answer-query",
        payload={"query": "status"},
        idempotency_key="stuck-request",
    )
    state.set_request_running(workspace, "stuck-request", job)

    assert main(["workspace", "recover", "--workspace", str(workspace), "--json"]) == 0
    recovered = json.loads(capsys.readouterr().out)

    assert recovered["failed_requests"] == ["stuck-request"]
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT status, error FROM operation_requests WHERE request_id = ?",
            ("stuck-request",),
        ).fetchone()
    assert tuple(row) == ("failed", "interrupted during workspace recovery; retry required")

    assert main(["request", "retry", "--workspace", str(workspace), "stuck-request", "--json"]) == 0
    retried = json.loads(capsys.readouterr().out)
    assert retried["request"]["status"] == "pending"


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
                "tail",
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
    source_id = captured["result"]["source_id"]
    assert captured["result"]["text_status"] == "metadata-only"
    with state.connect(workspace) as conn:
        conn.execute(
            "UPDATE catalog_sources SET check_status = 'checked' WHERE source_id = ?",
            (source_id,),
        )

    assert (
        main(
            [
                "work",
                "digest",
                "--workspace",
                str(workspace),
                source_id,
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
    assert not (workspace / f"knowledge/works/{source_id}.md").exists()
    attention = workspace / f"inbox/flag-digest-full-text-{source_id}.md"
    assert read_frontmatter(attention)["target"] == f"catalog/sources/{source_id}"


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
                "tail",
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
    assert (workspace / "system/eval/alpha15-seeded-errors.json").is_file()

    def fake_verdict(
        vault: Path,
        *,
        template_root: Path,
        bundle_path: Path,
        runner: dict,
        operation_id: str,
        machine: str,
    ) -> dict[str, object]:
        assert vault != workspace
        assert template_root == workspace
        assert bundle_path == workspace / "system/eval/alpha15-seeded-errors.json"
        assert operation_id == "run-seeded-error-verdict"
        assert runner["mode"] == "live"
        assert runner["provider"] == "gateway"
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
            "--mode",
            "live",
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
    assert json.loads(row["args_json"]) == {"mode": "live"}

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


def test_cli_eval_select_models_requires_alpha15_seeded_bundle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    (workspace / "system/eval/alpha15-seeded-errors.json").unlink()
    (workspace / "system/eval/alpha12-seeded-errors.json").write_text("{}", encoding="utf-8")

    rc = main(
        [
            "eval",
            "select-models",
            "--workspace",
            str(workspace),
            "--operation",
            "run-seeded-error-verdict",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert "system/eval/alpha15-seeded-errors.json" in output["error"]


def test_cli_eval_select_models_selects_manifest_runner(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    calls = []

    def fake_verdict(
        vault: Path,
        *,
        template_root: Path,
        bundle_path: Path,
        runner: dict,
        operation_id: str,
        machine: str,
    ) -> dict[str, object]:
        calls.append(
            {
                "vault": vault,
                "template_root": template_root,
                "bundle_path": bundle_path,
                "runner": runner,
                "operation_id": operation_id,
                "machine": machine,
            }
        )
        return {
            "passed": True,
            "bar_failures": [],
            "verdict_key": "sha256:pass",
            "non_sandbox_licensed": True,
        }

    monkeypatch.setattr(
        "memoria_vault.runtime.seeded_errors.run_seeded_error_verdict",
        fake_verdict,
    )

    rc = main(
        [
            "eval",
            "select-models",
            "--workspace",
            str(workspace),
            "--operation",
            "run-seeded-error-verdict",
            "--mode",
            "live",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["selection_count"] == 1
    assert output["failed_count"] == 0
    assert output["selection"]["candidate_count"] == 1
    assert output["selection"]["candidate_source"] == "operation_manifest_runner"
    assert output["selection"]["selected"]["mode"] == "live"
    assert output["selection"]["selected"]["provider"] == "gateway"
    assert output["selection"]["selected"]["model"] == "deterministic-fixture"
    assert output["selection"]["non_sandbox_licensed"] is True
    assert calls[0]["vault"] != workspace
    assert calls[0]["template_root"] == workspace
    assert calls[0]["bundle_path"] == workspace / "system/eval/alpha15-seeded-errors.json"
    assert calls[0]["operation_id"] == "run-seeded-error-verdict"
    assert calls[0]["machine"] == "memoria-cli"


def test_cli_eval_select_models_refuses_failed_candidate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    monkeypatch.setattr(
        "memoria_vault.runtime.seeded_errors.run_seeded_error_verdict",
        lambda *args, **kwargs: {
            "passed": False,
            "bar_failures": ["recall"],
            "verdict_key": "sha256:fail",
            "non_sandbox_licensed": False,
        },
    )

    rc = main(
        [
            "eval",
            "select-models",
            "--workspace",
            str(workspace),
            "--operation",
            "run-seeded-error-verdict",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert output["ok"] is False
    assert output["selection_count"] == 0
    assert output["failed_count"] == 1
    assert output["selection"]["selected"] is None
    assert output["selection"]["attention_required"] is True
    assert output["selection"]["bar_failures"] == ["recall"]


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
    assert output["result"]["source_id"] == "book2026"
    assert not (workspace / "catalog/sources/book2026/source.md").exists()
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT title, check_status, identifiers_json FROM catalog_sources WHERE source_id = ?",
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


def test_cli_doctor_runner_live_dispatches_through_pydantic_ai(
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

    class FakeResult:
        output = "runner ok"

    class FakeAgent:
        def __init__(self, model):
            seen.setdefault("models", []).append(model)

        def run_sync(self, prompt, *, model_settings):
            seen["prompt"] = prompt
            seen["model_settings"] = model_settings
            return FakeResult()

    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    write_runner_provider_config(workspace)
    monkeypatch.setenv("MEMORIA_MODEL_BASE_URL", "http://model.test/v1")
    monkeypatch.setenv("MEMORIA_MODEL", "live-test-model")
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
            "--live",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["checks"]["runner_live_dispatch"] is True
    assert seen["provider_kwargs"] == {"base_url": "http://model.test/v1"}
    assert seen["model_name"] == "live-test-model"
    assert len(seen["models"]) == 2
    assert "Memoria runner is reachable" in seen["prompt"]
    assert seen["model_settings"]["temperature"] == 0


def test_cli_doctor_live_requires_runner_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(["doctor", "--workspace", str(workspace), "--live", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output["ok"] is False
    assert output["error"] == "doctor --live is only valid with --check runner"


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
    mark_file_status(workspace, "knowledge/notes/qmd.md", "note")

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
    assert output["qmd"]["manifest"]["mode"] == "hybrid"
    assert output["qmd"]["manifest"]["embeddings"] is True
    assert output["qmd"]["manifest"]["qmd_commands"][-1] == "qmd embed --chunk-strategy auto"
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
    state.set_concept_verdict(workspace, "knowledge/notes/qmd.md", "checked")

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
    mark_file_status(workspace, "knowledge/projects/project-alpha.md", "project")
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
        mark_file_status(workspace, f"knowledge/notes/{name}.md", "note")


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
