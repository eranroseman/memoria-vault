"""The docs-only narrowing must not fire on runtime-shipped Markdown.

`.github/workflows/verify.yml` sets VERIFY_DOCS_ONLY=1 when a PR's whole diff is
documentation, which drops the wheel gate, the offline smoke, `memoria
--version`, and narrows pytest from six markers to `static`. Sixty-six tracked
*.md files ship under src/ as package data (capabilities/operations/*.md and
workspace_seed/), and every test that reads them is `contract` — so
misclassifying them skips exactly the checks that would catch a break.

This runs the workflow's classifier, rather than asserting on the regex text:
a test that only greps for a pattern passes on a pattern that is present and
wrong.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

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


def _classify(
    paths: list[str],
    tmp_path: Path,
    *,
    fail_after_output: bool = False,
    pr_view_paths: list[str] | None = None,
) -> dict[str, str]:
    """Run the unmodified workflow body with a local fake GitHub CLI."""
    fake_gh = tmp_path / "gh"
    args = tmp_path / "gh-args"
    output = tmp_path / "github-output"
    fake_gh.write_text(
        """#!/bin/sh
printf '%s\\n' \"$@\" > \"$FAKE_GH_ARGS\"
if [ \"$1\" = api ]; then
  printf '%s\\n' \"$FAKE_GH_API_FILES\"
else
  printf '%s\\n' \"$FAKE_GH_PR_FILES\"
fi
if [ \"$1\" = api ] && [ \"$FAKE_GH_FAIL_AFTER_OUTPUT\" = true ]; then
  exit 1
fi
""",
        encoding="utf-8",
    )
    fake_gh.chmod(0o755)
    env = os.environ | {
        "FAKE_GH_API_FILES": "\n".join(paths),
        "FAKE_GH_ARGS": str(args),
        "FAKE_GH_FAIL_AFTER_OUTPUT": str(fail_after_output).lower(),
        "FAKE_GH_PR_FILES": "\n".join(pr_view_paths if pr_view_paths is not None else paths),
        "GH_TOKEN": "test-token",
        "GITHUB_OUTPUT": str(output),
        "GITHUB_REPOSITORY": "owner/repository",
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "PR_NUMBER": "123",
    }
    result = subprocess.run(
        ["bash", "-c", _scope_script()],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    assert args.exists(), f"workflow did not invoke gh; stderr: {result.stderr}"
    assert output.exists(), f"workflow did not write scope outputs; stdout: {result.stdout}"
    return dict(
        line.split("=", maxsplit=1) for line in output.read_text(encoding="utf-8").splitlines()
    )


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
def test_classifier_verdicts(paths: list[str], expected: bool, why: str, tmp_path: Path) -> None:
    result = _classify(paths, tmp_path)
    assert (result["docs_only"] == "true") is expected, (
        f"{paths}: expected docs_only={expected} because {why}"
    )


def test_scope_reads_every_paginated_pr_file(tmp_path: Path) -> None:
    """A source or PowerShell file after the first 100 must widen the scope."""
    documentation = [f"docs/page-{index}.md" for index in range(100)]
    all_paths = [*documentation, "src/memoria_vault/cli.py", "scripts/setup.ps1"]

    result = _classify(all_paths, tmp_path, pr_view_paths=documentation)

    assert result == {"ps1": "true", "docs_only": "false"}
    assert (tmp_path / "gh-args").read_text(encoding="utf-8").splitlines() == [
        "api",
        "--paginate",
        "repos/owner/repository/pulls/123/files?per_page=100",
        "--jq",
        ".[].filename",
    ]


def test_scope_uses_safe_defaults_when_paginated_retrieval_fails(tmp_path: Path) -> None:
    """Partial API output must never narrow CI validation."""
    result = _classify(["docs/page.md"], tmp_path, fail_after_output=True)

    assert result == {"ps1": "true", "docs_only": "false"}


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
