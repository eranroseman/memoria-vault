"""Tests for the required-check contract."""

import copy

import ruleset_doctor
import yaml


def test_required_workflows_match_the_local_contract():
    assert ruleset_doctor.local_errors() == []


def test_contract_lists_each_required_check_once():
    checks = ruleset_doctor.load_contract()["required_checks"]
    assert len(checks) == len(set(checks))


def test_contract_declares_main_and_scratch_rulesets():
    names = {ruleset["name"] for ruleset in ruleset_doctor.load_contract()["rulesets"]}

    assert names == {"main", "scratch"}


def test_ruleset_contract_rejects_missing_scratch_rule():
    contract = copy.deepcopy(ruleset_doctor.load_contract())
    scratch = next(ruleset for ruleset in contract["rulesets"] if ruleset["name"] == "scratch")
    scratch["rules"] = [{"type": "deletion"}]

    assert any(
        "scratch ruleset must declare only" in err for err in ruleset_doctor.local_errors(contract)
    )


def test_ruleset_contract_rejects_main_status_context_drift():
    contract = copy.deepcopy(ruleset_doctor.load_contract())
    main = next(ruleset for ruleset in contract["rulesets"] if ruleset["name"] == "main")
    status = next(rule for rule in main["rules"] if rule["type"] == "required_status_checks")
    status["contexts_from"] = "stale_checks"

    assert any(
        "contexts_from: required_checks" in err for err in ruleset_doctor.local_errors(contract)
    )


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
