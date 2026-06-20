"""ADR-19 Tier 2: hub-threshold findings delegate to the map lane."""

from pathlib import Path

import tasks_mcp
from operations.integrity.linter import hub_handoff


def _vault(tmp_path: Path) -> Path:
    lo = tmp_path / ".memoria" / "lane-overrides"
    lo.mkdir(parents=True)
    (lo / "librarian.yaml").write_text(
        "profile: memoria-librarian\nrouting:\n  write_scope:\n"
        '    - "inbox/"\n    - "catalog/"\n'
        '    - "notes/fleeting/"\n    - "notes/sources/"\n',
        encoding="utf-8",
    )
    return tmp_path


def _claim(vault: Path, name: str, topics: str = "[sleep]") -> None:
    (vault / "notes/claims").mkdir(parents=True, exist_ok=True)
    (vault / f"notes/claims/{name}.md").write_text(
        "---\ntype: claim\nlifecycle: current\nmaturity: seedling\n"
        f"title: {name}\nsources: ['@x2024']\ntopics: {topics}\n---\nBody.\n",
        encoding="utf-8",
    )


def test_hub_threshold_handoff_creates_map_card_with_staging_paths(tmp_path):
    v = _vault(tmp_path)
    for i in range(3):
        _claim(v, f"sleep-{i}")
    calls = []

    class Result:
        stdout = '{"id":"card-42"}'

    def fake_runner(cmd, **kwargs):
        calls.append(cmd)
        return Result()

    rows = hub_handoff.handoff_hub_thresholds(v, threshold=3, card_runner=fake_runner)

    assert len(rows) == 1
    assert rows[0]["topic"] == "sleep"
    assert rows[0]["count"] == 3
    assert rows[0]["delegation"] == {
        "created": True,
        "card_id": "card-42",
        "lane": "map",
        "assignee": "memoria-librarian",
    }
    cmd = calls[0]
    assert cmd[:3] == ["hermes", "kanban", "create"]
    assert cmd[cmd.index("--assignee") + 1] == "memoria-librarian"
    assert cmd[cmd.index("--idempotency-key") + 1] == "hub-threshold-sleep"
    body = cmd[cmd.index("--body") + 1]
    allowed = body.split("## Allowed paths", 1)[1].split("## Expected outputs", 1)[0]
    assert "notes/fleeting/maps/" in allowed
    assert "inbox/" in allowed
    assert "notes/hubs/" not in allowed
    assert "Do not write, move, or create files under notes/hubs/" in body


def test_existing_hub_suppresses_handoff(tmp_path):
    v = _vault(tmp_path)
    for i in range(3):
        _claim(v, f"sleep-{i}")
    (v / "notes/hubs").mkdir(parents=True)
    (v / "notes/hubs/sleep.md").write_text(
        "---\ntype: hub\nlifecycle: current\ntitle: Sleep\ntopic: sleep\n---\n",
        encoding="utf-8",
    )

    assert (
        hub_handoff.handoff_hub_thresholds(v, threshold=3, card_runner=lambda *a, **k: None) == []
    )


def test_map_lane_ceiling_still_rejects_canonical_hub_home(tmp_path):
    v = _vault(tmp_path)
    assert tasks_mcp.validate(v, "map", ["notes/fleeting/maps/", "inbox/"]) == []
    errs = tasks_mcp.validate(v, "map", ["notes/hubs/"])
    assert errs and "exceeds" in errs[0]
