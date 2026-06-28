"""Bundled Obsidian plugin provenance lock validation."""

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import plugin_provenance_doctor as doctor

ROOT = Path(__file__).resolve().parent.parent
OBSIDIAN = ROOT / "vault-template" / ".obsidian"
PLUGINS = OBSIDIAN / "plugins"
LOCK = OBSIDIAN / "plugin-provenance-lock.json"
COMMUNITY = OBSIDIAN / "community-plugins.json"


def test_plugin_provenance_doctor_accepts_repo_lock():
    assert doctor.check(ROOT) == []


def test_plugin_provenance_lock_covers_enabled_plugins_and_artifacts():
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    enabled = set(json.loads(COMMUNITY.read_text(encoding="utf-8")))
    entries = {p["id"]: p for p in lock["plugins"]}

    assert lock["schema_version"] == 1
    assert set(entries) == enabled
    assert set(entries) == {p.name for p in PLUGINS.iterdir() if p.is_dir()}

    for plugin_id, entry in entries.items():
        manifest = json.loads((PLUGINS / plugin_id / "manifest.json").read_text(encoding="utf-8"))
        assert entry["name"] == manifest["name"]
        assert entry["version"] == manifest["version"]
        assert entry["pinned_ref"] == manifest["version"]
        assert entry["upstream"].startswith("https://github.com/")
        assert entry["pinned_commit"]
        assert entry["license"]
        assert entry["local_patch_status"]

        for relpath, digest in entry["sha256"].items():
            assert len(digest) == 64
            assert doctor.sha256(OBSIDIAN / relpath) == digest


def test_plugin_provenance_doctor_flags_undeclared_executables(tmp_path):
    root = _copy_plugin_fixture(tmp_path)
    extra = root / "vault-template/.obsidian/plugins/dataview/extra.js"
    extra.write_text("console.log('extra');\n", encoding="utf-8")

    findings = doctor.check(root)

    assert any("undeclared executable artifact" in finding.message for finding in findings)
    assert any(finding.path == "plugins/dataview/extra.js" for finding in findings)


def test_plugin_provenance_doctor_flags_bad_digest(tmp_path):
    root = _copy_plugin_fixture(tmp_path)
    lock_path = root / "vault-template/.obsidian/plugin-provenance-lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["plugins"][0]["sha256"]["plugins/dataview/main.js"] = "0" * 64
    lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")

    findings = doctor.check(root)

    assert any("SHA-256 mismatch" in finding.message for finding in findings)


def test_plugin_provenance_doctor_flags_duplicate_lock_entries(tmp_path):
    root = _copy_plugin_fixture(tmp_path)
    lock_path = root / "vault-template/.obsidian/plugin-provenance-lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["plugins"].append(dict(lock["plugins"][0]))
    lock_path.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")

    findings = doctor.check(root)

    assert any("has 2 lock entries" in finding.message for finding in findings)


def _copy_plugin_fixture(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    obsidian = root / "vault-template/.obsidian"
    obsidian.mkdir(parents=True)
    shutil.copy2(COMMUNITY, obsidian / "community-plugins.json")
    shutil.copy2(LOCK, obsidian / "plugin-provenance-lock.json")
    shutil.copytree(PLUGINS, obsidian / "plugins")
    return root
