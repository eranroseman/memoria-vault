"""L1 component tests for github-doctor."""

from pathlib import Path

from scripts.checks import github_doctor


def _write_valid_github_files(
    root: Path,
    pr_template: str = "Refs #123\nIssue tracker updated: N/A\n",
):
    templates = root / ".github" / "ISSUE_TEMPLATE"
    templates.mkdir(parents=True)
    (templates / "bug_report.yml").write_text(
        """
name: Bug
labels: ["bug"]
body: []
""".lstrip(),
        encoding="utf-8",
    )
    (templates / "feature_request.yml").write_text(
        """
name: Feature
labels: []
body: []
""".lstrip(),
        encoding="utf-8",
    )
    (root / ".github" / "dependabot.yml").write_text(
        """
version: 2
updates:
  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: monthly
  - package-ecosystem: pip
    directory: "/"
    schedule:
      interval: monthly
  - package-ecosystem: pre-commit
    directory: "/"
    schedule:
      interval: monthly
""".lstrip(),
        encoding="utf-8",
    )
    (root / ".github" / "pull_request_template.md").write_text(
        pr_template,
        encoding="utf-8",
    )


def test_github_doctor_accepts_current_github_files():
    assert github_doctor.check(github_doctor.ROOT) == []


def test_github_doctor_flags_retired_labels_and_stale_profiles(tmp_path):
    templates = tmp_path / ".github" / "ISSUE_TEMPLATE"
    templates.mkdir(parents=True)
    (templates / "bug_report.yml").write_text(
        """
name: Bug
labels: ["bug", "enhancement"]
body:
  - type: input
    id: profile
    attributes:
      label: Profile
      description: "Which profile? e.g. mapper"
""".lstrip(),
        encoding="utf-8",
    )
    (templates / "feature_request.yml").write_text(
        """
name: Feature
labels: ["documentation"]
body: []
""".lstrip(),
        encoding="utf-8",
    )
    dependabot = tmp_path / ".github" / "dependabot.yml"
    dependabot.write_text(
        """
version: 2
updates:
  - package-ecosystem: github-actions
    directory: "/"
    schedule:
      interval: monthly
    open-pull-requests-limit: 4
""".lstrip(),
        encoding="utf-8",
    )

    errors = github_doctor.check(Path(tmp_path))
    assert any("retired label" in error for error in errors)
    assert any("stale profile" in error for error in errors)
    assert any("feature requests should use Project fields" in error for error in errors)
    assert any("open-pull-requests-limit" in error for error in errors)
    assert any("missing update surface" in error for error in errors)


def test_github_doctor_flags_closes_only_pr_template(tmp_path):
    _write_valid_github_files(
        Path(tmp_path),
        pr_template="Closes #123\nIssue tracker updated: yes\n",
    )

    errors = github_doctor.check(Path(tmp_path))

    assert errors == [".github/pull_request_template.md: mention Refs # when Closes # appears"]
