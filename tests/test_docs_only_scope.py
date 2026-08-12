"""The docs-only narrowing must not fire on runtime-shipped Markdown.

`.github/workflows/verify.yml` sets VERIFY_DOCS_ONLY=1 when a PR's whole diff is
documentation, which drops the wheel gate, the offline smoke, `memoria
--version`, and narrows pytest from six markers to `static`. Sixty-six tracked
*.md files ship under src/ as package data (capabilities/operations/*.md and
workspace_seed/), and every test that reads them is `contract` — so
misclassifying them skips exactly the checks that would catch a break.

This extracts the classifier from the workflow and runs it, rather than
asserting on the regex text: a test that only greps for a pattern passes on a
pattern that is present and wrong.
"""

from __future__ import annotations

import re
import subprocess

import pytest
import yaml

from tests.paths import ROOT

pytestmark = pytest.mark.static

WORKFLOW = ROOT / ".github/workflows/verify.yml"


def _scope_script() -> str:
    """The `Detect change scope` step's shell body, lifted from the workflow."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["shards"]["steps"]
    step = next(s for s in steps if s.get("id") == "scope")
    return step["run"]


def _classify(paths: list[str]) -> bool:
    """Run the workflow's own classifier over `paths`, return its docs_only verdict."""
    body = _scope_script()
    # Drop the two lines that reach GitHub; feed the file list in directly.
    body = re.sub(r"^\s*files=.*$", 'files="$FILES"', body, count=1, flags=re.M)
    body = re.sub(r"^\s*printf .changed files.*$", "", body, count=1, flags=re.M)
    body = re.sub(r'^\s*echo "\w+=.*>> "\$GITHUB_OUTPUT"\s*$', "", body, flags=re.M)
    # Keep the workflow's progress echo. The appended verdict below is the final
    # line, so preceding human-readable output does not affect the parsed result.
    result = subprocess.run(
        ["bash", "-c", body + '\nprintf "%s" "$docs_only"'],
        env={"FILES": "\n".join(paths), "PATH": "/usr/bin:/bin"},
        text=True,
        capture_output=True,
        check=True,
    )
    # Last line only: the appended verdict follows all workflow output.
    lines = result.stdout.strip().splitlines()
    assert lines, f"classifier produced no verdict; stderr: {result.stderr}"
    return lines[-1].strip() == "true"


@pytest.mark.parametrize(
    ("paths", "expected", "why"),
    [
        (["docs/how-to-guides/setup/quickstart.md"], True, "published docs are documentation"),
        (["design-history/2026-08/chapter.md"], True, "the frozen record is documentation"),
        (["README.md"], True, "root Markdown is documentation"),
        (
            ["src/memoria_vault/product/capabilities/operations/capture-source.md"],
            False,
            "package data read by contract tests, not documentation",
        ),
        (
            ["src/memoria_vault/product/workspace_seed/CLAUDE.md"],
            False,
            "seeded into every vault; package data",
        ),
        (["docs/a.md", "src/memoria_vault/cli.py"], False, "a code change is in the diff"),
        (["scripts/verify"], False, "the gate itself is not documentation"),
        ([], False, "cannot read changed-file list"),
    ],
)
def test_classifier_verdicts(paths: list[str], expected: bool, why: str):
    assert _classify(paths) is expected, f"{paths}: expected docs_only={expected} because {why}"


def test_runtime_markdown_actually_exists_under_src():
    """If this ever returns nothing, the parametrised cases above stop testing anything."""
    listing = subprocess.run(
        ["git", "ls-files", "src/**/*.md"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    shipped = listing.stdout.split()
    assert len(shipped) > 50, (
        f"expected the package-data Markdown corpus, found {len(shipped)} files; "
        "if it genuinely moved, update this test and the workflow comment together"
    )
