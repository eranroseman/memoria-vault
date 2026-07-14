"""Hub-threshold findings create map-proposal requests."""

from pathlib import Path

from memoria_vault.runtime.subsystems.integrity.linter import hub_handoff


def _claim(vault: Path, name: str, topics: str = "[sleep]") -> None:
    (vault / "notes").mkdir(parents=True, exist_ok=True)
    (vault / f"notes/{name}.md").write_text(
        f"---\ntype: note\ncheck_status: checked\ntitle: {name}\ntags: {topics}\n---\nBody.\n",
        encoding="utf-8",
    )


def test_hub_threshold_handoff_creates_map_card_with_staging_paths(tmp_path):
    v = tmp_path
    for i in range(3):
        _claim(v, f"sleep-{i}")
    rows = hub_handoff.handoff_hub_thresholds(v, threshold=3)

    assert len(rows) == 1
    assert rows[0]["topic"] == "sleep"
    assert rows[0]["count"] == 3
    assert rows[0]["operation_id"] == "suggest-hubs"
    assert rows[0]["posture"] == "mapping"
    assert rows[0]["goal"] == "Draft hub proposal: sleep"
    assert rows[0]["idempotency_key"] == "hub-threshold-sleep"
    assert rows[0]["allowed_paths"] == ["notes/maps/"]
    assert "hubs/" not in "\n".join(rows[0]["allowed_paths"])
    assert "Do not write, move, or create files under hubs/" in rows[0]["expected_outputs"]


def test_existing_hub_suppresses_handoff(tmp_path):
    v = tmp_path
    for i in range(3):
        _claim(v, f"sleep-{i}")
    (v / "hubs").mkdir(parents=True)
    (v / "hubs/sleep.md").write_text(
        "---\ntype: hub\ncheck_status: checked\ntitle: Sleep\ndescription: Sleep\n---\n",
        encoding="utf-8",
    )

    assert hub_handoff.handoff_hub_thresholds(v, threshold=3) == []


def test_handoff_never_allows_canonical_hub_home(tmp_path):
    v = tmp_path
    for i in range(3):
        _claim(v, f"sleep-{i}")
    rows = hub_handoff.handoff_hub_thresholds(v, threshold=3)
    assert rows[0]["allowed_paths"] == ["notes/maps/"]
    assert "hubs/" not in rows[0]["allowed_paths"]
