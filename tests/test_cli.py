from __future__ import annotations

import argparse
import json
import re
import tomllib
from pathlib import Path

import pytest

from memoria_vault import __version__
from memoria_vault.cli import NEW_CONCEPT_TEMPLATE_FIELDS, _build_parser, main
from memoria_vault.engine.surface_contract import SURFACE_ACTIONS, actions_by_id
from memoria_vault.runtime import state
from memoria_vault.runtime.trusted_writer import append_journal_event
from memoria_vault.runtime.vaultio import read_frontmatter, split_frontmatter
from memoria_vault.runtime.worker import enqueue_operation, enqueue_trusted_write
from tests.helpers import ROOT, git, mark_file_status, patch_pydantic_ai


def _assert_alpha16_request_columns(columns: set[str]) -> None:
    assert {
        "input_refs_json",
        "output_intents_json",
        "primary_target",
        "precondition_hashes_json",
    } <= columns
    assert {"trigger_type", "target_path", "target_hash"}.isdisjoint(columns)


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


def _parser_for_command(parser: argparse.ArgumentParser, command: str) -> argparse.ArgumentParser:
    parts = command.split()
    if not parts or parts[0] != parser.prog:
        raise AssertionError(f"command must start with {parser.prog}: {command}")
    current = parser
    for part in parts[1:]:
        sub = next(
            action for action in current._actions if isinstance(action, argparse._SubParsersAction)
        )
        current = sub.choices[part]
    return current


def _parser_dests(command: str) -> set[str]:
    parser = _parser_for_command(_build_parser(), command)
    return {
        str(action.dest)
        for action in parser._actions
        if action.dest not in {argparse.SUPPRESS, "help"}
    }


def _subparser_help(parser: argparse.ArgumentParser, command: str) -> str:
    parts = command.split()
    parent = _parser_for_command(parser, " ".join(parts[:-1]))
    sub = next(
        action for action in parent._actions if isinstance(action, argparse._SubParsersAction)
    )
    choice = next(action for action in sub._choices_actions if action.dest == parts[-1])
    return str(choice.help or "")


def test_cli_help_imports_without_adapter_environment(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])

    assert exc.value.code == 0
    assert "memoria" in capsys.readouterr().out


def test_cli_version_uses_source_package_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])

    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"memoria {__version__}"


def test_pyproject_exposes_memoria_console_script() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["scripts"]["memoria"] == "memoria_vault.cli:main"


