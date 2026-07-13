"""Package-spine smoke tests for the installed Memoria package."""

from __future__ import annotations

import os
import subprocess
import sys
import tomllib
from importlib.resources import files
from pathlib import Path

import memoria_vault
import memoria_vault.runtime.policy as packaged_policy

ROOT = Path(__file__).resolve().parent.parent


def test_pyproject_declares_installable_memoria_package():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["name"] == "memoria-vault"
    assert data["project"]["version"] == memoria_vault.__version__
    assert data["project"]["requires-python"] == ">=3.12"
    assert data["tool"]["setuptools"]["packages"]["find"]["where"] == ["src"]
    assert data["tool"]["setuptools"]["packages"]["find"]["include"] == ["memoria_vault*"]
    assert data["tool"]["setuptools"]["package-data"]["memoria_vault"] == ["runtime/*.sql"]
    assert data["tool"]["setuptools"]["package-data"]["memoria_vault.product.workspace_seed"] == [
        ".githooks/*",
        ".memoria/config/*",
        ".memoria/eval/*",
        ".memoria/patterns/*",
        ".memoria/schemas/*.yaml",
        ".memoria/schemas/types/*.yaml",
        ".obsidian/*.json",
        ".obsidian/plugins/memoria-obsidian/*.js",
        ".obsidian/plugins/memoria-obsidian/*.json",
        ".obsidian/plugins/memoria-obsidian/*.css",
        ".gitignore",
        "steering.md",
        "system/*.md",
    ]


def test_stack_dependencies_stay_small_and_no_orm():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = {
        dependency.split("[", 1)[0].split(">=", 1)[0]
        for dependency in data["project"]["dependencies"]
    }

    assert dependencies.isdisjoint({"click", "typer"})
    assert dependencies.isdisjoint({"alembic", "django", "peewee", "sqlalchemy"})
    assert "mcp" not in dependencies
    assert data["project"]["optional-dependencies"]["mcp"] == ["mcp>=1.27"]


def test_runtime_sqlite_schema_is_packaged_resource():
    schema = files("memoria_vault.runtime").joinpath("schema.sql").read_text(encoding="utf-8")
    source = (ROOT / "src/memoria_vault/runtime/state.py").read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS operation_requests" in schema
    assert "PRAGMA user_version = 9" in schema
    assert "CREATE TABLE IF NOT EXISTS" not in source


def test_bare_package_import_does_not_need_mcp_sdk():
    code = (
        "import memoria_vault; "
        "from memoria_vault.runtime.policy import normalize_path; "
        "assert memoria_vault.__version__; "
        "assert normalize_path('./notes/claims/x.md') == 'notes/claims/x.md'"
    )
    env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, check=True)


def test_vault_side_policy_package_is_removed():
    assert not (ROOT / "src/memoria_vault/product/workspace_seed/.memoria/memoria_runtime").exists()
    assert packaged_policy.normalize_path("./a/b/../c") == "a/c"


def test_workspace_seed_is_packaged_runtime_minimum():
    seed = files("memoria_vault.product.workspace_seed")

    for rel in (
        ".githooks/pre-commit",
        ".gitignore",
        ".memoria/config/providers.yaml",
        ".memoria/eval/alpha15-seeded-errors.json",
        ".memoria/patterns/_preamble.md",
        ".memoria/schemas/folders.yaml",
        ".memoria/schemas/types/note.yaml",
        ".obsidian/app.json",
        ".obsidian/core-plugins.json",
        ".obsidian/community-plugins.json",
        ".obsidian/plugins/memoria-obsidian/main.js",
        ".obsidian/plugins/memoria-obsidian/manifest.json",
        ".obsidian/plugins/memoria-obsidian/schema.js",
        ".obsidian/plugins/memoria-obsidian/styles.css",
        "steering.md",
        "system/vocabulary.md",
    ):
        assert seed.joinpath(*rel.split("/")).is_file(), rel

    for rel in (
        "AGENTS.md",
        "AGENTS.override.md",
        "home.md",
        "_nav.md",
        "troubleshooting.md",
        "index.md",
        "bibliography.bib",
        ".memoria/design-system.md",
        ".memoria/templates/note.md",
        ".memoria/plugins/memoria-policy-gate/plugin.yaml",
        ".memoria/scripts/cron-runner.sh",
        "system/dashboards/board-state.md",
        "system/manifest.jsonl",
        "notes/.gitkeep",
    ):
        assert not seed.joinpath(*rel.split("/")).is_file(), rel
