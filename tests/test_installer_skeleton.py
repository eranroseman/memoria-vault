"""The installer initializes from the packaged workspace seed."""

import re

from memoria_vault.runtime.subsystems.lib import schema
from tests.helpers import ROOT, WORKSPACE_SEED

INSTALL = ROOT / "scripts" / "install.sh"
INSTALL_PS = ROOT / "scripts" / "install.ps1"


def _seed_files() -> set[str]:
    return {
        path.relative_to(WORKSPACE_SEED).as_posix()
        for path in WORKSPACE_SEED.rglob("*")
        if path.is_file()
        and path.name != "__init__.py"
        and "__pycache__" not in path.relative_to(WORKSPACE_SEED).parts
    }


def test_schema_skeleton_covers_every_type_home():
    folders = schema.load_folders()
    skeleton = set(folders["skeleton"])

    for concept_type, home in folders["homes"].items():
        assert home in skeleton, f"type {concept_type} home {home} not in skeleton"


def test_alpha20_package_seed_is_runtime_minimum():
    expected_files = {
        ".githooks/pre-commit",
        ".gitignore",
        ".memoria/config/providers.yaml",
        ".memoria/eval/alpha15-seeded-errors.json",
        ".memoria/patterns/_preamble.md",
        ".memoria/schemas/calibration.yaml",
        ".memoria/schemas/folders.yaml",
        ".memoria/schemas/types/code-artifact.yaml",
        ".memoria/schemas/types/digest.yaml",
        ".memoria/schemas/types/fulltext.yaml",
        ".memoria/schemas/types/hub.yaml",
        ".memoria/schemas/types/note.yaml",
        ".memoria/schemas/types/project.yaml",
        ".obsidian/app.json",
        ".obsidian/community-plugins.json",
        ".obsidian/core-plugins.json",
        ".obsidian/plugins/memoria-obsidian/main.js",
        ".obsidian/plugins/memoria-obsidian/manifest.json",
        ".obsidian/plugins/memoria-obsidian/styles.css",
        "steering.md",
        "system/vocabulary.md",
    }

    assert _seed_files() == expected_files


def test_package_seed_does_not_ship_removed_payloads():
    forbidden = (
        ".memoria/templates",
        ".memoria/plugins",
        ".memoria/scripts",
        ".memoria/profiles",
        ".memoria/lane-overrides",
        ".memoria/design-system.md",
        "AGENTS.md",
        "AGENTS.override.md",
        "_nav.md",
        "home.md",
        "index.md",
        "bibliography.bib",
        "troubleshooting.md",
        "system/dashboards",
        "system/incidents",
        "system/manifest.jsonl",
    )
    for rel in forbidden:
        assert not (WORKSPACE_SEED / rel).exists(), rel
    assert not list(WORKSPACE_SEED.rglob(".gitkeep"))


def test_linux_installer_defaults_to_package_seed_runtime():
    text = INSTALL.read_text(encoding="utf-8")

    assert "--with-hermes" not in text
    assert "--with-cluster" not in text
    assert "Proceed with the standalone Memoria install?" in text
    assert "doctor bundle --workspace" in text
    assert "memoria_vault.cli" not in text
    for required in (
        "ensure_prereqs",
        "resolve_repo",
        "prepare_vault",
        "install_runtime_deps",
        "initialize_workspace",
        "wire_vault_hook",
        "print_cli_next_steps",
    ):
        assert required in text
    for removed in (
        "scripts/install/manifest.sh",
        "SKELETON_DIRS",
        "copy_vault",
        "rsync -a",
        "cp -R",
        "vault-template",
        ".memoria/scripts/cron-runner.sh",
    ):
        assert removed not in text
    for adapter_only in (
        "ensure_hermes",
        "install_profiles",
        "install_skills",
        "wire_telemetry_cron",
        "wire_sweeps_cron",
        "wire_worker_cron",
        "wire_lint_cron",
        "wire_metrics_cron",
        "wire_eval_cron",
        "ensure_obsidian",
        "print_secrets_guidance",
    ):
        assert adapter_only not in text


def test_windows_installer_defaults_to_package_seed_runtime():
    text = INSTALL_PS.read_text(encoding="utf-8")

    assert "[switch]$WithHermes" not in text
    assert "[switch]$WithCluster" not in text
    assert "Default path: standalone CLI/runtime workspace" in text
    assert "memoria.exe" in text
    assert "doctor bundle --workspace" in text
    assert "workspace rebuild --workspace" in text
    assert "memoria_vault.cli" not in text
    for required in (
        "Assert-RequiredCommands",
        "Get-RepoRoot",
        "Initialize-WorkspaceTarget",
        "Install-RuntimeDeps",
        "Initialize-WorkspaceFromPackage",
        "Install-VaultHooks",
        "Write-CliNextSteps",
    ):
        assert required in text
    for removed in (
        "Copy-VaultSource",
        "Install-RuntimeScaffold",
        "Initialize-VaultGit",
        "Invoke-Robocopy",
        "vault-template",
        ".memoria/scripts/cron-runner.sh",
    ):
        assert removed not in text
    for adapter_only in (
        "Install-Hermes",
        "Enable-MemoriaCssSnippets",
        "Install-Profiles",
        "Install-Crons",
        "Write-SecretsGuidance",
        "Install-WingetApp",
    ):
        assert adapter_only not in text


