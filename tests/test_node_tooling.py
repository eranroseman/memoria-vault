"""Guards the repo-local Node tooling used by required prose checks."""

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_JSON = ROOT / "package.json"
PRECOMMIT = ROOT / ".pre-commit-config.yaml"
CSPELL_WORKFLOW = ROOT / ".github/workflows/cspell.yml"
MARKDOWNLINT_WORKFLOW = ROOT / ".github/workflows/markdownlint.yml"
CONTRACT = ROOT / ".github/ruleset-contract.yaml"


def _local_hook(hook_id: str) -> dict:
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    hooks = [h for repo in config["repos"] for h in repo["hooks"] if h["id"] == hook_id]
    assert len(hooks) == 1
    return hooks[0]


def test_required_node_checks_use_pinned_local_tools():
    package = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))

    assert package["devDependencies"]["cspell"] == "8.19.4"
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


def test_precommit_node_hooks_fail_fast_without_network_downloads():
    for hook_id, command in (
        ("cspell", "cspell lint --no-progress --no-must-find-files"),
        ("markdownlint-structural", "markdownlint --config .markdownlint.json"),
    ):
        entry = _local_hook(hook_id)["entry"]
        assert "PATH=node_modules/.bin:$PATH" in entry
        assert command in entry
        assert "npx" not in entry


def test_lint_config_and_markdownlint_are_required_checks():
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))

    assert "lint-config" in contract["required_checks"]
    assert "markdownlint" in contract["required_checks"]
    assert contract["workflow_jobs"]["lint-config"] == ".github/workflows/lint-config.yml"
    assert contract["workflow_jobs"]["markdownlint"] == ".github/workflows/markdownlint.yml"
