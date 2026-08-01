"""Agent-bundle templates, the single bundle writer, and the vault.json receipt."""

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
AGENT_BUNDLE_SEED_ROOTS = (".claude", ".codex", ".mcp.json", "CLAUDE.md")


def _packaged_agent_bundle_files() -> list[str]:
    """Every packaged agent-bundle path, walked from the package seed itself."""
    targets: list[str] = []
    for root in AGENT_BUNDLE_SEED_ROOTS:
        targets.extend(cli._seed_tree_file_targets(root, root))
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
    # `.probe` stands in for a seed tree carrying a Python file. It must stay
    # outside `bundles.BUNDLE_PATHS`: the seed-class copy declines bundle paths
    # on the init path, because `runtime.bundles` is their only writer.
    seed = tmp_path / "seed"
    hook = seed / ".probe/hooks/write_perimeter.py"
    hook.parent.mkdir(parents=True)
    hook.write_text("# hook\n", encoding="utf-8")
    artifacts = (
        seed / ".probe/__pycache__/ignored.cpython-312.pyc",
        seed / ".probe/hooks/__pycache__/write_perimeter.cpython-312.pyc",
        seed / ".probe/hooks/stray.pyc",
    )
    for artifact in artifacts:
        artifact.parent.mkdir(exist_ok=True)
        artifact.write_bytes(b"compiled bytecode")

    def fake_seed_resource(source_rel: str) -> Path:
        return seed.joinpath(*source_rel.split("/"))

    monkeypatch.setattr(cli, "_seed_resource", fake_seed_resource)
    monkeypatch.setattr(cli, "SEED_TREES", ((".probe", ".probe"),))
    monkeypatch.setattr(cli, "SEED_FILES", ())

    delivered = tmp_path / "workspace/.probe"
    cli._copy_seed_tree(".probe", delivered, overwrite=False, target_rel=".probe")
    manifest_targets = cli._seed_tree_file_targets(".probe", ".probe")
    preflight_targets = cli._seed_tree_write_targets(".probe", ".probe")
    repair_targets = cli._repair_seed_write_targets(tmp_path / "repair")
    repair_preflight_targets = cli._repair_write_targets(
        tmp_path / "preflight", include_obsidian=False
    )

    assert (delivered / "hooks/write_perimeter.py").read_text(encoding="utf-8") == "# hook\n"
    assert not (delivered / "__pycache__").exists()
    assert not (delivered / "hooks/__pycache__").exists()
    assert not (delivered / "hooks/stray.pyc").exists()
    for targets in (manifest_targets, preflight_targets, repair_targets, repair_preflight_targets):
        assert ".probe/hooks/write_perimeter.py" in targets
        assert ".probe/hooks/stray.pyc" not in targets
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


