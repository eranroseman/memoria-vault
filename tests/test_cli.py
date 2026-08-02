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
from tests.helpers import ROOT, WORKSPACE_SEED, _assert_request_columns, git, write_checked_concept


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


def _job_console_blocks(out: str) -> dict[str, list[str]]:
    blocks: dict[str, list[str]] = {}
    current: str | None = None
    for line in out.splitlines():
        if line.endswith(":") and not line.startswith(" "):
            current = line[:-1]
            blocks[current] = []
        elif current is not None and line.strip():
            blocks[current].append(line.strip())
    return blocks


def test_cli_help_imports_without_adapter_environment(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])

    assert exc.value.code == 0
    assert "memoria" in capsys.readouterr().out


def test_cli_help_renders_exactly_five_job_groups_in_order(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["help"])
    out = capsys.readouterr().out

    assert rc == 0
    assert _parser_dests("memoria help") == set()
    headings = [
        line[:-1] for line in out.splitlines() if line.endswith(":") and not line.startswith(" ")
    ]
    assert headings == ["read", "knowledge", "project", "review", "upkeep"]


def test_cli_help_groups_carry_correct_membership(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["help"])
    blocks = _job_console_blocks(capsys.readouterr().out)

    assert rc == 0
    assert set(blocks) == {"read", "knowledge", "project", "review", "upkeep"}

    def has(job: str, left: str) -> bool:
        return any(line.startswith(left + "  ") for line in blocks[job])

    assert has("read", "memoria status")
    assert has("read", "memoria operation list")
    assert has("read", "memoria surface schema")
    assert has("read", "surface.openapi (http)")
    assert has("read", "memoria list")
    assert has("read", "memoria show")
    assert has("read", "work.get (http, mcp)")
    assert has("read", "memoria journal tail")
    assert has("read", "memoria journal show")
    assert has("read", "exploration.list (http, mcp)")
    assert has("read", "memoria explore")
    assert blocks["knowledge"] == ["(no registered surfaces yet)"]
    assert has("project", "project.slice.read (http, mcp)")
    assert has("project", "project.draft.read (http, mcp)")
    assert has("review", "memoria request list")
    assert has("review", "memoria request show")
    assert has("review", "memoria attention list")
    assert has("review", "memoria attention worklist")
    assert has("review", "memoria attention show")
    assert has("read", "memoria context")
    # HTTP-only rows disclose themselves by id: the dashboard's CLI front is
    # a separate CLI-only command, so the console must not claim one here.
    assert has("review", "views.dashboard (http)")
    assert has("upkeep", "memoria operation run")


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
        "memoria onboard",
        "memoria status",
        "memoria context",
        "memoria surface schema",
        "memoria doctor",
        "memoria doctor bundle",
        "memoria doctor self-test",
        "memoria ask",
        "memoria secrets set",
        "memoria secrets list",
        "memoria explore",
        "memoria handshake",
        "memoria serve",
        "memoria mcp",
        "memoria help",
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
        "memoria seed install",
        "memoria link",
        "memoria mv",
        "memoria check",
        "memoria cockpit",
        "memoria dashboard",
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
        "memoria journal revert-preview",
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


