"""Package-spine smoke tests for ADR-76/#727."""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

import memoria_runtime.policy as legacy_policy

import memoria
import memoria.runtime.policy as packaged_policy

ROOT = Path(__file__).resolve().parent.parent


def test_pyproject_declares_installable_memoria_package():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["name"] == "memoria-vault"
    assert data["project"]["version"] == memoria.__version__
    assert data["tool"]["setuptools"]["packages"]["find"]["include"] == ["memoria*"]


def test_bare_package_import_does_not_need_mcp_sdk():
    code = (
        "import memoria; "
        "from memoria.runtime.policy import normalize_path; "
        "assert memoria.__version__; "
        "assert normalize_path('./notes/claims/x.md') == 'notes/claims/x.md'"
    )
    subprocess.run([sys.executable, "-c", code], cwd=ROOT, check=True)


def test_legacy_policy_import_matches_packaged_policy():
    assert legacy_policy.normalize_path("./a/b/../c") == packaged_policy.normalize_path("./a/b/../c")
    assert legacy_policy.glob_to_regex("projects/*/code/**") == packaged_policy.glob_to_regex(
        "projects/*/code/**"
    )
    assert legacy_policy.REVIEW_GATED_PREFIXES == packaged_policy.REVIEW_GATED_PREFIXES
