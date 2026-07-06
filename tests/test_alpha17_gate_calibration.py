from __future__ import annotations

from memoria_vault.runtime.seeded_errors import (
    SEEDED_PROBE_SENTINEL,
    gate_calibration_config,
    seeded_probe_review_batch,
    summarize_gate_calibration,
)


def test_seeded_probe_batch_is_contained_and_load_capped() -> None:
    cases = [
        {
            "id": "case-a",
            "target_id": "notes/a.md",
            "error_class": "missing-evidence",
            "self_rebuttal": "This proposal cites a missing source.",
            "rationale": "A persuasive explanation must not be shown.",
        },
        {
            "id": "case-b",
            "target_id": "notes/b.md",
            "error_class": "wrong-claim",
        },
    ]

    batch = seeded_probe_review_batch(cases, max_items=1)

    assert batch["production_enabled"] is False
    assert batch["max_items_per_batch"] == 1
    assert len(batch["probes"]) == 1
    probe = batch["probes"][0]
    assert probe["sentinel"] == SEEDED_PROBE_SENTINEL
    assert "run_id" not in probe
    assert "commit" not in probe
    assert "rationale" not in probe
    assert probe["self_rebuttal"] == "This proposal cites a missing source."
    assert probe["certainty"] == "low"


def test_gate_calibration_config_forces_production_disabled() -> None:
    config = gate_calibration_config(
        {
            "production_enabled": True,
            "max_items_per_batch": 0,
            "show_persuasive_explanations": True,
        }
    )

    assert config == {
        "production_enabled": False,
        "max_items_per_batch": 1,
        "show_persuasive_explanations": False,
    }


def test_gate_calibration_summarizes_both_rejudge_directions() -> None:
    summary = summarize_gate_calibration(
        [
            {
                "expected_disposition": "reject",
                "disposition": "accept",
                "rejudged_disposition": "reject",
            },
            {
                "expected_disposition": "reject",
                "disposition": "reject",
                "rejudged_disposition": "accept",
            },
            {
                "expected_disposition": "accept",
                "disposition": "accept",
                "rejudged_disposition": "accept",
            },
        ]
    )

    assert summary == {
        "production_enabled": False,
        "judged_count": 3,
        "correct_to_wrong": 1,
        "wrong_to_correct": 1,
        "healthy_direction": False,
    }
