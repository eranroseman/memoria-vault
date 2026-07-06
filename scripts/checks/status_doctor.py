#!/usr/bin/env python3
"""Keep release/testing routing prose from rotting."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

MD_LINK = re.compile(r"(?<!\!)\[[^\]]*\]\(([^)]+)\)")

STALE_PATHS = [
    (re.compile(r"docs/releasing/release-plan-template\.md"), ".agents/templates/release-plan.md"),
    (
        re.compile(r"docs/releasing/\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?/tmp/"),
        "`releases/<version>/` on the `scratch` branch",
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
LATEST_CHECKPOINT_RE = re.compile(r"^Latest completed checkpoint:\s*`([^`]+)`\s*$", re.MULTILINE)
ROUTING_DOCS = (
    Path("CONTRIBUTING.md"),
    Path(".agents/playbooks/release.md"),
    Path(".agents/playbooks/verify-change.md"),
    Path(".agents/playbooks/exec-plan.md"),
)


def targets(root: Path) -> list[Path]:
    files = [root / rel for rel in ROUTING_DOCS if (root / rel).is_file()]
    files += sorted((root / ".agents" / "templates").glob("*.md"))
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
    return len(parts) >= 3 and parts[0] == "releases"


def _expected_design_history_chapter(root: Path, checkpoint: str) -> tuple[Path | None, str]:
    history = root / "design-history"
    if found := re.fullmatch(r"alpha\.(\d+)", checkpoint):
        number = int(found.group(1))
        name = "01-alpha.1-baseline.md" if number == 1 else f"{number:02d}-alpha.{number}.md"
        return history / name, name

    suffix = f"-{checkpoint}.md"
    matches = sorted(path for path in history.glob("*.md") if path.name.endswith(suffix))
    if len(matches) == 1:
        return matches[0], matches[0].name
    return None, f"*{suffix}"


def check_design_history(root: Path) -> list[str]:
    """Return release-close drift findings for the durable design-history record."""
    errors: list[str] = []
    history = root / "design-history"
    readme = history / "README.md"
    arcs = history / "arcs.md"
    if not readme.is_file():
        return ["design-history/README.md: missing latest completed checkpoint marker"]

    text = readme.read_text(encoding="utf-8").replace("\r\n", "\n")
    match = LATEST_CHECKPOINT_RE.search(text)
    if not match:
        errors.append(
            "design-history/README.md: missing latest checkpoint marker "
            "(example line: Latest completed checkpoint: `alpha.16`)"
        )
        return errors

    checkpoint = match.group(1)
    chapter, expected = _expected_design_history_chapter(root, checkpoint)
    if not chapter or not chapter.is_file():
        errors.append(
            f"design-history/README.md: latest checkpoint `{checkpoint}` needs "
            f"design-history/{expected}"
        )

    if not arcs.is_file():
        errors.append("design-history/arcs.md: missing")
    elif f"Current (as of {checkpoint})" not in arcs.read_text(encoding="utf-8"):
        errors.append(f"design-history/arcs.md: missing `Current (as of {checkpoint})` line")
    return errors


def main() -> int:
    errors: list[str] = []
    files = targets(ROOT)
    for p in files:
        errors.extend(check_file(p, ROOT))
    errors.extend(check_design_history(ROOT))
    if errors:
        print(f"status-doctor: {len(errors)} issue(s)\n")
        for e in errors:
            print(f"  x {e}")
        return 1
    print(f"status-doctor: clean ({len(files)} routing doc(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
