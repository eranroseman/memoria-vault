"""Tests for the required-check contract."""

import yaml

from scripts.checks import ruleset_doctor


def test_required_workflows_match_the_local_contract():
    assert ruleset_doctor.local_errors() == []


def test_contract_lists_each_required_check_once():
    checks = ruleset_doctor.load_contract()["required_checks"]
    assert len(checks) == len(set(checks))


def test_non_required_workflows_declare_explicit_permissions():
    required_workflows = set(ruleset_doctor.load_contract()["workflow_jobs"].values())
    missing = []
    for path in sorted((ruleset_doctor.ROOT / ".github/workflows").glob("*.yml")):
        rel = path.relative_to(ruleset_doctor.ROOT).as_posix()
        if rel in required_workflows:
            continue
        workflow = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader) or {}
        if "permissions" not in workflow:
            missing.append(rel)

    assert missing == []
