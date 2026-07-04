import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "scripts" / "test_env_harness.py"
CASSETTE = ROOT / "tests" / "fixtures" / "test-env" / "cassettes" / "package-gate-golden-path.json"


def _load_harness():
    spec = importlib.util.spec_from_file_location("test_env_harness", HARNESS)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_cassette_matches_tool_name_and_arg_shape():
    harness = _load_harness()
    cassette = harness.load_cassette(CASSETTE)

    assert cassette["match"] == "tool_name+arg_shape"
    assert cassette["gates"] == ["source", "package"]
    assert [step["id"] for step in cassette["steps"]][:3] == [
        "seed-project",
        "seed-thesis",
        "seed-supporting-note",
    ]
    for step in cassette["steps"]:
        assert harness.arg_shape(step["args"]) == step["arg_shape"]


def test_cassette_replay_runs_model_free_l4_path(tmp_path):
    harness = _load_harness()

    summary = harness.replay(ROOT, tmp_path, CASSETTE)

    assert summary["cassette"] == "package-gate-golden-path"
    assert "knowledge/projects/harness.md" in summary["artifacts"]
    assert "knowledge/notes/harness-support.md" in summary["artifacts"]
    assert "knowledge/projects/harness/argument.canvas" in summary["artifacts"]
    assert not (tmp_path / "knowledge/notes/blocked-by-harness.md").exists()

    canvas = json.loads(
        (tmp_path / "knowledge/projects/harness/argument.canvas").read_text(encoding="utf-8")
    )
    assert len(canvas["nodes"]) == 3
    assert {edge["label"] for edge in canvas["edges"]} == {"contradicts", "supports"}
