"""Tests for generated reference documentation."""

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_schema_reference_docs_are_current():
    subprocess.run(["python", "scripts/gen_reference_refs.py", "--check"], cwd=ROOT, check=True)


def test_profile_reference_doc_is_current():
    subprocess.run(
        ["python", "scripts/render_profile_configs.py", "reference", "--check"],
        cwd=ROOT,
        check=True,
    )
