"""The delegation path (ADR-48): lane routing + the ceiling-narrowing rule."""

from pathlib import Path
from types import SimpleNamespace

import tasks_mcp

SRC = Path(__file__).resolve().parent.parent / "vault-template"


def _vault(tmp_path: Path) -> Path:
    lo = tmp_path / ".memoria" / "lane-overrides"
    lo.mkdir(parents=True)
    (lo / "librarian.yaml").write_text(
        "profile: memoria-librarian\nrouting:\n  write_scope:\n"
        '    - ".memoria/staging/catalog/"\n    - ".memoria/staging/knowledge/"\n',
        encoding="utf-8",
    )
    (lo / "copi.yaml").write_text(
        "profile: memoria-copi\nrouting:\n  write_scope: []\n", encoding="utf-8"
    )
    return tmp_path


def test_every_lane_routes_to_a_shipped_profile():
    shipped = {p.name for p in (SRC / ".memoria" / "profiles").iterdir() if p.is_dir()}
    for lane, profile in tasks_mcp.LANE_PROFILE.items():
        assert profile in shipped, f"lane {lane} routes to unshipped {profile}"
    assert set(tasks_mcp.LANE_PROFILE) == {
        "catalog",
        "extract",
        "link",
        "map",
        "verify",
    }


def test_narrowing_passes_widening_fails(tmp_path):
    v = _vault(tmp_path)
    assert tasks_mcp.validate(v, "catalog", [".memoria/staging/catalog/"]) == []
    errs = tasks_mcp.validate(v, "catalog", ["catalog/"])
    assert errs and "exceeds" in errs[0]
    assert tasks_mcp.validate(v, "verify", []) == []


def test_deferred_alpha11_lanes_are_not_routable(tmp_path):
    v = _vault(tmp_path)
    for lane in ("draft", "code"):
        errs = tasks_mcp.validate(v, lane, [])
        assert errs and "unknown lane" in errs[0]


def test_corrupt_lane_override_fails_closed_with_warning(tmp_path, capsys):
    v = _vault(tmp_path)
    lo = v / ".memoria" / "lane-overrides"
    (lo / "librarian.yaml").write_text("routing: [unclosed\n", encoding="utf-8")
    errs = tasks_mcp.validate(v, "catalog", [".memoria/staging/catalog/"])
    assert errs and "exceeds" in errs[0]  # fail-closed: nothing delegable
    assert "librarian.yaml" in capsys.readouterr().err


def test_unknown_lane_rejected(tmp_path):
    v = _vault(tmp_path)
    errs = tasks_mcp.validate(v, "publish", [])
    assert errs and "unknown lane" in errs[0]


def test_delegate_blocks_ceiling_violations_before_card_creation(tmp_path):
    v = _vault(tmp_path)
    out = tasks_mcp.delegate(v, "catalog", "goal", allowed_paths=["system/"])
    assert out["created"] is False and out["error"] == "ceiling-violation"


def test_card_creation_degrades_with_fallback_hint(tmp_path, monkeypatch):
    v = _vault(tmp_path)
    monkeypatch.setattr(
        tasks_mcp,
        "create_card",
        lambda lane, goal, body, idempotency_key="", **kwargs: {
            "created": False,
            "error": "hermes-cli-not-found",
            "fallback": "manual",
        },
    )
    out = tasks_mcp.delegate(
        v,
        "catalog",
        "Ingest @smith2024",
        allowed_paths=[".memoria/staging/catalog/"],
        idempotency_key="reingest:smith2024",
    )
    # in CI there is no hermes CLI — the tool must degrade with a usable fallback
    if not out.get("created"):
        assert out["error"].startswith(("hermes-cli-not-found", "kanban-create"))
        if out["error"] == "hermes-cli-not-found":
            assert "fallback" in out


def test_delegate_stops_when_block_loudness_card_is_open(tmp_path):
    v = _vault(tmp_path)
    (v / "inbox").mkdir()
    (v / "inbox/block.md").write_text(
        "---\ntitle: Stop\ntype: alert\nlifecycle: proposed\nloudness: block\n---\n",
        encoding="utf-8",
    )
    out = tasks_mcp.delegate(v, "catalog", "goal", allowed_paths=[".memoria/staging/catalog/"])
    assert out["created"] is False
    assert out["error"] == "loudness-block-active"
    assert out["blockers"][0]["path"] == "inbox/block.md"


def test_delegate_resumes_after_block_card_is_acknowledged(tmp_path, monkeypatch):
    v = _vault(tmp_path)
    (v / "inbox").mkdir()
    (v / "inbox/block.md").write_text(
        "---\ntitle: Stop\ntype: alert\nlifecycle: current\nloudness: block\n---\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(tasks_mcp, "create_card", lambda *args, **kwargs: {"created": True})
    assert (
        tasks_mcp.delegate(v, "catalog", "goal", allowed_paths=[".memoria/staging/catalog/"])[
            "created"
        ]
        is True
    )


def test_delegate_projects_success_to_inbox_activity(tmp_path):
    v = _vault(tmp_path)

    def runner(*args, **kwargs):
        return SimpleNamespace(stdout='{"task": {"id": "t_copi", "status": "ready"}}')

    out = tasks_mcp.delegate(v, "catalog", "Ingest @smith2026", card_runner=runner)
    assert out["created"] is True
    activity = v / "system" / "board" / "t_copi.md"
    assert activity.is_file()
    text = activity.read_text(encoding="utf-8")
    assert "type: worker-card" in text
    assert 'task_id: "t_copi"' in text
    assert "Status: queued. No action needed; wait for the result." in text
    assert not (v / "inbox").exists()
