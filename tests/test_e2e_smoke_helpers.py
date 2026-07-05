from __future__ import annotations

import pytest

from scripts.sandbox import e2e_smoke


def test_stage_labels_preserve_e2e_smoke_order() -> None:
    assert e2e_smoke.STAGE_ORDER == (
        "vault-assembly-1",
        "vault-assembly-2",
        "vault-assembly-3",
        "commit-gate",
        "offline-ingest-1",
        "offline-ingest-2",
        "workflow-replay",
        "final-integrity",
    )
    assert [e2e_smoke.STAGE_LABELS[name].split(":", 1)[0] for name in e2e_smoke.STAGE_ORDER] == [
        "1. vault-assembly",
        "2. vault-assembly",
        "3. vault-assembly",
        "4. commit-gate",
        "5. offline-ingest",
        "6. offline-ingest",
        "7. workflow-replay",
        "8. final-integrity",
    ]


def test_final_verdict_accepts_pass_or_review_only() -> None:
    e2e_smoke.assert_final_verdict("8 finding(s) -- verdict: REVIEW")
    e2e_smoke.assert_final_verdict("0 finding(s) -- verdict: PASS")
    with pytest.raises(AssertionError):
        e2e_smoke.assert_final_verdict("1 finding(s) -- verdict: FAIL")


def test_assert_executable_reports_missing_path(tmp_path) -> None:
    with pytest.raises(AssertionError, match="missing helper"):
        e2e_smoke.assert_executable(tmp_path / "missing", "missing helper")
