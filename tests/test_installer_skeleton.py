"""The installer skeleton cannot drift from the schema home (ADR-55 risk control)."""

import re
import subprocess
from pathlib import Path

from operations.lib import schema

ROOT = Path(__file__).resolve().parent.parent
INSTALL = ROOT / "scripts" / "install.sh"
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
        ".memoria/quarantine",
        ".memoria/queue/pending",
        ".memoria/queue/running",
        ".memoria/queue/done",
        ".memoria/queue/failed",
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
        "capabilities/operations",
        "capabilities/skills",
        "capabilities/mcp",
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
    ):
        assert (ROOT / "vault-template" / rel).is_file(), rel
    for rel in (
        ".memoria/index/qmd",
        ".memoria/quarantine",
        ".memoria/queue/pending",
        ".memoria/queue/running",
        ".memoria/queue/done",
        ".memoria/queue/failed",
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
        ROOT / "vault-template/.memoria/lane-overrides",
        ROOT / "vault-template/.memoria/profiles",
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
        paths = (
            [root] if root.is_file() else sorted(path for path in root.rglob("*") if path.is_file())
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for token in retired:
                if token in text:
                    offenders.append(f"{path.relative_to(ROOT)}: {token}")
    assert not offenders


def test_installer_deploys_exactly_the_shipped_profiles():
    text = INSTALL.read_text(encoding="utf-8")
    m = re.search(r'ALL_PROFILES="([^"]+)"', text)
    listed = set(m.group(1).split())
    shipped = {p.name for p in (ROOT / "vault-template/.memoria/profiles").iterdir() if p.is_dir()}
    assert listed == shipped, f"ALL_PROFILES {listed ^ shipped} out of sync with src profiles"


def test_cron_wrappers_exist_for_wired_jobs():
    text = INSTALL.read_text(encoding="utf-8")
    for wrapper in re.findall(r"\.memoria/scripts/([a-z-]+\.sh)", text):
        assert (ROOT / "vault-template/.memoria/scripts" / wrapper).is_file(), f"missing {wrapper}"


def test_installer_cron_helper_keeps_all_job_schedules():
    helper = RUNTIME_TOOLS.read_text(encoding="utf-8")
    text = INSTALL.read_text(encoding="utf-8")

    assert "install_hermes_cron()" in helper
    assert 'hermes cron create "$schedule" --script "$dest_name" --no-agent' in helper
    for source, dest, schedule, job in (
        ("board-export-cron.sh", "memoria-board-export.sh", "* * * * *", "memoria-board-export"),
        ("sweeps-cron.sh", "memoria-sweeps.sh", "*/15 * * * *", "memoria-sweeps"),
        ("worker-cron.sh", "memoria-worker.sh", "* * * * *", "memoria-worker"),
        ("lint-cron.sh", "memoria-lint.sh", "0 6 * * *", "memoria-lint"),
        ("metrics-cron.sh", "memoria-metrics.sh", "30 6 * * 1", "memoria-metrics"),
        ("eval-cron.sh", "memoria-eval.sh", "0 7 1 */3 *", "memoria-eval"),
    ):
        assert source in text
        assert dest in text
        assert schedule in text
        assert job in text


def test_lint_cron_writes_lint_findings_telemetry():
    text = (ROOT / "vault-template/.memoria/scripts/cron-runner.sh").read_text(encoding="utf-8")
    assert "--jsonl-out" in text
    assert "$vault/system/logs/lint-findings.jsonl" in text
    assert '-m memoria_vault.runtime.worker --vault "$vault" integrity-sweep' in text


def test_worker_cron_runs_pi_observer_and_pending_queue():
    text = (ROOT / "vault-template/.memoria/scripts/cron-runner.sh").read_text(encoding="utf-8")
    assert '-m memoria_vault.runtime.worker --vault "$vault" observe-pi-edits' in text
    assert '-m memoria_vault.runtime.worker --vault "$vault" run-pending --limit 10' in text
    assert 'heartbeat="memoria-worker"' in text


def test_cron_runner_uses_memoria_python_without_template_brace(tmp_path):
    runner = ROOT / "vault-template/.memoria/scripts/cron-runner.sh"
    result = subprocess.run(
        ["bash", str(runner), "board-export"],
        env={"MEMORIA_PYTHON": "/bin/true", "MEMORIA_VAULT": str(tmp_path)},
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_zotero_left_the_installer():
    text = INSTALL.read_text(encoding="utf-8")
    assert "ensure_zotero" not in text and "zotero_plugins" not in text


def test_installer_escapes_template_replacements():
    text = INSTALL.read_text(encoding="utf-8")
    assert "sed_repl()" in text
    assert "s|{{VAULT_PATH}}|$VAULT_PATH|g" not in text
    assert "s|{{PYTHON}}|$pybin|g" not in text
    assert "s|{{QMD}}|${QMD_BIN:-qmd}|g" not in text


def test_installers_verify_generated_profiles_use_https_ssl_verify():
    sh = INSTALL.read_text(encoding="utf-8")
    ps = (ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")
    for text, function_name in (
        (sh, "verify_profile_obsidian_mcp"),
        (ps, "Assert-ProfileObsidianMcpHttps"),
    ):
        assert function_name in text
        assert "https://127.0.0.1:" in text
        assert "OBSIDIAN_MCP_PORT" in text
        assert "/mcp" in text
        assert "OBSIDIAN_MCP_SSL_VERIFY" in text
        assert 'url: "http://127' not in text
    assert 'url:[[:space:]]*"?https://127\\.0\\.0\\.1:' in sh
    assert 'ssl_verify:[[:space:]]*"?\\$\\{OBSIDIAN_MCP_SSL_VERIFY\\}' in sh


def test_installers_render_profile_model_placeholders():
    sh = INSTALL.read_text(encoding="utf-8")
    ps = (ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")
    for placeholder in ("{{MODEL_PROVIDER}}", "{{MODEL_BASE_URL}}", "{{MODEL_DEFAULT}}"):
        assert placeholder in sh
        assert placeholder in ps
    assert "MODEL_LOCAL_CONTEXT" in sh
    assert "{{MODEL_LOCAL_CONTEXT}}" in ps
    assert "MEMORIA_ENV" in sh
    assert "MEMORIA_ENV" in ps
    assert "meta-llama/llama-4-scout" in sh
    assert "meta-llama/llama-4-scout" in ps
    assert "MEMORIA_MODEL_PROVIDER" in sh
    assert "MEMORIA_MODEL_PROVIDER" in ps


def test_installer_removes_legacy_profile_mcp_json():
    text = INSTALL.read_text(encoding="utf-8")
    assert "remove_legacy_profile_mcp_json()" in text
    assert 'run rm -f "$profile_dir/mcp.json"' in text
    assert 'remove_legacy_profile_mcp_json "$HERMES_PROFILES_DIR/$p"' in text


def test_installer_treats_python_as_a_hard_prerequisite():
    text = INSTALL.read_text(encoding="utf-8")
    assert "python_install_guidance()" in text
    assert "Python 3 is required for Memoria's deterministic tools and MCP servers." in text
    assert "sudo apt-get update && sudo apt-get install -y python3 python3-venv" in text
    ensure_prereqs = re.search(
        r"ensure_prereqs\(\) \{(?P<body>.*?)\n\}",
        text,
        re.S,
    ).group("body")
    assert 'missing="$missing python3"' in ensure_prereqs
    assert "python_install_guidance" in ensure_prereqs
    assert "sudo apt-get install -y$missing" in ensure_prereqs


def test_installers_treat_git_as_a_hard_prerequisite():
    sh = INSTALL.read_text(encoding="utf-8")
    ps = (ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")
    assert "ensure_git_available()" in sh
    assert "Git is required on PATH" in sh
    assert "ensure_git_available" in re.search(
        r'if \[ "\$PROFILES_ONLY" -eq 1 \]; then(?P<body>.*?)\n  fi',
        sh,
        re.S,
    ).group("body")
    assert "function Assert-RequiredCommands" in ps
    assert "Git is required on PATH" in ps
    assert "Assert-RequiredCommands" in ps


def test_mcp_deps_fail_loudly_without_python():
    text = INSTALL.read_text(encoding="utf-8")
    install_mcp_deps = re.search(
        r"install_mcp_deps\(\) \{(?P<body>.*?)\n\}",
        text,
        re.S,
    ).group("body")
    assert "No Python found" in install_mcp_deps
    assert "python_install_guidance" in install_mcp_deps
    assert "sudo apt-get install -y python3 python3-venv" in install_mcp_deps
    assert "skipping MCP deps" not in install_mcp_deps


def test_installers_install_memoria_package_non_editable():
    text = INSTALL.read_text(encoding="utf-8")
    install_mcp_deps = re.search(
        r"install_mcp_deps\(\) \{(?P<body>.*?)\n\}",
        text,
        re.S,
    ).group("body")
    assert 'install --quiet "$REPO_DIR"' in install_mcp_deps
    assert '-e "$REPO_DIR"' not in install_mcp_deps
    ps = (ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")
    assert "@('-m', 'pip', 'install', $RepoRoot)" in ps


def test_installers_refuse_existing_vaults_instead_of_refreshing():
    sh = (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
    ps = (ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")
    assert "This installer is fresh-install only" in sh
    assert "Refresh it from the repo" not in sh
    assert "This installer is fresh-install only" in ps


def test_fresh_installer_copies_the_runtime_src_tree():
    text = INSTALL.read_text(encoding="utf-8")
    assert (ROOT / "vault-template" / "_nav.md").is_file()
    assert 'rsync -a --exclude \'.git\' "$src"/ "$VAULT_PATH"/' in text
    assert 'cp -R \\"$src\\"/. \\"$VAULT_PATH\\"/' in text


def test_installers_refuse_profile_deploy_without_policy_gate():
    sh = (ROOT / "scripts/install.sh").read_text(encoding="utf-8")
    ps = (ROOT / "scripts/install.ps1").read_text(encoding="utf-8")

    assert "refusing to deploy $prof without the write gate" in sh
    assert "refusing to deploy $ProfileName without the write gate" in ps


def test_installers_reconcile_memoria_css_snippets_without_clobbering_appearance():
    sh = (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
    ps = (ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")
    for text, function_name in (
        (sh, "ensure_memoria_css_snippets"),
        (ps, "Enable-MemoriaCssSnippets"),
    ):
        assert function_name in text
        assert "memoria-link-colors" in text
        assert "memoria-property-badges" in text
        assert "enabledCssSnippets" in text
    assert "ensure_memoria_css_snippets" in re.search(
        r'if \[ "\$PROFILES_ONLY" -eq 1 \]; then(?P<body>.*?)\n  fi',
        sh,
        re.S,
    ).group("body")
    assert "Enable-MemoriaCssSnippets -RepoRoot $repoRoot" in ps


def test_installers_reconcile_profile_skills_on_profile_deploy():
    sh = (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
    ps = (ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")

    for text, function_name in (
        (sh, "sync_profile_skills"),
        (ps, "Update-DeployedProfileSkills"),
    ):
        assert function_name in text
        assert ".no-bundled-skills" in text
        assert "Refusing to reconcile skills outside" in text
        assert "cleared profile skills" in text
        assert "refreshed profile skills" in text


def test_windows_profiles_only_reinstalls_mcp_deps_from_checkout():
    ps = (ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")
    body = re.search(
        r"else \{\n        Assert-RequiredCommands(?P<body>.*?)\n    \}\n\n    Install-Profiles",
        ps,
        re.S,
    ).group("body")

    assert "Get-LocalRepoRoot" in body
    assert "Run -ProfilesOnly from a memoria-vault checkout" in body
    assert "Install-McpDeps -RepoRoot $repoRoot" in body


def test_windows_installer_uv_fallback_enables_mcp_extra():
    text = (ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")
    assert "'--extra', 'mcp', 'hermes'" in text


def test_windows_installer_fails_on_placeholder_obsidian_mcp_env():
    text = (ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")
    assert "function Assert-ObsidianMcpEnv" in text
    assert "OBSIDIAN_MCP_PORT" in text
    assert "OBSIDIAN_MCP_SSL_VERIFY" in text
    assert "OBSIDIAN_API_KEY', 'OBSIDIAN_MCP_PORT', 'OBSIDIAN_MCP_SSL_VERIFY" in text
    assert "Test-PlaceholderValue" in text
    assert "rerun -ProfilesOnly" in text
