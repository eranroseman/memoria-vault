"""The installer skeleton cannot drift from the schema home (ADR-55 risk control)."""

import re
from pathlib import Path

import schema

ROOT = Path(__file__).resolve().parent.parent
INSTALL = ROOT / "scripts" / "install.sh"
MANIFEST = ROOT / "scripts" / "install" / "manifest.sh"


def _skeleton_dirs() -> set[str]:
    text = MANIFEST.read_text(encoding="utf-8")
    m = re.search(r"SKELETON_DIRS=\((.*?)\)", text, re.S)
    assert m, "SKELETON_DIRS not found in scripts/install/manifest.sh"
    return {line.strip() for line in m.group(1).splitlines()
            if line.strip() and not line.strip().startswith("#")}

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

def test_installer_deploys_exactly_the_shipped_profiles():
    text = INSTALL.read_text(encoding="utf-8")
    m = re.search(r'ALL_PROFILES="([^"]+)"', text)
    listed = set(m.group(1).split())
    shipped = {p.name for p in (ROOT / "src/.memoria/profiles").iterdir() if p.is_dir()}
    assert listed == shipped, f"ALL_PROFILES {listed ^ shipped} out of sync with src profiles"

def test_cron_wrappers_exist_for_wired_jobs():
    text = INSTALL.read_text(encoding="utf-8")
    for wrapper in re.findall(r'\.memoria/scripts/([a-z-]+\.sh)', text):
        assert (ROOT / "src/.memoria/scripts" / wrapper).is_file(), f"missing {wrapper}"

def test_lint_cron_writes_lint_findings_telemetry():
    text = (ROOT / "src/.memoria/scripts/lint-cron.sh").read_text(encoding="utf-8")
    assert "--jsonl-out" in text
    assert "{{VAULT_PATH}}/system/logs/lint-findings.jsonl" in text

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
    assert "qwen2.5:7b" in sh
    assert "qwen2.5:7b" in ps

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

def test_installer_installs_memoria_package_editable():
    text = INSTALL.read_text(encoding="utf-8")
    install_mcp_deps = re.search(
        r"install_mcp_deps\(\) \{(?P<body>.*?)\n\}",
        text,
        re.S,
    ).group("body")
    assert '-e "$REPO_DIR"' in install_mcp_deps
    assert "install Memoria editable" in install_mcp_deps

def test_installer_preserves_user_appearance_on_refresh():
    sh = (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
    ps = (ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")
    assert "--exclude '.obsidian/appearance.json'" in sh
    assert "'appearance.json'" in ps

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
    assert "Enable-MemoriaCssSnippets -RepoRoot (Get-LocalRepoRoot)" in ps

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
