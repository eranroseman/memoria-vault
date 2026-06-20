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
        workflow = yaml.load(text, Loader=yaml.BaseLoader) or {}
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
    return errors


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
    wanted = contract["ruleset_name"]
    match = next(
        (
            item
            for item in summaries
            if item.get("name") == wanted and item.get("enforcement") == "active"
        ),
        None,
    )
    if not match:
        return [f"active ruleset {wanted!r} not found"]
    detail = _gh_json(f"repos/{repository}/rulesets/{match['id']}")
    rule = next(
        (item for item in detail.get("rules", []) if item.get("type") == "required_status_checks"),
        None,
    )
    actual = {
        item["context"]
        for item in ((rule or {}).get("parameters") or {}).get("required_status_checks", [])
    }
    expected = set(contract["required_checks"])
    errors = []
    if missing := expected - actual:
        errors.append(f"live ruleset missing checks: {sorted(missing)}")
    if extra := actual - expected:
        errors.append(f"live ruleset has undeclared checks: {sorted(extra)}")
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
