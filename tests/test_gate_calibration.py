from __future__ import annotations

import pytest

from memoria_vault.runtime.seeded_errors import (
    SEEDED_PROBE_SENTINEL,
    seeded_probe_review_batch,
)

pytestmark = pytest.mark.unit


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

    assert batch["max_items_per_batch"] == 1
    assert len(batch["probes"]) == 1
    probe = batch["probes"][0]
    assert probe["sentinel"] == SEEDED_PROBE_SENTINEL
    assert "run_id" not in probe
    assert "commit" not in probe
    assert "rationale" not in probe
    assert probe["self_rebuttal"] == "This proposal cites a missing source."
    assert probe["certainty"] == "low"


def test_probe_payload_carries_the_case_not_a_sentinel_shape() -> None:
    """Replacing any field with a constant must fail here; before this test the
    whole payload survived a wholesale "MUT" substitution."""
    cases = [
        {
            "id": "case-a",
            "target_id": "notes/a.md",
            "error_class": "missing-evidence",
            "expected_disposition": "quarantine",
            "certainty": "high",
        }
    ]

    [probe] = seeded_probe_review_batch(cases)["probes"]

    assert probe["case_id"] == "case-a"
    assert probe["target_id"] == "notes/a.md"
    assert probe["error_class"] == "missing-evidence"
    assert probe["expected_disposition"] == "quarantine"
    assert probe["certainty"] == "high"


def test_probe_defaults_come_from_the_builder_not_the_case() -> None:
    [probe] = seeded_probe_review_batch([{"id": "bare", "target_id": "notes/b.md"}])["probes"]

    assert probe["expected_disposition"] == "reject"
    assert probe["certainty"] == "low"
    assert probe["error_class"] == ""
    assert "reviewer should check" in probe["self_rebuttal"]


def test_default_cap_is_five_and_the_floor_is_one() -> None:
    cases = [{"id": f"c{i}", "target_id": f"notes/{i}.md"} for i in range(7)]

    default_batch = seeded_probe_review_batch(cases)
    floored_batch = seeded_probe_review_batch(cases, max_items=0)

    assert default_batch["max_items_per_batch"] == 5
    assert len(default_batch["probes"]) == 5
    assert floored_batch["max_items_per_batch"] == 1
    assert len(floored_batch["probes"]) == 1
