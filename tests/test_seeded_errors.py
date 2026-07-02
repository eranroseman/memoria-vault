from __future__ import annotations

import json
from pathlib import Path

import pytest

from memoria_vault.runtime.seeded_errors import (
    _metrics_by_error_class,
    load_seeded_error_bundle,
    run_seeded_error_verdict,
)

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "vault-template/system/eval/alpha11-seeded-errors.json"


def test_seeded_error_bundle_is_frozen_alpha11_contract() -> None:
    bundle = load_seeded_error_bundle(BUNDLE)

    assert bundle["version"] == "0.1.0-alpha.11"
    assert bundle["bars"]["recall_min"] == 1.0
    assert bundle["bars"]["checkpoint_value_rate_min"] == 1.0
    assert [case["id"] for case in bundle["cases"]] == [
        "missing-evidence-source",
        "unchecked-evidence-source",
        "missing-digest-evidence",
        "missing-contradiction-target",
        "false-link-target",
        "conflicting-doi-metadata",
        "ambiguous-entity-identity",
        "stale-as-current",
        "unwarranted-claim",
        "crafted-injection",
        "fresh-uncorroborated-source",
        "poisoned-span",
        "wrong-extraction",
    ]


def test_seeded_error_bundle_validation_rejects_duplicate_targets(tmp_path: Path) -> None:
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))
    bundle["cases"][1]["target_id"] = bundle["cases"][0]["target_id"]
    path = tmp_path / "bad-seeded-errors.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")

    try:
        load_seeded_error_bundle(path)
    except ValueError as exc:
        assert "duplicate seeded-error target_id" in str(exc)
    else:
        raise AssertionError("duplicate seeded-error target should fail validation")


def test_metrics_by_error_class_counts_matching_check_false_positives() -> None:
    cases = [
        {
            "id": "expected",
            "error_class": "structural:quote-anchor",
            "target_id": "knowledge/notes/expected.md",
            "expected_check": "quote-anchor",
            "rollback": "include-target",
        }
    ]
    findings = [
        {
            "target_id": "knowledge/notes/expected.md",
            "check": "quote-anchor",
            "route": "ask",
        },
        {
            "target_id": "knowledge/notes/control.md",
            "check": "quote-anchor",
            "route": "ask",
        },
    ]

    by_class = _metrics_by_error_class(cases, findings, ["knowledge/notes/expected.md"], [])

    assert by_class["structural:quote-anchor"]["detected_errors"] == 1
    assert by_class["structural:quote-anchor"]["false_positives"] == 1
    assert by_class["structural:quote-anchor"]["false_positive_rate"] == 0.5


