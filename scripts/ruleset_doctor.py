#!/usr/bin/env python3
"""Audit required-check workflows locally and, optionally, GitHub's live ruleset."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / ".github/ruleset-contract.yaml"


def load_contract() -> dict:
    data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8")) or {}
    if data.get("version") != 1:
        raise ValueError("ruleset contract must use version: 1")
    return data


def local_errors(contract: dict | None = None) -> list[str]:
    contract = contract or load_contract()
    errors = []
    for check, relative in contract["workflow_jobs"].items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"{check}: workflow missing: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        # BaseLoader (not safe_load) keeps the GitHub Actions `on:` key as the
        # string "on" -- safe_load parses it to bool True (YAML 1.1). BaseLoader
        # never instantiates objects, so it is safe.
        workflow = yaml.load(text, Loader=yaml.BaseLoader) or {}  # noqa: S506
        triggers = workflow.get("on") or {}
        if "pull_request" not in triggers and "pull_request_target" not in triggers:
            errors.append(f"{check}: workflow does not report on pull requests")
        if any(
            key in (triggers.get(event) or {})
            for event in ("pull_request", "pull_request_target", "push")
            for key in ("paths", "paths-ignore")
            if isinstance(triggers.get(event), dict)
        ):
            errors.append(f"{check}: required workflow has a path-filtered trigger")
        if "concurrency:" not in text:
            errors.append(f"{check}: workflow has no concurrency policy")
        jobs = workflow.get("jobs") or {}
        job_names = {job.get("name", job_id) for job_id, job in jobs.items()}
        if check not in jobs and check not in job_names:
            errors.append(f"{check}: expected job id or name not found in {relative}")
    errors.extend(ruleset_contract_errors(contract))
    return errors


def ruleset_contract_errors(contract: dict) -> list[str]:
    errors = []
    rulesets = contract.get("rulesets") or []
    names = [ruleset.get("name") for ruleset in rulesets]
    if len(names) != len(set(names)):
        errors.append("ruleset contract has duplicate ruleset names")
    if "main" not in names:
        errors.append("ruleset contract must declare main")
    if "scratch" not in names:
        errors.append("ruleset contract must declare scratch")

    by_name = {ruleset.get("name"): ruleset for ruleset in rulesets}
    if main := by_name.get("main"):
        errors.extend(_declared_ruleset_errors(main))
        status_rule = _declared_rule(main, "required_status_checks")
        if not status_rule:
            errors.append("main ruleset must declare required_status_checks")
        elif status_rule.get("contexts_from") != "required_checks":
            errors.append("main required_status_checks must use contexts_from: required_checks")
    if scratch := by_name.get("scratch"):
        errors.extend(_declared_ruleset_errors(scratch))
        scratch_types = [rule.get("type") for rule in scratch.get("rules", [])]
        if scratch_types != ["deletion", "non_fast_forward"]:
            errors.append(
                f"scratch ruleset must declare only deletion and non_fast_forward: {scratch_types}"
            )
    return errors


def _declared_ruleset_errors(ruleset: dict) -> list[str]:
    errors = []
    name = ruleset.get("name", "<unnamed>")
    if ruleset.get("target") != "branch":
        errors.append(f"{name}: target must be branch")
    if ruleset.get("enforcement") != "active":
        errors.append(f"{name}: enforcement must be active")
    if not ruleset.get("ref_includes"):
        errors.append(f"{name}: ref_includes is required")
    if not ruleset.get("rules"):
        errors.append(f"{name}: rules are required")
    return errors


def _declared_rule(ruleset: dict, rule_type: str) -> dict | None:
    return next((rule for rule in ruleset.get("rules", []) if rule.get("type") == rule_type), None)


def _gh_json(endpoint: str) -> object:
    proc = subprocess.run(
        ["gh", "api", endpoint],
        check=False,
        capture_output=True,
        text=True,
        env=os.environ,
    )
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or f"gh api failed for {endpoint}")
    return json.loads(proc.stdout)


def live_errors(repository: str, contract: dict | None = None) -> list[str]:
    contract = contract or load_contract()
    summaries = _gh_json(f"repos/{repository}/rulesets")
    errors = []
    for declared in contract.get("rulesets", []):
        wanted = declared["name"]
        match = next(
            (
                item
                for item in summaries
                if item.get("name") == wanted and item.get("enforcement") == declared["enforcement"]
            ),
            None,
        )
        if not match:
            errors.append(f"active ruleset {wanted!r} not found")
            continue
        detail = _gh_json(f"repos/{repository}/rulesets/{match['id']}")
        errors.extend(_live_ruleset_errors(detail, declared, contract))
    return errors


def _live_ruleset_errors(detail: dict, declared: dict, contract: dict) -> list[str]:
    name = declared["name"]
    errors = []
    actual_includes = ((detail.get("conditions") or {}).get("ref_name") or {}).get("include", [])
    if actual_includes != declared.get("ref_includes", []):
        errors.append(f"live ruleset {name!r} ref_includes mismatch: {actual_includes}")

    actual_rules = {rule.get("type"): rule for rule in detail.get("rules", [])}
    expected_types = [rule["type"] for rule in declared.get("rules", [])]
    actual_types = list(actual_rules)
    if set(actual_types) != set(expected_types):
        errors.append(f"live ruleset {name!r} rules mismatch: {actual_types} != {expected_types}")

    status_rule = _declared_rule(declared, "required_status_checks")
    if status_rule:
        actual_status = {
            item["context"]
            for item in (
                ((actual_rules.get("required_status_checks") or {}).get("parameters") or {}).get(
                    "required_status_checks", []
                )
            )
        }
        expected_status = set(contract[status_rule["contexts_from"]])
        if missing := expected_status - actual_status:
            errors.append(f"live ruleset {name!r} missing checks: {sorted(missing)}")
        if extra := actual_status - expected_status:
            errors.append(f"live ruleset {name!r} has undeclared checks: {sorted(extra)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="also query GitHub with gh")
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    args = parser.parse_args()
    try:
        contract = load_contract()
        errors = local_errors(contract)
        if args.live:
            if not args.repository:
                raise ValueError("--repository or GITHUB_REPOSITORY is required with --live")
            errors.extend(live_errors(args.repository, contract))
    except (OSError, ValueError, yaml.YAMLError, RuntimeError, json.JSONDecodeError) as exc:
        errors = [str(exc)]
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors), file=sys.stderr)
        return 1
    print("ruleset-doctor: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
