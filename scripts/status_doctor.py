#!/usr/bin/env python3
"""Keep release/testing routing prose from rotting."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MD_LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")

STALE_PATHS = [
    (re.compile(r"docs/releasing/release-plan-template\.md"), ".agents/templates/release-plan.md"),
    (
        re.compile(r"docs/releasing/\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?/tmp/"),
        "scratch/releases/<version>/",
    ),
    (re.compile(r"docs/releasing/"), ".agents/playbooks/release.md or GitHub release issues"),
    (re.compile(r"docs/testing/"), "CONTRIBUTING.md or .agents/playbooks/verify-change.md"),
    (re.compile(r"(?:\.\./|project/)(releases)/"), ".agents/playbooks/release.md"),
    (re.compile(r"(?:\.\./|project/)(tests)/"), "CONTRIBUTING.md"),
    (
        re.compile(r"\brelease/\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?/"),
        ".agents/playbooks/release.md",
    ),
    (
        re.compile(r"(?<!docs/)\breleasing/\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?/"),
        ".agents/playbooks/release.md",
    ),
]
STALE_TESTING_NAMES = {
    "coverage-matrix.md": "CONTRIBUTING.md",
    "verification-matrix.md": "CONTRIBUTING.md",
    "e2e-golden-path-plan.md": ".agents/playbooks/verify-change.md",
    "g10-ingest-plan.md": ".agents/playbooks/verify-change.md",
    "g9-spine-plan.md": ".agents/playbooks/verify-change.md",
    "gui-test-plan.md": ".agents/playbooks/verify-change.md",
    "headless-test-plan.md": ".agents/playbooks/verify-change.md",
    "hermes-cli-test-plan.md": ".agents/playbooks/verify-change.md",
    "installer-test-plan.md": ".agents/playbooks/verify-change.md",
    "release-candidate-runbook.md": ".agents/playbooks/release.md",
    "test-plan-template.md": ".agents/playbooks/verify-change.md",
    "test-env-harness-plan.md": ".agents/playbooks/verify-change.md",
}

PRIVATE_SCRATCH_LINK_RE = re.compile(r"(?:^|[/(])\.claude/projects/|/memory/")
ROUTING_DOCS = (
    Path("CONTRIBUTING.md"),
    Path(".agents/playbooks/release.md"),
    Path(".agents/playbooks/verify-change.md"),
    Path(".agents/playbooks/exec-plan.md"),
)


def targets(root: Path) -> list[Path]:
    files = [root / rel for rel in ROUTING_DOCS if (root / rel).is_file()]
    files += sorted((root / ".agents" / "templates").glob("*.md"))
    files += sorted((root / "scratch" / "releases").glob("**/*.md"))
    return sorted(files)


def check_file(p: Path, root: Path) -> list[str]:
    """Return drift findings for one file."""
    errs: list[str] = []
    text = p.read_text(encoding="utf-8").replace("\r\n", "\n")
    rel = p.relative_to(root)

    # 1. stale path renames / wrong canonical examples
    for rx, replacement in STALE_PATHS:
        for m in rx.finditer(text):
            errs.append(f"{rel}: stale path `{m.group(0)}`; use `{replacement}`")
    for old, replacement in STALE_TESTING_NAMES.items():
        if old in text:
            errs.append(f"{rel}: stale testing plan `{old}`; use `{replacement}`")

    if "tmp" in rel.parts and not _release_scratch(rel):
        errs.append(f"{rel}: tmp/ is no longer a tracked release scratch home")

    if _release_scratch(rel) and PRIVATE_SCRATCH_LINK_RE.search(text):
        errs.append(f"{rel}: tracked scratch note links to local/private memory outside the repo")

    # 2. broken relative links (skip external, anchors, and {{ }} placeholders)
    for raw in MD_LINK.findall(text):
        target = raw.strip()
        if (
            not target
            or target.startswith(("http://", "https://", "mailto:", "#"))
            or "{{" in target
            or target in {"...", "\u2026"}
        ):
            continue
        path_part = target.split("#", 1)[0]
        if not path_part:
            continue
        if not (p.parent / path_part).resolve().exists():
            errs.append(f"{rel}: broken link -> {raw.strip()}")
    return errs


def _release_scratch(rel: Path) -> bool:
    parts = rel.parts
    return len(parts) >= 4 and parts[0] == "scratch" and parts[1] == "releases"


def main() -> int:
    errors: list[str] = []
    files = targets(ROOT)
    for p in files:
        errors.extend(check_file(p, ROOT))
    if errors:
        print(f"status-doctor: {len(errors)} issue(s)\n")
        for e in errors:
            print(f"  x {e}")
        return 1
    print(f"status-doctor: clean ({len(files)} routing doc(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
