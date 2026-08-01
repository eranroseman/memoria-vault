"""Agent-bundle seeding, vault.json manifest, upgrade, and skew detection."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from memoria_vault import cli
from memoria_vault.cli import main
from memoria_vault.runtime import bundles
from memoria_vault.runtime.policy.audit import sha256_file
from tests.helpers import WORKSPACE_SEED, git

PERIMETER_MESSAGE = (
    "Memoria write perimeter: vault notes are engine-mediated — a direct edit "
    "would be recorded as the human's work by the provenance layer. "
    "Use the MCP tool `operation_run` or the `memoria` CLI."
)
PROTECTED_PATTERNS = (
    "**/*.md",
    ".claude/**",
    ".codex/**",
    ".mcp.json",
    ".memoria/**",
    ".obsidian/**",
)
OBSIDIAN_PLUGIN_REL = ".obsidian/plugins/memoria-obsidian"


def _packaged_agent_bundle_files() -> list[str]:
    """Every packaged agent-bundle path, walked from the seed roster constants."""
    targets: list[str] = []
    for source_rel, target_rel in cli.AGENT_BUNDLE_SEED_TREES:
        targets.extend(cli._seed_tree_file_targets(source_rel, target_rel))
    targets.extend(target for _source, target in cli.AGENT_BUNDLE_SEED_FILES)
    return sorted(targets)


def test_seed_claude_settings_deny_rules_cover_every_protected_path():
    settings = json.loads((WORKSPACE_SEED / ".claude/settings.json").read_text("utf-8"))
    expected = {
        f"{tool}({pattern})"
        for tool in ("Edit", "Write", "NotebookEdit")
        for pattern in PROTECTED_PATTERNS
    }
    assert set(settings["permissions"]["deny"]) == expected
    assert len(settings["permissions"]["deny"]) == 18


def test_seed_claude_settings_registers_the_perimeter_hook():
    settings = json.loads((WORKSPACE_SEED / ".claude/settings.json").read_text("utf-8"))
    entries = settings["hooks"]["PreToolUse"]
    assert len(entries) == 1
    assert entries[0]["matcher"] == "Edit|Write|NotebookEdit"
    assert entries[0]["hooks"] == [
        {
            "type": "command",
            "command": 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/write_perimeter.py"',
        }
    ]


def test_write_perimeter_hook_denies_unconditionally_with_exit_2():
    hook = WORKSPACE_SEED / ".claude/hooks/write_perimeter.py"
    result = subprocess.run(
        [sys.executable, "-B", str(hook)],
        input='{"tool_name": "Write", "tool_input": {"file_path": "notes/x.md"}}',
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert PERIMETER_MESSAGE in result.stderr
    assert result.stdout == ""


def test_seed_tree_skips_python_bytecode_caches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seed = tmp_path / "seed"
    hook = seed / ".claude/hooks/write_perimeter.py"
    hook.parent.mkdir(parents=True)
    hook.write_text("# hook\n", encoding="utf-8")
    artifacts = (
        seed / ".claude/__pycache__/ignored.cpython-312.pyc",
        seed / ".claude/hooks/__pycache__/write_perimeter.cpython-312.pyc",
        seed / ".claude/hooks/stray.pyc",
    )
    for artifact in artifacts:
        artifact.parent.mkdir(exist_ok=True)
        artifact.write_bytes(b"compiled bytecode")

    def fake_seed_resource(source_rel: str) -> Path:
        return seed.joinpath(*source_rel.split("/"))

    monkeypatch.setattr(cli, "_seed_resource", fake_seed_resource)
    monkeypatch.setattr(cli, "SEED_TREES", ((".claude", ".claude"),))
    monkeypatch.setattr(cli, "SEED_FILES", ())

    delivered = tmp_path / "workspace/.claude"
    cli._copy_seed_tree(".claude", delivered, overwrite=False, target_rel=".claude")
    manifest_targets = cli._seed_tree_file_targets(".claude", ".claude")
    preflight_targets = cli._seed_tree_write_targets(".claude", ".claude")
    repair_targets = cli._repair_seed_write_targets(tmp_path / "repair")
    repair_preflight_targets = cli._repair_write_targets(
        tmp_path / "preflight", include_obsidian=False
    )

    assert (delivered / "hooks/write_perimeter.py").read_text(encoding="utf-8") == "# hook\n"
    assert not (delivered / "__pycache__").exists()
    assert not (delivered / "hooks/__pycache__").exists()
    assert not (delivered / "hooks/stray.pyc").exists()
    for targets in (manifest_targets, preflight_targets, repair_targets, repair_preflight_targets):
        assert ".claude/hooks/write_perimeter.py" in targets
        assert ".claude/hooks/stray.pyc" not in targets
    assert all("__pycache__" not in Path(target).parts for target in manifest_targets)
    assert all("__pycache__" not in Path(target).parts for target in preflight_targets)
    assert all("__pycache__" not in Path(target).parts for target in repair_targets)
    assert all("__pycache__" not in Path(target).parts for target in repair_preflight_targets)


def test_write_perimeter_hook_is_stdlib_only():
    source = (WORKSPACE_SEED / ".claude/hooks/write_perimeter.py").read_text("utf-8")
    for forbidden in ("memoria_vault", "import requests", "import yaml"):
        assert forbidden not in source


def test_seed_mcp_json_wires_memoria_mcp_stdio():
    config = json.loads((WORKSPACE_SEED / ".mcp.json").read_text("utf-8"))
    server = config["mcpServers"]["memoria"]
    assert server["command"] == "memoria"
    assert server["args"][:3] == ["mcp", "--workspace", "."]
    scopes = [
        server["args"][index + 1]
        for index, arg in enumerate(server["args"])
        if arg == "--read-scope"
    ]
    assert scopes == ["notes", "hubs", "projects", "digests", "fulltexts", "inbox"]


def test_seed_claude_md_is_an_agents_md_loader():
    assert (WORKSPACE_SEED / "CLAUDE.md").read_text("utf-8") == "@AGENTS.md\n"


def test_seed_codex_hooks_mirror_the_deny_rules():
    mirror = json.loads((WORKSPACE_SEED / ".codex/hooks.json").read_text("utf-8"))
    assert mirror["schema"] == 1
    assert mirror["deny"]["tools"] == ["edit", "write"]
    assert mirror["deny"]["paths"] == list(PROTECTED_PATTERNS)


def _init(tmp_path: Path, capsys: pytest.CaptureFixture[str], *extra: str) -> Path:
    workspace = tmp_path / "workspace"
    assert main(["init", "--workspace", str(workspace), "--yes", "--json", *extra]) == 0
    capsys.readouterr()
    return workspace


def _read_manifest(workspace: Path) -> dict:
    return json.loads((workspace / bundles.MANIFEST_REL).read_text("utf-8"))


def test_bundle_files_registry_covers_every_packaged_bundle_file():
    """The manifest roster is derived from the package tree, not retyped.

    A third hand-written roster silently under-records the manifest the first
    time a file joins `workspace_seed/.claude/` or the plugin (U3-PLUG's
    `viewspec.js`), so both rosters are compared against what actually ships.
    """
    assert sorted(bundles.BUNDLE_FILES["agent"]) == _packaged_agent_bundle_files()
    assert sorted(bundles.BUNDLE_FILES["obsidian"]) == sorted(
        cli._seed_tree_file_targets(OBSIDIAN_PLUGIN_REL, OBSIDIAN_PLUGIN_REL)
    )


def test_init_seeds_agent_and_obsidian_bundles_and_writes_current_hash_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = _init(tmp_path, capsys)

    for rel in bundles.BUNDLE_FILES["agent"] + bundles.BUNDLE_FILES["obsidian"]:
        assert (workspace / rel).is_file(), rel
        assert (workspace / rel).read_bytes() == (WORKSPACE_SEED / rel).read_bytes(), rel

    manifest = _read_manifest(workspace)
    assert manifest["schema"] == bundles.MANIFEST_SCHEMA
    assert manifest["vault_id"]
    assert sorted(manifest["bundles"]) == ["agent", "obsidian"]
    for name, rels in bundles.BUNDLE_FILES.items():
        recorded = manifest["bundles"][name]["files"]
        assert sorted(recorded) == sorted(rels)
        for rel, digest in recorded.items():
            assert sha256_file(workspace / rel) == digest, rel


def test_init_no_obsidian_seeds_only_the_agent_bundle_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    workspace = _init(tmp_path, capsys, "--no-obsidian")

    manifest = _read_manifest(workspace)
    assert sorted(manifest["bundles"]) == ["agent"]
    for rel, digest in manifest["bundles"]["agent"]["files"].items():
        assert sha256_file(workspace / rel) == digest, rel
    assert not (workspace / ".obsidian").exists()
    assert (workspace / ".claude/settings.json").is_file()


def test_init_tracks_the_vault_manifest_in_the_first_commit(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The manifest is seeded evidence, so it is tracked, not gitignored."""
    workspace = _init(tmp_path, capsys)

    assert git(workspace, "ls-files", bundles.MANIFEST_REL) == bundles.MANIFEST_REL
    assert git(workspace, "status", "--porcelain") == ""


def test_reinit_preserves_pi_edited_bundle_files_and_hashes_what_is_on_disk(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`scripts/install.sh` re-runs `memoria init --yes` as its upgrade path.

    Two of these paths *are* the write perimeter, so an unconditional reseed
    silently discards PI-owned policy; and once a file is preserved, hashing
    the template bytes would record a digest for content not on disk.
    """
    workspace = _init(tmp_path, capsys)
    edited = {
        ".claude/settings.json": '{"PI_OWNED": true}\n',
        "CLAUDE.md": "@AGENTS.md\n\nPI addendum.\n",
        ".obsidian/plugins/memoria-obsidian/main.js": "// PI patch\n",
    }
    for rel, text in edited.items():
        (workspace / rel).write_text(text, encoding="utf-8")

    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    for rel, text in edited.items():
        assert (workspace / rel).read_text(encoding="utf-8") == text, rel
    manifest = _read_manifest(workspace)
    for name, rels in bundles.BUNDLE_FILES.items():
        recorded = manifest["bundles"][name]["files"]
        assert sorted(recorded) == sorted(rels)
        for rel, digest in recorded.items():
            assert sha256_file(workspace / rel) == digest, rel
