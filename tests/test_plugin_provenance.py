"""Static ADR-74 precursor: bundled plugin lock matches the vendored artifacts."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OBSIDIAN = ROOT / "src" / ".obsidian"
PLUGINS = OBSIDIAN / "plugins"
LOCK = OBSIDIAN / "plugin-provenance-lock.json"
COMMUNITY = OBSIDIAN / "community-plugins.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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

        expected_files = {
            p.relative_to(OBSIDIAN).as_posix()
            for p in (PLUGINS / plugin_id).iterdir()
            if p.is_file()
        }
        assert set(entry["sha256"]) == expected_files
        for relpath, digest in entry["sha256"].items():
            assert len(digest) == 64
            assert _sha256(OBSIDIAN / relpath) == digest
