#!/usr/bin/env python3
"""golden — the restorable golden copy of system files (ADR-55).

The installer stages a canonical copy of every system file at
`<vault>/.memoria/golden/` with a SHA-256 manifest. This engine turns the Linter
into a *repairer*: `check` reports drift between the live system files and the
golden copy; `restore` writes the golden content back — **propose-only by
default** (a dry-run diff + an Inbox flag); `--apply` performs the restore
(the PI or cron runs it deliberately).

Usage:
  python3 golden_restore.py --vault V stage          stage/refresh the golden copy from the live system files
  python3 golden_restore.py --vault V check          report drifted/missing system files (exit 1 if any)
  python3 golden_restore.py --vault V restore [--apply] [PATH ...]
  python3 golden_restore.py --vault V upgrade --source SRC [--apply]
  python3 golden_restore.py --self-test
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

GOLDEN_RELDIR = ".memoria/golden"
MANIFEST = "manifest.json"

# the system files the golden copy covers (vault-relative prefixes/files)
SYSTEM_PREFIXES = (
    "system/templates/",
    "system/dashboards/",
    "system/patterns/",
    "system/eval/",
    "system/scripts/",
)
SYSTEM_FILES = ("home.md", "system/vocabulary.md", "AGENTS.md")

# Memoria-shipped Obsidian config the installer deploys (plugin-config drift,
# ADR-67): the per-plugin settings files plus the plugin/snippet rosters. Only
# shipped config enters the manifest — never per-machine or runtime-generated
# state: agent-client/data.json is seeded per machine from its .example,
# obsidian-local-rest-api regenerates data.json (apiKey + TLS) on first launch,
# and workspace/appearance/graph state is the user's to mutate.
OBSIDIAN_FILES = (
    ".obsidian/community-plugins.json",
    ".obsidian/core-plugins.json",
    ".obsidian/snippets/memoria-link-colors.css",
    ".obsidian/snippets/memoria-property-badges.css",
)
OBSIDIAN_PLUGIN_DATA_SKIP = ("agent-client", "obsidian-local-rest-api")


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _iter_system_files(vault: Path):
    for prefix in SYSTEM_PREFIXES:
        d = vault / prefix
        if d.is_dir():
            for p in sorted(d.rglob("*")):
                if p.is_file() and p.name != ".gitkeep":
                    yield p.relative_to(vault).as_posix()
    for f in SYSTEM_FILES:
        if (vault / f).is_file():
            yield f
    plugdir = vault / ".obsidian" / "plugins"
    if plugdir.is_dir():
        for plug in sorted(p for p in plugdir.iterdir() if p.is_dir()):
            if plug.name in OBSIDIAN_PLUGIN_DATA_SKIP:
                continue
            f = plug / "data.json"
            if f.is_file():
                yield f.relative_to(vault).as_posix()
    for f in OBSIDIAN_FILES:
        if (vault / f).is_file():
            yield f


def stage(vault: Path) -> dict[str, str]:
    """Copy every system file into the golden dir and write the manifest."""
    golden = vault / GOLDEN_RELDIR
    manifest: dict[str, str] = {}
    for rel in _iter_system_files(vault):
        src = vault / rel
        dst = golden / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        manifest[rel] = _sha256(src)
    golden.mkdir(parents=True, exist_ok=True)
    (golden / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True),
                                   encoding="utf-8")
    return manifest


def _stage_from_source(vault: Path, source: Path) -> dict[str, str]:
    """Copy every source system file into the golden dir and write the manifest."""
    golden = vault / GOLDEN_RELDIR
    old_manifest = set(load_manifest(vault))
    manifest: dict[str, str] = {}
    for rel in _iter_system_files(source):
        src = source / rel
        dst = golden / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        manifest[rel] = _sha256(src)
    for rel in sorted(old_manifest - set(manifest)):
        stale = golden / rel
        if stale.is_file():
            stale.unlink()
    golden.mkdir(parents=True, exist_ok=True)
    (golden / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True),
                                   encoding="utf-8")
    return manifest


def load_manifest(vault: Path) -> dict[str, str]:
    f = vault / GOLDEN_RELDIR / MANIFEST
    if not f.is_file():
        return {}
    return json.loads(f.read_text(encoding="utf-8"))


def check(vault: Path) -> dict[str, str]:
    """Return {relpath: 'drifted' | 'missing'} vs the manifest."""
    out: dict[str, str] = {}
    for rel, want in load_manifest(vault).items():
        live = vault / rel
        if not live.is_file():
            out[rel] = "missing"
        elif _sha256(live) != want:
            out[rel] = "drifted"
    return out


def restore(vault: Path, paths: list[str] | None = None, apply: bool = False) -> list[str]:
    """Restore drifted/missing system files from the golden copy.

    Propose-only by default: returns the list it WOULD restore. With apply=True
    it writes the golden bytes back. Only files in the manifest are touched.
    """
    drift = check(vault)
    targets = [p for p in drift if not paths or p in paths]
    if apply:
        for rel in targets:
            src = vault / GOLDEN_RELDIR / rel
            dst = vault / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())
    return targets


def upgrade(vault: Path, source: Path, apply: bool = False) -> dict[str, list[str]]:
    """Three-way reconcile source-system files against old golden and live.

    For each covered path:
    - old golden is the previous release baseline;
    - source is the new release baseline;
    - live is the user's deployed vault.

    Clean release changes apply only when live still matches old golden (or the
    path is new and absent live). User-customized paths are preserved and reported.
    With apply=True the golden copy is refreshed to the new source baseline after
    live reconciliation, so future drift checks compare against the new release.
    """
    old = load_manifest(vault)
    new = {rel: _sha256(source / rel) for rel in _iter_system_files(source)}
    result = {k: [] for k in ("would_apply", "would_remove", "applied", "removed",
                              "unchanged", "customized", "conflicts")}
    for rel in sorted(set(old) | set(new)):
        old_hash = old.get(rel)
        new_hash = new.get(rel)
        live = vault / rel
        live_hash = _sha256(live) if live.is_file() else None
        if new_hash is None:
            if live_hash is None:
                result["unchanged"].append(rel)
            elif live_hash == old_hash:
                if apply:
                    live.unlink()
                    result["removed"].append(rel)
                else:
                    result["would_remove"].append(rel)
            else:
                result["conflicts"].append(rel)
            continue
        src = source / rel
        if old_hash is None:
            if live_hash is None:
                if apply:
                    live.parent.mkdir(parents=True, exist_ok=True)
                    live.write_bytes(src.read_bytes())
                    result["applied"].append(rel)
                else:
                    result["would_apply"].append(rel)
            elif live_hash == new_hash:
                result["unchanged"].append(rel)
            else:
                result["conflicts"].append(rel)
            continue
        if live_hash == new_hash:
            result["unchanged"].append(rel)
        elif live_hash == old_hash:
            if apply:
                live.parent.mkdir(parents=True, exist_ok=True)
                live.write_bytes(src.read_bytes())
                result["applied"].append(rel)
            else:
                result["would_apply"].append(rel)
        elif old_hash == new_hash:
            result["customized"].append(rel)
        else:
            result["conflicts"].append(rel)
    if apply:
        _stage_from_source(vault, source)
    return result


def _self_test() -> int:
    import tempfile
    failures = 0

    def ck(label: str, ok: bool) -> None:
        nonlocal failures
        print(("  ok " if ok else "  FAIL ") + label)
        if not ok:
            failures += 1

    with tempfile.TemporaryDirectory() as td:
        v = Path(td)
        (v / "system/templates").mkdir(parents=True)
        (v / "system/templates/claim.md").write_text("CANON", encoding="utf-8")
        (v / "home.md").write_text("HOME", encoding="utf-8")
        m = stage(v)
        ck("manifest covers both", len(m) == 2)
        ck("clean check is empty", check(v) == {})
        (v / "system/templates/claim.md").write_text("DRIFTED", encoding="utf-8")
        (v / "home.md").unlink()
        d = check(v)
        ck("drift + missing detected",
           d.get("system/templates/claim.md") == "drifted" and d.get("home.md") == "missing")
        proposed = restore(v)
        ck("restore is propose-only by default",
           (v / "system/templates/claim.md").read_text(encoding="utf-8") == "DRIFTED"
           and len(proposed) == 2)
        restore(v, apply=True)
        ck("apply restores bytes",
           (v / "system/templates/claim.md").read_text(encoding="utf-8") == "CANON"
           and (v / "home.md").read_text(encoding="utf-8") == "HOME")
        ck("post-restore check clean", check(v) == {})
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        old_src, new_src, v = root / "old", root / "new", root / "vault"
        (old_src / "system/templates").mkdir(parents=True)
        (new_src / "system/templates").mkdir(parents=True)
        (v / "system/templates").mkdir(parents=True)
        (old_src / "system/templates/a.md").write_text("OLD", encoding="utf-8")
        (new_src / "system/templates/a.md").write_text("NEW", encoding="utf-8")
        (new_src / "system/templates/b.md").write_text("ADDED", encoding="utf-8")
        (v / "system/templates/a.md").write_text("OLD", encoding="utf-8")
        _stage_from_source(v, old_src)
        planned = upgrade(v, new_src)
        ck("upgrade dry-run plans clean changed + added files",
           planned["would_apply"] == ["system/templates/a.md", "system/templates/b.md"])
        upgrade(v, new_src, apply=True)
        ck("upgrade apply writes clean changed + added files",
           (v / "system/templates/a.md").read_text(encoding="utf-8") == "NEW"
           and (v / "system/templates/b.md").read_text(encoding="utf-8") == "ADDED")
        ck("upgrade refreshes golden manifest to new baseline", check(v) == {})
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        old_src, new_src, v = root / "old", root / "new", root / "vault"
        (old_src / "system/templates").mkdir(parents=True)
        (new_src / "system/templates").mkdir(parents=True)
        (v / "system/templates").mkdir(parents=True)
        (old_src / "system/templates/a.md").write_text("OLD", encoding="utf-8")
        (new_src / "system/templates/a.md").write_text("NEW", encoding="utf-8")
        (v / "system/templates/a.md").write_text("USER", encoding="utf-8")
        _stage_from_source(v, old_src)
        got = upgrade(v, new_src, apply=True)
        ck("upgrade preserves customized conflicting live file",
           got["conflicts"] == ["system/templates/a.md"]
           and (v / "system/templates/a.md").read_text(encoding="utf-8") == "USER")
    print("self-test:", "PASS" if failures == 0 else f"{failures} FAILURE(S)")
    return 1 if failures else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("command", nargs="?", choices=["stage", "check", "restore", "upgrade"])
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--source", type=Path,
                    help="new release source tree for three-way golden upgrade")
    args = ap.parse_args()
    if args.self_test:
        sys.exit(_self_test())
    if not args.vault or not args.command:
        ap.error("provide --vault and a command (stage | check | restore)")
    if args.command == "stage":
        m = stage(args.vault)
        print(f"golden: staged {len(m)} system file(s)")
    elif args.command == "check":
        d = check(args.vault)
        for rel, state in sorted(d.items()):
            print(f"  {state:8s} {rel}")
        print(f"golden: {len(d)} drifted/missing file(s)")
        sys.exit(1 if d else 0)
    elif args.command == "restore":
        targets = restore(args.vault, args.paths or None, apply=args.apply)
        verb = "restored" if args.apply else "would restore (use --apply)"
        for rel in targets:
            print(f"  {rel}")
        print(f"golden: {verb} {len(targets)} file(s)")
    else:
        if not args.source:
            ap.error("upgrade requires --source")
        result = upgrade(args.vault, args.source, apply=args.apply)
        for key in ("would_apply", "would_remove", "applied", "removed",
                    "customized", "conflicts"):
            for rel in result[key]:
                print(f"  {key:12s} {rel}")
        changed = sum(len(result[k]) for k in ("would_apply", "would_remove", "applied", "removed"))
        conflicts = len(result["conflicts"])
        mode = "applied" if args.apply else "would apply (use --apply)"
        print(f"golden: upgrade {mode} {changed} clean change(s), {conflicts} conflict(s)")
        sys.exit(2 if conflicts else 0)


if __name__ == "__main__":
    main()
