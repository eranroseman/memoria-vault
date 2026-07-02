#!/usr/bin/env python3
"""github-doctor — lightweight guardrails for .github process files."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
GITHUB = ROOT / ".github"
ISSUE_TEMPLATES = GITHUB / "ISSUE_TEMPLATE"
DEPENDABOT = GITHUB / "dependabot.yml"

BUG_LABELS = ["bug"]
FEATURE_LABELS: list[str] = []
RETIRED_LABELS = {"enhancement", "question", "research", "needs-scoping"}
BOT_LABELS = {"dependencies", "python", "github_actions", "release"}
EXPECTED_DEPENDABOT_UPDATES = {
    ("github-actions", "/"),
    ("pip", "/"),
}
STALE_PROFILE_TERMS = {
    "memoria-mapper",
    "memoria-socratic",
    "memoria-verifier",
    "memoria-coder",
    "memoria-linter",
    "researcher profile",
    "mapper",
    "socratic",
    "verifier",
    "coder",
    "linter",
}


def _load_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return {"__error__": str(exc)}
    return data


def _labels(data: dict) -> list[str]:
    labels = data.get("labels", [])
    return labels if isinstance(labels, list) else [labels]


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8").lower()


def check(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    templates = root / ".github" / "ISSUE_TEMPLATE"
    bug = templates / "bug_report.yml"
    feature = templates / "feature_request.yml"

    for path in (bug, feature):
        if not path.is_file():
            errors.append(f"{path.relative_to(root)}: missing")
            continue
        data = _load_yaml(path)
        if "__error__" in data:
            errors.append(f"{path.relative_to(root)}: invalid YAML: {data['__error__']}")
            continue
        labels = _labels(data)
        retired = sorted(RETIRED_LABELS.intersection(labels))
        if retired:
            errors.append(f"{path.relative_to(root)}: retired label(s): {', '.join(retired)}")
        stale_terms = sorted(term for term in STALE_PROFILE_TERMS if term in _text(path))
        if stale_terms:
            errors.append(
                f"{path.relative_to(root)}: stale profile term(s): {', '.join(stale_terms)}"
            )

    if bug.is_file() and _load_yaml(bug).get("__error__") is None:
        labels = _labels(_load_yaml(bug))
        if labels != BUG_LABELS:
            errors.append(f"{bug.relative_to(root)}: labels must be {BUG_LABELS}, got {labels}")

    if feature.is_file() and _load_yaml(feature).get("__error__") is None:
        labels = _labels(_load_yaml(feature))
        if labels != FEATURE_LABELS:
            errors.append(
                f"{feature.relative_to(root)}: feature requests should use Project fields, not labels"
            )

    dependabot = root / ".github" / "dependabot.yml"
    if dependabot.is_file():
        data = _load_yaml(dependabot)
        if "__error__" in data:
            errors.append(f"{dependabot.relative_to(root)}: invalid YAML: {data['__error__']}")
        else:
            update_keys = set()
            for idx, update in enumerate(data.get("updates") or [], start=1):
                update_keys.add((update.get("package-ecosystem"), update.get("directory")))
                limit = update.get("open-pull-requests-limit")
                if limit is not None and limit > 3:
                    errors.append(
                        f"{dependabot.relative_to(root)}: update #{idx} open-pull-requests-limit "
                        "should stay <= 3"
                    )
                labels = set(update.get("labels") or [])
                unexpected = sorted(labels - BOT_LABELS - RETIRED_LABELS)
                if unexpected:
                    errors.append(
                        f"{dependabot.relative_to(root)}: update #{idx} has unexpected label(s): "
                        f"{', '.join(unexpected)}"
                    )
            missing = sorted(EXPECTED_DEPENDABOT_UPDATES - update_keys)
            if missing:
                rendered = ", ".join(f"{ecosystem}:{directory}" for ecosystem, directory in missing)
                errors.append(
                    f"{dependabot.relative_to(root)}: missing update surface(s): {rendered}"
                )
    return errors


def main() -> int:
    errors = check()
    if errors:
        print(f"github-doctor: {len(errors)} issue(s)\n")
        for error in errors:
            print(f"  ✗ {error}")
        return 1
    print("github-doctor: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
