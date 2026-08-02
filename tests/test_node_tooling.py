"""Guards repo-local tooling used by required checks."""

import json
import re
import tomllib
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.static

# A release tag, not a moving ref: "v6.0.0", "0.16.0", "v0.11.0.1". Doubles as
# an exact npm version -- "10.0.1" passes, "^10.0.1" and "latest" do not.
RELEASE_TAG = re.compile(r"v?\d+(?:\.\d+)*")

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_JSON = ROOT / "package.json"
PACKAGE_LOCK = ROOT / "package-lock.json"
PYPROJECT = ROOT / "pyproject.toml"
PRECOMMIT = ROOT / ".pre-commit-config.yaml"
REQUIREMENTS_DEV = ROOT / "requirements-dev.txt"
DOCS_CONFIG = ROOT / "docs" / "_config.yml"


def _pins(package: str) -> list[str]:
    """The requirements-dev lines pinning `package` to an exact version.

    Matches on `package==`, so "pre-commit" never swallows "pre-commit-hooks".
    """
    requirements = REQUIREMENTS_DEV.read_text(encoding="utf-8").splitlines()
    return [line for line in requirements if line.strip().startswith(f"{package}==")]


def _hook(hook_id: str) -> dict:
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    hooks = [h for repo in config["repos"] for h in repo["hooks"] if h["id"] == hook_id]
    assert len(hooks) == 1
    return hooks[0]


def _assert_pinned_npm_tool(hook: dict, tool: str) -> None:
    """Assert the hook installs `tool` alone, pinned to an exact release."""
    dependencies = hook["additional_dependencies"]
    assert len(dependencies) == 1, f"{tool} must be the hook's only dependency: {dependencies}"
    package, _, version = dependencies[0].rpartition("@")
    assert package == tool, f"expected the {tool} package, got {package}"
    assert RELEASE_TAG.fullmatch(version), f"{tool} is not pinned to a release: {version}"


def test_required_node_checks_use_pinned_local_tools():
    package = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))

    assert "devDependencies" not in package
    assert "scripts" not in package
    assert not PACKAGE_LOCK.exists()

    # Same reasoning as the roster below: the shape of the pin is the invariant,
    # the version is Dependabot's to move. Each node check installs one tool at
    # an exact release, so an upgrade stays a reviewable diff and never becomes
    # a range or a floating tag.
    cspell = _hook("cspell")
    assert cspell["language"] == "node"
    assert cspell["entry"] == "cspell lint --no-progress --no-must-find-files"
    _assert_pinned_npm_tool(cspell, "cspell")

    markdownlint = _hook("markdownlint-structural")
    assert markdownlint["language"] == "node"
    assert markdownlint["entry"] == "markdownlint --config .markdownlint.json"
    _assert_pinned_npm_tool(markdownlint, "markdownlint-cli")


def test_precommit_hooks_use_pinned_tool_environments():
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    pinned_repos = {
        repo["repo"]: repo["rev"] for repo in config["repos"] if repo["repo"] != "local"
    }
    # The roster is the invariant; the revs are Dependabot's to move. Asserting
    # exact versions made every monthly hook bump red until someone hand-edited
    # this list (#1355, #1619) -- a mirror whose only failure mode was reporting
    # its own staleness. GitHub Actions are Dependabot-managed with no such
    # mirror and have never needed one.
    assert set(pinned_repos) == {
        "https://github.com/pre-commit/pre-commit-hooks",
        "https://github.com/gitleaks/gitleaks",
        "https://github.com/astral-sh/ruff-pre-commit",
        "https://github.com/adrienverge/yamllint",
        "https://github.com/shellcheck-py/shellcheck-py",
        "https://github.com/errata-ai/vale",
    }
    # What does matter: every hook environment is pinned to a release tag, so a
    # bump is a reviewable diff and never a silently moving branch.
    for repo, rev in pinned_repos.items():
        assert RELEASE_TAG.fullmatch(rev), f"{repo} is not pinned to a release tag: {rev}"

    for package in ("pre-commit", "pre-commit-hooks"):
        assert _pins(package), f"{package} must be pinned in requirements-dev.txt"
    # These come from the pinned hook environments above. Matching on the
    # package rather than one version closes the hole the old assertions left:
    # `ruff==0.15.21 not in requirements` said nothing about `ruff==0.16.0`.
    for tool in ("ruff", "shellcheck-py", "yamllint"):
        assert not _pins(tool), f"{tool} is supplied by pre-commit; drop the pip pin"


def test_coverage_audit_tool_is_pinned_for_contributors():
    assert _pins("pytest-cov"), "pytest-cov must be pinned in requirements-dev.txt"


def test_runtime_package_declares_yaml_dependency():
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))

    assert "PyYAML>=6.0" in pyproject["project"]["dependencies"]


def test_local_precommit_python_hooks_use_python3():
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    local_hooks = next(repo["hooks"] for repo in config["repos"] if repo["repo"] == "local")

    bare_python_entries = [
        hook["entry"]
        for hook in local_hooks
        if hook["entry"].startswith("python ") or " python -m " in hook["entry"]
    ]

    assert bare_python_entries == []


def test_pages_rewrites_relative_markdown_links():
    config = yaml.safe_load(DOCS_CONFIG.read_text(encoding="utf-8"))

    assert "jekyll-relative-links" in config["plugins"]