def test_cli_explore_help_and_read_envelope_are_pure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    parser = _build_parser()
    explore_parser = _parser_for_command(parser, "memoria explore")
    project_parser = _parser_for_command(parser, "memoria project explore")
    assert "memoria project explore" in str(explore_parser.description)
    assert "memoria explore" in str(project_parser.description)
    assert _parser_dests("memoria explore") >= {"topic", "versus", "project", "depth", "trace"}

    with state.connect(workspace) as conn:
        before = conn.execute("SELECT COUNT(*) FROM operation_requests").fetchone()[0]
    rc = main(["explore", "absent", "--workspace", str(workspace), "--json", "--trace"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["api_version"] == "engine-read-api.v1"
    assert output["explore"]["trace"]["rerank"] == "off"
    with state.connect(workspace) as conn:
        after = conn.execute("SELECT COUNT(*) FROM operation_requests").fetchone()[0]
    assert after == before


def test_cli_explore_text_reports_empty_sides_and_requested_traces(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    assert main(["explore", "absent", "--workspace", str(workspace), "--json"]) == 0
    empty = json.loads(capsys.readouterr().out)["explore"]["honest_empty"]

    assert main(["explore", "absent", "--workspace", str(workspace), "--trace"]) == 0
    text = capsys.readouterr().out
    assert text.splitlines()[0] == empty
    assert "universe:" in text
    assert "rerank: off" in text

    assert (
        main(
            [
                "explore",
                "absent",
                "--versus",
                "also-absent",
                "--workspace",
                str(workspace),
                "--trace",
            ]
        )
        == 0
    )
    versus_text = capsys.readouterr().out
    assert f"a: {empty}" in versus_text
    assert "b: 0 of " in versus_text
    assert "a: universe:" in versus_text
    assert "b: rerank: off" in versus_text

    write_checked_concept(
        workspace,
        "notes/known.md",
        "type: note\ntitle: Known topic\nmode: claim\n",
        body="Known topic evidence.",
    )
    assert (
        main(
            [
                "explore",
                "known",
                "--versus",
                "absent",
                "--workspace",
                str(workspace),
                "--json",
            ]
        )
        == 0
    )
    mixed_empty = json.loads(capsys.readouterr().out)["explore"]["b"]["honest_empty"]

    assert (
        main(
            [
                "explore",
                "known",
                "--versus",
                "absent",
                "--workspace",
                str(workspace),
                "--trace",
            ]
        )
        == 0
    )
    mixed_text = capsys.readouterr().out
    assert mixed_text.splitlines()[0] == "completed; details available with --json"
    assert f"b: {mixed_empty}" in mixed_text
    assert "a: universe:" in mixed_text
    assert "b: rerank: off" in mixed_text


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


def test_steering_show_renders_effective_steering_provenance(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    assert (
        main(
            [
                "new",
                "project",
                "Retrieval Practice",
                "--workspace",
                str(workspace),
                "--json",
                "--idempotency-key",
                "steering-show-project",
            ]
        )
        == 0
    )
    created = json.loads(capsys.readouterr().out)
    assert (
        main(
            [
                "steering",
                "edit",
                "--workspace",
                str(workspace),
                "--body",
                "---\ntype: system\ntitle: Steering\n---\n\n"
                "## Watch for\n\n- interleaving\n\n## Muted\n\n- practice\n",
                "--json",
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert main(["steering", "show", "--workspace", str(workspace), "--json"]) == 0
    shown = json.loads(capsys.readouterr().out)

    assert shown["ok"] is True
    assert shown["path"] == "steering.md"
    assert shown["muted"] == ["practice"]
    by_token = {row["token"]: row["sources"] for row in shown["tokens"]}
    assert by_token["retrieval"] == [f"project:{created['path']}"]
    assert by_token["interleaving"] == ["watch"]
    assert "practice" not in by_token

    assert main(["steering", "show", "--workspace", str(workspace)]) == 0
    readable = capsys.readouterr().out
    assert "interleaving" in readable
    assert "muted: practice" in readable


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
    assert core_plugins["graph"] is True
    assert core_plugins["properties"] is True
    assert core_plugins["daily-notes"] is False
    assert core_plugins["templates"] is False
    assert app["propertiesInDocument"] == "source"
    assert app["alwaysUpdateLinks"] is True
    assert community_plugins == ["memoria-obsidian"]
    assert manifest["id"] == "memoria-obsidian"
    graph = json.loads((workspace / ".obsidian/graph.json").read_text("utf-8"))
    types = json.loads((workspace / ".obsidian/types.json").read_text("utf-8"))
    assert {group["query"] for group in graph["colorGroups"]} == {
        "path:notes/",
        "path:hubs/",
        "path:projects/",
        "path:digests/",
        "path:fulltexts/",
        "path:inbox/",
    }
    assert types["types"]["stale"] == "checkbox"
    assert types["types"]["consequence"] == "text"
    assert types["types"]["superseded"] == "checkbox"
    assert types["types"]["loudness"] == "text"
    assert types["types"]["target"] == "text"
    assert types["types"]["thesis"] == "text"
    assert types["types"]["question"] == "text"
    assert (workspace / ".obsidian/plugins/memoria-obsidian/main.js").is_file()
    assert (workspace / ".obsidian/plugins/memoria-obsidian/schema.js").is_file()
    assert (workspace / ".obsidian/plugins/memoria-obsidian/styles.css").is_file()
    # `main.js` requires these by relative path; without them it cannot load.
    assert (workspace / ".obsidian/plugins/memoria-obsidian/handshake.js").is_file()
    assert (workspace / ".obsidian/plugins/memoria-obsidian/pill.js").is_file()
    assert (workspace / ".obsidian/plugins/memoria-obsidian/relate.js").is_file()
    assert (workspace / ".obsidian/plugins/memoria-obsidian/viewspec.js").is_file()


def test_cli_init_seeds_exact_boot_c1_agent_bundle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"

    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    expected = {
        ".claude/hooks/write_perimeter.py",
        ".claude/settings.json",
        ".codex/hooks.json",
        ".mcp.json",
        "CLAUDE.md",
    }
    delivered = {
        path.relative_to(workspace).as_posix()
        for directory in (workspace / ".claude", workspace / ".codex")
        for path in directory.rglob("*")
        if path.is_file()
    } | {rel for rel in (".mcp.json", "CLAUDE.md") if (workspace / rel).is_file()}

    assert delivered == expected
    for rel in expected:
        assert (workspace / rel).read_bytes() == (WORKSPACE_SEED / rel).read_bytes()


def test_cli_init_no_obsidian_skips_obsidian_seed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    dry_workspace = tmp_path / "dry-workspace"

    rc = main(["init", "--workspace", str(workspace), "--yes", "--no-obsidian", "--json"])
    capsys.readouterr()

    assert rc == 0
    assert not (workspace / ".obsidian").exists()
    assert not any(
        (workspace / base).exists()
        for base in ("catalog.base", "claims.base", "inbox.base", "projects.base", "sources.base")
    )
    assert (workspace / ".memoria/schemas/folders.yaml").is_file()
    assert (workspace / "steering.md").is_file()
    for rel in (
        ".claude/hooks/write_perimeter.py",
        ".claude/settings.json",
        ".codex/hooks.json",
        ".mcp.json",
        "CLAUDE.md",
    ):
        assert (workspace / rel).is_file()

    rc = main(["init", "--workspace", str(dry_workspace), "--dry-run", "--no-obsidian", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert ".obsidian" not in output["package"]["seed_trees"]
    assert not set(output["package"]["seed_files"]) & {
        "catalog.base",
        "claims.base",
        "inbox.base",
        "projects.base",
        "sources.base",
    }
    assert not {".claude", ".codex"} & set(output["package"]["seed_trees"])
    assert not {".mcp.json", "CLAUDE.md"} & set(output["package"]["seed_files"])
    assert output["package"]["bundle_files"] == [
        ".claude/hooks/write_perimeter.py",
        ".claude/settings.json",
        ".codex/hooks.json",
        ".mcp.json",
        "CLAUDE.md",
    ]
    assert not dry_workspace.exists()


def test_cli_init_no_obsidian_skips_untouched_view_symlinks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    outside_obsidian = tmp_path / "outside-obsidian"
    outside_base = tmp_path / "outside-inbox.base"
    workspace.mkdir()
    outside_obsidian.mkdir()
    outside_base.write_text("PI-owned\n", encoding="utf-8")
    (workspace / ".obsidian").symlink_to(outside_obsidian, target_is_directory=True)
    (workspace / "inbox.base").symlink_to(outside_base)

    rc = main(["init", "--workspace", str(workspace), "--yes", "--no-obsidian", "--json"])
    capsys.readouterr()

    assert rc == 0
    assert (workspace / ".obsidian").is_symlink()
    assert (workspace / "inbox.base").is_symlink()
    assert outside_base.read_text(encoding="utf-8") == "PI-owned\n"
    assert not any(outside_obsidian.iterdir())


def test_cli_init_rejects_dangling_seed_symlink(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside-catalog.base"
    workspace.mkdir()
    (workspace / "catalog.base").symlink_to(outside)

    rc = main(["init", "--workspace", str(workspace), "--yes", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output == {
        "ok": False,
        "error": "workspace write target must not redirect through a symlink or junction: "
        "catalog.base",
    }
    assert not outside.exists()
    assert not (workspace / ".memoria").exists()


def test_cli_init_rejects_dynamic_canvas_symlink(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside-argument.canvas"

    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()
    write_checked_concept(
        workspace,
        "projects/dynamic/project.md",
        "type: project\ncheck_status: checked\ntitle: Dynamic project\n",
        "project",
    )
    canvas = workspace / "projects/dynamic/argument.canvas"
    canvas.write_text("{}\n", encoding="utf-8")
    git(workspace, "add", "projects/dynamic/project.md", "projects/dynamic/argument.canvas")
    git(workspace, "commit", "-m", "track dynamic canvas")
    canvas.unlink()
    canvas.symlink_to(outside)

    rc = main(["init", "--workspace", str(workspace), "--yes", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output == {
        "ok": False,
        "error": "workspace write target must not redirect through a symlink or junction: "
        "projects/dynamic/argument.canvas",
    }
    assert not outside.exists()


def test_cli_init_rejects_gitfile_indirection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    external = tmp_path / "external"
    workspace.mkdir()
    external.mkdir()
    git(external, "init", "-q")
    external_config = external / ".git/config"
    before = external_config.read_text(encoding="utf-8")
    (workspace / ".git").write_text(f"gitdir: {external / '.git'}\n", encoding="utf-8")

    rc = main(["init", "--workspace", str(workspace), "--yes", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output == {"ok": False, "error": "workspace Git metadata must be a directory"}
    assert external_config.read_text(encoding="utf-8") == before
    assert not (workspace / ".memoria").exists()


def test_cli_init_rejects_git_common_directory_indirection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    external = tmp_path / "external"
    git_metadata = workspace / ".git"
    external.mkdir()
    git(external, "init", "-q")
    external_config = external / ".git/config"
    before = external_config.read_text(encoding="utf-8")
    git_metadata.mkdir(parents=True)
    (git_metadata / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (git_metadata / "commondir").write_text(f"{external / '.git'}\n", encoding="utf-8")

    rc = main(["init", "--workspace", str(workspace), "--yes", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert output == {
        "ok": False,
        "error": "workspace Git common-directory indirection is not supported",
    }
    assert external_config.read_text(encoding="utf-8") == before
    assert not (workspace / ".memoria").exists()


def test_cli_init_does_not_run_workspace_fsmonitor(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"
    marker = tmp_path / "fsmonitor-ran"
    script = tmp_path / "fsmonitor"
    workspace.mkdir()
    script.write_text(f"#!/bin/sh\ntouch {marker}\n", encoding="utf-8")
    script.chmod(0o700)
    git(workspace, "init", "-q")
    git(workspace, "config", "core.fsmonitor", str(script))

    rc = main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()

    assert rc == 0
    assert not marker.exists()


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
    assert output["package"]["seed_files"] == [
        ".gitignore",
        "Start here.md",
        "steering.md",
        "system/vocabulary.md",
        "catalog.base",
        "claims.base",
        "inbox.base",
        "projects.base",
        "sources.base",
    ]
    # The bundle files are reported separately: `runtime.bundles` writes them,
    # not the seed-class copy (BOOT-C.6, one writer).
    assert output["package"]["bundle_files"] == [
        ".claude/hooks/write_perimeter.py",
        ".claude/settings.json",
        ".codex/hooks.json",
        ".mcp.json",
        ".obsidian/plugins/memoria-obsidian/handshake.js",
        ".obsidian/plugins/memoria-obsidian/main.js",
        ".obsidian/plugins/memoria-obsidian/manifest.json",
        ".obsidian/plugins/memoria-obsidian/pill.js",
        ".obsidian/plugins/memoria-obsidian/relate.js",
        ".obsidian/plugins/memoria-obsidian/schema.js",
        ".obsidian/plugins/memoria-obsidian/styles.css",
        ".obsidian/plugins/memoria-obsidian/viewspec.js",
        "CLAUDE.md",
    ]
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
        "vault_manifest": ".memoria/vault.json",
    }
    assert not workspace.exists()


def test_cli_init_seeds_start_here_front_door(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = tmp_path / "workspace"

    rc = main(["init", "--workspace", str(workspace), "--yes", "--json"])
    capsys.readouterr()
    text = (workspace / "Start here.md").read_text(encoding="utf-8")

    assert rc == 0
    assert "type: system" in text
    assert "tutorials/01-system-tour" in text
    assert "tutorials/07-customize" in text
    assert ".claude/skills/memoria-copi/SKILL.md" in text
    assert "memoria status --workspace ." in text


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


def test_cli_onboard_runs_runway_and_is_non_interactive_under_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from memoria_vault.runtime import onboarding

    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--quiet"]) == 0
    capsys.readouterr()
    seen: dict[str, object] = {}

    def fake_run_onboarding(ws: Path, **kwargs: object) -> dict[str, object]:
        seen["workspace"] = ws
        # Pin the production call site: BOOT-D.4 replaced a bare
        # urllib.request.urlopen default with the proxy-free, redirect-free
        # `_open_zotero_probe` specifically so a `127.0.0.1` probe cannot
        # leave the machine under an ambient proxy. `memoria onboard` is the
        # real caller that exercises that default in production, so it must
        # thread the hardened opener explicitly rather than merely rely on
        # `run_onboarding`'s own default staying correct.
        seen["url_open"] = kwargs["url_open"]
        ask = kwargs["ask"]
        seen["ask_result"] = ask("Run this command now? [y/N] ")  # type: ignore[operator]
        return {"ok": True, "workspace": str(ws), "completed": True, "steps": []}

    monkeypatch.setattr(onboarding, "run_onboarding", fake_run_onboarding)
    rc = main(["onboard", "--workspace", str(workspace), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert output["ok"] is True
    assert output["completed"] is True
    assert seen["workspace"] == workspace.resolve()
    assert seen["ask_result"] == ""  # --json never prompts: consent defaults to no
    assert seen["url_open"] is onboarding._open_zotero_probe


def test_cli_init_onboard_flag_runs_onboarding_tail(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from memoria_vault.runtime import onboarding

    workspace = tmp_path / "workspace"
    calls: list[Path] = []

    def fake_run_onboarding(ws: Path, **kwargs: object) -> dict[str, object]:
        calls.append(ws)
        return {
            "ok": True,
            "workspace": str(ws),
            "completed": True,
            "steps": [{"step": "obsidian", "status": "present"}],
        }

    monkeypatch.setattr(onboarding, "run_onboarding", fake_run_onboarding)
    rc = main(["init", "--workspace", str(workspace), "--yes", "--onboard", "--json"])
    output = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert calls == [workspace.resolve()]
    assert output["ok"] is True
    assert output["onboard"]["steps"] == [{"step": "obsidian", "status": "present"}]
    assert (workspace / "Start here.md").is_file()


def test_cli_onboard_ask_survives_unusable_stdin_without_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """`ask` is not total end to end: `run_onboarding` only guards its own
    call sites against `EOFError`/`RuntimeError` (a closed-stdin `input()`
    can also raise `OSError` -- a closed fd 0 -- or `ValueError` -- an
    in-process `sys.stdin.close()`), and neither is caught there. Under
    `memoria onboard` with no `--json`/`--quiet` (the interactive branch),
    the CLI-level `ask` closure itself must swallow every unusable-stdin
    shape so a piped/closed-stdin invocation degrades to a declined prompt,
    never an uncaught exception.
    """
    from memoria_vault.runtime import onboarding

    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--quiet"]) == 0
    capsys.readouterr()
    captured: dict[str, object] = {}

    def fake_run_onboarding(ws: Path, **kwargs: object) -> dict[str, object]:
        captured["ask"] = kwargs["ask"]
        return {"ok": True, "workspace": str(ws), "completed": True, "steps": []}

    monkeypatch.setattr(onboarding, "run_onboarding", fake_run_onboarding)

    def closed_fd_input(_prompt: str = "") -> str:
        raise OSError("[Errno 9] Bad file descriptor")

    monkeypatch.setattr("builtins.input", closed_fd_input)
    rc = main(["onboard", "--workspace", str(workspace)])
    capsys.readouterr()

    assert rc == 0
    ask = captured["ask"]
    assert ask("prompt? ") == ""  # type: ignore[operator]

    def closed_file_input(_prompt: str = "") -> str:
        raise ValueError("I/O operation on closed file")

    monkeypatch.setattr("builtins.input", closed_file_input)
    assert ask("prompt? ") == ""  # type: ignore[operator]