def test_init_seeds_agent_and_obsidian_bundles_and_writes_the_as_created_manifest(
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


def test_reinit_preserves_pi_edited_bundle_files_and_the_as_created_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`scripts/install.sh` re-runs `memoria init --yes` as its upgrade path.

    Two of these paths *are* the write perimeter, so an unconditional reseed
    silently discards PI-owned policy. The manifest is an as-created receipt
    (BOOT-C.6), so a later PI edit leaves the file alone *and* the record
    alone — it does not follow the edit onto disk.
    """
    workspace = _init(tmp_path, capsys)
    as_created = (workspace / bundles.MANIFEST_REL).read_bytes()
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
    assert (workspace / bundles.MANIFEST_REL).read_bytes() == as_created
    recorded = _read_manifest(workspace)["bundles"]["agent"]["files"]
    assert recorded[".claude/settings.json"] == sha256_file(
        WORKSPACE_SEED / ".claude/settings.json"
    )


def test_reinit_pins_the_vault_identity_and_leaves_the_vault_git_tree_clean(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A pure installer re-run must record nothing in the vault's own history.

    The manifest is tracked, so re-minting `vault_id` left `' M
    .memoria/vault.json'` in every upgrade — a spurious modification in vault
    history, and a churned identity in `runtime.json`.
    """
    workspace = _init(tmp_path, capsys)
    as_created = (workspace / bundles.MANIFEST_REL).read_bytes()
    vault_id = _read_manifest(workspace)["vault_id"]
    assert git(workspace, "status", "--porcelain") == ""

    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    assert _read_manifest(workspace)["vault_id"] == vault_id
    assert (workspace / bundles.MANIFEST_REL).read_bytes() == as_created
    assert git(workspace, "status", "--porcelain") == ""


def test_reinit_restores_a_deleted_bundle_file_without_rewriting_the_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Write-if-absent still re-delivers a removed bundle file on the next run."""
    workspace = _init(tmp_path, capsys)
    as_created = (workspace / bundles.MANIFEST_REL).read_bytes()
    (workspace / ".mcp.json").unlink()

    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    assert (workspace / ".mcp.json").read_bytes() == (WORKSPACE_SEED / ".mcp.json").read_bytes()
    assert (workspace / bundles.MANIFEST_REL).read_bytes() == as_created


def test_reinit_adding_the_obsidian_bundle_keeps_the_as_created_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The recorded cost of the as-created receipt (BOOT-C.6 amendment).

    A bundle seeded by a later run is on disk but absent from the manifest:
    the receipt describes the vault as created, not as it stands. Nothing
    reads these hashes, and a drift check must keep its own as-seeded record.
    """
    workspace = _init(tmp_path, capsys, "--no-obsidian")
    as_created = (workspace / bundles.MANIFEST_REL).read_bytes()

    assert main(["init", "--workspace", str(workspace), "--yes", "--json"]) == 0
    capsys.readouterr()

    assert (workspace / f"{OBSIDIAN_PLUGIN_REL}/main.js").is_file()
    assert (workspace / bundles.MANIFEST_REL).read_bytes() == as_created
    assert sorted(_read_manifest(workspace)["bundles"]) == ["agent"]


def test_the_bundle_writer_is_the_only_writer_of_bundle_paths_on_init(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Silence the one writer and `init` must deliver no bundle path at all.

    The seed-class copy wrote all nine a second time before BOOT-C.6, with the
    opposite overwrite policy; a second writer reappearing leaves the files on
    disk even with `seed_bundles` disabled.
    """
    calls: list[list[str] | None] = []

    def _record(workspace: Path, *, bundle_names: list[str] | None = None) -> None:
        calls.append(bundle_names)

    monkeypatch.setattr(bundles, "seed_bundles", _record)

    workspace = _init(tmp_path, capsys)

    assert calls == [["agent", "obsidian"]]
    for rel in sorted(bundles.BUNDLE_PATHS):
        assert not (workspace / rel).exists(), rel
    assert not (workspace / bundles.MANIFEST_REL).exists()


def test_the_seed_class_copy_declines_every_bundle_path_on_the_init_path(
    tmp_path: Path,
) -> None:
    """One policy: the seed-class writer never competes for a bundle path."""
    for rel in sorted(bundles.BUNDLE_PATHS):
        assert cli._seed_write_allowed(rel, tmp_path / rel, overwrite=False) is False, rel


def test_no_seed_class_roster_carries_an_agent_bundle_path() -> None:
    """The agent bundle left the seed rosters, so repair cannot reach it."""
    targets = {target for _source, target in cli.SEED_FILES}
    for source_rel, target_rel in cli.SEED_TREES:
        targets.update(cli._seed_tree_file_targets(source_rel, target_rel))

    assert not targets & set(bundles.BUNDLE_FILES["agent"])


def test_init_declares_every_bundle_path_and_the_manifest_as_a_write_target(
    tmp_path: Path,
) -> None:
    """The preflight set is complete, not merely non-empty."""
    declared = set(
        cli._repair_write_targets(tmp_path / "ws", include_obsidian=True, include_agent_bundle=True)
    )
    agent_only = set(
        cli._repair_write_targets(
            tmp_path / "ws", include_obsidian=False, include_agent_bundle=True
        )
    )
    repair = set(cli._repair_write_targets(tmp_path / "ws"))

    assert set(bundles.bundle_write_targets()) <= declared
    assert bundles.MANIFEST_REL in declared
    assert set(bundles.bundle_write_targets(["agent"])) <= agent_only
    assert not agent_only & set(bundles.BUNDLE_FILES["obsidian"])
    assert bundles.MANIFEST_REL not in repair


def test_init_refuses_a_manifest_that_redirects_outside_the_workspace(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The declared set is a preflight: a symlinked manifest stops init."""
    workspace = tmp_path / "workspace"
    (workspace / ".memoria").mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text("{}\n", encoding="utf-8")
    (workspace / bundles.MANIFEST_REL).symlink_to(outside)

    rc = main(["init", "--workspace", str(workspace), "--yes", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert bundles.MANIFEST_REL in payload["error"]
    assert outside.read_text(encoding="utf-8") == "{}\n"
    assert not (workspace / ".claude").exists()


def test_doctor_repair_never_touches_the_agent_bundle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Repair neither overwrites PI-owned perimeter policy nor recreates it."""
    workspace = _init(tmp_path, capsys)
    as_created = (workspace / bundles.MANIFEST_REL).read_bytes()
    edited = {
        rel: f"# PI owns {rel}\n" for rel in bundles.BUNDLE_FILES["agent"] if rel != ".mcp.json"
    }
    for rel, text in edited.items():
        (workspace / rel).write_text(text, encoding="utf-8")
    (workspace / ".mcp.json").unlink()

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])
    capsys.readouterr()

    assert rc == 0
    for rel, text in edited.items():
        assert (workspace / rel).read_text(encoding="utf-8") == text, rel
    assert not (workspace / ".mcp.json").exists()
    assert (workspace / bundles.MANIFEST_REL).read_bytes() == as_created


def test_doctor_repair_restores_the_obsidian_plugin_to_the_recorded_bytes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Why the manifest needs no post-repair warning under an as-created receipt.

    Repair reseeds `.obsidian/plugins/*` as a runtime seed. Those are the same
    package bytes the receipt recorded, so repair moves disk back *onto* the
    manifest rather than away from it.
    """
    workspace = _init(tmp_path, capsys)
    rel = f"{OBSIDIAN_PLUGIN_REL}/main.js"
    recorded = _read_manifest(workspace)["bundles"]["obsidian"]["files"][rel]
    (workspace / rel).write_text("// PI patch\n", encoding="utf-8")

    rc = main(["doctor", "--workspace", str(workspace), "--repair", "--json"])
    capsys.readouterr()

    assert rc == 0
    assert (workspace / rel).read_bytes() == (WORKSPACE_SEED / rel).read_bytes()
    assert sha256_file(workspace / rel) == recorded
