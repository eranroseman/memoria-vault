"""Tests for the local high-risk secret pre-commit scanner."""

from scripts import gitleaks_precommit


def test_gitleaks_precommit_flags_key_shaped_secret(tmp_path):
    probe = tmp_path / "probe.txt"
    probe.write_text("AKIA" + "IOSFODNN7EXAMPLE\n", encoding="utf-8")

    assert gitleaks_precommit.findings([str(probe)]) == [f"{probe}:1: AWS access key"]


def test_gitleaks_precommit_allows_common_placeholder_tokens(tmp_path):
    probe = tmp_path / "probe.py"
    probe.write_text('"sk-testsecret0123456789"\n', encoding="utf-8")

    assert gitleaks_precommit.findings([str(probe)]) == []
