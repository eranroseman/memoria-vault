"""Validate the package seed ships only bundled Memoria Obsidian adapter files."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# This doctor owns exactly one job: positive membership over the seeded
# .obsidian tree. The retired-payload denylist that used to live beside it
# (FORBIDDEN_REL / FORBIDDEN_GLOBS) moved into removed_surfaces.json, where
# every other must-not-reappear rule already lives with an owner and reason —
# two mechanisms for one job had already drifted into overlap.
SEED_OBSIDIAN = Path("src/memoria_vault/product/workspace_seed/.obsidian")
# Deny by default: exact membership, never a prefix or glob. Widening it is a
# deliberate act per file, which is the only reason it catches the payload it
# exists to catch. The plugin's three entries are generated release artifacts.
ALLOWED_SEED_OBSIDIAN_FILES = {
    Path("app.json"),
    Path("community-plugins.json"),
    Path("core-plugins.json"),
    Path("graph.json"),
    Path("plugins/memoria-obsidian/main.js"),
    Path("plugins/memoria-obsidian/manifest.json"),
    Path("plugins/memoria-obsidian/styles.css"),
    Path("types.json"),
}


def check(root: Path = ROOT) -> list[str]:
    root = root.resolve()
    findings: list[str] = []
    seed_obsidian = root / SEED_OBSIDIAN
    if seed_obsidian.exists():
        for path in sorted(seed_obsidian.rglob("*")):
            if path.is_file():
                rel = path.relative_to(seed_obsidian)
                if rel not in ALLOWED_SEED_OBSIDIAN_FILES:
                    findings.append(
                        f"{path.relative_to(root).as_posix()}: "
                        "only bundled Memoria Obsidian seed files are allowed"
                    )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root to validate")
    args = parser.parse_args(argv)

    findings = check(args.root)
    if findings:
        print("plugin-provenance-doctor: FAIL", file=sys.stderr)
        for finding in findings:
            print(f"  - {finding}", file=sys.stderr)
        return 1
    print("plugin-provenance-doctor: clean (only bundled Memoria Obsidian seed files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
