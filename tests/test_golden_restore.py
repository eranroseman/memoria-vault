"""The golden copy makes system files restorable (ADR-55)."""

from pathlib import Path

import golden


def _seed(v: Path) -> None:
    (v / "system/templates").mkdir(parents=True)
    (v / "system/templates/claim.md").write_text("CANON", encoding="utf-8")
    (v / "system/dashboards").mkdir(parents=True)
    (v / "system/dashboards/home-board.md").write_text("DASH", encoding="utf-8")
    (v / "home.md").write_text("HOME", encoding="utf-8")


def test_stage_builds_manifest(tmp_path):
    _seed(tmp_path)
    manifest = golden.stage(tmp_path)
    assert set(manifest) == {"system/templates/claim.md",
                             "system/dashboards/home-board.md", "home.md"}
    assert golden.check(tmp_path) == {}


def test_drift_and_missing_detected(tmp_path):
    _seed(tmp_path)
    golden.stage(tmp_path)
    (tmp_path / "system/templates/claim.md").write_text("EDITED", encoding="utf-8")
    (tmp_path / "home.md").unlink()
    drift = golden.check(tmp_path)
    assert drift == {"system/templates/claim.md": "drifted", "home.md": "missing"}


def test_restore_is_propose_only_by_default(tmp_path):
    _seed(tmp_path)
    golden.stage(tmp_path)
    (tmp_path / "system/templates/claim.md").write_text("EDITED", encoding="utf-8")
    proposed = golden.restore(tmp_path)
    assert proposed == ["system/templates/claim.md"]
    # nothing changed — propose, not dispose
    assert (tmp_path / "system/templates/claim.md").read_text(encoding="utf-8") == "EDITED"


def test_restore_apply_round_trips(tmp_path):
    _seed(tmp_path)
    golden.stage(tmp_path)
    (tmp_path / "system/templates/claim.md").write_text("EDITED", encoding="utf-8")
    (tmp_path / "home.md").unlink()
    golden.restore(tmp_path, apply=True)
    assert (tmp_path / "system/templates/claim.md").read_text(encoding="utf-8") == "CANON"
    assert (tmp_path / "home.md").read_text(encoding="utf-8") == "HOME"
    assert golden.check(tmp_path) == {}


def test_deleted_template_is_restorable(tmp_path):
    """#179: a template removed from the vault comes back from the golden copy."""
    _seed(tmp_path)
    golden.stage(tmp_path)
    (tmp_path / "system/templates/claim.md").unlink()
    assert golden.check(tmp_path) == {"system/templates/claim.md": "missing"}
    golden.restore(tmp_path, apply=True)
    assert (tmp_path / "system/templates/claim.md").read_text(encoding="utf-8") == "CANON"


def test_restore_scoped_to_named_paths(tmp_path):
    _seed(tmp_path)
    golden.stage(tmp_path)
    (tmp_path / "system/templates/claim.md").write_text("E1", encoding="utf-8")
    (tmp_path / "system/dashboards/home-board.md").write_text("E2", encoding="utf-8")
    golden.restore(tmp_path, ["system/templates/claim.md"], apply=True)
    assert (tmp_path / "system/templates/claim.md").read_text(encoding="utf-8") == "CANON"
    assert (tmp_path / "system/dashboards/home-board.md").read_text(encoding="utf-8") == "E2"
