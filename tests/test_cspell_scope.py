"""Guards the single-source cspell scope.

The set of spell-checked files must be defined once, in cspell.json (`files` +
`enableGlobDot` + `ignorePaths`). CI and pre-commit defer to it; neither may
reintroduce a hand-rolled file list (for example `git ls-files | grep ...`
form), which is exactly the drift this PR removed. These tests fail if a future
change re-splits the scope across files.
"""

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CSPELL_JSON = ROOT / "cspell.json"
PRECOMMIT = ROOT / ".pre-commit-config.yaml"


def _cspell_hook() -> dict:
    config = yaml.safe_load(PRECOMMIT.read_text(encoding="utf-8"))
    hooks = [h for repo in config["repos"] for h in repo["hooks"] if h["id"] == "cspell"]
    assert len(hooks) == 1, "expected exactly one cspell pre-commit hook"
    return hooks[0]


def test_cspell_json_owns_the_scope():
    config = json.loads(CSPELL_JSON.read_text(encoding="utf-8"))
    assert config.get("files") == ["**/*.md"], "cspell.json must select all markdown"
    assert config.get("enableGlobDot") is True, "dot-dirs like .github/ need enableGlobDot"
    assert config.get("ignorePaths"), "exclusions must live in cspell.json ignorePaths"
    assert "design-history/**" not in config["ignorePaths"]


def test_precommit_hook_triggers_on_any_markdown():
    hook = _cspell_hook()
    assert hook["files"] == r"\.md$", (
        "pre-commit must trigger on any .md, not a docs/src/root allow-list"
    )
    assert hook["language"] == "node"
    assert hook["entry"] == "cspell lint --no-progress --no-must-find-files"
    assert hook["additional_dependencies"] == ["cspell@10.0.1"]
    assert "npx" not in hook["entry"]