def test_alpha17_cli_command_surface_is_exact() -> None:
    assert _cli_command_surface() == {
        "memoria init",
        "memoria status",
        "memoria surface schema",
        "memoria doctor",
        "memoria doctor bundle",
        "memoria doctor self-test",
        "memoria ask",
        "memoria serve",
        "memoria migrate",
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
        "memoria project slice",
        "memoria project compose",
        "memoria project verify",
        "memoria project resolve-evidence",
        "memoria project promote",
        "memoria project explore",
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


def test_cli_surface_schema_prints_contract_json(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["surface", "schema", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["surface_contract_version"] == "surface-contract.v1"
    assert {action["id"] for action in output["actions"]} >= {
        "status.read",
        "surface.schema",
    }


def test_cli_surface_schema_prints_contract_without_json(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["surface", "schema"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["surface_contract_version"] == "surface-contract.v1"


def test_cli_shared_surface_help_uses_registry_summaries() -> None:
    parser = _build_parser()
    actions = actions_by_id()

    for action in SURFACE_ACTIONS:
        cli = action.get("cli")
        if not isinstance(cli, dict):
            continue
        for command in cli.get("commands") or []:
            command_parser = _parser_for_command(parser, str(command))
            assert command_parser.description == actions[str(action["id"])]["summary"]


def test_cli_parent_help_exposes_shared_surface_summaries() -> None:
    parser = _build_parser()

    assert _subparser_help(parser, "memoria surface") == "Inspect Memoria surface contracts."
    assert (
        _subparser_help(parser, "memoria journal tail")
        == actions_by_id()["journal.list"]["summary"]
    )
    assert (
        _subparser_help(parser, "memoria journal show") == actions_by_id()["journal.get"]["summary"]
    )


def test_cli_new_template_contract_matches_shipped_templates() -> None:
    template_root = ROOT / "vault-template/.memoria/templates"

    assert {
        path.stem: set(re.findall(r"{{VALUE:([^}]+)}}", path.read_text(encoding="utf-8")))
        for path in sorted(template_root.glob("*.md"))
    } == {concept_type: set(fields) for concept_type, fields in NEW_CONCEPT_TEMPLATE_FIELDS.items()}


def test_cli_new_template_contract_fields_are_exposed_by_parser() -> None:
    assert _parser_dests("memoria new note") >= {"title", "description", "body", "file"}
    assert _parser_dests("memoria new hub") >= {"tag", "title", "description", "body"}
    assert _parser_dests("memoria new project") >= {"name", "description", "direction"}


@pytest.mark.parametrize(
    (
        "argv",
        "expected_type",
        "expected_title",
        "expected_frontmatter_keys",
        "expected_body",
    ),
    [
        (
            [
                "new",
                "note",
                "Template Note",
                "--description",
                "Note description.",
                "--body",
                "Note body.",
            ],
            "note",
            "Template Note",
            {"title", "type", "id", "description", "tags", "links"},
            "# Template Note\n\nNote body.\n",
        ),
        (
            [
                "new",
                "hub",
                "template-tag",
                "--title",
                "Template Hub",
                "--description",
                "Hub description.",
                "--body",
                "Hub body.",
            ],
            "hub",
            "Template Hub",
            {"title", "type", "id", "description", "tags", "links", "tag"},
            "# Template Hub\n\nHub body.\n",
        ),
        (
            [
                "new",
                "project",
                "Template Project",
                "--description",
                "Project description.",
                "--direction",
                "Project direction.",
            ],
            "project",
            "Template Project",
            {
                "title",
                "type",
                "id",
                "description",
                "tags",
                "links",
                "outcome_frame",
                "paper_plan",
            },
            "# Template Project\n\nProject direction.\n",
        ),
    ],
)
def test_memoria_new_commands_follow_shipped_template_contract(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    expected_type: str,
    expected_title: str,
    expected_frontmatter_keys: set[str],
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
            f"template-{expected_type}",
        ]
    )
    created = json.loads(capsys.readouterr().out)
    frontmatter, body = split_frontmatter((workspace / created["path"]).read_text(encoding="utf-8"))

    assert rc == 0
    assert set(frontmatter) >= expected_frontmatter_keys
    assert frontmatter["type"] == expected_type
    assert frontmatter["title"] == expected_title
    assert body == expected_body


@pytest.mark.parametrize(
    ("argv", "expected_type"),
    [
        (["new", "note", "Default Description Note", "--body", "Body."], "note"),
        (["new", "hub", "default-description-hub"], "hub"),
        (["new", "project", "Default Description Project"], "project"),
    ],
)
def test_memoria_new_defaults_include_template_description_key(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    expected_type: str,
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
            f"default-description-{expected_type}",
        ]
    )
    created = json.loads(capsys.readouterr().out)
    frontmatter = read_frontmatter(workspace / created["path"])

    assert rc == 0
    assert "description" in frontmatter
    assert frontmatter["description"] == ""


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
    assert ".memoria/index/search/checked" in output["skeleton"]["missing"]
    assert output["package"]["seed_files"] == [".gitignore", "steering.md", "system/vocabulary.md"]
    assert "capabilities" not in output["package"]["seed_trees"]
    assert {
        "index.md",
        "bibliography.bib",
    } <= set(output["generated_targets"])
    assert output["concepts"] == {
        "steering": "steering.md",
        "vocabulary": "system/vocabulary.md",
    }
    assert output["search"] == {
        "engine": "bm25",
        "checked_root": ".memoria/index/search/checked",
        "manifest": ".memoria/index/search/manifest.json",
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
    assert (workspace / "system/manifest.jsonl").read_text(encoding="utf-8") == ""
    assert git(
        workspace,
        "check-ignore",
        ".memoria/memoria.sqlite",
        ".memoria/config/providers.yaml",
        ".memoria/locks/worker.lock",
        ".memoria/schemas/folders.yaml",
        ".memoria/journal/test-machine.jsonl",
    ).splitlines() == [
        ".memoria/memoria.sqlite",
        ".memoria/config/providers.yaml",
        ".memoria/locks/worker.lock",
        ".memoria/schemas/folders.yaml",
        ".memoria/journal/test-machine.jsonl",
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
    assert output["result"]["work_id"] == "doi-10.1000_alpha"
    assert not (workspace / ".memoria/index/search/manifest.json").exists()
    assert not (workspace / "catalog/sources/doi-10.1000_alpha/source.md").exists()
    assert (workspace / output["result"]["content_path"]).is_file()
    with state.connect(workspace) as conn:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(operation_requests)")}
        row = conn.execute(
            "SELECT operation_id, provenance_json FROM operation_requests WHERE request_id = ?",
            ("capture-alpha",),
        ).fetchone()
        _assert_alpha16_request_columns(columns)
    assert row["operation_id"] == "capture-source"
    assert json.loads(row["provenance_json"]) == {
        "command": "capture-source",
        "surface": "memoria-cli",
    }


def test_cli_migrate_alpha15_imports_root_level_alpha16_contract(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    old = tmp_path / "old"
    old_note = old / "knowledge/notes/claim.md"
    old_hub = old / "knowledge/hubs/topic.md"
    old_project = old / "knowledge/projects/review.md"
    old_work = old / "knowledge/works/source-alpha.md"
    old_work.parent.mkdir(parents=True, exist_ok=True)
    old_note.parent.mkdir(parents=True, exist_ok=True)
    old_hub.parent.mkdir(parents=True, exist_ok=True)
    old_project.parent.mkdir(parents=True, exist_ok=True)
    old_work.write_text(
        "---\n"
        "type: work\n"
        "id: 01KBN6V6KX0000000000000001\n"
        "title: Alpha Source\n"
        "tags: [memory]\n"
        "links: {}\n"
        "work_id: source-alpha\n"
        "---\n"
        "Digest body.\n",
        encoding="utf-8",
    )
    old_note.write_text("---\ntype: note\ntitle: Claim\n---\nClaim body.\n", encoding="utf-8")
    old_hub.write_text("---\ntype: hub\ntitle: Topic\n---\nTopic body.\n", encoding="utf-8")
    old_project.write_text(
        "---\ntype: project\ntitle: Review\n---\nProject body.\n", encoding="utf-8"
    )
    (old / "references.bib").write_text("@article{alpha,title={Alpha}}\n", encoding="utf-8")

    workspace = tmp_path / "new"
    rc = main(
        [
            "migrate",
            "--workspace",
            str(workspace),
            "--from-alpha15",
            str(old),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["imported_count"] == 5
    assert (workspace / "notes/claim.md").is_file()
    assert (workspace / "hubs/topic.md").is_file()
    assert (workspace / "projects/review/project.md").is_file()
    assert (workspace / "bibliography.bib").read_text(encoding="utf-8") == (
        "@article{alpha,title={Alpha}}\n"
    )
    digest = read_frontmatter(workspace / "digests/source-alpha.md")
    assert digest["type"] == "digest"
    assert digest["work_id"] == "source-alpha"
    assert not (workspace / "works/source-alpha/record.md").exists()
    assert "Digest body." in (workspace / "digests/source-alpha.md").read_text(encoding="utf-8")


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
            "SELECT operation_id, status FROM operation_requests WHERE request_id = ?",
            ("enrich-doi-10.1000_import.2026",),
        ).fetchone()
    assert tuple(row) == (
        "Alpha Import",
        "unchecked",
        output["result"]["content_path"],
    )
    assert tuple(enrich) == ("enrich-source", "pending")


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
    _assert_alpha16_request_columns(columns)
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
                "--json",
                "--idempotency-key",
                "note-new",
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
                "Hub body from the template contract.",
            ],
            "hub-new",
            "hub",
            "hubs/",
            "# Framing Hub\n\nHub body from the template contract.\n",
        ),
        (
            [
                "new",
                "project",
                "Alpha Project",
                "--description",
                "Project brief.",
                "--direction",
                "Project direction from the template contract.",
            ],
            "project-new",
            "project",
            "projects/",
            "# Alpha Project\n\nProject direction from the template contract.\n",
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


def test_cli_operation_list_and_run_use_workspace_operation_concepts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    digest = workspace / "digests/source-alpha.md"
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text(
        "---\ntype: digest\ncheck_status: checked\ntitle: Alpha digest\ntags: [sleep]\n---\nBody.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "digests/source-alpha.md", "digest")

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
    digest = workspace / "digests/source-alpha.md"
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text(
        "---\ntype: digest\ncheck_status: checked\ntitle: Alpha digest\ntags: [sleep]\n---\nBody.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "digests/source-alpha.md", "digest")
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
        "notes/pi-scan.md",
        note,
        idempotency_key="write-pi-scan",
    )
    main(["workspace", "run", "--workspace", str(workspace), "--limit", "1", "--json"])
    capsys.readouterr()
    path = workspace / "notes/pi-scan.md"
    assert "check_status" not in read_frontmatter(path)
    assert state.concept_check_status(workspace, "notes/pi-scan.md") == "checked"

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
    assert scanned["needs_check_paths"] == ["notes/pi-scan.md"]
    assert scanned["result"]["observed_count"] == 1
    assert "check_status" not in read_frontmatter(path)
    assert state.concept_check_status(workspace, "notes/pi-scan.md") == "unchecked"
    with state.connect(workspace) as conn:
        row = conn.execute(
            "SELECT check_status FROM outputs WHERE output_id = ?",
            ("notes/pi-scan.md",),
        ).fetchone()
        consumable = conn.execute(
            "SELECT output_id FROM consumable_outputs WHERE output_id = ?",
            ("notes/pi-scan.md",),
        ).fetchone()
        event = conn.execute(
            """
            SELECT event_type
            FROM event_log
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
                '{"target_path": "notes/pi-scan.md"}',
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
    assert state.concept_check_status(workspace, "notes/pi-scan.md") == "checked"
    with state.connect(workspace) as conn:
        consumable = conn.execute(
            "SELECT output_id FROM consumable_outputs WHERE output_id = ?",
            ("notes/pi-scan.md",),
        ).fetchone()
    assert consumable["output_id"] == "notes/pi-scan.md"


def test_cli_request_list_show_and_resume_pending_request(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    digest = workspace / "digests/source-alpha.md"
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text(
        "---\ntype: digest\ncheck_status: checked\ntitle: Alpha digest\ntags: [sleep]\n---\nBody.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "digests/source-alpha.md", "digest")
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
        "notes/queued.md",
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
    assert cancelled["request"]["args"]["target_path"] == "notes/queued.md"
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
        "target: notes/alpha.md\n"
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
        "target: projects/alpha/project.md\n"
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


def test_cli_wires_alpha16_maintenance_and_pi_commands(
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
    assert (workspace / "bibliography.bib").is_file()

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
    assert imported["result"]["work_id"] == "portable-work"

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

    digest = workspace / "digests/hub-seed.md"
    digest.parent.mkdir(parents=True, exist_ok=True)
    digest.write_text(
        "---\n"
        "type: digest\n"
        "title: Hub seed\n"
        "description: Hub seed\n"
        "work_id: hub-seed\n"
        "work_id: catalog/sources/ZOT1\n"
        "tags: [personal-informatics]\n"
        "links: {}\n"
        "---\n"
        "Body.\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "digests/hub-seed.md", "digest")
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
    assert scan["result"]["paths"] == ["digests/hub-seed.md"]

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


def test_cli_doctor_reports_backup_contract(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    assert main(["doctor", "--workspace", str(workspace), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)

    assert report["ok"] is True
    assert report["backup"]["git_remote"]["configured"] is False
    assert report["backup"]["sqlite_replication"]["configured"] is False
    assert report["backup"]["sqlite_replication"]["runtime_dependency"] is False
    assert report["backup"]["blob_sync"]["configured"] is False
    assert report["backup"]["blob_sync"]["blob_root_exists"] is True

    git(workspace, "remote", "add", "origin", "https://example.invalid/memoria.git")
    (workspace / ".memoria/config/litestream.yaml").write_text("dbs: []\n", encoding="utf-8")
    (workspace / ".memoria/config/blob-sync.yaml").write_text("paths: []\n", encoding="utf-8")

    assert main(["doctor", "bundle", "--workspace", str(workspace), "--json"]) == 0
    bundle = json.loads(capsys.readouterr().out)

    assert bundle["backup"]["git_remote"] == {"configured": True, "remotes": ["origin"]}
    assert bundle["backup"]["sqlite_replication"]["configured"] is True
    assert bundle["backup"]["blob_sync"]["configured"] is True


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
        "path": "index.md",
    }
    assert scan["quarantine"]["finding_count"] == 1
    assert scan["quarantine"]["findings"][0]["target_id"] == "index.md"
    assert "index.md" in scan["regeneration"]["changed"]
    assert scan["result"]["observed_count"] == 0
    assert (workspace / "index.md").is_file()
    assert "direct-write-generated-projection fixture" not in (workspace / "index.md").read_text(
        encoding="utf-8"
    )
    assert (workspace / ".memoria/quarantine/index.md").is_file()
    with state.connect(workspace) as conn:
        consumable = conn.execute(
            "SELECT output_id FROM consumable_outputs WHERE output_id = 'index.md'"
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

    target = "notes/crash-before-materialization.md"
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
            "target_id": "notes/alpha.md",
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
            "target_id": "notes/beta.md",
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
                "notes/alpha.md",
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
    assert (workspace / ".memoria/eval/alpha15-seeded-errors.json").is_file()

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
        assert bundle_path == workspace / ".memoria/eval/alpha15-seeded-errors.json"
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
    assert eval_run["result"]["outputs"] == [".memoria/eval/last-run.md"]
    assert eval_run["result"]["dry_run"] is False
    assert (workspace / ".memoria/eval/last-run.md").is_file()


def test_cli_eval_select_models_requires_alpha15_seeded_bundle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    (workspace / ".memoria/eval/alpha15-seeded-errors.json").unlink()
    (workspace / ".memoria/eval/alpha12-seeded-errors.json").write_text("{}", encoding="utf-8")

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
    assert ".memoria/eval/alpha15-seeded-errors.json" in output["error"]


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
    assert calls[0]["bundle_path"] == workspace / ".memoria/eval/alpha15-seeded-errors.json"
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
    _assert_alpha16_request_columns(columns)


def test_cli_doctor_search_checks_workspace_local_state(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    rc = main(["doctor", "--workspace", str(workspace), "--check", "search", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 1
    assert output["ok"] is False
    assert output["search_engine"] == "bm25"
    assert output["search_manifest"] == ".memoria/index/search/manifest.json"
    assert output["search_document_count"] == 0
    assert output["checks"]["search_checked_root"] is True
    assert output["checks"]["search_manifest"] is False


def test_cli_doctor_runner_constructs_local_pydantic_ai_agent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    seen = {}

    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    monkeypatch.setenv("MEMORIA_MODEL_BASE_URL", "http://127.0.0.1:11434/v1")
    monkeypatch.setenv("MEMORIA_MODEL", "local-test-model")
    patch_pydantic_ai(monkeypatch, seen=seen)

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
    patch_pydantic_ai(monkeypatch, seen=seen)

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

    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    write_runner_provider_config(workspace)
    monkeypatch.setenv("MEMORIA_MODEL_BASE_URL", "http://model.test/v1")
    monkeypatch.setenv("MEMORIA_MODEL", "live-test-model")
    patch_pydantic_ai(monkeypatch, output="runner ok", seen=seen)

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


def test_cli_workspace_rebuild_writes_checked_search_index(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    note = workspace / "notes/search.md"
    note.parent.mkdir(parents=True, exist_ok=True)
    note.write_text(
        "---\ntype: note\ncheck_status: checked\ntitle: search\n---\nalpha search\n",
        encoding="utf-8",
    )
    mark_file_status(workspace, "notes/search.md", "note")

    rc = main(
        [
            "workspace",
            "rebuild",
            "--workspace",
            str(workspace),
            "--search",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["search"]["engine"] == "bm25"
    assert output["search"]["manifest"]["mode"] == "bm25"
    assert output["search"]["manifest"]["documents"][0]["path"] == "notes/search.md"
    assert (workspace / ".memoria/index/search/checked/notes/search.md").is_file()

    rc = main(["doctor", "--workspace", str(workspace), "--check", "search", "--json"])
    doctor = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert doctor["ok"] is True
    assert doctor["search_document_count"] == 1


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
