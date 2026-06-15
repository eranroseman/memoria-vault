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
    print("self-test:", "PASS" if failures == 0 else f"{failures} FAILURE(S)")
    return 1 if failures else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", type=Path)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("command", nargs="?", choices=["stage", "check", "restore"])
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--apply", action="store_true")
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
    else:
        targets = restore(args.vault, args.paths or None, apply=args.apply)
        verb = "restored" if args.apply else "would restore (use --apply)"
        for rel in targets:
            print(f"  {rel}")
        print(f"golden: {verb} {len(targets)} file(s)")


if __name__ == "__main__":
    main()
