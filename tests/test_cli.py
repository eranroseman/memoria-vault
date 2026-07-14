from __future__ import annotations

import argparse
import json
import tomllib
from pathlib import Path

import pytest

from memoria_vault import __version__
from memoria_vault.cli import _build_parser, main
from memoria_vault.engine.surface_contract import SURFACE_ACTIONS, actions_by_id
from memoria_vault.runtime import state
from memoria_vault.runtime.vaultio import read_frontmatter, split_frontmatter
from tests.cli_test_helpers import _cli_command_surface
from tests.helpers import ROOT, _assert_request_columns, git


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


def test_cli_command_surface_is_exact() -> None:
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
        "memoria journal verify",
        "memoria workspace scan",
        "memoria workspace run",
        "memoria workspace recover",
        "memoria workspace rollback",
        "memoria workspace check",
        "memoria workspace backup",
        "memoria workspace restore",
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


def test_cli_new_concept_fields_are_exposed_by_parser() -> None:
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
def test_memoria_new_commands_follow_cli_concept_contract(
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
def test_memoria_new_defaults_include_description_key(
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


def test_cli_init_seeds_obsidian_defaults_and_memoria_plugin(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"

    rc = main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    core_plugins = json.loads((workspace / ".obsidian/core-plugins.json").read_text("utf-8"))
    app = json.loads((workspace / ".obsidian/app.json").read_text("utf-8"))
    community_plugins = json.loads(
        (workspace / ".obsidian/community-plugins.json").read_text("utf-8")
    )
    manifest = json.loads(
        (workspace / ".obsidian/plugins/memoria-obsidian/manifest.json").read_text("utf-8")
    )

    assert rc == 0
    assert core_plugins["command-palette"] is True
    assert core_plugins["global-search"] is True
    assert core_plugins["backlink"] is True
    assert core_plugins["canvas"] is True
    assert core_plugins["bases"] is True
    assert core_plugins["properties"] is False
    assert core_plugins["daily-notes"] is False
    assert core_plugins["templates"] is False
    assert app["propertiesInDocument"] == "source"
    assert app["alwaysUpdateLinks"] is True
    assert community_plugins == ["memoria-obsidian"]
    assert manifest["id"] == "memoria-obsidian"
    assert (workspace / ".obsidian/plugins/memoria-obsidian/main.js").is_file()
    assert (workspace / ".obsidian/plugins/memoria-obsidian/schema.js").is_file()
    assert (workspace / ".obsidian/plugins/memoria-obsidian/styles.css").is_file()


def test_cli_init_no_obsidian_skips_obsidian_seed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    dry_workspace = tmp_path / "dry-workspace"

    rc = main(["init", "--workspace", str(workspace), "--yes", "--no-obsidian", "--json"])
    capsys.readouterr()

    assert rc == 0
    assert not (workspace / ".obsidian").exists()
    assert (workspace / ".memoria/schemas/folders.yaml").is_file()
    assert (workspace / "steering.md").is_file()

    rc = main(["init", "--workspace", str(dry_workspace), "--dry-run", "--no-obsidian", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert ".obsidian" not in output["package"]["seed_trees"]
    assert not dry_workspace.exists()


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
    assert ".memoria/index/search" in output["skeleton"]["missing"]
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
        ".memoria/locks/worker.lock",
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
        _assert_request_columns(columns)
    assert row["operation_id"] == "capture-source"
    assert json.loads(row["provenance_json"]) == {
        "command": "capture-source",
        "surface": "memoria-cli",
    }


def test_cli_migrate_from_alpha15_imports_current_root_contract(
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