@pytest.mark.slow
def test_seeded_error_verdict_detects_and_rolls_back_structural_case(
    tmp_path: Path,
) -> None:
    result = run_seeded_error_verdict(
        tmp_path,
        template_root=ROOT / "vault-template",
        bundle_path=BUNDLE,
    )

    target = "knowledge/notes/seeded-missing-evidence.md"
    unchecked_target = "knowledge/notes/seeded-unchecked-evidence.md"
    contradiction_target = "knowledge/digests/seeded-missing-contradiction.md"
    digest_target = "knowledge/digests/seeded-missing-digest-evidence.md"
    false_link_target = "knowledge/notes/seeded-false-link.md"
    conflicting_doi_target = "catalog/sources/conflicting-doi"
    ambiguous_entity_target = "catalog/sources/ambiguous-entity"
    stale_target = "knowledge/notes/seeded-stale-as-current.md"
    claim_target = "knowledge/notes/seeded-unwarranted-claim.md"
    injection_target = "knowledge/notes/seeded-crafted-injection.md"
    checkpoint_target = "knowledge/notes/seeded-provenance-checkpoint.md"
    poisoned_target = "catalog/sources/poisoned-span"
    extraction_target = "knowledge/notes/seeded-wrong-extraction.md"
    control = "knowledge/notes/seeded-valid-evidence.md"
    assert result["passed"] is True
    assert result["bar_failures"] == []
    assert result["metrics"] == {
        "expected_errors": 13,
        "detected_errors": 13,
        "false_positives": 0,
        "rolled_back_errors": 13,
        "residual_errors": 0,
        "no_checks_residual_errors": 13,
        "residual_reduction_errors": 13,
        "checkpoint_value_errors": 13,
        "recall": 1.0,
        "false_positive_rate": 0.0,
        "rollback_completeness": 1.0,
        "no_checks_residual_error_rate": 1.0,
        "residual_error_rate": 0.0,
        "residual_reduction_rate": 1.0,
        "checkpoint_value_rate": 1.0,
    }
    assert [row["check"] for row in result["check_timings"]] == [
        "integrity-evidence-check",
        "integrity-quote-anchor-check",
        "integrity-claim-quote-check",
        "integrity-prompt-injection-check",
        "integrity-provenance-checkpoint",
        "integrity-contradiction-check",
        "integrity-link-target-check",
        "check-source-metadata",
    ]
    assert all(row["duration_ms"] >= 0 for row in result["check_timings"])
    assert set(result["detection_times_ms"]) == {
        target,
        unchecked_target,
        contradiction_target,
        digest_target,
        false_link_target,
        ambiguous_entity_target,
        conflicting_doi_target,
        stale_target,
        claim_target,
        injection_target,
        checkpoint_target,
        poisoned_target,
        extraction_target,
    }
    assert (
        result["detection_timing_by_error_class"]["structural:source-metadata"]["detected_errors"]
        == 2
    )
    assert (
        result["detection_timing_by_error_class"]["structural:source-metadata"]["max_detection_ms"]
        >= 0
    )
    assert result["by_error_class"]["checkpoint:fresh-uncorroborated-source"] == {
        "expected_errors": 1,
        "detected_errors": 1,
        "false_positives": 0,
        "rolled_back_errors": 1,
        "residual_errors": 0,
        "no_checks_residual_errors": 1,
        "residual_reduction_errors": 1,
        "checkpoint_value_errors": 1,
        "recall": 1.0,
        "false_positive_rate": 0.0,
        "rollback_completeness": 1.0,
        "no_checks_residual_error_rate": 1.0,
        "residual_error_rate": 0.0,
        "residual_reduction_rate": 1.0,
        "checkpoint_value_rate": 1.0,
    }
    assert result["by_error_class"]["blind:unwarranted-claim"] == {
        "expected_errors": 1,
        "detected_errors": 1,
        "false_positives": 0,
        "rolled_back_errors": 1,
        "residual_errors": 0,
        "no_checks_residual_errors": 1,
        "residual_reduction_errors": 1,
        "checkpoint_value_errors": 1,
        "recall": 1.0,
        "false_positive_rate": 0.0,
        "rollback_completeness": 1.0,
        "no_checks_residual_error_rate": 1.0,
        "residual_error_rate": 0.0,
        "residual_reduction_rate": 1.0,
        "checkpoint_value_rate": 1.0,
    }
    assert result["detected"] == [
        ambiguous_entity_target,
        conflicting_doi_target,
        poisoned_target,
        contradiction_target,
        digest_target,
        injection_target,
        false_link_target,
        target,
        checkpoint_target,
        stale_target,
        unchecked_target,
        claim_target,
        extraction_target,
    ]
    assert result["rolled_back"] == [
        ambiguous_entity_target,
        conflicting_doi_target,
        poisoned_target,
        contradiction_target,
        digest_target,
        injection_target,
        false_link_target,
        target,
        checkpoint_target,
        stale_target,
        unchecked_target,
        claim_target,
        extraction_target,
    ]
    assert result["false_positives"] == []
    assert not (tmp_path / target).exists()
    assert not (tmp_path / unchecked_target).exists()
    assert not (tmp_path / contradiction_target).exists()
    assert not (tmp_path / digest_target).exists()
    assert not (tmp_path / false_link_target).exists()
    assert not (tmp_path / ambiguous_entity_target).exists()
    assert not (tmp_path / conflicting_doi_target).exists()
    assert not (tmp_path / stale_target).exists()
    assert not (tmp_path / claim_target).exists()
    assert not (tmp_path / injection_target).exists()
    assert not (tmp_path / checkpoint_target).exists()
    assert not (tmp_path / poisoned_target).exists()
    assert not (tmp_path / extraction_target).exists()
    assert (tmp_path / ".memoria/quarantine" / target).is_file()
    assert (tmp_path / ".memoria/quarantine" / unchecked_target).is_file()
    assert (tmp_path / ".memoria/quarantine" / contradiction_target).is_file()
    assert (tmp_path / ".memoria/quarantine" / digest_target).is_file()
    assert (tmp_path / ".memoria/quarantine" / false_link_target).is_file()
    assert (tmp_path / ".memoria/quarantine" / ambiguous_entity_target).is_file()
    assert (tmp_path / ".memoria/quarantine" / conflicting_doi_target).is_file()
    assert (tmp_path / ".memoria/quarantine" / stale_target).is_file()
    assert (tmp_path / ".memoria/quarantine" / claim_target).is_file()
    assert (tmp_path / ".memoria/quarantine" / injection_target).is_file()
    assert (tmp_path / ".memoria/quarantine" / checkpoint_target).is_file()
    assert (tmp_path / ".memoria/quarantine" / poisoned_target).is_file()
    assert (tmp_path / ".memoria/quarantine" / extraction_target).is_file()
    assert (tmp_path / control).is_file()
