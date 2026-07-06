from __future__ import annotations

from memoria_vault.runtime.seeded_errors import (
    SEEDED_PROBE_SENTINEL,
    seeded_probe_review_batch,
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
