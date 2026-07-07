"""Guards repo-local tooling used by required checks."""

import json
import os
import subprocess
import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_JSON = ROOT / "package.json"
PYPROJECT = ROOT / "pyproject.toml"
PRECOMMIT = ROOT / ".pre-commit-config.yaml"
REQUIREMENTS_DEV = ROOT / "requirements-dev.txt"
CSPELL_WORKFLOW = ROOT / ".github/workflows/cspell.yml"
MARKDOWNLINT_WORKFLOW = ROOT / ".github/workflows/markdownlint.yml"
CONTRACT = ROOT / ".github/ruleset-contract.yaml"
DOCS_CONFIG = ROOT / "docs" / "_config.yml"
NODE_TOOL_WRAPPER = ROOT / "scripts" / "dev" / "run-node-tool.sh"


def _hook(hook_id: str) -> dict:
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    hooks = [h for repo in config["repos"] for h in repo["hooks"] if h["id"] == hook_id]
    assert len(hooks) == 1
    return hooks[0]


def test_required_node_checks_use_pinned_local_tools():
    package = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))

    assert package["devDependencies"]["cspell"] == "10.0.1"
    assert package["devDependencies"]["markdownlint-cli"] == "0.49.0"
    assert package["scripts"]["spellcheck"] == (
        'cspell lint --no-progress --no-must-find-files --gitignore "**/*.md"'
    )
    assert package["scripts"]["markdownlint"] == (
        'markdownlint --config .markdownlint.json "docs/**/*.md"'
    )


def test_node_workflows_do_not_download_cli_packages_at_run_time():
    for path in (CSPELL_WORKFLOW, MARKDOWNLINT_WORKFLOW):
        text = path.read_text(encoding="utf-8")
        assert "npx --yes" not in text
        assert "npm ci --ignore-scripts" in text


def test_precommit_hooks_use_pinned_tool_environments():
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    pinned_repos = {
        repo["repo"]: repo["rev"] for repo in config["repos"] if repo["repo"] != "local"
    }
    assert pinned_repos == {
        "https://github.com/pre-commit/pre-commit-hooks": "v6.0.0",
        "https://github.com/gitleaks/gitleaks": "v8.30.1",
        "https://github.com/astral-sh/ruff-pre-commit": "v0.15.20",
        "https://github.com/adrienverge/yamllint": "v1.38.0",
        "https://github.com/shellcheck-py/shellcheck-py": "v0.11.0.1",
    }

    requirements = REQUIREMENTS_DEV.read_text(encoding="utf-8").splitlines()
    for package in (
        "pre-commit==4.6.0",
        "pre-commit-hooks==6.0.0",
    ):
        assert package in requirements
    assert "ruff==0.15.20" not in requirements
    assert "shellcheck-py==0.11.0.1" not in requirements
    assert "yamllint==1.38.0" not in requirements


def test_runtime_package_declares_yaml_dependency():
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))

    assert "PyYAML>=6.0" in pyproject["project"]["dependencies"]


def test_precommit_node_hooks_fail_fast_without_network_downloads():
    wrapper = "scripts/dev/run-node-tool.sh"
    for hook_id, command in (
        ("cspell", "cspell lint --no-progress --no-must-find-files"),
        ("markdownlint-structural", "markdownlint --config .markdownlint.json"),
    ):
        entry = _hook(hook_id)["entry"]
        assert entry.startswith(f"{wrapper} ")
        assert command in entry
        assert "npx" not in entry

    assert os.access(NODE_TOOL_WRAPPER, os.X_OK)


def test_node_tool_wrapper_fails_with_setup_hint(tmp_path):
    result = subprocess.run(
        [str(NODE_TOOL_WRAPPER), "cspell", "--version"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 127
    assert "Run npm ci in this worktree" in result.stderr
    assert "SKIP=cspell" in result.stderr


def test_local_precommit_python_hooks_use_python3():
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    local_hooks = next(repo["hooks"] for repo in config["repos"] if repo["repo"] == "local")

    bare_python_entries = [
        hook["entry"]
        for hook in local_hooks
        if hook["entry"].startswith("python ") or " python -m " in hook["entry"]
    ]

    assert bare_python_entries == []


def test_lint_config_and_markdownlint_are_required_checks():
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))

    assert "lint-config" in contract["required_checks"]
    assert "markdownlint" in contract["required_checks"]
    assert contract["workflow_jobs"]["lint-config"] == ".github/workflows/lint-config.yml"
    assert contract["workflow_jobs"]["markdownlint"] == ".github/workflows/markdownlint.yml"


def test_pages_rewrites_relative_markdown_links():
    config = yaml.safe_load(DOCS_CONFIG.read_text(encoding="utf-8"))

    assert "jekyll-relative-links" in config["plugins"]
