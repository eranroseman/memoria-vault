"""Guards repo-local tooling used by required checks."""

import json
import re
import tomllib

import pytest
import yaml

from tests.paths import ROOT

pytestmark = pytest.mark.static

# A release tag, not a moving ref: "v6.0.0", "0.16.0", "v0.11.0.1". Doubles as
# an exact npm version -- "10.0.1" passes, "^10.0.1" and "latest" do not.
RELEASE_TAG = re.compile(r"v?\d+(?:\.\d+)*")

PACKAGE_JSON = ROOT / "package.json"
PACKAGE_LOCK = ROOT / "package-lock.json"
PYPROJECT = ROOT / "pyproject.toml"
PRECOMMIT = ROOT / ".pre-commit-config.yaml"
REQUIREMENTS_DEV = ROOT / "requirements-dev.txt"
DOCS_CONFIG = ROOT / "docs" / "_config.yml"
OBSIDIAN_PACKAGE = ROOT / "packages" / "memoria-obsidian" / "package.json"
OBSIDIAN_LOCK = ROOT / "packages" / "memoria-obsidian" / "package-lock.json"
VERIFY_WORKFLOW = ROOT / ".github" / "workflows" / "verify.yml"
DEPENDABOT = ROOT / ".github" / "dependabot.yml"
VSCODE_SETTINGS = ROOT / ".vscode" / "settings.json"


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


def test_obsidian_adapter_build_dependency_is_pinned_and_provisioned_in_ci():
    """Catch an adapter build that drifts from its lockfile or CI setup."""
    package = json.loads(OBSIDIAN_PACKAGE.read_text(encoding="utf-8"))
    lock = json.loads(OBSIDIAN_LOCK.read_text(encoding="utf-8"))
    workflow = yaml.safe_load(VERIFY_WORKFLOW.read_text(encoding="utf-8"))
    dependabot = yaml.safe_load(DEPENDABOT.read_text(encoding="utf-8"))

    assert package["scripts"]["build"] == "node scripts/build.mjs"
    assert package["scripts"]["check"] == "node scripts/build.mjs --check"
    assert RELEASE_TAG.fullmatch(package["devDependencies"]["esbuild"])
    assert (
        lock["packages"][""]["devDependencies"]["esbuild"] == package["devDependencies"]["esbuild"]
    )

    # The gate runs in the `shards` matrix job; `verify` is the fan-in that owns
    # the required-check name. Every shard installs the adapter build dependency,
    # because the roster it runs is decided at run time.
    steps = workflow["jobs"]["shards"]["steps"]
    install_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("run") == "npm ci --prefix packages/memoria-obsidian"
    )
    verify_index = next(
        index
        for index, step in enumerate(steps)
        if step.get("run", "").startswith("python scripts/verify")
    )
    assert steps[install_index]["name"] == "Install Obsidian adapter build dependency"
    assert install_index < verify_index

    npm_updates = [
        update for update in dependabot["updates"] if update["package-ecosystem"] == "npm"
    ]
    assert len(npm_updates) == 1
    assert npm_updates[0]["directory"] == "/packages/memoria-obsidian"


