import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "scripts" / "test_env_harness.py"
CASSETTE = ROOT / "fixtures" / "test-env" / "cassettes" / "alpha6-l4-golden-path.json"


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
    assert [step["id"] for step in cassette["steps"]][:3] == [
        "ingest-source",
        "classify-source",
        "seed-project",
    ]
    for step in cassette["steps"]:
        assert harness.arg_shape(step["args"]) == step["arg_shape"]


def test_cassette_replay_runs_model_free_l4_path(tmp_path):
    harness = _load_harness()

    result = harness.replay(ROOT, tmp_path, CASSETTE)
    summary = result.as_dict()

    assert summary["cassette"] == "alpha6-l4-golden-path"
    assert "catalog/papers/harness2026.md" in summary["artifacts"]
    assert "projects/harness/project-gate-index.md" in summary["artifacts"]
    assert "projects/harness/exports/harness-section.md" in summary["artifacts"]
    assert not (tmp_path / "notes/claims/blocked-by-harness.md").exists()

    audit = [
        json.loads(line)
        for line in (tmp_path / "system/logs/audit.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert audit[-1]["decision"] == "deny"
    assert audit[-1]["task_id"] == "HARNESS-DENY"

    project_gate = (tmp_path / "projects/harness/project-gate-index.md").read_text(encoding="utf-8")
    assert "Harness support" in project_gate
    assert "evidence_saturation: \"unsaturated\"" in project_gate