def test_installer_does_not_install_or_register_search_binaries():
    sh = INSTALL.read_text(encoding="utf-8")
    ps = INSTALL_PS.read_text(encoding="utf-8")

    for source in (sh, ps):
        assert "MEMORIA_SEARCH_BIN" not in source
        assert "collection add" not in source
        assert "embed --chunk-strategy" not in source
        assert ".memoria/index/search/checked" not in source
        assert "--name memoria-checked" not in source


def test_zotero_left_the_installer():
    text = INSTALL.read_text(encoding="utf-8")
    assert "ensure_zotero" not in text and "zotero_plugins" not in text
    assert "Zotero.Zotero" not in INSTALL_PS.read_text(encoding="utf-8")


def test_installer_has_no_profile_template_replacement_layer():
    sh = INSTALL.read_text(encoding="utf-8")
    ps = INSTALL_PS.read_text(encoding="utf-8")
    for text in (sh, ps):
        assert "{{VAULT_PATH}}" not in text
        assert "{{PYTHON}}" not in text
        assert "sed_repl()" not in text
        assert "Set-TemplateValues" not in text


def test_installer_treats_python_as_a_hard_prerequisite():
    text = INSTALL.read_text(encoding="utf-8")
    assert "python_install_guidance()" in text
    assert "Python 3.12+ + venv" in text
    assert "Python 3.12+ is required for Memoria's standalone CLI and deterministic tools." in text
    assert "sudo apt-get update && sudo apt-get install -y python3 python3-venv" in text
    assert "python_version_ok python3" in text
    assert "sys.version_info >= (3, 12)" in text
    ps = INSTALL_PS.read_text(encoding="utf-8")
    assert "Assert-PythonRuntime" in ps
    assert "Memoria requires Python 3.12+" in ps
    ensure_prereqs = re.search(
        r"ensure_prereqs\(\) \{(?P<body>.*?)\n\}",
        text,
        re.S,
    ).group("body")
    assert 'missing="$missing python3"' in ensure_prereqs
    assert "have pandoc || missing" not in ensure_prereqs
    assert "Pandoc not found" in ensure_prereqs
    assert "python_install_guidance" in ensure_prereqs
    assert "sudo apt-get install -y$missing" in ensure_prereqs


def test_installers_treat_git_as_a_hard_prerequisite():
    sh = INSTALL.read_text(encoding="utf-8")
    ps = INSTALL_PS.read_text(encoding="utf-8")
    assert "ensure_git_available()" in sh
    assert "Git is required on PATH" in sh
    assert "function Assert-RequiredCommands" in ps
    assert "Git is required on PATH" in ps
    assert "Assert-RequiredCommands" in ps


def test_runtime_deps_fail_loudly_without_python():
    text = INSTALL.read_text(encoding="utf-8")
    install_runtime_deps = re.search(
        r"install_runtime_deps\(\) \{(?P<body>.*?)\n\}",
        text,
        re.S,
    ).group("body")
    assert "No Python 3.12+ found" in install_runtime_deps
    assert "python_install_guidance" in install_runtime_deps
    assert "sudo apt-get install -y python3 python3-venv" in install_runtime_deps
    assert "skipping MCP deps" not in install_runtime_deps


def test_installers_install_memoria_package_non_editable():
    text = INSTALL.read_text(encoding="utf-8")
    install_runtime_deps = re.search(
        r"install_runtime_deps\(\) \{(?P<body>.*?)\n\}",
        text,
        re.S,
    ).group("body")
    assert 'install --quiet "$REPO_DIR"' in install_runtime_deps
    assert '-e "$REPO_DIR"' not in install_runtime_deps
    ps = INSTALL_PS.read_text(encoding="utf-8")
    assert "@('-m', 'pip', 'install', $RepoRoot)" in ps


def test_installers_refuse_existing_vaults_instead_of_refreshing():
    sh = INSTALL.read_text(encoding="utf-8")
    ps = INSTALL_PS.read_text(encoding="utf-8")
    assert "This installer is fresh-install only" in sh
    assert "Refresh it from the repo" not in sh
    assert "This installer is fresh-install only" in ps


def test_windows_installer_uv_fallback_is_standalone():
    text = INSTALL_PS.read_text(encoding="utf-8")
    assert "Get-CommandPath @('uv.exe', 'uv')" in text
    assert "'--extra', 'mcp', 'hermes'" not in text
    assert "HermesHome" not in text