def test_oxc_editor_tools_match_the_pinned_hook_versions():
    """Catch the editor formatting differently from the gate.

    oxlint and oxfmt run twice over the same files: from the pinned pre-commit
    hook environments in `scripts/verify`, and from `node_modules` for the
    `oxc.oxc-vscode` extension, which does not bundle either tool. Two pins for
    one tool is a version skew waiting to happen -- and a skewed oxfmt reformats
    on save exactly what the commit hook then reformats back. Only oxfmt's
    freeze is expressed in `.github/dependabot.yml`; nothing but this assertion
    keeps the npm side equal to the hook side.
    """
    package = json.loads(OBSIDIAN_PACKAGE.read_text(encoding="utf-8"))
    lock = json.loads(OBSIDIAN_LOCK.read_text(encoding="utf-8"))
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    revs = {repo["repo"]: repo["rev"] for repo in config["repos"] if repo["repo"] != "local"}

    for tool in ("oxlint", "oxfmt"):
        pinned = package["devDependencies"][tool]
        assert RELEASE_TAG.fullmatch(pinned), f"{tool} is not pinned to a release: {pinned}"
        assert lock["packages"][""]["devDependencies"][tool] == pinned
        hook_rev = revs[f"https://github.com/oxc-project/mirrors-{tool}"]
        assert hook_rev.removeprefix("v") == pinned, (
            f"{tool} is {pinned} in packages/memoria-obsidian but {hook_rev} in "
            "the pre-commit hook; the editor and the gate would disagree"
        )

    # The extension is what reads those node_modules; recommending it is the
    # only thing that makes the pin above serve anyone.
    extensions = json.loads((ROOT / ".vscode" / "extensions.json").read_text(encoding="utf-8"))
    assert "oxc.oxc-vscode" in extensions["recommendations"]


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
        "https://github.com/pre-commit/mirrors-mypy",
        "https://github.com/adrienverge/yamllint",
        "https://github.com/shellcheck-py/shellcheck-py",
        "https://github.com/oxc-project/mirrors-oxlint",
        "https://github.com/oxc-project/mirrors-oxfmt",
        "https://github.com/errata-ai/vale",
    }
    # What does matter: every hook environment is pinned to a release tag, so a
    # bump is a reviewable diff and never a silently moving branch.
    for repo, rev in pinned_repos.items():
        assert RELEASE_TAG.fullmatch(rev), f"{repo} is not pinned to a release tag: {rev}"

    for package in ("pre-commit", "pre-commit-hooks", "setuptools"):
        assert _pins(package), f"{package} must be pinned in requirements-dev.txt"
    # These come from the pinned hook environments above. Matching on the
    # package rather than one version closes the hole the old assertions left:
    # `ruff==0.15.21 not in requirements` said nothing about `ruff==0.16.0`.
    for tool in ("shellcheck-py", "yamllint"):
        assert not _pins(tool), f"{tool} is supplied by pre-commit; drop the pip pin"

    # ruff is the exception, and only because the Ruff VS Code extension needs
    # it: `ruff.importStrategy` is `fromEnvironment`, so the editor formats with
    # the pip-installed ruff and silently falls back to its own bundled copy --
    # pinned by no gate -- when there is none. Two pins for one tool is a skew
    # waiting to happen, and a skewed ruff format-on-save writes exactly what
    # the commit-stage hook writes back. This is the only thing holding them
    # equal; see the same assertion for oxlint/oxfmt above.
    ruff_pins = _pins("ruff")
    assert len(ruff_pins) == 1, f"expected exactly one ruff pin, got {ruff_pins}"
    ruff_version = ruff_pins[0].strip().removeprefix("ruff==")
    ruff_rev = pinned_repos["https://github.com/astral-sh/ruff-pre-commit"]
    assert ruff_rev.removeprefix("v") == ruff_version, (
        f"ruff is {ruff_version} in requirements-dev.txt but {ruff_rev} in the "
        "pre-commit hook; the editor and the gate would disagree"
    )

    # mypy is the second tool pinned twice, and for the same reason as ruff:
    # `mypy-type-checker.importStrategy` is `fromEnvironment`, so a skewed
    # editor copy reports type errors the gate does not, and misses ones it does.
    mypy_pins = _pins("mypy")
    assert len(mypy_pins) == 1, f"expected exactly one mypy pin, got {mypy_pins}"
    mypy_version = mypy_pins[0].strip().removeprefix("mypy==")
    mypy_rev = pinned_repos["https://github.com/pre-commit/mirrors-mypy"]
    assert mypy_rev.removeprefix("v") == mypy_version, (
        f"mypy is {mypy_version} in requirements-dev.txt but {mypy_rev} in the "
        "pre-commit hook; the editor and the gate would disagree"
    )


def test_mypy_gate_is_source_scoped_and_pinned_for_offline_manual_checks():
    """The manual gate owns one fully pinned, package-wide MyPy invocation."""
    mypy = _hook("mypy")
    assert mypy["stages"] == ["manual"]
    assert mypy["pass_filenames"] is False
    assert mypy["additional_dependencies"] == [
        "types-PyYAML==6.0.12.20260724",
        "pydantic-ai-slim[openai]==2.28.0",
    ]

    config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["tool"]["mypy"]
    assert config["files"] == ["src/memoria_vault"]
    assert config["python_version"] == "3.12"
    assert config["warn_redundant_casts"] is True
    assert config["warn_unused_ignores"] is True
    assert config["warn_unused_configs"] is True
    assert config["no_implicit_optional"] is True
    assert "check_untyped_defs" not in config
    assert "strict_equality" not in config
    assert config["overrides"] == [{"module": ["fitz", "mcp.*"], "ignore_missing_imports": True}]


def test_python_editor_applies_ruff_import_and_fix_actions_on_save():
    """Keep saved Python aligned with the Ruff gate's fixes."""
    raw_settings = VSCODE_SETTINGS.read_text(encoding="utf-8")
    settings = json.loads(re.sub(r"^\s*//.*$", "", raw_settings, flags=re.MULTILINE))

    python_settings = settings["[python]"]
    assert python_settings["editor.defaultFormatter"] == "charliermarsh.ruff"
    assert python_settings["editor.formatOnSave"] is True
    code_actions = python_settings["editor.codeActionsOnSave"]
    assert code_actions["source.organizeImports.ruff"] == "explicit"
    assert code_actions["source.fixAll.ruff"] == "explicit"


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
