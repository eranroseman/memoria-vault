"""Tests for the repository's agent-guidance drift guard."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "agents_doctor", ROOT / "scripts/agents-doctor.py"
)
assert SPEC and SPEC.loader
agents_doctor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(agents_doctor)


def test_agent_guidance_is_valid_and_generated_files_are_current():
    assert agents_doctor.check() == []


def test_change_impact_registry_has_paths_and_checks():
    data = agents_doctor.yaml.safe_load(agents_doctor.IMPACT_SOURCE.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert all(row["paths"] and row["checks"] for row in data["areas"])
