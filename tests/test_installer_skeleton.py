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


def test_zotero_left_the_installer():
    text = INSTALL.read_text(encoding="utf-8")
    assert "ensure_zotero" not in text and "zotero_plugins" not in text


def test_installer_escapes_template_replacements():
    text = INSTALL.read_text(encoding="utf-8")
    assert "sed_repl()" in text
    assert "s|{{VAULT_PATH}}|$VAULT_PATH|g" not in text
    assert "s|{{PYTHON}}|$pybin|g" not in text
    assert "s|{{QMD}}|${QMD_BIN:-qmd}|g" not in text


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
