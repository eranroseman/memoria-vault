"""Tests for the required-check contract."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location(
    "ruleset_doctor", ROOT / "scripts/ruleset-doctor.py"
)
assert SPEC and SPEC.loader
ruleset_doctor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ruleset_doctor)


def test_required_workflows_match_the_local_contract():
    assert ruleset_doctor.local_errors() == []


def test_contract_lists_each_required_check_once():
    checks = ruleset_doctor.load_contract()["required_checks"]
    assert len(checks) == len(set(checks))
