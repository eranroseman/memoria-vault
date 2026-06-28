#!/usr/bin/env python3
"""Validate the bundled Obsidian plugin provenance lock.

This doctor is intentionally local-only: it reads the committed lock and
artifacts, computes SHA-256 digests, and never contacts upstream repositories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
OBSIDIAN_REL = Path("vault-template/.obsidian")
PLUGINS_REL = OBSIDIAN_REL / "plugins"
LOCK_REL = OBSIDIAN_REL / "plugin-provenance-lock.json"
COMMUNITY_REL = OBSIDIAN_REL / "community-plugins.json"

EXECUTABLE_SUFFIXES = {
    ".bat",
    ".cmd",
    ".cjs",
    ".dll",
    ".dylib",
    ".exe",
    ".js",
    ".mjs",
    ".node",
    ".ps1",
    ".sh",
    ".so",
    ".wasm",
}


@dataclass(frozen=True)
class Finding:
    path: str
    message: str

    def format(self) -> str:
        return f"{self.path}: {self.message}"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(root: Path = ROOT) -> list[Finding]:
    root = root.resolve()
    obsidian = root / OBSIDIAN_REL
    plugins_root = root / PLUGINS_REL
    lock_path = root / LOCK_REL
    community_path = root / COMMUNITY_REL
    findings: list[Finding] = []

    lock = _read_json(lock_path, findings)
    enabled = _read_json(community_path, findings)
    if not isinstance(lock, dict) or not isinstance(enabled, list):
        return findings

    if lock.get("schema_version") != 1:
        findings.append(Finding(_rel(lock_path, root), "schema_version must be 1"))

    entries_raw = lock.get("plugins")
    if not isinstance(entries_raw, list):
        findings.append(Finding(_rel(lock_path, root), "plugins must be a list"))
        return findings

    enabled_ids = _string_list(enabled, _rel(community_path, root), findings)
    entries = _entries_by_id(entries_raw, _rel(lock_path, root), findings)
    plugin_dirs = (
        {p.name for p in plugins_root.iterdir() if p.is_dir()} if plugins_root.exists() else set()
    )

    _compare_ids(
        expected=set(enabled_ids),
        actual=set(entries),
        expected_name="enabled plugins",
        actual_name="lock entries",
        path=_rel(lock_path, root),
        findings=findings,
    )
    _compare_ids(
        expected=plugin_dirs,
        actual=set(entries),
        expected_name="plugin directories",
        actual_name="lock entries",
        path=_rel(lock_path, root),
        findings=findings,
    )

    declared_relpaths: set[str] = set()
    for plugin_id, entry in entries.items():
        plugin_dir = plugins_root / plugin_id
        manifest_path = plugin_dir / "manifest.json"
        manifest = _read_json(manifest_path, findings)
        if not isinstance(manifest, dict):
            continue
        _check_metadata(plugin_id, entry, manifest, _rel(lock_path, root), findings)
        declared_relpaths.update(_check_artifacts(entry, obsidian, root, findings))

    _check_undeclared_executables(plugins_root, obsidian, declared_relpaths, root, findings)
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root to validate")
    args = parser.parse_args(argv)

    findings = check(args.root)
    if findings:
        print("plugin-provenance-doctor: FAIL", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding.format()}", file=sys.stderr)
        return 1
    print("plugin-provenance-doctor: clean")
    return 0


def _read_json(path: Path, findings: list[Finding]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        findings.append(Finding(str(path), "missing required JSON file"))
    except json.JSONDecodeError as exc:
        findings.append(Finding(str(path), f"invalid JSON: {exc}"))
    return None


def _string_list(values: list[Any], path: str, findings: list[Finding]) -> list[str]:
    strings: list[str] = []
    for index, value in enumerate(values):
        if isinstance(value, str) and value:
            strings.append(value)
        else:
            findings.append(Finding(path, f"entry {index} must be a non-empty string"))
    for plugin_id, count in Counter(strings).items():
        if count > 1:
            findings.append(Finding(path, f"plugin {plugin_id!r} appears {count} times"))
    return strings


def _entries_by_id(
    entries_raw: list[Any], path: str, findings: list[Finding]
) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    ids: list[str] = []
    for index, entry in enumerate(entries_raw):
        if not isinstance(entry, dict):
            findings.append(Finding(path, f"plugins[{index}] must be an object"))
            continue
        plugin_id = entry.get("id")
        if not isinstance(plugin_id, str) or not plugin_id:
            findings.append(Finding(path, f"plugins[{index}].id must be a non-empty string"))
            continue
        ids.append(plugin_id)
        entries.setdefault(plugin_id, entry)
    for plugin_id, count in Counter(ids).items():
        if count > 1:
            findings.append(Finding(path, f"plugin {plugin_id!r} has {count} lock entries"))
    return entries


def _compare_ids(
    *,
    expected: set[str],
    actual: set[str],
    expected_name: str,
    actual_name: str,
    path: str,
    findings: list[Finding],
) -> None:
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        findings.append(
            Finding(path, f"{actual_name} missing {expected_name}: {', '.join(missing)}")
        )
    if extra:
        findings.append(Finding(path, f"{actual_name} not in {expected_name}: {', '.join(extra)}"))


def _check_metadata(
    plugin_id: str,
    entry: dict[str, Any],
    manifest: dict[str, Any],
    path: str,
    findings: list[Finding],
) -> None:
    expected = {
        "name": manifest.get("name"),
        "version": manifest.get("version"),
        "pinned_ref": manifest.get("version"),
    }
    for field, value in expected.items():
        if entry.get(field) != value:
            findings.append(
                Finding(path, f"{plugin_id}.{field} must match manifest value {value!r}")
            )
    for field in ("upstream", "pinned_commit", "license", "local_patch_status"):
        if not isinstance(entry.get(field), str) or not entry[field]:
            findings.append(Finding(path, f"{plugin_id}.{field} must be a non-empty string"))
    upstream = entry.get("upstream")
    if isinstance(upstream, str) and not upstream.startswith("https://github.com/"):
        findings.append(Finding(path, f"{plugin_id}.upstream must be a GitHub HTTPS URL"))


def _check_artifacts(
    entry: dict[str, Any],
    obsidian: Path,
    root: Path,
    findings: list[Finding],
) -> set[str]:
    plugin_id = entry.get("id", "<unknown>")
    artifacts = entry.get("sha256")
    if not isinstance(artifacts, dict):
        findings.append(
            Finding(_rel(root / LOCK_REL, root), f"{plugin_id}.sha256 must be an object")
        )
        return set()

    declared: set[str] = set()
    for relpath, digest in artifacts.items():
        if not isinstance(relpath, str) or not relpath:
            findings.append(
                Finding(_rel(root / LOCK_REL, root), f"{plugin_id}.sha256 has a non-string path")
            )
            continue
        artifact_path = _safe_artifact_path(obsidian, relpath)
        if artifact_path is None:
            findings.append(
                Finding(relpath, "artifact path must stay under vault-template/.obsidian")
            )
            continue
        declared.add(relpath)
        if not artifact_path.is_file():
            findings.append(Finding(relpath, "declared artifact is missing"))
            continue
        if not isinstance(digest, str) or len(digest) != 64 or not _is_hex(digest):
            findings.append(Finding(relpath, "digest must be a 64-character SHA-256 hex string"))
            continue
        actual = sha256(artifact_path)
        if actual != digest:
            findings.append(Finding(relpath, f"SHA-256 mismatch: expected {digest}, got {actual}"))
    return declared


def _check_undeclared_executables(
    plugins_root: Path,
    obsidian: Path,
    declared_relpaths: set[str],
    root: Path,
    findings: list[Finding],
) -> None:
    if not plugins_root.exists():
        findings.append(Finding(_rel(plugins_root, root), "plugin directory is missing"))
        return
    for path in sorted(plugins_root.rglob("*")):
        if not path.is_file() or not _is_executable_artifact(path):
            continue
        relpath = path.relative_to(obsidian).as_posix()
        if relpath not in declared_relpaths:
            findings.append(Finding(relpath, "undeclared executable artifact"))


def _safe_artifact_path(obsidian: Path, relpath: str) -> Path | None:
    candidate = Path(relpath)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    artifact_path = (obsidian / candidate).resolve()
    try:
        artifact_path.relative_to(obsidian.resolve())
    except ValueError:
        return None
    return artifact_path


def _is_executable_artifact(path: Path) -> bool:
    return path.suffix.lower() in EXECUTABLE_SUFFIXES or bool(path.stat().st_mode & stat.S_IXUSR)


def _is_hex(value: str) -> bool:
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
