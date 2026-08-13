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

import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

from tests.paths import ROOT

pytestmark = pytest.mark.static

WORKFLOW = ROOT / ".github/workflows/verify.yml"
FULL_MATRIX = {"shard": ["lint", "contract", "runtime", "sweep"]}
DOCS_MATRIX = {"shard": ["lint", "sweep"]}


def _scope_script() -> str:
    """The `Detect change scope` step's shell body, lifted from the workflow."""
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["scope"]["steps"]
    step = next(s for s in steps if s.get("id") == "scope")
    return step["run"]


def _classify(
    paths: list[str],
    tmp_path: Path,
    *,
    api_pages: list[list[dict[str, str]]] | None = None,
    expected_count: int | str | None = None,
    fail_after_output: bool = False,
) -> dict[str, object]:
    """Run the unmodified workflow body with a local fake GitHub CLI."""
    fake_gh = tmp_path / "gh"
    args = tmp_path / "gh-args"
    api_response = tmp_path / "gh-api-response.json"
    output = tmp_path / "github-output"
    if api_pages is None:
        api_pages = [[{"filename": path} for path in paths]]
    if expected_count is None:
        expected_count = sum(len(page) for page in api_pages)
    api_response.write_text(json.dumps(api_pages), encoding="utf-8")
    fake_gh.write_text(
        """#!/bin/sh
printf '%s\\n' \"$@\" > \"$FAKE_GH_ARGS\"
project_filenames=false
for argument in \"$@\"; do
  [ \"$argument\" = --jq ] && project_filenames=true
done
if [ \"$project_filenames\" = true ]; then
  jq -r '.[][] | .filename' \"$FAKE_GH_API_RESPONSE\"
else
  cat \"$FAKE_GH_API_RESPONSE\"
fi
if [ \"$1\" = api ] && [ \"$FAKE_GH_FAIL_AFTER_OUTPUT\" = true ]; then
  exit 1
fi
""",
        encoding="utf-8",
    )
    fake_gh.chmod(0o755)
    env = os.environ | {
        "FAKE_GH_API_RESPONSE": str(api_response),
        "FAKE_GH_ARGS": str(args),
        "FAKE_GH_FAIL_AFTER_OUTPUT": str(fail_after_output).lower(),
        "GH_TOKEN": "test-token",
        "GITHUB_OUTPUT": str(output),
        "GITHUB_EVENT_NAME": "pull_request",
        "GITHUB_REPOSITORY": "owner/repository",
        "PATH": f"{tmp_path}:{os.environ['PATH']}",
        "PR_CHANGED_FILES": str(expected_count),
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
    scope = dict(
        line.split("=", maxsplit=1) for line in output.read_text(encoding="utf-8").splitlines()
    )
    scope["matrix"] = json.loads(scope["matrix"])
    return scope


@pytest.mark.parametrize(
    ("paths", "expected", "why"),
    [
        (
            ["docs/how-to-guides/setup/quickstart.md"],
            {"ps1": "false", "docs_only": "true", "matrix": DOCS_MATRIX},
            "published docs are documentation",
        ),
        (
            ["design-history/2026-08/chapter.md"],
            {"ps1": "false", "docs_only": "true", "matrix": DOCS_MATRIX},
            "the frozen record is documentation",
        ),
        (
            ["README.md"],
            {"ps1": "false", "docs_only": "true", "matrix": DOCS_MATRIX},
            "root Markdown is documentation",
        ),
        (
            ["src/memoria_vault/product/capabilities/operations/capture-source.md"],
            {"ps1": "false", "docs_only": "false", "matrix": FULL_MATRIX},
            "package data read by contract tests, not documentation",
        ),
        (
            ["src/memoria_vault/product/workspace_seed/CLAUDE.md"],
            {"ps1": "false", "docs_only": "false", "matrix": FULL_MATRIX},
            "seeded into every vault; package data",
        ),
        (
            ["docs/a.md", "src/memoria_vault/cli.py"],
            {"ps1": "false", "docs_only": "false", "matrix": FULL_MATRIX},
            "a code change is in the diff",
        ),
        (
            ["scripts/verify"],
            {"ps1": "false", "docs_only": "false", "matrix": FULL_MATRIX},
            "the gate itself is not documentation",
        ),
        (
            [],
            {"ps1": "true", "docs_only": "false", "matrix": FULL_MATRIX},
            "cannot read changed-file list",
        ),
    ],
)
def test_classifier_verdicts(
    paths: list[str], expected: dict[str, object], why: str, tmp_path: Path
) -> None:
    result = _classify(paths, tmp_path)
    assert result == expected, f"{paths}: unexpected scope because {why}"


def test_scope_reads_every_paginated_pr_file(tmp_path: Path) -> None:
    """A source or PowerShell file after the first 100 must widen the scope."""
    documentation = [f"docs/page-{index}.md" for index in range(100)]
    all_paths = [*documentation, "src/memoria_vault/cli.py", "scripts/setup.ps1"]
    pages = [
        [{"filename": path} for path in documentation],
        [{"filename": path} for path in all_paths[100:]],
    ]

    result = _classify(all_paths, tmp_path, api_pages=pages)

    assert result == {"ps1": "true", "docs_only": "false", "matrix": FULL_MATRIX}
    assert (tmp_path / "gh-args").read_text(encoding="utf-8").splitlines() == [
        "api",
        "--paginate",
        "--slurp",
        "repos/owner/repository/pulls/123/files?per_page=100",
    ]


def test_scope_uses_safe_defaults_when_paginated_retrieval_fails(tmp_path: Path) -> None:
    """Partial API output must never narrow CI validation."""
    result = _classify(["docs/page.md"], tmp_path, fail_after_output=True)

    assert result == {"ps1": "true", "docs_only": "false", "matrix": FULL_MATRIX}


@pytest.mark.parametrize(
    ("previous_filename", "expected"),
    [
        (
            "src/memoria_vault/cli.py",
            {"ps1": "false", "docs_only": "false", "matrix": FULL_MATRIX},
        ),
        (
            "scripts/setup.ps1",
            {"ps1": "true", "docs_only": "false", "matrix": FULL_MATRIX},
        ),
    ],
)
def test_scope_classifies_both_paths_of_a_rename(
    previous_filename: str, expected: dict[str, object], tmp_path: Path
) -> None:
    page = [[{"filename": "docs/renamed.md", "previous_filename": previous_filename}]]

    assert _classify([], tmp_path, api_pages=page) == expected


def test_complete_markdown_documentation_response_still_narrows_scope(tmp_path: Path) -> None:
    paths = ["docs/guide.md", "design-history/2026-08/chapter.md", "README.md"]

    assert _classify(paths, tmp_path) == {
        "ps1": "false",
        "docs_only": "true",
        "matrix": DOCS_MATRIX,
    }


@pytest.mark.parametrize("expected_count", [2, "not-a-number"])
def test_scope_uses_safe_defaults_when_expected_count_is_not_confirmed(
    expected_count: int | str, tmp_path: Path
) -> None:
    result = _classify(["docs/page.md"], tmp_path, expected_count=expected_count)

    assert result == {"ps1": "true", "docs_only": "false", "matrix": FULL_MATRIX}


def test_scope_uses_safe_defaults_at_the_api_record_cap(tmp_path: Path) -> None:
    paths = [f"docs/page-{index}.md" for index in range(3_000)]

    assert _classify(paths, tmp_path) == {
        "ps1": "true",
        "docs_only": "false",
        "matrix": FULL_MATRIX,
    }


def test_scope_treats_command_like_newline_filename_as_literal_input(tmp_path: Path) -> None:
    marker = tmp_path / "shell-side-effect"
    path = f'$(touch "{marker}")\ndocs/page.md'

    result = _classify([path], tmp_path)

    assert result == {"ps1": "true", "docs_only": "false", "matrix": FULL_MATRIX}
    assert not marker.exists()


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
