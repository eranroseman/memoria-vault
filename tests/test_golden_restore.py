"""The golden copy makes system files restorable (ADR-55)."""

from pathlib import Path

from memoria_vault.runtime.subsystems.integrity.linter import golden_restore as golden


def _seed(v: Path) -> None:
    (v / "system/templates").mkdir(parents=True)
    (v / "system/templates/claim.md").write_text("CANON", encoding="utf-8")
    (v / "system/dashboards").mkdir(parents=True)
    (v / "system/dashboards/home-board.md").write_text("DASH", encoding="utf-8")
    (v / "home.md").write_text("HOME", encoding="utf-8")
    (v / "_nav.md").write_text("NAV", encoding="utf-8")


def test_stage_builds_manifest(tmp_path):
    _seed(tmp_path)
    manifest = golden.stage(tmp_path)
    assert set(manifest) == {
        "system/templates/claim.md",
        "system/dashboards/home-board.md",
        "home.md",
        "_nav.md",
    }
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


def _seed_obsidian(v: Path) -> None:
    """Shipped Obsidian config (covered) + per-machine state (never covered)."""
    for plug in ("dataview", "quickadd", "agent-client", "obsidian-local-rest-api"):
        d = v / ".obsidian/plugins" / plug
        d.mkdir(parents=True)
        (d / "data.json").write_text('{"shipped": true}', encoding="utf-8")
    (v / ".obsidian/community-plugins.json").write_text('["dataview"]', encoding="utf-8")
    (v / ".obsidian/core-plugins.json").write_text('["graph"]', encoding="utf-8")
    (v / ".obsidian/snippets").mkdir(parents=True)
    (v / ".obsidian/snippets/memoria-link-colors.css").write_text("a {}", encoding="utf-8")
    (v / ".obsidian/snippets/memoria-property-badges.css").write_text("b {}", encoding="utf-8")
    (v / ".obsidian/workspace.json").write_text('{"user": "state"}', encoding="utf-8")


def test_manifest_covers_shipped_plugin_config_only(tmp_path):
    """Plugin-config drift: shipped Obsidian config is golden-covered;
    per-machine / runtime-generated state never enters the manifest."""
    _seed(tmp_path)
    _seed_obsidian(tmp_path)
    manifest = golden.stage(tmp_path)
    assert ".obsidian/plugins/dataview/data.json" in manifest
    assert ".obsidian/plugins/quickadd/data.json" in manifest
    assert ".obsidian/community-plugins.json" in manifest
    assert ".obsidian/core-plugins.json" in manifest
    assert ".obsidian/snippets/memoria-link-colors.css" in manifest
    assert ".obsidian/snippets/memoria-property-badges.css" in manifest
    # per-machine state: agent-client is seeded per machine, the REST API plugin
    # regenerates its data.json, and workspace state is the user's
    assert ".obsidian/plugins/agent-client/data.json" not in manifest
    assert ".obsidian/plugins/obsidian-local-rest-api/data.json" not in manifest
    assert ".obsidian/workspace.json" not in manifest


def test_plugin_config_drift_detected_and_restored(tmp_path):
    _seed(tmp_path)
    _seed_obsidian(tmp_path)
    golden.stage(tmp_path)
    (tmp_path / ".obsidian/plugins/dataview/data.json").write_text(
        '{"shipped": false}', encoding="utf-8"
    )
    assert golden.check(tmp_path) == {".obsidian/plugins/dataview/data.json": "drifted"}
    golden.restore(tmp_path, apply=True)
    assert (tmp_path / ".obsidian/plugins/dataview/data.json").read_text(
        encoding="utf-8"
    ) == '{"shipped": true}'
    assert golden.check(tmp_path) == {}


def test_upgrade_command_is_not_shipped():
    assert not hasattr(golden, "upgrade")
