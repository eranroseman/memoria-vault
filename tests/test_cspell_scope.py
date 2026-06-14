"""Guards the single-source cspell scope.

The set of spell-checked files must be defined once, in cspell.json (`files` +
`enableGlobDot` + `ignorePaths`). CI and pre-commit defer to it; neither may
reintroduce a hand-rolled file list (the old `git ls-files | grep 'docs/|src/'`
form), which is exactly the drift this PR removed. These tests fail if a future
change re-splits the scope across files.
"""

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CSPELL_JSON = ROOT / "cspell.json"
CSPELL_WORKFLOW = ROOT / ".github/workflows/cspell.yml"
PRECOMMIT = ROOT / ".pre-commit-config.yaml"
CONTRACT = ROOT / ".github/ruleset-contract.yaml"


def _cspell_hook() -> dict:
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    hooks = [h for repo in config["repos"] for h in repo["hooks"] if h["id"] == "cspell"]
    assert len(hooks) == 1, "expected exactly one cspell pre-commit hook"
    return hooks[0]


def test_cspell_json_owns_the_scope():
    config = json.loads(CSPELL_JSON.read_text(encoding="utf-8"))
    assert config.get("files") == ["**/*.md"], "cspell.json must select all markdown"
    assert config.get("enableGlobDot") is True, "dot-dirs (.agents/, src/.memoria/) need enableGlobDot"
    assert config.get("ignorePaths"), "exclusions must live in cspell.json ignorePaths"


def test_workflow_defers_to_cspell_json():
    run = CSPELL_WORKFLOW.read_text(encoding="utf-8")
    assert "git ls-files" not in run, "scope must not be re-derived from a file list"
    assert "docs/|src/" not in run, "scope must not be re-split across docs/src/root"
    assert '"**/*.md"' in run and "--gitignore" in run


def test_precommit_hook_triggers_on_any_markdown():
    hook = _cspell_hook()
    assert hook["files"] == r"\.md$", "pre-commit must trigger on any .md, not a docs/src/root allow-list"


def test_required_check_is_scope_agnostic():
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    assert "cspell" in contract["required_checks"]
    assert contract["workflow_jobs"].get("cspell") == ".github/workflows/cspell.yml"
