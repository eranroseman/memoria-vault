"""The installer skeleton cannot drift from the schema home (ADR-55 risk control)."""

import re
import subprocess
from pathlib import Path

from memoria_vault.runtime.subsystems.lib import schema

ROOT = Path(__file__).resolve().parent.parent
INSTALL = ROOT / "scripts" / "install.sh"
INSTALL_PS = ROOT / "scripts" / "install.ps1"
MANIFEST = ROOT / "scripts" / "install" / "manifest.sh"
RUNTIME_TOOLS = ROOT / "scripts" / "install" / "runtime-tools.sh"


def _skeleton_dirs() -> set[str]:
    text = MANIFEST.read_text(encoding="utf-8")
    m = re.search(r"SKELETON_DIRS=\((.*?)\)", text, re.S)
    assert m, "SKELETON_DIRS not found in scripts/install/manifest.sh"
    return {
        line.strip()
        for line in m.group(1).splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


def test_skeleton_covers_the_schema_skeleton():
    """Every dir folders.yaml declares must be created by the installer."""
    declared = set(schema.load_folders()["skeleton"])
    installed = _skeleton_dirs()
    missing = declared - installed
    assert not missing, f"installer SKELETON_DIRS missing schema dirs: {sorted(missing)}"


def test_skeleton_covers_every_type_home():
    folders = schema.load_folders()
    installed = _skeleton_dirs()
    for t, home in folders["homes"].items():
        assert home in installed, f"type {t} home {home} not in SKELETON_DIRS"


def test_alpha11_fresh_package_contract_is_shipped():
    required_dirs = {
        ".memoria/index/qmd",
        ".memoria/config",
        ".memoria/quarantine",
        ".memoria/staging/catalog",
        ".memoria/staging/knowledge",
        ".memoria/staging/capabilities",
        "journal",
        "catalog",
        "catalog/sources",
        "catalog/entities",
        "knowledge",
        "knowledge/digests",
        "knowledge/notes",
        "knowledge/hubs",
        "knowledge/projects",
        "capabilities",
        "capabilities/adapters",
        "capabilities/operations",
        "capabilities/skills",
        "capabilities/workflows",
    }
    skeleton = set(schema.load_folders()["skeleton"])
    installed = _skeleton_dirs()

    assert required_dirs <= skeleton
    assert required_dirs <= installed
    for rel in required_dirs:
        assert (ROOT / "vault-template" / rel).is_dir(), rel
    for rel in (
        "index.md",
        "catalog/index.md",
        "knowledge/index.md",
        "capabilities/index.md",
        "references.bib",
        "steering.md",
        ".memoria/config/providers.yaml",
    ):
        assert (ROOT / "vault-template" / rel).is_file(), rel
    for rel in (
        ".memoria/index/qmd",
        ".memoria/quarantine",
        ".memoria/staging/catalog",
        ".memoria/staging/knowledge",
        ".memoria/staging/capabilities",
        "journal",
    ):
        assert (ROOT / "vault-template" / rel / ".gitkeep").is_file(), rel
    assert not (ROOT / "vault-template/.memoria/memoria.bib").exists()


def test_alpha11_template_has_no_legacy_alpha10_root_files():
    legacy_roots = (
        "vault-template/inbox",
        "vault-template/notes",
        "vault-template/projects",
        "vault-template/catalog/papers",
        "vault-template/catalog/people",
        "vault-template/catalog/organizations",
        "vault-template/catalog/venues",
        "vault-template/catalog/datasets",
        "vault-template/catalog/repositories",
        "vault-template/system/board",
        "vault-template/system/worklists",
    )
    leftovers = [
        path.relative_to(ROOT).as_posix()
        for rel in legacy_roots
        for path in (ROOT / rel).rglob("*")
        if path.is_file()
    ]
    assert not leftovers


def test_alpha11_template_has_no_legacy_alpha10_path_literals():
    roots = [
        ROOT / "vault-template/system",
        ROOT / "vault-template/AGENTS.md",
    ]
    retired = (
        "notes/claims",
        "notes/hubs",
        "notes/sources",
        "notes/fleeting",
        "catalog/papers",
        "catalog/repositories",
        "catalog/datasets",
        "memoria.bib",
    )
    offenders = []
    for root in roots:
        if not root.exists():
            continue
        paths = (
            [root] if root.is_file() else sorted(path for path in root.rglob("*") if path.is_file())
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for token in retired:
                if token in text:
                    offenders.append(f"{path.relative_to(ROOT)}: {token}")
    assert not offenders


def test_alpha14_installer_does_not_ship_installed_profiles():
    text = INSTALL.read_text(encoding="utf-8")
    assert "ALL_PROFILES" not in text
    assert "--profiles-only" not in text
    assert not (ROOT / "vault-template/.memoria/profiles").exists()
    assert not (ROOT / "vault-template/.memoria/lane-overrides").exists()


def test_cron_wrappers_exist_for_wired_jobs():
    text = INSTALL.read_text(encoding="utf-8")
    for wrapper in re.findall(r"\.memoria/scripts/([a-z-]+\.sh)", text):
        assert (ROOT / "vault-template/.memoria/scripts" / wrapper).is_file(), f"missing {wrapper}"


def test_standalone_installer_does_not_wire_hermes_cron_jobs():
    text = INSTALL.read_text(encoding="utf-8")
    runtime_tools = RUNTIME_TOOLS.read_text(encoding="utf-8")

    for source, dest, schedule, job in (
        ("board-export-cron.sh", "memoria-board-export.sh", "* * * * *", "memoria-board-export"),
        ("metrics-cron.sh", "memoria-metrics.sh", "30 6 * * 1", "memoria-metrics"),
    ):
        assert source not in text
        assert dest not in text
        assert schedule not in text
        assert job not in text
    for deleted in ("install_hermes_cron", "hermes cron", "cron create", "HERMES_HOME/scripts"):
        assert deleted not in runtime_tools


def test_linux_installer_defaults_to_standalone_cli_runtime():
    text = INSTALL.read_text(encoding="utf-8")

    assert "--with-hermes" not in text
    assert "--with-cluster" not in text
    assert "Proceed with the standalone Memoria install?" in text
    assert "memoria_vault.cli doctor bundle --workspace" in text
    for required in (
        "ensure_prereqs",
        "resolve_repo",
        "load_install_modules",
        "copy_vault",
        "install_runtime_deps",
        "ensure_qmd",
        "print_cli_next_steps",
    ):
        assert required in text
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


def test_windows_installer_defaults_to_standalone_cli_runtime():
    text = INSTALL_PS.read_text(encoding="utf-8")

    assert "[switch]$WithHermes" not in text
    assert "[switch]$WithCluster" not in text
    assert "Default path: standalone CLI/runtime workspace" in text
    assert "memoria_vault.cli doctor bundle --workspace" in text
    assert "memoria_vault.cli workspace rebuild --workspace" in text
    for required in (
        "Assert-RequiredCommands",
        "Get-RepoRoot",
        "Copy-VaultSource",
        "Install-RuntimeDeps",
        "Install-RuntimeScaffold",
        "Initialize-VaultGit",
        "Install-VaultHooks",
        "Install-Qmd",
        "Write-CliNextSteps",
    ):
        assert required in text
    for adapter_only in (
        "Install-Hermes",
        "Enable-MemoriaCssSnippets",
        "Install-Profiles",
        "Install-Crons",
        "Write-SecretsGuidance",
        "Install-WingetApp",
    ):
        assert adapter_only not in text


def test_lint_cron_writes_lint_findings_telemetry():
    text = (ROOT / "vault-template/.memoria/scripts/cron-runner.sh").read_text(encoding="utf-8")
    assert 'PYTHONPATH="$vault/.memoria:${PYTHONPATH:-}"' in text
    assert "--jsonl-out" in text
    assert "$vault/system/logs/lint-findings.jsonl" in text
    assert (
        '-m memoria_vault.cli workspace check --workspace "$vault" '
        "--schedule-id lint-integrity --json"
    ) in text


def test_worker_cron_runs_pi_observer_and_pending_queue():
    text = (ROOT / "vault-template/.memoria/scripts/cron-runner.sh").read_text(encoding="utf-8")
    assert (
        '-m memoria_vault.cli workspace scan --workspace "$vault" --schedule-id worker-scan --json'
    ) in text
    assert (
        '-m memoria_vault.cli workspace run --workspace "$vault" '
        "--schedule-id worker-drain --limit 10 --json"
    ) in text


def test_eval_cron_dispatches_through_cli_with_schedule_id():
    text = (ROOT / "vault-template/.memoria/scripts/cron-runner.sh").read_text(encoding="utf-8")
    assert (
        '-m memoria_vault.cli eval run --workspace "$vault" --schedule-id eval-dispatch --json'
    ) in text


def test_cron_runner_uses_memoria_python_without_template_brace(tmp_path):
    runner = ROOT / "vault-template/.memoria/scripts/cron-runner.sh"
    result = subprocess.run(
        ["bash", str(runner), "worker"],
        env={"MEMORIA_PYTHON": "/bin/true", "MEMORIA_VAULT": str(tmp_path)},
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_installer_registers_qmd_with_workspace_local_state():
    text = RUNTIME_TOOLS.read_text(encoding="utf-8")
    assert 'QMD_CONFIG_DIR="$VAULT_PATH/.memoria/index/qmd/config"' in text
    assert 'INDEX_PATH="$VAULT_PATH/.memoria/index/qmd/index.sqlite"' in text
    assert "--name memoria-checked" in text
    ps = INSTALL_PS.read_text(encoding="utf-8")
    assert "$env:QMD_CONFIG_DIR = $config" in ps
    assert "$env:INDEX_PATH = $index" in ps
    assert "--name memoria-checked --mask '**/*.md'" in ps


def test_installer_qmd_resolution_avoids_ambiguous_path_binary():
    text = RUNTIME_TOOLS.read_text(encoding="utf-8")
    assert "MEMORIA_QMD_BIN" in text
    assert "command -v qmd" not in text
    ps = INSTALL_PS.read_text(encoding="utf-8")
    assert "MEMORIA_QMD_BIN" in ps
    assert "Get-CommandPath @('qmd.cmd', 'qmd.exe', 'qmd')" not in ps


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
        assert "{{QMD}}" not in text
        assert "sed_repl()" not in text
        assert "Set-TemplateValues" not in text


def test_installer_treats_python_as_a_hard_prerequisite():
    text = INSTALL.read_text(encoding="utf-8")
    assert "python_install_guidance()" in text
    assert "Python 3 is required for Memoria's standalone CLI and deterministic tools." in text
    assert "sudo apt-get update && sudo apt-get install -y python3 python3-venv" in text
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
    assert "No Python found" in install_runtime_deps
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
    sh = (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
    ps = INSTALL_PS.read_text(encoding="utf-8")
    assert "This installer is fresh-install only" in sh
    assert "Refresh it from the repo" not in sh
    assert "This installer is fresh-install only" in ps


def test_fresh_installer_copies_the_runtime_src_tree():
    text = INSTALL.read_text(encoding="utf-8")
    ps = INSTALL_PS.read_text(encoding="utf-8")
    assert (ROOT / "vault-template" / "_nav.md").is_file()
    assert 'rsync -a --exclude \'.git\' "$src"/ "$VAULT_PATH"/' in text
    assert 'cp -R \\"$src\\"/. \\"$VAULT_PATH\\"/' in text
    assert 'run git -C "$VAULT_PATH" init -q' in text
    assert 'run git -C "$VAULT_PATH" branch -M main' in text
    assert 'git -C "$VAULT_PATH" commit' not in text
    assert "Invoke-Robocopy -Source $src -Destination $Vault" in ps
    assert "Invoke-Logged -FilePath 'git' -ArgumentList @('-C', $Vault, 'init', '-q')" in ps
    assert (
        "Invoke-Logged -FilePath 'git' -ArgumentList @('-C', $Vault, 'branch', '-M', 'main')" in ps
    )
    assert "memoria_vault.runtime.subsystems.integrity.linter.golden_restore" in ps
    assert "Install-VaultHooks" in ps


def test_windows_installer_uv_fallback_is_standalone():
    text = INSTALL_PS.read_text(encoding="utf-8")
    assert "Get-CommandPath @('uv.exe', 'uv')" in text
    assert "'--extra', 'mcp', 'hermes'" not in text
    assert "HermesHome" not in text
