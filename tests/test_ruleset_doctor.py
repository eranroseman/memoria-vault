"""Tests for the required-check contract."""

import ruleset_doctor


def test_required_workflows_match_the_local_contract():
    assert ruleset_doctor.local_errors() == []


def test_contract_lists_each_required_check_once():
    checks = ruleset_doctor.load_contract()["required_checks"]
    assert len(checks) == len(set(checks))
