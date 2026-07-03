"""Standalone runtime ships no bundled Obsidian plugin provenance payload."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import plugin_provenance_doctor as doctor

ROOT = Path(__file__).resolve().parent.parent


def test_plugin_provenance_doctor_accepts_standalone_repo():
    assert doctor.check(ROOT) == []


def test_plugin_provenance_doctor_flags_removed_payloads(tmp_path):
    root = tmp_path / "repo"
    (root / "vault-template/.obsidian").mkdir(parents=True)
    (root / "vault-template/system/scripts").mkdir(parents=True)

    findings = doctor.check(root)

    assert {finding.path for finding in findings} == {
        "vault-template/.obsidian",
        "vault-template/system/scripts",
    }
