"""Fast Memoria-test refresh helper keeps runtime state out of the blast radius."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "refresh-test-vault.sh"
WORKSPACES = ROOT / "vault-template" / ".obsidian" / "workspaces.json"


def _script() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def _refresh_entries(sync_call: str) -> set[str]:
    match = re.search(
        rf"for rel in \\\n(?P<body>.*?)\ndo\n  {sync_call} \"\$rel\"", _script(), re.S
    )
    assert match, f"{sync_call} loop not found"
    return {
        line.strip().removesuffix("\\").strip()
        for line in match.group("body").splitlines()
        if line.strip()
    }


def _workspace_file_refs() -> set[str]:
    data = json.loads(WORKSPACES.read_text(encoding="utf-8"))
    refs: set[str] = set()
    stack = list(data["workspaces"].values())
    while stack:
        node = stack.pop()
        state = node.get("state", {})
        file = state.get("state", {}).get("file")
        if file:
            refs.add(file)
        stack.extend(node.get("children", []))
    return refs


def test_refresh_test_vault_helper_exists_and_is_executable():
    assert SCRIPT.is_file()
    assert SCRIPT.stat().st_mode & 0o111
    assert _script().startswith("#!/usr/bin/env bash\n")


def test_refresh_helper_preserves_runtime_only_state():
    text = _script()
    for marker in (
        ".memoria/.venv/bin/python",
        "system/logs",
        "system/exports",
        "plugins/agent-client/data.json",
        "plugins/obsidian-local-rest-api/data.json",
    ):
        assert marker in text
    assert 'rsync -a --delete "$SRC"/ "$VAULT"/' not in text


def test_refresh_helper_updates_source_owned_surfaces_and_golden_copy():
    text = _script()
    for marker in (
        "system/dashboards",
        "system/scripts",
        "system/templates",
        "capabilities",
        "spaces",
        "index.md",
        "catalog/catalog.base",
        "catalog/index.md",
        "knowledge/index.md",
        "capabilities/index.md",
        "references.bib",
        ".obsidian",
        "golden_restore",
        "stage",
    ):
        assert marker in text


def test_refresh_helper_deploys_every_workspace_referenced_file():
    dirs = _refresh_entries("sync_dir")
    files = _refresh_entries("sync_file")

    def deployed(ref: str) -> bool:
        return ref in files or any(ref == d or ref.startswith(f"{d}/") for d in dirs)

    missing = {ref for ref in _workspace_file_refs() if not deployed(ref)}

    assert not missing, f"workspace file refs missing from refresh deploy set: {sorted(missing)}"


def test_refresh_helper_has_no_profile_redeploy_mode():
    text = _script()
    assert "--profiles" not in text
    assert "--profiles-only" not in text
